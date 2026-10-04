"""Economic family planning and local campaign-history helpers."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
import re
from typing import Any

from etf_autoresearch_context import compact_planning_context
from etf_autoresearch_implementation import KERNEL_SELECTION_GUIDANCE

# Search prompts, not a closed taxonomy or evidence of independent factors.
MECHANISM_FOCI = {
    "demand_supply": "creation/redemption, participation and demand/supply imbalance",
    "price_discovery": "auction acceptance, overnight/intraday adjustment and information absorption",
    "liquidity_capacity": "trading depth, price impact and liquidity replenishment",
    "risk_response": "asymmetric, nonlinear or state-dependent risk response",
    "valuation_adjustment": "valuation disagreement, convergence and adjustment speed",
    "relative_transmission": "peer dispersion, lead/lag and cross-market transmission",
    "open_search": "another economically justified channel outside these search prompts",
    "flow_absorption": "Does secondary-market participation absorb or amplify disclosed creation/redemption pressure? Compare response paths with the existing contemporaneous flow-return slopes.",
    "premium_resolution": "Does a disclosed NAV premium resolve through price adjustment or persist alongside trading participation? Distinguish adjustment paths from premium levels and simple range correlations.",
    "liquidity_recovery": "After a past large price-impact episode, does participation recover before the price range normalizes? Use only episodes already observed by D; compare recovery paths with average illiquidity.",
    "participation_concentration": "Is trading participation concentrated in isolated sessions or sustained across a trailing path, and does price acceptance differ? Explain information beyond average volume and volatility.",
    "shock_recovery": "Following an already available external shock, how does ETF price acceptance recover over observed sessions? Distinguish recovery sequence from direct shock beta, sign conditioning and absolute sensitivity.",
}

# These are input-supported questions, not newly discovered economic families.
FOCUS_PANELS = {
    "flow_absorption": {"shares", "close", "amount"},
    "premium_resolution": {"premium", "close", "volume"},
    "liquidity_recovery": {"high", "low", "close", "amount"},
    "participation_concentration": {"close", "volume", "amount"},
    "shock_recovery": {"close"},
}


def eligible_foci(profile):
    panels = set(profile.get("panel_names", []))
    return [key for key in MECHANISM_FOCI
            if key not in FOCUS_PANELS or (FOCUS_PANELS[key] <= panels and
                (key != "shock_recovery" or any(p.endswith("_shock") for p in panels)))]


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


def classify_plans(specs, context):
    """Filter known identities before paying for implementations; no semantic claims."""
    if context.get("mode") == "open":
        return deepcopy(specs), []
    aliases = context.get("aliases", {})
    def canonical(key):
        key, seen = normalize_family(key), set()
        while key in aliases and key not in seen:
            seen.add(key)
            key = normalize_family(aliases[key])
        return key
    blocked = {canonical(k) for k in context.get("forbidden_family_keys", [])}
    historical = {canonical(k) for k in historical_family_keys(context)}
    references = {row.get("candidate") for field in ("historical_formal_definitions", "local_trial_definitions")
                  for row in context.get(field, []) if row.get("candidate")}
    accepted, skipped, seen = [], [], set()
    for spec in specs:
        key = canonical(spec["family_key"])
        reason = ("DECLARED_VARIANT_REQUIRES_PARENT_PLAN" if spec.get("novelty_basis") == "bounded_variant" else
                  "UNRESOLVED_HISTORICAL_REFERENCE" if references and spec.get("nearest_existing_candidate") not in references else
                  "OLD_FAMILY_REQUIRES_PARENT_PLAN" if key in historical else
                  "RESERVED_OR_PAUSED_FAMILY" if key in blocked else
                  "SAME_PLAN_FAMILY" if key in seen else None)
        if reason:
            skipped.append({"spec": spec, "canonical_family": key, "reason_code": reason})
        else:
            accepted.append(spec)
            seen.add(key)
    return accepted, skipped


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
                  forbidden_family_keys: Any, *, open_search=False) -> list[dict]:
    """Validate model output and canonicalize family/profile identifiers."""
    if not isinstance(specs, list):
        raise ValueError("family plan must be a list")
    if count < 0 or len(specs) > count:
        raise ValueError("family plan exceeds requested count")
    allowed = _profile_names(allowed_profiles)
    profile_panels = _profile_panels(allowed_profiles)
    forbidden = {_canonical(key) for key in forbidden_family_keys or []}
    seen: set[str] = set()
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
        if not key or (key in seen and not open_search):
            raise ValueError("repeated or empty family_key")
        if key in forbidden and not open_search:
            raise ValueError(f"family_key is forbidden by history: {key}")
        if profile not in allowed:
            raise ValueError(f"input_profile is not allowed: {profile}")
        unknown_panels = set(panels) - profile_panels.get(profile, set())
        if unknown_panels:
            raise ValueError(f"required_panels are not available in {profile}: {sorted(unknown_panels)}")
        if re.search(r"\b(label|target|forward_return|future_return|fwd_return)\b", item["formula"], re.I):
            raise ValueError("formula cannot name outcome labels")
        item["family_key"] = key
        item["input_profile"] = profile
        seen.add(key)
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
    """Ask the local campaign model for distinct economic mechanisms."""
    requested = int(context["requested_count"])
    # Historical family identities are shown to the planner for reclassification and
    # bounded-variant decisions. They are not themselves hard bans.
    excluded = {_canonical(k) for k in context.get("forbidden_family_keys", [])}
    context = {**context, "forbidden_family_keys": sorted(excluded)}
    from etf_autoresearch_recovery import atomic
    atomic(Path(directory) / 'planning_context.json', context)
    prompt = (
        "Plan up to the requested number of ETF factor families. Prioritize genuinely distinct economic "
        "mechanisms and source-independent family keys shared across input profiles. A different window, "
        "weighting, alias, normalization, or gate does not make a new family. Do not pad: return fewer "
        "when no defensible mechanism remains. Explain the economic distinction in distinct_from and "
        "why_distinct; that explanation is a proposal, not empirical proof. Use only allowed input profiles. "
        "Use only the explicitly listed panel_names; do not infer within-session activity from daily OHLCV "
        "panels. Never propose a deliberately uncomputable plan or use/request outcome labels. "
        "Prioritize under-covered mechanisms using family_attempt_counts and unsuccessful_refinements. "
        "Read diversity_memory and the tested formulas in local_trial_definitions before selecting a question. "
        "Name one exact historical candidate ID in nearest_existing_candidate (not a family name or invented ID) "
        "when any historical candidate exists. Explain the extra observable information and causal channel in "
        "new_information. A different data source alone is not a new mechanism. Windows, weights, transforms "
        "Choose math_kernel=conditional_ols for subset/conditional population slopes, rolling_spearman "
        "for trailing-window rank correlation, otherwise custom. Trusted kernels are embedded before "
        "implementation review; freeze masks, lag, window and minimum pairs in the formula. "
        "and conditioning of an existing channel are bounded_variant work, not new exploration. Declare "
        "novelty_basis honestly; a new name cannot turn a variant into new information. Choose a mechanism "
        "outside repeatedly overlapping directions unless a concrete new input/channel explains why it differs. "
        "In explore mode, do not revisit historical mechanisms or fill a short plan with old-family variants. "
        "Historical family keys are evidence for novelty classification: when explicitly assigned a refinement, "
        "a mechanism, identify the nearest candidate and state a bounded, substantive difference. Exact duplicate "
        "and cooldown exclusions are supplied separately. Each plan must freeze its formula, direction and required "
        "panels now, before any outcome is opened. Use review_contract definitions to check feasibility. "
        "When context mode is refine, propose at most one bounded improvement to the supplied parent_contract; "
        "keep assigned_family, input profile and parent direction exactly. State the changed formula and panels "
        "before implementation. Do not invent a new family for that slot. "
        "Return JSON matching the schema.\n\n" +
        json.dumps(compact_planning_context(context), ensure_ascii=False)
    )
    if context.get("mode") == "open":
        prompt = (
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
            "fewer proposals if useful questions are exhausted. Return the required JSON schema.\n" +
            json.dumps(compact_planning_context(context), ensure_ascii=False))
    prompt = KERNEL_SELECTION_GUIDANCE + '\n' + prompt
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
                             open_search=context.get("mode") == "open")
    except ValueError as exc:
        raise PlannerResponseError(str(exc)) from exc


def plan_profile_lanes(context: dict, directory: Path, model: str) -> list[dict]:
    """Bound exploration attention by source, preserving global novelty evidence.

    This schedules proposal work only. Profiles rotate independently of IC, and
    the unchanged batch review determines economic family identity.
    """
    from concurrent.futures import ThreadPoolExecutor
    from etf_autoresearch_recovery import atomic
    profiles = list(context.get("allowed_profiles", {}))
    count = min(int(context["requested_count"]), len(profiles))
    if not count:
        return []
    counts = context.get("profile_search_counts", {})
    used = set(context.get("profiles_already_requested", []))
    selected = sorted((p for p in profiles if p not in used),
                      key=lambda p: (counts.get(p, 0) + context.get("diversity_memory", {}).get(
                          "profile_penalties", {}).get(p, 0), profiles.index(p)))[:count]
    count = len(selected)
    if not count:
        return []
    requests = []
    global_focus_counts = {key: sum(bucket.get(key, 0) for bucket in
                           context.get("profile_focus_counts", {}).values()) for key in MECHANISM_FOCI}
    assigned_foci = set()
    for i, profile in enumerate(selected):
        lane = Path(directory) / f"lane_{i + 1}_{profile}"
        lane.mkdir(exist_ok=True)
        focus_counts = context.get("profile_focus_counts", {}).get(profile, {})
        focus_penalties = context.get("diversity_memory", {}).get("focus_penalties", {}).get(profile, {})
        eligible = eligible_foci(context["allowed_profiles"][profile])
        # Source rotation alone can repeatedly request the same channel. Prefer
        # different supported questions in this batch and globally under-searched
        # questions, then balance the source-specific effort. No outcome filtering.
        focus = min(eligible, key=lambda k: (k in assigned_foci,
                    global_focus_counts[k] + focus_penalties.get(k, 0), focus_counts.get(k, 0)))
        assigned_foci.add(focus)
        global_focus_counts[focus] += 1
        request = {**context, "requested_count": 1,
                   "allowed_profiles": {profile: context["allowed_profiles"][profile]},
                   "feature_diagnostics": {profile: context.get("feature_diagnostics", {}).get(profile, {})},
                   "source_focus": profile,
                   "mechanism_focus": {"key": focus, "search_question": MECHANISM_FOCI[focus]},
                   "eligible_search_questions": {k: MECHANISM_FOCI[k] for k in eligible},
                   "search_task": "Find one distinct economic mechanism from this source's actual panels. "
                       "Compare its measurement and channel with global historical definitions. A new "
                       "source or family name alone is not novelty. Use diagnostics to avoid constant "
                       "or jointly unavailable member scores. Do not require strong expected IC; "
                       "freeze an economically justified direction before labels. Return empty if "
                       "only tested variants remain; do not rename a historical mechanism. The mechanism_focus "
                       "is a search aid, not a mandatory family or a claim of novelty. If infeasible with "
                       "these panels, explore another justified channel; do not invent missing inputs. "
                       "For path/recovery questions use only completed observations through D, never a "
                       "future recovery endpoint. Explain which observable distinction from the nearest "
                       "historical formula this channel adds. A listed question is not proof of novelty."}
        requests.append((request, lane))
    results, errors = [], []
    with ThreadPoolExecutor(max_workers=count) as pool:
        futures = [pool.submit(plan_families, request, lane, model) for request, lane in requests]
        for (request, lane), future in zip(requests, futures):
            try:
                specs = [{**spec, "search_focus": request["mechanism_focus"]["key"]}
                         for spec in future.result()]
                results.append({"profile": request["source_focus"],
                                "mechanism_focus": request["mechanism_focus"]["key"], "specs": specs})
            except (ValueError, RuntimeError, TimeoutError) as exc:
                errors.append(exc)
                results.append({"profile": request["source_focus"], "specs": [],
                                "mechanism_focus": request["mechanism_focus"]["key"],
                                "error": str(exc), "service_error": isinstance(exc, (RuntimeError, TimeoutError))})
    atomic(Path(directory) / "planning_lanes.json", {"policy": "source_mechanism_v3", "lanes": results})
    if errors and len(errors) == count and all(isinstance(e, (RuntimeError, TimeoutError)) for e in errors):
        raise RuntimeError("all profile planning services failed: " + str(errors[0]))
    # Different sources may describe the same mechanism: collapse exact keys now;
    # semantic aliases still pass through the existing canonical-family review.
    unique = {}
    for result in results:
        for spec in result["specs"]:
            unique.setdefault(spec["family_key"], spec)
    return list(unique.values())


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
