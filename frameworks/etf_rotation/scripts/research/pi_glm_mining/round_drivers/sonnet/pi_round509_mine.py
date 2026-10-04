#!/usr/bin/env python3
"""Round 509 driver: S2 stage step 7. The 17-partner pool used in
rounds 505-508 is now exhaustively covered; this round expands the
partner pool with atoms pulled from OTHER admitted combos across the
line's full history that were never tried against upside_tail/coskewness
(RESILIENCY_20 -- the single most recurring leg across W3/Z1/AI1/AL2/
AL3/AN2/AN6 -- SHARE_RET_CORR_20, LBAR_RET_CONTRIB_20, SIGN_ACF1_5), plus
rank_interaction retries of round_508's three closest misses (XD10 t=3.06
missed only the audit-bp floor; XD7 t=2.78 missed identity; XE2 t=2.20
missed the audit-bp floor)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_509"

_RESIL = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_SHARE_CORR = {"name": "SHARE_RET_CORR_20", "source": "fund_flow"}
_LBAR_RC = {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"}
_SIGN_ACF = {"name": "SIGN_ACF1_5", "source": "serial_dependence"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_EDGE_CONC = {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"}

base.CANDIDATES = [
    # ---- Group 1: rank_interaction retry of round_508's 3 closest misses ----
    {
        "id": "YR1",
        "operator": "rank_interaction",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _OPEN30,
        "mechanism": "max_xvol20_interaction_open30_vol_share",
        "hypothesis": "round_508 XD10（同一对atom的rank_spread）t=3.06/审超+4.3bp仅因未过5bp审计地板被拒（其余全过，identity通过，3/3年度）。本候选改用rank_interaction，检验交互项组合方式是否能把审计超额推过5bp。",
        "expected_sign": 1,
    },
    {
        "id": "YR2",
        "operator": "rank_interaction",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _EDGE_CONC,
        "mechanism": "max_xvol20_interaction_edge_concentration",
        "hypothesis": "round_508 XD7（rank_spread）t=2.78/审超+26.6bp仅因identity_gate未过被拒。本候选改用rank_interaction，检验交互项是否改变LOSO稳健性。",
        "expected_sign": 1,
    },
    {
        "id": "YR3",
        "operator": "rank_interaction",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _OPEN30,
        "mechanism": "downside_coskew_interaction_open30_vol_share",
        "hypothesis": "round_508 XE2（rank_spread）t=2.20/审超+0.6bp仅因未过5bp审计地板被拒（identity通过，3/3年度）。本候选改用rank_interaction，检验能否推过地板。",
        "expected_sign": 1,
    },
    # ---- Group 2-5: 4 upside_tail legs x RESILIENCY_20 (most recurring leg in line history: W3/Z1/AI1/AL2/AL3/AN2/AN6) ----
    {
        "id": "YS1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _RESIL,
        "mechanism": "max_xvol60_confirmed_by_resiliency",
        "hypothesis": "两腿角色：A=60日波动率残差化MAX（round_507 WI2 admitted leg，disc-0.0135/审计-0.0120）；B=1m冲击回复力（round_049体检单腿：disc-0.114/审计-0.041，Kyle-Obizhaeva 2016代理，是全线admitted组合中出现频次最高的原子——W3/r043、Z1/r046、AI1/r060、AL2/AL3/r063、AN2/AN6/r065共7次）。假设：彩票偏好高(A高)且流动性回复力弱(B低，冲击难消化)=偏好在脆弱流动性环境下更易被定价错误，延续。",
        "expected_sign": 1,
    },
    {
        "id": "YS2",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _RESIL,
        "mechanism": "max5_xvol_confirmed_by_resiliency",
        "hypothesis": "同YS1，A=MAX(5)残差化（round_508 XB2 admitted leg，disc+0.0020/审计+0.0197）；B=回复力（同上）。假设同YS1。",
        "expected_sign": 1,
    },
    {
        "id": "YS3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _RESIL,
        "mechanism": "max_xvol20_confirmed_by_resiliency",
        "hypothesis": "同YS1，A=20日窗残差化MAX（round_508 XD8 admitted leg，disc+0.0034/审计-0.0146）；B=回复力（同上）。假设同YS1。",
        "expected_sign": 1,
    },
    {
        "id": "YS4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _RESIL,
        "mechanism": "intraday_max_xvol_confirmed_by_resiliency",
        "hypothesis": "同YS1，A=1m日内MAX残差化（round_506 VB8 admitted leg，disc-0.0203/审计-0.0002）；B=回复力（同上）。假设同YS1，且A/B同为1m路径构造，机制上更贴近（同为流动性/冲击消化视角）。",
        "expected_sign": 1,
    },
    {
        "id": "YS5",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _RESIL,
        "mechanism": "pos_day_frac_confirmed_by_resiliency",
        "hypothesis": "同YS1，A=正收益日占比状态切换（disc-0.0139/审计-0.0209）；B=回复力（同上）。假设：状态切换(A高)且流动性回复力弱(B低)=切换发生在脆弱流动性环境，延续。",
        "expected_sign": 1,
    },
    # ---- Group 6-9: 4 legs x SHARE_RET_CORR_20 (second most recurring leg: W1/W3/Z6/AL4/AN1) ----
    {
        "id": "YT1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _SHARE_CORR,
        "mechanism": "max_xvol60_confirmed_by_share_ret_corr",
        "hypothesis": "两腿角色：A=同YS1；B=份额变化与收益相关性（round_034体检单腿：disc+0.0137/审计+0.0320，出现在W1/W3/Z6/AL4/AN1共5个admitted组合）。假设：彩票偏好高(A高)且份额-收益同向性强(B高，申购追涨)=偏好伴随资金追涨行为，延续。",
        "expected_sign": 1,
    },
    {
        "id": "YT2",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _SHARE_CORR,
        "mechanism": "max5_xvol_confirmed_by_share_ret_corr",
        "hypothesis": "同YT1，A=MAX(5)残差化。假设同YT1。",
        "expected_sign": 1,
    },
    {
        "id": "YT3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _SHARE_CORR,
        "mechanism": "max_xvol20_confirmed_by_share_ret_corr",
        "hypothesis": "同YT1，A=20日窗残差化MAX。假设同YT1。",
        "expected_sign": 1,
    },
    {
        "id": "YT4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _SHARE_CORR,
        "mechanism": "intraday_max_xvol_confirmed_by_share_ret_corr",
        "hypothesis": "同YT1，A=1m日内MAX残差化。假设同YT1。",
        "expected_sign": 1,
    },
    # ---- Group 10-13: 4 legs x LBAR_RET_CONTRIB_20 (largebar footprint, never paired with upside_tail) ----
    {
        "id": "YU1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _LBAR_RC,
        "mechanism": "max_xvol60_confirmed_by_bigbar_ret_contrib",
        "hypothesis": "两腿角色：A=同YS1；B=大bar收益承载份额（round_079单腿：disc-0.0164/审计-0.0111/t=0.55/审超+6.2bp，出现在BJ3/BJ6两个admitted组合的一条腿，largebar_footprint_1m家族从未与upside_tail配对）。假设：彩票偏好高(A高)且收益由大bar承载(B高)=偏好由大单驱动而非渐进积累，延续。",
        "expected_sign": 1,
    },
    {
        "id": "YU2",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _LBAR_RC,
        "mechanism": "max5_xvol_confirmed_by_bigbar_ret_contrib",
        "hypothesis": "同YU1，A=MAX(5)残差化。假设同YU1。",
        "expected_sign": 1,
    },
    {
        "id": "YU3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _LBAR_RC,
        "mechanism": "max_xvol20_confirmed_by_bigbar_ret_contrib",
        "hypothesis": "同YU1，A=20日窗残差化MAX。假设同YU1。",
        "expected_sign": 1,
    },
    {
        "id": "YU4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _LBAR_RC,
        "mechanism": "intraday_max_xvol_confirmed_by_bigbar_ret_contrib",
        "hypothesis": "同YU1，A=1m日内MAX残差化，且A/B同为1m路径构造。假设同YU1。",
        "expected_sign": 1,
    },
    # ---- Group 14-17: 4 legs x SIGN_ACF1_5 (serial_dependence, appears in AF4/AI6/AL5) ----
    {
        "id": "YV1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _SIGN_ACF,
        "mechanism": "max_xvol60_confirmed_by_sign_acf",
        "hypothesis": "两腿角色：A=同YS1；B=5日收益自相关符号（round_079单腿：disc-0.0211/审计+0.0070/t=0.12/审超+3.9bp，出现在AF4/AI6/AL5三个admitted组合）。假设：彩票偏好高(A高)且短期动量确认(B高)=偏好由趋势性推进承载，延续。",
        "expected_sign": 1,
    },
    {
        "id": "YV2",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _SIGN_ACF,
        "mechanism": "max5_xvol_confirmed_by_sign_acf",
        "hypothesis": "同YV1，A=MAX(5)残差化。假设同YV1。",
        "expected_sign": 1,
    },
    {
        "id": "YV3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _SIGN_ACF,
        "mechanism": "max_xvol20_confirmed_by_sign_acf",
        "hypothesis": "同YV1，A=20日窗残差化MAX。假设同YV1。",
        "expected_sign": 1,
    },
    {
        "id": "YV4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _SIGN_ACF,
        "mechanism": "intraday_max_xvol_confirmed_by_sign_acf",
        "hypothesis": "同YV1，A=1m日内MAX残差化。假设同YV1。",
        "expected_sign": 1,
    },
    # ---- Group 18: DOWNSIDE_COSKEW_60 x new partners ----
    {
        "id": "YW1",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _RESIL,
        "mechanism": "downside_coskew_confirmed_by_resiliency",
        "hypothesis": "两腿角色：A=下行条件化协偏度（round_500体检 disc+0.0319/审计+0.0404，identity通过）；B=回复力（round_049体检：disc-0.114/审计-0.041，本线admitted组合中出现频次最高的原子）。假设：崩盘暴露高(A高)且流动性回复力弱(B低)=暴露发生在脆弱流动性环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "YW2",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _SHARE_CORR,
        "mechanism": "downside_coskew_confirmed_by_share_ret_corr",
        "hypothesis": "两腿角色：A=同上；B=份额变化与收益相关性（round_034体检：disc+0.0137/审计+0.0320）。假设：崩盘暴露高(A高)且份额-收益同向性强(B高)=暴露伴随资金追涨行为，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
