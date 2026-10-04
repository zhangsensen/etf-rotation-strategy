#!/usr/bin/env python3
"""Round 561 driver: S12 stage step 1 -- intraday_pain_recovery_1m family
(Martin-McCann 1989 Ulcer Index; Zephyr Pain Index; Magdon-Ismail-Atiya
2004; Grossman-Zhou 1993; Bacon 2008 recovery framing), main controller's
pre-specified S12 direction deepening the S7 channel after S11's closure
(round_560): UNDERWATER_FRAC_CHG_20 (QA8) remains this line's highest
audit-excess single atom (+60.6bp / t 2.88).

Atom health (round_561_atom_health, vs S7's intraday_drawdown_1m/
drawdown_duration/downside_risk): 4 of 8 atoms are shadow --
ULCER_INDEX_20 (0.96) and PAIN_INDEX_20 (0.95) vs INTRADAY_CDAR_20;
ULCER_INDEX_CHG_20 (0.83) and PAIN_INDEX_CHG_20 (0.79) vs
INTRADAY_MAXDD_CHG_20 -- all against OTHER S7 atoms, not QA8 itself.
Exactly as hypothesized, the "depth" framing (ulcer/pain indices, RMS or
mean drawdown magnitude) redundantly restates S7's existing
depth-measures (CDaR, MAXDD), while the "recovery structure" framing is
genuinely new: RECOVERY_TIME_FRAC_20 (0.47), DD_RECOVERY_SPEED_RATIO_20
(0.27), UNDERWATER_FRAC_Z_60 (0.22, notably low even against QA8 itself),
RECOVERY_TIME_FRAC_CHG_20 (0.40) are all non-shadow.

This round: 8 atomic (all new atoms) + 2 first pairing batches for the
two most independent atoms, DD_RECOVERY_SPEED_RATIO_20 and
UNDERWATER_FRAC_Z_60 = 24 candidates, within the 15-30 band."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_561"

_HKS_SLOT = {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"}
_TRACK_ERR20 = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_CONTINUOUS_BETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_LIQ_COMMON_BETA = {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"}
_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}

_OVERNIGHT_DIFF = {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"}
_REL_MOM60 = {"name": "REL_MARKET_MOM_60", "source": "market_relative_strength"}
_CAT_DISP20 = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_GK_RATIO = {"name": "GK_RV_RATIO_20", "source": "range_based_vol_1m"}
_PERM_ENTROPY_RET = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}

_ULCER = {"name": "ULCER_INDEX_20", "source": "intraday_pain_recovery_1m"}
_PAIN = {"name": "PAIN_INDEX_20", "source": "intraday_pain_recovery_1m"}
_ULCER_CHG = {"name": "ULCER_INDEX_CHG_20", "source": "intraday_pain_recovery_1m"}
_PAIN_CHG = {"name": "PAIN_INDEX_CHG_20", "source": "intraday_pain_recovery_1m"}
_RECOVERY_FRAC = {"name": "RECOVERY_TIME_FRAC_20", "source": "intraday_pain_recovery_1m"}
_SPEED_RATIO = {"name": "DD_RECOVERY_SPEED_RATIO_20", "source": "intraday_pain_recovery_1m"}
_UF_Z60 = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}
_RECOVERY_FRAC_CHG = {"name": "RECOVERY_TIME_FRAC_CHG_20", "source": "intraday_pain_recovery_1m"}

base.CANDIDATES = [
    # ---- 8 atomic: new intraday_pain_recovery_1m atoms ----
    {
        "id": "FA1",
        "operator": "atomic",
        "left": _ULCER,
        "right": _ULCER,
        "mechanism": "ulcer_index_20",
        "hypothesis": "Martin-McCann(1989)溃疡指数,日内1m路径分数回撤的均方根,20日均值。体检:disc-0.0965/579天/审计-0.0739,max|corr|=0.96(vs intraday_drawdown_1m:INTRADAY_CDAR_20,S7同族原子),标记shadow。假设:溃疡指数高(A高,深回撤集中)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "FA2",
        "operator": "atomic",
        "left": _PAIN,
        "right": _PAIN,
        "mechanism": "pain_index_20",
        "hypothesis": "Zephyr痛苦指数,日内分数回撤均值(非平方),20日均值。体检:disc-0.0935/审计-0.0763,max|corr|=0.95(vs同一S7原子),shadow。假设方向同溃疡指数。",
        "expected_sign": -1,
    },
    {
        "id": "FA3",
        "operator": "atomic",
        "left": _ULCER_CHG,
        "right": _ULCER_CHG,
        "mechanism": "ulcer_index_chg_20",
        "hypothesis": "ULCER_INDEX_20的20日变化。体检:disc-0.0284/审计+0.0639,max|corr|=0.83(vs intraday_drawdown_1m:INTRADAY_MAXDD_CHG_20),shadow。假设:溃疡指数正在上升(A高)=延续,负相关(符号按discovery定)。",
        "expected_sign": -1,
    },
    {
        "id": "FA4",
        "operator": "atomic",
        "left": _PAIN_CHG,
        "right": _PAIN_CHG,
        "mechanism": "pain_index_chg_20",
        "hypothesis": "PAIN_INDEX_20的20日变化。体检:disc-0.0252/审计+0.0586,max|corr|=0.79(vs同一S7 CHG原子),shadow。假设方向同ULCER_CHG。",
        "expected_sign": -1,
    },
    {
        "id": "FA5",
        "operator": "atomic",
        "left": _RECOVERY_FRAC,
        "right": _RECOVERY_FRAC,
        "mechanism": "recovery_time_frac_20",
        "hypothesis": "Bacon(2008)恢复时间框架:日内最大回撤谷底到前高的bar数占全日比例(未恢复记1),20日均值。体检:disc-0.0462/审计-0.0469,max|corr|=0.47(vs intraday_drawdown_1m:DD_TROUGH_TIMING_20),非shadow——本族最独立原子之一。假设:恢复耗时占比高(A高,难以收复)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "FA6",
        "operator": "atomic",
        "left": _SPEED_RATIO,
        "right": _SPEED_RATIO,
        "mechanism": "dd_recovery_speed_ratio_20",
        "hypothesis": "回撤速度(峰到谷)与恢复速度(谷到前高或日终)之比,20日均值。体检:disc+0.0457/审计-0.0345,max|corr|=0.27,非shadow(本族最独立)。假设:回撤快而恢复慢(A高)=延续,正相关(弱)。",
        "expected_sign": 1,
    },
    {
        "id": "FA7",
        "operator": "atomic",
        "left": _UF_Z60,
        "right": _UF_Z60,
        "mechanism": "underwater_frac_z_60",
        "hypothesis": "水下bar占比的60日滚动z分数(与SHARE_Z_60同规范)。体检:disc-0.0023(接近0)/审计+0.0102,max|corr|=0.22(vs intraday_drawdown_1m:UNDERWATER_FRAC_CHG_20即QA8本身),非shadow,本族相关性最低原子。假设:水下占比异常偏高(A高)=延续(弱,符号按discovery定)。",
        "expected_sign": -1,
    },
    {
        "id": "FA8",
        "operator": "atomic",
        "left": _RECOVERY_FRAC_CHG,
        "right": _RECOVERY_FRAC_CHG,
        "mechanism": "recovery_time_frac_chg_20",
        "hypothesis": "RECOVERY_TIME_FRAC_20的20日变化。体检:disc+0.0186/审计-0.0259,max|corr|=0.40(vs QA8),非shadow。假设:恢复耗时占比正在上升(A高,收复能力恶化)=延续(弱,符号按discovery定)。",
        "expected_sign": 1,
    },
    # ---- DD_RECOVERY_SPEED_RATIO_20: first pairing batch ----
    {
        "id": "FB1",
        "operator": "rank_spread",
        "left": _SPEED_RATIO,
        "right": _HKS_SLOT,
        "mechanism": "speed_ratio_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=回撤/恢复速度比(体检disc+0.0457,本族最独立原子之一)。B=日内时段模式持续性(intraday_periodicity,S4阶段命中partner,本族首次配对)。假设:回撤快恢复慢(A高)且日内时段模式稳定(B高)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "FB2",
        "operator": "rank_spread",
        "left": _SPEED_RATIO,
        "right": _TRACK_ERR20,
        "mechanism": "speed_ratio_confirmed_by_tracking_error_20",
        "hypothesis": "A=同上。B=相对基准跟踪误差,20日(market_relative_strength,本族首次配对)。假设:回撤快恢复慢(A高)且跟踪误差高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "FB3",
        "operator": "rank_spread",
        "left": _SPEED_RATIO,
        "right": _CATEGORY_VOL,
        "mechanism": "speed_ratio_confirmed_by_category_vol_20",
        "hypothesis": "A=同上。B=板块20日波动率(category_state,本族首次配对)。假设:回撤快恢复慢(A高)且板块波动低(B低,个股特异性弱势)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "FB4",
        "operator": "rank_spread",
        "left": _SPEED_RATIO,
        "right": _VOL_SPIKE,
        "mechanism": "speed_ratio_confirmed_by_vol_spike_freq_20",
        "hypothesis": "A=同上。B=成交量突增频率(intraday_volume_profile_1m,本族首次配对)。假设:回撤快恢复慢(A高)且成交放量突增频繁(B高,恐慌抛售)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "FB5",
        "operator": "rank_spread",
        "left": _SPEED_RATIO,
        "right": _GAP_FILL60,
        "mechanism": "speed_ratio_confirmed_by_gap_fill_fraction_60",
        "hypothesis": "A=同上。B=跳空回补比例,60日(gap_repair,本族首次配对)。假设:回撤快恢复慢(A高)且跳空回补比例低(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "FB6",
        "operator": "rank_spread",
        "left": _SPEED_RATIO,
        "right": _CONTINUOUS_BETA60,
        "mechanism": "speed_ratio_confirmed_by_continuous_beta_60",
        "hypothesis": "A=同上。B=对14只等权篮子的连续beta,60日(jump_continuous_beta,S4阶段CONTINUOUS_BETA_60簇最强,本族首次配对)。假设:回撤快恢复慢(A高)且系统性beta高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "FB7",
        "operator": "rank_spread",
        "left": _SPEED_RATIO,
        "right": _LIQ_COMMON_BETA,
        "mechanism": "speed_ratio_confirmed_by_liq_common_beta_20",
        "hypothesis": "A=同上。B=流动性共性beta(liquidity_commonality_1m,本族首次配对)。假设:回撤快恢复慢(A高)且流动性共性高(B高,系统性流动性枯竭)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "FB8",
        "operator": "rank_spread",
        "left": _SPEED_RATIO,
        "right": _BIGBAR_DIR_SKEW,
        "mechanism": "speed_ratio_confirmed_by_bigbar_dir_skew_20",
        "hypothesis": "A=同上。B=大单方向偏度(bar_size_order_flow,本线通道原子之一,本族首次配对)。假设:回撤快恢复慢(A高)且大单方向偏度明显(B按discovery定)=延续;本族最后一批。",
        "expected_sign": 1,
    },
    # ---- UNDERWATER_FRAC_Z_60: first pairing batch ----
    {
        "id": "FC1",
        "operator": "rank_spread",
        "left": _UF_Z60,
        "right": _OVERNIGHT_DIFF,
        "mechanism": "underwater_frac_z60_confirmed_by_overnight_intra_diff",
        "hypothesis": "A=水下占比60日z分数(体检disc-0.0023,本族相关性最低原子,含QA8在内max|corr|=0.22)。B=隔夜与日内收益差异(intraday_periodicity,本族首次配对)。假设:水下占比异常偏高(A高)且隔夜/日内分化明显(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "FC2",
        "operator": "rank_spread",
        "left": _UF_Z60,
        "right": _REL_MOM60,
        "mechanism": "underwater_frac_z60_confirmed_by_relative_market_momentum_60",
        "hypothesis": "A=同上。B=相对基准篮子动量,60日(market_relative_strength,本族首次配对)。假设:水下占比异常偏高(A高)且相对动量弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "FC3",
        "operator": "rank_spread",
        "left": _UF_Z60,
        "right": _CAT_DISP20,
        "mechanism": "underwater_frac_z60_confirmed_by_category_dispersion_20",
        "hypothesis": "A=同上。B=板块内部20日收益离散度(category_state,本族首次配对)。假设:水下占比异常偏高(A高)且板块内部分化大(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "FC4",
        "operator": "rank_spread",
        "left": _UF_Z60,
        "right": _AMIHUD_1M,
        "mechanism": "underwater_frac_z60_confirmed_by_amihud_1m_20",
        "hypothesis": "A=同上。B=Amihud非流动性比率1m版本(microstructure_1m,本族首次配对)。假设:水下占比异常偏高(A高)且非流动性高(B高)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "FC5",
        "operator": "rank_spread",
        "left": _UF_Z60,
        "right": _GAP_SESSION_CORR,
        "mechanism": "underwater_frac_z60_confirmed_by_gap_session_correlation_20",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性(gap_response,S4阶段最强命中partner,t=3.89,本族首次配对)。假设:水下占比异常偏高(A高)且跳空延续性强(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "FC6",
        "operator": "rank_spread",
        "left": _UF_Z60,
        "right": _CHIP_RANGE,
        "mechanism": "underwater_frac_z60_confirmed_by_chip_range_90_60",
        "hypothesis": "A=同上。B=90分位筹码分布宽度(cost_distribution,本族首次配对)。假设:水下占比异常偏高(A高)且筹码分布宽(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "FC7",
        "operator": "rank_spread",
        "left": _UF_Z60,
        "right": _GK_RATIO,
        "mechanism": "underwater_frac_z60_confirmed_by_gk_rv_ratio_20",
        "hypothesis": "A=同上。B=Garman-Klass区间估计/RV之比(range_based_vol_1m,S9阶段本族原子,本族首次配对)。假设:水下占比异常偏高(A高)且bar内活动占比高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "FC8",
        "operator": "rank_spread",
        "left": _UF_Z60,
        "right": _PERM_ENTROPY_RET,
        "mechanism": "underwater_frac_z60_confirmed_by_perm_entropy_ret_20",
        "hypothesis": "A=同上。B=1m收益排列熵(permutation_entropy_1m,S6阶段全线首个不含成交量两窗口显著原子,本族首次配对)。假设:水下占比异常偏高(A高)且排列熵高(B高,更随机)=延续;本族最后一批,S12阶段两个先行原子的合法配对将用尽。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
