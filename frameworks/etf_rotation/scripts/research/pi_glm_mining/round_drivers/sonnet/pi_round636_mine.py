#!/usr/bin/env python3
"""Round 636 driver: S37 stage (main controller directive, 2026-09-21) --
deepen the positional structure of MFI extremes inside intraday
drawdowns (S33/S29Q1's finding that WHERE MFI extremes occur matters
more than volume share: MFI_EXTREME_UNDERWATER_SKEW_20 audit t 3.60).
New family mfi_extreme_timing_1m (self-contained, computes its own
MFI(14), no cross-family imports).

Small-sample pilot (3 symbols) ran 5.16s; full 14-symbol run
extrapolated ~24s, ran directly.

Plan-time discovery: the originally-planned atomic
MFI_EXTREME_TOD_SKEW_20 hit a canonical-hash collision -- round_570's
already-registered money_flow_extremes_1m family (S15 self-directed
deepening) had already claimed that exact atom name with a different
(continuous, late-in-day) construction. That family turned out to
already cover directional asymmetry (MFI_EXTREME_ASYM_20) and streak
persistence (MFI_EXTREME_STREAK_20) too. Re-ran atom_health against it:
MFI_EXTREME_DIR_SKEW_20 (level) came back shadow-flagged (corr=0.87 vs
MFI_EXTREME_ASYM_20) and MFI_EXTREME_STREAK_LEN_20 was independently
shadow-flagged (corr=0.94 vs S10's MFI_EXTREME_FRAC_20) even before the
collision was found. Final atom set: MFI_EXTREME_TROUGH_SKEW_20,
MFI_EXTREME_PEAK_SKEW_20 (both independent, |corr|<0.21 vs
mechanism_atoms_v2's MFI_EXTREME_UNDERWATER_SKEW_20), MFI_EXTREME_
DIR_SKEW_CHG_20 (independent at corr=0.44, level dropped, change kept),
MFI_EXTREME_EDGE_MID_SKEW_20 (renamed from TOD_SKEW to avoid the
collision, and a genuinely distinct segment-count construction from
money_flow_extremes_1m's continuous mean-position statistic,
corr=-0.09)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_636"

_TROUGH_SKEW = {"name": "MFI_EXTREME_TROUGH_SKEW_20", "source": "mfi_extreme_timing_1m"}
_PEAK_SKEW = {"name": "MFI_EXTREME_PEAK_SKEW_20", "source": "mfi_extreme_timing_1m"}
_DIR_SKEW_CHG = {"name": "MFI_EXTREME_DIR_SKEW_CHG_20", "source": "mfi_extreme_timing_1m"}
_EDGE_MID_SKEW = {"name": "MFI_EXTREME_EDGE_MID_SKEW_20", "source": "mfi_extreme_timing_1m"}

_UWF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_GAP_DD_CONS = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_PV_ELASTICITY = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}
_HAR_RESID = {"name": "S28_VOV_HAR_RESID_20", "source": "pi_repl_s28"}
_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_VT_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_ON_SIGN_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}
_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_FP_UP = {"name": "FIRST_PASSAGE_UP_20", "source": "first_passage_times_1m"}
_EXTREME_ORDER = {"name": "EXTREME_TIME_ORDER", "source": "intraday_extremes_timing"}
_R2_BIGBAR = {"name": "R2_BIGBAR_VOL_SHARE_20", "source": "repl_volume_core_v2b"}

base.CANDIDATES = [
    # ---- 4 atomic tests ----
    {"id": "S37A1", "operator": "atomic", "left": _TROUGH_SKEW, "right": _TROUGH_SKEW,
     "mechanism": "s37_trough_skew_atomic",
     "hypothesis": "MFI_EXTREME_TROUGH_SKEW_20（MFI 极值 bar 相对日内谷底前后的计数差/总数，20日均值）单原子门7重裁。"
                   "体检 disc_ic=-0.0386，与 MFI_EXTREME_UNDERWATER_SKEW_20 corr=-0.21（独立）。"
                   "经济假设：极值更集中在谷底之前(下跌途中确认)比谷底之后(反弹途中)更像抛压确认信号，正方向。",
     "expected_sign": 1},
    {"id": "S37A2", "operator": "atomic", "left": _PEAK_SKEW, "right": _PEAK_SKEW,
     "mechanism": "s37_peak_skew_atomic",
     "hypothesis": "MFI_EXTREME_PEAK_SKEW_20（同一统计量相对日内高点）单原子门7重裁。"
                   "体检 disc_ic=+0.0253，与 MFI_EXTREME_UNDERWATER_SKEW_20 corr=-0.13（独立）。"
                   "经济假设：极值集中在日内高点之前=上涨途中确认(趋势型)而非见顶衰竭，正方向。",
     "expected_sign": 1},
    {"id": "S37A3", "operator": "atomic", "left": _DIR_SKEW_CHG, "right": _DIR_SKEW_CHG,
     "mechanism": "s37_dir_skew_chg_atomic",
     "hypothesis": "MFI_EXTREME_DIR_SKEW_CHG_20（高位/低位极值计数差比例的20日变化；水平版因与 round_570 money_flow_extremes_1m "
                   "的 MFI_EXTREME_ASYM_20 corr=0.87 被体检剔除，只留变化量）单原子门7重裁。体检 disc_ic=+0.0125，独立 corr=0.44。"
                   "经济假设：买方向极值占比持续增强，正方向。",
     "expected_sign": 1},
    {"id": "S37A4", "operator": "atomic", "left": _EDGE_MID_SKEW, "right": _EDGE_MID_SKEW,
     "mechanism": "s37_edge_mid_skew_atomic",
     "hypothesis": "MFI_EXTREME_EDGE_MID_SKEW_20（极值在首尾30分钟占比 − 中段占比，均相对总极值数，20日均值；"
                   "与 round_570 的连续型 TOD_SKEW 构造不同，本条按分段计数）单原子门7重裁。体检 disc_ic=+0.0079，"
                   "与 money_flow_extremes_1m:MFI_EXTREME_TOD_SKEW_20 corr=-0.09（独立）。"
                   "经济假设：极值集中在开盘/收盘等价格发现活跃时段=信息含量更高，正方向。",
     "expected_sign": 1},
    # ---- 12 pairs ----
    {"id": "S37P1", "operator": "rank_spread", "left": _TROUGH_SKEW, "right": _UWF_CHG,
     "mechanism": "s37_p1", "hypothesis": "MFI_EXTREME_TROUGH_SKEW_20 × UNDERWATER_FRAC_CHG_20（S7，本线最强单原子之一）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P2", "operator": "rank_spread", "left": _TROUGH_SKEW, "right": _GAP_DD_CONS,
     "mechanism": "s37_p2", "hypothesis": "MFI_EXTREME_TROUGH_SKEW_20 × GAP_DD_CONSUMPTION_RATIO_20（S27，本线最强配对左腿）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P3", "operator": "rank_spread", "left": _TROUGH_SKEW, "right": _PV_ELASTICITY,
     "mechanism": "s37_p3", "hypothesis": "MFI_EXTREME_TROUGH_SKEW_20 × PV_ELASTICITY_20（S14）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P4", "operator": "rank_spread", "left": _PEAK_SKEW, "right": _HAR_RESID,
     "mechanism": "s37_p4", "hypothesis": "MFI_EXTREME_PEAK_SKEW_20 × S28_VOV_HAR_RESID_20（S28）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P5", "operator": "rank_spread", "left": _PEAK_SKEW, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s37_p5", "hypothesis": "MFI_EXTREME_PEAK_SKEW_20 × R_LOG_AMOUNT_VOL_20（S26R）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P6", "operator": "rank_spread", "left": _PEAK_SKEW, "right": _D1_LEVEL,
     "mechanism": "s37_p6", "hypothesis": "MFI_EXTREME_PEAK_SKEW_20 × D1_LEVEL_60（S20）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P7", "operator": "rank_spread", "left": _DIR_SKEW_CHG, "right": _VT_GINI,
     "mechanism": "s37_p7", "hypothesis": "MFI_EXTREME_DIR_SKEW_CHG_20 × VT_BUCKET_GINI_20（S24）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P8", "operator": "rank_spread", "left": _DIR_SKEW_CHG, "right": _ON_SIGN_STREAK,
     "mechanism": "s37_p8", "hypothesis": "MFI_EXTREME_DIR_SKEW_CHG_20 × ON_SIGN_STREAK_20（S21）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P9", "operator": "rank_spread", "left": _DIR_SKEW_CHG, "right": _R_ULCER,
     "mechanism": "s37_p9", "hypothesis": "MFI_EXTREME_DIR_SKEW_CHG_20 × R_ULCER_20（S26R）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P10", "operator": "rank_spread", "left": _EDGE_MID_SKEW, "right": _FP_UP,
     "mechanism": "s37_p10", "hypothesis": "MFI_EXTREME_EDGE_MID_SKEW_20 × FIRST_PASSAGE_UP_20（S17）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P11", "operator": "rank_spread", "left": _EDGE_MID_SKEW, "right": _EXTREME_ORDER,
     "mechanism": "s37_p11", "hypothesis": "MFI_EXTREME_EDGE_MID_SKEW_20 × EXTREME_TIME_ORDER（日内极值时序，直接相关主题）。方向由发现期定。", "expected_sign": 1},
    {"id": "S37P12", "operator": "rank_spread", "left": _EDGE_MID_SKEW, "right": _R2_BIGBAR,
     "mechanism": "s37_p12", "hypothesis": "MFI_EXTREME_EDGE_MID_SKEW_20 × R2_BIGBAR_VOL_SHARE_20（S26R2，本轮末条）。方向由发现期定。", "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
