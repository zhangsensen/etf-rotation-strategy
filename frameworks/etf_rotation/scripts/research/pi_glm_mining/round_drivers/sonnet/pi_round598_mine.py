#!/usr/bin/env python3
"""Round 598 driver: S22 stage step 3 -- lunch_break_1m pairing, round 3.
Final 4 left-leg batches for this family, exhausting the pairing-discipline
allowance: LUNCH_GAP_20, LUNCH_GAP_ABS_20, LUNCH_GAP_CHG_20,
AM_PM_RET_CORR_20 (the 4 atoms not yet used as left legs in S22; the other
4 -- AM_PM_RV_RATIO_20, LUNCH_POST_RUN_20, LUNCH_PRERUN_POSTRUN_RATIO_20 --
already spent their one-batch allowance in round_596/597;
LUNCH_GAP_FILL_15M_20 remains permanently ineligible, 315 disc days).

Right legs: all fresh atoms with ZERO prior use as a right leg in S22
(round_596/597 used UNDERWATER_FRAC_CHG_20, TRUE_RANGE_RATIO_20,
D1_LEVEL_60, AD_NET_FLOW_20, YZ_OVERNIGHT_SHARE_20, COSKEW_20,
WORST_DAY_20, PATH_EFFICIENCY_20, MARKET_BETA_20, NOISE_VAR_20,
RECOVERY_TIME_FRAC_20, SAMPEN_RET_20, VAR_RATIO_5_60, MAX_DD_20,
SESSION_MEAN_20, UNDERWATER_RUN_60, REL_MARKET_MOM_20, BEST_DAY_20,
GAP_FILL_FRACTION_20 -- all avoided here to keep this round's per-right
usage at exactly 1, well under the 3x cap). Also avoids this line's known
'redundancy magnets' (PERM_ENTROPY_RET_20, CONTINUOUS_BETA_60,
RCOV_N_SHARE_20, MSPE_5M_20, BETA_HF_20). Drawn from
first_passage_times_1m (S17), overnight_structure_1d (S21),
range_contraction_cycle (S19), price_delay (S20),
intraday_pain_recovery_1m (S12), complexity_measures_1m (S11),
realized_semicov_1m (S8) -- 7 distinct families, none shared with
lunch_break_1m, satisfying cross_family_only pair policy."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_598"

_GAP = {"name": "LUNCH_GAP_20", "source": "lunch_break_1m"}
_GAP_ABS = {"name": "LUNCH_GAP_ABS_20", "source": "lunch_break_1m"}
_GAP_CHG = {"name": "LUNCH_GAP_CHG_20", "source": "lunch_break_1m"}
_RET_CORR = {"name": "AM_PM_RET_CORR_20", "source": "lunch_break_1m"}

_FP_DOWN_CHG = {"name": "FIRST_PASSAGE_DOWN_CHG_20", "source": "first_passage_times_1m"}
_ON_ABS_MEAN = {"name": "ON_ABS_MEAN_20", "source": "overnight_structure_1d"}
_NR7_FREQ = {"name": "NR7_FLAG_FREQ_20", "source": "range_contraction_cycle"}
_D2_LAGSHARE_CHG = {"name": "D2_LAGSHARE_CHG_20", "source": "price_delay"}
_ULCER_CHG = {"name": "ULCER_INDEX_CHG_20", "source": "intraday_pain_recovery_1m"}
_APEN = {"name": "APEN_RET_20", "source": "complexity_measures_1m"}
_SEMICOV_DOWN_BETA = {"name": "SEMICOV_DOWNSIDE_BETA_20", "source": "realized_semicov_1m"}

_PASSAGE_ASYM = {"name": "PASSAGE_ASYM_20", "source": "first_passage_times_1m"}
_ON_INTRADAY_CORR = {"name": "ON_INTRADAY_CORR_20", "source": "overnight_structure_1d"}
_BB_WIDTH_CHG = {"name": "BB_WIDTH_CHG_20", "source": "range_contraction_cycle"}
_LAG1_COEF60 = {"name": "LAG1_COEF_60", "source": "price_delay"}
_PAIN_INDEX = {"name": "PAIN_INDEX_20", "source": "intraday_pain_recovery_1m"}
_LZ_COMPLEXITY = {"name": "LZ_COMPLEXITY_20", "source": "complexity_measures_1m"}
_BETA_ASYM = {"name": "BETA_ASYM_20", "source": "realized_semicov_1m"}

_FALSE_BREAK = {"name": "FALSE_BREAK_RATE_20", "source": "first_passage_times_1m"}
_ON_PREM_CHG = {"name": "ON_PREM_CHG_20", "source": "overnight_structure_1d"}
_DAYS_SINCE_NR7 = {"name": "DAYS_SINCE_NR7_20", "source": "range_contraction_cycle"}
_D1_1M_CHG = {"name": "D1_1M_CHG_20", "source": "price_delay"}
_DD_RECOVERY_RATIO = {"name": "DD_RECOVERY_SPEED_RATIO_20", "source": "intraday_pain_recovery_1m"}
_MSPE_SCALE_DIFF = {"name": "MSPE_SCALE_DIFF_20", "source": "complexity_measures_1m"}
_MIXED_NET = {"name": "MIXED_NET_20", "source": "realized_semicov_1m"}

_SIGMA_CROSSING = {"name": "SIGMA_CROSSING_COUNT_20", "source": "first_passage_times_1m"}
_ON_VOL_ADJ_RET = {"name": "ON_VOL_ADJ_RET_20", "source": "overnight_structure_1d"}
_CONTRACTION_DEPTH = {"name": "CONTRACTION_DEPTH_60", "source": "range_contraction_cycle"}
_D1_DIFF_1D_1M = {"name": "D1_DIFF_1D_1M_20", "source": "price_delay"}
_UF_Z60 = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}
_RECURRENCE_RATE = {"name": "RECURRENCE_RATE_20", "source": "complexity_measures_1m"}

base.CANDIDATES = [
    # ---- LUNCH_GAP_20: first (and only, per pairing discipline) pairing batch ----
    {"id": "GA1", "operator": "rank_spread", "left": _GAP, "right": _FP_DOWN_CHG,
     "mechanism": "lunch_gap_confirmed_by_first_passage_down_chg_20",
     "hypothesis": "A=午间跳空(13:00首bar开/11:30收-1)20日均值(体检disc+0.0126/审计+0.0101同向)。B=首达-1σ时间20日变化(S17,first_passage_times_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA2", "operator": "rank_spread", "left": _GAP, "right": _ON_ABS_MEAN,
     "mechanism": "lunch_gap_confirmed_by_on_abs_mean_20",
     "hypothesis": "A=同上。B=隔夜收益绝对值20日均值(S21,overnight_structure_1d,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA3", "operator": "rank_spread", "left": _GAP, "right": _NR7_FREQ,
     "mechanism": "lunch_gap_confirmed_by_nr7_flag_freq_20",
     "hypothesis": "A=同上。B=NR7标志20日频率(S19,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA4", "operator": "rank_spread", "left": _GAP, "right": _D2_LAGSHARE_CHG,
     "mechanism": "lunch_gap_confirmed_by_d2_lagshare_chg_20",
     "hypothesis": "A=同上。B=价格延迟D2滞后系数份额20日变化(S20,price_delay,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA5", "operator": "rank_spread", "left": _GAP, "right": _ULCER_CHG,
     "mechanism": "lunch_gap_confirmed_by_ulcer_index_chg_20",
     "hypothesis": "A=同上。B=日内溃疡指数20日变化(S12,intraday_pain_recovery_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA6", "operator": "rank_spread", "left": _GAP, "right": _APEN,
     "mechanism": "lunch_gap_confirmed_by_apen_ret_20",
     "hypothesis": "A=同上。B=1m收益近似熵(S11,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA7", "operator": "rank_spread", "left": _GAP, "right": _SEMICOV_DOWN_BETA,
     "mechanism": "lunch_gap_confirmed_by_semicov_downside_beta_20",
     "hypothesis": "A=同上。B=已实现下行半协方差beta(S8,realized_semicov_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- LUNCH_GAP_ABS_20: first pairing batch ----
    {"id": "GB1", "operator": "rank_spread", "left": _GAP_ABS, "right": _PASSAGE_ASYM,
     "mechanism": "lunch_gap_abs_confirmed_by_passage_asym_20",
     "hypothesis": "A=午间跳空绝对值20日均值(幅度维度,体检disc-0.0239/审计-0.0234同向)。B=首达上下不对称(S17,first_passage_times_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GB2", "operator": "rank_spread", "left": _GAP_ABS, "right": _ON_INTRADAY_CORR,
     "mechanism": "lunch_gap_abs_confirmed_by_on_intraday_corr_20",
     "hypothesis": "A=同上。B=隔夜收益与日内收益20日相关(S21,overnight_structure_1d,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GB3", "operator": "rank_spread", "left": _GAP_ABS, "right": _BB_WIDTH_CHG,
     "mechanism": "lunch_gap_abs_confirmed_by_bb_width_chg_20",
     "hypothesis": "A=同上。B=布林带宽20日变化率(S19,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GB4", "operator": "rank_spread", "left": _GAP_ABS, "right": _LAG1_COEF60,
     "mechanism": "lunch_gap_abs_confirmed_by_lag1_coef_60",
     "hypothesis": "A=同上。B=滞后1期回归系数60日(S20,price_delay,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GB5", "operator": "rank_spread", "left": _GAP_ABS, "right": _PAIN_INDEX,
     "mechanism": "lunch_gap_abs_confirmed_by_pain_index_20",
     "hypothesis": "A=同上。B=日内痛苦指数20日均值(S12,intraday_pain_recovery_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GB6", "operator": "rank_spread", "left": _GAP_ABS, "right": _LZ_COMPLEXITY,
     "mechanism": "lunch_gap_abs_confirmed_by_lz_complexity_20",
     "hypothesis": "A=同上。B=收益符号序列LZ复杂度(S11,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GB7", "operator": "rank_spread", "left": _GAP_ABS, "right": _BETA_ASYM,
     "mechanism": "lunch_gap_abs_confirmed_by_beta_asym_20",
     "hypothesis": "A=同上。B=上下行beta不对称(S8,realized_semicov_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- LUNCH_GAP_CHG_20: first pairing batch ----
    {"id": "GC1", "operator": "rank_spread", "left": _GAP_CHG, "right": _FALSE_BREAK,
     "mechanism": "lunch_gap_chg_confirmed_by_false_break_rate_20",
     "hypothesis": "A=午间跳空20日均值的20日变化(体检disc+0.0174/审计+0.0128同向)。B=假突破率(S17,first_passage_times_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GC2", "operator": "rank_spread", "left": _GAP_CHG, "right": _ON_PREM_CHG,
     "mechanism": "lunch_gap_chg_confirmed_by_on_prem_chg_20",
     "hypothesis": "A=同上。B=隔夜收益20日变化(S21,overnight_structure_1d,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GC3", "operator": "rank_spread", "left": _GAP_CHG, "right": _DAYS_SINCE_NR7,
     "mechanism": "lunch_gap_chg_confirmed_by_days_since_nr7_20",
     "hypothesis": "A=同上。B=距最近NR7天数(S19,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GC4", "operator": "rank_spread", "left": _GAP_CHG, "right": _D1_1M_CHG,
     "mechanism": "lunch_gap_chg_confirmed_by_d1_1m_chg_20",
     "hypothesis": "A=同上。B=1m频价格延迟D1的20日变化(S20,price_delay,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GC5", "operator": "rank_spread", "left": _GAP_CHG, "right": _DD_RECOVERY_RATIO,
     "mechanism": "lunch_gap_chg_confirmed_by_dd_recovery_speed_ratio_20",
     "hypothesis": "A=同上。B=回撤/恢复速度之比(S12,intraday_pain_recovery_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GC6", "operator": "rank_spread", "left": _GAP_CHG, "right": _MSPE_SCALE_DIFF,
     "mechanism": "lunch_gap_chg_confirmed_by_mspe_scale_diff_20",
     "hypothesis": "A=同上。B=多尺度排列熵尺度差(S11,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GC7", "operator": "rank_spread", "left": _GAP_CHG, "right": _MIXED_NET,
     "mechanism": "lunch_gap_chg_confirmed_by_mixed_net_20",
     "hypothesis": "A=同上。B=混合半协方差净值(S8,realized_semicov_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- AM_PM_RET_CORR_20: first pairing batch ----
    {"id": "GD1", "operator": "rank_spread", "left": _RET_CORR, "right": _SIGMA_CROSSING,
     "mechanism": "am_pm_ret_corr_confirmed_by_sigma_crossing_count_20",
     "hypothesis": "A=上午收益与下午收益20日滚动相关(体检disc-0.0089/审计-0.0310同向弱)。B=日内±1σ穿越次数(S17,first_passage_times_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GD2", "operator": "rank_spread", "left": _RET_CORR, "right": _ON_VOL_ADJ_RET,
     "mechanism": "am_pm_ret_corr_confirmed_by_on_vol_adj_ret_20",
     "hypothesis": "A=同上。B=波动调整后隔夜收益(S21,overnight_structure_1d,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GD3", "operator": "rank_spread", "left": _RET_CORR, "right": _CONTRACTION_DEPTH,
     "mechanism": "am_pm_ret_corr_confirmed_by_contraction_depth_60",
     "hypothesis": "A=同上。B=区间收缩深度60日(S19,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GD4", "operator": "rank_spread", "left": _RET_CORR, "right": _D1_DIFF_1D_1M,
     "mechanism": "am_pm_ret_corr_confirmed_by_d1_diff_1d_1m_20",
     "hypothesis": "A=同上。B=日频与1m频D1之差(S20,price_delay,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GD5", "operator": "rank_spread", "left": _RET_CORR, "right": _UF_Z60,
     "mechanism": "am_pm_ret_corr_confirmed_by_underwater_frac_z_60",
     "hypothesis": "A=同上。B=水下时间占比60日z分数(S12,intraday_pain_recovery_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "GD6", "operator": "rank_spread", "left": _RET_CORR, "right": _RECURRENCE_RATE,
     "mechanism": "am_pm_ret_corr_confirmed_by_recurrence_rate_20",
     "hypothesis": "A=同上。B=递归率(S11,complexity_measures_1m,本族首次配对)。假设方向由发现期定。本批最后一条，本轮末条。",
     "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
