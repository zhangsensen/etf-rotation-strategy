#!/usr/bin/env python3
"""Round 658 driver: S54 stage continuation (main controller directive,
2026-09-21). Main controller rejected round_657's stage-exhaustion claim:
"REJECT op_ok=True three_zero=False space_exhausted=False
used=['atomic', 'rank_spread']" -- the S54 left legs had only been
tested with the rank_spread operator (rank(a)-rank(b)); the
rank_interaction operator (rank(a)*rank(b)) was never tried, so the
operator space for this family/stage was not actually exhausted.
Per the controller's explicit instruction ("先实现并验证阶段算子；只有
连续3轮门7零入选才算穷尽"), this round registers rank_interaction
versions of the 3 already rank_spread-tested S54 left legs
(REL_ULCER_CATEGORY_CHG_20, REL_RECOVERY_TIME_CATEGORY_CHG_20,
REL_UNDERWATER_CATEGORY_CHG_20) against the same right-leg pools used
in round_656/657 -- these are genuinely new canonical expressions
(different operator = different hash), not duplicates."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_658"

_REL_ULCER_CHG = {"name": "REL_ULCER_CATEGORY_CHG_20", "source": "category_relative_geometry"}
_REL_RECOVERY_CHG = {"name": "REL_RECOVERY_TIME_CATEGORY_CHG_20", "source": "category_relative_geometry"}
_REL_UW_CHG = {"name": "REL_UNDERWATER_CATEGORY_CHG_20", "source": "category_relative_geometry"}

_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_YZ_OVERNIGHT_SHARE = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_ON_SIGN_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}
_R_VOL_SPIKE_FREQ = {"name": "R_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_a"}

_POOL_ULCER_RECOV = [
    ("A", _R_LOG_AMOUNT_VOL), ("B", _MFI_EXTREME_FRAC), ("C", _GAP_DD_CONSUMPTION),
    ("D", _PERM_ENTROPY), ("E", _YZ_OVERNIGHT_SHARE), ("F", _CONTINUOUS_BETA),
    ("G", _VT_AUTOCORR), ("H", _RESILIENCY),
]
_POOL_UWCAT = [
    ("A", _GAP_DD_CONSUMPTION), ("B", _CONTINUOUS_BETA), ("C", _VT_AUTOCORR),
    ("D", _PERM_ENTROPY), ("E", _YZ_OVERNIGHT_SHARE), ("F", _RESILIENCY),
    ("G", _ON_SIGN_STREAK), ("H", _R_VOL_SPIKE_FREQ),
]

CANDIDATES = []
for tag, right in _POOL_ULCER_RECOV:
    CANDIDATES.append({
        "id": f"S54I_ULCER_{tag}", "operator": "rank_interaction", "left": _REL_ULCER_CHG, "right": right,
        "mechanism": f"s54_interaction_rel_ulcer_chg_x_{right['name'].lower()}",
        "hypothesis": f"rank_interaction(REL_ULCER_CATEGORY_CHG_20, {right['name']})：round_656 只测过 rank_spread"
                      "（差值）方向，本轮补测 rank_interaction（乘积）算子，检验该左腿的信息是否是条件化"
                      "（乘积捕捉的是二者同时处于极端的联合效应，而非相对排序差）。",
        "expected_sign": 1,
    })
for tag, right in _POOL_ULCER_RECOV:
    CANDIDATES.append({
        "id": f"S54I_RECOV_{tag}", "operator": "rank_interaction", "left": _REL_RECOVERY_CHG, "right": right,
        "mechanism": f"s54_interaction_rel_recovery_chg_x_{right['name'].lower()}",
        "hypothesis": f"rank_interaction(REL_RECOVERY_TIME_CATEGORY_CHG_20, {right['name']})：round_656 该左腿"
                      "rank_spread 8/8 全拒；补测乘积算子作为算子空间穷尽的最后确认。",
        "expected_sign": 1,
    })
for tag, right in _POOL_UWCAT:
    CANDIDATES.append({
        "id": f"S54I_UWCAT_{tag}", "operator": "rank_interaction", "left": _REL_UW_CHG, "right": right,
        "mechanism": f"s54_interaction_rel_underwater_category_chg_x_{right['name'].lower()}",
        "hypothesis": f"rank_interaction(REL_UNDERWATER_CATEGORY_CHG_20, {right['name']})：round_657 该左腿"
                      "rank_spread 已配满且 2 条高t因冗余被拒；补测乘积算子。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
