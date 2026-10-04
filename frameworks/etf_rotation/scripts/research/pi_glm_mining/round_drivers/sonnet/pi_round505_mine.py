#!/usr/bin/env python3
"""Round 505 driver: S2 stage step 3 — large batch (main controller
directive 2026-09-20 14:30: 15-30 preregistrations per round, one round
covers atomic + first pairing pass). 4 atomic candidates for the new
volatility-residualized upside_tail atoms (BEST_DAY_20/60_XVOL,
MAX5_MEAN_20_XVOL, INTRADAY_MAXBAR_RET_20_XVOL; round_505 atom_health:
all non-shadow, corr < 0.70 vs shelf16, but IC dropped sharply after
residualization vs the raw round_504 atoms -- most of the raw MAX signal
was REALIZED_VOL_60 in disguise). Plus 25 directed cross-family pairings
of the 4 XVOL atoms and the one surviving raw atom (POS_DAY_FRAC_Z_20)
against the pool of atoms with known single-leg gate-7 numbers from
round_053 (7 atomic winners), round_079 (3 single-leg citations) and
round_018 atom_health (3 more, no historical topk numbers recorded)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_505"

base.CANDIDATES = [
    # ---- 4 atomic: new volatility-residualized upside_tail atoms ----
    {
        "id": "UX1",
        "operator": "atomic",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "mechanism": "max_effect_best_day_20_xvol",
        "hypothesis": "Bali-Cakici-Whitelaw MAX效应，20日窗，对REALIZED_VOL_60做逐日横截面OLS残差化（round_504体检：原始BEST_DAY_20 disc-0.0941/审计-0.0736，shadow=0.72 vs该货架因子；round_505残差化后体检：disc+0.0034/551天/审计-0.0146，max|corr|=0.57 vs RETURN_SKEW_20，非shadow）。假设：剔除波动率水平后仍有独立彩票偏好定价，高rank=高估=未来跑输。",
        "expected_sign": -1,
    },
    {
        "id": "UX2",
        "operator": "atomic",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "mechanism": "max_effect_best_day_60_xvol",
        "hypothesis": "同UX1，60日窗。round_504体检：原始BEST_DAY_60 disc-0.1143/审计-0.0767，shadow=0.84（本批最高相关）；round_505残差化后：disc-0.0135/551天/审计-0.0120，max|corr|=0.67 vs RETURN_SKEW_60，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "UX3",
        "operator": "atomic",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "mechanism": "max_effect_top5_mean_20_xvol",
        "hypothesis": "MAX(5)稳健变体残差化。round_504体检：原始disc-0.0929/审计-0.0544，shadow=0.74；round_505残差化后：disc+0.0020/551天/审计+0.0197，max|corr|=0.40 vs downside_risk:CURRENT_DD_60，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "UX4",
        "operator": "atomic",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "mechanism": "intraday_maxbar_lottery_xvol",
        "hypothesis": "1m日内MAX代理残差化。round_504体检：原始disc-0.0860/审计-0.0611，shadow=0.75；round_505残差化后：disc-0.0203/551天/审计-0.0002，max|corr|=0.52 vs gap_volatility货架因子，非shadow。",
        "expected_sign": -1,
    },
    # ---- 10 pairs: BEST_DAY_60_XVOL (strongest pre-residualization solo) x round_053 7-winner pool + round_079 3 ----
    {
        "id": "UP1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "max_xvol60_confirmed_by_bigbar_vol_share",
        "hypothesis": "两腿角色：A=60日波动率残差化MAX（round_505体检 disc-0.0135/审计-0.0120，非shadow）；B=大bar成交量占比（round_053门7全过：disc+0.0832/审计+0.0548/t=2.92/审超+41.6bp）。假设：独立彩票偏好高(A高)且大单/知情流入活跃(B高)=偏好被真实资金承接确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UP2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "mechanism": "max_xvol60_confirmed_by_edge_concentration",
        "hypothesis": "两腿角色：A=同上；B=大bar价格边缘集中度（round_053门7全过：disc-0.0971/审计-0.0459/t=2.55/审超+30.7bp；round_502 RT1已证明与协偏度强配对，t=1.74）。假设：彩票偏好高(A高)且边缘集中冲击强(B高)=偏好伴随激进订单，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UP3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "max_xvol60_confirmed_by_category_vol",
        "hypothesis": "两腿角色：A=同上；B=同类别板块波动率（round_053门7全过：disc-0.0711/审计-0.0653/t=2.42/审超+19.0bp；round_502 RT2已证明与协偏度强配对，identity通过）。假设：彩票偏好高(A高)且所属板块高波动(B高)=偏好来自板块层面共振，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UP4",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "max_xvol60_confirmed_by_gap_absorption",
        "hypothesis": "两腿角色：A=同上；B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：彩票偏好高(A高)且缺口易回补(B高，流动性缓冲强)=偏好资产的定价错误更容易被修正，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UP5",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "max_xvol60_confirmed_by_volume_profile_shift",
        "hypothesis": "两腿角色：A=同上；B=日内成交量分布对同伴均值的偏离（round_053门7全过：disc+0.0952/审计+0.0442/t=4.04，本线最高t值单原子）。假设：彩票偏好高(A高)且日内成交结构异常(B高)=偏好伴随异常时点结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UP6",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "max_xvol60_confirmed_by_session_ushape",
        "hypothesis": "两腿角色：A=同上；B=日内成交量U型集中度（round_053门7全过：disc-0.0832/审计-0.0891/t=2.12/审超+33.9bp；round_501 RS3已证明与协偏度强配对，t=1.88全线最高）。假设：彩票偏好高(A高)且开收盘成交集中(B高)=偏好伴随主力时点操作，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UP7",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "max_xvol60_confirmed_by_own_worst_day",
        "hypothesis": "两腿角色：A=同上（系统性剥离波动率后的彩票偏好）；B=自身20日最差单日收益（round_053门7全过：disc+0.0635/审计+0.0648/t=2.18/审超+16.2bp）。假设：独立彩票偏好高(A高)且自身尾部也重(B高)=彩票特征与尾部风险叠加，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UP8",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "max_xvol60_confirmed_by_orderflow",
        "hypothesis": "两腿角色：A=同上；B=主买不平衡（round_079 BM6单腿读数：disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp，偏弱）。假设：彩票偏好高(A高)且日内买流强(B高)=偏好有主动买盘确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UP9",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "max_xvol60_locked_by_chip_concentration",
        "hypothesis": "两腿角色：A=同上；B=筹码区间宽度（round_079 BM2单腿读数：disc-0.0574/审计-0.0620/t=0.70/审超+14.6bp；round_502 RT2/round_503 RU6均已用同族partner）。假设：彩票偏好高(A高)且筹码集中(B高即区间窄)=偏好资产被锁仓盘固化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UP10",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "max_xvol60_confirmed_by_high_activity",
        "hypothesis": "两腿角色：A=同上；B=对数成交额（round_079 BM3单腿读数：disc+0.0661/审计+0.0701/t=2.23/审超+36.8bp，本线历史最强单腿之一）。假设：彩票偏好高(A高)且活跃度高(B高)=偏好发生在流动性充足、易被套利的环境，延续。",
        "expected_sign": 1,
    },
    # ---- 6 pairs: BEST_DAY_20_XVOL x round_018-cited + shared partners for cross-window comparison ----
    {
        "id": "UQ1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "mechanism": "max_xvol20_confirmed_by_bigbar_dir_skew",
        "hypothesis": "两腿角色：A=20日窗残差化MAX（round_505体检 disc+0.0034/审计-0.0146，非shadow）；B=大bar方向偏斜（round_018体检单腿：disc-0.0117/579天/审计+0.0254，Z2入选组合一条腿，topk历史数字未见单腿记录）。假设：短窗彩票偏好高(A高)且大单方向一致偏斜(B高)=偏好伴随方向性大单流，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UQ2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "max_xvol20_confirmed_by_volume_autocorr",
        "hypothesis": "两腿角色：A=同上；B=日内成交量自相关（round_018体检单腿：disc-0.0722/579天/审计-0.0551，Z2入选组合另一条腿）。假设：短窗彩票偏好高(A高)且日内成交有规律持续性(B高)=偏好伴随有节奏的流动性投放，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UQ3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "max_xvol20_confirmed_by_volume_spike_freq",
        "hypothesis": "两腿角色：A=同上；B=成交量脉冲频率（round_018体检单腿：disc+0.0661/579天/审计+0.0460，BB1入选组合一条腿）。假设：短窗彩票偏好高(A高)且脉冲式放量频繁(B高)=偏好伴随间歇冲击型交易，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UQ4",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "max_xvol20_confirmed_by_ulcer",
        "hypothesis": "两腿角色：A=同上；B=溃疡指数（round_079 BM4单腿读数：disc-0.0415/审计-0.0607/t=0.76/审超+10.7bp，BB1入选组合另一条腿）。假设：短窗彩票偏好高(A高)且无慢性失血(B低即溃疡低，与spread方向对齐)=偏好发生在健康推进资产上，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UQ5",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "max_xvol20_confirmed_by_bigbar_vol_share",
        "hypothesis": "对照UP1（60日窗）：A=20日窗版本；B=大bar成交量占比（同UP1，disc+0.0832/审计+0.0548/t=2.92/审超+41.6bp）。检验短窗MAX是否与长窗一样能被同一partner确认。",
        "expected_sign": 1,
    },
    {
        "id": "UQ6",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "max_xvol20_confirmed_by_category_vol",
        "hypothesis": "对照UP3（60日窗）：A=20日窗版本；B=同类别板块波动率（同UP3，disc-0.0711/审计-0.0653/t=2.42/审超+19.0bp）。检验短窗MAX是否与长窗一样能被同一partner确认。",
        "expected_sign": 1,
    },
    # ---- 4 pairs: MAX5_MEAN_20_XVOL ----
    {
        "id": "UM1",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "max5_xvol_confirmed_by_gap_absorption",
        "hypothesis": "两腿角色：A=MAX(5)残差化（round_505体检 disc+0.0020/审计+0.0197，非shadow）；B=缺口回补比例（同UP4，disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：稳健版彩票偏好高(A高)且缺口易回补(B高)=定价错误易被修正，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UM2",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "max5_xvol_confirmed_by_volume_profile_shift",
        "hypothesis": "两腿角色：A=同上；B=日内成交量分布偏离（同UP5，disc+0.0952/审计+0.0442/t=4.04，本线最高t单原子）。假设：稳健版彩票偏好高(A高)且日内结构异常(B高)=偏好伴随异常成交时点，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UM3",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "max5_xvol_confirmed_by_own_worst_day",
        "hypothesis": "两腿角色：A=同上；B=自身20日最差单日收益（同UP7，disc+0.0635/审计+0.0648/t=2.18/审超+16.2bp）。假设：稳健版彩票偏好(A高)叠加自身尾部重(B高)，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UM4",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "max5_xvol_confirmed_by_high_activity",
        "hypothesis": "两腿角色：A=同上；B=对数成交额（同UP10，disc+0.0661/审计+0.0701/t=2.23/审超+36.8bp）。假设：稳健版彩票偏好(A高)发生在高活跃环境(B高)，延续。",
        "expected_sign": 1,
    },
    # ---- 3 pairs: INTRADAY_MAXBAR_RET_20_XVOL ----
    {
        "id": "UI1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "intraday_max_xvol_confirmed_by_orderflow",
        "hypothesis": "两腿角色：A=1m日内MAX残差化（round_505体检 disc-0.0203/审计-0.0002，非shadow）；B=主买不平衡（同UP8，disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp）。假设：日内彩票偏好高(A高)且买流强(B高)=偏好有主动买盘同时发生，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UI2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "intraday_max_xvol_locked_by_chip_concentration",
        "hypothesis": "两腿角色：A=同上；B=筹码区间宽度（同UP9，disc-0.0574/审计-0.0620/t=0.70/审超+14.6bp）。假设：日内彩票偏好高(A高)且筹码集中(B高)=偏好被锁仓盘固化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UI3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "intraday_max_xvol_confirmed_by_session_ushape",
        "hypothesis": "两腿角色：A=同上；B=日内成交量U型集中度（同UP6，disc-0.0832/审计-0.0891/t=2.12/审超+33.9bp）。假设：日内彩票偏好高(A高)且开收盘成交集中(B高)=偏好伴随主力时点操作，延续。",
        "expected_sign": 1,
    },
    # ---- 2 pairs: POS_DAY_FRAC_Z_20 (weak solo, round_504) ----
    {
        "id": "UZ1",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "mechanism": "pos_day_frac_confirmed_by_edge_concentration",
        "hypothesis": "两腿角色：A=正收益日占比状态切换（round_504体检 disc-0.0139/579天/审计-0.0209，非shadow但弱）；B=大bar价格边缘集中度（同UP2，disc-0.0971/审计-0.0459/t=2.55/审超+30.7bp）。假设：正收益日占比异常升高(A高)且边缘冲击集中(B高)=状态切换有激进订单确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "UZ2",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "pos_day_frac_confirmed_by_category_vol",
        "hypothesis": "两腿角色：A=同上；B=同类别板块波动率（同UP3，disc-0.0711/审计-0.0653/t=2.42/审超+19.0bp）。假设：正收益日占比异常升高(A高)且板块高波动(B高)=状态切换来自板块共振，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
