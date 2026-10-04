#!/usr/bin/env python3
"""Round 681 driver: S67 stage (main controller directive, 2026-09-21) --
extend S64's split construct to volume-channel atoms. New family
`mechanism_atoms_v7_split_volume` (8 atoms; see family docstring for the
5 base statistics x 4 conditions design, each statistic <=2 conditions).

atom_health (outputs/round_681/atom_health.csv, run before this driver)
confirms all 8 atoms clean: max |corr vs unsplit original| = 0.136
(MFIEXT_MAXDD_SPLIT_20 vs MFI_EXTREME_FRAC_20), max |corr vs ret1| = 0.085
(R2VOLAC_AMIHUD_SPLIT_20) -- both far under the 0.7 shadow/E30 thresholds.

Pairing: first batch, one right leg each, distributed across the 4
directive-preferred no-volume right legs (UNDERWATER_FRAC_CHG_20,
PERM_ENTROPY_RET_20, ULCER_INDEX_20, GAP_DD_CONSUMPTION_RATIO_20), 2
lefts per right leg (well under the 3-left cap, leaving room for a
follow-up batch if this stage isn't closed out by pairing discipline)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_681"

_VOLSPIKE_ONGAP = {"name": "VOLSPIKE_ONGAP_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}
_VOLSPIKE_MAXDD = {"name": "VOLSPIKE_MAXDD_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}
_VTAC_NOISECHG = {"name": "VTAC_NOISECHG_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}
_VTAC_AMIHUD = {"name": "VTAC_AMIHUD_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}
_MFIEXT_ONGAP = {"name": "MFIEXT_ONGAP_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}
_MFIEXT_MAXDD = {"name": "MFIEXT_MAXDD_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}
_BIGBARVOL_NOISECHG = {"name": "BIGBARVOL_NOISECHG_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}
_R2VOLAC_AMIHUD = {"name": "R2VOLAC_AMIHUD_SPLIT_20", "source": "mechanism_atoms_v7_split_volume"}

_ATOMS = [
    _VOLSPIKE_ONGAP, _VOLSPIKE_MAXDD, _VTAC_NOISECHG, _VTAC_AMIHUD,
    _MFIEXT_ONGAP, _MFIEXT_MAXDD, _BIGBARVOL_NOISECHG, _R2VOLAC_AMIHUD,
]

_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_ULCER_INDEX = {"name": "ULCER_INDEX_20", "source": "intraday_pain_recovery_1m"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}

_PAIR_RIGHT_LEG = {
    "VOLSPIKE_ONGAP_SPLIT_20": _UNDERWATER_FRAC_CHG,
    "MFIEXT_ONGAP_SPLIT_20": _UNDERWATER_FRAC_CHG,
    "VOLSPIKE_MAXDD_SPLIT_20": _PERM_ENTROPY,
    "MFIEXT_MAXDD_SPLIT_20": _PERM_ENTROPY,
    "VTAC_NOISECHG_SPLIT_20": _ULCER_INDEX,
    "BIGBARVOL_NOISECHG_SPLIT_20": _ULCER_INDEX,
    "VTAC_AMIHUD_SPLIT_20": _GAP_DD_CONSUMPTION,
    "R2VOLAC_AMIHUD_SPLIT_20": _GAP_DD_CONSUMPTION,
}

CANDIDATES = []
for atom in _ATOMS:
    CANDIDATES.append({
        "id": f"S67A_{atom['name']}", "operator": "atomic", "left": atom, "right": atom,
        "mechanism": f"s67_{atom['name'].lower()}_atomic",
        "hypothesis": f"S64拆分构造施于量通道原子：{atom['name']}。",
        "expected_sign": 1,
    })

for atom in _ATOMS:
    right = _PAIR_RIGHT_LEG[atom["name"]]
    CANDIDATES.append({
        "id": f"S67P_{atom['name']}", "operator": "rank_spread", "left": atom, "right": right,
        "mechanism": f"s67_{atom['name'].lower()}_x_{right['name'].lower()}",
        "hypothesis": f"{atom['name']} x {right['name']}：量通道拆分原子配无量右腿首批。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
