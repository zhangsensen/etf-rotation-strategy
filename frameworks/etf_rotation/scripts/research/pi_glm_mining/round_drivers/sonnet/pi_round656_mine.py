#!/usr/bin/env python3
"""Round 656 driver: S54 stage (main controller directive, 2026-09-21) --
deepen the category-relative water-occupancy-change mechanism (S32P1's
REL_UNDERWATER_CATEGORY_CHG_20 x R_LOG_AMOUNT_VOL_20 was +74.0bp/t4.16
under pi's independent reproduction). Two genuinely new atoms added to
category_relative_geometry: REL_ULCER_CATEGORY_CHG_20,
REL_RECOVERY_TIME_CATEGORY_CHG_20. The directive's other two "atoms"
(REL_UNDERWATER_CATEGORY_CHG_20 itself, and the full-basket-relative
REL_UNDERWATER_FRAC_CHG_20) were ALREADY single-atom gate-7
re-adjudicated in round_631 (S32A1, rejected: rank_correlation_redundancy
vs prior:round_545:QA8, corr 0.83) and round_571 (NA2, rejected:
topk_gate, t=0.87) respectively -- re-registering them would hit the
engine's duplicate-canonical-hash guard, so they are cited directly in
REPORT.md's three-column comparison table instead of re-run.

Pairing discipline (standing 2026-09-20 17:00 rule): each new atom as
left leg gets exactly one batch (<=8 right legs, cross-family, matches
category_relative_geometry's pair_policy=cross_family_only) this stage.
Right-leg pool prioritizes the directive's three named atoms
(R_LOG_AMOUNT_VOL_20, MFI_EXTREME_FRAC_20, GAP_DD_CONSUMPTION_RATIO_20)
plus five other established cross-family atoms, shared across both left
legs (each right leg used with only 2 left legs total, under the <=3
cap)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_656"

_REL_ULCER_CHG = {"name": "REL_ULCER_CATEGORY_CHG_20", "source": "category_relative_geometry"}
_REL_RECOVERY_CHG = {"name": "REL_RECOVERY_TIME_CATEGORY_CHG_20", "source": "category_relative_geometry"}

_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_YZ_OVERNIGHT_SHARE = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}

_RIGHT_LEG_POOL = [
    ("A", _R_LOG_AMOUNT_VOL),
    ("B", _MFI_EXTREME_FRAC),
    ("C", _GAP_DD_CONSUMPTION),
    ("D", _PERM_ENTROPY),
    ("E", _YZ_OVERNIGHT_SHARE),
    ("F", _CONTINUOUS_BETA),
    ("G", _VT_AUTOCORR),
    ("H", _RESILIENCY),
]

CANDIDATES = [
    {"id": "S54A1", "operator": "atomic", "left": _REL_ULCER_CHG, "right": _REL_ULCER_CHG,
     "mechanism": "s54_rel_ulcer_category_chg_atomic",
     "hypothesis": "类内相对溃疡指数(Ulcer Index)变化：本ETF相对同sleeve同伴的Ulcer Index水平之差，20日变化。"
                   "与REL_UNDERWATER_CATEGORY_CHG_20同一参照系(类内相对)但用RMS回撤幅度而非水下占比。"
                   "体检:与ULCER_INDEX_CHG_20 corr=0.838(shadow,同源派生预期高)，与REL_UNDERWATER_CATEGORY_CHG_20 corr=0.31(独立)。",
     "expected_sign": -1},
    {"id": "S54A2", "operator": "atomic", "left": _REL_RECOVERY_CHG, "right": _REL_RECOVERY_CHG,
     "mechanism": "s54_rel_recovery_time_category_chg_atomic",
     "hypothesis": "类内相对恢复时间占比变化：REL_RECOVERY_TIME_CATEGORY_20(S32已建,仅水平)首次做20日差分。"
                   "体检:与自身水平corr=0.52，与RECOVERY_TIME_FRAC_20 corr=0.48，均<0.7无shadow。",
     "expected_sign": -1},
]

for tag, right in _RIGHT_LEG_POOL:
    CANDIDATES.append({
        "id": f"S54P_ULCER_{tag}", "operator": "rank_spread", "left": _REL_ULCER_CHG, "right": right,
        "mechanism": f"s54_rel_ulcer_chg_x_{right['name'].lower()}",
        "hypothesis": f"REL_ULCER_CATEGORY_CHG_20 x {right['name']}：类内相对回撤幅度变化配{right['name']}，"
                      "沿S29P10/S32P1(类内相对水下×资金/量能腿)机制加深，换用Ulcer Index口径。",
        "expected_sign": -1,
    })

for tag, right in _RIGHT_LEG_POOL:
    CANDIDATES.append({
        "id": f"S54P_RECOV_{tag}", "operator": "rank_spread", "left": _REL_RECOVERY_CHG, "right": right,
        "mechanism": f"s54_rel_recovery_chg_x_{right['name'].lower()}",
        "hypothesis": f"REL_RECOVERY_TIME_CATEGORY_CHG_20 x {right['name']}：类内相对恢复速度变化配{right['name']}。",
        "expected_sign": -1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
