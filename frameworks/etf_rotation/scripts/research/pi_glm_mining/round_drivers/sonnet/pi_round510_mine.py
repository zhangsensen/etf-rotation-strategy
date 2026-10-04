#!/usr/bin/env python3
"""Round 510 driver: S2 stage step 8. Continues expanding the partner
pool with atoms from historical admitted combos never paired against
upside_tail/coskewness_risk: cojump_1m (IDIO_JUMP_SHARE_20,
COJUMP_INDEX_SHARE_20, COJUMP_DIR_AGREE_20 -- Jacod-Todorov 2009),
fund_flow (STREAK_DAYS), liquidity_commonality_1m (LIQ_COMMON_BETA_20/R2_20
-- CRS 2000/KLvD 2012), largebar_footprint_1m's remaining untested atoms
(LBAR_TREND_20_60, LBAR_RUN_MAX_20, LBAR_OVERNIGHT_20, LBAR_PERM15_20),
and cost_distribution's untested atoms (PROFIT_RATIO_60,
PRICE_VS_AVGCOST_20). round_509 came back empty (0/22) after RESILIENCY_20
and SHARE_RET_CORR_20 didn't confirm as strongly as VOL_SPIKE_FREQ_20/
OPEN30_VOL_SHARE_20/VOL_AUTOCORR_20/VOL_USHAPE_20 did in rounds 506-508;
this is round 2 of 3 before the stage's zero-round exhaustion clock."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_510"

_IDIO_JUMP = {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"}
_COJUMP_IDX = {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"}
_COJUMP_DIR = {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"}
_STREAK = {"name": "STREAK_DAYS", "source": "fund_flow"}
_LIQ_BETA = {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"}
_LIQ_R2 = {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"}
_LBAR_TREND = {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"}
_LBAR_RUNMAX = {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"}
_LBAR_ON = {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"}
_LBAR_PERM = {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"}
_PROFIT_RATIO = {"name": "PROFIT_RATIO_60", "source": "cost_distribution"}
_AVGCOST = {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"}

base.CANDIDATES = [
    # ---- Group A: BEST_DAY_60_XVOL x 6 cojump/liquidity-commonality atoms ----
    {
        "id": "ZA1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _IDIO_JUMP,
        "mechanism": "max_xvol60_confirmed_by_idio_jump_share",
        "hypothesis": "两腿角色：A=60日波动率残差化MAX（round_507 WI2 admitted leg，disc-0.0135/审计-0.0120）；B=特质跳跃份额（round_049体检单腿，Jacod-Todorov 2009：disc+0.047/审计+0.014，max|shelf corr|=0.32，从未与upside_tail配对）。假设：彩票偏好高(A高)且跳跃是特质性而非系统性(B高)=偏好由个体事件驱动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZA2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _COJUMP_IDX,
        "mechanism": "max_xvol60_confirmed_by_cojump_index_share",
        "hypothesis": "两腿角色：A=同上；B=共跳指数份额（round_049体检单腿：disc-0.064/审计-0.045，Bollerslev-Law-Tauchen 2008）。假设：彩票偏好高(A高)且跳跃与市场同步(B高)=偏好在系统性跳跃环境中被放大，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZA3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _COJUMP_DIR,
        "mechanism": "max_xvol60_confirmed_by_cojump_dir_agree",
        "hypothesis": "两腿角色：A=同上；B=共跳方向一致度（round_049体检单腿：disc-0.080/审计-0.068，max|shelf corr|=0.62，本cojump族相关性最高的原子）。假设：彩票偏好高(A高)且跳跃方向与市场一致(B高)=偏好伴随同步性上涨跳跃，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZA4",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _STREAK,
        "mechanism": "max_xvol60_confirmed_by_streak_days",
        "hypothesis": "两腿角色：A=同上；B=份额连续净申购天数（round_034体检单腿：disc+0.0004/审计+0.0122，出现在Z4 admitted组合的一条腿）。假设：彩票偏好高(A高)且份额持续净申购(B高)=偏好伴随资金持续流入确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZA5",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _LIQ_BETA,
        "mechanism": "max_xvol60_confirmed_by_liq_common_beta",
        "hypothesis": "两腿角色：A=同上；B=流动性共性beta（round_049体检单腿，CRS 2000/KLvD 2012：disc-0.007/审计-0.003，出现在W1/W5/Z2 admitted组合）。假设：彩票偏好高(A高)且流动性对池共性敏感度低(B低，即流动性更独立)=偏好定价错误不易被套利资金跨资产对冲消化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZA6",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _LIQ_R2,
        "mechanism": "max_xvol60_confirmed_by_liq_common_r2",
        "hypothesis": "两腿角色：A=同上；B=流动性共性拟合优度（round_049体检单腿：disc-0.009/审计+0.002，出现在W5 admitted组合）。假设：彩票偏好高(A高)且流动性共性弱(B低)=偏好独立于系统性流动性环境，延续。",
        "expected_sign": 1,
    },
    # ---- Group B: MAX5_MEAN_20_XVOL x 4 cojump/streak atoms ----
    {
        "id": "ZB1",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _IDIO_JUMP,
        "mechanism": "max5_xvol_confirmed_by_idio_jump_share",
        "hypothesis": "同ZA1，A=MAX(5)残差化（round_508 XB2 admitted leg，disc+0.0020/审计+0.0197）。假设同ZA1。",
        "expected_sign": 1,
    },
    {
        "id": "ZB2",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _COJUMP_IDX,
        "mechanism": "max5_xvol_confirmed_by_cojump_index_share",
        "hypothesis": "同ZA2，A=MAX(5)残差化。假设同ZA2。",
        "expected_sign": 1,
    },
    {
        "id": "ZB3",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _COJUMP_DIR,
        "mechanism": "max5_xvol_confirmed_by_cojump_dir_agree",
        "hypothesis": "同ZA3，A=MAX(5)残差化。假设同ZA3。",
        "expected_sign": 1,
    },
    {
        "id": "ZB4",
        "operator": "rank_spread",
        "left": {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"},
        "right": _STREAK,
        "mechanism": "max5_xvol_confirmed_by_streak_days",
        "hypothesis": "同ZA4，A=MAX(5)残差化。假设同ZA4。",
        "expected_sign": 1,
    },
    # ---- Group C: BEST_DAY_20_XVOL x 3 largebar atoms ----
    {
        "id": "ZC1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _LBAR_TREND,
        "mechanism": "max_xvol20_confirmed_by_bigbar_trend",
        "hypothesis": "两腿角色：A=20日窗残差化MAX（round_508 XD8 admitted leg族群，disc+0.0034/审计-0.0146）；B=大bar量占比趋势（round_079单腿：disc+0.0426/审计+0.0206/t=0.82/审超+23.7bp）。假设：彩票偏好高(A高)且大单活动升温(B高)=偏好伴随知情流入渐进增强，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZC2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _LBAR_RUNMAX,
        "mechanism": "max_xvol20_confirmed_by_bigbar_run_max",
        "hypothesis": "两腿角色：A=同上；B=大bar同向游程（round_079单腿：disc-0.0273/审计-0.0140/t=0.27/审超-1.6bp）。假设：彩票偏好高(A高)且大单连续同向(B高)=偏好伴随连续性大单推进，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZC3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"},
        "right": _LBAR_ON,
        "mechanism": "max_xvol20_confirmed_by_bigbar_overnight",
        "hypothesis": "两腿角色：A=同上；B=大bar后隔夜承接（round_079单腿：disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp）。假设：彩票偏好高(A高)且隔夜有承接(B高)=偏好跨夜延续，延续。",
        "expected_sign": 1,
    },
    # ---- Group D: INTRADAY_MAXBAR_RET_20_XVOL x 4 largebar atoms ----
    {
        "id": "ZD1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _LBAR_TREND,
        "mechanism": "intraday_max_xvol_confirmed_by_bigbar_trend",
        "hypothesis": "两腿角色：A=1m日内MAX残差化（round_506 VB8 admitted leg，disc-0.0203/审计-0.0002）；B=大bar量占比趋势（同ZC1，disc+0.0426/审计+0.0206/t=0.82/审超+23.7bp）。A/B同为1m路径构造。假设：日内彩票偏好高(A高)且大单活动升温(B高)=偏好伴随知情流入渐进增强，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZD2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _LBAR_RUNMAX,
        "mechanism": "intraday_max_xvol_confirmed_by_bigbar_run_max",
        "hypothesis": "同ZD1，B=大bar同向游程（同ZC2，disc-0.0273/审计-0.0140/t=0.27/审超-1.6bp）。假设：日内彩票偏好高(A高)且大单连续同向(B高)=偏好伴随连续性推进，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZD3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _LBAR_ON,
        "mechanism": "intraday_max_xvol_confirmed_by_bigbar_overnight",
        "hypothesis": "同ZD1，B=大bar后隔夜承接（同ZC3，disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp）。假设：日内彩票偏好高(A高)且隔夜有承接(B高)=偏好跨夜延续，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZD4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"},
        "right": _LBAR_PERM,
        "mechanism": "intraday_max_xvol_confirmed_by_bigbar_perm15",
        "hypothesis": "同ZD1，B=大bar后15分钟延续比例（round_073体检：disc-0.0949/审计-0.0356/t=2.56/审超+0.04bp，Bouchaud-Farmer-Lillo 2009冲击永久性）。假设：日内彩票偏好高(A高)且冲击延续性强(B高)=偏好由持久性冲击驱动，延续。",
        "expected_sign": 1,
    },
    # ---- Group E: POS_DAY_FRAC_Z_20 x 3 cojump/liquidity atoms ----
    {
        "id": "ZE1",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _COJUMP_IDX,
        "mechanism": "pos_day_frac_confirmed_by_cojump_index_share",
        "hypothesis": "两腿角色：A=正收益日占比状态切换（disc-0.0139/审计-0.0209）；B=共跳指数份额（同ZA2，disc-0.064/审计-0.045）。假设：状态切换(A高)且跳跃与市场同步(B高)=切换在系统性跳跃环境发生，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZE2",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _STREAK,
        "mechanism": "pos_day_frac_confirmed_by_streak_days",
        "hypothesis": "两腿角色：A=同上；B=份额连续净申购天数（同ZA4，disc+0.0004/审计+0.0122）。假设：状态切换(A高)且份额持续净申购(B高)=切换伴随资金持续流入，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZE3",
        "operator": "rank_spread",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": _LIQ_BETA,
        "mechanism": "pos_day_frac_confirmed_by_liq_common_beta",
        "hypothesis": "两腿角色：A=同上；B=流动性共性beta（同ZA5，disc-0.007/审计-0.003）。假设：状态切换(A高)且流动性独立性高(B低)=切换定价错误不易被跨资产套利，延续。",
        "expected_sign": 1,
    },
    # ---- Group F: BEST_DAY_60_XVOL x 3 remaining new atoms ----
    {
        "id": "ZF1",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _LBAR_PERM,
        "mechanism": "max_xvol60_confirmed_by_bigbar_perm15",
        "hypothesis": "两腿角色：A=同ZA1；B=大bar后15分钟延续比例（同ZD4，disc-0.0949/审计-0.0356/t=2.56/审超+0.04bp）。假设：彩票偏好高(A高)且冲击延续性强(B高)=偏好由持久性冲击驱动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZF2",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _AVGCOST,
        "mechanism": "max_xvol60_confirmed_by_price_vs_avgcost",
        "hypothesis": "两腿角色：A=同ZA1；B=现价相对平均成本位置（cost_distribution家族，出现在W4 admitted组合的另一条腿，本线尚无独立单腿数字记录）。假设：彩票偏好高(A高)且现价远高于平均成本(B高，浮盈厚)=偏好在获利丰厚的资产上更易被追高定价错误，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZF3",
        "operator": "rank_spread",
        "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
        "right": _PROFIT_RATIO,
        "mechanism": "max_xvol60_confirmed_by_profit_ratio",
        "hypothesis": "两腿角色：A=同ZA1；B=获利盘比例（cost_distribution家族，出现在W2/Z1 admitted组合的一条腿，本线尚无独立单腿数字记录）。假设：彩票偏好高(A高)且获利盘比例高(B高)=偏好在浮盈筹码集中的资产上更易被追捧，延续。",
        "expected_sign": 1,
    },
    # ---- Group G: DOWNSIDE_COSKEW_60 x 2 new atoms ----
    {
        "id": "ZG1",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _IDIO_JUMP,
        "mechanism": "downside_coskew_confirmed_by_idio_jump_share",
        "hypothesis": "两腿角色：A=下行条件化协偏度（round_500体检 disc+0.0319/审计+0.0404，identity通过）；B=特质跳跃份额（同ZA1，disc+0.047/审计+0.014）。假设：崩盘暴露高(A高)且跳跃是特质性(B高)=系统性风险与个体事件叠加，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ZG2",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": _COJUMP_DIR,
        "mechanism": "downside_coskew_confirmed_by_cojump_dir_agree",
        "hypothesis": "两腿角色：A=同上；B=共跳方向一致度（同ZA3，disc-0.080/审计-0.068）。假设：崩盘暴露高(A高)且跳跃方向与市场一致(B高)=系统性风险由同步性跳跃驱动，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
