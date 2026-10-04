#!/usr/bin/env python3
"""Round 629 driver: S31 stage (main controller directive, 2026-09-21) --
deepen S27's GAP_DD_CONSUMPTION_RATIO_20 mechanism (this line's
strongest left leg). New family gap_absorption_path_1m (8 atoms,
self-contained, single 1m pass per symbol).

Small-sample pilot (3 symbols) ran 4.31s; full 14-symbol run
extrapolated ~20s, ran directly without optimization.

Atom health (round_629_atom_health): all 8 atoms corr <0.16 vs their
reference atoms (no shadow flags -- fully independent new slices).
Strongest disc_ic: GAP_DD_DIRECTION_MATCH_CHG_20 (-0.055).

8 atomic tests + 16 pairs (2 right legs per left atom, pairing
discipline respected). Right legs prioritize MFI_EXTREME_FRAC_20 and
UNDERWATER_FRAC_CHG_20 per the directive's explicit instruction
('MFI_EXTREME_FRAC、UNDERWATER_FRAC_CHG 作右腿优先'), each maxed at
their <=3-distinct-left-legs quota; remaining rights are established
atoms not yet used this stage."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_629"

_FILL_TIMING = {"name": "GAP_FILL_TIMING_20", "source": "gap_absorption_path_1m"}
_REMAIN_10AM = {"name": "GAP_REMAIN_10AM_20", "source": "gap_absorption_path_1m"}
_REMAIN_1130 = {"name": "GAP_REMAIN_1130_20", "source": "gap_absorption_path_1m"}
_REMAIN_CLOSE = {"name": "GAP_REMAIN_CLOSE_20", "source": "gap_absorption_path_1m"}
_DD_MATCH = {"name": "GAP_DD_DIRECTION_MATCH_20", "source": "gap_absorption_path_1m"}
_SHARE_RANGE = {"name": "GAP_SHARE_OF_RANGE_20", "source": "gap_absorption_path_1m"}
_FILL_TIMING_CHG = {"name": "GAP_FILL_TIMING_CHG_20", "source": "gap_absorption_path_1m"}
_DD_MATCH_CHG = {"name": "GAP_DD_DIRECTION_MATCH_CHG_20", "source": "gap_absorption_path_1m"}

_MFI_EXTREME = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_UW_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_VT_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}

base.CANDIDATES = [
    # ---- 8 atomic tests ----
    {"id": "S31A1", "operator": "atomic", "left": _FILL_TIMING, "right": _FILL_TIMING,
     "mechanism": "s31_gap_fill_timing_atomic",
     "hypothesis": "GAP_FILL_TIMING_20（跳空首次回补的 bar 位置/全日 bar 数，未回补记 1，20 日均值）单原子门 7 重裁。体检 disc_ic 0.023，corr_vs_ref=0.01（独立）。",
     "expected_sign": 1},
    {"id": "S31A2", "operator": "atomic", "left": _REMAIN_10AM, "right": _REMAIN_10AM,
     "mechanism": "s31_gap_remain_10am_atomic",
     "hypothesis": "GAP_REMAIN_10AM_20（10:00 时点跳空剩余比例，20 日均值）单原子门 7 重裁。体检 disc_ic 0.021，corr_vs_ref=0.05（独立）。",
     "expected_sign": 1},
    {"id": "S31A3", "operator": "atomic", "left": _REMAIN_1130, "right": _REMAIN_1130,
     "mechanism": "s31_gap_remain_1130_atomic",
     "hypothesis": "GAP_REMAIN_1130_20（11:30 收盘时点跳空剩余比例，20 日均值）单原子门 7 重裁。体检 disc_ic −0.009，corr_vs_ref=0.05（独立）。",
     "expected_sign": -1},
    {"id": "S31A4", "operator": "atomic", "left": _REMAIN_CLOSE, "right": _REMAIN_CLOSE,
     "mechanism": "s31_gap_remain_close_atomic",
     "hypothesis": "GAP_REMAIN_CLOSE_20（收盘时点跳空剩余比例，20 日均值）单原子门 7 重裁。体检 disc_ic 0.022，corr_vs_ref=0.03（独立）。",
     "expected_sign": 1},
    {"id": "S31A5", "operator": "atomic", "left": _DD_MATCH, "right": _DD_MATCH,
     "mechanism": "s31_gap_dd_direction_match_atomic",
     "hypothesis": "GAP_DD_DIRECTION_MATCH_20（跳空方向与日内最大回撤起点一致率，20 日均值）单原子门 7 重裁。体检 disc_ic −0.009，与 ON_TROUGH_RECOVERY_MATCH_20 corr=−0.15（独立）。",
     "expected_sign": -1},
    {"id": "S31A6", "operator": "atomic", "left": _SHARE_RANGE, "right": _SHARE_RANGE,
     "mechanism": "s31_gap_share_of_range_atomic",
     "hypothesis": "GAP_SHARE_OF_RANGE_20（|跳空|/全日区间，20 日均值）单原子门 7 重裁。体检 disc_ic 0.016，corr_vs_ref=−0.08（独立）。",
     "expected_sign": 1},
    {"id": "S31A7", "operator": "atomic", "left": _FILL_TIMING_CHG, "right": _FILL_TIMING_CHG,
     "mechanism": "s31_gap_fill_timing_chg_atomic",
     "hypothesis": "GAP_FILL_TIMING_CHG_20（回补位置 20 日变化）单原子门 7 重裁。体检 disc_ic 0.007，corr_vs_ref=−0.12（独立）。",
     "expected_sign": 1},
    {"id": "S31A8", "operator": "atomic", "left": _DD_MATCH_CHG, "right": _DD_MATCH_CHG,
     "mechanism": "s31_gap_dd_direction_match_chg_atomic",
     "hypothesis": "GAP_DD_DIRECTION_MATCH_CHG_20（回撤起点一致率 20 日变化）单原子门 7 重裁。体检 disc_ic −0.055（本批最强），corr_vs_ref=−0.02（独立）。",
     "expected_sign": -1},
    # ---- 16 pairs (2 right legs per left atom, MFI_EXTREME_FRAC/UNDERWATER_FRAC_CHG prioritized) ----
    {"id": "S31P1", "operator": "rank_spread", "left": _DD_MATCH_CHG, "right": _MFI_EXTREME,
     "mechanism": "s31_p1", "hypothesis": "GAP_DD_DIRECTION_MATCH_CHG_20 × MFI_EXTREME_FRAC_20（主控指定优先右腿）。方向由发现期定。", "expected_sign": -1},
    {"id": "S31P2", "operator": "rank_spread", "left": _DD_MATCH_CHG, "right": _UW_CHG,
     "mechanism": "s31_p2", "hypothesis": "GAP_DD_DIRECTION_MATCH_CHG_20 × UNDERWATER_FRAC_CHG_20（主控指定优先右腿，本线历史最强单原子）。方向由发现期定。", "expected_sign": -1},
    {"id": "S31P3", "operator": "rank_spread", "left": _FILL_TIMING, "right": _MFI_EXTREME,
     "mechanism": "s31_p3", "hypothesis": "GAP_FILL_TIMING_20 × MFI_EXTREME_FRAC_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31P4", "operator": "rank_spread", "left": _FILL_TIMING, "right": _UW_CHG,
     "mechanism": "s31_p4", "hypothesis": "GAP_FILL_TIMING_20 × UNDERWATER_FRAC_CHG_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31P5", "operator": "rank_spread", "left": _REMAIN_CLOSE, "right": _MFI_EXTREME,
     "mechanism": "s31_p5", "hypothesis": "GAP_REMAIN_CLOSE_20 × MFI_EXTREME_FRAC_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31P6", "operator": "rank_spread", "left": _REMAIN_CLOSE, "right": _R_ULCER,
     "mechanism": "s31_p6", "hypothesis": "GAP_REMAIN_CLOSE_20 × R_ULCER_20（S26R）。方向由发现期定。", "expected_sign": 1},
    {"id": "S31P7", "operator": "rank_spread", "left": _REMAIN_10AM, "right": _UW_CHG,
     "mechanism": "s31_p7", "hypothesis": "GAP_REMAIN_10AM_20 × UNDERWATER_FRAC_CHG_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31P8", "operator": "rank_spread", "left": _REMAIN_10AM, "right": _D1_LEVEL,
     "mechanism": "s31_p8", "hypothesis": "GAP_REMAIN_10AM_20 × D1_LEVEL_60（S20）。方向由发现期定。", "expected_sign": 1},
    {"id": "S31P9", "operator": "rank_spread", "left": _SHARE_RANGE, "right": _R_ULCER,
     "mechanism": "s31_p9", "hypothesis": "GAP_SHARE_OF_RANGE_20 × R_ULCER_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31P10", "operator": "rank_spread", "left": _SHARE_RANGE, "right": _D1_LEVEL,
     "mechanism": "s31_p10", "hypothesis": "GAP_SHARE_OF_RANGE_20 × D1_LEVEL_60。方向由发现期定。", "expected_sign": 1},
    {"id": "S31P11", "operator": "rank_spread", "left": _FILL_TIMING_CHG, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s31_p11", "hypothesis": "GAP_FILL_TIMING_CHG_20 × R_LOG_AMOUNT_VOL_20（S26R）。方向由发现期定。", "expected_sign": 1},
    {"id": "S31P12", "operator": "rank_spread", "left": _FILL_TIMING_CHG, "right": _VT_GINI,
     "mechanism": "s31_p12", "hypothesis": "GAP_FILL_TIMING_CHG_20 × VT_BUCKET_GINI_20（S24）。方向由发现期定。", "expected_sign": 1},
    {"id": "S31P13", "operator": "rank_spread", "left": _REMAIN_1130, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s31_p13", "hypothesis": "GAP_REMAIN_1130_20 × R_LOG_AMOUNT_VOL_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S31P14", "operator": "rank_spread", "left": _REMAIN_1130, "right": _VT_GINI,
     "mechanism": "s31_p14", "hypothesis": "GAP_REMAIN_1130_20 × VT_BUCKET_GINI_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S31P15", "operator": "rank_spread", "left": _DD_MATCH, "right": _D1_LEVEL,
     "mechanism": "s31_p15", "hypothesis": "GAP_DD_DIRECTION_MATCH_20 × D1_LEVEL_60。方向由发现期定。", "expected_sign": -1},
    {"id": "S31P16", "operator": "rank_spread", "left": _DD_MATCH, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s31_p16", "hypothesis": "GAP_DD_DIRECTION_MATCH_20 × R_LOG_AMOUNT_VOL_20。本轮末条。方向由发现期定。", "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
