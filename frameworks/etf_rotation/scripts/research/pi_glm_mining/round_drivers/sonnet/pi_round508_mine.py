#!/usr/bin/env python3
"""Round 508 driver: S2 stage step 6 -- exhaustive completion pass. Across
rounds 505-507, four upside_tail legs (BEST_DAY_60_XVOL,
INTRADAY_MAXBAR_RET_20_XVOL, MAX5_MEAN_20_XVOL, POS_DAY_FRAC_Z_20) were
paired against a growing pool of validated channel atoms (round_053's 7
atomic winners, round_079's 3 single-leg citations, round_018's 4
atom_health citations, and the 3 remaining intraday_volume_profile_1m
atoms discovered useful in round_507). This round fills every remaining
gap in that (leg x partner) matrix for BEST_DAY_20_XVOL,
INTRADAY_MAXBAR_RET_20_XVOL, MAX5_MEAN_20_XVOL and POS_DAY_FRAC_Z_20, plus
completes DOWNSIDE_COSKEW_60 (coskewness_risk, S1 stage) against the 3
newest partners never tried on it -- so that after this round the full
17-partner x 5-leg grid is exhaustively covered at least once via
rank_spread, a clean basis for declaring this pairing avenue closed if
the next rounds also come back empty."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_508"

_ULCER = {"name": "ULCER_20", "source": "downside_risk"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_CLOSE30 = {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_VOL_PROFILE_DIST = {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_TICK_IMB = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_EDGE_CONC = {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"}
_USHAPE = {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"}

base.CANDIDATES = [
    # ---- XA: INTRADAY_MAXBAR_RET_20_XVOL's last untested partner ----
    {
        "id": "XA1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _ULCER,
        "mechanism": "intraday_max_xvol_confirmed_by_ulcer_final",
        "hypothesis": "两腿角色：A=1m日内MAX残差化（round_506 VB8 admitted leg，disc-0.0203/审计-0.0002）；B=溃疡指数（round_079 BM4单腿：disc-0.0415/审计-0.0607/t=0.76/审超+10.7bp）。完成该leg对17-partner池的最后一个组合。假设：日内彩票偏好高(A高)且无慢性失血(B低)=偏好发生在健康推进资产上，延续。",
        "expected_sign": 1,
    },
    # ---- XB: MAX5_MEAN_20_XVOL x 3 intraday_volume_profile_1m atoms not yet tried on this leg ----
    {
        "id": "XB1",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _VOL_ENTROPY,
        "mechanism": "max5_xvol_confirmed_by_volume_entropy",
        "hypothesis": "A=MAX(5)残差化（disc+0.0020/审计+0.0197）；B=日内成交量分布熵（round_024体检单腿：disc+0.0070/审计+0.0229）。假设：稳健版彩票偏好高(A高)且成交分布分散(B高)=偏好伴随不集中的日内结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XB2",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _OPEN30,
        "mechanism": "max5_xvol_confirmed_by_open30_vol_share",
        "hypothesis": "A=同上；B=开盘30分钟成交占比（round_024体检单腿：disc-0.1173/审计-0.0476，本家族发现IC绝对值最大者；round_507 WI2已证明该partner可与BEST_DAY_60_XVOL配对通过全部七道门）。假设：稳健版彩票偏好高(A高)且开盘集中交易(B高)=偏好在开盘后段被快速定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XB3",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _CLOSE30,
        "mechanism": "max5_xvol_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上；B=收盘30分钟成交占比（round_024体检单腿：disc+0.0468/审计-0.0044）。假设：稳健版彩票偏好高(A高)且尾盘集中交易(B高)=偏好在尾盘被知情资金定价，延续。",
        "expected_sign": 1,
    },
    # ---- XC: POS_DAY_FRAC_Z_20 x 7 remaining untested partners ----
    {
        "id": "XC1",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _CHIP_RANGE,
        "mechanism": "pos_day_frac_confirmed_by_chip_concentration",
        "hypothesis": "A=正收益日占比状态切换（disc-0.0139/审计-0.0209）；B=筹码区间宽度（round_079 BM2单腿：disc-0.0574/审计-0.0620/t=0.70/审超+14.6bp）。假设：状态切换(A高)且筹码集中(B高)=切换被锁仓盘固化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XC2",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _DIR_SKEW,
        "mechanism": "pos_day_frac_confirmed_by_bigbar_dir_skew",
        "hypothesis": "A=同上；B=大bar方向偏斜（round_018体检单腿：disc-0.0117/审计+0.0254）。假设：状态切换(A高)且大单方向一致偏斜(B高)=切换伴随方向性大单流，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XC3",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _AUTOCORR,
        "mechanism": "pos_day_frac_confirmed_by_volume_autocorr",
        "hypothesis": "A=同上；B=日内成交量自相关（round_018体检单腿：disc-0.0722/审计-0.0551；round_507 WJ4已证明该partner可与MAX5_MEAN_20_XVOL配对通过全部七道门）。假设：状态切换(A高)且成交有节奏持续性(B高)=切换伴随规律流动性投放，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XC4",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _ULCER,
        "mechanism": "pos_day_frac_confirmed_by_ulcer",
        "hypothesis": "A=同上；B=溃疡指数（round_079 BM4单腿：disc-0.0415/审计-0.0607/t=0.76/审超+10.7bp）。假设：状态切换(A高)且无慢性失血(B低)=切换发生在健康资产上，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XC5",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _VOL_ENTROPY,
        "mechanism": "pos_day_frac_confirmed_by_volume_entropy",
        "hypothesis": "A=同上；B=日内成交量分布熵（round_024体检单腿：disc+0.0070/审计+0.0229）。假设：状态切换(A高)且成交分布分散(B高)=切换伴随不集中日内结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XC6",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _OPEN30,
        "mechanism": "pos_day_frac_confirmed_by_open30_vol_share",
        "hypothesis": "A=同上；B=开盘30分钟成交占比（round_024体检单腿：disc-0.1173/审计-0.0476）。假设：状态切换(A高)且开盘集中交易(B高)=切换在开盘后段被快速定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XC7",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _CLOSE30,
        "mechanism": "pos_day_frac_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上；B=收盘30分钟成交占比（round_024体检单腿：disc+0.0468/审计-0.0044）。假设：状态切换(A高)且尾盘集中交易(B高)=切换在尾盘被知情资金定价，延续。",
        "expected_sign": 1,
    },
    # ---- XD: BEST_DAY_20_XVOL x 11 remaining untested partners (only 6/17 tested so far) ----
    {
        "id": "XD1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _GAP_FILL,
        "mechanism": "max_xvol20_confirmed_by_gap_absorption",
        "hypothesis": "A=20日窗残差化MAX（round_505体检 disc+0.0034/审计-0.0146）；B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：彩票偏好高(A高)且缺口易回补(B高)=定价错误容易被修正，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XD2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _VOL_PROFILE_DIST,
        "mechanism": "max_xvol20_confirmed_by_volume_profile_shift",
        "hypothesis": "A=同上；B=日内成交量分布偏离（round_053门7全过：disc+0.0952/审计+0.0442/t=4.04，本线最高t单原子）。假设：彩票偏好高(A高)且日内成交结构异常(B高)=偏好伴随异常时点结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XD3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _WORST_DAY,
        "mechanism": "max_xvol20_confirmed_by_own_worst_day",
        "hypothesis": "A=同上；B=自身20日最差单日收益（round_053门7全过：disc+0.0635/审计+0.0648/t=2.18/审超+16.2bp）。假设：彩票偏好高(A高)且自身尾部也重(B高)=彩票特征与尾部风险叠加，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XD4",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _TICK_IMB,
        "mechanism": "max_xvol20_confirmed_by_orderflow",
        "hypothesis": "A=同上；B=主买不平衡（round_079 BM6单腿：disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp，偏弱）。假设：彩票偏好高(A高)且买流强(B高)=偏好有主动买盘确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XD5",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _CHIP_RANGE,
        "mechanism": "max_xvol20_locked_by_chip_concentration",
        "hypothesis": "A=同上；B=筹码区间宽度（round_079 BM2单腿：disc-0.0574/审计-0.0620/t=0.70/审超+14.6bp）。假设：彩票偏好高(A高)且筹码集中(B高)=偏好被锁仓盘固化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XD6",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _LOG_AMT,
        "mechanism": "max_xvol20_confirmed_by_high_activity",
        "hypothesis": "A=同上；B=对数成交额（round_079 BM3单腿：disc+0.0661/审计+0.0701/t=2.23/审超+36.8bp，本线历史最强单腿之一）。假设：彩票偏好高(A高)且活跃度高(B高)=偏好发生在流动性充足的环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XD7",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _EDGE_CONC,
        "mechanism": "max_xvol20_confirmed_by_edge_concentration",
        "hypothesis": "A=同上；B=大bar价格边缘集中度（round_053门7全过：disc-0.0971/审计-0.0459/t=2.55/审超+30.7bp）。假设：彩票偏好高(A高)且边缘冲击集中(B高)=偏好伴随激进订单，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XD8",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _USHAPE,
        "mechanism": "max_xvol20_confirmed_by_session_ushape",
        "hypothesis": "A=同上；B=日内成交量U型集中度（round_053门7全过：disc-0.0832/审计-0.0891/t=2.12/审超+33.9bp）。假设：彩票偏好高(A高)且开收盘成交集中(B高)=偏好伴随主力时点操作，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XD9",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _VOL_ENTROPY,
        "mechanism": "max_xvol20_confirmed_by_volume_entropy",
        "hypothesis": "A=同上；B=日内成交量分布熵（round_024体检单腿：disc+0.0070/审计+0.0229）。假设：彩票偏好高(A高)且成交分布分散(B高)=偏好伴随不集中日内结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XD10",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _OPEN30,
        "mechanism": "max_xvol20_confirmed_by_open30_vol_share",
        "hypothesis": "A=同上；B=开盘30分钟成交占比（round_024体检单腿：disc-0.1173/审计-0.0476；round_507 WI2已证明该partner可与BEST_DAY_60_XVOL配对通过全部七道门，本候选测试20日窗版本是否同样成立）。假设：彩票偏好高(A高)且开盘集中交易(B高)=偏好在开盘后段被快速定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XD11",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _CLOSE30,
        "mechanism": "max_xvol20_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上；B=收盘30分钟成交占比（round_024体检单腿：disc+0.0468/审计-0.0044）。假设：彩票偏好高(A高)且尾盘集中交易(B高)=偏好在尾盘被知情资金定价，延续。",
        "expected_sign": 1,
    },
    # ---- XE: DOWNSIDE_COSKEW_60 (S1 stage) x 3 newest partners never tried on it ----
    {
        "id": "XE1",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _VOL_ENTROPY,
        "mechanism": "downside_coskew_confirmed_by_volume_entropy",
        "hypothesis": "A=下行条件化协偏度（round_500体检 disc+0.0319/审计+0.0404，identity通过，round_501-503多轮最高t=1.88）；B=日内成交量分布熵（round_024体检单腿：disc+0.0070/审计+0.0229，此partner此前从未与本atom配对）。假设：系统性崩盘暴露高(A高)且成交分布分散(B高)=暴露伴随不集中日内结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XE2",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _OPEN30,
        "mechanism": "downside_coskew_confirmed_by_open30_vol_share",
        "hypothesis": "A=同上；B=开盘30分钟成交占比（round_024体检单腿：disc-0.1173/审计-0.0476；round_507已证明可与upside_tail两条腿配对通过七道门中的一条）。假设：崩盘暴露高(A高)且开盘集中交易(B高)=暴露在开盘后段被快速定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "XE3",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _CLOSE30,
        "mechanism": "downside_coskew_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上；B=收盘30分钟成交占比（round_024体检单腿：disc+0.0468/审计-0.0044）。假设：崩盘暴露高(A高)且尾盘集中交易(B高)=暴露在尾盘被知情资金定价，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
