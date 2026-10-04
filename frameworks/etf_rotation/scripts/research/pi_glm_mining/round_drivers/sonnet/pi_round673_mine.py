#!/usr/bin/env python3
"""Round 673 driver: S64 stage (main controller directive, 2026-09-21) --
apply S60's only productive construct this stage (conditional-split
difference) to this line's no-volume representative atoms. New family
mechanism_atoms_v6_split (8 atoms, reusing S36's split helpers verbatim,
applied to UNDERWATER_FRAC_CHG_20, PERM_ENTROPY_RET_20,
LUNCH_POST_RUN_20, ULCER_INDEX_20, YZ_OVERNIGHT_SHARE_20 -- see the
family docstring for exact construction).

S64A1-A8: single-atom gate-7 re-adjudication for all 8 new atoms.

S64P_*: pairing batch, one pair per new atom (respecting pairing
discipline), using the 3 right legs S60 already proved effective
(CONTINUOUS_BETA_60, GAP_DD_CONSUMPTION_RATIO_20, ULCER_INDEX_20), each
landing exactly at the <=3-lefts-per-right-leg cap. ULCER_INDEX_20 is
deliberately NOT paired with the two ULCER_INDEX_20-derived atoms
(ULCER_NOISERATIO_SPLIT_20 / ULCER_TURNOVER_SPLIT_20) to avoid a
near-tautological right leg."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_673"

_UWCHG_TURNOVER = {"name": "UWCHG_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_UWCHG_ONGAP = {"name": "UWCHG_ONGAP_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_PERMENT_TURNOVER = {"name": "PERMENT_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_PERMENT_AMIHUD = {"name": "PERMENT_AMIHUD_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_LUNCHPR_ONGAP = {"name": "LUNCHPR_ONGAP_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_ULCER_NOISERATIO = {"name": "ULCER_NOISERATIO_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_ULCER_TURNOVER = {"name": "ULCER_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_YZSHARE_AMIHUD = {"name": "YZSHARE_AMIHUD_SPLIT_20", "source": "mechanism_atoms_v6_split"}

_ATOMS = [
    _UWCHG_TURNOVER, _UWCHG_ONGAP, _PERMENT_TURNOVER, _PERMENT_AMIHUD,
    _LUNCHPR_ONGAP, _ULCER_NOISERATIO, _ULCER_TURNOVER, _YZSHARE_AMIHUD,
]

_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_ULCER_INDEX = {"name": "ULCER_INDEX_20", "source": "intraday_pain_recovery_1m"}

CANDIDATES = []
for atom in _ATOMS:
    CANDIDATES.append({
        "id": f"S64A_{atom['name']}", "operator": "atomic", "left": atom, "right": atom,
        "mechanism": f"s64_{atom['name'].lower()}_atomic",
        "hypothesis": f"S60条件切分构造应用于无量代表原子：{atom['name']}。",
        "expected_sign": 1,
    })

_PAIR_RIGHT_LEG = {
    "UWCHG_TURNOVER_SPLIT_20": _CONTINUOUS_BETA,
    "UWCHG_ONGAP_SPLIT_20": _GAP_DD_CONSUMPTION,
    "PERMENT_TURNOVER_SPLIT_20": _CONTINUOUS_BETA,
    "PERMENT_AMIHUD_SPLIT_20": _ULCER_INDEX,
    "LUNCHPR_ONGAP_SPLIT_20": _GAP_DD_CONSUMPTION,
    "ULCER_NOISERATIO_SPLIT_20": _CONTINUOUS_BETA,
    "ULCER_TURNOVER_SPLIT_20": _GAP_DD_CONSUMPTION,
    "YZSHARE_AMIHUD_SPLIT_20": _ULCER_INDEX,
}

for atom in _ATOMS:
    right = _PAIR_RIGHT_LEG[atom["name"]]
    CANDIDATES.append({
        "id": f"S64P_{atom['name']}", "operator": "rank_spread", "left": atom, "right": right,
        "mechanism": f"s64_{atom['name'].lower()}_x_{right['name'].lower()}",
        "hypothesis": f"{atom['name']} x {right['name']}：S60已证有效的右腿，配无量条件切分新原子。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
