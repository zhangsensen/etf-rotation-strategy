#!/usr/bin/env python3
"""Round 516 driver: S3 stage step 4. Yield has been shrinking each round
(round_513: 4/17, round_514: 2/23, round_515: 1/22) as OVERNIGHT_FIRST30_
CORR_20/INTRADAY_MOM_CORR_20's information keeps getting absorbed by
their own earlier admissions. This round shifts weight to the two
still-mostly-untested atoms (LAST30_NEXTOPEN_CORR_20, INTRADAY_MOM_
BETA_20) against a broad partner set including PEER_OU_HALFLIFE_20 (just
proven in round_515's GO4 admission) plus a couple of remaining
cross_dependence_1m atoms for OVERNIGHT_FIRST30_CORR_20. If this round
also comes back weak, the next round (if also zero) would be the third
consecutive zero and trigger the stage retrospective."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_516"

_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_RESIL = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_PEER_OU = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_CAT_DISP = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}

base.CANDIDATES = [
    # ---- Group A: LAST30_NEXTOPEN_CORR_20 x 9 new partners (mostly untested atom) ----
    {
        "id": "GS1",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_SPIKE,
        "mechanism": "last30_nextopen_confirmed_by_volume_spike_freq",
        "hypothesis": "A=尾盘30分钟收益与次日隔夜跳空相关（已按信号时点错位对齐，round_513体检 disc+0.0188/审计-0.0508）；B=成交量脉冲频率（round_506已证明是S2阶段有效confirming partner，disc+0.0661/审计+0.0460）。假设：尾盘预测次日跳空关系强(A高)且脉冲放量频繁(B高)=关系有交易活动确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GS2",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "last30_nextopen_confirmed_by_bigbar_vol_share",
        "hypothesis": "A=同上；B=大bar成交量占比（round_053门7全过：disc+0.0832/审计+0.0548/t=2.92/审超+41.6bp）。假设：尾盘-次日关系强(A高)且大单流入活跃(B高)=关系被真实资金承接，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GS3",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _GAP_FILL,
        "mechanism": "last30_nextopen_confirmed_by_gap_absorption",
        "hypothesis": "A=同上；B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：尾盘-次日关系强(A高)且缺口易回补(B高)=关系有流动性缓冲，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GS4",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _WORST_DAY,
        "mechanism": "last30_nextopen_confirmed_by_own_worst_day",
        "hypothesis": "A=同上；B=自身20日最差单日收益（round_053门7全过：disc+0.0635/审计+0.0648/t=2.18/审超+16.2bp）。假设：尾盘-次日关系强(A高)且自身尾部重(B高)=关系与尾部风险叠加，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GS5",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CHIP_RANGE,
        "mechanism": "last30_nextopen_locked_by_chip_concentration",
        "hypothesis": "A=同上；B=筹码区间宽度（round_079单腿：disc-0.0574/审计-0.0620/t=0.70/审超+14.6bp）。假设：尾盘-次日关系强(A高)且筹码集中(B高)=关系被锁仓盘固化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GS6",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LOG_AMT,
        "mechanism": "last30_nextopen_confirmed_by_high_activity",
        "hypothesis": "A=同上；B=对数成交额（round_079单腿：disc+0.0661/审计+0.0701/t=2.23/审超+36.8bp，本线历史最强单腿之一）。假设：尾盘-次日关系强(A高)且活跃度高(B高)=关系发生在流动性充足环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GS7",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _RESIL,
        "mechanism": "last30_nextopen_confirmed_by_resiliency",
        "hypothesis": "A=同上；B=1m冲击回复力（round_049体检：disc-0.114/审计-0.041，本线admitted组合中出现频次最高原子）。假设：尾盘-次日关系强(A高)且流动性回复力弱(B低)=关系发生在脆弱流动性环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GS8",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _PEER_OU,
        "mechanism": "last30_nextopen_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上；B=同伴篓子OU均值回复半衰期（round_515 GO4已证明是本家族有效confirming partner，disc+0.013/审计+0.035）。假设：尾盘-次日关系强(A高)且相对同伴回复慢(B高)=关系叠加统计套利式错定价持续，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GS9",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CAT_DISP,
        "mechanism": "last30_nextopen_confirmed_by_category_dispersion",
        "hypothesis": "A=同上；B=类别内离散度（round_071复盘：货架16门7独立通过的3个之一，审计超额+23.3bp）。假设：尾盘-次日关系强(A高)且类别内分化大(B高)=关系在有相对赢家输家的环境中更易兑现，延续。",
        "expected_sign": 1,
    },
    # ---- Group B: INTRADAY_MOM_BETA_20 x 6 new partners ----
    {
        "id": "GT1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _VOL_SPIKE,
        "mechanism": "intraday_momentum_beta_confirmed_by_volume_spike_freq",
        "hypothesis": "A=末30分钟对首30分钟收益回归斜率（round_513体检 disc-0.0108/审计-0.0551）；B=成交量脉冲频率（同GS1）。假设：传导斜率大(A高)且脉冲放量频繁(B高)=传导强度有交易活动确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GT2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "intraday_momentum_beta_confirmed_by_bigbar_vol_share",
        "hypothesis": "A=同上；B=大bar成交量占比（同GS2）。假设：传导斜率大(A高)且大单流入活跃(B高)=传导被真实资金承接，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GT3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _GAP_FILL,
        "mechanism": "intraday_momentum_beta_confirmed_by_gap_absorption",
        "hypothesis": "A=同上；B=缺口回补比例（同GS3）。假设：传导斜率大(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GT4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _WORST_DAY,
        "mechanism": "intraday_momentum_beta_confirmed_by_own_worst_day",
        "hypothesis": "A=同上；B=自身20日最差单日收益（同GS4）。假设：传导斜率大(A高)且自身尾部重(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GT5",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _RESIL,
        "mechanism": "intraday_momentum_beta_confirmed_by_resiliency",
        "hypothesis": "A=同上；B=1m冲击回复力（同GS7）。假设：传导斜率大(A高)且流动性回复力弱(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GT6",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _PEER_OU,
        "mechanism": "intraday_momentum_beta_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上；B=同伴篓子OU半衰期（同GS8）。假设：传导斜率大(A高)且相对同伴回复慢(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- Group C: INTRADAY_MOM_CORR_60 x 3 new partners ----
    {
        "id": "GU1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _PEER_OU,
        "mechanism": "intraday_momentum60_confirmed_by_peer_ou_halflife",
        "hypothesis": "60日窗版本。A=首末30分钟收益相关性60日窗（round_514已admit与OPEN30_VOL_SHARE_20配对，t=2.08）；B=同伴篓子OU半衰期（同GS8）。假设：长窗关系强(A高)且相对同伴回复慢(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GU2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _CAT_DISP,
        "mechanism": "intraday_momentum60_confirmed_by_category_dispersion",
        "hypothesis": "同GU1，B=类别内离散度（同GS9）。假设：长窗关系强(A高)且类别内分化大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GU3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "intraday_momentum60_confirmed_by_bigbar_vol_share",
        "hypothesis": "同GU1，B=大bar成交量占比（同GS2）。假设：长窗关系强(A高)且大单流入活跃(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- Group D: OVERNIGHT_FIRST30_CORR_20 x 2 remaining new partners ----
    {
        "id": "GV1",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _DEP_DRIFT,
        "mechanism": "overnight_first30_confirmed_by_dep_drift",
        "hypothesis": "A=隔夜-开盘延续相关性（round_513-515已admit4个partner）；B=依赖度漂移（round_052体检：disc-0.018/审计-0.015）。假设：延续性稳定(A高)且与池依赖度下降(B低)=延续伴随脱离系统性联动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GV2",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _GRANGER_IN,
        "mechanism": "overnight_first30_confirmed_by_granger_in_degree",
        "hypothesis": "A=同上；B=Granger网络入度（round_052体检：disc-0.079/审计-0.044，本cross_dependence_1m家族相关性最高原子）。假设：延续性稳定(A高)且接受外部溢出弱(B低)=延续独立于池内联动，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
