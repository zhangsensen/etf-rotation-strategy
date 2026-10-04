#!/usr/bin/env python3
"""Round 571 driver: S15 stage step 1 -- relative_path_vs_basket_1m
family (controller-specified 2026-09-20 20:03), reapplying S7's
drawdown/recovery geometry and S6's permutation entropy to the ACTIVE
return path (asset minus 510300/510500 basket proxy) rather than the
absolute price path. Note: this line's round_570 completed a separate,
self-directed "S15" (money_flow_extremes_1m, deepening S10) in the same
turn the controller specified this official S15 -- round_570's outputs
retain their own S15_money_flow_extremes_1m label; this is a distinct
stage under the same "S15" number as issued by the controller.

Atom health (round_571_atom_health, vs intraday_drawdown_1m/
permutation_entropy_1m/market_relative_strength/path_efficiency): only 1
of 8 atoms is shadow -- UNDERWATER_FRAC_DIFF_20 (0.89 vs
intraday_drawdown_1m:UNDERWATER_FRAC_20, expected since it's directly
derived by subtracting the active-path underwater fraction from the
absolute one). The other 7 are non-shadow (0.22-0.70) -- applying
familiar path geometry to the genuinely new ACTIVE-return object
produces mostly independent signal, unlike S11/S12's deepenings which
stayed closer to their seed atoms' correlation structure.

This round: 8 atomic (all new atoms) + 2 first pairing batches for the
two strongest atoms by |discovery IC|, UNDERWATER_FRAC_DIFF_20 (shadow,
prioritized per this line's established shadow-rescue heuristic) and
REL_MAXDD_20 (non-shadow, right at the 0.70 threshold) = 24 candidates,
within the 15-30 band."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_571"

_HKS_SLOT = {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"}
_TRACK_ERR20 = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}
_RS_RATIO = {"name": "RS_RV_RATIO_20", "source": "range_based_vol_1m"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_YZ_OVERNIGHT = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}

_OVERNIGHT_DIFF = {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"}
_REL_MOM60 = {"name": "REL_MARKET_MOM_60", "source": "market_relative_strength"}
_CAT_DISP20 = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_GK_RATIO = {"name": "GK_RV_RATIO_20", "source": "range_based_vol_1m"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}
_UF_Z60 = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}
_PERM_ENTROPY_RET = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}

_REL_UF = {"name": "REL_UNDERWATER_FRAC_20", "source": "relative_path_vs_basket_1m"}
_REL_UF_CHG = {"name": "REL_UNDERWATER_FRAC_CHG_20", "source": "relative_path_vs_basket_1m"}
_REL_MAXDD = {"name": "REL_MAXDD_20", "source": "relative_path_vs_basket_1m"}
_REL_MAXDD_CHG = {"name": "REL_MAXDD_CHG_20", "source": "relative_path_vs_basket_1m"}
_REL_RECOVERY = {"name": "REL_RECOVERY_FRAC_20", "source": "relative_path_vs_basket_1m"}
_REL_PERM_ENTROPY = {"name": "REL_PERM_ENTROPY_20", "source": "relative_path_vs_basket_1m"}
_REL_PATH_EFF = {"name": "REL_PATH_EFFICIENCY_20", "source": "relative_path_vs_basket_1m"}
_UF_DIFF = {"name": "UNDERWATER_FRAC_DIFF_20", "source": "relative_path_vs_basket_1m"}

base.CANDIDATES = [
    # ---- 8 atomic: new relative_path_vs_basket_1m atoms ----
    {
        "id": "NA1",
        "operator": "atomic",
        "left": _REL_UF,
        "right": _REL_UF,
        "mechanism": "rel_underwater_frac_20",
        "hypothesis": "主动1m收益累积路径的日内水下占比(Chekhlov-Uryasev-Zabarankin 2005框架用于主动收益),20日均值。体检:disc-0.0152/579天/审计-0.0405,max|corr|=0.44(vs intraday_drawdown_1m:UNDERWATER_FRAC_20),非shadow。假设:主动水下占比高(A高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "NA2",
        "operator": "atomic",
        "left": _REL_UF_CHG,
        "right": _REL_UF_CHG,
        "mechanism": "rel_underwater_frac_chg_20",
        "hypothesis": "REL_UNDERWATER_FRAC_20的20日变化。体检:disc-0.0332/审计-0.0761,max|corr|=0.49,非shadow。假设:主动水下占比正在上升(A高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "NA3",
        "operator": "atomic",
        "left": _REL_MAXDD,
        "right": _REL_MAXDD,
        "mechanism": "rel_maxdd_20",
        "hypothesis": "主动收益累积路径的日内最大回撤(加法,收益单位),20日均值。体检:disc-0.1003/审计-0.0879,max|corr|=0.70(vs intraday_drawdown_1m:INTRADAY_CDAR_20),非shadow(恰在阈值),本族disc_ic绝对值第二大原子。假设:主动最大回撤大(A高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "NA4",
        "operator": "atomic",
        "left": _REL_MAXDD_CHG,
        "right": _REL_MAXDD_CHG,
        "mechanism": "rel_maxdd_chg_20",
        "hypothesis": "REL_MAXDD_20的20日变化。体检:disc-0.0177/审计-0.0024,max|corr|=0.60,非shadow。假设:主动最大回撤正在扩大(A高)=延续,负相关(弱)。",
        "expected_sign": -1,
    },
    {
        "id": "NA5",
        "operator": "atomic",
        "left": _REL_RECOVERY,
        "right": _REL_RECOVERY,
        "mechanism": "rel_recovery_frac_20",
        "hypothesis": "S12恢复时间占比构造应用于主动路径:主动回撤谷底回到前高的bar数占全日比例(未恢复记1),20日均值。体检:disc-0.0073/审计-0.0594,max|corr|=0.34(vs intraday_drawdown_1m:DD_RUNUP_ASYM_20),非shadow(本族最独立原子之一)。假设:主动恢复耗时占比高(A高)=延续,负相关(弱)。",
        "expected_sign": -1,
    },
    {
        "id": "NA6",
        "operator": "atomic",
        "left": _REL_PERM_ENTROPY,
        "right": _REL_PERM_ENTROPY,
        "mechanism": "rel_perm_entropy_20",
        "hypothesis": "Bandt-Pompe(2002)排列熵应用于主动收益序列(而非S6的绝对收益序列),d=3,20日均值。体检:disc-0.0103/审计-0.0284,max|corr|=0.22,非shadow,本族最独立原子。假设:主动收益排列熵高(A高,更随机)=延续,负相关(弱)。",
        "expected_sign": -1,
    },
    {
        "id": "NA7",
        "operator": "atomic",
        "left": _REL_PATH_EFF,
        "right": _REL_PATH_EFF,
        "mechanism": "rel_path_efficiency_20",
        "hypothesis": "Kaufman效率比应用于主动路径:主动路径终点位移绝对值/路径总长度,20日均值。体检:disc-0.0228/审计-0.0054,max|corr|=0.38(vs permutation_entropy_1m:ENTROPY_RET_VOL_DIFF_20),非shadow。假设:主动路径效率高(A高,方向性强)=延续,负相关(弱)。",
        "expected_sign": -1,
    },
    {
        "id": "NA8",
        "operator": "atomic",
        "left": _UF_DIFF,
        "right": _UF_DIFF,
        "mechanism": "underwater_frac_diff_20",
        "hypothesis": "绝对水下占比减主动水下占比(篮子对个体回撤的贡献份额),20日均值。体检:disc-0.1172/审计-0.0621,max|corr|=0.89(vs intraday_drawdown_1m:UNDERWATER_FRAC_20),标记shadow,本族disc_ic绝对值最大原子。假设:篮子贡献份额高(A高,系统性回撤为主)=延续,负相关。",
        "expected_sign": -1,
    },
    # ---- UNDERWATER_FRAC_DIFF_20: first pairing batch (shadow, prioritized) ----
    {
        "id": "NB1",
        "operator": "rank_spread",
        "left": _UF_DIFF,
        "right": _HKS_SLOT,
        "mechanism": "underwater_frac_diff_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=绝对vs主动水下占比之差(体检disc-0.1172,shadow)。B=日内时段模式持续性(intraday_periodicity,S4阶段命中partner,本族首次配对)。假设:篮子贡献份额高(A高)且日内时段模式稳定(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "NB2",
        "operator": "rank_spread",
        "left": _UF_DIFF,
        "right": _TRACK_ERR20,
        "mechanism": "underwater_frac_diff_confirmed_by_tracking_error_20",
        "hypothesis": "A=同上。B=相对基准跟踪误差,20日(market_relative_strength,本族首次配对)。假设:篮子贡献份额高(A高)且跟踪误差低(B低,系统性强)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "NB3",
        "operator": "rank_spread",
        "left": _UF_DIFF,
        "right": _RS_RATIO,
        "mechanism": "underwater_frac_diff_confirmed_by_rs_rv_ratio_20",
        "hypothesis": "A=同上。B=Rogers-Satchell区间估计/RV之比(range_based_vol_1m,S9阶段本族唯一有信号比值,本族首次配对)。假设:篮子贡献份额高(A高)且bar内活动占比低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "NB4",
        "operator": "rank_spread",
        "left": _UF_DIFF,
        "right": _SAMPEN,
        "mechanism": "underwater_frac_diff_confirmed_by_sampen_ret_20",
        "hypothesis": "A=同上。B=1m收益样本熵(complexity_measures_1m,S11阶段本族原子,本族首次配对)。假设:篮子贡献份额高(A高)且样本熵低(B低,结构性强)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "NB5",
        "operator": "rank_spread",
        "left": _UF_DIFF,
        "right": _GAP_FILL60,
        "mechanism": "underwater_frac_diff_confirmed_by_gap_fill_fraction_60",
        "hypothesis": "A=同上。B=跳空回补比例,60日(gap_repair,本族首次配对)。假设:篮子贡献份额高(A高)且跳空回补比例高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "NB6",
        "operator": "rank_spread",
        "left": _UF_DIFF,
        "right": _DEP_DRIFT,
        "mechanism": "underwater_frac_diff_confirmed_by_dep_drift_20",
        "hypothesis": "A=同上。B=依赖漂移指标(cross_dependence_1m,S10阶段NI8的制胜partner,本族首次配对)。假设:篮子贡献份额高(A高)且依赖漂移方向按discovery定(B)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "NB7",
        "operator": "rank_spread",
        "left": _UF_DIFF,
        "right": _CHIP_RANGE,
        "mechanism": "underwater_frac_diff_confirmed_by_chip_range_90_60",
        "hypothesis": "A=同上。B=90分位筹码分布宽度(cost_distribution,本族首次配对)。假设:篮子贡献份额高(A高)且筹码分布窄(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "NB8",
        "operator": "rank_spread",
        "left": _UF_DIFF,
        "right": _YZ_OVERNIGHT,
        "mechanism": "underwater_frac_diff_confirmed_by_yz_overnight_share_20",
        "hypothesis": "A=同上。B=Yang-Zhang隔夜方差占比(range_based_vol_1m,S9阶段唯一净入选原子,本族首次配对)。假设:篮子贡献份额高(A高)且隔夜驱动为主(B高)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- REL_MAXDD_20: first pairing batch ----
    {
        "id": "NC1",
        "operator": "rank_spread",
        "left": _REL_MAXDD,
        "right": _OVERNIGHT_DIFF,
        "mechanism": "rel_maxdd_confirmed_by_overnight_intra_diff_20",
        "hypothesis": "A=主动最大回撤(体检disc-0.1003,本族disc_ic绝对值第二大)。B=隔夜与日内收益差异(intraday_periodicity,本族首次配对)。假设:主动最大回撤大(A高)且隔夜/日内分化明显(B按discovery定)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "NC2",
        "operator": "rank_spread",
        "left": _REL_MAXDD,
        "right": _REL_MOM60,
        "mechanism": "rel_maxdd_confirmed_by_relative_market_momentum_60",
        "hypothesis": "A=同上。B=相对基准篮子动量,60日(market_relative_strength,本族首次配对)。假设:主动最大回撤大(A高)且相对动量弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "NC3",
        "operator": "rank_spread",
        "left": _REL_MAXDD,
        "right": _CAT_DISP20,
        "mechanism": "rel_maxdd_confirmed_by_category_dispersion_20",
        "hypothesis": "A=同上。B=板块内部20日收益离散度(category_state,本族首次配对)。假设:主动最大回撤大(A高)且板块内部分化大(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "NC4",
        "operator": "rank_spread",
        "left": _REL_MAXDD,
        "right": _AMIHUD_1M,
        "mechanism": "rel_maxdd_confirmed_by_amihud_1m_20",
        "hypothesis": "A=同上。B=Amihud非流动性比率1m版本(microstructure_1m,本族首次配对)。假设:主动最大回撤大(A高)且非流动性高(B高)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "NC5",
        "operator": "rank_spread",
        "left": _REL_MAXDD,
        "right": _GK_RATIO,
        "mechanism": "rel_maxdd_confirmed_by_gk_rv_ratio_20",
        "hypothesis": "A=同上。B=Garman-Klass区间估计/RV之比(range_based_vol_1m,S9阶段本族原子,本族首次配对)。假设:主动最大回撤大(A高)且bar内活动占比高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "NC6",
        "operator": "rank_spread",
        "left": _REL_MAXDD,
        "right": _GAP_SESSION_CORR,
        "mechanism": "rel_maxdd_confirmed_by_gap_session_correlation_20",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性(gap_response,S4阶段最强命中partner,t=3.89,本族首次配对)。假设:主动最大回撤大(A高)且跳空延续性强(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "NC7",
        "operator": "rank_spread",
        "left": _REL_MAXDD,
        "right": _UF_Z60,
        "mechanism": "rel_maxdd_confirmed_by_underwater_frac_z_60",
        "hypothesis": "A=同上。B=水下时间占比60日z分数(intraday_pain_recovery_1m,S12阶段本族唯一净入选原子,本族首次配对)。假设:主动最大回撤大(A高)且绝对水下占比异常偏高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "NC8",
        "operator": "rank_spread",
        "left": _REL_MAXDD,
        "right": _PERM_ENTROPY_RET,
        "mechanism": "rel_maxdd_confirmed_by_perm_entropy_ret_20",
        "hypothesis": "A=同上。B=1m收益排列熵(permutation_entropy_1m,S6阶段全线首个不含成交量两窗口显著原子,本族首次配对)。假设:主动最大回撤大(A高)且绝对收益排列熵高(B高,更随机)=延续;本族最后一批。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
