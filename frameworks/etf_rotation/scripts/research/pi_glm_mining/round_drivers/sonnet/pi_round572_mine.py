#!/usr/bin/env python3
"""Round 572 driver: S15 (controller) stage step 2 --
relative_path_vs_basket_1m pairing, round 2. Three first-pairing batches
for 3 of the 6 remaining atoms not yet used as a left leg:
REL_UNDERWATER_FRAC_20, REL_PERM_ENTROPY_20, REL_PATH_EFFICIENCY_20
(round_571 covered UNDERWATER_FRAC_DIFF_20 and REL_MAXDD_20, admitting 3
-- all sharing left leg REL_MAXDD_20, collapsing to 1 net at closure).
Per the controller's 2026-09-20 20:10 note, round_570's self-directed
money_flow_extremes_1m is closed (no further pairing), and this line
should not self-assign new stages when the queue is empty -- this round
continues the controller-specified S15 queue as instructed.

All 24 right-leg partners below are new to this family's S15 pairing
history (round_571's 16 partners are not repeated). No same-family
pairs, no window variants. REL_UNDERWATER_FRAC_CHG_20, REL_MAXDD_CHG_20
and REL_RECOVERY_FRAC_20 still have their pairing batch available for a
later S15 round."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_572"

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
_GK_CHG = {"name": "GK_RV_RATIO_CHG_20", "source": "range_based_vol_1m"}
_APEN = {"name": "APEN_RET_20", "source": "complexity_measures_1m"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}

_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_PRICE_AVGCOST = {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"}
_VOL_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_MARKET_CORR20 = {"name": "MARKET_CORR_20", "source": "market_sensitivity"}
_WICK_SHARE = {"name": "WICK_SHARE_20", "source": "range_based_vol_1m"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_LBAR_RET_CONTRIB = {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"}
_MFI_TOD_SKEW = {"name": "MFI_EXTREME_TOD_SKEW_20", "source": "money_flow_extremes_1m"}

_REL_UF = {"name": "REL_UNDERWATER_FRAC_20", "source": "relative_path_vs_basket_1m"}
_REL_PERM_ENTROPY = {"name": "REL_PERM_ENTROPY_20", "source": "relative_path_vs_basket_1m"}
_REL_PATH_EFF = {"name": "REL_PATH_EFFICIENCY_20", "source": "relative_path_vs_basket_1m"}

base.CANDIDATES = [
    # ---- REL_UNDERWATER_FRAC_20: first pairing batch ----
    {
        "id": "OA1",
        "operator": "rank_spread",
        "left": _REL_UF,
        "right": _TAIL30_BETA_FULL,
        "mechanism": "rel_underwater_frac_confirmed_by_tail30_beta_full_20",
        "hypothesis": "A=主动路径日内水下占比(体检disc-0.0152,atomic未过topk_gate)。B=尾盘30分钟beta相对全天beta比值(intraday_periodicity,本族首次配对)。假设:主动水下占比高(A高)且尾盘beta占比高(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "OA2",
        "operator": "rank_spread",
        "left": _REL_UF,
        "right": _TRACK_ERR60,
        "mechanism": "rel_underwater_frac_confirmed_by_tracking_error_60",
        "hypothesis": "A=同上。B=相对基准跟踪误差,60日(market_relative_strength,本族首次配对)。假设:主动水下占比高(A高)且跟踪误差高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OA3",
        "operator": "rank_spread",
        "left": _REL_UF,
        "right": _CAT_MOM20,
        "mechanism": "rel_underwater_frac_confirmed_by_category_momentum_20",
        "hypothesis": "A=同上。B=板块20日动量(category_state,本族首次配对)。假设:主动水下占比高(A高)且板块动量弱(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OA4",
        "operator": "rank_spread",
        "left": _REL_UF,
        "right": _OPEN30,
        "mechanism": "rel_underwater_frac_confirmed_by_open30_vol_share_20",
        "hypothesis": "A=同上。B=开盘30分钟成交量占比(intraday_volume_profile_1m,本族首次配对)。假设:主动水下占比高(A高)且开盘放量集中(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OA5",
        "operator": "rank_spread",
        "left": _REL_UF,
        "right": _GAP_FILL20,
        "mechanism": "rel_underwater_frac_confirmed_by_gap_fill_fraction_20",
        "hypothesis": "A=同上。B=跳空回补比例,20日(gap_repair,本族首次配对)。假设:主动水下占比高(A高)且跳空回补比例低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OA6",
        "operator": "rank_spread",
        "left": _REL_UF,
        "right": _LIQ_COMMON_BETA,
        "mechanism": "rel_underwater_frac_confirmed_by_liq_common_beta_20",
        "hypothesis": "A=同上。B=流动性共性beta(liquidity_commonality_1m,本族首次配对)。假设:主动水下占比高(A高)且流动性共性高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OA7",
        "operator": "rank_spread",
        "left": _REL_UF,
        "right": _TICK_IMBALANCE,
        "mechanism": "rel_underwater_frac_confirmed_by_tick_imbalance_20",
        "hypothesis": "A=同上。B=tick方向不平衡(bar_size_order_flow,本族首次配对)。假设:主动水下占比高(A高)且tick不平衡明显偏卖(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OA8",
        "operator": "rank_spread",
        "left": _REL_UF,
        "right": _LBAR_CLOCK_STD,
        "mechanism": "rel_underwater_frac_confirmed_by_lbar_clock_std_20",
        "hypothesis": "A=同上。B=大单出现时刻标准差(largebar_footprint_1m,本族首次配对)。假设:主动水下占比高(A高)且大单时刻分散(B高)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- REL_PERM_ENTROPY_20: first pairing batch ----
    {
        "id": "OB1",
        "operator": "rank_spread",
        "left": _REL_PERM_ENTROPY,
        "right": _VOL_ENTROPY,
        "mechanism": "rel_perm_entropy_confirmed_by_vol_entropy_20",
        "hypothesis": "A=主动收益排列熵(体检disc-0.0103,本族最独立原子之一)。B=日内成交量分布熵(intraday_volume_profile_1m,本族首次配对)。假设:主动收益排列熵高(A高,更随机)且成交时点分布均匀(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "OB2",
        "operator": "rank_spread",
        "left": _REL_PERM_ENTROPY,
        "right": _PEER_RESID_Z,
        "mechanism": "rel_perm_entropy_confirmed_by_peer_resid_z_20",
        "hypothesis": "A=同上。B=相对同伴协整残差z值(peer_relative_value,本族首次配对)。假设:主动收益排列熵高(A高)且相对同伴无明显偏离(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OB3",
        "operator": "rank_spread",
        "left": _REL_PERM_ENTROPY,
        "right": _GRANGER_IN,
        "mechanism": "rel_perm_entropy_confirmed_by_granger_in_degree_20",
        "hypothesis": "A=同上。B=格兰杰因果入度(cross_dependence_1m,本族首次配对)。假设:主动收益排列熵高(A高)且被同伴领先影响强(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OB4",
        "operator": "rank_spread",
        "left": _REL_PERM_ENTROPY,
        "right": _PREMIUM_Z20,
        "mechanism": "rel_perm_entropy_confirmed_by_premium_z_20",
        "hypothesis": "A=同上。B=净值溢价20日z值(nav_premium,本族首次配对)。假设:主动收益排列熵高(A高)且溢价异常(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OB5",
        "operator": "rank_spread",
        "left": _REL_PERM_ENTROPY,
        "right": _SHARE_CHG20,
        "mechanism": "rel_perm_entropy_confirmed_by_share_change_20",
        "hypothesis": "A=同上。B=基金份额20日变化(fund_flow,本族首次配对)。假设:主动收益排列熵高(A高)且份额收缩(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OB6",
        "operator": "rank_spread",
        "left": _REL_PERM_ENTROPY,
        "right": _GK_CHG,
        "mechanism": "rel_perm_entropy_confirmed_by_gk_rv_ratio_chg_20",
        "hypothesis": "A=同上。B=GK区间估计/RV之比的20日变化(range_based_vol_1m,本族首次配对)。假设:主动收益排列熵高(A高)且区间比值同步上升(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OB7",
        "operator": "rank_spread",
        "left": _REL_PERM_ENTROPY,
        "right": _APEN,
        "mechanism": "rel_perm_entropy_confirmed_by_apen_ret_20",
        "hypothesis": "A=同上。B=1m绝对收益近似熵(complexity_measures_1m,S11阶段本族原子,本族首次配对,测试主动熵与绝对熵是否独立叠加)。假设:主动收益排列熵高(A高)且绝对收益近似熵也高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OB8",
        "operator": "rank_spread",
        "left": _REL_PERM_ENTROPY,
        "right": _LOG_AMT,
        "mechanism": "rel_perm_entropy_confirmed_by_log_amount_vol_20",
        "hypothesis": "A=同上。B=成交额对数波动率(liquidity_variability,本族首次配对)。假设:主动收益排列熵高(A高)且成交额稳定性低(B高)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- REL_PATH_EFFICIENCY_20: first pairing batch ----
    {
        "id": "OC1",
        "operator": "rank_spread",
        "left": _REL_PATH_EFF,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "rel_path_eff_confirmed_by_idio_liquidity_shock_20",
        "hypothesis": "A=主动路径效率(体检disc-0.0228)。B=特异流动性冲击z值(liquidity_commonality_1m,本族首次配对)。假设:主动路径效率高(A高,方向性强)且特异流动性冲击大(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "OC2",
        "operator": "rank_spread",
        "left": _REL_PATH_EFF,
        "right": _PRICE_AVGCOST,
        "mechanism": "rel_path_eff_confirmed_by_price_vs_avgcost_20",
        "hypothesis": "A=同上。B=现价相对平均成本偏离(cost_distribution,本族首次配对)。假设:主动路径效率高(A高)且现价低于成本(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "OC3",
        "operator": "rank_spread",
        "left": _REL_PATH_EFF,
        "right": _VOL_AUTOCORR,
        "mechanism": "rel_path_eff_confirmed_by_vol_autocorr_20",
        "hypothesis": "A=同上。B=成交量自相关(intraday_volume_profile_1m,本族首次配对)。假设:主动路径效率高(A高)且成交量自相关低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OC4",
        "operator": "rank_spread",
        "left": _REL_PATH_EFF,
        "right": _MARKET_CORR20,
        "mechanism": "rel_path_eff_confirmed_by_market_corr_20",
        "hypothesis": "A=同上。B=对14只等权篮子相关性,20日(market_sensitivity,本族首次配对)。假设:主动路径效率高(A高)且与篮子相关性低(B低,特异性方向强)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OC5",
        "operator": "rank_spread",
        "left": _REL_PATH_EFF,
        "right": _WICK_SHARE,
        "mechanism": "rel_path_eff_confirmed_by_wick_share_20",
        "hypothesis": "A=同上。B=全天影线占比(range_based_vol_1m,本族首次配对)。假设:主动路径效率高(A高)且影线占比低(B低,试探性弱)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OC6",
        "operator": "rank_spread",
        "left": _REL_PATH_EFF,
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "rel_path_eff_confirmed_by_bigbar_vol_share_20",
        "hypothesis": "A=同上。B=大单成交量占比(bar_size_order_flow,本线通道原子之一,本族首次配对)。假设:主动路径效率高(A高)且大单占比高(B高,单方向大单驱动)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OC7",
        "operator": "rank_spread",
        "left": _REL_PATH_EFF,
        "right": _LBAR_RET_CONTRIB,
        "mechanism": "rel_path_eff_confirmed_by_lbar_ret_contrib_20",
        "hypothesis": "A=同上。B=大单bar对当日收益贡献占比(largebar_footprint_1m,本族首次配对)。假设:主动路径效率高(A高)且大单贡献高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "OC8",
        "operator": "rank_spread",
        "left": _REL_PATH_EFF,
        "right": _MFI_TOD_SKEW,
        "mechanism": "rel_path_eff_confirmed_by_mfi_extreme_tod_skew_20",
        "hypothesis": "A=同上。B=MFI极端bar出现时刻偏移(money_flow_extremes_1m,round_570本族已收录但不再配对,本族首次配对)。假设:主动路径效率高(A高)且极端资金流偏向尾盘(B按discovery定)=延续;本族最后一批。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
