#!/usr/bin/env python3
"""Round 562 driver: S12 stage step 2 -- intraday_pain_recovery_1m
pairing, round 2. Three first-pairing batches for 3 of the 6 remaining
atoms not yet used as a left leg: ULCER_INDEX_20, PAIN_INDEX_20,
RECOVERY_TIME_FRAC_20 (round_561 covered DD_RECOVERY_SPEED_RATIO_20 and
UNDERWATER_FRAC_Z_60, admitting 2 -- both from the same UNDERWATER_FRAC_Z_60
cluster). This round tests whether the "depth" atoms (ULCER/PAIN, both
atom-health shadow against downside_risk, not the expected S7 reference)
can be rescued by a confirming partner, and gives the second
non-shadow "recovery structure" atom its first real test.

All 24 right-leg partners below are new to this family's S12 pairing
history (round_561's 16 partners are not repeated). No same-family
pairs, no window variants. ULCER_INDEX_CHG_20, PAIN_INDEX_CHG_20 and
RECOVERY_TIME_FRAC_CHG_20 still have their pairing batch available for a
later S12 round."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_562"

_TAIL30_BETA_FULL = {"name": "TAIL30_BETA_FULL_20", "source": "intraday_periodicity"}
_TRACK_ERR60 = {"name": "TRACKING_ERROR_60", "source": "market_relative_strength"}
_CAT_MOM20 = {"name": "CATEGORY_MOM_20", "source": "category_state"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_GAP_FILL20 = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}
_JUMP_BETA20 = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_RESILIENCY20 = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_TICK_IMBALANCE = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}

_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_PEER_RESID_Z = {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_PREMIUM_Z20 = {"name": "PREMIUM_Z_20", "source": "nav_premium"}
_SHARE_CHG20 = {"name": "SHARE_CHG_20", "source": "fund_flow"}
_RS_RATIO = {"name": "RS_RV_RATIO_20", "source": "range_based_vol_1m"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}

_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_PRICE_AVGCOST = {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_VOL_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_MARKET_CORR20 = {"name": "MARKET_CORR_20", "source": "market_sensitivity"}
_YZ_OVERNIGHT = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_LBAR_RET_CONTRIB = {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"}

_ULCER = {"name": "ULCER_INDEX_20", "source": "intraday_pain_recovery_1m"}
_PAIN = {"name": "PAIN_INDEX_20", "source": "intraday_pain_recovery_1m"}
_RECOVERY_FRAC = {"name": "RECOVERY_TIME_FRAC_20", "source": "intraday_pain_recovery_1m"}

base.CANDIDATES = [
    # ---- ULCER_INDEX_20: first pairing batch ----
    {
        "id": "GA1",
        "operator": "rank_spread",
        "left": _ULCER,
        "right": _TAIL30_BETA_FULL,
        "mechanism": "ulcer_index_confirmed_by_tail30_beta_full_20",
        "hypothesis": "A=溃疡指数(体检disc-0.0965,atomic因vs downside_risk族冗余被拒,而非体检标记的S7参照)。B=尾盘30分钟beta相对全天beta比值(intraday_periodicity,本族首次配对)。假设:溃疡指数高(A高,深回撤集中)且尾盘beta占比高(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "GA2",
        "operator": "rank_spread",
        "left": _ULCER,
        "right": _TRACK_ERR60,
        "mechanism": "ulcer_index_confirmed_by_tracking_error_60",
        "hypothesis": "A=同上。B=相对基准跟踪误差,60日(market_relative_strength,本族首次配对)。假设:溃疡指数高(A高)且跟踪误差高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GA3",
        "operator": "rank_spread",
        "left": _ULCER,
        "right": _CAT_MOM20,
        "mechanism": "ulcer_index_confirmed_by_category_momentum_20",
        "hypothesis": "A=同上。B=板块20日动量(category_state,本族首次配对)。假设:溃疡指数高(A高)且板块动量弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "GA4",
        "operator": "rank_spread",
        "left": _ULCER,
        "right": _OPEN30,
        "mechanism": "ulcer_index_confirmed_by_open30_vol_share_20",
        "hypothesis": "A=同上。B=开盘30分钟成交量占比(intraday_volume_profile_1m,本族首次配对)。假设:溃疡指数高(A高)且开盘放量集中(B高,恐慌性开盘抛售)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GA5",
        "operator": "rank_spread",
        "left": _ULCER,
        "right": _GAP_FILL20,
        "mechanism": "ulcer_index_confirmed_by_gap_fill_fraction_20",
        "hypothesis": "A=同上。B=跳空回补比例,20日(gap_repair,本族首次配对)。假设:溃疡指数高(A高)且跳空回补比例低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GA6",
        "operator": "rank_spread",
        "left": _ULCER,
        "right": _JUMP_BETA20,
        "mechanism": "ulcer_index_confirmed_by_jump_beta_20",
        "hypothesis": "A=同上。B=对14只等权篮子跳跃beta,20日(jump_continuous_beta,本族首次配对)。假设:溃疡指数高(A高)且跳跃beta高(B高,系统性冲击驱动深回撤)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GA7",
        "operator": "rank_spread",
        "left": _ULCER,
        "right": _RESILIENCY20,
        "mechanism": "ulcer_index_confirmed_by_resiliency_20",
        "hypothesis": "A=同上。B=流动性恢复力(liquidity_commonality_1m,本族首次配对,概念上与A的痛苦框架呼应)。假设:溃疡指数高(A高)且流动性恢复慢(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GA8",
        "operator": "rank_spread",
        "left": _ULCER,
        "right": _TICK_IMBALANCE,
        "mechanism": "ulcer_index_confirmed_by_tick_imbalance_20",
        "hypothesis": "A=同上。B=tick方向不平衡(bar_size_order_flow,本族首次配对)。假设:溃疡指数高(A高)且tick不平衡明显偏卖(B按discovery定)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- PAIN_INDEX_20: first pairing batch ----
    {
        "id": "GB1",
        "operator": "rank_spread",
        "left": _PAIN,
        "right": _VOL_ENTROPY,
        "mechanism": "pain_index_confirmed_by_vol_entropy_20",
        "hypothesis": "A=痛苦指数(体检disc-0.0935,atomic同样因冗余被拒vs downside_risk族)。B=日内成交量分布熵(intraday_volume_profile_1m,本族首次配对)。假设:痛苦指数高(A高)且成交时点分布均匀(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "GB2",
        "operator": "rank_spread",
        "left": _PAIN,
        "right": _PEER_RESID_Z,
        "mechanism": "pain_index_confirmed_by_peer_resid_z_20",
        "hypothesis": "A=同上。B=相对同伴协整残差z值(peer_relative_value,本族首次配对)。假设:痛苦指数高(A高)且相对同伴负向偏离(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "GB3",
        "operator": "rank_spread",
        "left": _PAIN,
        "right": _GRANGER_IN,
        "mechanism": "pain_index_confirmed_by_granger_in_degree_20",
        "hypothesis": "A=同上。B=格兰杰因果入度(cross_dependence_1m,本族首次配对)。假设:痛苦指数高(A高)且被同伴领先影响强(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GB4",
        "operator": "rank_spread",
        "left": _PAIN,
        "right": _PREMIUM_Z20,
        "mechanism": "pain_index_confirmed_by_premium_z_20",
        "hypothesis": "A=同上。B=净值溢价20日z值(nav_premium,本族首次配对)。假设:痛苦指数高(A高)且溢价异常走低(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "GB5",
        "operator": "rank_spread",
        "left": _PAIN,
        "right": _SHARE_CHG20,
        "mechanism": "pain_index_confirmed_by_share_change_20",
        "hypothesis": "A=同上。B=基金份额20日变化(fund_flow,本族首次配对)。假设:痛苦指数高(A高)且份额收缩(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GB6",
        "operator": "rank_spread",
        "left": _PAIN,
        "right": _RS_RATIO,
        "mechanism": "pain_index_confirmed_by_rs_rv_ratio_20",
        "hypothesis": "A=同上。B=Rogers-Satchell区间估计/RV之比(range_based_vol_1m,S9阶段本族唯一有信号比值,本族首次配对)。假设:痛苦指数高(A高)且bar内活动占比低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GB7",
        "operator": "rank_spread",
        "left": _PAIN,
        "right": _SAMPEN,
        "mechanism": "pain_index_confirmed_by_sampen_ret_20",
        "hypothesis": "A=同上。B=1m收益样本熵(complexity_measures_1m,S11阶段本族原子,本族首次配对)。假设:痛苦指数高(A高)且样本熵高(B高,更随机)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GB8",
        "operator": "rank_spread",
        "left": _PAIN,
        "right": _LOG_AMT,
        "mechanism": "pain_index_confirmed_by_log_amount_vol_20",
        "hypothesis": "A=同上。B=成交额对数波动率(liquidity_variability,本族首次配对)。假设:痛苦指数高(A高)且成交额稳定性低(B高)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- RECOVERY_TIME_FRAC_20: first pairing batch ----
    {
        "id": "GC1",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "recovery_time_frac_confirmed_by_idio_liquidity_shock_20",
        "hypothesis": "A=恢复时间占比(体检disc-0.0462,非shadow,本族最独立原子之一)。B=特异流动性冲击z值(liquidity_commonality_1m,本族首次配对)。假设:恢复耗时占比高(A高,难收复)且特异流动性冲击大(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "GC2",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC,
        "right": _PRICE_AVGCOST,
        "mechanism": "recovery_time_frac_confirmed_by_price_vs_avgcost_20",
        "hypothesis": "A=同上。B=现价相对平均成本偏离(cost_distribution,本族首次配对)。假设:恢复耗时占比高(A高)且现价低于成本(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "GC3",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC,
        "right": _DEP_DRIFT,
        "mechanism": "recovery_time_frac_confirmed_by_dep_drift_20",
        "hypothesis": "A=同上。B=依赖漂移指标(cross_dependence_1m,本族首次配对)。假设:恢复耗时占比高(A高)且依赖漂移方向按discovery定(B)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GC4",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC,
        "right": _VOL_AUTOCORR,
        "mechanism": "recovery_time_frac_confirmed_by_vol_autocorr_20",
        "hypothesis": "A=同上。B=成交量自相关(intraday_volume_profile_1m,本族首次配对)。假设:恢复耗时占比高(A高)且成交量自相关低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GC5",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC,
        "right": _MARKET_CORR20,
        "mechanism": "recovery_time_frac_confirmed_by_market_corr_20",
        "hypothesis": "A=同上。B=对14只等权篮子相关性,20日(market_sensitivity,本族首次配对)。假设:恢复耗时占比高(A高)且与篮子相关性高(B高,系统性拖累恢复)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GC6",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC,
        "right": _YZ_OVERNIGHT,
        "mechanism": "recovery_time_frac_confirmed_by_yz_overnight_share_20",
        "hypothesis": "A=同上。B=Yang-Zhang隔夜方差占比(range_based_vol_1m,S9阶段唯一净入选原子,本族首次配对)。假设:恢复耗时占比高(A高)且隔夜驱动为主(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GC7",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC,
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "recovery_time_frac_confirmed_by_bigbar_vol_share_20",
        "hypothesis": "A=同上。B=大单成交量占比(bar_size_order_flow,本线通道原子之一,本族首次配对)。假设:恢复耗时占比高(A高)且大单占比低(B低,无大单托底)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GC8",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC,
        "right": _LBAR_RET_CONTRIB,
        "mechanism": "recovery_time_frac_confirmed_by_lbar_ret_contrib_20",
        "hypothesis": "A=同上。B=大单bar对当日收益贡献占比(largebar_footprint_1m,本族首次配对)。假设:恢复耗时占比高(A高)且大单贡献低(B低)=延续;本族最后一批。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
