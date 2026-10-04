#!/usr/bin/env python3
"""Round 558 driver: S11 stage step 2 -- complexity_measures_1m pairing,
round 2. Three first-pairing batches for 3 of the 6 remaining atoms not
yet used as a left leg: SAMPEN_RET_20, LZ_COMPLEXITY_20,
RECURRENCE_RATE_20 -- the three MOST extreme atom-health shadows this
round_557 confirmed (0.96/0.96/0.98 vs S6's prior-admitted
PERM_ENTROPY_RET_20/CEP_DISTANCE_20), all of which failed their own
atomic test specifically on rank_correlation_redundancy despite very
strong discovery block-t (3.4-4.1). This round tests the
shadow-atom-rescue heuristic (7/8 prior successes across S4-S9) at its
most extreme correlation level yet -- if a confirming partner can
decorrelate rank_spread(A, partner) enough to clear the official dedup
gate even from a 0.96-0.98 base correlation, or if this is where the
heuristic finally fails outright (as it did once before, in S8, for
intra-family redundancy).

All 24 right-leg partners below are new to this family's S11 pairing
history (round_557's 16 partners are not repeated), chosen to be as
unrelated as possible to the "return randomness" axis (liquidity, cost
distribution, cross-dependence, fund-flow, market-sensitivity) to
maximize decorrelation potential. APEN_RET_20, MSPE_SCALE_DIFF_20 and
SAMPEN_RET_CHG_20 still have their pairing batch available for a later
S11 round."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_558"

_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_TRACK_ERR20 = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}
_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_CAT_MOM20 = {"name": "CATEGORY_MOM_20", "source": "category_state"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_LBAR_RET_CONTRIB = {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"}

_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_SHARE_CHG20 = {"name": "SHARE_CHG_20", "source": "fund_flow"}
_PREMIUM_Z20 = {"name": "PREMIUM_Z_20", "source": "nav_premium"}
_VOL_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_OFI_AUTOCORR = {"name": "OFI_AUTOCORR_20", "source": "microstructure_1m"}
_BIGBAR_EDGE_CONC = {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"}
_CLOSE5_CONSIST = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}

_MARKET_CORR20 = {"name": "MARKET_CORR_20", "source": "market_sensitivity"}
_UPSIDE_BETA20 = {"name": "UPSIDE_BETA_20", "source": "market_sensitivity"}
_OVERHAND_THICK = {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"}
_COST_CENTER_SHIFT = {"name": "COST_CENTER_SHIFT_20", "source": "cost_distribution"}
_LIQ_COMMON_BETA = {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"}
_RESILIENCY20 = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_GAP_FILL20 = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}
_VOL_USHAPE20 = {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"}

_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_LZ = {"name": "LZ_COMPLEXITY_20", "source": "complexity_measures_1m"}
_RR = {"name": "RECURRENCE_RATE_20", "source": "complexity_measures_1m"}

base.CANDIDATES = [
    # ---- SAMPEN_RET_20: first pairing batch ----
    {
        "id": "DA1",
        "operator": "rank_spread",
        "left": _SAMPEN,
        "right": _LOG_AMT,
        "mechanism": "sampen_ret_confirmed_by_log_amount_vol_20",
        "hypothesis": "A=样本熵(体检disc-0.0971,atomic因vs PERM_ENTROPY_RET_20冗余被拒,t=4.14未获采信)。B=成交额对数波动率(liquidity_variability,与A无直接关联,本族首次配对,测试partner能否把A去相关到清过冗余门)。假设:样本熵高(A高)且成交额稳定性低(B高)=噪声由流动性不稳驱动,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "DA2",
        "operator": "rank_spread",
        "left": _SAMPEN,
        "right": _CHIP_RANGE,
        "mechanism": "sampen_ret_confirmed_by_chip_range_90_60",
        "hypothesis": "A=同上。B=90分位筹码分布宽度(cost_distribution,本族首次配对)。假设:样本熵高(A高)且筹码分布宽(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "DA3",
        "operator": "rank_spread",
        "left": _SAMPEN,
        "right": _TRACK_ERR20,
        "mechanism": "sampen_ret_confirmed_by_tracking_error_20",
        "hypothesis": "A=同上。B=相对基准跟踪误差,20日(market_relative_strength,本族首次配对)。假设:样本熵高(A高)且跟踪误差高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "DA4",
        "operator": "rank_spread",
        "left": _SAMPEN,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "sampen_ret_confirmed_by_idio_liquidity_shock_20",
        "hypothesis": "A=同上。B=特异流动性冲击z值(liquidity_commonality_1m,本族首次配对)。假设:样本熵高(A高)且特异流动性冲击大(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "DA5",
        "operator": "rank_spread",
        "left": _SAMPEN,
        "right": _GAP_FILL60,
        "mechanism": "sampen_ret_confirmed_by_gap_fill_fraction_60",
        "hypothesis": "A=同上。B=跳空回补比例,60日(gap_repair,本族首次配对)。假设:样本熵高(A高)且跳空回补比例低(B低,更持续)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "DA6",
        "operator": "rank_spread",
        "left": _SAMPEN,
        "right": _CAT_MOM20,
        "mechanism": "sampen_ret_confirmed_by_category_momentum_20",
        "hypothesis": "A=同上。B=板块20日动量(category_state,本族首次配对)。假设:样本熵高(A高)且板块动量弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "DA7",
        "operator": "rank_spread",
        "left": _SAMPEN,
        "right": _DEP_DRIFT,
        "mechanism": "sampen_ret_confirmed_by_dep_drift_20",
        "hypothesis": "A=同上。B=依赖漂移指标(cross_dependence_1m,本族首次配对)。假设:样本熵高(A高)且依赖漂移方向按discovery定(B)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "DA8",
        "operator": "rank_spread",
        "left": _SAMPEN,
        "right": _LBAR_RET_CONTRIB,
        "mechanism": "sampen_ret_confirmed_by_lbar_ret_contrib_20",
        "hypothesis": "A=同上。B=大单bar对当日收益贡献占比(largebar_footprint_1m,本族首次配对)。假设:样本熵高(A高)且大单贡献低(B低,非结构性)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- LZ_COMPLEXITY_20: first pairing batch ----
    {
        "id": "DB1",
        "operator": "rank_spread",
        "left": _LZ,
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "lz_complexity_confirmed_by_peer_ou_halflife_20",
        "hypothesis": "A=LZ归一化复杂度(体检disc-0.0965,atomic同样因冗余被拒,t=3.83)。B=相对同伴OU回归半衰期(peer_relative_value,本族首次配对)。假设:复杂度高(A高,更随机)且相对同伴均值回归慢(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "DB2",
        "operator": "rank_spread",
        "left": _LZ,
        "right": _SHARE_CHG20,
        "mechanism": "lz_complexity_confirmed_by_share_change_20",
        "hypothesis": "A=同上。B=基金份额20日变化(fund_flow,本族首次配对)。假设:复杂度高(A高)且份额收缩(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "DB3",
        "operator": "rank_spread",
        "left": _LZ,
        "right": _PREMIUM_Z20,
        "mechanism": "lz_complexity_confirmed_by_premium_z_20",
        "hypothesis": "A=同上。B=净值溢价20日z值(nav_premium,本族首次配对)。假设:复杂度高(A高)且溢价异常(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "DB4",
        "operator": "rank_spread",
        "left": _LZ,
        "right": _VOL_AUTOCORR,
        "mechanism": "lz_complexity_confirmed_by_vol_autocorr_20",
        "hypothesis": "A=同上。B=成交量自相关(intraday_volume_profile_1m,本族首次配对)。假设:复杂度高(A高)且成交量自相关低(B低,量能也随机)=噪声在价与量两个维度共振,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "DB5",
        "operator": "rank_spread",
        "left": _LZ,
        "right": _OFI_AUTOCORR,
        "mechanism": "lz_complexity_confirmed_by_ofi_autocorr_20",
        "hypothesis": "A=同上。B=订单流不平衡自相关(microstructure_1m,本族首次配对)。假设:复杂度高(A高)且订单流自相关低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "DB6",
        "operator": "rank_spread",
        "left": _LZ,
        "right": _BIGBAR_EDGE_CONC,
        "mechanism": "lz_complexity_confirmed_by_bigbar_edge_concentration_20",
        "hypothesis": "A=同上。B=大单集中在日内两端的程度(bar_size_order_flow,本族首次配对)。假设:复杂度高(A高)且大单不集中于两端(B低,全天分散=更随机)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "DB7",
        "operator": "rank_spread",
        "left": _LZ,
        "right": _CLOSE5_CONSIST,
        "mechanism": "lz_complexity_confirmed_by_close5_day_consistency_20",
        "hypothesis": "A=同上。B=收盘前5分钟方向一致性(bar_size_order_flow,本族首次配对)。假设:复杂度高(A高)且尾盘方向一致性低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "DB8",
        "operator": "rank_spread",
        "left": _LZ,
        "right": _GAP_SESSION_CORR,
        "mechanism": "lz_complexity_confirmed_by_gap_session_correlation_20",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性(gap_response,S4阶段最强命中partner,t=3.89,本族首次配对)。假设:复杂度高(A高)且跳空延续性弱(B低)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- RECURRENCE_RATE_20: first pairing batch ----
    {
        "id": "DC1",
        "operator": "rank_spread",
        "left": _RR,
        "right": _MARKET_CORR20,
        "mechanism": "recurrence_rate_confirmed_by_market_corr_20",
        "hypothesis": "A=递归率(体检disc+0.0945,atomic同样因冗余被拒,t=3.44,本族最高相关0.98)。B=对篮子20日相关性(market_sensitivity,本族首次配对)。假设:递归率高(A高,轨迹重访多=结构性强)且与篮子相关性高(B高,系统性)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "DC2",
        "operator": "rank_spread",
        "left": _RR,
        "right": _UPSIDE_BETA20,
        "mechanism": "recurrence_rate_confirmed_by_upside_beta_20",
        "hypothesis": "A=同上。B=上行beta,20日(market_sensitivity,本族首次配对)。假设:递归率高(A高)且上行beta高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "DC3",
        "operator": "rank_spread",
        "left": _RR,
        "right": _OVERHAND_THICK,
        "mechanism": "recurrence_rate_confirmed_by_overhand_thickness_60",
        "hypothesis": "A=同上。B=套牢盘厚度,60日(cost_distribution,本族首次配对)。假设:递归率高(A高)且套牢盘薄(B低,轨迹能自由重访)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "DC4",
        "operator": "rank_spread",
        "left": _RR,
        "right": _COST_CENTER_SHIFT,
        "mechanism": "recurrence_rate_confirmed_by_cost_center_shift_20",
        "hypothesis": "A=同上。B=筹码成本中枢20日位移(cost_distribution,本族首次配对)。假设:递归率高(A高)且成本中枢稳定(B按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "DC5",
        "operator": "rank_spread",
        "left": _RR,
        "right": _LIQ_COMMON_BETA,
        "mechanism": "recurrence_rate_confirmed_by_liq_common_beta_20",
        "hypothesis": "A=同上。B=流动性共性beta(liquidity_commonality_1m,本族首次配对)。假设:递归率高(A高)且流动性共性高(B高,系统性强)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "DC6",
        "operator": "rank_spread",
        "left": _RR,
        "right": _RESILIENCY20,
        "mechanism": "recurrence_rate_confirmed_by_resiliency_20",
        "hypothesis": "A=同上。B=流动性恢复力(liquidity_commonality_1m,本族首次配对)。假设:递归率高(A高)且流动性恢复快(B高,轨迹能快速复原)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "DC7",
        "operator": "rank_spread",
        "left": _RR,
        "right": _GAP_FILL20,
        "mechanism": "recurrence_rate_confirmed_by_gap_fill_fraction_20",
        "hypothesis": "A=同上。B=跳空回补比例,20日(gap_repair,本族首次配对)。假设:递归率高(A高)且跳空回补比例高(B高,轨迹回归)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "DC8",
        "operator": "rank_spread",
        "left": _RR,
        "right": _VOL_USHAPE20,
        "mechanism": "recurrence_rate_confirmed_by_vol_ushape_20",
        "hypothesis": "A=同上。B=日内成交量U型强度(realized_measures_1m,round_053门7已admitted原子,本族首次配对)。假设:递归率高(A高)且U型强度高(B高,日内节奏规律)=延续;本族最后一批。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
