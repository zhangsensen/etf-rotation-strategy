#!/usr/bin/env python3
"""Round 554 driver: S9 stage step 2 -- range_based_vol_1m pairing,
round 2. Three first-pairing batches for 3 of the remaining 5 atoms not
yet used as a left leg: PARKINSON_RV_RATIO_20, RS_RV_RATIO_20,
WICK_SHARE_20 (round_553 covered YZ_OVERNIGHT_SHARE_20 and
GK_RV_RATIO_20; both admitted via YZ_OVERNIGHT_SHARE_20, GK_RV_RATIO_20's
batch found nothing). GK_RV_RATIO_CHG_20 and GK_RV_RATIO_Z_60 still have
their pairing batch available for a later S9 round.

All 24 right-leg partners below are new to this family's S9 pairing
history (round_553's 16 partners are not repeated). No same-family pairs,
no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_554"

_HKS_SLOT = {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"}
_TAIL30_BETA_FULL = {"name": "TAIL30_BETA_FULL_20", "source": "intraday_periodicity"}
_TRACK_ERR20 = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_IMPACT_ASYM = {"name": "IMPACT_ASYM_20", "source": "microstructure_1m"}

_OVERNIGHT_DIFF = {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"}
_REL_MOM60 = {"name": "REL_MARKET_MOM_60", "source": "market_relative_strength"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_CONTINUOUS_BETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_LBAR_CLOCK_STD = {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"}

_TICK_IMBALANCE = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_KYLE_LAMBDA = {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"}
_PROFIT_RATIO60 = {"name": "PROFIT_RATIO_60", "source": "cost_distribution"}
_COST_CENTER_SHIFT = {"name": "COST_CENTER_SHIFT_20", "source": "cost_distribution"}
_RESILIENCY20 = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_MARKET_CORR60 = {"name": "MARKET_CORR_60", "source": "market_sensitivity"}
_BENCH_RESID_VOL20 = {"name": "BENCHMARK_RESIDUAL_VOL_20", "source": "market_sensitivity"}

_PARKINSON = {"name": "PARKINSON_RV_RATIO_20", "source": "range_based_vol_1m"}
_RS_RATIO = {"name": "RS_RV_RATIO_20", "source": "range_based_vol_1m"}
_WICK_SHARE = {"name": "WICK_SHARE_20", "source": "range_based_vol_1m"}

base.CANDIDATES = [
    # ---- PARKINSON_RV_RATIO_20: first pairing batch ----
    {
        "id": "PA1",
        "operator": "rank_spread",
        "left": _PARKINSON,
        "right": _HKS_SLOT,
        "mechanism": "parkinson_rv_ratio_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=Parkinson区间估计/RV之比(体检disc-0.0232)。B=日内时段模式持续性(intraday_periodicity,S4阶段命中partner,本族首次配对)。假设:bar内活动占主导(A高)且日内时段模式稳定(B高)=区间信息可预测,延续,rank与未来收益负相关(符号按discovery定)。",
        "expected_sign": -1,
    },
    {
        "id": "PA2",
        "operator": "rank_spread",
        "left": _PARKINSON,
        "right": _TAIL30_BETA_FULL,
        "mechanism": "parkinson_rv_ratio_confirmed_by_tail30_beta_full",
        "hypothesis": "A=同上。B=尾盘30分钟beta相对全天beta比值(intraday_periodicity,本族首次配对)。假设:bar内活动占主导(A高)且尾盘beta占比高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PA3",
        "operator": "rank_spread",
        "left": _PARKINSON,
        "right": _TRACK_ERR20,
        "mechanism": "parkinson_rv_ratio_confirmed_by_tracking_error_20",
        "hypothesis": "A=同上。B=相对基准跟踪误差,20日(market_relative_strength,本族首次配对)。假设:bar内活动占主导(A高)且跟踪误差高(B高)=个股特异区间信息更强,延续。",
        "expected_sign": -1,
    },
    {
        "id": "PA4",
        "operator": "rank_spread",
        "left": _PARKINSON,
        "right": _CATEGORY_VOL,
        "mechanism": "parkinson_rv_ratio_confirmed_by_category_vol_20",
        "hypothesis": "A=同上。B=板块20日波动率(category_state,本族首次配对)。假设:bar内活动占主导(A高)且所属板块波动低(B低)=区间信息来自个股而非板块共振,延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PA5",
        "operator": "rank_spread",
        "left": _PARKINSON,
        "right": _GAP_FILL60,
        "mechanism": "parkinson_rv_ratio_confirmed_by_gap_fill_fraction_60",
        "hypothesis": "A=同上。B=跳空回补比例,60日(gap_repair,本族首次配对)。假设:bar内活动占主导(A高)且跳空回补比例低(B低,跳空更持续)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PA6",
        "operator": "rank_spread",
        "left": _PARKINSON,
        "right": _LOG_AMT,
        "mechanism": "parkinson_rv_ratio_confirmed_by_log_amount_vol_20",
        "hypothesis": "A=同上。B=成交额对数波动率(liquidity_variability,本族首次配对)。假设:bar内活动占主导(A高)且成交额稳定性低(B高)=区间波动与流动性不稳定共振,延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PA7",
        "operator": "rank_spread",
        "left": _PARKINSON,
        "right": _VOL_SPIKE,
        "mechanism": "parkinson_rv_ratio_confirmed_by_vol_spike_freq_20",
        "hypothesis": "A=同上。B=成交量突增频率(intraday_volume_profile_1m,本族首次配对)。假设:bar内活动占主导(A高)且成交放量突增频繁(B高)=区间波动由放量驱动而非噪声,延续。",
        "expected_sign": -1,
    },
    {
        "id": "PA8",
        "operator": "rank_spread",
        "left": _PARKINSON,
        "right": _IMPACT_ASYM,
        "mechanism": "parkinson_rv_ratio_confirmed_by_impact_asymmetry",
        "hypothesis": "A=同上。B=价格冲击不对称性(microstructure_1m,本族首次配对)。假设:bar内活动占主导(A高)且冲击不对称明显(B按discovery定)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- RS_RV_RATIO_20: first pairing batch ----
    {
        "id": "PB1",
        "operator": "rank_spread",
        "left": _RS_RATIO,
        "right": _OVERNIGHT_DIFF,
        "mechanism": "rs_rv_ratio_confirmed_by_overnight_intra_diff",
        "hypothesis": "A=Rogers-Satchell漂移无关估计/RV之比(体检disc+0.0035,接近0)。B=隔夜与日内收益差异(intraday_periodicity,本族首次配对)。假设:漂移调整后bar内活动占主导(A高)且隔夜/日内分化明显(B按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB2",
        "operator": "rank_spread",
        "left": _RS_RATIO,
        "right": _REL_MOM60,
        "mechanism": "rs_rv_ratio_confirmed_by_relative_market_momentum_60",
        "hypothesis": "A=同上。B=相对基准篮子动量,60日(market_relative_strength,本族首次配对)。假设:A高且相对动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB3",
        "operator": "rank_spread",
        "left": _RS_RATIO,
        "right": _OPEN30,
        "mechanism": "rs_rv_ratio_confirmed_by_open30_vol_share",
        "hypothesis": "A=同上。B=开盘30分钟成交量占比(intraday_volume_profile_1m,本族首次配对)。假设:A高且开盘放量集中(B高)=区间信息来自开盘阶段的知情交易,延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB4",
        "operator": "rank_spread",
        "left": _RS_RATIO,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "rs_rv_ratio_confirmed_by_idio_liquidity_shock",
        "hypothesis": "A=同上。B=特异流动性冲击z值(liquidity_commonality_1m,本族首次配对)。假设:A高且特异流动性冲击大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB5",
        "operator": "rank_spread",
        "left": _RS_RATIO,
        "right": _GAP_SESSION_CORR,
        "mechanism": "rs_rv_ratio_confirmed_by_gap_session_correlation",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性(gap_response,S4阶段最强命中partner,t=3.89,本族首次配对)。假设:A高且跳空延续性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB6",
        "operator": "rank_spread",
        "left": _RS_RATIO,
        "right": _CHIP_RANGE,
        "mechanism": "rs_rv_ratio_confirmed_by_chip_range",
        "hypothesis": "A=同上。B=90分位筹码分布宽度(cost_distribution,本族首次配对)。假设:A高且筹码分布宽(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB7",
        "operator": "rank_spread",
        "left": _RS_RATIO,
        "right": _CONTINUOUS_BETA60,
        "mechanism": "rs_rv_ratio_confirmed_by_continuous_beta_60",
        "hypothesis": "A=同上。B=对14只等权篮子的连续beta,60日(jump_continuous_beta,S4阶段CONTINUOUS_BETA_60簇最强KU2/KR1的同源原子,本族首次配对)。假设:A高且系统性连续beta高(B高)=区间信息与系统性风险共振,延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB8",
        "operator": "rank_spread",
        "left": _RS_RATIO,
        "right": _LBAR_CLOCK_STD,
        "mechanism": "rs_rv_ratio_confirmed_by_lbar_clock_std",
        "hypothesis": "A=同上。B=大单出现时刻的标准差(largebar_footprint_1m,本族首次配对)。假设:A高且大单时刻分散(B高)=延续;本族最后一批。",
        "expected_sign": 1,
    },
    # ---- WICK_SHARE_20: first pairing batch ----
    {
        "id": "PC1",
        "operator": "rank_spread",
        "left": _WICK_SHARE,
        "right": _TICK_IMBALANCE,
        "mechanism": "wick_share_confirmed_by_tick_imbalance_20",
        "hypothesis": "A=全天影线占比(体检disc+0.0137)。B=tick方向不平衡(bar_size_order_flow,本族首次配对)。假设:影线占比高(A高,反转/试探强)且tick不平衡明显(B按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC2",
        "operator": "rank_spread",
        "left": _WICK_SHARE,
        "right": _VOL_ENTROPY,
        "mechanism": "wick_share_confirmed_by_vol_entropy_20",
        "hypothesis": "A=同上。B=日内成交量分布熵(intraday_volume_profile_1m,本族首次配对)。假设:影线占比高(A高)且成交时点分布均匀(B高,熵大)=反转由分散交易而非单点冲击驱动,延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC3",
        "operator": "rank_spread",
        "left": _WICK_SHARE,
        "right": _KYLE_LAMBDA,
        "mechanism": "wick_share_confirmed_by_kyle_lambda_20",
        "hypothesis": "A=同上。B=Kyle lambda价格冲击系数(microstructure_1m,本族首次配对)。假设:影线占比高(A高)且价格冲击系数低(B低,流动性好)=影线是试探而非流动性稀缺造成,延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "PC4",
        "operator": "rank_spread",
        "left": _WICK_SHARE,
        "right": _PROFIT_RATIO60,
        "mechanism": "wick_share_confirmed_by_profit_ratio_60",
        "hypothesis": "A=同上。B=60日获利盘比例(cost_distribution,本族首次配对)。假设:影线占比高(A高)且获利盘比例高(B高,抛压试探)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC5",
        "operator": "rank_spread",
        "left": _WICK_SHARE,
        "right": _COST_CENTER_SHIFT,
        "mechanism": "wick_share_confirmed_by_cost_center_shift_20",
        "hypothesis": "A=同上。B=筹码成本中枢20日位移(cost_distribution,本族首次配对)。假设:影线占比高(A高)且成本中枢正在上移(B高)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "PC6",
        "operator": "rank_spread",
        "left": _WICK_SHARE,
        "right": _RESILIENCY20,
        "mechanism": "wick_share_confirmed_by_resiliency_20",
        "hypothesis": "A=同上。B=流动性恢复力(liquidity_commonality_1m,本族首次配对)。假设:影线占比高(A高)且流动性恢复快(B高)=价格试探后能快速回归,延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC7",
        "operator": "rank_spread",
        "left": _WICK_SHARE,
        "right": _MARKET_CORR60,
        "mechanism": "wick_share_confirmed_by_market_corr_60",
        "hypothesis": "A=同上。B=对篮子的60日相关性(market_sensitivity,本族首次配对)。假设:影线占比高(A高)且与篮子相关性低(B低,特异性强)=影线是个股特异行为而非系统性,延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "PC8",
        "operator": "rank_spread",
        "left": _WICK_SHARE,
        "right": _BENCH_RESID_VOL20,
        "mechanism": "wick_share_confirmed_by_benchmark_residual_vol_20",
        "hypothesis": "A=同上。B=对基准回归后的残差波动率,20日(market_sensitivity,本族首次配对)。假设:影线占比高(A高)且特异波动率高(B高)=延续;本族最后一批。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
