#!/usr/bin/env python3
"""Round 685 driver: S70 stage (main controller directive, 2026-09-21) --
extend the split construct (S64/S67) to a second tier of no-volume
representative atoms not yet split: LUNCH_PRE_RUN_20 (CJ16's leg),
R_VFP_ULCER_SHIFT_20 (DD48's leg), RESILIENCY_20, GAP_DD_CONSUMPTION_
RATIO_20, CLOSE5_DAY_CONSIST_20. New family `mechanism_atoms_v8_split_
tier2` (8 atoms; see family docstring for the 5 base statistics x 4
conditions design, each statistic <=2 conditions).

atom_health (outputs/round_685/atom_health.csv, run before this driver)
confirms all 8 atoms clean: max |corr vs unsplit original| = 0.1041
(RESIL_AMIHUD_SPLIT_20 vs RESILIENCY_20), max |corr vs ret1| = 0.0664,
max |corr vs ret20| = 0.0854 (VFPULCER_NOISECHG_SPLIT_20) -- all far
under the 0.7 shadow/E30 thresholds.

Pairing: first batch, one right leg each, distributed across the
directive-preferred right legs (UNDERWATER_FRAC_CHG_20, PERM_ENTROPY_
RET_20, CONTINUOUS_BETA_60, R2_VOL_SPIKE_FREQ_20), 2 lefts per right
leg (well under the 3-left cap)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_685"

_LUNCHPR_TURNOVER = {"name": "LUNCHPR_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_LUNCHPR_ONGAP_B = {"name": "LUNCHPR_ONGAP_SPLIT_20B", "source": "mechanism_atoms_v8_split_tier2"}
_VFPULCER_TURNOVER = {"name": "VFPULCER_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_VFPULCER_NOISECHG = {"name": "VFPULCER_NOISECHG_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_RESIL_ONGAP = {"name": "RESIL_ONGAP_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_RESIL_AMIHUD = {"name": "RESIL_AMIHUD_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_GAPDD_TURNOVER = {"name": "GAPDD_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_CLOSE5_NOISECHG = {"name": "CLOSE5_NOISECHG_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}

_ATOMS = [
    _LUNCHPR_TURNOVER, _LUNCHPR_ONGAP_B, _VFPULCER_TURNOVER, _VFPULCER_NOISECHG,
    _RESIL_ONGAP, _RESIL_AMIHUD, _GAPDD_TURNOVER, _CLOSE5_NOISECHG,
]

_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_R2_VOL_SPIKE_FREQ = {"name": "R2_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_v2a"}

_PAIR_RIGHT_LEG = {
    "LUNCHPR_TURNOVER_SPLIT_20": _UNDERWATER_FRAC_CHG,
    "GAPDD_TURNOVER_SPLIT_20": _UNDERWATER_FRAC_CHG,
    "VFPULCER_TURNOVER_SPLIT_20": _PERM_ENTROPY,
    "CLOSE5_NOISECHG_SPLIT_20": _PERM_ENTROPY,
    "LUNCHPR_ONGAP_SPLIT_20B": _CONTINUOUS_BETA,
    "RESIL_ONGAP_SPLIT_20": _CONTINUOUS_BETA,
    "VFPULCER_NOISECHG_SPLIT_20": _R2_VOL_SPIKE_FREQ,
    "RESIL_AMIHUD_SPLIT_20": _R2_VOL_SPIKE_FREQ,
}

CANDIDATES = []
for atom in _ATOMS:
    CANDIDATES.append({
        "id": f"S70A_{atom['name']}", "operator": "atomic", "left": atom, "right": atom,
        "mechanism": f"s70_{atom['name'].lower()}_atomic",
        "hypothesis": f"S64/S67拆分构造施于第二梯队无量代表原子：{atom['name']}。",
        "expected_sign": 1,
    })

for atom in _ATOMS:
    right = _PAIR_RIGHT_LEG[atom["name"]]
    CANDIDATES.append({
        "id": f"S70P_{atom['name']}", "operator": "rank_spread", "left": atom, "right": right,
        "mechanism": f"s70_{atom['name'].lower()}_x_{right['name'].lower()}",
        "hypothesis": f"{atom['name']} x {right['name']}：第二梯队拆分原子配右腿首批。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
