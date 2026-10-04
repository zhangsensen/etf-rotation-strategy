#!/usr/bin/env python3
"""Round 515 driver: S3 stage step 3 -- third pairing batch for
intraday_momentum_30m. rounds 513-514 admitted 6 candidates total but
also produced repeated redundancy rejections (GHP4/GHP6/GI1/GI7, all
t>2.5) whenever OVERNIGHT_FIRST30_CORR_20 paired with a partner too
similar to an already-admitted candidate or to the partner's own strong
standalone signal. This round broadens to genuinely new partner families
never tried against ANY intraday_momentum_30m atom (peer_relative_value,
cross_dependence_1m, cojump_1m, fund_flow, category_state's
CATEGORY_DISPERSION_20 -- the one historically shelf16 gate-7-standalone
factor) plus fills remaining gaps for INTRADAY_MOM_CORR_20/60,
LAST30_NEXTOPEN_CORR_20 and INTRADAY_MOM_BETA_20."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_515"

_PEER_OU = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_GRANGER_OUT = {"name": "GRANGER_OUT_DEGREE_20", "source": "cross_dependence_1m"}
_NET_SPILL = {"name": "NET_SPILLOVER_20", "source": "cross_dependence_1m"}
_IDIO_JUMP = {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"}
_COJUMP_DIR = {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"}
_SHARE_CORR = {"name": "SHARE_RET_CORR_20", "source": "fund_flow"}
_CAT_DISP = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_CLOSE30 = {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_LBAR_TREND = {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"}
_VOL_USHAPE = {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"}
_EDGE_CONC = {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_RESIL = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_TICK_IMB = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}
_VOL_PROFILE_DIST = {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}

base.CANDIDATES = [
    # ---- Group A: OVERNIGHT_FIRST30_CORR_20 x 10 genuinely new-family partners ----
    {
        "id": "GN1",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _PEER_OU,
        "mechanism": "overnight_first30_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=隔夜-开盘延续相关性（round_513体检 disc+0.0452/审计+0.0789，round_513-514已admit4个partner）；B=同伴篓子OU均值回复半衰期（round_052体检：disc+0.013/审计+0.035，peer_relative_value家族从未与本atom配对）。假设：延续性稳定(A高)且相对同伴回复慢(B高)=延续叠加统计套利式错定价持续，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GN2",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _GRANGER_OUT,
        "mechanism": "overnight_first30_confirmed_by_granger_out_degree",
        "hypothesis": "A=同上；B=Granger网络出度（round_052体检：disc-0.022/审计-0.039，cross_dependence_1m家族从未与本atom配对）。假设：延续性稳定(A高)且对外溢出弱(B低)=延续不易被跨资产套利消化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GN3",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _NET_SPILL,
        "mechanism": "overnight_first30_confirmed_by_net_spillover",
        "hypothesis": "A=同上；B=净溢出（round_052体检：disc+0.048/审计-0.016，本cross_dependence_1m家族发现IC最高原子）。假设：延续性稳定(A高)且净溢出为正(B高)=延续由领先性资产驱动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GN4",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _IDIO_JUMP,
        "mechanism": "overnight_first30_confirmed_by_idio_jump_share",
        "hypothesis": "A=同上；B=特质跳跃份额（round_049体检，Jacod-Todorov 2009：disc+0.047/审计+0.014，cojump_1m家族从未与本atom配对）。假设：延续性稳定(A高)且跳跃为特质性(B高)=延续由个体事件驱动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GN5",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _COJUMP_DIR,
        "mechanism": "overnight_first30_confirmed_by_cojump_dir_agree",
        "hypothesis": "A=同上；B=共跳方向一致度（round_049体检：disc-0.080/审计-0.068）。假设：延续性稳定(A高)且跳跃方向与市场一致(B高)=延续伴随同步性跳跃，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GN6",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _SHARE_CORR,
        "mechanism": "overnight_first30_confirmed_by_share_ret_corr",
        "hypothesis": "A=同上；B=份额变化与收益相关性（round_034体检：disc+0.0137/审计+0.0320，出现在5个admitted组合，fund_flow家族从未与本atom配对）。假设：延续性稳定(A高)且份额-收益同向性强(B高)=延续伴随资金追涨行为，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GN7",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CAT_DISP,
        "mechanism": "overnight_first30_confirmed_by_category_dispersion",
        "hypothesis": "A=同上；B=类别内离散度（round_071复盘：货架16中门7独立通过的3个之一，审计超额+23.3bp，本线迄今唯一已知单独可过门7的候选，从未与upside_tail/coskewness/本家族配对过）。假设：延续性稳定(A高)且类别内分化大(B高)=延续在有相对赢家输家的环境中更易兑现，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GN8",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_ENTROPY,
        "mechanism": "overnight_first30_confirmed_by_volume_entropy",
        "hypothesis": "A=同上；B=日内成交量分布熵（round_024体检：disc+0.0070/审计+0.0229）。假设：延续性稳定(A高)且成交分布分散(B高)=延续伴随不集中日内结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GN9",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CLOSE30,
        "mechanism": "overnight_first30_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上；B=收盘30分钟成交占比（round_024体检：disc+0.0468/审计-0.0044）。假设：延续性稳定(A高)且尾盘集中交易(B高)=延续在尾盘被知情资金定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GN10",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_TREND,
        "mechanism": "overnight_first30_confirmed_by_bigbar_trend",
        "hypothesis": "A=同上；B=大bar量占比趋势（round_079单腿：disc+0.0426/审计+0.0206/t=0.82/审超+23.7bp）。假设：延续性稳定(A高)且大单活动升温(B高)=延续伴随知情流入渐进增强，延续。",
        "expected_sign": 1,
    },
    # ---- Group B: INTRADAY_MOM_CORR_20 x 5 new partners ----
    {
        "id": "GO1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_USHAPE,
        "mechanism": "intraday_momentum_confirmed_by_session_ushape",
        "hypothesis": "A=首末30分钟收益相关性（round_513已admit与VOL_PROFILE_DISTANCE配对，t=3.50）；B=日内成交量U型集中度（round_053门7全过：disc-0.0832/审计-0.0891/t=2.12/审超+33.9bp）。假设：日内动量关系强(A高)且开收盘成交集中(B高)=关系伴随主力时点操作，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GO2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _EDGE_CONC,
        "mechanism": "intraday_momentum_confirmed_by_edge_concentration",
        "hypothesis": "A=同上；B=大bar价格边缘集中度（round_053门7全过：disc-0.0971/审计-0.0459/t=2.55/审超+30.7bp）。假设：日内动量关系强(A高)且边缘冲击集中(B高)=关系伴随激进订单，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GO3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "intraday_momentum_confirmed_by_bigbar_vol_share",
        "hypothesis": "A=同上；B=大bar成交量占比（round_053门7全过：disc+0.0832/审计+0.0548/t=2.92/审超+41.6bp）。假设：日内动量关系强(A高)且大单流入活跃(B高)=关系被真实资金承接，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GO4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _PEER_OU,
        "mechanism": "intraday_momentum_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上；B=同伴篓子OU半衰期（同GN1）。假设：日内动量关系强(A高)且相对同伴回复慢(B高)=关系叠加统计套利式错定价持续，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GO5",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _GRANGER_OUT,
        "mechanism": "intraday_momentum_confirmed_by_granger_out_degree",
        "hypothesis": "A=同上；B=Granger网络出度（同GN2）。假设：日内动量关系强(A高)且对外溢出弱(B低)=关系不易被跨资产套利消化，延续。",
        "expected_sign": 1,
    },
    # ---- Group C: INTRADAY_MOM_CORR_60 x 3 new partners ----
    {
        "id": "GP1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _GAP_FILL,
        "mechanism": "intraday_momentum60_confirmed_by_gap_absorption",
        "hypothesis": "60日窗版本。A=首末30分钟收益相关性60日窗（round_513体检 disc-0.0146/审计+0.0076；round_514已admit与OPEN30_VOL_SHARE_20配对，t=2.08）；B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：长窗关系强(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GP2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _WORST_DAY,
        "mechanism": "intraday_momentum60_confirmed_by_own_worst_day",
        "hypothesis": "同GP1，B=自身20日最差单日收益（round_053门7全过：disc+0.0635/审计+0.0648/t=2.18/审超+16.2bp）。假设：长窗关系强(A高)且自身尾部重(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GP3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _RESIL,
        "mechanism": "intraday_momentum60_confirmed_by_resiliency",
        "hypothesis": "同GP1，B=1m冲击回复力（round_049体检：disc-0.114/审计-0.041，本线admitted组合中出现频次最高原子）。假设：长窗关系强(A高)且流动性回复力弱(B低)=延续。",
        "expected_sign": 1,
    },
    # ---- Group D: LAST30_NEXTOPEN_CORR_20 x 2 new partners ----
    {
        "id": "GQ1",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CATEGORY_VOL,
        "mechanism": "last30_nextopen_confirmed_by_category_vol",
        "hypothesis": "A=尾盘30分钟收益与次日隔夜跳空相关（已按信号时点错位对齐，round_513体检 disc+0.0188/审计-0.0508）；B=同类别板块波动率（round_053门7全过：disc-0.0711/审计-0.0653/t=2.42/审超+19.0bp）。假设：尾盘预测次日跳空关系强(A高)且板块高波动(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GQ2",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _TICK_IMB,
        "mechanism": "last30_nextopen_confirmed_by_orderflow",
        "hypothesis": "同GQ1，B=主买不平衡（round_079单腿：disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp）。假设：尾盘-次日关系强(A高)且日内买流强(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- Group E: INTRADAY_MOM_BETA_20 x 2 new partners ----
    {
        "id": "GR1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _VOL_PROFILE_DIST,
        "mechanism": "intraday_momentum_beta_confirmed_by_volume_profile_shift",
        "hypothesis": "回归斜率版本。A=末30分钟对首30分钟收益回归斜率（round_513体检 disc-0.0108/审计-0.0551）；B=日内成交量分布偏离（round_053门7全过，本线最高t单原子t=4.04）。假设：传导斜率大(A高)且日内成交结构异常(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GR2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _CATEGORY_VOL,
        "mechanism": "intraday_momentum_beta_confirmed_by_category_vol",
        "hypothesis": "同GR1，B=同类别板块波动率（同GQ1）。假设：传导斜率大(A高)且板块高波动(B高)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
