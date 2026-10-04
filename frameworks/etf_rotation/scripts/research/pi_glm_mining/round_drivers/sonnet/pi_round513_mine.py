#!/usr/bin/env python3
"""Round 513 driver: S3 stage step 1 -- intraday_momentum_30m family (Gao,
Han, Li & Zhou 2018 market intraday momentum), the first family to use
the previously-untapped 30m bar frequency (round_513 GAP_SCAN_2). 5
atomic candidates (all non-shadow per atom_health, max|shelf corr| <=
0.22) plus a first directed-pairing batch against the strongest validated
channel atoms from the S2 stage's proven day-part/volume-distribution
channel (VOL_SPIKE_FREQ_20, OPEN30_VOL_SHARE_20, VOL_AUTOCORR_20,
VOL_USHAPE_20 -- all 4 confirmed upside_tail admitted-candidate partners)
plus round_053's 7 atomic winners, run together per the controller's
15-30-per-round batching rule."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_513"

_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_VOL_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_VOL_USHAPE = {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_BIGBAR_EDGE_CONC = {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_VOL_PROFILE_DIST = {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}

base.CANDIDATES = [
    # ---- 5 atomic: new intraday_momentum_30m atoms ----
    {
        "id": "GH1",
        "operator": "atomic",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "mechanism": "intraday_momentum_corr_20",
        "hypothesis": "Gao-Han-Li-Zhou 2018 日内动量：首个30分钟收益与最后30分钟收益的20日滚动相关系数。体检：disc-0.0131/579天/审计-0.0562，max|corr|=0.21（vs market_sensitivity货架因子），非shadow。假设：相关性越强(A高)=早盘定调能力越强越稳定，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GH2",
        "operator": "atomic",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "mechanism": "intraday_momentum_corr_60",
        "hypothesis": "同GH1，60日窗。体检：disc-0.0146/579天/审计+0.0076，max|corr|=0.22（vs serial_dependence:VAR_RATIO_20_120），非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "GH3",
        "operator": "atomic",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "mechanism": "intraday_momentum_beta_20",
        "hypothesis": "同一关系的回归斜率版本（非相关系数）。体检：disc-0.0108/579天/审计-0.0551，max|corr|=0.19，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "GH4",
        "operator": "atomic",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "mechanism": "overnight_first30_corr_20",
        "hypothesis": "隔夜跳空与开盘30分钟收益的20日滚动相关（同日）。体检：disc+0.0452/579天/审计+0.0789，方向一致，是本家族发现期最强原子，max|corr|=0.18（vs return_tail_shape货架因子），非shadow。假设：隔夜方向被开盘延续确认得越稳定(A高)=价格发现效率越低越可预测，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GH5",
        "operator": "atomic",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "mechanism": "last30_nextopen_corr_20",
        "hypothesis": "前一日尾盘30分钟收益与次日隔夜跳空的20日滚动相关（已按信号时点错位对齐，见provider docstring避免未来泄漏）。体检：disc+0.0188/579天/审计-0.0508，max|corr|=0.15，非shadow。",
        "expected_sign": 1,
    },
    # ---- pairing: OVERNIGHT_FIRST30_CORR_20 (strongest atom) x proven S2 channel + round_053 pool ----
    {
        "id": "GHP1",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_SPIKE,
        "mechanism": "overnight_first30_confirmed_by_volume_spike_freq",
        "hypothesis": "两腿角色：A=隔夜-开盘延续相关性（本家族最强，disc+0.0452/审计+0.0789）；B=成交量脉冲频率（round_506已证明是本线S2阶段最有效confirming partner之一，disc+0.0661/审计+0.0460）。假设：延续性稳定(A高)且脉冲放量频繁(B高)=价格发现效率低且有交易活动确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GHP2",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _OPEN30,
        "mechanism": "overnight_first30_confirmed_by_open30_vol_share",
        "hypothesis": "两腿角色：A=同上；B=开盘30分钟成交占比（round_507/508已证明是本线S2阶段最强confirming partner，disc-0.1173/审计-0.0476）。假设：延续性稳定(A高)且开盘集中放量(B高)=开盘定价信息量大，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GHP3",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_AUTOCORR,
        "mechanism": "overnight_first30_confirmed_by_volume_autocorr",
        "hypothesis": "两腿角色：A=同上；B=日内成交量自相关（round_507已证明confirming partner，disc-0.0722/审计-0.0551）。假设：延续性稳定(A高)且成交有规律持续性(B高)=延续伴随有节奏的流动性投放，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GHP4",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_USHAPE,
        "mechanism": "overnight_first30_confirmed_by_session_ushape",
        "hypothesis": "两腿角色：A=同上；B=日内成交量U型集中度（round_508已证明confirming partner，disc-0.0832/审计-0.0891/t=2.12/审超+6.8bp）。假设：延续性稳定(A高)且开收盘成交集中(B高)=延续伴随主力时点操作，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GHP5",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "overnight_first30_confirmed_by_bigbar_vol_share",
        "hypothesis": "两腿角色：A=同上；B=大bar成交量占比（round_053门7全过：disc+0.0832/审计+0.0548/t=2.92/审超+41.6bp）。假设：延续性稳定(A高)且大单流入活跃(B高)=延续被真实资金承接，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GHP6",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _BIGBAR_EDGE_CONC,
        "mechanism": "overnight_first30_confirmed_by_edge_concentration",
        "hypothesis": "两腿角色：A=同上；B=大bar价格边缘集中度（round_053门7全过：disc-0.0971/审计-0.0459/t=2.55/审超+30.7bp）。假设：延续性稳定(A高)且边缘冲击集中(B高)=延续伴随激进订单，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GHP7",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CATEGORY_VOL,
        "mechanism": "overnight_first30_confirmed_by_category_vol",
        "hypothesis": "两腿角色：A=同上；B=同类别板块波动率（round_053门7全过：disc-0.0711/审计-0.0653/t=2.42/审超+19.0bp）。假设：延续性稳定(A高)且所属板块高波动(B高)=延续来自板块层面共振，延续。",
        "expected_sign": 1,
    },
    # ---- pairing: INTRADAY_MOM_CORR_20 x proven channel (second-strongest atom) ----
    {
        "id": "GHP8",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_SPIKE,
        "mechanism": "intraday_momentum_confirmed_by_volume_spike_freq",
        "hypothesis": "两腿角色：A=首末30分钟收益相关性（disc-0.0131/审计-0.0562）；B=成交量脉冲频率（同GHP1）。假设：日内动量关系强(A高)且脉冲放量频繁(B高)=动量关系有交易活动确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GHP9",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _OPEN30,
        "mechanism": "intraday_momentum_confirmed_by_open30_vol_share",
        "hypothesis": "两腿角色：A=同上；B=开盘30分钟成交占比（同GHP2）。假设：日内动量关系强(A高)且开盘集中放量(B高)=动量关系发生在信息量大的开盘环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GHP10",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _GAP_FILL,
        "mechanism": "intraday_momentum_confirmed_by_gap_absorption",
        "hypothesis": "两腿角色：A=同上；B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：日内动量关系强(A高)且缺口易回补(B高)=延续性资产也有流动性缓冲，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GHP11",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_PROFILE_DIST,
        "mechanism": "intraday_momentum_confirmed_by_volume_profile_shift",
        "hypothesis": "两腿角色：A=同上；B=日内成交量分布偏离（round_053门7全过：disc+0.0952/审计+0.0442/t=4.04，本线最高t单原子）。假设：日内动量关系强(A高)且日内成交结构异常(B高)=关系伴随异常时点结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GHP12",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _WORST_DAY,
        "mechanism": "intraday_momentum_confirmed_by_own_worst_day",
        "hypothesis": "两腿角色：A=同上；B=自身20日最差单日收益（round_053门7全过：disc+0.0635/审计+0.0648/t=2.18/审超+16.2bp）。假设：日内动量关系强(A高)且自身尾部也重(B高)=关系与尾部风险叠加，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
