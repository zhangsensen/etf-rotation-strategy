#!/usr/bin/env python3
"""Round 603 driver: S24 stage step 1 -- volume_time_1m family (Clark
1973 subordinated volume clock; Ane-Geman 2000; Easley-Lopez de
Prado-O'Hara 2012 -- fixed reference bucket VOLUME size, variable bucket
COUNT per day, the standard volume-clock construction, distinct from
S23's fixed-count/variable-size design), main controller's pre-specified
S24 direction after S23's closure (round_602), built as a parallel
independent implementation alongside pi lane's stage 17 -- NOT built by
reading pi's code, only the literature definitions and the two required
right-leg formulas supplied in the directive.

Atom health (round_603_atom_health, vs volume_time_drawdown,
bar_size_order_flow, largebar_footprint_1m, intraday_volume_profile_1m):
2/8 atoms shadow (RV_V_20 corr 0.90 vs S23's VT_MAXDD_20; VT_BUCKET_GINI_20
corr 0.83 vs bar_size_order_flow:BIGBAR_VOL_SHARE_20). The directive's two
required right legs (VOL_SPIKE_FREQ_20, OPEN30_VOL_SHARE_20) were already
implemented in this codebase under intraday_volume_profile_1m (built in
an earlier, already-compacted portion of this session) -- reused directly
per the 'no reinventing the wheel' rule rather than rebuilt.

Per the directive, this round tests all 8 atomically, then runs the
first pairing batch for the two atoms named in pi's CO36/CR08 candidates
(VT_AUTOCORR_20, VT_BUCKET_COUNT_SHIFT_20), each batch including the
exact CO36/CR08 right leg as one of 8 candidates. The remaining 6 atoms
(RV_V_20, RV_V_RATIO_20, VT_RET_SKEW_20, VT_BUCKET_GINI_20,
VT_BUCKET_COUNT_20, VT_LATE_MOM_20) remain eligible for a future round
per the pairing-discipline rule."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_603"

_RV_V = {"name": "RV_V_20", "source": "volume_time_1m"}
_RV_V_RATIO = {"name": "RV_V_RATIO_20", "source": "volume_time_1m"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_VT_RET_SKEW = {"name": "VT_RET_SKEW_20", "source": "volume_time_1m"}
_VT_BUCKET_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_VT_BUCKET_COUNT = {"name": "VT_BUCKET_COUNT_20", "source": "volume_time_1m"}
_VT_BUCKET_COUNT_SHIFT = {"name": "VT_BUCKET_COUNT_SHIFT_20", "source": "volume_time_1m"}
_VT_LATE_MOM = {"name": "VT_LATE_MOM_20", "source": "volume_time_1m"}

_VOL_SPIKE_FREQ = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_LUNCH_PRERUN_POSTRUN = {"name": "LUNCH_PRERUN_POSTRUN_RATIO_20", "source": "lunch_break_1m"}
_ON_SIGN_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}
_TRR = {"name": "TRUE_RANGE_RATIO_20", "source": "range_contraction_cycle"}
_D1_60 = {"name": "D1_LEVEL_60", "source": "price_delay"}
_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_COSKEW20 = {"name": "COSKEW_20", "source": "coskewness_risk"}

_OPEN30_VOL_SHARE = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_BEST_DAY = {"name": "BEST_DAY_20", "source": "upside_tail"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}
_VAR_RATIO = {"name": "VAR_RATIO_5_60", "source": "serial_dependence"}

base.CANDIDATES = [
    # ---- 8 atomic: new volume_time_1m atoms ----
    {
        "id": "XA1", "operator": "atomic", "left": _RV_V, "right": _RV_V,
        "mechanism": "rv_v_20",
        "hypothesis": "成交量钟已实现方差(固定参考桶量=前20日均日成交量/50,今日成交量不参与定桶)20日均值。体检:disc-0.1047/审计-0.0772(同向)，shadow(corr 0.90 vs S23 volume_time_drawdown:VT_MAXDD_20)。",
        "expected_sign": -1,
    },
    {
        "id": "XA2", "operator": "atomic", "left": _RV_V_RATIO, "right": _RV_V_RATIO,
        "mechanism": "rv_v_ratio_20",
        "hypothesis": "成交量钟RV/日历RV之比20日均值(噪声吸收度)。体检:disc-0.1040/审计-0.0380(同向但审计衰减)，非shadow(corr 0.61)。",
        "expected_sign": -1,
    },
    {
        "id": "XA3", "operator": "atomic", "left": _VT_AUTOCORR, "right": _VT_AUTOCORR,
        "mechanism": "vt_autocorr_20",
        "hypothesis": "成交量时间收益1桶滞后自相关20日均值(Easley-LdP-OHara 2012;pi CO36左腿)。体检:disc-0.0642/审计-0.0516(同向)，非shadow(corr 0.40)，本轮首个配对左腿。",
        "expected_sign": -1,
    },
    {
        "id": "XA4", "operator": "atomic", "left": _VT_RET_SKEW, "right": _VT_RET_SKEW,
        "mechanism": "vt_ret_skew_20",
        "hypothesis": "成交量时间收益偏度20日均值。体检:disc-0.0028/审计+0.0155(接近零,符号不稳)，非shadow(corr 0.27)。",
        "expected_sign": -1,
    },
    {
        "id": "XA5", "operator": "atomic", "left": _VT_BUCKET_GINI, "right": _VT_BUCKET_GINI,
        "mechanism": "vt_bucket_gini_20",
        "hypothesis": "等量桶日历时长分布Gini系数20日均值。体检:disc+0.0522/审计+0.0022(同向但审计接近零)，shadow(corr 0.83 vs bar_size_order_flow:BIGBAR_VOL_SHARE_20)。",
        "expected_sign": 1,
    },
    {
        "id": "XA6", "operator": "atomic", "left": _VT_BUCKET_COUNT, "right": _VT_BUCKET_COUNT,
        "mechanism": "vt_bucket_count_20",
        "hypothesis": "当日实现的等量桶数(相对固定参考桶量)20日均值。体检:disc-0.0257/审计+0.0684(符号翻转)，非shadow(corr 0.26)。",
        "expected_sign": -1,
    },
    {
        "id": "XA7", "operator": "atomic", "left": _VT_BUCKET_COUNT_SHIFT, "right": _VT_BUCKET_COUNT_SHIFT,
        "mechanism": "vt_bucket_count_shift_20",
        "hypothesis": "等量桶数20日变化(今日成交量相对近期参考的regime;pi CR08左腿)。体检:disc-0.0403/审计+0.0612(符号翻转)，非shadow(corr 0.18)，本轮第二个配对左腿。",
        "expected_sign": -1,
    },
    {
        "id": "XA8", "operator": "atomic", "left": _VT_LATE_MOM, "right": _VT_LATE_MOM,
        "mechanism": "vt_late_mom_20",
        "hypothesis": "最后20%等量桶收益之和20日均值(成交量时间尾段动量)。体检:disc+0.0046/审计+0.0403(同向弱)，非shadow(corr 0.35)。",
        "expected_sign": 1,
    },
    # ---- VT_AUTOCORR_20: first pairing batch (includes pi CO36's exact right leg) ----
    {"id": "XB1", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _VOL_SPIKE_FREQ,
     "mechanism": "vt_autocorr_confirmed_by_vol_spike_freq_20",
     "hypothesis": "A=成交量时间收益1桶滞后自相关20日(体检disc-0.0642/审计-0.0516同向)。B=1m成交量超过当日均量3σ的bar占比20日均值(pi CO36原表达式的右腿,复用已有intraday_volume_profile_1m原子)。假设方向由发现期定，本条是必测的pi CO36对照。",
     "expected_sign": -1},
    {"id": "XB2", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _UF_CHG,
     "mechanism": "vt_autocorr_confirmed_by_underwater_frac_chg_20",
     "hypothesis": "A=同上。B=日内水下占比20日变化(S7本线单原子审计最高,intraday_drawdown_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XB3", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _LUNCH_PRERUN_POSTRUN,
     "mechanism": "vt_autocorr_confirmed_by_lunch_prerun_postrun_ratio_20",
     "hypothesis": "A=同上。B=午前/午后抢跑成交量份额之比(S22原子级入选KA7,lunch_break_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XB4", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _ON_SIGN_STREAK,
     "mechanism": "vt_autocorr_confirmed_by_on_sign_streak_20",
     "hypothesis": "A=同上。B=隔夜收益符号连续天数(S21入选原子HB1的左腿,overnight_structure_1d,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XB5", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _TRR,
     "mechanism": "vt_autocorr_confirmed_by_true_range_ratio_20",
     "hypothesis": "A=同上。B=真实区间比率(S19唯一净入选原子AB1,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XB6", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _D1_60,
     "mechanism": "vt_autocorr_confirmed_by_d1_level_60",
     "hypothesis": "A=同上。B=价格延迟D1水平(S20入选原子搭档,price_delay,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XB7", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _MFI_EXTREME_FRAC,
     "mechanism": "vt_autocorr_confirmed_by_mfi_extreme_frac_20",
     "hypothesis": "A=同上。B=MFI极端占比(S23阶段最强候选WA1的右腿,accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XB8", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _COSKEW20,
     "mechanism": "vt_autocorr_confirmed_by_coskew_20",
     "hypothesis": "A=同上。B=共偏度20日(coskewness_risk,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- VT_BUCKET_COUNT_SHIFT_20: first pairing batch (includes pi CR08's exact right leg) ----
    {"id": "XC1", "operator": "rank_spread", "left": _VT_BUCKET_COUNT_SHIFT, "right": _OPEN30_VOL_SHARE,
     "mechanism": "vt_bucket_count_shift_confirmed_by_open30_vol_share_20",
     "hypothesis": "A=等量桶数20日变化(体检disc-0.0403/审计+0.0612符号翻转)。B=首30分钟成交量占全日比例20日均值(pi CR08原表达式的右腿,复用已有intraday_volume_profile_1m原子)。假设方向由发现期定，本条是必测的pi CR08对照。",
     "expected_sign": -1},
    {"id": "XC2", "operator": "rank_spread", "left": _VT_BUCKET_COUNT_SHIFT, "right": _WORST_DAY,
     "mechanism": "vt_bucket_count_shift_confirmed_by_worst_day_20",
     "hypothesis": "A=同上。B=20日最差单日收益(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XC3", "operator": "rank_spread", "left": _VT_BUCKET_COUNT_SHIFT, "right": _SAMPEN,
     "mechanism": "vt_bucket_count_shift_confirmed_by_sampen_ret_20",
     "hypothesis": "A=同上。B=收益样本熵(S11,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XC4", "operator": "rank_spread", "left": _VT_BUCKET_COUNT_SHIFT, "right": _MARKET_BETA20,
     "mechanism": "vt_bucket_count_shift_confirmed_by_market_beta_20",
     "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XC5", "operator": "rank_spread", "left": _VT_BUCKET_COUNT_SHIFT, "right": _BEST_DAY,
     "mechanism": "vt_bucket_count_shift_confirmed_by_best_day_20",
     "hypothesis": "A=同上。B=20日最佳单日收益(S2,upside_tail,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XC6", "operator": "rank_spread", "left": _VT_BUCKET_COUNT_SHIFT, "right": _GAP_FILL,
     "mechanism": "vt_bucket_count_shift_confirmed_by_gap_fill_fraction_20",
     "hypothesis": "A=同上。B=跳空当日回补比例20日(gap_repair,S18/S22入选原子搭档,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XC7", "operator": "rank_spread", "left": _VT_BUCKET_COUNT_SHIFT, "right": _AD_NET_FLOW,
     "mechanism": "vt_bucket_count_shift_confirmed_by_ad_net_flow_20",
     "hypothesis": "A=同上。B=A/D净流20日(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XC8", "operator": "rank_spread", "left": _VT_BUCKET_COUNT_SHIFT, "right": _VAR_RATIO,
     "mechanism": "vt_bucket_count_shift_confirmed_by_var_ratio_5_60",
     "hypothesis": "A=同上。B=方差比5/60日(serial_dependence,本族首次配对)。假设方向由发现期定。本批最后一条，本轮末条。",
     "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
