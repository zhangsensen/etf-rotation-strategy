#!/usr/bin/env python3
"""Round 662 (S57, main controller directive 2026-09-21): drawdown-
geometry cluster representative selection, report-only, no new
preregistration. Computes pairwise rank corr (discovery/audit windows,
stride=5) and daily top-3 overlap across 11 named candidates, backfills
H10/H20 for the 4 candidates that postdate the S39 profile cutoff
(round_638) via the engine's own _topk_referee against forward[10]/[20],
and applies the controller's stated selection criteria (跨实现成立 +
三视界 + 2025正 + 换手低) to pick a representative."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as eng  # noqa: E402
from etf_strategy.core.family_registry import load_builtin_families, resolve_family  # noqa: E402

OUT = eng.WORKSPACE_OUTPUTS / "round_662"
OUT.mkdir(parents=True, exist_ok=True)

# id -> (lane_round, direction, [(atom_name, source), ...] -- 1 atom = atomic, 2 = rank_spread(a)-rank(b))
CANDIDATES = {
    "QA8": ("round_545", -1.0, [("UNDERWATER_FRAC_CHG_20", "intraday_drawdown_1m")]),
    "R_DD48": ("round_652", 1.0, [("R_VFP_ULCER_SHIFT_20", "repl_pi37_core_v1"), ("UNDERWATER_FRAC_CHG_20", "intraday_drawdown_1m")]),
    "S42P17": ("round_641", -1.0, [("UNDERWATER_FRAC_CHG_20", "intraday_drawdown_1m"), ("UNDERWATER_FRAC_Z_60", "intraday_pain_recovery_1m")]),
    "S54P_ULCER_C": ("round_656", 1.0, [("REL_ULCER_CATEGORY_CHG_20", "category_relative_geometry"), ("GAP_DD_CONSUMPTION_RATIO_20", "overnight_intraday_mismatch_v1")]),
    "S32P1": ("round_631", -1.0, [("REL_UNDERWATER_CATEGORY_CHG_20", "category_relative_geometry"), ("R_LOG_AMOUNT_VOL_20", "repl_volume_core_a")]),
    "HB1": ("round_592", 1.0, [("ON_SIGN_STREAK_20", "overnight_structure_1d"), ("UNDERWATER_FRAC_CHG_20", "intraday_drawdown_1m")]),
    "UE3": ("round_575", 1.0, [("YZ_OVERNIGHT_SHARE_20", "range_based_vol_1m"), ("UNDERWATER_FRAC_CHG_20", "intraday_drawdown_1m")]),
    "FC3": ("round_561", 1.0, [("UNDERWATER_FRAC_Z_60", "intraday_pain_recovery_1m"), ("CATEGORY_DISPERSION_20", "category_state")]),
    "FC8": ("round_561", 1.0, [("UNDERWATER_FRAC_Z_60", "intraday_pain_recovery_1m"), ("PERM_ENTROPY_RET_20", "permutation_entropy_1m")]),
    "S42P10": ("round_641", 1.0, [("UNDERWATER_FRAC_Z_60", "intraday_pain_recovery_1m"), ("GAP_DD_CONSUMPTION_RATIO_20", "overnight_intraday_mismatch_v1")]),
    "WA1": ("round_601", -1.0, [("VT_UNDERWATER_FRAC_20", "volume_time_drawdown"), ("MFI_EXTREME_FRAC_20", "accumulation_distribution_1m")]),
}

# candidates missing H10/H20 in round_638's slow_signal_profile.csv (postdate its round_638 cutoff)
NEED_H10_H20 = {"R_DD48", "S42P17", "S54P_ULCER_C", "S42P10"}

DISCOVERY_END = eng.DISCOVERY_END
AUDIT_START, AUDIT_END = eng.AUDIT_START, eng.AUDIT_END


def main() -> None:
    load_builtin_families()
    panels, eligibility_all, symbols, forward = eng._load_context()
    dates = panels["close"].index
    discovery_mask = dates <= DISCOVERY_END
    audit_mask = (dates >= AUDIT_START) & (dates <= AUDIT_END)

    space_cache: dict[str, dict] = {}

    def get_raw(name: str, source: str) -> pd.DataFrame:
        if source not in space_cache:
            mining = yaml.safe_load(eng._config_path(source).read_text())
            space_cache[source] = resolve_family(source).builder(panels, eligibility_all, eng.CANONICAL_ROOT, mining)
        return space_cache[source][name][symbols]

    signals: dict[str, pd.DataFrame] = {}
    for cid, (rnd, direction, atoms) in CANDIDATES.items():
        if len(atoms) == 1:
            raw = get_raw(*atoms[0])
            score = eng.cross_sectional_rank(raw, eligibility_all[symbols])
        else:
            (na, sa), (nb, sb) = atoms
            ra = eng.cross_sectional_rank(get_raw(na, sa), eligibility_all[symbols])
            rb = eng.cross_sectional_rank(get_raw(nb, sb), eligibility_all[symbols])
            score = ra - rb
        signals[cid] = (score * direction).where(eligibility_all[symbols])

    # backfill H10/H20 for the 4 gap candidates. _topk_referee only returns a
    # discovery-window block-t; replicate the same block_means recipe on the
    # AUDIT-window excess series to get an audit block-t (matching what the
    # historical round_638 slow_signal_profile.csv's h10/h20_audit_t columns
    # represent), since direction is already baked into `signals[cid]`.
    k = eng.GATES["topk_k"]

    def _audit_block_t(sig: pd.DataFrame, fwd: pd.DataFrame) -> tuple[float, float]:
        f = fwd.where(eligibility_all[symbols])
        s = sig.where(eligibility_all[symbols])
        valid = s.notna() & f.notna()
        s, f = s.where(valid), f.where(valid)
        n = valid.sum(axis=1)
        ok = n >= max(eng.MIN_PAIRS, k + 1)
        top_mask = s.rank(axis=1, ascending=False, method="first") <= k
        top_ret = f.where(top_mask).mean(axis=1).where(ok)
        ew_ret = f.mean(axis=1).where(ok)
        excess = (top_ret - ew_ret).loc[AUDIT_START:AUDIT_END].dropna()
        if len(excess) == 0:
            return float("nan"), float("nan")
        blocks = eng.block_means(excess.to_frame("x"), eng.PRIMARY)["x"].dropna()
        t_val = float(blocks.mean() / (blocks.std(ddof=1) / np.sqrt(len(blocks)))) if len(blocks) > 3 else float("nan")
        return float(excess.mean() * 1e4), t_val

    h_backfill = {}
    for cid in NEED_H10_H20:
        sig = signals[cid]
        row = {}
        for h in (10, 20):
            bp, t_val = _audit_block_t(sig, forward[h])
            row[f"h{h}_audit_bp"] = bp
            row[f"h{h}_audit_t"] = t_val
        h_backfill[cid] = row
        print(cid, "H10/H20 backfill:", row)

    # pairwise rank corr (discovery + audit, stride=5) and daily top-3 overlap
    ids = list(CANDIDATES.keys())
    stride_disc = {cid: eng._stride_vector(signals[cid].loc[discovery_mask]) for cid in ids}

    def _audit_stride(df: pd.DataFrame) -> pd.Series:
        return df.iloc[:: eng.RANK_CORR_STRIDE].stack(future_stack=True)

    stride_audit = {cid: _audit_stride(signals[cid].loc[audit_mask]) for cid in ids}

    def _top3_overlap(a: pd.DataFrame, b: pd.DataFrame, mask) -> float:
        aa, bb = a.loc[mask], b.loc[mask]
        top_a = aa.rank(axis=1, ascending=False, method="first") <= 3
        top_b = bb.rank(axis=1, ascending=False, method="first") <= 3
        both_valid = aa.notna().sum(axis=1).ge(3) & bb.notna().sum(axis=1).ge(3)
        inter = (top_a & top_b & both_valid.to_frame().values).sum(axis=1)
        return float(inter.loc[both_valid].mean()) if both_valid.any() else float("nan")

    corr_disc = pd.DataFrame(index=ids, columns=ids, dtype=float)
    corr_audit = pd.DataFrame(index=ids, columns=ids, dtype=float)
    overlap_disc = pd.DataFrame(index=ids, columns=ids, dtype=float)
    overlap_audit = pd.DataFrame(index=ids, columns=ids, dtype=float)
    for i in ids:
        for j in ids:
            corr_disc.loc[i, j] = eng._pairwise_pearson(stride_disc[i], stride_disc[j])
            frame = pd.DataFrame({"a": stride_audit[i], "b": stride_audit[j]})
            v = frame.corr(min_periods=50)
            corr_audit.loc[i, j] = float(v.loc["a", "b"]) if np.isfinite(v.loc["a", "b"]) else float("nan")
            overlap_disc.loc[i, j] = _top3_overlap(signals[i], signals[j], discovery_mask)
            overlap_audit.loc[i, j] = _top3_overlap(signals[i], signals[j], audit_mask)

    corr_disc.to_csv(OUT / "pairwise_rank_corr_discovery.csv")
    corr_audit.to_csv(OUT / "pairwise_rank_corr_audit.csv")
    overlap_disc.to_csv(OUT / "top3_overlap_discovery.csv")
    overlap_audit.to_csv(OUT / "top3_overlap_audit.csv")
    (OUT / "h_backfill.json").write_text(json.dumps(h_backfill, indent=2))

    print("\n--- discovery-window rank corr matrix ---")
    print(corr_disc.round(2).to_string())
    print("\n--- discovery-window top-3 daily overlap (mean intersection size, max 3) ---")
    print(overlap_disc.round(2).to_string())


if __name__ == "__main__":
    main()
