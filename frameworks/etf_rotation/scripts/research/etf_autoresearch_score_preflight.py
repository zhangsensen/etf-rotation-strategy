"""Label-free exact-score deduplication for the unified ETF workflow.

Only a full score surface under the same fixed data/evaluator contract can
reuse an earlier local result. Partial overlap and high correlation never skip IC.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pandas as pd
import yaml

import run_etf_autoresearch_ic as fixed
from etf_autoresearch_recovery import bounded_call, validate_result


class CandidateScoreError(RuntimeError):
    """Candidate-local calculation/causality failure; never a data failure."""


def _score(path, features):
    return fixed.causal_scores(fixed.load_candidate(path), features, pd.Timestamp("2024-12-31"))



def score_surface(candidate_path: Path, input_profile: str) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Mirror the frozen evaluator's feature preparation, without opening labels."""
    groups = yaml.safe_load(fixed.GROUPS.read_text())["groups"]
    calendar_file = fixed.DATA / "1d/510300.SH.parquet"
    calendar = pd.DatetimeIndex(pd.to_datetime(
        pd.read_parquet(calendar_file, columns=["trade_date"]).trade_date)).sort_values()
    calendar = calendar[calendar <= fixed.COLD]
    panels = fixed.load_canonical_daily(fixed.DATA, fixed.UNIVERSE,
                                       as_of=str(fixed.COLD.date()), roles=("candidate",))
    fixed.engine.validate_groups(groups, panels["close"].columns)
    calendar = calendar[calendar >= panels["close"].index.min()]
    if len(panels["close"].index.difference(calendar)):
        raise ValueError("candidate calendar differs from exchange calendar")
    panels = {key: value.reindex(calendar) for key, value in panels.items()}
    features = {key: panels[key] for key in ("close", "open", "high", "low", "amount", "volume")}
    input_manifest = {"profile": "daily"}
    if input_profile != "daily":
        from etf_autoresearch_inputs import load_inputs
        features, input_manifest = load_inputs(input_profile, features, fixed.COLD, fixed.ROOT)
    paths = [calendar_file]
    for symbol in panels["close"].columns:
        paths.extend([fixed.DATA / "1d" / f"{symbol}.parquet",
                      fixed.DATA / "adj_factor" / f"{symbol}.parquet"])
    contract = {
        "input_profile": input_profile, "input_manifest": input_manifest,
        "evaluator_sha256": fixed.digest(Path(fixed.__file__)),
        "groups_sha256": fixed.digest(fixed.GROUPS),
        "universe_sha256": fixed.digest(fixed.UNIVERSE),
        "input_sha256": {str(p): fixed.digest(p) for p in paths},
        "implementation_sha256": {str(Path(m.__file__).resolve().relative_to(fixed.ROOT)):
                                  fixed.digest(Path(m.__file__)) for m in
                                  (fixed.engine, fixed.etf_mining_referee, fixed.etf_rank_utils, fixed.canonical_data)},
        "python_version": fixed.sys.version, "pandas_version": fixed.pd.__version__,
        "numpy_version": fixed.np.__version__, "cold_cutoff": str(fixed.COLD.date()),
    }
    # Only this isolated stage is attributable to candidate code, including timeout.
    candidate_error = None
    try:
        score = bounded_call(_score, candidate_path, features)
    except Exception as exc:
        candidate_error = exc
    for path, expected in contract["input_sha256"].items():
        if fixed.digest(Path(path)) != expected:
            raise ValueError("input hash mismatch during score preflight")
    if input_profile != "daily":
        _, after = load_inputs(input_profile, {key: panels[key] for key in
                              ("close", "open", "high", "low", "amount", "volume")}, fixed.COLD, fixed.ROOT)
        if after != input_manifest:
            raise ValueError("input manifest changed during score preflight")
    implementation_paths = {fixed.ROOT / path: expected for path, expected in contract['implementation_sha256'].items()}
    implementation_paths.update({Path(fixed.__file__): contract['evaluator_sha256'],
                                 fixed.GROUPS: contract['groups_sha256'], fixed.UNIVERSE: contract['universe_sha256']})
    if any(fixed.digest(path) != expected for path, expected in implementation_paths.items()):
        raise ValueError('evaluation contract changed during score preflight')
    if candidate_error is not None:
        raise CandidateScoreError(str(candidate_error)) from candidate_error
    surface = fixed.engine.aggregate(score, groups)
    surface = surface.loc[surface.index >= fixed.EVALUATION_START]
    known = (panels["close"].notna().rolling(60).sum().eq(60).all(axis=1)
             & panels["volume"].gt(0).all(axis=1) & score.notna().all(axis=1))
    known = known.reindex(surface.index)
    return surface, known, contract


