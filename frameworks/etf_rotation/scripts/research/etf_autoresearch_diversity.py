"""Economic family planning and local campaign-history helpers."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
import re
from typing import Any

from etf_autoresearch_context import compact_planning_context, tabulate_history
from etf_autoresearch_implementation import KERNEL_SELECTION_GUIDANCE

def diversity_memory(context):
    """Observed redundancy affects search effort only, never IC retention."""
    families, profiles, foci, seen = {}, {}, {}, set()
    for row in context.get("local_trial_definitions", []):
        if not row.get("run_id") or row["run_id"] in seen:
            continue
        seen.add(row["run_id"])
        family = normalize_family(row.get("canonical_family") or row.get("family"))
        if not family:
            continue
        bucket = families.setdefault(family, {"attempts": 0, "overlap_observations": [], "variants": []})
        bucket["attempts"] += 1
        bucket["variants"].append({k: row.get(k) for k in
                                   ("candidate", "run_id", "status", "formula", "mechanism", "input_profile")})
        nearest = row.get("nearest") or {}
        exact = row.get("reason_code") == "EXACT_SCORE_DUPLICATE"
        high = (row.get("status") == "COMPLETED" and nearest.get("n", 0) >= 40
                and nearest.get("mean_abs_daily_rank_corr", 0) >= .7)
        if not exact and not high:
            continue
        bucket["overlap_observations"].append({"run_id": row["run_id"], "exact": exact,
            "nearest": row.get("duplicate_of") if exact else nearest})
        profile = row.get("input_profile")
        if profile:
            profiles[profile] = profiles.get(profile, 0) + 1
            if row.get("search_focus"):
                by_focus = foci.setdefault(profile, {})
                focus = row["search_focus"]
                by_focus[focus] = by_focus.get(focus, 0) + 1
    # Bounded scheduling penalties age out naturally as other cells receive work.
    # One failed or similar variant is not a universal family verdict.
    penalty = lambda n: min(2, n - 1) if n >= 2 else 0
    return {"family_evidence": families,
            "family_penalties": {k: penalty(len(v["overlap_observations"])) for k, v in families.items()},
            "profile_penalties": {k: penalty(v) for k, v in profiles.items()},
            "focus_penalties": {p: {k: penalty(v) for k, v in bucket.items()} for p, bucket in foci.items()},
            "policy": "Repeated observed rank overlap >=0.7 with >=40 common days or sealed exact duplicates "
                      "adds at most two search-effort units. Not an IC gate, independence count or permanent ban."}


PLAN_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["families"],
    "properties": {"families": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["family_key", "mechanism", "distinct_from", "why_distinct", "input_profile",
                      "formula", "direction", "required_panels", "nearest_existing_candidate",
                      "difference_from_existing", "novelty_basis", "new_information", "math_kernel"],
        "properties": {
            **{key: {"type": "string"} for key in
               ("family_key", "mechanism", "distinct_from", "why_distinct", "input_profile", "formula",
                "nearest_existing_candidate", "difference_from_existing", "new_information")},
            "novelty_basis": {"type": "string", "enum": ["new_mechanism", "new_information", "bounded_variant"]},
            "math_kernel": {"type": "string", "enum": ["custom", "conditional_ols", "rolling_spearman"]},
            "direction": {"type": "integer", "enum": [-1, 1]},
            "required_panels": {"type": "array", "items": {"type": "string"}},
        },
    }}},
}

MAX_PLANNING_PROMPT_CHARS = 900000
PLANNING_PROMPT_HEADROOM_CHARS = 25000


def build_planning_prompt(context: dict) -> str:
    """Serialize a label-blind history view with deterministic budget fallback."""
    prefix = KERNEL_SELECTION_GUIDANCE + '\n' + (
        "Propose up to the requested number of ETF factor hypotheses in an OPEN search. "
        "Choose freely among all approved input profiles; do not combine unavailable panels. "
        "The question menu and historical families are optional references, not a taxonomy, whitelist, "
        "novelty threshold or quota. Existing families, bounded variants, same-family siblings and "
        "questions outside the menu are eligible. Explain the question each formula tests and its "
        "difference from actual historical definitions; do not invent novelty or filler proposals. "
        "Consult historical positive, weak and negative results without treating one variant as a "
        "universal family verdict. Semantic similarity and score correlation are diagnostic only. "
        "Avoid knowingly repeating the identical formula without new information; exact-score reuse "
        "is decided by the controller under the full input/evaluation contract, not by family labels. "
        "Freeze formula, ex-ante direction, windows, masks and required panels before outcomes. "
        "Do not flip direction to rescue previously observed negative IC. Use only available panels "
        "with their review_contract timing and definitions. Never request labels or future data. "
        "Give a real nearest historical candidate ID when available; this is a comparison reference, "
        "not a compulsory parent or family restriction. Choose conditional_ols for conditional slopes, "
        "rolling_spearman for within-window ranks, custom otherwise. No expected IC cutoff. Return "
        "fewer proposals if useful questions are exhausted. Return the required JSON schema.\n")
    packed = compact_planning_context(context)

    compact_json = False

    def render():
        options = {'separators': (',', ':')} if compact_json else {}
        return prefix + json.dumps(packed, ensure_ascii=False, **options)

    prompt = render()
    soft_limit = MAX_PLANNING_PROMPT_CHARS - PLANNING_PROMPT_HEADROOM_CHARS
    if len(prompt) > soft_limit:
        # Repeated JSON field names consume space without adding evidence.
        # Explicit column order keeps every value, including exact formulas,
        # signed directions, coverage and outcome references, available.
        tabulate_history(packed)
        prompt = render()
    if len(prompt) > soft_limit:
        definitions = {row.get('run_id'): row.get('candidate')
                       for row in context.get('local_trial_definitions', []) if row.get('run_id')}
        outcomes = context.get('local_completed_candidates', [])
        columns = packed.get('local_completed_candidates_columns', [])
        if (outcomes and 'candidate' in columns
                and all(row.get('run_id') in definitions
                        and definitions[row['run_id']] == row.get('candidate') for row in outcomes)):
            index = columns.index('candidate')
            columns.pop(index)
            for row in packed['local_completed_candidates']:
                row.pop(index)
            packed['history_detail_note'] += (
                " Outcome candidate names join exactly to local_trial_definitions by run_id; "
                "the repeated candidate-name column was omitted."
            )
            prompt = render()
    if len(prompt) > soft_limit:
        # Whitespace is also redundant. The JSON content is unchanged.
        compact_json = True
        prompt = render()
    if len(prompt) > soft_limit:
        columns = packed.get('local_trial_definitions_columns')
        if columns and 'mechanism' in columns:
            index = columns.index('mechanism')
            columns.pop(index)
            for row in packed['local_trial_definitions']:
                row.pop(index)
        packed['history_detail_note'] += (
            " Planner prompt exceeded its soft size target, so repeated mechanism prose was omitted; "
            "all run/candidate/family IDs, exact formulas, directions and required panels remain."
        )
        prompt = render()
    if len(prompt) > soft_limit:
        columns = packed.get('local_completed_candidates_columns', [])
        for field in ('hac_t', 'n', 'parent_eligible'):
            if field in columns:
                index = columns.index(field)
                columns.pop(index)
                for row in packed['local_completed_candidates']:
                    row.pop(index)
        packed['history_detail_note'] += (
            " Repeated historical HAC/coverage diagnostics were omitted for prompt capacity; "
            "signed IC and run/candidate IDs remain."
        )
        prompt = render()
    if len(prompt) > soft_limit:
        for bucket in packed.get('diversity_memory', {}).get('family_evidence', {}).values():
            bucket.pop('overlap_examples', None)
        packed['history_detail_note'] += (
            " Per-observation overlap examples were omitted for prompt capacity; family overlap counts remain."
        )
        prompt = render()
    if len(prompt) > soft_limit:
        for bucket in packed.get('diversity_memory', {}).get('family_evidence', {}).values():
            bucket.pop('variant_examples', None)
        packed['history_detail_note'] += (
            " Repeated variant examples were omitted; all variant counts and exact local definition identities remain."
        )
        prompt = render()
    if len(prompt) > soft_limit:
        columns = packed.get('local_completed_candidates_columns', [])
        for field in ('family', 'input_profile', 'parent_eligible'):
            if field in columns:
                index = columns.index(field)
                columns.pop(index)
                for row in packed['local_completed_candidates']:
                    row.pop(index)
        packed['history_detail_note'] += (
            " Redundant family/profile fields were omitted from outcomes; local definition identities retain them."
        )
        prompt = render()
    if len(prompt) > MAX_PLANNING_PROMPT_CHARS:
        raise ValueError(f"compact ETF planning prompt exceeds hard limit: {len(prompt)} characters")
    return prompt


def _canonical(value: Any) -> str:
    return re.sub(r"[-_\s]+", "_", str(value or "").strip().lower()).strip("_")


def normalize_family(value: Any) -> str:
    """Normalize family labels so spelling aliases share one family key."""
    return _canonical(value)


def _profile_names(allowed_profiles: Any) -> set[str]:
    names = set()
    for item in allowed_profiles or []:
        value = item if isinstance(item, str) else next(
            (item[key] for key in ("profile", "name", "key") if item.get(key)), "")
        if value:
            names.add(_canonical(value))
    return names


def _profile_panels(allowed_profiles: Any) -> dict[str, set[str]]:
    result = {}
    if isinstance(allowed_profiles, dict):
        rows = allowed_profiles.items()
    else:
        rows = ((item.get("profile") or item.get("name") or item.get("key"), item)
                for item in allowed_profiles or [] if isinstance(item, dict))
    for name, profile in rows:
        if name and isinstance(profile, dict):
            result[_canonical(name)] = {str(panel) for panel in profile.get("panel_names", [])}
    return result


def validate_plan(specs: Any, count: int, allowed_profiles: Any,
                  forbidden_family_keys: Any, *, open_search=True) -> list[dict]:
    """Validate model output and canonicalize family/profile identifiers."""
    if not open_search:
        raise ValueError("legacy family-admission policies are archived")
    if not isinstance(specs, list):
        raise ValueError("family plan must be a list")
    if count < 0 or len(specs) > count:
        raise ValueError("family plan exceeds requested count")
    allowed = _profile_names(allowed_profiles)
    profile_panels = _profile_panels(allowed_profiles)
    result = []
    fields = ("family_key", "mechanism", "distinct_from", "why_distinct", "input_profile", "formula",
              "nearest_existing_candidate", "difference_from_existing", "new_information")
    for raw in specs:
        if not isinstance(raw, dict):
            raise ValueError("family spec must be an object")
        item = {key: str(raw.get(key, "")).strip() for key in fields}
        if raw.get("novelty_basis") not in {"new_mechanism", "new_information", "bounded_variant"}:
            raise ValueError("plan must declare novelty basis")
        item["novelty_basis"] = raw["novelty_basis"]
        if raw.get("math_kernel") not in {"custom", "conditional_ols", "rolling_spearman"}:
            raise ValueError("plan must select the matching mathematical kernel")
        item["math_kernel"] = raw['math_kernel']
        if raw.get("direction") not in (-1, 1) or isinstance(raw.get("direction"), bool):
            raise ValueError("direction must be +1 or -1")
        panels = raw.get("required_panels")
        if (not isinstance(panels, list) or any(not isinstance(panel, str) or not panel.strip() for panel in panels)
                or len(set(panels)) != len(panels)):
            raise ValueError("required_panels must be a unique string array")
        item["direction"] = raw["direction"]
        item["required_panels"] = panels
        if any(not item[key] for key in fields):
            raise ValueError("family spec is missing mechanism, distinction rationale, or profile")
        key = _canonical(item["family_key"])
        profile = _canonical(item["input_profile"])
        if not key:
            raise ValueError("empty family_key")
        if profile not in allowed:
            raise ValueError(f"input_profile is not allowed: {profile}")
        unknown_panels = set(panels) - profile_panels.get(profile, set())
        if unknown_panels:
            raise ValueError(f"required_panels are not available in {profile}: {sorted(unknown_panels)}")
        if re.search(r"\b(label|target|forward_return|future_return|fwd_return)\b", item["formula"], re.I):
            raise ValueError("formula cannot name outcome labels")
        item["family_key"] = key
        item["input_profile"] = profile
        result.append(item)
    return result


def historical_family_keys(context: dict) -> set[str]:
    """Collect family identities already represented in formal or local history."""
    blocked: set[str] = set()
    formal = context.get("historical_formal_definitions", [])
    for row in formal if isinstance(formal, list) else []:
        if isinstance(row, dict):
            for field in ("family", "canonical_family", "family_key"):
                key = _canonical(row.get(field))
                if key:
                    blocked.add(key)
    completed = context.get("local_completed_candidates", [])
    for row in completed if isinstance(completed, list) else []:
        if isinstance(row, dict):
            for field in ("family", "canonical_family"):
                key = _canonical(row.get(field))
                if key:
                    blocked.add(key)
    history = context.get("aliases", context.get("family_history", {}).get("aliases", {}))
    if isinstance(history, dict):
        for alias, canonical in history.items():
            if _canonical(canonical) in blocked or _canonical(alias) in blocked:
                blocked.update({_canonical(alias), _canonical(canonical)})
    return blocked


class PlannerResponseError(ValueError):
    """A model returned an invalid plan; one label-free correction is permitted."""


def plan_families(context: dict, directory: Path, model: str) -> list[dict]:
    """Propose frozen hypotheses using all approved inputs and saved history."""
    requested = int(context["requested_count"])
    # Historical family identities are shown to the planner for reclassification and
    # bounded-variant decisions. They are not themselves hard bans.
    excluded = {_canonical(k) for k in context.get("forbidden_family_keys", [])}
    context = {**context, "forbidden_family_keys": sorted(excluded)}
    from etf_autoresearch_recovery import atomic
    atomic(Path(directory) / 'planning_context.json', context)
    prompt = build_planning_prompt(context)
    # Import the existing bounded, local model interface at call time.
    from run_etf_autoresearch_campaign import model_json
    schema = deepcopy(PLAN_SCHEMA)
    schema['properties']['families']['maxItems'] = requested
    schema['properties']['families']['items']['properties']['input_profile']['enum'] = sorted(
        _profile_names(context.get('allowed_profiles', [])))
    panel_names = sorted({panel for panels in _profile_panels(context.get('allowed_profiles', [])).values()
                          for panel in panels})
    schema['properties']['families']['items']['properties']['required_panels']['items']['enum'] = panel_names
    payload = model_json(prompt, schema, Path(directory), model, "family_plan")
    if not isinstance(payload, dict) or set(payload) != {"families"}:
        raise PlannerResponseError("family planner response does not match schema")
    # Keep valid raw proposals for the workflow's auditable pre-implementation
    # classification. Do not silently discard known identities in the model adapter.
    if not isinstance(payload["families"], list) or len(payload["families"]) > requested:
        raise PlannerResponseError("family plan exceeds requested count or is not a list")
    try:
        return validate_plan(payload["families"], requested, context.get("allowed_profiles", []), [],
                             open_search=context.get("mode", "open") == "open")
    except ValueError as exc:
        raise PlannerResponseError(str(exc)) from exc


def family_history(output_root: Path) -> dict:
    """Summarize family attempts and cooldowns by completed campaign round."""
    root = Path(output_root)
    summaries = []
    for path in (root / "campaigns").glob("*/summary.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or "reference" in path.parent.name.lower():
            continue
        rows = data.get("rounds")
        if isinstance(rows, list):
            # Legacy IDs provide an immutable deterministic fallback, not mtime.
            dates = re.findall(r"20\d{6}", path.parent.name)
            legacy_key = (dates[-1] if dates else "", path.parent.name)
            summaries.append(((data.get("event_sequence", 0), legacy_key), data, rows))
    summaries.sort(key=lambda pair: pair[0])

    # Only an approved, completed reviewed row establishes a global alias.
    # Rejected reviewer classifications describe a proposal and cannot relabel
    # its planned parent family.
    aliases: dict[str, str] = {}
    for _, _, rows in summaries:
        for row in rows:
            if not isinstance(row, dict):
                continue
            family = normalize_family(row.get("family") or row.get("planned_family"))
            canonical = normalize_family(row.get("canonical_family") or family)
            review = row.get("review")
            safely_reviewed = (isinstance(review, dict) and review.get("approved") is True
                               and str(row.get("status", "")).upper() == "COMPLETED")
            if family and canonical and (family == canonical or safely_reviewed):
                aliases[family] = canonical

    def resolve(name: str) -> str:
        seen = set()
        while name in aliases and aliases[name] != name and name not in seen:
            seen.add(name)
            name = aliases[name]
        return name

    aliases = {name: resolve(name) for name in aliases}
    family_counts: dict[str, int] = {}
    completed_rounds: list[list[str]] = []
    refinement_streaks: dict[str, int] = {}
    terminal = {"COMPLETED", "FAILED", "REJECTED", "DUPLICATE", "DIVERSITY_SKIPPED"}
    for _, summary, rows in summaries:
        grouped: dict[int, list[dict]] = {}
        for row in sorted(rows, key=lambda r: (r.get("round", 0), r.get("run_id", "")) if isinstance(r, dict) else (0, "")):
            if not isinstance(row, dict):
                continue
            family = normalize_family(row.get("family") or row.get("planned_family") or row.get("canonical_family"))
            canonical = resolve(normalize_family(row.get("canonical_family") or family))
            if family and canonical:
                family_counts[canonical] = family_counts.get(canonical, 0) + 1
            round_no = row.get("round")
            if isinstance(round_no, int) and not isinstance(round_no, bool):
                grouped.setdefault(round_no, []).append(row)
            if (row.get("status") == "DUPLICATE" and row.get("mode") == "refine"
                    and row.get("reason_code") == "EXACT_SCORE_DUPLICATE" and canonical):
                refinement_streaks[canonical] = refinement_streaks.get(canonical, 0) + 1
            if row.get("status") != "COMPLETED" or not family or not canonical:
                continue
            numeric_ic = row.get("ic")
            try:
                numeric = float(numeric_ic)
            except (TypeError, ValueError):
                continue
            if numeric != numeric or numeric in (float("inf"), float("-inf")):
                continue
            if row.get("keep") is True:
                # A successful proposal becomes a new local parent, regardless of mode.
                refinement_streaks[canonical] = 0
            elif normalize_family(row.get("mode")) == "refine" and row.get("keep") is False:
                refinement_streaks[canonical] = refinement_streaks.get(canonical, 0) + 1

        declared_completed = summary.get("completed_rounds")
        if isinstance(declared_completed, int):
            # Empty completed rounds consume scheduling budget and age cooldowns,
            # without inventing candidate rows in the research library.
            for number in range(1, declared_completed + 1):
                grouped.setdefault(number, [])
        for number in sorted(grouped):
            rows_in_round = grouped[number]
            if isinstance(declared_completed, int) and number <= declared_completed:
                finished = True
            elif declared_completed is None:
                finished = bool(rows_in_round) and all(
                    str(row.get("status", "")).upper() in terminal for row in rows_in_round)
            else:
                finished = False
            if finished:
                families = []
                for row in rows_in_round:
                    raw = normalize_family(row.get("canonical_family") or row.get("family") or row.get("planned_family"))
                    canonical = resolve(raw)
                    if canonical and canonical not in families:
                        families.append(canonical)
                completed_rounds.append(families)
    recent = [family for batch in completed_rounds[-2:] for family in batch]
    profile_counts, focus_counts = {}, {}
    for path in sorted((root / "campaigns").glob("*/planning_r*/planning_lanes.json")):
        data = json.loads(path.read_text())
        for lane in data.get("lanes", []):
            profile = lane["profile"]
            profile_counts[profile] = profile_counts.get(profile, 0) + 1
            focus = lane.get("mechanism_focus")
            if focus:
                bucket = focus_counts.setdefault(profile, {})
                bucket[focus] = bucket.get(focus, 0) + 1
    return {"recent_round_families": recent,
            "profile_search_counts": profile_counts, "profile_focus_counts": focus_counts,
            "family_attempt_counts": family_counts, "aliases": aliases,
            "next_event_sequence": 1 + max((key[0] for key, _, _ in summaries), default=0),
            "unsuccessful_refinements": {key: value for key, value in refinement_streaks.items() if value}}
