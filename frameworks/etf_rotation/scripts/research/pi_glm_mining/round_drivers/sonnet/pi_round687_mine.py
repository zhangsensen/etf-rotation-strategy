#!/usr/bin/env python3
"""Round 687 driver: S71 stage (main controller directive, 2026-09-21) --
S64 only split the LEFT leg of its pairs (e.g. PERMENT_TURNOVER_SPLIT_20 x
UNDERWATER_FRAC_CHG_20 unsplit, round_675, audit +49.7bp/t2.45). This
round splits the RIGHT-leg base statistics too (new family mechanism_
atoms_v9_split_right for the 3 atoms that don't already exist: GAPDD_
ONGAP_SPLIT_20B, CBETA_TURNOVER_SPLIT_20, CBETA_ONGAP_SPLIT_20; reuses
UWCHG_TURNOVER_SPLIT_20/UWCHG_ONGAP_SPLIT_20 from S64's mechanism_atoms_
v6_split and GAPDD_TURNOVER_SPLIT_20 from S70's mechanism_atoms_v8_
split_tier2 as-is), and tests same-condition vs different-condition
left x right contrasts for every S64-admitted left atom against its
original (now-split) right-leg base statistic.

Group A as originally planned (PERMENT_TURNOVER_SPLIT_20 x UWCHG_
TURNOVER_SPLIT_20/UWCHG_ONGAP_SPLIT_20, both from mechanism_atoms_v6_
split) turned out IMPOSSIBLE: cmd_plan hard-asserts cross_family_only
on the atom's own declared `family` field (yaml-level, not just the
`source` module it's registered under), and both atoms share `family:
mechanism_atoms_v6_split` -- this is the exact same-family same-stage
pairing the S71 directive's example (1) proposed, so it cannot be run
as literally worded. Substituted: same-vs-different-condition test now
uses VFPULCER_TURNOVER_SPLIT_20 (S70's mechanism_atoms_v8_split_tier2,
a different family, strongest S70 left atom with 3/3 admissions) against
UWCHG_TURNOVER_SPLIT_20 (same_cond) / UWCHG_ONGAP_SPLIT_20 (diff_cond)
-- preserves the directive's actual intent (same-condition vs different-
condition right-leg contrast) within the engine's hard constraint.

Candidate groups (each S64-admitted left atom x both split versions of
its ORIGINAL unsplit right leg, or the cross-family substitute above):
  Group A' (cross-family substitute for UNDERWATER_FRAC_CHG_20 split):
    VFPULCER_TURNOVER_SPLIT_20 (mechanism_atoms_v8_split_tier2)
  Group B (orig right = GAP_DD_CONSUMPTION_RATIO_20, round_673 pairs):
    UWCHG_ONGAP_SPLIT_20, LUNCHPR_ONGAP_SPLIT_20, ULCER_TURNOVER_SPLIT_20
  Group C (orig right = CONTINUOUS_BETA_60, round_673 pairs):
    PERMENT_TURNOVER_SPLIT_20, UWCHG_TURNOVER_SPLIT_20, ULCER_NOISERATIO_SPLIT_20

Pairing discipline (S71 is a new stage, counters reset per left/right
role separately -- an atom used as LEFT in one pair and RIGHT in
another is tracked independently per role, since the whole point of
this stage is reusing already-split atoms as right legs regardless of
their history as left legs elsewhere): every left atom <=2 pairings
(room for a 3rd, not required to fill), every right atom exactly 3
pairings for the 4 split atoms with >=3 available slots (GAPDD_
ONGAP_SPLIT_20B, GAPDD_TURNOVER_SPLIT_20, CBETA_TURNOVER_SPLIT_20,
CBETA_ONGAP_SPLIT_20) and 1 each for UWCHG_TURNOVER_SPLIT_20/UWCHG_
ONGAP_SPLIT_20 used as right legs. 14 total candidates (>=12 floor)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_687"

_PERMENT_TURNOVER = {"name": "PERMENT_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_UWCHG_ONGAP = {"name": "UWCHG_ONGAP_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_LUNCHPR_ONGAP = {"name": "LUNCHPR_ONGAP_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_ULCER_TURNOVER = {"name": "ULCER_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_UWCHG_TURNOVER = {"name": "UWCHG_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_ULCER_NOISERATIO = {"name": "ULCER_NOISERATIO_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_VFPULCER_TURNOVER = {"name": "VFPULCER_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}

_GAPDD_TURNOVER = {"name": "GAPDD_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_GAPDD_ONGAP_B = {"name": "GAPDD_ONGAP_SPLIT_20B", "source": "mechanism_atoms_v9_split_right"}
_CBETA_TURNOVER = {"name": "CBETA_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v9_split_right"}
_CBETA_ONGAP = {"name": "CBETA_ONGAP_SPLIT_20", "source": "mechanism_atoms_v9_split_right"}

_PAIRS = [
    # Group A': cross-family substitute for the UNDERWATER_FRAC_CHG_20-split
    # same-vs-diff-condition test (VFPULCER_TURNOVER_SPLIT_20 is mechanism_
    # atoms_v8_split_tier2, cross-family with UWCHG_*'s mechanism_atoms_v6_split)
    (_VFPULCER_TURNOVER, _UWCHG_TURNOVER, "same_cond_turnover"),
    (_VFPULCER_TURNOVER, _UWCHG_ONGAP, "diff_cond"),
    # Group B: orig right = GAP_DD_CONSUMPTION_RATIO_20 (round_673) -> split
    # into GAPDD_TURNOVER_SPLIT_20 (S70) / GAPDD_ONGAP_SPLIT_20B (new)
    (_UWCHG_ONGAP, _GAPDD_ONGAP_B, "same_cond_ongap"),
    (_UWCHG_ONGAP, _GAPDD_TURNOVER, "diff_cond"),
    (_LUNCHPR_ONGAP, _GAPDD_ONGAP_B, "same_cond_ongap"),
    (_LUNCHPR_ONGAP, _GAPDD_TURNOVER, "diff_cond"),
    (_ULCER_TURNOVER, _GAPDD_TURNOVER, "same_cond_turnover"),
    (_ULCER_TURNOVER, _GAPDD_ONGAP_B, "diff_cond"),
    # Group C: orig right = CONTINUOUS_BETA_60 (round_673) -> split into
    # CBETA_TURNOVER_SPLIT_20 (new) / CBETA_ONGAP_SPLIT_20 (new)
    (_PERMENT_TURNOVER, _CBETA_TURNOVER, "same_cond_turnover"),
    (_PERMENT_TURNOVER, _CBETA_ONGAP, "diff_cond"),
    (_UWCHG_TURNOVER, _CBETA_TURNOVER, "same_cond_turnover"),
    (_UWCHG_TURNOVER, _CBETA_ONGAP, "diff_cond"),
    (_ULCER_NOISERATIO, _CBETA_TURNOVER, "diff_cond_noiseratio_vs_turnover"),
    (_ULCER_NOISERATIO, _CBETA_ONGAP, "diff_cond_noiseratio_vs_ongap"),
]

CANDIDATES = []
for left, right, tag in _PAIRS:
    CANDIDATES.append({
        "id": f"S71_{left['name']}_{right['name']}",
        "operator": "rank_spread", "left": left, "right": right,
        "mechanism": f"s71_{left['name'].lower()}_x_{right['name'].lower()}_{tag}",
        "hypothesis": f"{left['name']} x {right['name']}：S64 原对右腿拆分后的{tag}对照。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