def diagnose_overlap(surface, known, references):
    """Read saved score surfaces only. High overlap never prevents IC evaluation."""
    from audit_etf_autoresearch_novelty import read_prefix
    comparisons, skipped = [], []
    ranks = fixed.etf_rank_utils.stable_rank(surface)
    for reference in references:
        path = Path(reference['score_path'])
        try:
            other = read_prefix(path)
            if set(other.columns) != set(surface.columns):
                raise ValueError('different groups')
            dates = surface.index.intersection(other.index)
            left, right = surface.loc[dates], other.loc[dates, surface.columns]
            valid = known.loc[dates] & left.notna().all(axis=1) & right.notna().all(axis=1)
            corr = ranks.loc[dates[valid]].corrwith(fixed.etf_rank_utils.stable_rank(right.loc[valid]), axis=1).dropna()
            if len(corr) < 40:
                skipped.append({'candidate': reference['candidate'], 'reason': 'insufficient_common_dates', 'n': len(corr)})
                continue
            comparisons.append({**reference, 'n': len(corr),
                'first_date': str(corr.index.min().date()), 'last_date': str(corr.index.max().date()),
                'mean_abs_daily_rank_corr': float(corr.abs().mean()),
                'mean_signed_daily_rank_corr': float(corr.mean())})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            skipped.append({'candidate': reference['candidate'], 'reason': str(exc)})
    comparisons.sort(key=lambda r: (-r['mean_abs_daily_rank_corr'], r['candidate']))
    nearest = comparisons[0] if comparisons else None
    return {'nearest': nearest, 'top_matches': comparisons[:5], 'compared': len(comparisons), 'skipped': skipped,
            'classification': ('UNKNOWN' if nearest is None else 'HIGH_RANK_OVERLAP'
                               if nearest['mean_abs_daily_rank_corr'] >= .7 else 'LOWER_OBSERVED_OVERLAP'),
            'scope': 'Prelabel score diagnostic only; common complete group scores and current ETF known mask. '
                     'Different manifests/old masks may limit comparability. Not exact deduplication or an IC gate.',
            'labels_opened': False}


def check_exact_scores(candidate_path: Path, input_profile: str, output_root: Path,
                       historical_rows: list[dict], *, inventory=None, runs_root=None) -> dict:
    candidate_path, output_root = Path(candidate_path), Path(output_root)
    source_hash = fixed.digest(candidate_path)
    try:
        surface, known, contract = score_surface(candidate_path, input_profile)
    finally:
        if fixed.digest(candidate_path) != source_hash:
            raise ValueError("candidate source changed during score preflight")
    score_hash = sha256(surface.to_csv(index_label="signal_date").encode()).hexdigest()
    receipt = {"candidate_sha256": source_hash, "score_sha256": score_hash,
               "contract": contract, "known_sha256": sha256(known.to_csv().encode()).hexdigest(),
               "duplicate_of": None,
               "scope": "complete signed group scores/index and ETF known mask, same input manifest and evaluation contract",
               "labels_opened": False}
    # Same ranking arithmetic as the frozen evaluator; no returns or labels used.
    complete = known & surface.notna().all(axis=1)
    rankable = complete & fixed.etf_rank_utils.stable_rank(surface).nunique(axis=1).gt(1)
    receipt['known_complete_days'] = int(complete.sum())
    receipt['rankable_signal_days'] = int(rankable.sum())
    receipt['structural_failure'] = None if rankable.any() else 'ZERO_RANKABLE_DATES'
    if not rankable.any():
        return receipt
    for row in sorted(historical_rows, key=lambda item: item["run_id"]):
        run_dir = output_root / row["run_id"]
        result_path, score_path = run_dir / "result.json", run_dir / "group_scores.csv"
        if not result_path.is_file() or not score_path.is_file():
            continue
        result = json.loads(result_path.read_text())
        if any(result.get(key) != value for key, value in contract.items()):
            continue
        # Missing provenance cannot justify skipping; existing broken seals are system failures.
        seal = run_dir / "evaluation_complete.json"
        source = Path(row["code_path"]) if row.get("code_path") else None
        if not seal.is_file() or source is None or not source.is_file():
            continue
        validate_result(run_dir, fixed.digest(source), input_profile, fixed.ROOT)
        if fixed.digest(score_path) != score_hash:
            continue
        try:
            old_surface, old_known, old_contract = score_surface(source, input_profile)
        except CandidateScoreError:
            continue
        if (old_contract != contract or not old_surface.equals(surface)
                or not old_known.equals(known)
                or fixed.digest(source) != result.get("candidate_sha256")):
            continue
        receipt["duplicate_of"] = {"run_id": row["run_id"], "candidate": row.get("candidate"),
                                   "result_path": str(result_path), "score_sha256": score_hash}
        break
    if inventory is not None and runs_root is not None and not receipt['duplicate_of']:
        import csv
        references = [{'candidate': r['candidate'], 'family': r.get('canonical_family') or r.get('family'),
                       'source': 'local_trial', 'score_path': str(output_root / r['run_id'] / 'group_scores.csv')}
                      for r in historical_rows if r.get('candidate')]
        with Path(inventory).open() as handle:
            references.extend({'candidate': r['candidate'], 'family': r.get('family'), 'source': 'formal_inventory',
                               'score_path': str(Path(runs_root) / r['source_run'] / f"scores_{r['candidate']}.csv")}
                              for r in csv.DictReader(handle))
        receipt['score_overlap'] = diagnose_overlap(surface, known, references)
    return receipt
