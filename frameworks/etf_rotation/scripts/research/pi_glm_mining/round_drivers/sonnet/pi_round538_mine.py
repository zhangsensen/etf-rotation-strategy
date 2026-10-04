#!/usr/bin/env python3
"""Round 538 driver: S10 stage step 3 -- accumulation_distribution_1m
pairing, round 3. Three independent first-pairing batches for the three
remaining non-shadow, not-yet-paired atoms: AD_NET_FLOW_20,
AD_NET_FLOW_SLOPE_20, AD_NET_FLOW_CHG_20 (round_536 atomic: t=2.57, 2.64,
1.29 respectively -- the first two had strong discovery block-t but
failed on audit-sign instability and identity gate, i.e. the raw
directional relationship isn't stable enough on its own; testing whether
a confirming partner narrows this down to a more robust subset of
days/regimes, the same logic that turned round_536's atomic AD_PRICE_CORR_20
into round_537's two pairing confirmations).

Only OBV_SLOPE_20 and MFI_EXTREME_FRAC_20 (both atom-health shadow) will
remain untested as left legs after this round -- the last legal pairing
space for this family.

All right-leg partners below are new or a second use (well under the
<=3-different-left-legs cap) relative to this family's S10 pairing
history (round_536/537's 24 partners). No same-family pairs, no window
variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_538"

_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_LBAR_CLOCK = {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"}
_CLOSE5_CONSIST = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_PROFIT_RATIO = {"name": "PROFIT_RATIO_60", "source": "cost_distribution"}
_PEER_RESID_MOM = {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"}

_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_BIGBAR_EDGE = {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"}
_VOL_PROFILE_DIST = {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_TURNOVER_DIST = {"name": "TURNOVER_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_COJUMP_INDEX = {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"}
_LIQ_COMMON_BETA = {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}

_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_DOWNSIDE_COSKEW60 = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}
_RS_MINUS20 = {"name": "RS_MINUS_20", "source": "realized_measures_1m"}
_VPIN_CLOSE = {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"}
_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_PEER_LEAD_NET60 = {"name": "PEER_LEAD_NETWORK_CORR_60", "source": "cross_etf_lead_lag"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}

_AD_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}
_AD_FLOW_SLOPE = {"name": "AD_NET_FLOW_SLOPE_20", "source": "accumulation_distribution_1m"}
_AD_FLOW_CHG = {"name": "AD_NET_FLOW_CHG_20", "source": "accumulation_distribution_1m"}

base.CANDIDATES = [
    # ---- AD_NET_FLOW_20: first pairing batch (atomic t=2.57, failed only
    # on audit-sign instability + identity) ----
    {
        "id": "NE1",
        "operator": "rank_spread",
        "left": _AD_FLOW,
        "right": _OPEN30,
        "mechanism": "ad_net_flow_confirmed_by_open30_vol_share",
        "hypothesis": "A=CLV加权量流净额占比（Chaikin 1966/1982，round_536 atomic disc-0.056/审计+0.027，t=2.57但audit-sign翻转+identity不稳定）。B=开盘30分钟成交占比（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：量流净额高(A高)且开盘集中放量(B高)=积累行为在开盘时段被确认，可能筛选出更稳定的子集，延续。",
        "expected_sign": 1,
    },
    {
        "id": "NE2",
        "operator": "rank_spread",
        "left": _AD_FLOW,
        "right": _VOL_SPIKE,
        "mechanism": "ad_net_flow_confirmed_by_volume_spike_freq",
        "hypothesis": "A=同上。B=成交量脉冲频率（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：量流净额高(A高)且脉冲放量频繁(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NE3",
        "operator": "rank_spread",
        "left": _AD_FLOW,
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "ad_net_flow_confirmed_by_bigbar_vol_share",
        "hypothesis": "A=同上。B=大bar成交量占比（bar_size_order_flow，本族首次配对）。假设：量流净额高(A高)且大bar贡献成交量占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NE4",
        "operator": "rank_spread",
        "left": _AD_FLOW,
        "right": _LBAR_CLOCK,
        "mechanism": "ad_net_flow_confirmed_by_lbar_clock_std",
        "hypothesis": "A=同上。B=大bar发生时点的20日标准差（largebar_footprint_1m，本族首次配对）。假设：量流净额高(A高)且大bar发生时点分散(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NE5",
        "operator": "rank_spread",
        "left": _AD_FLOW,
        "right": _CLOSE5_CONSIST,
        "mechanism": "ad_net_flow_confirmed_by_close5_day_consistency",
        "hypothesis": "A=同上。B=收盘前5分钟方向一致性（bar_size_order_flow，本族首次配对）。假设：量流净额高(A高)且尾盘方向一致性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NE6",
        "operator": "rank_spread",
        "left": _AD_FLOW,
        "right": _VOL_ENTROPY,
        "mechanism": "ad_net_flow_confirmed_by_volume_entropy",
        "hypothesis": "A=同上。B=日内成交量分布熵（intraday_volume_profile_1m，本族首次配对）。假设：量流净额高(A高)且成交量分布熵低(B低，集中)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NE7",
        "operator": "rank_spread",
        "left": _AD_FLOW,
        "right": _PROFIT_RATIO,
        "mechanism": "ad_net_flow_confirmed_by_profit_ratio",
        "hypothesis": "A=同上。B=60日获利比例（cost_distribution，本族首次配对）。假设：量流净额高(A高)且获利盘占比高(B高)=积累行为伴随获利盘扩大，延续。",
        "expected_sign": 1,
    },
    {
        "id": "NE8",
        "operator": "rank_spread",
        "left": _AD_FLOW,
        "right": _PEER_RESID_MOM,
        "mechanism": "ad_net_flow_confirmed_by_peer_resid_momentum",
        "hypothesis": "A=同上。B=同伴协整残差动量（peer_relative_value，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：量流净额高(A高)且相对同伴偏离扩大(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- AD_NET_FLOW_SLOPE_20: first pairing batch (atomic t=2.64,
    # strongest atomic block-t in the family, same failure pattern) ----
    {
        "id": "NF1",
        "operator": "rank_spread",
        "left": _AD_FLOW_SLOPE,
        "right": _LOG_AMT,
        "mechanism": "ad_net_flow_slope_confirmed_by_high_activity",
        "hypothesis": "A=量流净额占比的20日趋势斜率（round_536 atomic t=2.64，本族最高原子门7 discovery t，但audit-sign翻转+identity不稳定）。B=对数成交额（liquidity_variability，本线历史最强单腿之一）。假设：量流净额趋势上升(A高)且整体活跃度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NF2",
        "operator": "rank_spread",
        "left": _AD_FLOW_SLOPE,
        "right": _GAP_FILL60,
        "mechanism": "ad_net_flow_slope_confirmed_by_gap_absorption",
        "hypothesis": "A=同上。B=60日窗缺口回补比例（gap_repair，round_053门7全过史）。假设：量流净额趋势上升(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NF3",
        "operator": "rank_spread",
        "left": _AD_FLOW_SLOPE,
        "right": _BIGBAR_EDGE,
        "mechanism": "ad_net_flow_slope_confirmed_by_bigbar_edge_concentration",
        "hypothesis": "A=同上。B=大bar集中于日内边缘时段的程度（bar_size_order_flow，本族首次配对）。假设：量流净额趋势上升(A高)且大bar集中在开盘/收盘边缘(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NF4",
        "operator": "rank_spread",
        "left": _AD_FLOW_SLOPE,
        "right": _VOL_PROFILE_DIST,
        "mechanism": "ad_net_flow_slope_confirmed_by_volume_profile_shift",
        "hypothesis": "A=同上。B=日内成交量分布偏离（intraday_profile_deviation，本线最高t单原子历史，本族首次配对）。假设：量流净额趋势上升(A高)且日内成交结构异常(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NF5",
        "operator": "rank_spread",
        "left": _AD_FLOW_SLOPE,
        "right": _TURNOVER_DIST,
        "mechanism": "ad_net_flow_slope_confirmed_by_turnover_profile_shift",
        "hypothesis": "A=同上。B=日内换手分布偏离（intraday_profile_deviation，本族首次配对）。假设：量流净额趋势上升(A高)且日内换手结构异常(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NF6",
        "operator": "rank_spread",
        "left": _AD_FLOW_SLOPE,
        "right": _COJUMP_INDEX,
        "mechanism": "ad_net_flow_slope_confirmed_by_cojump_index_share",
        "hypothesis": "A=同上。B=共跳占指数跳跃比例（cojump_1m，本族首次配对）。假设：量流净额趋势上升(A高)且与指数共跳比例高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NF7",
        "operator": "rank_spread",
        "left": _AD_FLOW_SLOPE,
        "right": _LIQ_COMMON_BETA,
        "mechanism": "ad_net_flow_slope_confirmed_by_liquidity_common_beta",
        "hypothesis": "A=同上。B=流动性共性beta（liquidity_commonality_1m，本族首次配对）。假设：量流净额趋势上升(A高)且流动性共性beta高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NF8",
        "operator": "rank_spread",
        "left": _AD_FLOW_SLOPE,
        "right": _GRANGER_IN,
        "mechanism": "ad_net_flow_slope_confirmed_by_granger_in_degree",
        "hypothesis": "A=同上。B=格兰杰因果入度（cross_dependence_1m，本族首次配对）。假设：量流净额趋势上升(A高)且被同伴领先影响强(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- AD_NET_FLOW_CHG_20: first pairing batch ----
    {
        "id": "NG1",
        "operator": "rank_spread",
        "left": _AD_FLOW_CHG,
        "right": _BIGBAR_DIR_SKEW,
        "mechanism": "ad_net_flow_chg_confirmed_by_bigbar_dir_skew",
        "hypothesis": "A=量流净额占比的20日变化（round_536 atomic disc-0.040/审计+0.023，t=1.29较弱，但与其他两个AD_NET_FLOW原子同源，测试其配对空间）。B=大bar方向偏斜（bar_size_order_flow，S4阶段最强confirming partner之一，t=3.48）。假设：量流净额正在上升(A高)且大bar方向持续偏向一侧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NG2",
        "operator": "rank_spread",
        "left": _AD_FLOW_CHG,
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "ad_net_flow_chg_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=同伴OU回归半衰期（peer_relative_value，S4阶段本线最高命中率家族，t=3.75）。假设：量流净额上升(A高)且相对同伴回复速度慢(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NG3",
        "operator": "rank_spread",
        "left": _AD_FLOW_CHG,
        "right": _DOWNSIDE_COSKEW60,
        "mechanism": "ad_net_flow_chg_confirmed_by_downside_coskewness",
        "hypothesis": "A=同上。B=条件协偏度，仅用市场下跌日计算（coskewness_risk，本族首次配对）。假设：量流净额上升(A高)且下行协偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NG4",
        "operator": "rank_spread",
        "left": _AD_FLOW_CHG,
        "right": _RS_MINUS20,
        "mechanism": "ad_net_flow_chg_confirmed_by_realized_semivariance_minus",
        "hypothesis": "A=同上。B=已实现负半方差占比（realized_measures_1m，S4阶段CONTINUOUS_BETA_60命中partner，t=2.34，本族首次配对）。假设：量流净额上升(A高)且下行半方差占比低(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NG5",
        "operator": "rank_spread",
        "left": _AD_FLOW_CHG,
        "right": _VPIN_CLOSE,
        "mechanism": "ad_net_flow_chg_confirmed_by_vpin",
        "hypothesis": "A=同上。B=收盘时点VPIN（microstructure_1m，本族首次配对）。假设：量流净额上升(A高)且VPIN高(B高，知情交易占比高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NG6",
        "operator": "rank_spread",
        "left": _AD_FLOW_CHG,
        "right": _AMIHUD_1M,
        "mechanism": "ad_net_flow_chg_confirmed_by_amihud_1m",
        "hypothesis": "A=同上。B=Amihud非流动性比率的1m版本（microstructure_1m，本族首次配对）。假设：量流净额上升(A高)且非流动性低(B低，流动性好支持积累)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "NG7",
        "operator": "rank_spread",
        "left": _AD_FLOW_CHG,
        "right": _PEER_LEAD_NET60,
        "mechanism": "ad_net_flow_chg_confirmed_by_peer_lead_network_corr",
        "hypothesis": "A=同上。B=同伴网络领先相关性，60日（cross_etf_lead_lag，S4阶段CONTINUOUS_BETA_60命中partner，t=3.30，本族首次配对）。假设：量流净额上升(A高)且网络领先关系强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NG8",
        "operator": "rank_spread",
        "left": _AD_FLOW_CHG,
        "right": _GAP_SESSION_CORR,
        "mechanism": "ad_net_flow_chg_confirmed_by_gap_session_correlation",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性（gap_response，S4阶段CONTINUOUS_BETA_60最强命中partner，t=3.89，本族首次配对）。假设：量流净额上升(A高)且跳空延续性强(B高)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
