#!/usr/bin/env python3
"""Round 682 driver: S67 pairing-space closeout (main controller directive,
2026-09-21). round_681 gave all 8 mechanism_atoms_v7_split_volume atoms
their first pairing (2 lefts per right leg, 4 right legs: UNDERWATER_FRAC_
CHG_20, PERM_ENTROPY_RET_20, ULCER_INDEX_20, GAP_DD_CONSUMPTION_RATIO_20),
1 admission (S67P_VOLSPIKE_MAXDD_SPLIT_20).

This round closes the remaining 1-slot-each capacity on all 4 preferred
right legs, assigning them to the atoms that showed the strongest
discovery signal in round_681 (excluding repeats of the same left-right
pair already tested): BIGBARVOL_NOISECHG_SPLIT_20 x UNDERWATER_FRAC_
CHG_20 (disc t=1.81 atom, fresh combo), VOLSPIKE_ONGAP_SPLIT_20 x PERM_
ENTROPY_RET_20 (disc t=2.35 atom, fresh combo), MFIEXT_MAXDD_SPLIT_20 x
ULCER_INDEX_20 (disc t=2.02 atom, fresh combo -- its round_681 pairing
had a sign-flipped audit), MFIEXT_ONGAP_SPLIT_20 x GAP_DD_CONSUMPTION_
RATIO_20 (fresh combo). After this round all 4 preferred right legs are
at their 3-left cap -> 0 legal pairs remain on the directive-named right
legs; S67 pairing space exhausted."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_682"

_VOLSPIKE_ONGAP = {"name": "VOLSPIKE_ONGAP_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}
_MFIEXT_ONGAP = {"name": "MFIEXT_ONGAP_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}
_MFIEXT_MAXDD = {"name": "MFIEXT_MAXDD_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}
_BIGBARVOL_NOISECHG = {"name": "BIGBARVOL_NOISECHG_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}

_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_ULCER_INDEX = {"name": "ULCER_INDEX_20", "source": "intraday_pain_recovery_1m"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}

_PAIRS = [
    ("S67P2_BIGBARVOL_NOISECHG_UWCHG", _BIGBARVOL_NOISECHG, _UNDERWATER_FRAC_CHG),
    ("S67P2_VOLSPIKE_ONGAP_PERMENT", _VOLSPIKE_ONGAP, _PERM_ENTROPY),
    ("S67P2_MFIEXT_MAXDD_ULCER", _MFIEXT_MAXDD, _ULCER_INDEX),
    ("S67P2_MFIEXT_ONGAP_GAPDD", _MFIEXT_ONGAP, _GAP_DD_CONSUMPTION),
]

CANDIDATES = []
for cid, left, right in _PAIRS:
    CANDIDATES.append({
        "id": cid, "operator": "rank_spread", "left": left, "right": right,
        "mechanism": f"s67_{left['name'].lower()}_x_{right['name'].lower()}_closeout",
        "hypothesis": f"{left['name']} x {right['name']}：S67收官批，填满右腿最后 1 个左腿名额。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
