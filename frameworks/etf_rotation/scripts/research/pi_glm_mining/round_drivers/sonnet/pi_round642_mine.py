#!/usr/bin/env python3
"""Round 642 driver: S42 continuation + closure (main controller
directive, 2026-09-21). round_641 left 8 of the 14-atom no-volume pool
never used as a LEFT leg (VT_AUTOCORR_20, CLOSE5_DAY_CONSIST_20,
NOISE_VAR_20, D1_LEVEL_60, ON_STREAK_UF_COV_20, SAMPEN_RET_20,
MSPE_15M_20, REL_UNDERWATER_CATEGORY_20) and reported "25 legal
remaining pairs" -- but that count only checked each pair independently
for "at least one fresh-left side + right has spare capacity", without
accounting for multiple candidate pairs COMPETING for the same
right-leg's remaining slots. Redone here with an actual greedy
allocation (respecting round_641's already-consumed right-leg counts):
only 9 pairs can legally be registered before every remaining right leg
hits its <=3-distinct-left-partners cap. 9 < 12, so this batch also
closes S42."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_642"

_REL_UW_CAT = {"name": "REL_UNDERWATER_CATEGORY_20", "source": "mechanism_atoms_v2"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_CLOSE5 = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_ON_STREAK_UF = {"name": "ON_STREAK_UF_COV_20", "source": "overnight_intraday_mismatch_v1"}
_UWF_Z = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}
_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}

base.CANDIDATES = [
    {"id": "S42P27", "operator": "rank_spread", "left": _REL_UW_CAT, "right": _D1_LEVEL,
     "mechanism": "s42_p27", "hypothesis": "类别内相对水下占比 × 价格延迟D1水平。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P28", "operator": "rank_spread", "left": _CLOSE5, "right": _VT_AUTOCORR,
     "mechanism": "s42_p28", "hypothesis": "尾5分钟方向一致率 × 成交量时间自相关。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P29", "operator": "rank_spread", "left": _REL_UW_CAT, "right": _ON_STREAK_UF,
     "mechanism": "s42_p29", "hypothesis": "类别内相对水下占比 × 隔夜符号-水下占比协方差。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P30", "operator": "rank_spread", "left": _REL_UW_CAT, "right": _UWF_Z,
     "mechanism": "s42_p30", "hypothesis": "类别内相对水下占比 × 水下占比60日z分数（类别内相对水下占比用满3条右腿配额）。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P31", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _NOISE_VAR,
     "mechanism": "s42_p31", "hypothesis": "成交量时间自相关 × 噪声方差。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P32", "operator": "rank_spread", "left": _CLOSE5, "right": _D1_LEVEL,
     "mechanism": "s42_p32", "hypothesis": "尾5分钟方向一致率 × 价格延迟D1水平。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P33", "operator": "rank_spread", "left": _SAMPEN, "right": _VT_AUTOCORR,
     "mechanism": "s42_p33", "hypothesis": "收益样本熵 × 成交量时间自相关。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P34", "operator": "rank_spread", "left": _ON_STREAK_UF, "right": _VT_AUTOCORR,
     "mechanism": "s42_p34", "hypothesis": "隔夜符号-水下占比协方差 × 成交量时间自相关（VT_AUTOCORR_20 用满3条右腿配额）。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P35", "operator": "rank_spread", "left": _NOISE_VAR, "right": _D1_LEVEL,
     "mechanism": "s42_p35", "hypothesis": "噪声方差 × 价格延迟D1水平（本批末条，D1_LEVEL_60 用满3条右腿配额）。方向由发现期定。", "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
