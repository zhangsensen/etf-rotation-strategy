#!/usr/bin/env python3
"""Round 570 driver: S15 stage step 1 -- money_flow_extremes_1m family,
a self-directed deepening of S10's single strongest finding (NI8:
MFI_EXTREME_FRAC_20 x DEP_DRIFT_20, discovery block-t=4.88, the highest
recorded anywhere in this line). See the family module's docstring for
the process-correction note: round_570 initially and mistakenly
attempted to re-register S10 itself, which this line's own history
(outputs/round_540) shows already closed. This driver instead follows
this line's established "deepen the strongest channel" pattern (S6->S11,
S7->S12) applied to S10.

Atom health (round_570_atom_health, vs accumulation_distribution_1m/
cross_dependence_1m/bar_size_order_flow): 5 of 8 atoms are shadow, all at
extreme correlation (0.89-0.94) against S10's own MFI_EXTREME_FRAC_20 or
MFI_14_MEAN_20 -- expected, since HI/LO/ASYM/STREAK/VOL_CONC are all
different weightings of the same underlying MFI-extremity signal S10
already captured in pooled form. The 3 non-shadow atoms (TOD_SKEW 0.39,
FRAC_CHG 0.19 [most independent], REVERSAL_HITRATE 0.34) are the
genuinely new facets: timing, trend, and reversal-quality.

This round: 8 atomic (all new atoms) + 2 first pairing batches for
MFI_EXTREME_HI_FRAC_20 (shadow but strongest |disc IC|, prioritized per
this line's established shadow-rescue heuristic -- and directly tests
whether S10's winning DEP_DRIFT_20 partner still works on the directional
decomposition) and MFI_EXTREME_TOD_SKEW_20 (non-shadow, most independent
economically distinct facet) = 24 candidates, within the 15-30 band."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_570"

_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_HKS_SLOT = {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"}
_TRACK_ERR20 = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}
_RS_RATIO = {"name": "RS_RV_RATIO_20", "source": "range_based_vol_1m"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_UF_Z60 = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}
_PERM_ENTROPY_RET = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}

_OVERNIGHT_DIFF = {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"}
_REL_MOM60 = {"name": "REL_MARKET_MOM_60", "source": "market_relative_strength"}
_CAT_DISP20 = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_GK_RATIO = {"name": "GK_RV_RATIO_20", "source": "range_based_vol_1m"}
_YZ_OVERNIGHT = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}

_HI_FRAC = {"name": "MFI_EXTREME_HI_FRAC_20", "source": "money_flow_extremes_1m"}
_LO_FRAC = {"name": "MFI_EXTREME_LO_FRAC_20", "source": "money_flow_extremes_1m"}
_ASYM = {"name": "MFI_EXTREME_ASYM_20", "source": "money_flow_extremes_1m"}
_STREAK = {"name": "MFI_EXTREME_STREAK_20", "source": "money_flow_extremes_1m"}
_TOD_SKEW = {"name": "MFI_EXTREME_TOD_SKEW_20", "source": "money_flow_extremes_1m"}
_FRAC_CHG = {"name": "MFI_EXTREME_FRAC_CHG_20", "source": "money_flow_extremes_1m"}
_REVERSAL = {"name": "MFI_REVERSAL_HITRATE_20", "source": "money_flow_extremes_1m"}
_VOL_CONC = {"name": "MFI_EXTREME_VOL_CONC_20", "source": "money_flow_extremes_1m"}

base.CANDIDATES = [
    # ---- 8 atomic: new money_flow_extremes_1m atoms ----
    {
        "id": "MA1",
        "operator": "atomic",
        "left": _HI_FRAC,
        "right": _HI_FRAC,
        "mechanism": "mfi_extreme_hi_frac_20",
        "hypothesis": "日内MFI>80(超买/买方极端)的bar占比,20日均值。体检:disc+0.0773/579天/审计+0.0420,max|corr|=0.89(vs accumulation_distribution_1m:MFI_EXTREME_FRAC_20,S10已admitted原子),标记shadow。假设:买方极端占比高(A高)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "MA2",
        "operator": "atomic",
        "left": _LO_FRAC,
        "right": _LO_FRAC,
        "mechanism": "mfi_extreme_lo_frac_20",
        "hypothesis": "日内MFI<20(超卖/卖方极端)的bar占比,20日均值。体检:disc+0.0663/审计+0.0350,max|corr|=0.91(vs同一S10原子),shadow。假设方向同HI_FRAC。",
        "expected_sign": 1,
    },
    {
        "id": "MA3",
        "operator": "atomic",
        "left": _ASYM,
        "right": _ASYM,
        "mechanism": "mfi_extreme_asym_20",
        "hypothesis": "HI_frac减LO_frac(净方向性极端偏向),20日均值。体检:disc+0.0338/审计+0.0215,max|corr|=0.93(vs accumulation_distribution_1m:MFI_14_MEAN_20),shadow。假设:净偏向买方极端(A高)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "MA4",
        "operator": "atomic",
        "left": _STREAK,
        "right": _STREAK,
        "mechanism": "mfi_extreme_streak_20",
        "hypothesis": "Wilder(1978)持续性框架:日内最长连续极端bar占全日比例,20日均值。体检:disc+0.0655/审计+0.0458,max|corr|=0.94(vs S10 MFI_EXTREME_FRAC_20),shadow。假设:极端持续性强(A高)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "MA5",
        "operator": "atomic",
        "left": _TOD_SKEW,
        "right": _TOD_SKEW,
        "mechanism": "mfi_extreme_tod_skew_20",
        "hypothesis": "Admati-Pfleiderer(1988)日内模式框架:极端bar出现时刻均值相对全天中点的偏移,20日均值。体检:disc-0.0799/审计-0.0083,max|corr|=0.39(vs downside_risk族),非shadow,本族原子中disc_ic绝对值最大。假设:极端偏向尾盘(A高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "MA6",
        "operator": "atomic",
        "left": _FRAC_CHG,
        "right": _FRAC_CHG,
        "mechanism": "mfi_extreme_frac_chg_20",
        "hypothesis": "MFI极端占比(两端汇总)的20日变化,本族内自包含重算S10自身原子。体检:disc+0.0391/审计-0.0260,max|corr|=0.19,非shadow,本族最独立原子。假设:极端占比正在上升(A高)=延续,正相关(弱)。",
        "expected_sign": 1,
    },
    {
        "id": "MA7",
        "operator": "atomic",
        "left": _REVERSAL,
        "right": _REVERSAL,
        "mechanism": "mfi_reversal_hitrate_20",
        "hypothesis": "Wilder(1978)反转质量框架:极端bar后5-bar收益方向与极端方向相反的命中率,20日均值。体检:disc+0.0349/审计-0.0029,max|corr|=0.34(vs gap_volatility族历史shelf key),非shadow。假设:反转命中率高(A高,极端信号质量好)=延续,正相关(弱)。",
        "expected_sign": 1,
    },
    {
        "id": "MA8",
        "operator": "atomic",
        "left": _VOL_CONC,
        "right": _VOL_CONC,
        "mechanism": "mfi_extreme_vol_conc_20",
        "hypothesis": "Easley-Kiefer-O'Hara-Paperman(1996)PIN式框架:极端MFI bar占全日成交量比例,20日均值。体检:disc+0.0637/审计+0.0457,max|corr|=0.92(vs S10 MFI_EXTREME_FRAC_20),shadow。假设:极端bar携带更多成交量(A高)=延续,正相关。",
        "expected_sign": 1,
    },
    # ---- MFI_EXTREME_HI_FRAC_20: first pairing batch (shadow, prioritized) ----
    {
        "id": "MB1",
        "operator": "rank_spread",
        "left": _HI_FRAC,
        "right": _DEP_DRIFT,
        "mechanism": "mfi_hi_frac_confirmed_by_dep_drift_20",
        "hypothesis": "A=买方极端占比(体检disc+0.0773,shadow)。B=依赖漂移指标(cross_dependence_1m,S10阶段NI8的制胜partner,本族首次配对,直接测试同一partner对方向分解版原子是否仍有效)。假设:买方极端占比高(A高)且依赖漂移方向按discovery定(B)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB2",
        "operator": "rank_spread",
        "left": _HI_FRAC,
        "right": _HKS_SLOT,
        "mechanism": "mfi_hi_frac_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=同上。B=日内时段模式持续性(intraday_periodicity,S4阶段命中partner,本族首次配对)。假设:买方极端占比高(A高)且日内时段模式稳定(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB3",
        "operator": "rank_spread",
        "left": _HI_FRAC,
        "right": _TRACK_ERR20,
        "mechanism": "mfi_hi_frac_confirmed_by_tracking_error_20",
        "hypothesis": "A=同上。B=相对基准跟踪误差,20日(market_relative_strength,本族首次配对)。假设:买方极端占比高(A高)且跟踪误差高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB4",
        "operator": "rank_spread",
        "left": _HI_FRAC,
        "right": _RS_RATIO,
        "mechanism": "mfi_hi_frac_confirmed_by_rs_rv_ratio_20",
        "hypothesis": "A=同上。B=Rogers-Satchell区间估计/RV之比(range_based_vol_1m,S9阶段本族唯一有信号比值,本族首次配对)。假设:买方极端占比高(A高)且bar内活动占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB5",
        "operator": "rank_spread",
        "left": _HI_FRAC,
        "right": _SAMPEN,
        "mechanism": "mfi_hi_frac_confirmed_by_sampen_ret_20",
        "hypothesis": "A=同上。B=1m收益样本熵(complexity_measures_1m,S11阶段本族原子,本族首次配对)。假设:买方极端占比高(A高)且样本熵低(B低,结构性更强)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "MB6",
        "operator": "rank_spread",
        "left": _HI_FRAC,
        "right": _UF_Z60,
        "mechanism": "mfi_hi_frac_confirmed_by_underwater_frac_z_60",
        "hypothesis": "A=同上。B=水下时间占比60日z分数(intraday_pain_recovery_1m,S12阶段本族唯一净入选原子,本族首次配对)。假设:买方极端占比高(A高)且水下占比异常偏低(B低)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "MB7",
        "operator": "rank_spread",
        "left": _HI_FRAC,
        "right": _PERM_ENTROPY_RET,
        "mechanism": "mfi_hi_frac_confirmed_by_perm_entropy_ret_20",
        "hypothesis": "A=同上。B=1m收益排列熵(permutation_entropy_1m,S6阶段全线首个不含成交量两窗口显著原子,本族首次配对)。假设:买方极端占比高(A高)且排列熵低(B低)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "MB8",
        "operator": "rank_spread",
        "left": _HI_FRAC,
        "right": _GAP_FILL60,
        "mechanism": "mfi_hi_frac_confirmed_by_gap_fill_fraction_60",
        "hypothesis": "A=同上。B=跳空回补比例,60日(gap_repair,本族首次配对)。假设:买方极端占比高(A高)且跳空回补比例低(B低)=延续;本族最后一批。",
        "expected_sign": 1,
    },
    # ---- MFI_EXTREME_TOD_SKEW_20: first pairing batch ----
    {
        "id": "MC1",
        "operator": "rank_spread",
        "left": _TOD_SKEW,
        "right": _OVERNIGHT_DIFF,
        "mechanism": "mfi_tod_skew_confirmed_by_overnight_intra_diff_20",
        "hypothesis": "A=极端bar出现时刻偏移(体检disc-0.0799,本族最独立原子之一)。B=隔夜与日内收益差异(intraday_periodicity,本族首次配对)。假设:极端偏向尾盘(A高)且隔夜/日内分化明显(B按discovery定)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "MC2",
        "operator": "rank_spread",
        "left": _TOD_SKEW,
        "right": _REL_MOM60,
        "mechanism": "mfi_tod_skew_confirmed_by_relative_market_momentum_60",
        "hypothesis": "A=同上。B=相对基准篮子动量,60日(market_relative_strength,本族首次配对)。假设:极端偏向尾盘(A高)且相对动量弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "MC3",
        "operator": "rank_spread",
        "left": _TOD_SKEW,
        "right": _CAT_DISP20,
        "mechanism": "mfi_tod_skew_confirmed_by_category_dispersion_20",
        "hypothesis": "A=同上。B=板块内部20日收益离散度(category_state,本族首次配对)。假设:极端偏向尾盘(A高)且板块内部分化大(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "MC4",
        "operator": "rank_spread",
        "left": _TOD_SKEW,
        "right": _AMIHUD_1M,
        "mechanism": "mfi_tod_skew_confirmed_by_amihud_1m_20",
        "hypothesis": "A=同上。B=Amihud非流动性比率1m版本(microstructure_1m,本族首次配对)。假设:极端偏向尾盘(A高)且非流动性高(B高)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "MC5",
        "operator": "rank_spread",
        "left": _TOD_SKEW,
        "right": _GK_RATIO,
        "mechanism": "mfi_tod_skew_confirmed_by_gk_rv_ratio_20",
        "hypothesis": "A=同上。B=Garman-Klass区间估计/RV之比(range_based_vol_1m,S9阶段本族原子,本族首次配对)。假设:极端偏向尾盘(A高)且bar内活动占比低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "MC6",
        "operator": "rank_spread",
        "left": _TOD_SKEW,
        "right": _YZ_OVERNIGHT,
        "mechanism": "mfi_tod_skew_confirmed_by_yz_overnight_share_20",
        "hypothesis": "A=同上。B=Yang-Zhang隔夜方差占比(range_based_vol_1m,S9阶段唯一净入选原子,本族首次配对)。假设:极端偏向尾盘(A高)且隔夜驱动为主(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "MC7",
        "operator": "rank_spread",
        "left": _TOD_SKEW,
        "right": _CHIP_RANGE,
        "mechanism": "mfi_tod_skew_confirmed_by_chip_range_90_60",
        "hypothesis": "A=同上。B=90分位筹码分布宽度(cost_distribution,本族首次配对)。假设:极端偏向尾盘(A高)且筹码分布窄(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "MC8",
        "operator": "rank_spread",
        "left": _TOD_SKEW,
        "right": _GAP_SESSION_CORR,
        "mechanism": "mfi_tod_skew_confirmed_by_gap_session_correlation_20",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性(gap_response,S4阶段最强命中partner,t=3.89,本族首次配对)。假设:极端偏向尾盘(A高)且跳空延续性弱(B低)=延续;本族最后一批。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
