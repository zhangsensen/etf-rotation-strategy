#!/usr/bin/env python3
"""Round 507 driver: S2 stage step 5 — exploit the round_506 discovery
that VOL_SPIKE_FREQ_20 (intraday_volume_profile_1m) is a real confirming
partner for volatility-residualized upside_tail atoms (VA3, VB8 both
admitted, both paired against exactly this atom). This round: (a) pair
the two untested XVOL/raw legs against VOL_SPIKE_FREQ_20 directly
(MAX5_MEAN_20_XVOL, POS_DAY_FRAC_Z_20); (b) test whether the raw
(non-residualized, shadow-flagged-as-standalone) upside_tail atoms also
confirm against VOL_SPIKE_FREQ_20 as a spread leg -- redundancy is
evaluated on the combined spread signal, not the raw atom in isolation,
so this is a genuinely different test from round_504's atomic rejection;
(c) broaden to the rest of the intraday_volume_profile_1m family
(VOL_ENTROPY_20, OPEN30_VOL_SHARE_20, CLOSE30_VOL_SHARE_20) against the
two admitted legs, to see if the whole family shares this property or if
VOL_SPIKE_FREQ_20 is specifically the mechanism; (d) round out partner
coverage for MAX5_MEAN_20_XVOL and POS_DAY_FRAC_Z_20 with the remaining
validated-atom pool."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_507"

base.CANDIDATES = [
    # ---- Group G: the two untested legs directly against VOL_SPIKE_FREQ_20 ----
    {
        "id": "WG1",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "max5_xvol_confirmed_by_volume_spike_freq",
        "hypothesis": "round_506 发现：VOL_SPIKE_FREQ_20 是两条已入选候选（VA3=BEST_DAY_60_XVOL、VB8=INTRADAY_MAXBAR_RET_20_XVOL）共同的确认partner，t分别2.01/2.10。本候选检验同一partner是否对第三条腿（MAX(5)残差化，disc+0.0020/审计+0.0197）同样有效。B单腿：round_018体检 disc+0.0661/579天/审计+0.0460。假设：稳健版彩票偏好(A高)且脉冲式放量频繁(B高)=偏好伴随间歇冲击型交易，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WG2",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "pos_day_frac_confirmed_by_volume_spike_freq",
        "hypothesis": "同WG1目的，测试VOL_SPIKE_FREQ_20是否对第四条腿（正收益日占比状态切换，disc-0.0139/审计-0.0209）同样有效。假设：状态切换(A高)且脉冲放量频繁(B高)=切换有交易活动确认，延续。",
        "expected_sign": 1,
    },
    # ---- Group H: raw (non-residualized) upside_tail atoms x VOL_SPIKE_FREQ_20 as a SPREAD leg
    #      (round_504 rejected these atomically on redundancy vs REALIZED_VOL_60; the spread's
    #      combined rank signal is a different object and was never tested against dedup) ----
    {
        "id": "WH1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20", "source": "upside_tail"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "raw_max_best_day_20_confirmed_by_volume_spike_freq",
        "hypothesis": "round_504体检：BEST_DAY_20原子disc-0.0941/审计-0.0736被判shadow=0.72（vs REALIZED_VOL_60货架因子），未作为atomic候选提交。此处作为rank_spread的一条腿，与已证实的确认partner VOL_SPIKE_FREQ_20（disc+0.0661/审计+0.0460）配对，检验组合后的排名信号是否仍与该货架因子冗余，还是能像VA3/VB8一样通过冗余门。",
        "expected_sign": 1,
    },
    {
        "id": "WH2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60", "source": "upside_tail"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "raw_max_best_day_60_confirmed_by_volume_spike_freq",
        "hypothesis": "同WH1，60日窗原始（未残差化）MAX。round_504体检：disc-0.1143/审计-0.0767，shadow=0.84（本线最高相关）。检验与VOL_SPIKE_FREQ_20配对后是否仍冗余。",
        "expected_sign": 1,
    },
    {
        "id": "WH3",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20", "source": "upside_tail"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "raw_max5_mean_confirmed_by_volume_spike_freq",
        "hypothesis": "同WH1，原始MAX(5)。round_504体检：disc-0.0929/审计-0.0544，shadow=0.74。检验配对后是否仍冗余。",
        "expected_sign": 1,
    },
    {
        "id": "WH4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20", "source": "upside_tail"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "raw_intraday_maxbar_confirmed_by_volume_spike_freq",
        "hypothesis": "同WH1，原始1m日内MAX代理。round_504体检：disc-0.0860/审计-0.0611，shadow=0.75。检验配对后是否仍冗余。",
        "expected_sign": 1,
    },
    # ---- Group I: broaden to rest of intraday_volume_profile_1m family x the two admitted legs ----
    {
        "id": "WI1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "max_xvol60_confirmed_by_volume_entropy",
        "hypothesis": "两腿角色：A=60日波动率残差化MAX（round_506 VA3 admitted leg，disc-0.0135/审计-0.0120）；B=日内成交量分布熵（round_024体检单腿：disc+0.0070/审计+0.0229，同家族但尚未与该腿配对，topk数字未见记录）。假设：彩票偏好高(A高)且日内成交分布不确定性高(B高)=偏好伴随分散、不集中的成交结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WI2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "max_xvol60_confirmed_by_open30_vol_share",
        "hypothesis": "两腿角色：A=同上；B=开盘30分钟成交占比（round_024体检单腿：disc-0.1173/审计-0.0476，本家族发现IC绝对值最大者，topk数字未见记录）。假设：彩票偏好高(A高)且开盘集中交易(B高)=偏好在开盘竞价后段被快速定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WI3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "max_xvol60_confirmed_by_close30_vol_share",
        "hypothesis": "两腿角色：A=同上；B=收盘30分钟成交占比（round_024体检单腿：disc+0.0468/审计-0.0044，topk数字未见记录）。假设：彩票偏好高(A高)且尾盘集中交易(B高)=偏好在尾盘被知情资金定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WI4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "intraday_max_xvol_confirmed_by_volume_entropy",
        "hypothesis": "两腿角色：A=1m日内MAX残差化（round_506 VB8 admitted leg，disc-0.0203/审计-0.0002）；B=日内成交量分布熵（同WI1，disc+0.0070/审计+0.0229）。假设：日内彩票偏好高(A高)且成交分布分散(B高)=偏好伴随不集中的日内结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WI5",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "intraday_max_xvol_confirmed_by_open30_vol_share",
        "hypothesis": "两腿角色：A=同上；B=开盘30分钟成交占比（同WI2，disc-0.1173/审计-0.0476）。假设：日内彩票偏好高(A高)且开盘集中交易(B高)=偏好在开盘后段被快速定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WI6",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "intraday_max_xvol_confirmed_by_close30_vol_share",
        "hypothesis": "两腿角色：A=同上；B=收盘30分钟成交占比（同WI3，disc+0.0468/审计-0.0044）。假设：日内彩票偏好高(A高)且尾盘集中交易(B高)=偏好在尾盘被知情资金定价，延续。",
        "expected_sign": 1,
    },
    # ---- Group J: MAX5_MEAN_20_XVOL x remaining validated partners ----
    {
        "id": "WJ1",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "mechanism": "max5_xvol_confirmed_by_edge_concentration",
        "hypothesis": "两腿角色：A=MAX(5)残差化（disc+0.0020/审计+0.0197）；B=大bar价格边缘集中度（round_053门7全过：disc-0.0971/审计-0.0459/t=2.55/审超+30.7bp）。假设：稳健版彩票偏好高(A高)且边缘冲击集中(B高)=偏好伴随激进订单，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WJ2",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "max5_xvol_confirmed_by_session_ushape",
        "hypothesis": "两腿角色：A=同上；B=日内成交量U型集中度（round_053门7全过：disc-0.0832/审计-0.0891/t=2.12/审超+33.9bp）。假设：稳健版彩票偏好高(A高)且开收盘成交集中(B高)=偏好伴随主力时点操作，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WJ3",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "mechanism": "max5_xvol_confirmed_by_bigbar_dir_skew",
        "hypothesis": "两腿角色：A=同上；B=大bar方向偏斜（round_018体检单腿：disc-0.0117/579天/审计+0.0254）。假设：稳健版彩票偏好高(A高)且大单方向一致偏斜(B高)=偏好伴随方向性大单流，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WJ4",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "max5_xvol_confirmed_by_volume_autocorr",
        "hypothesis": "两腿角色：A=同上；B=日内成交量自相关（round_018体检单腿：disc-0.0722/579天/审计-0.0551）。假设：稳健版彩票偏好高(A高)且成交有节奏持续性(B高)=偏好伴随规律流动性投放，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WJ5",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "max5_xvol_confirmed_by_ulcer",
        "hypothesis": "两腿角色：A=同上；B=溃疡指数（round_079 BM4单腿读数：disc-0.0415/审计-0.0607/t=0.76/审超+10.7bp）。假设：稳健版彩票偏好高(A高)且无慢性失血(B低)=偏好发生在健康推进资产上，延续。",
        "expected_sign": 1,
    },
    # ---- Group K: POS_DAY_FRAC_Z_20 x remaining validated partners ----
    {
        "id": "WK1",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "pos_day_frac_confirmed_by_gap_absorption",
        "hypothesis": "两腿角色：A=正收益日占比状态切换（disc-0.0139/审计-0.0209）；B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：状态切换(A高)且缺口易回补(B高)=切换发生在流动性缓冲强的环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WK2",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "pos_day_frac_confirmed_by_volume_profile_shift",
        "hypothesis": "两腿角色：A=同上；B=日内成交量分布偏离（round_053门7全过：disc+0.0952/审计+0.0442/t=4.04，本线最高t单原子）。假设：状态切换(A高)且日内成交结构异常(B高)=切换伴随异常时点结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WK3",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "pos_day_frac_confirmed_by_bigbar_vol_share",
        "hypothesis": "两腿角色：A=同上；B=大bar成交量占比（round_053门7全过：disc+0.0832/审计+0.0548/t=2.92/审超+41.6bp）。假设：状态切换(A高)且大单流入活跃(B高)=切换被真实资金承接，延续。",
        "expected_sign": 1,
    },
    {
        "id": "WK4",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "pos_day_frac_confirmed_by_orderflow",
        "hypothesis": "两腿角色：A=同上；B=主买不平衡（round_079 BM6单腿读数：disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp）。假设：状态切换(A高)且买流强(B高)=切换有主动买盘确认，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
