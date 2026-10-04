#!/usr/bin/env python3
"""Round 512 driver: S2 stage step 9. round_509-510 both came back zero
(2 consecutive zero pairing rounds after the 3-round admission streak in
506-508); this round opens two families never paired against
upside_tail/coskewness_risk at all: peer_relative_value (round_052:
PEER_RESID_Z_20, PEER_RESID_MOM_20, PEER_OU_HALFLIFE_20 -- Gatev-
Goetzmann-Rouwenhorst 2006 pairs / Avellaneda-Lee 2010) and
cross_dependence_1m (round_052: GRANGER_OUT/IN_DEGREE_20, NET_SPILLOVER_20,
DEP_DRIFT_20 -- Billio-Getmansky-Lo-Pelizzon 2012 / Diebold-Yilmaz 2014),
plus category_state atoms beyond CATEGORY_VOL_20 (CATEGORY_DISPERSION_20 --
itself a shelf16 atom that passed gate 7 standalone per round_071's
retrospective, audit excess +23.3bp; CATEGORY_BREADTH_MA20;
CATEGORY_MOM_60). If this round also comes back zero, that is 3
consecutive zero rounds (509, 510, 512 -- round_511 was a data-outage
block with no evaluation, doesn't count) and triggers the stage
retrospective/exhaustion writeup."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_512"

_PEER_RESID_Z = {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"}
_PEER_RESID_MOM = {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"}
_PEER_OU = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_GRANGER_OUT = {"name": "GRANGER_OUT_DEGREE_20", "source": "cross_dependence_1m"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_NET_SPILL = {"name": "NET_SPILLOVER_20", "source": "cross_dependence_1m"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_CAT_DISP = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_CAT_BREADTH = {"name": "CATEGORY_BREADTH_MA20", "source": "category_state"}
_CAT_MOM60 = {"name": "CATEGORY_MOM_60", "source": "category_state"}

base.CANDIDATES = [
    # ---- Group A: BEST_DAY_60_XVOL x 7 new atoms ----
    {
        "id": "XPA1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _PEER_RESID_Z,
        "mechanism": "max_xvol60_confirmed_by_peer_resid_z",
        "hypothesis": "两腿角色：A=60日波动率残差化MAX（round_507 WI2 admitted leg，disc-0.0135/审计-0.0120）；B=同伴篓子残差z分数（round_052体检单腿，Gatev-Goetzmann-Rouwenhorst 2006/Avellaneda-Lee 2010：disc-0.036/审计-0.022，peer_relative_value家族从未与upside_tail配对）。假设：彩票偏好高(A高)且相对同伴篓子偏离大(B高)=偏好伴随统计套利式相对错定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPA2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _PEER_OU,
        "mechanism": "max_xvol60_confirmed_by_peer_ou_halflife",
        "hypothesis": "两腿角色：A=同上；B=同伴篓子OU均值回复半衰期（round_052体检单腿：disc+0.013/审计+0.035）。假设：彩票偏好高(A高)且回复速度慢(B高，偏离难修正)=偏好定价错误持续更久，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPA3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _GRANGER_OUT,
        "mechanism": "max_xvol60_confirmed_by_granger_out_degree",
        "hypothesis": "两腿角色：A=同上；B=Granger网络出度（round_052体检单腿，Billio-Getmansky-Lo-Pelizzon 2012：disc-0.022/审计-0.039，cross_dependence_1m家族从未与upside_tail配对）。假设：彩票偏好高(A高)且对外溢出弱(B低，即独立性强)=偏好定价错误不易被跨资产套利消化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPA4",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _NET_SPILL,
        "mechanism": "max_xvol60_confirmed_by_net_spillover",
        "hypothesis": "两腿角色：A=同上；B=净溢出（round_052体检单腿，Diebold-Yilmaz 2014：disc+0.048/审计-0.016，本cross_dependence_1m家族发现IC最高的原子）。假设：彩票偏好高(A高)且净溢出为正(B高，即输出信息多于接收)=偏好由领先性资产驱动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPA5",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _CAT_DISP,
        "mechanism": "max_xvol60_confirmed_by_category_dispersion",
        "hypothesis": "两腿角色：A=同上；B=类别内离散度（round_071复盘：货架16因子中门7独立通过的3个之一，审计超额+23.3bp，是本线迄今唯一已知单独可通过门7的候选，此前从未与upside_tail配对）。假设：彩票偏好高(A高)且类别内分化大(B高)=偏好在板块内部离散、有相对赢家输家的环境中更易兑现，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPA6",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _CAT_BREADTH,
        "mechanism": "max_xvol60_confirmed_by_category_breadth",
        "hypothesis": "两腿角色：A=同上；B=类别广度均值（category_state家族，本线尚无独立单腿数字记录）。假设：彩票偏好高(A高)且所属类别参与广度低(B低，即少数票领涨)=偏好在窄幅领涨环境中被放大，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPA7",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _CAT_MOM60,
        "mechanism": "max_xvol60_confirmed_by_category_mom60",
        "hypothesis": "两腿角色：A=同上；B=类别60日动量（category_state家族，本线尚无独立单腿数字记录）。假设：彩票偏好高(A高)且所属类别中期动量强(B高)=偏好伴随板块层面的趋势性支撑，延续。",
        "expected_sign": 1,
    },
    # ---- Group B: MAX5_MEAN_20_XVOL x 4 new atoms ----
    {
        "id": "XPB1",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _PEER_RESID_Z,
        "mechanism": "max5_xvol_confirmed_by_peer_resid_z",
        "hypothesis": "同XPA1，A=MAX(5)残差化（round_508 XB2 admitted leg，disc+0.0020/审计+0.0197）。假设同XPA1。",
        "expected_sign": 1,
    },
    {
        "id": "XPB2",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _PEER_OU,
        "mechanism": "max5_xvol_confirmed_by_peer_ou_halflife",
        "hypothesis": "同XPA2，A=MAX(5)残差化。假设同XPA2。",
        "expected_sign": 1,
    },
    {
        "id": "XPB3",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _GRANGER_OUT,
        "mechanism": "max5_xvol_confirmed_by_granger_out_degree",
        "hypothesis": "同XPA3，A=MAX(5)残差化。假设同XPA3。",
        "expected_sign": 1,
    },
    {
        "id": "XPB4",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _NET_SPILL,
        "mechanism": "max5_xvol_confirmed_by_net_spillover",
        "hypothesis": "同XPA4，A=MAX(5)残差化。假设同XPA4。",
        "expected_sign": 1,
    },
    # ---- Group C: BEST_DAY_20_XVOL x 4 new atoms ----
    {
        "id": "XPC1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _PEER_RESID_MOM,
        "mechanism": "max_xvol20_confirmed_by_peer_resid_mom",
        "hypothesis": "两腿角色：A=20日窗残差化MAX（round_508 XD8 admitted leg族群，disc+0.0034/审计-0.0146）；B=同伴篓子残差动量（round_052体检单腿：disc-0.019/审计+0.007）。假设：彩票偏好高(A高)且相对偏离正在扩大(B高)=偏好伴随相对错定价加速，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPC2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _GRANGER_IN,
        "mechanism": "max_xvol20_confirmed_by_granger_in_degree",
        "hypothesis": "两腿角色：A=同上；B=Granger网络入度（round_052体检单腿：disc-0.079/审计-0.044，本cross_dependence_1m家族相关性最高原子）。假设：彩票偏好高(A高)且接受外部溢出弱(B低)=偏好独立于池内其他资产，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPC3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _DEP_DRIFT,
        "mechanism": "max_xvol20_confirmed_by_dep_drift",
        "hypothesis": "两腿角色：A=同上；B=依赖度漂移（round_052体检单腿：disc-0.018/审计-0.015）。假设：彩票偏好高(A高)且与池依赖度正在下降(B低，独立性增强)=偏好伴随脱离系统性联动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPC4",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _CAT_DISP,
        "mechanism": "max_xvol20_confirmed_by_category_dispersion",
        "hypothesis": "同XPA5，A=20日窗残差化MAX。假设同XPA5。",
        "expected_sign": 1,
    },
    # ---- Group D: INTRADAY_MAXBAR_RET_20_XVOL x 3 new atoms ----
    {
        "id": "XPD1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _PEER_RESID_Z,
        "mechanism": "intraday_max_xvol_confirmed_by_peer_resid_z",
        "hypothesis": "同XPA1，A=1m日内MAX残差化（round_506 VB8 admitted leg，disc-0.0203/审计-0.0002）。假设同XPA1。",
        "expected_sign": 1,
    },
    {
        "id": "XPD2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _GRANGER_OUT,
        "mechanism": "intraday_max_xvol_confirmed_by_granger_out_degree",
        "hypothesis": "同XPA3，A=1m日内MAX残差化，且A/B同为1m路径构造。假设同XPA3。",
        "expected_sign": 1,
    },
    {
        "id": "XPD3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _CAT_DISP,
        "mechanism": "intraday_max_xvol_confirmed_by_category_dispersion",
        "hypothesis": "同XPA5，A=1m日内MAX残差化。假设同XPA5。",
        "expected_sign": 1,
    },
    # ---- Group E: POS_DAY_FRAC_Z_20 x 3 new atoms ----
    {
        "id": "XPE1",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _PEER_OU,
        "mechanism": "pos_day_frac_confirmed_by_peer_ou_halflife",
        "hypothesis": "两腿角色：A=正收益日占比状态切换（disc-0.0139/审计-0.0209）；B=同伴篓子OU半衰期（同XPA2，disc+0.013/审计+0.035）。假设：状态切换(A高)且回复速度慢(B高)=切换定价错误持续更久，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPE2",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _NET_SPILL,
        "mechanism": "pos_day_frac_confirmed_by_net_spillover",
        "hypothesis": "两腿角色：A=同上；B=净溢出（同XPA4，disc+0.048/审计-0.016）。假设：状态切换(A高)且净溢出为正(B高)=切换由领先性资产驱动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPE3",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _CAT_BREADTH,
        "mechanism": "pos_day_frac_confirmed_by_category_breadth",
        "hypothesis": "两腿角色：A=同上；B=类别广度均值（同XPA6，本线尚无独立单腿数字记录）。假设：状态切换(A高)且所属类别参与广度低(B低)=切换在窄幅领涨环境中被放大，延续。",
        "expected_sign": 1,
    },
    # ---- Group F: DOWNSIDE_COSKEW_60 x 3 new atoms ----
    {
        "id": "XPF1",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _GRANGER_OUT,
        "mechanism": "downside_coskew_confirmed_by_granger_out_degree",
        "hypothesis": "两腿角色：A=下行条件化协偏度（round_500体检 disc+0.0319/审计+0.0404，identity通过）；B=Granger网络出度（同XPA3，disc-0.022/审计-0.039）。假设：崩盘暴露高(A高)且对外溢出弱(B低)=系统性暴露不易被跨资产套利，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPF2",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _NET_SPILL,
        "mechanism": "downside_coskew_confirmed_by_net_spillover",
        "hypothesis": "两腿角色：A=同上；B=净溢出（同XPA4，disc+0.048/审计-0.016）。假设：崩盘暴露高(A高)且净溢出为正(B高)=系统性风险由领先性资产传导，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XPF3",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _PEER_RESID_Z,
        "mechanism": "downside_coskew_confirmed_by_peer_resid_z",
        "hypothesis": "两腿角色：A=同上；B=同伴篓子残差z（同XPA1，disc-0.036/审计-0.022）。假设：崩盘暴露高(A高)且相对同伴篓子偏离大(B高)=系统性风险叠加统计套利式相对错定价，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
