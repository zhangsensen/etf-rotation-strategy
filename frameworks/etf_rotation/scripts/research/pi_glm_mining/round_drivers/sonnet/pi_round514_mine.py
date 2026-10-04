#!/usr/bin/env python3
"""Round 514 driver: S3 stage step 2 -- second pairing batch for
intraday_momentum_30m (Gao-Han-Li-Zhou 2018). round_513 admitted 4/17 on
the first round: GHP2/GHP3/GHP7 (OVERNIGHT_FIRST30_CORR_20 x
OPEN30_VOL_SHARE_20/VOL_AUTOCORR_20/CATEGORY_VOL_20) and GHP11
(INTRADAY_MOM_CORR_20 x VOL_PROFILE_DISTANCE); GHP4/GHP6 would also have
passed but were caught by rank_correlation_redundancy against GHP2/GHP3
(same left leg, same batch). This round broadens partner coverage for
OVERNIGHT_FIRST30_CORR_20 and INTRADAY_MOM_CORR_20 to atoms never yet
tried against this family, plus a first pairing pass for the three
untested atoms (INTRADAY_MOM_CORR_60, INTRADAY_MOM_BETA_20,
LAST30_NEXTOPEN_CORR_20)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_514"

_GAP_FILL = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_VOL_PROFILE_DIST = {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_TICK_IMB = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_RESIL = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_LBAR_RC = {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"}
_VOL_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}

base.CANDIDATES = [
    # ---- Group A: OVERNIGHT_FIRST30_CORR_20 x 8 new partners (strongest atom, 3/7 admitted so far) ----
    {
        "id": "GI1",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _GAP_FILL,
        "mechanism": "overnight_first30_confirmed_by_gap_absorption",
        "hypothesis": "两腿角色：A=隔夜-开盘延续相关性（round_513体检 disc+0.0452/审计+0.0789；round_513已admit 3个partner）；B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：延续性稳定(A高)且缺口易回补(B高)=延续性资产也有流动性缓冲，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GI2",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_PROFILE_DIST,
        "mechanism": "overnight_first30_confirmed_by_volume_profile_shift",
        "hypothesis": "两腿角色：A=同上；B=日内成交量分布偏离（round_053门7全过：disc+0.0952/审计+0.0442/t=4.04，本线最高t单原子；round_513 GHP11已证明与本家族另一原子配对通过）。假设：延续性稳定(A高)且日内成交结构异常(B高)=延续伴随异常时点结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GI3",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _WORST_DAY,
        "mechanism": "overnight_first30_confirmed_by_own_worst_day",
        "hypothesis": "两腿角色：A=同上；B=自身20日最差单日收益（round_053门7全过：disc+0.0635/审计+0.0648/t=2.18/审超+16.2bp）。假设：延续性稳定(A高)且自身尾部也重(B高)=延续与尾部风险叠加，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GI4",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _TICK_IMB,
        "mechanism": "overnight_first30_confirmed_by_orderflow",
        "hypothesis": "两腿角色：A=同上；B=主买不平衡（round_079单腿：disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp，偏弱）。假设：延续性稳定(A高)且日内买流强(B高)=延续有主动买盘确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GI5",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CHIP_RANGE,
        "mechanism": "overnight_first30_locked_by_chip_concentration",
        "hypothesis": "两腿角色：A=同上；B=筹码区间宽度（round_079单腿：disc-0.0574/审计-0.0620/t=0.70/审超+14.6bp）。假设：延续性稳定(A高)且筹码集中(B高)=延续被锁仓盘固化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GI6",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LOG_AMT,
        "mechanism": "overnight_first30_confirmed_by_high_activity",
        "hypothesis": "两腿角色：A=同上；B=对数成交额（round_079单腿：disc+0.0661/审计+0.0701/t=2.23/审超+36.8bp，本线历史最强单腿之一）。假设：延续性稳定(A高)且活跃度高(B高)=延续发生在流动性充足的环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GI7",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _RESIL,
        "mechanism": "overnight_first30_confirmed_by_resiliency",
        "hypothesis": "两腿角色：A=同上；B=1m冲击回复力（round_049体检：disc-0.114/审计-0.041，本线admitted组合中出现频次最高的原子，7次）。假设：延续性稳定(A高)且流动性回复力弱(B低)=延续发生在脆弱流动性环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GI8",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_RC,
        "mechanism": "overnight_first30_confirmed_by_bigbar_ret_contrib",
        "hypothesis": "两腿角色：A=同上；B=大bar收益承载份额（round_079单腿：disc-0.0164/审计-0.0111/t=0.55/审超+6.2bp）。假设：延续性稳定(A高)且收益由大bar承载(B高)=延续由大单驱动，延续。",
        "expected_sign": 1,
    },
    # ---- Group B: INTRADAY_MOM_CORR_20 x 6 new partners (already admitted with VOL_PROFILE_DISTANCE) ----
    {
        "id": "GJ1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _TICK_IMB,
        "mechanism": "intraday_momentum_confirmed_by_orderflow",
        "hypothesis": "两腿角色：A=首末30分钟收益相关性（round_513 GHP11已admit与VOL_PROFILE_DISTANCE配对，t=3.50）；B=主买不平衡（同GI4）。假设：日内动量关系强(A高)且买流强(B高)=关系有主动买盘确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GJ2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CHIP_RANGE,
        "mechanism": "intraday_momentum_locked_by_chip_concentration",
        "hypothesis": "两腿角色：A=同上；B=筹码区间宽度（同GI5）。假设：日内动量关系强(A高)且筹码集中(B高)=关系被锁仓盘固化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GJ3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _RESIL,
        "mechanism": "intraday_momentum_confirmed_by_resiliency",
        "hypothesis": "两腿角色：A=同上；B=1m冲击回复力（同GI7）。假设：日内动量关系强(A高)且流动性回复力弱(B低)=关系发生在脆弱流动性环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GJ4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_RC,
        "mechanism": "intraday_momentum_confirmed_by_bigbar_ret_contrib",
        "hypothesis": "两腿角色：A=同上；B=大bar收益承载份额（同GI8）。假设：日内动量关系强(A高)且收益由大bar承载(B高)=关系由大单驱动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GJ5",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_AUTOCORR,
        "mechanism": "intraday_momentum_confirmed_by_volume_autocorr",
        "hypothesis": "两腿角色：A=同上；B=日内成交量自相关（round_513 GHP3已证明是本家族确认partner，disc-0.0722/审计-0.0551）。假设：日内动量关系强(A高)且成交有节奏持续性(B高)=关系伴随规律流动性投放，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GJ6",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CATEGORY_VOL,
        "mechanism": "intraday_momentum_confirmed_by_category_vol",
        "hypothesis": "两腿角色：A=同上；B=同类别板块波动率（round_513 GHP7已证明是本家族确认partner，disc-0.0711/审计-0.0653）。假设：日内动量关系强(A高)且板块高波动(B高)=关系来自板块层面共振，延续。",
        "expected_sign": 1,
    },
    # ---- Group C: INTRADAY_MOM_CORR_60 x 4 proven partners (untested atom) ----
    {
        "id": "GK1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _OPEN30,
        "mechanism": "intraday_momentum60_confirmed_by_open30_vol_share",
        "hypothesis": "60日窗版本首次配对测试。A=首末30分钟收益相关性60日窗（round_513体检 disc-0.0146/审计+0.0076）；B=开盘30分钟成交占比（round_513已证明是本家族最强confirming partner之一）。假设：长窗日内动量关系强(A高)且开盘集中放量(B高)=关系发生在信息量大的开盘环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GK2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _VOL_AUTOCORR,
        "mechanism": "intraday_momentum60_confirmed_by_volume_autocorr",
        "hypothesis": "同GK1，B=日内成交量自相关（同GJ5）。假设：长窗关系强(A高)且成交有规律持续性(B高)=延续，同GJ5。",
        "expected_sign": 1,
    },
    {
        "id": "GK3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _VOL_PROFILE_DIST,
        "mechanism": "intraday_momentum60_confirmed_by_volume_profile_shift",
        "hypothesis": "同GK1，B=日内成交量分布偏离（round_513最强confirming partner，本线最高t单原子t=4.04）。假设同GI2。",
        "expected_sign": 1,
    },
    {
        "id": "GK4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _CATEGORY_VOL,
        "mechanism": "intraday_momentum60_confirmed_by_category_vol",
        "hypothesis": "同GK1，B=同类别板块波动率（同GJ6）。假设同GJ6。",
        "expected_sign": 1,
    },
    # ---- Group D: LAST30_NEXTOPEN_CORR_20 x 3 proven partners (untested atom) ----
    {
        "id": "GL1",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _OPEN30,
        "mechanism": "last30_nextopen_confirmed_by_open30_vol_share",
        "hypothesis": "尾盘-次日隔夜关系首次配对测试。A=尾盘30分钟收益与次日隔夜跳空相关（已按信号时点错位对齐，round_513体检 disc+0.0188/审计-0.0508）；B=开盘30分钟成交占比（本家族最强confirming partner）。假设：尾盘预测次日跳空的关系强(A高)且开盘集中放量(B高)=关系被次日开盘活动确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GL2",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_AUTOCORR,
        "mechanism": "last30_nextopen_confirmed_by_volume_autocorr",
        "hypothesis": "同GL1，B=日内成交量自相关（同GJ5）。假设同GL1。",
        "expected_sign": 1,
    },
    {
        "id": "GL3",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_PROFILE_DIST,
        "mechanism": "last30_nextopen_confirmed_by_volume_profile_shift",
        "hypothesis": "同GL1，B=日内成交量分布偏离（本线最高t单原子）。假设同GL1。",
        "expected_sign": 1,
    },
    # ---- Group E: INTRADAY_MOM_BETA_20 x 2 proven partners (untested atom) ----
    {
        "id": "GM1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _OPEN30,
        "mechanism": "intraday_momentum_beta_confirmed_by_open30_vol_share",
        "hypothesis": "回归斜率版本首次配对测试。A=末30分钟对首30分钟收益的回归斜率（round_513体检 disc-0.0108/审计-0.0551）；B=开盘30分钟成交占比。假设：动量传导斜率大(A高)且开盘集中放量(B高)=传导强度有开盘活动确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GM2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _VOL_AUTOCORR,
        "mechanism": "intraday_momentum_beta_confirmed_by_volume_autocorr",
        "hypothesis": "同GM1，B=日内成交量自相关（同GJ5）。假设同GM1。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
