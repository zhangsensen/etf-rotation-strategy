#!/usr/bin/env python3
"""Round 506 driver: S2 stage step 4 — second pairing batch (26
candidates), building on round_505's findings: (a) BEST_DAY_60_XVOL is the
strongest surviving upside_tail leg -- pair it against the 4 round_018
partners not yet tried; (b) INTRADAY_MAXBAR_RET_20_XVOL had the closest
overall miss (UI3, t=1.98, audit +45.2bp) -- broaden its partner coverage;
(c) round_505's UP1 was blocked only by redundancy with its own strong
leg (already-admitted BIGBAR_VOL_SHARE_20) -- retry that exact pair as
rank_interaction (a different canonical expression, may combine the two
legs' information differently and not simply degenerate to the dominant
leg); (d) new-family x new-family: DOWNSIDE_COSKEW_60 (coskewness_risk,
round_500, closest historical miss at t=1.88 in round_501) x each
upside_tail XVOL/survivor atom, testing whether systemic crash exposure
compounds with orthogonalized lottery preference."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_506"

base.CANDIDATES = [
    # ---- Group A: BEST_DAY_60_XVOL x 4 round_018 partners not yet tried with this leg ----
    {
        "id": "VA1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "mechanism": "max_xvol60_confirmed_by_bigbar_dir_skew",
        "hypothesis": "两腿角色：A=60日波动率残差化MAX（round_505体检 disc-0.0135/审计-0.0120，非shadow；round_505 UP系列最强leg，UP1 t=2.63仅因与BIGBAR_VOL_SHARE_20冗余被拒）；B=大bar方向偏斜（round_018体检单腿：disc-0.0117/579天/审计+0.0254，Z2入选组合一条腿，topk数字未见单腿记录）。假设：彩票偏好高(A高)且大单方向一致偏斜(B高)=偏好伴随方向性大单流，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VA2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "max_xvol60_confirmed_by_volume_autocorr",
        "hypothesis": "两腿角色：A=同上；B=日内成交量自相关（round_018体检单腿：disc-0.0722/579天/审计-0.0551，Z2入选组合另一条腿）。假设：彩票偏好高(A高)且日内成交有规律持续性(B高)=偏好伴随有节奏的流动性投放，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VA3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "max_xvol60_confirmed_by_volume_spike_freq",
        "hypothesis": "两腿角色：A=同上；B=成交量脉冲频率（round_018体检单腿：disc+0.0661/579天/审计+0.0460，BB1入选组合一条腿）。假设：彩票偏好高(A高)且脉冲式放量频繁(B高)=偏好伴随间歇冲击型交易，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VA4",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "max_xvol60_confirmed_by_ulcer",
        "hypothesis": "两腿角色：A=同上；B=溃疡指数（round_079 BM4单腿读数：disc-0.0415/审计-0.0607/t=0.76/审超+10.7bp，BB1入选组合另一条腿）。假设：彩票偏好高(A高)且无慢性失血(B低)=偏好发生在健康推进资产上，延续。",
        "expected_sign": 1,
    },
    # ---- Group B: INTRADAY_MAXBAR_RET_20_XVOL x 8 new partners (round_505 UI3 was closest overall miss: t=1.98, audit+45.2bp) ----
    {
        "id": "VB1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "intraday_max_xvol_confirmed_by_own_worst_day",
        "hypothesis": "两腿角色：A=1m日内MAX残差化（round_505体检 disc-0.0203/审计-0.0002，非shadow；round_505 UI3与VOL_USHAPE_20配对 t=1.98/审超+45.2bp 是全线最接近门7的一条）；B=自身20日最差单日收益（round_053门7全过：disc+0.0635/审计+0.0648/t=2.18/审超+16.2bp）。假设：日内彩票偏好高(A高)且自身尾部重(B高)=偏好与尾部风险叠加，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VB2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "intraday_max_xvol_confirmed_by_gap_absorption",
        "hypothesis": "两腿角色：A=同上；B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：日内彩票偏好高(A高)且缺口易回补(B高)=定价错误容易被修正，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VB3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "intraday_max_xvol_confirmed_by_volume_profile_shift",
        "hypothesis": "两腿角色：A=同上；B=日内成交量分布偏离（round_053门7全过：disc+0.0952/审计+0.0442/t=4.04，本线最高t单原子）。假设：日内彩票偏好高(A高)且日内成交结构异常(B高)=同为日内层面的确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VB4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "intraday_max_xvol_confirmed_by_bigbar_vol_share",
        "hypothesis": "两腿角色：A=同上；B=大bar成交量占比（round_053门7全过：disc+0.0832/审计+0.0548/t=2.92/审超+41.6bp）。假设：日内彩票偏好高(A高)且大单流入活跃(B高)=偏好被真实资金承接，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VB5",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "intraday_max_xvol_confirmed_by_category_vol",
        "hypothesis": "两腿角色：A=同上；B=同类别板块波动率（round_053门7全过：disc-0.0711/审计-0.0653/t=2.42/审超+19.0bp）。假设：日内彩票偏好高(A高)且板块高波动(B高)=偏好来自板块层面共振，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VB6",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "mechanism": "intraday_max_xvol_confirmed_by_bigbar_dir_skew",
        "hypothesis": "两腿角色：A=同上；B=大bar方向偏斜（round_018体检单腿：disc-0.0117/579天/审计+0.0254）。假设：日内彩票偏好高(A高)且大单方向一致偏斜(B高)=偏好伴随方向性大单流，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VB7",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "intraday_max_xvol_confirmed_by_volume_autocorr",
        "hypothesis": "两腿角色：A=同上；B=日内成交量自相关（round_018体检单腿：disc-0.0722/579天/审计-0.0551）。假设：日内彩票偏好高(A高)且成交有节奏持续性(B高)=偏好伴随规律流动性投放，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VB8",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "intraday_max_xvol_confirmed_by_volume_spike_freq",
        "hypothesis": "两腿角色：A=同上；B=成交量脉冲频率（round_018体检单腿：disc+0.0661/579天/审计+0.0460）。假设：日内彩票偏好高(A高)且脉冲式放量频繁(B高)=偏好伴随间歇冲击型交易，延续。",
        "expected_sign": 1,
    },
    # ---- Group C: new x new -- DOWNSIDE_COSKEW_60 (coskewness_risk) x upside_tail atoms ----
    {
        "id": "VC1",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "mechanism": "downside_coskew_confirmed_by_max_xvol60",
        "hypothesis": "两腿角色：A=下行条件化协偏度（round_500体检 disc+0.0319/审计+0.0404，identity通过，仅topk未过t=0.61；round_501-503多轮配对最高t=1.88）；B=60日波动率残差化MAX（round_505最强upside_tail leg，disc-0.0135/审计-0.0120）。假设：系统性崩盘暴露高(A高)且独立彩票偏好高(B高)=两种不同来源的定价异常同时出现，叠加信号更强，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VC2",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "mechanism": "downside_coskew_confirmed_by_max5_xvol",
        "hypothesis": "两腿角色：A=同上；B=MAX(5)残差化（round_505体检 disc+0.0020/审计+0.0197）。假设：崩盘暴露高(A高)且稳健版彩票偏好高(B高)=两来源异常叠加，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VC3",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "mechanism": "downside_coskew_confirmed_by_intraday_max_xvol",
        "hypothesis": "两腿角色：A=同上；B=1m日内MAX残差化（round_505 UI3最接近门7的leg，disc-0.0203/审计-0.0002）。假设：崩盘暴露高(A高)且日内彩票偏好高(B高)=系统性风险叠加日内投机行为，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VC4",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "mechanism": "downside_coskew_confirmed_by_pos_day_frac",
        "hypothesis": "两腿角色：A=同上；B=正收益日占比状态切换（round_504体检 disc-0.0139/审计-0.0209）。假设：崩盘暴露高(A高)且正收益日占比异常升高(B高)=系统性风险与短期状态切换同时发生，延续。",
        "expected_sign": 1,
    },
    # ---- Group D: rank_interaction retry of round_505's redundancy-blocked / identity-blocked pairs ----
    {
        "id": "VD1",
        "operator": "rank_interaction",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "max_xvol60_interaction_bigbar_vol_share",
        "hypothesis": "round_505 UP1（同一对atom的rank_spread）t=2.63/审超+28.1bp但被rank_correlation_redundancy拒绝（0.725 vs已入选的BIGBAR_VOL_SHARE_20标准品）。本候选改用rank_interaction（乘积式组合，非差值），是不同的canonical表达式，检验交互项是否降低与dominant leg的相关性同时保留信号。",
        "expected_sign": 1,
    },
    {
        "id": "VD2",
        "operator": "rank_interaction",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "max5_xvol_interaction_gap_absorption",
        "hypothesis": "round_505 UM1（rank_spread）t=2.35/审超+30.4bp仅因identity_gate未过被拒。本候选改用rank_interaction，检验交互项组合方式是否改变LOSO稳健性（不同symbol对交互项与差值项的边际贡献不同）。",
        "expected_sign": 1,
    },
    {
        "id": "VD3",
        "operator": "rank_interaction",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "mechanism": "pos_day_frac_interaction_edge_concentration",
        "hypothesis": "round_505 UZ1（rank_spread）t=2.14/审超+27.5bp仅因identity_gate未过被拒。本候选改用rank_interaction，同VD2目的。",
        "expected_sign": 1,
    },
    # ---- Group E: MAX5_MEAN_20_XVOL x 4 more partners ----
    {
        "id": "VE1",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "max5_xvol_confirmed_by_bigbar_vol_share",
        "hypothesis": "两腿角色：A=MAX(5)残差化（disc+0.0020/审计+0.0197）；B=大bar成交量占比（round_053门7全过：disc+0.0832/审计+0.0548/t=2.92/审超+41.6bp）。假设：稳健版彩票偏好高(A高)且大单流入活跃(B高)=偏好被真实资金承接，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VE2",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "max5_xvol_confirmed_by_category_vol",
        "hypothesis": "两腿角色：A=同上；B=同类别板块波动率（round_053门7全过：disc-0.0711/审计-0.0653/t=2.42/审超+19.0bp）。假设：稳健版彩票偏好高(A高)且板块高波动(B高)=偏好来自板块层面共振，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VE3",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "max5_xvol_confirmed_by_orderflow",
        "hypothesis": "两腿角色：A=同上；B=主买不平衡（round_079 BM6单腿读数：disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp，偏弱）。假设：稳健版彩票偏好高(A高)且买流强(B高)=偏好有主动买盘确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VE4",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "max5_xvol_locked_by_chip_concentration",
        "hypothesis": "两腿角色：A=同上；B=筹码区间宽度（round_079 BM2单腿读数：disc-0.0574/审计-0.0620/t=0.70/审超+14.6bp）。假设：稳健版彩票偏好高(A高)且筹码集中(B高)=偏好被锁仓盘固化，延续。",
        "expected_sign": 1,
    },
    # ---- Group F: POS_DAY_FRAC_Z_20 x 3 more partners ----
    {
        "id": "VF1",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "pos_day_frac_confirmed_by_own_worst_day",
        "hypothesis": "两腿角色：A=正收益日占比状态切换（disc-0.0139/审计-0.0209）；B=自身20日最差单日收益（round_053门7全过：disc+0.0635/审计+0.0648/t=2.18/审超+16.2bp）。假设：正收益日占比异常升高(A高)且自身尾部重(B高)=状态切换叠加尾部风险，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VF2",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "pos_day_frac_confirmed_by_high_activity",
        "hypothesis": "两腿角色：A=同上；B=对数成交额（round_079 BM3单腿读数：disc+0.0661/审计+0.0701/t=2.23/审超+36.8bp，本线历史最强单腿之一）。假设：正收益日占比异常升高(A高)且活跃度高(B高)=状态切换发生在高流动性环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "VF3",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "pos_day_frac_confirmed_by_session_ushape",
        "hypothesis": "两腿角色：A=同上；B=日内成交量U型集中度（round_053门7全过：disc-0.0832/审计-0.0891/t=2.12/审超+33.9bp）。假设：正收益日占比异常升高(A高)且开收盘成交集中(B高)=状态切换伴随主力时点操作，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
