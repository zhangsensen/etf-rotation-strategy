#!/usr/bin/env python3
"""Round 604 driver: S24 stage step 2 -- volume_time_1m pairing, round 2.
Remaining 6 left legs not yet used in round_603: RV_V_20, RV_V_RATIO_20,
VT_RET_SKEW_20, VT_BUCKET_GINI_20, VT_BUCKET_COUNT_20, VT_LATE_MOM_20.
This exhausts all 8 volume_time_1m atoms' pairing-batch allowance for
S24.

Right legs: all fresh atoms with ZERO prior use as a right leg in S24
(round_603 used VOL_SPIKE_FREQ_20, UNDERWATER_FRAC_CHG_20,
LUNCH_PRERUN_POSTRUN_RATIO_20, ON_SIGN_STREAK_20, TRUE_RANGE_RATIO_20,
D1_LEVEL_60, MFI_EXTREME_FRAC_20, COSKEW_20, OPEN30_VOL_SHARE_20,
WORST_DAY_20, SAMPEN_RET_20, MARKET_BETA_20, BEST_DAY_20,
GAP_FILL_FRACTION_20, AD_NET_FLOW_20, VAR_RATIO_5_60 -- all avoided
here). Drawn broadly across families never used as S24 right legs
before."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_604"

_RV_V = {"name": "RV_V_20", "source": "volume_time_1m"}
_RV_V_RATIO = {"name": "RV_V_RATIO_20", "source": "volume_time_1m"}
_VT_RET_SKEW = {"name": "VT_RET_SKEW_20", "source": "volume_time_1m"}
_VT_BUCKET_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_VT_BUCKET_COUNT = {"name": "VT_BUCKET_COUNT_20", "source": "volume_time_1m"}
_VT_LATE_MOM = {"name": "VT_LATE_MOM_20", "source": "volume_time_1m"}

_ON_ABS_MEAN = {"name": "ON_ABS_MEAN_20", "source": "overnight_structure_1d"}
_LAG_COEF_SIGN_FREQ = {"name": "LAG_COEF_SIGN_FREQ_20", "source": "price_delay"}
_NR7_FREQ = {"name": "NR7_FLAG_FREQ_20", "source": "range_contraction_cycle"}
_FP_DOWN_CHG = {"name": "FIRST_PASSAGE_DOWN_CHG_20", "source": "first_passage_times_1m"}
_SEMICOV_DOWN_BETA = {"name": "SEMICOV_DOWNSIDE_BETA_20", "source": "realized_semicov_1m"}

_RETURN_SKEW20 = {"name": "RETURN_SKEW_20", "source": "return_tail_shape"}
_RET_ACF1_20 = {"name": "RET_ACF1_20", "source": "serial_dependence"}
_DOWNSIDE_BETA20 = {"name": "DOWNSIDE_BETA_20", "source": "market_sensitivity"}
_DOWNSIDE_COSKEW60 = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}
_MAX5_MEAN20 = {"name": "MAX5_MEAN_20", "source": "upside_tail"}

_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_OBV_SLOPE = {"name": "OBV_SLOPE_20", "source": "accumulation_distribution_1m"}
_APEN = {"name": "APEN_RET_20", "source": "complexity_measures_1m"}
_BETA_LF = {"name": "BETA_LF_20", "source": "frequency_domain_beta_1m"}
_MFI_HI_FRAC = {"name": "MFI_EXTREME_HI_FRAC_20", "source": "money_flow_extremes_1m"}

_LUNCH_POST_RUN = {"name": "LUNCH_POST_RUN_20", "source": "lunch_break_1m"}
_ULCER_INDEX = {"name": "ULCER_INDEX_20", "source": "intraday_pain_recovery_1m"}
_BB_WIDTH_CHG = {"name": "BB_WIDTH_CHG_20", "source": "range_contraction_cycle"}
_COKURT60 = {"name": "COKURT_60", "source": "coskewness_risk"}
_WORST_DAY60 = {"name": "WORST_DAY_60", "source": "return_tail_shape"}

_VAR_RATIO_20_120 = {"name": "VAR_RATIO_20_120", "source": "serial_dependence"}
_UPSIDE_BETA20 = {"name": "UPSIDE_BETA_20", "source": "market_sensitivity"}
_CONTRACTION_DEPTH = {"name": "CONTRACTION_DEPTH_60", "source": "range_contraction_cycle"}
_D2_LAGSHARE_CHG = {"name": "D2_LAGSHARE_CHG_20", "source": "price_delay"}
_PASSAGE_ASYM = {"name": "PASSAGE_ASYM_20", "source": "first_passage_times_1m"}

_RCOV_P_SHARE = {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"}
_POS_DAY_FRAC_Z = {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"}
_RECOVERY_TIME_FRAC = {"name": "RECOVERY_TIME_FRAC_20", "source": "intraday_pain_recovery_1m"}
_AD_PRICE_CORR = {"name": "AD_PRICE_CORR_20", "source": "accumulation_distribution_1m"}
_RET_ACF2_20 = {"name": "RET_ACF2_20", "source": "serial_dependence"}

base.CANDIDATES = [
    # ---- RV_V_20: first pairing batch ----
    {"id": "YA1", "operator": "rank_spread", "left": _RV_V, "right": _ON_ABS_MEAN,
     "mechanism": "rv_v_confirmed_by_on_abs_mean_20",
     "hypothesis": "A=成交量钟已实现方差20日均值(体检disc-0.1047/审计-0.0772同向,shadow vs S23 VT_MAXDD_20)。B=隔夜收益绝对值20日均值(overnight_structure_1d,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YA2", "operator": "rank_spread", "left": _RV_V, "right": _LAG_COEF_SIGN_FREQ,
     "mechanism": "rv_v_confirmed_by_lag_coef_sign_freq_20",
     "hypothesis": "A=同上。B=价格延迟滞后系数符号频率(price_delay,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YA3", "operator": "rank_spread", "left": _RV_V, "right": _NR7_FREQ,
     "mechanism": "rv_v_confirmed_by_nr7_flag_freq_20",
     "hypothesis": "A=同上。B=NR7标志20日频率(S19,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YA4", "operator": "rank_spread", "left": _RV_V, "right": _FP_DOWN_CHG,
     "mechanism": "rv_v_confirmed_by_first_passage_down_chg_20",
     "hypothesis": "A=同上。B=首达-1σ时间20日变化(S17,first_passage_times_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YA5", "operator": "rank_spread", "left": _RV_V, "right": _SEMICOV_DOWN_BETA,
     "mechanism": "rv_v_confirmed_by_semicov_downside_beta_20",
     "hypothesis": "A=同上。B=已实现下行半协方差beta(S8,realized_semicov_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- RV_V_RATIO_20: first pairing batch ----
    {"id": "YB1", "operator": "rank_spread", "left": _RV_V_RATIO, "right": _RETURN_SKEW20,
     "mechanism": "rv_v_ratio_confirmed_by_return_skew_20",
     "hypothesis": "A=成交量钟RV/日历RV之比20日均值(体检disc-0.1040/审计-0.0380同向但衰减,非shadow)。B=收益偏度20日(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YB2", "operator": "rank_spread", "left": _RV_V_RATIO, "right": _RET_ACF1_20,
     "mechanism": "rv_v_ratio_confirmed_by_ret_acf1_20",
     "hypothesis": "A=同上。B=收益1阶自相关20日(serial_dependence,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YB3", "operator": "rank_spread", "left": _RV_V_RATIO, "right": _DOWNSIDE_BETA20,
     "mechanism": "rv_v_ratio_confirmed_by_downside_beta_20",
     "hypothesis": "A=同上。B=下行beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YB4", "operator": "rank_spread", "left": _RV_V_RATIO, "right": _DOWNSIDE_COSKEW60,
     "mechanism": "rv_v_ratio_confirmed_by_downside_coskew_60",
     "hypothesis": "A=同上。B=下行共偏度60日(S1幸存原子,coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YB5", "operator": "rank_spread", "left": _RV_V_RATIO, "right": _MAX5_MEAN20,
     "mechanism": "rv_v_ratio_confirmed_by_max5_mean_20",
     "hypothesis": "A=同上。B=最大5日收益均值(S2,upside_tail,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- VT_RET_SKEW_20: first pairing batch ----
    {"id": "YC1", "operator": "rank_spread", "left": _VT_RET_SKEW, "right": _GAP_FILL60,
     "mechanism": "vt_ret_skew_confirmed_by_gap_fill_fraction_60",
     "hypothesis": "A=成交量时间收益偏度20日均值(体检disc-0.0028/审计+0.0155,接近零符号不稳)。B=跳空当日回补比例60日(gap_repair,本族首次配对)。假设方向由发现期定，本条方向不确定性高。",
     "expected_sign": -1},
    {"id": "YC2", "operator": "rank_spread", "left": _VT_RET_SKEW, "right": _OBV_SLOPE,
     "mechanism": "vt_ret_skew_confirmed_by_obv_slope_20",
     "hypothesis": "A=同上。B=OBV日内斜率20日(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YC3", "operator": "rank_spread", "left": _VT_RET_SKEW, "right": _APEN,
     "mechanism": "vt_ret_skew_confirmed_by_apen_ret_20",
     "hypothesis": "A=同上。B=收益近似熵(S11,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YC4", "operator": "rank_spread", "left": _VT_RET_SKEW, "right": _BETA_LF,
     "mechanism": "vt_ret_skew_confirmed_by_beta_lf_20",
     "hypothesis": "A=同上。B=低频带beta(S13,frequency_domain_beta_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YC5", "operator": "rank_spread", "left": _VT_RET_SKEW, "right": _MFI_HI_FRAC,
     "mechanism": "vt_ret_skew_confirmed_by_mfi_extreme_hi_frac_20",
     "hypothesis": "A=同上。B=MFI极端高值占比(money_flow_extremes_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- VT_BUCKET_GINI_20: first pairing batch ----
    {"id": "YD1", "operator": "rank_spread", "left": _VT_BUCKET_GINI, "right": _LUNCH_POST_RUN,
     "mechanism": "vt_bucket_gini_confirmed_by_lunch_post_run_20",
     "hypothesis": "A=等量桶日历时长分布Gini系数20日均值(体检disc+0.0522/审计+0.0022,shadow vs bar_size_order_flow:BIGBAR_VOL_SHARE_20)。B=13:00-13:10成交量占全日比例(S22入选原子搭档LB8的左腿,lunch_break_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "YD2", "operator": "rank_spread", "left": _VT_BUCKET_GINI, "right": _ULCER_INDEX,
     "mechanism": "vt_bucket_gini_confirmed_by_ulcer_index_20",
     "hypothesis": "A=同上。B=日内溃疡指数20日均值(S12,intraday_pain_recovery_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "YD3", "operator": "rank_spread", "left": _VT_BUCKET_GINI, "right": _BB_WIDTH_CHG,
     "mechanism": "vt_bucket_gini_confirmed_by_bb_width_chg_20",
     "hypothesis": "A=同上。B=布林带宽20日变化率(S19,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "YD4", "operator": "rank_spread", "left": _VT_BUCKET_GINI, "right": _COKURT60,
     "mechanism": "vt_bucket_gini_confirmed_by_cokurt_60",
     "hypothesis": "A=同上。B=共峰度60日(coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "YD5", "operator": "rank_spread", "left": _VT_BUCKET_GINI, "right": _WORST_DAY60,
     "mechanism": "vt_bucket_gini_confirmed_by_worst_day_60",
     "hypothesis": "A=同上。B=60日最差单日收益(return_tail_shape,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- VT_BUCKET_COUNT_20: first pairing batch ----
    {"id": "YE1", "operator": "rank_spread", "left": _VT_BUCKET_COUNT, "right": _VAR_RATIO_20_120,
     "mechanism": "vt_bucket_count_confirmed_by_var_ratio_20_120",
     "hypothesis": "A=当日实现等量桶数20日均值(体检disc-0.0257/审计+0.0684,符号翻转)。B=方差比20/120日(serial_dependence,本族首次配对)。假设方向由发现期定，本条方向不确定性高。",
     "expected_sign": -1},
    {"id": "YE2", "operator": "rank_spread", "left": _VT_BUCKET_COUNT, "right": _UPSIDE_BETA20,
     "mechanism": "vt_bucket_count_confirmed_by_upside_beta_20",
     "hypothesis": "A=同上。B=上行beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YE3", "operator": "rank_spread", "left": _VT_BUCKET_COUNT, "right": _CONTRACTION_DEPTH,
     "mechanism": "vt_bucket_count_confirmed_by_contraction_depth_60",
     "hypothesis": "A=同上。B=区间收缩深度60日(S19,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YE4", "operator": "rank_spread", "left": _VT_BUCKET_COUNT, "right": _D2_LAGSHARE_CHG,
     "mechanism": "vt_bucket_count_confirmed_by_d2_lagshare_chg_20",
     "hypothesis": "A=同上。B=价格延迟D2滞后系数份额20日变化(S20,price_delay,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "YE5", "operator": "rank_spread", "left": _VT_BUCKET_COUNT, "right": _PASSAGE_ASYM,
     "mechanism": "vt_bucket_count_confirmed_by_passage_asym_20",
     "hypothesis": "A=同上。B=首达上下不对称(S17,first_passage_times_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- VT_LATE_MOM_20: first pairing batch ----
    {"id": "YF1", "operator": "rank_spread", "left": _VT_LATE_MOM, "right": _RCOV_P_SHARE,
     "mechanism": "vt_late_mom_confirmed_by_rcov_p_share_20",
     "hypothesis": "A=最后20%等量桶收益之和20日均值(体检disc+0.0046/审计+0.0403同向弱)。B=已实现同正半协方差份额(S8,realized_semicov_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "YF2", "operator": "rank_spread", "left": _VT_LATE_MOM, "right": _POS_DAY_FRAC_Z,
     "mechanism": "vt_late_mom_confirmed_by_pos_day_frac_z_20",
     "hypothesis": "A=同上。B=正收益日占比20日z分数(S2,upside_tail,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "YF3", "operator": "rank_spread", "left": _VT_LATE_MOM, "right": _RECOVERY_TIME_FRAC,
     "mechanism": "vt_late_mom_confirmed_by_recovery_time_frac_20",
     "hypothesis": "A=同上。B=日内回撤恢复时间占比(S12,intraday_pain_recovery_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "YF4", "operator": "rank_spread", "left": _VT_LATE_MOM, "right": _AD_PRICE_CORR,
     "mechanism": "vt_late_mom_confirmed_by_ad_price_corr_20",
     "hypothesis": "A=同上。B=A/D净流与价格相关20日(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "YF5", "operator": "rank_spread", "left": _VT_LATE_MOM, "right": _RET_ACF2_20,
     "mechanism": "vt_late_mom_confirmed_by_ret_acf2_20",
     "hypothesis": "A=同上。B=收益2阶自相关20日(serial_dependence,本族首次配对)。假设方向由发现期定。本批最后一条，本轮末条，本族8原子左腿配额全部用尽。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
