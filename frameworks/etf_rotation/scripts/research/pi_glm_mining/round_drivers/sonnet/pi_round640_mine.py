#!/usr/bin/env python3
"""Round 640 driver: S41 stage (main controller directive, 2026-09-21) --
deepen this line's strongest no-volume dimension (overnight behavior)
beyond mean/variance-share/sign-streak into distribution SHAPE. New
family overnight_return_distribution (6 atoms, pure daily-panel, no 1m
read at all).

No small-sample pilot needed (no 1m data touched); full build ran
directly, sub-second.

Atom health (round_640_atom_health) caught a real bug on first run:
OVERNIGHT_DOWNSIDE_VAR_SHARE_60 was 97% NaN (n_finite=701 of ~23000)
because its numerator (downside_sq, masked to negative-overnight days
only, ~50% sparse by construction) used min_periods=40 copied from the
unmasked denominator's window -- never satisfiable. Fixed to
min_periods=15 (matched to the ~30-entry expected density of a fully
populated 60-bar window); coverage recovered to 22509/23274 (97%),
matching the other atoms' scale. No shadow flags after the fix (highest
corr_vs_ref magnitude 0.26, OVERNIGHT_ACTIVITY_RATIO_20_60 vs
YZ_OVERNIGHT_SHARE_20); OVERNIGHT_SKEW_60/KURTOSIS_60/TAIL_RATIO_60 show
NaN corr_vs_ref against ON_PREM_20 due to insufficient discovery-window
overlap (60-bar min_periods start much later than ON_PREM_20's 20-bar
window), not a shadow signal -- reported as N/A, not a pass.

6 atomic tests + 18 pairs (3 right legs per left atom). UNDERWATER_
FRAC_CHG_20 used as right leg 3 times (cap), per directive priority."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_640"

_SKEW = {"name": "OVERNIGHT_SKEW_60", "source": "overnight_return_distribution"}
_KURT = {"name": "OVERNIGHT_KURTOSIS_60", "source": "overnight_return_distribution"}
_DOWNSIDE_SHARE = {"name": "OVERNIGHT_DOWNSIDE_VAR_SHARE_60", "source": "overnight_return_distribution"}
_TAIL_RATIO = {"name": "OVERNIGHT_TAIL_RATIO_60", "source": "overnight_return_distribution"}
_ACTIVITY_RATIO = {"name": "OVERNIGHT_ACTIVITY_RATIO_20_60", "source": "overnight_return_distribution"}
_PRIOR_CORR = {"name": "OVERNIGHT_PRIOR_INTRADAY_CORR_20", "source": "overnight_return_distribution"}

_UWF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PV_ELASTICITY = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_MFI_EXTREME = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_VT_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_HAR_RESID = {"name": "S28_VOV_HAR_RESID_20", "source": "pi_repl_s28"}
_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_FP_UP = {"name": "FIRST_PASSAGE_UP_20", "source": "first_passage_times_1m"}
_EXTREME_ORDER = {"name": "EXTREME_TIME_ORDER", "source": "intraday_extremes_timing"}
_R2_BIGBAR = {"name": "R2_BIGBAR_VOL_SHARE_20", "source": "repl_volume_core_v2b"}
_ON_SIGN_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}

base.CANDIDATES = [
    # ---- 6 atomic tests ----
    {"id": "S41A1", "operator": "atomic", "left": _SKEW, "right": _SKEW,
     "mechanism": "s41_skew_atomic",
     "hypothesis": "OVERNIGHT_SKEW_60（隔夜收益60日偏度）单原子门7重裁。体检 disc_ic=-0.0369。"
                   "经济假设：隔夜收益正偏（右尾更长，罕见大涨）反映情绪乐观积累，正方向。",
     "expected_sign": 1},
    {"id": "S41A2", "operator": "atomic", "left": _KURT, "right": _KURT,
     "mechanism": "s41_kurtosis_atomic",
     "hypothesis": "OVERNIGHT_KURTOSIS_60（隔夜收益60日超额峰度）单原子门7重裁。体检 disc_ic=-0.0352。"
                   "经济假设：隔夜收益尖峰厚尾=信息事件驱动的跳空更集中，方向不确定，标记待验证。",
     "expected_sign": -1},
    {"id": "S41A3", "operator": "atomic", "left": _DOWNSIDE_SHARE, "right": _DOWNSIDE_SHARE,
     "mechanism": "s41_downside_share_atomic",
     "hypothesis": "OVERNIGHT_DOWNSIDE_VAR_SHARE_60（隔夜下行半方差/隔夜总方差，60日）单原子门7重裁（修复 min_periods bug 后）。"
                   "体检 disc_ic=+0.0295，与 YZ_OVERNIGHT_SHARE_20 corr=-0.08（独立）。经济假设：下行方差占比越高=隔夜风险偏负面，负方向。",
     "expected_sign": -1},
    {"id": "S41A4", "operator": "atomic", "left": _TAIL_RATIO, "right": _TAIL_RATIO,
     "mechanism": "s41_tail_ratio_atomic",
     "hypothesis": "OVERNIGHT_TAIL_RATIO_60（隔夜收益60日5%分位/95%分位之比）单原子门7重裁。体检 disc_ic=+0.0035（近零）。"
                   "经济假设：该比值恒为负，越接近0（左尾相对右尾更短）代表下行尾部风险更小，正方向。",
     "expected_sign": 1},
    {"id": "S41A5", "operator": "atomic", "left": _ACTIVITY_RATIO, "right": _ACTIVITY_RATIO,
     "mechanism": "s41_activity_ratio_atomic",
     "hypothesis": "OVERNIGHT_ACTIVITY_RATIO_20_60（|隔夜收益|20日/60日均值比）单原子门7重裁。体检 disc_ic=+0.0156，"
                   "与 YZ_OVERNIGHT_SHARE_20 corr=0.26（独立但偏高）。经济假设：近期隔夜活动度相对放大=风险溢价上升，正方向。",
     "expected_sign": 1},
    {"id": "S41A6", "operator": "atomic", "left": _PRIOR_CORR, "right": _PRIOR_CORR,
     "mechanism": "s41_prior_corr_atomic",
     "hypothesis": "OVERNIGHT_PRIOR_INTRADAY_CORR_20（隔夜收益与前一日日内收益的20日相关）单原子门7重裁。体检 disc_ic=-0.0336，"
                   "与 GAP_DD_CONSUMPTION_RATIO_20 corr=0.05（独立）。经济假设：隔夜延续前日日内动量=趋势确认，正方向。",
     "expected_sign": 1},
    # ---- 18 pairs (3 right legs per left atom) ----
    {"id": "S41P1", "operator": "rank_spread", "left": _SKEW, "right": _UWF_CHG,
     "mechanism": "s41_p1", "hypothesis": "OVERNIGHT_SKEW_60 × UNDERWATER_FRAC_CHG_20（S7，本线最强单原子之一，优先右腿）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P2", "operator": "rank_spread", "left": _SKEW, "right": _PV_ELASTICITY,
     "mechanism": "s41_p2", "hypothesis": "OVERNIGHT_SKEW_60 × PV_ELASTICITY_20（S14）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P3", "operator": "rank_spread", "left": _SKEW, "right": _D1_LEVEL,
     "mechanism": "s41_p3", "hypothesis": "OVERNIGHT_SKEW_60 × D1_LEVEL_60（S20）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P4", "operator": "rank_spread", "left": _KURT, "right": _UWF_CHG,
     "mechanism": "s41_p4", "hypothesis": "OVERNIGHT_KURTOSIS_60 × UNDERWATER_FRAC_CHG_20（S7，优先右腿）。方向由发现期定。", "expected_sign": -1},
    {"id": "S41P5", "operator": "rank_spread", "left": _KURT, "right": _MFI_EXTREME,
     "mechanism": "s41_p5", "hypothesis": "OVERNIGHT_KURTOSIS_60 × MFI_EXTREME_FRAC_20（S10）。方向由发现期定。", "expected_sign": -1},
    {"id": "S41P6", "operator": "rank_spread", "left": _KURT, "right": _VT_GINI,
     "mechanism": "s41_p6", "hypothesis": "OVERNIGHT_KURTOSIS_60 × VT_BUCKET_GINI_20（S24）。方向由发现期定。", "expected_sign": -1},
    {"id": "S41P7", "operator": "rank_spread", "left": _DOWNSIDE_SHARE, "right": _UWF_CHG,
     "mechanism": "s41_p7", "hypothesis": "OVERNIGHT_DOWNSIDE_VAR_SHARE_60 × UNDERWATER_FRAC_CHG_20（S7，优先右腿，用满3次配额）。方向由发现期定。", "expected_sign": -1},
    {"id": "S41P8", "operator": "rank_spread", "left": _DOWNSIDE_SHARE, "right": _HAR_RESID,
     "mechanism": "s41_p8", "hypothesis": "OVERNIGHT_DOWNSIDE_VAR_SHARE_60 × S28_VOV_HAR_RESID_20（S28）。方向由发现期定。", "expected_sign": -1},
    {"id": "S41P9", "operator": "rank_spread", "left": _DOWNSIDE_SHARE, "right": _R_ULCER,
     "mechanism": "s41_p9", "hypothesis": "OVERNIGHT_DOWNSIDE_VAR_SHARE_60 × R_ULCER_20（S26R）。方向由发现期定。", "expected_sign": -1},
    {"id": "S41P10", "operator": "rank_spread", "left": _TAIL_RATIO, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s41_p10", "hypothesis": "OVERNIGHT_TAIL_RATIO_60 × R_LOG_AMOUNT_VOL_20（S26R）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P11", "operator": "rank_spread", "left": _TAIL_RATIO, "right": _FP_UP,
     "mechanism": "s41_p11", "hypothesis": "OVERNIGHT_TAIL_RATIO_60 × FIRST_PASSAGE_UP_20（S17）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P12", "operator": "rank_spread", "left": _TAIL_RATIO, "right": _EXTREME_ORDER,
     "mechanism": "s41_p12", "hypothesis": "OVERNIGHT_TAIL_RATIO_60 × EXTREME_TIME_ORDER（日内极值时序）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P13", "operator": "rank_spread", "left": _ACTIVITY_RATIO, "right": _R2_BIGBAR,
     "mechanism": "s41_p13", "hypothesis": "OVERNIGHT_ACTIVITY_RATIO_20_60 × R2_BIGBAR_VOL_SHARE_20（S26R2）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P14", "operator": "rank_spread", "left": _ACTIVITY_RATIO, "right": _ON_SIGN_STREAK,
     "mechanism": "s41_p14", "hypothesis": "OVERNIGHT_ACTIVITY_RATIO_20_60 × ON_SIGN_STREAK_20（S21）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P15", "operator": "rank_spread", "left": _ACTIVITY_RATIO, "right": _MFI_EXTREME,
     "mechanism": "s41_p15", "hypothesis": "OVERNIGHT_ACTIVITY_RATIO_20_60 × MFI_EXTREME_FRAC_20（S10）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P16", "operator": "rank_spread", "left": _PRIOR_CORR, "right": _D1_LEVEL,
     "mechanism": "s41_p16", "hypothesis": "OVERNIGHT_PRIOR_INTRADAY_CORR_20 × D1_LEVEL_60（S20）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P17", "operator": "rank_spread", "left": _PRIOR_CORR, "right": _VT_GINI,
     "mechanism": "s41_p17", "hypothesis": "OVERNIGHT_PRIOR_INTRADAY_CORR_20 × VT_BUCKET_GINI_20（S24）。方向由发现期定。", "expected_sign": 1},
    {"id": "S41P18", "operator": "rank_spread", "left": _PRIOR_CORR, "right": _PV_ELASTICITY,
     "mechanism": "s41_p18", "hypothesis": "OVERNIGHT_PRIOR_INTRADAY_CORR_20 × PV_ELASTICITY_20（S14，本轮末条）。方向由发现期定。", "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
