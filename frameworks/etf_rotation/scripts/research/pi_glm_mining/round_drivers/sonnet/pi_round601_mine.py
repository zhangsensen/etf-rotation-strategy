#!/usr/bin/env python3
"""Round 601 driver: S23 stage step 2 -- volume_time_drawdown pairing,
round 2. Remaining 6 left legs not yet used in round_600: the 4 shadow
level/maxdd atoms (VT_UNDERWATER_FRAC_20, VT_MAXDD_20,
VT_RECOVERY_FRAC_20, VT_TROUGH_VOL_POS_20 -- shadow status does not
block pairing eligibility per the standing rule established in S18/S21)
plus the 2 sign-flip atoms deliberately skipped last round
(VT_MAXDD_CHG_20, VT_PATH_EFFICIENCY_20). This exhausts all 8
volume_time_drawdown atoms' pairing-batch allowance for S23.

Right legs: all fresh atoms with ZERO prior use as a right leg in S23
(round_600 used AD_NET_FLOW_20, LUNCH_PRERUN_POSTRUN_RATIO_20,
ON_SIGN_STREAK_20, LAG_COEF_SIGN_FREQ_20, TRUE_RANGE_RATIO_20,
FIRST_PASSAGE_DOWN_CHG_20, SEMICOV_DOWNSIDE_BETA_20, BEST_DAY_20,
COSKEW_20, WORST_DAY_20, SAMPEN_RET_20, VAR_RATIO_5_60, MARKET_BETA_20,
BETA_LF_20, MFI_EXTREME_HI_FRAC_20, GAP_FILL_FRACTION_20 -- all avoided
here). Drawn from 5 families never used as S23 right legs before:
accumulation_distribution_1m, coskewness_risk, return_tail_shape,
serial_dependence, market_sensitivity, plus upside_tail/gap_repair for
the two smaller batches -- all cross-family vs volume_time_drawdown."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_601"

_VT_UF = {"name": "VT_UNDERWATER_FRAC_20", "source": "volume_time_drawdown"}
_VT_MAXDD = {"name": "VT_MAXDD_20", "source": "volume_time_drawdown"}
_VT_RECOVERY = {"name": "VT_RECOVERY_FRAC_20", "source": "volume_time_drawdown"}
_VT_TROUGH_POS = {"name": "VT_TROUGH_VOL_POS_20", "source": "volume_time_drawdown"}
_VT_MAXDD_CHG = {"name": "VT_MAXDD_CHG_20", "source": "volume_time_drawdown"}
_VT_PATH_EFF = {"name": "VT_PATH_EFFICIENCY_20", "source": "volume_time_drawdown"}

_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_DOWNSIDE_COSKEW60 = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}
_RETURN_SKEW20 = {"name": "RETURN_SKEW_20", "source": "return_tail_shape"}
_RET_ACF1_20 = {"name": "RET_ACF1_20", "source": "serial_dependence"}
_DOWNSIDE_BETA20 = {"name": "DOWNSIDE_BETA_20", "source": "market_sensitivity"}

_AD_NET_FLOW_SLOPE = {"name": "AD_NET_FLOW_SLOPE_20", "source": "accumulation_distribution_1m"}
_COSKEW60 = {"name": "COSKEW_60", "source": "coskewness_risk"}
_TAIL_Q10_20 = {"name": "TAIL_Q10_20", "source": "return_tail_shape"}
_VAR_RATIO_20_120 = {"name": "VAR_RATIO_20_120", "source": "serial_dependence"}
_UPSIDE_BETA20 = {"name": "UPSIDE_BETA_20", "source": "market_sensitivity"}

_OBV_SLOPE = {"name": "OBV_SLOPE_20", "source": "accumulation_distribution_1m"}
_COSKEW_CHG20 = {"name": "COSKEW_CHG_20", "source": "coskewness_risk"}
_RETURN_SKEW60 = {"name": "RETURN_SKEW_60", "source": "return_tail_shape"}
_SIGN_ACF1_20 = {"name": "SIGN_ACF1_20", "source": "serial_dependence"}
_MARKET_CORR20 = {"name": "MARKET_CORR_20", "source": "market_sensitivity"}

_AD_PRICE_CORR = {"name": "AD_PRICE_CORR_20", "source": "accumulation_distribution_1m"}
_COKURT60 = {"name": "COKURT_60", "source": "coskewness_risk"}
_WORST_DAY60 = {"name": "WORST_DAY_60", "source": "return_tail_shape"}
_RET_ACF2_20 = {"name": "RET_ACF2_20", "source": "serial_dependence"}
_BENCHMARK_RESID_VOL20 = {"name": "BENCHMARK_RESIDUAL_VOL_20", "source": "market_sensitivity"}

_OBV_SLOPE_CHG = {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"}
_MAX5_MEAN20 = {"name": "MAX5_MEAN_20", "source": "upside_tail"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_TAIL_Q10_60 = {"name": "TAIL_Q10_60", "source": "return_tail_shape"}

_MFI_14_MEAN = {"name": "MFI_14_MEAN_20", "source": "accumulation_distribution_1m"}
_POS_DAY_FRAC_Z = {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"}
_INTRADAY_MAXBAR_RET = {"name": "INTRADAY_MAXBAR_RET_20", "source": "upside_tail"}
_RET_ACF1_60 = {"name": "RET_ACF1_60", "source": "serial_dependence"}

base.CANDIDATES = [
    # ---- VT_UNDERWATER_FRAC_20: first pairing batch ----
    {"id": "WA1", "operator": "rank_spread", "left": _VT_UF, "right": _MFI_EXTREME_FRAC,
     "mechanism": "vt_underwater_frac_confirmed_by_mfi_extreme_frac_20",
     "hypothesis": "A=成交量时间水下占比20日均值(体检disc-0.0640/审计-0.0245同向,shadow vs 日历版)。B=资金流指标极端占比(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WA2", "operator": "rank_spread", "left": _VT_UF, "right": _DOWNSIDE_COSKEW60,
     "mechanism": "vt_underwater_frac_confirmed_by_downside_coskew_60",
     "hypothesis": "A=同上。B=下行共偏度60日(S1幸存原子,coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WA3", "operator": "rank_spread", "left": _VT_UF, "right": _RETURN_SKEW20,
     "mechanism": "vt_underwater_frac_confirmed_by_return_skew_20",
     "hypothesis": "A=同上。B=收益偏度20日(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WA4", "operator": "rank_spread", "left": _VT_UF, "right": _RET_ACF1_20,
     "mechanism": "vt_underwater_frac_confirmed_by_ret_acf1_20",
     "hypothesis": "A=同上。B=收益1阶自相关20日(serial_dependence,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WA5", "operator": "rank_spread", "left": _VT_UF, "right": _DOWNSIDE_BETA20,
     "mechanism": "vt_underwater_frac_confirmed_by_downside_beta_20",
     "hypothesis": "A=同上。B=下行beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- VT_MAXDD_20: first pairing batch ----
    {"id": "WB1", "operator": "rank_spread", "left": _VT_MAXDD, "right": _AD_NET_FLOW_SLOPE,
     "mechanism": "vt_maxdd_confirmed_by_ad_net_flow_slope_20",
     "hypothesis": "A=成交量时间最大回撤20日均值(体检disc-0.1020/审计-0.0712同向,shadow vs 日历版)。B=A/D净流斜率20日(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WB2", "operator": "rank_spread", "left": _VT_MAXDD, "right": _COSKEW60,
     "mechanism": "vt_maxdd_confirmed_by_coskew_60",
     "hypothesis": "A=同上。B=共偏度60日(coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WB3", "operator": "rank_spread", "left": _VT_MAXDD, "right": _TAIL_Q10_20,
     "mechanism": "vt_maxdd_confirmed_by_tail_q10_20",
     "hypothesis": "A=同上。B=收益10%分位尾部20日(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WB4", "operator": "rank_spread", "left": _VT_MAXDD, "right": _VAR_RATIO_20_120,
     "mechanism": "vt_maxdd_confirmed_by_var_ratio_20_120",
     "hypothesis": "A=同上。B=方差比20/120日(serial_dependence,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WB5", "operator": "rank_spread", "left": _VT_MAXDD, "right": _UPSIDE_BETA20,
     "mechanism": "vt_maxdd_confirmed_by_upside_beta_20",
     "hypothesis": "A=同上。B=上行beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- VT_RECOVERY_FRAC_20: first pairing batch ----
    {"id": "WC1", "operator": "rank_spread", "left": _VT_RECOVERY, "right": _OBV_SLOPE,
     "mechanism": "vt_recovery_frac_confirmed_by_obv_slope_20",
     "hypothesis": "A=成交量时间回撤恢复桶数占比20日均值(体检disc-0.0669/审计-0.0600同向,shadow vs pain_recovery)。B=OBV日内斜率20日(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WC2", "operator": "rank_spread", "left": _VT_RECOVERY, "right": _COSKEW_CHG20,
     "mechanism": "vt_recovery_frac_confirmed_by_coskew_chg_20",
     "hypothesis": "A=同上。B=共偏度20日变化(coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WC3", "operator": "rank_spread", "left": _VT_RECOVERY, "right": _RETURN_SKEW60,
     "mechanism": "vt_recovery_frac_confirmed_by_return_skew_60",
     "hypothesis": "A=同上。B=收益偏度60日(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WC4", "operator": "rank_spread", "left": _VT_RECOVERY, "right": _SIGN_ACF1_20,
     "mechanism": "vt_recovery_frac_confirmed_by_sign_acf1_20",
     "hypothesis": "A=同上。B=收益符号1阶自相关20日(serial_dependence,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WC5", "operator": "rank_spread", "left": _VT_RECOVERY, "right": _MARKET_CORR20,
     "mechanism": "vt_recovery_frac_confirmed_by_market_corr_20",
     "hypothesis": "A=同上。B=与篮子相关系数20日(market_sensitivity,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- VT_TROUGH_VOL_POS_20: first pairing batch ----
    {"id": "WD1", "operator": "rank_spread", "left": _VT_TROUGH_POS, "right": _AD_PRICE_CORR,
     "mechanism": "vt_trough_vol_pos_confirmed_by_ad_price_corr_20",
     "hypothesis": "A=成交量时间最大回撤谷底所在的成交量相对位置20日均值(体检disc-0.0786/审计-0.0434同向,corr 0.68边界)。B=A/D净流与价格相关20日(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WD2", "operator": "rank_spread", "left": _VT_TROUGH_POS, "right": _COKURT60,
     "mechanism": "vt_trough_vol_pos_confirmed_by_cokurt_60",
     "hypothesis": "A=同上。B=共峰度60日(coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WD3", "operator": "rank_spread", "left": _VT_TROUGH_POS, "right": _WORST_DAY60,
     "mechanism": "vt_trough_vol_pos_confirmed_by_worst_day_60",
     "hypothesis": "A=同上。B=60日最差单日收益(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WD4", "operator": "rank_spread", "left": _VT_TROUGH_POS, "right": _RET_ACF2_20,
     "mechanism": "vt_trough_vol_pos_confirmed_by_ret_acf2_20",
     "hypothesis": "A=同上。B=收益2阶自相关20日(serial_dependence,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WD5", "operator": "rank_spread", "left": _VT_TROUGH_POS, "right": _BENCHMARK_RESID_VOL20,
     "mechanism": "vt_trough_vol_pos_confirmed_by_benchmark_residual_vol_20",
     "hypothesis": "A=同上。B=对篮子残差波动20日(market_sensitivity,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- VT_MAXDD_CHG_20: first pairing batch (sign-flip atom, smaller batch) ----
    {"id": "WE1", "operator": "rank_spread", "left": _VT_MAXDD_CHG, "right": _OBV_SLOPE_CHG,
     "mechanism": "vt_maxdd_chg_confirmed_by_obv_slope_chg_20",
     "hypothesis": "A=成交量时间最大回撤20日变化(体检disc-0.0226/审计+0.0634,符号翻转不稳)。B=OBV斜率20日变化(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定，本条方向不确定性高。",
     "expected_sign": -1},
    {"id": "WE2", "operator": "rank_spread", "left": _VT_MAXDD_CHG, "right": _MAX5_MEAN20,
     "mechanism": "vt_maxdd_chg_confirmed_by_max5_mean_20",
     "hypothesis": "A=同上。B=最大5日收益均值(S2,upside_tail,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WE3", "operator": "rank_spread", "left": _VT_MAXDD_CHG, "right": _GAP_FILL60,
     "mechanism": "vt_maxdd_chg_confirmed_by_gap_fill_fraction_60",
     "hypothesis": "A=同上。B=跳空当日回补比例60日(gap_repair,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "WE4", "operator": "rank_spread", "left": _VT_MAXDD_CHG, "right": _TAIL_Q10_60,
     "mechanism": "vt_maxdd_chg_confirmed_by_tail_q10_60",
     "hypothesis": "A=同上。B=收益10%分位尾部60日(return_tail_shape,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- VT_PATH_EFFICIENCY_20: first pairing batch (sign-flip atom, smaller batch) ----
    {"id": "WF1", "operator": "rank_spread", "left": _VT_PATH_EFF, "right": _MFI_14_MEAN,
     "mechanism": "vt_path_efficiency_confirmed_by_mfi_14_mean_20",
     "hypothesis": "A=成交量时间路径效率20日均值(体检disc+0.0197/审计-0.0276,符号翻转不稳)。B=MFI(14)均值20日(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定，本条方向不确定性高。",
     "expected_sign": 1},
    {"id": "WF2", "operator": "rank_spread", "left": _VT_PATH_EFF, "right": _POS_DAY_FRAC_Z,
     "mechanism": "vt_path_efficiency_confirmed_by_pos_day_frac_z_20",
     "hypothesis": "A=同上。B=正收益日占比20日z分数(S2,upside_tail,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "WF3", "operator": "rank_spread", "left": _VT_PATH_EFF, "right": _INTRADAY_MAXBAR_RET,
     "mechanism": "vt_path_efficiency_confirmed_by_intraday_maxbar_ret_20",
     "hypothesis": "A=同上。B=日内1m最大单bar收益20日均值(S2彩票代理,upside_tail,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "WF4", "operator": "rank_spread", "left": _VT_PATH_EFF, "right": _RET_ACF1_60,
     "mechanism": "vt_path_efficiency_confirmed_by_ret_acf1_60",
     "hypothesis": "A=同上。B=收益1阶自相关60日(serial_dependence,本族首次配对)。假设方向由发现期定。本批最后一条，本轮末条，本族8原子左腿配额全部用尽。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
