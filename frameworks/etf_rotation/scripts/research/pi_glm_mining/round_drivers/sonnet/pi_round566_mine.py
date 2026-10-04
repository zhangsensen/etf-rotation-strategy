#!/usr/bin/env python3
"""Round 566 driver: S13 stage step 2 -- frequency_domain_beta_1m
pairing, round 2. Three first-pairing batches for the 3 shadow atoms not
yet used as a left leg: BETA_HF_20, BETA_MF_20, BETA_LF_20 (round_565
covered BETA_FREQ_SLOPE_CHG_20 and BETA_LF_CHG_20, admitting 0/24 --
notably a discovery-only-noise pattern, not redundancy: several
candidates had striking discovery t-stats up to 4.53 that all failed
audit-consistency gates). This round gives the three atomic-shadow band
betas their one pairing shot, per this line's established
shadow-rescue heuristic, while treating any high-t results with the
extra skepticism round_565's finding warrants.

All 24 right-leg partners below are new to this family's S13 pairing
history (round_565's 16 partners are not repeated). No same-family
pairs, no window variants. BETA_FREQ_SLOPE_20, COHERENCE_LF_HF_DIFF_20
and BETA_HF_CHG_20 still have their pairing batch available for a later
S13 round."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_566"

_TAIL30_BETA_FULL = {"name": "TAIL30_BETA_FULL_20", "source": "intraday_periodicity"}
_TRACK_ERR60 = {"name": "TRACKING_ERROR_60", "source": "market_relative_strength"}
_CAT_MOM20 = {"name": "CATEGORY_MOM_20", "source": "category_state"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_GAP_FILL20 = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}
_LIQ_COMMON_BETA = {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"}
_TICK_IMBALANCE = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}
_LBAR_CLOCK_STD = {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"}

_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_PEER_RESID_Z = {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_PREMIUM_Z20 = {"name": "PREMIUM_Z_20", "source": "nav_premium"}
_SHARE_CHG20 = {"name": "SHARE_CHG_20", "source": "fund_flow"}
_GK_RATIO = {"name": "GK_RV_RATIO_20", "source": "range_based_vol_1m"}
_APEN = {"name": "APEN_RET_20", "source": "complexity_measures_1m"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}

_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_PRICE_AVGCOST = {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_VOL_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_MARKET_CORR20 = {"name": "MARKET_CORR_20", "source": "market_sensitivity"}
_WICK_SHARE = {"name": "WICK_SHARE_20", "source": "range_based_vol_1m"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_LBAR_RET_CONTRIB = {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"}

_BETA_HF = {"name": "BETA_HF_20", "source": "frequency_domain_beta_1m"}
_BETA_MF = {"name": "BETA_MF_20", "source": "frequency_domain_beta_1m"}
_BETA_LF = {"name": "BETA_LF_20", "source": "frequency_domain_beta_1m"}

base.CANDIDATES = [
    # ---- BETA_HF_20: first pairing batch ----
    {
        "id": "JA1",
        "operator": "rank_spread",
        "left": _BETA_HF,
        "right": _TAIL30_BETA_FULL,
        "mechanism": "beta_hf_confirmed_by_tail30_beta_full_20",
        "hypothesis": "A=高频带beta(体检disc-0.1045,atomic因vs market_sensitivity:MARKET_BETA_60冗余被拒,t=3.35未获采信)。B=尾盘30分钟beta相对全天beta比值(intraday_periodicity,本族首次配对)。假设:高频beta高(A高)且尾盘beta占比高(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "JA2",
        "operator": "rank_spread",
        "left": _BETA_HF,
        "right": _TRACK_ERR60,
        "mechanism": "beta_hf_confirmed_by_tracking_error_60",
        "hypothesis": "A=同上。B=相对基准跟踪误差,60日(market_relative_strength,本族首次配对)。假设:高频beta高(A高)且跟踪误差低(B低,系统性强)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "JA3",
        "operator": "rank_spread",
        "left": _BETA_HF,
        "right": _CAT_MOM20,
        "mechanism": "beta_hf_confirmed_by_category_momentum_20",
        "hypothesis": "A=同上。B=板块20日动量(category_state,本族首次配对)。假设:高频beta高(A高)且板块动量弱(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JA4",
        "operator": "rank_spread",
        "left": _BETA_HF,
        "right": _OPEN30,
        "mechanism": "beta_hf_confirmed_by_open30_vol_share_20",
        "hypothesis": "A=同上。B=开盘30分钟成交量占比(intraday_volume_profile_1m,本族首次配对)。假设:高频beta高(A高)且开盘放量集中(B高,高频共振驱动)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JA5",
        "operator": "rank_spread",
        "left": _BETA_HF,
        "right": _GAP_FILL20,
        "mechanism": "beta_hf_confirmed_by_gap_fill_fraction_20",
        "hypothesis": "A=同上。B=跳空回补比例,20日(gap_repair,本族首次配对)。假设:高频beta高(A高)且跳空回补比例低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JA6",
        "operator": "rank_spread",
        "left": _BETA_HF,
        "right": _LIQ_COMMON_BETA,
        "mechanism": "beta_hf_confirmed_by_liq_common_beta_20",
        "hypothesis": "A=同上。B=流动性共性beta(liquidity_commonality_1m,本族首次配对)。假设:高频beta高(A高)且流动性共性高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JA7",
        "operator": "rank_spread",
        "left": _BETA_HF,
        "right": _TICK_IMBALANCE,
        "mechanism": "beta_hf_confirmed_by_tick_imbalance_20",
        "hypothesis": "A=同上。B=tick方向不平衡(bar_size_order_flow,本族首次配对)。假设:高频beta高(A高)且tick不平衡明显(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JA8",
        "operator": "rank_spread",
        "left": _BETA_HF,
        "right": _LBAR_CLOCK_STD,
        "mechanism": "beta_hf_confirmed_by_lbar_clock_std_20",
        "hypothesis": "A=同上。B=大单出现时刻标准差(largebar_footprint_1m,本族首次配对)。假设:高频beta高(A高)且大单时刻分散(B高)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- BETA_MF_20: first pairing batch ----
    {
        "id": "JB1",
        "operator": "rank_spread",
        "left": _BETA_MF,
        "right": _VOL_ENTROPY,
        "mechanism": "beta_mf_confirmed_by_vol_entropy_20",
        "hypothesis": "A=中频带beta(体检disc-0.0920,atomic因冗余被拒)。B=日内成交量分布熵(intraday_volume_profile_1m,本族首次配对)。假设:中频beta高(A高)且成交时点分布均匀(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "JB2",
        "operator": "rank_spread",
        "left": _BETA_MF,
        "right": _PEER_RESID_Z,
        "mechanism": "beta_mf_confirmed_by_peer_resid_z_20",
        "hypothesis": "A=同上。B=相对同伴协整残差z值(peer_relative_value,本族首次配对)。假设:中频beta高(A高)且相对同伴无明显偏离(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JB3",
        "operator": "rank_spread",
        "left": _BETA_MF,
        "right": _GRANGER_IN,
        "mechanism": "beta_mf_confirmed_by_granger_in_degree_20",
        "hypothesis": "A=同上。B=格兰杰因果入度(cross_dependence_1m,本族首次配对)。假设:中频beta高(A高)且被同伴领先影响强(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JB4",
        "operator": "rank_spread",
        "left": _BETA_MF,
        "right": _PREMIUM_Z20,
        "mechanism": "beta_mf_confirmed_by_premium_z_20",
        "hypothesis": "A=同上。B=净值溢价20日z值(nav_premium,本族首次配对)。假设:中频beta高(A高)且溢价异常(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JB5",
        "operator": "rank_spread",
        "left": _BETA_MF,
        "right": _SHARE_CHG20,
        "mechanism": "beta_mf_confirmed_by_share_change_20",
        "hypothesis": "A=同上。B=基金份额20日变化(fund_flow,本族首次配对)。假设:中频beta高(A高)且份额同步扩张(B高)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "JB6",
        "operator": "rank_spread",
        "left": _BETA_MF,
        "right": _GK_RATIO,
        "mechanism": "beta_mf_confirmed_by_gk_rv_ratio_20",
        "hypothesis": "A=同上。B=Garman-Klass区间估计/RV之比(range_based_vol_1m,S9阶段本族原子,本族首次配对)。假设:中频beta高(A高)且bar内活动占比高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JB7",
        "operator": "rank_spread",
        "left": _BETA_MF,
        "right": _APEN,
        "mechanism": "beta_mf_confirmed_by_apen_ret_20",
        "hypothesis": "A=同上。B=1m收益近似熵(complexity_measures_1m,S11阶段本族原子,本族首次配对)。假设:中频beta高(A高)且近似熵低(B低,结构性更强)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "JB8",
        "operator": "rank_spread",
        "left": _BETA_MF,
        "right": _LOG_AMT,
        "mechanism": "beta_mf_confirmed_by_log_amount_vol_20",
        "hypothesis": "A=同上。B=成交额对数波动率(liquidity_variability,本族首次配对)。假设:中频beta高(A高)且成交额稳定性低(B高)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- BETA_LF_20: first pairing batch ----
    {
        "id": "JC1",
        "operator": "rank_spread",
        "left": _BETA_LF,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "beta_lf_confirmed_by_idio_liquidity_shock_20",
        "hypothesis": "A=低频带beta(体检disc-0.0708,atomic因冗余被拒,仅3个频率bin估计噪声较大)。B=特异流动性冲击z值(liquidity_commonality_1m,本族首次配对)。假设:低频beta高(A高)且特异流动性冲击小(B低)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "JC2",
        "operator": "rank_spread",
        "left": _BETA_LF,
        "right": _PRICE_AVGCOST,
        "mechanism": "beta_lf_confirmed_by_price_vs_avgcost_20",
        "hypothesis": "A=同上。B=现价相对平均成本偏离(cost_distribution,本族首次配对)。假设:低频beta高(A高)且现价低于成本(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "JC3",
        "operator": "rank_spread",
        "left": _BETA_LF,
        "right": _DEP_DRIFT,
        "mechanism": "beta_lf_confirmed_by_dep_drift_20",
        "hypothesis": "A=同上。B=依赖漂移指标(cross_dependence_1m,本族首次配对)。假设:低频beta高(A高)且依赖漂移方向按discovery定(B)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JC4",
        "operator": "rank_spread",
        "left": _BETA_LF,
        "right": _VOL_AUTOCORR,
        "mechanism": "beta_lf_confirmed_by_vol_autocorr_20",
        "hypothesis": "A=同上。B=成交量自相关(intraday_volume_profile_1m,本族首次配对)。假设:低频beta高(A高)且成交量自相关高(B高,持续性强)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JC5",
        "operator": "rank_spread",
        "left": _BETA_LF,
        "right": _MARKET_CORR20,
        "mechanism": "beta_lf_confirmed_by_market_corr_20",
        "hypothesis": "A=同上。B=对14只等权篮子相关性,20日(market_sensitivity,本族首次配对)。假设:低频beta高(A高)且与篮子相关性高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JC6",
        "operator": "rank_spread",
        "left": _BETA_LF,
        "right": _WICK_SHARE,
        "mechanism": "beta_lf_confirmed_by_wick_share_20",
        "hypothesis": "A=同上。B=全天影线占比(range_based_vol_1m,本族首次配对)。假设:低频beta高(A高)且影线占比低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JC7",
        "operator": "rank_spread",
        "left": _BETA_LF,
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "beta_lf_confirmed_by_bigbar_vol_share_20",
        "hypothesis": "A=同上。B=大单成交量占比(bar_size_order_flow,本线通道原子之一,本族首次配对)。假设:低频beta高(A高)且大单占比高(B高,系统性资金驱动)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "JC8",
        "operator": "rank_spread",
        "left": _BETA_LF,
        "right": _LBAR_RET_CONTRIB,
        "mechanism": "beta_lf_confirmed_by_lbar_ret_contrib_20",
        "hypothesis": "A=同上。B=大单bar对当日收益贡献占比(largebar_footprint_1m,本族首次配对)。假设:低频beta高(A高)且大单贡献高(B高)=延续;本族最后一批。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
