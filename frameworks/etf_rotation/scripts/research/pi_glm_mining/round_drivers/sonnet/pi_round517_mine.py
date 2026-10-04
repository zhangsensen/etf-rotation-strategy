#!/usr/bin/env python3
"""Round 517 driver: S3 stage step 5 -- exhaustive completion pass for
OVERNIGHT_FIRST30_CORR_20 (the strongest atom, 5/8 S3 admissions so far)
against every remaining atom in this line's full validated-partner
catalog (13 atoms: largebar_footprint_1m's 3 untested, cost_distribution's
2, fund_flow's 2, liquidity_commonality_1m's 2, cojump_1m's
COJUMP_INDEX_SHARE_20, bar_size_order_flow's BIGBAR_DIR_SKEW_20,
category_state's 2, downside_risk's ULCER_20) -- after this round, that
atom will have been paired against essentially every atom this line has
ever validated. Also fills 10 of the largest remaining gaps for
INTRADAY_MOM_CORR_20 (1 admission so far)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_517"

_LBAR_RUNMAX = {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"}
_LBAR_ON = {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"}
_LBAR_PERM = {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"}
_LBAR_TREND = {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"}
_AVGCOST = {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"}
_PROFIT_RATIO = {"name": "PROFIT_RATIO_60", "source": "cost_distribution"}
_STREAK = {"name": "STREAK_DAYS", "source": "fund_flow"}
_SHARE_CORR = {"name": "SHARE_RET_CORR_20", "source": "fund_flow"}
_LIQ_BETA = {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"}
_LIQ_R2 = {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"}
_COJUMP_IDX = {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"}
_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_CAT_BREADTH = {"name": "CATEGORY_BREADTH_MA20", "source": "category_state"}
_CAT_MOM60 = {"name": "CATEGORY_MOM_60", "source": "category_state"}
_CAT_DISP = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_ULCER = {"name": "ULCER_20", "source": "downside_risk"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_NET_SPILL = {"name": "NET_SPILLOVER_20", "source": "cross_dependence_1m"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_CLOSE30 = {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}

base.CANDIDATES = [
    # ---- Group A: OVERNIGHT_FIRST30_CORR_20 x last 13 untested atoms (completes exhaustive coverage) ----
    {
        "id": "GW1",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_RUNMAX,
        "mechanism": "overnight_first30_confirmed_by_bigbar_run_max",
        "hypothesis": "A=隔夜-开盘延续相关性（round_513-516已admit5个partner，本线最强atom）；B=大bar同向游程（round_079单腿：disc-0.0273/审计-0.0140/t=0.27/审超-1.6bp）。假设：延续性稳定(A高)且大单连续同向(B高)=延续伴随连续性推进，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW2",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_ON,
        "mechanism": "overnight_first30_confirmed_by_bigbar_overnight",
        "hypothesis": "A=同上；B=大bar后隔夜承接（round_079单腿：disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp）。假设：延续性稳定(A高)且隔夜有承接(B高)=两种隔夜视角互相确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW3",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_PERM,
        "mechanism": "overnight_first30_confirmed_by_bigbar_perm15",
        "hypothesis": "A=同上；B=大bar后15分钟延续比例（round_073体检：disc-0.0949/审计-0.0356/t=2.56/审超+0.04bp）。假设：延续性稳定(A高)且冲击延续性强(B高)=延续由持久性冲击驱动，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW4",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _AVGCOST,
        "mechanism": "overnight_first30_confirmed_by_price_vs_avgcost",
        "hypothesis": "A=同上；B=现价相对平均成本位置（cost_distribution家族，本线尚无独立单腿数字记录）。假设：延续性稳定(A高)且现价远高于平均成本(B高)=延续发生在浮盈厚的资产上，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW5",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _PROFIT_RATIO,
        "mechanism": "overnight_first30_confirmed_by_profit_ratio",
        "hypothesis": "A=同上；B=获利盘比例（cost_distribution家族，本线尚无独立单腿数字记录）。假设：延续性稳定(A高)且获利盘比例高(B高)=延续发生在浮盈筹码集中的资产上，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW6",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _STREAK,
        "mechanism": "overnight_first30_confirmed_by_streak_days",
        "hypothesis": "A=同上；B=份额连续净申购天数（round_034体检：disc+0.0004/审计+0.0122）。假设：延续性稳定(A高)且份额持续净申购(B高)=延续伴随资金持续流入，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW7",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LIQ_BETA,
        "mechanism": "overnight_first30_confirmed_by_liq_common_beta",
        "hypothesis": "A=同上；B=流动性共性beta（round_049体检：disc-0.007/审计-0.003）。假设：延续性稳定(A高)且流动性共性弱(B低)=延续独立于系统性流动性环境，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW8",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LIQ_R2,
        "mechanism": "overnight_first30_confirmed_by_liq_common_r2",
        "hypothesis": "A=同上；B=流动性共性拟合优度（round_049体检：disc-0.009/审计+0.002）。假设：延续性稳定(A高)且流动性共性弱(B低)=延续，同GW7。",
        "expected_sign": 1,
    },
    {
        "id": "GW9",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _COJUMP_IDX,
        "mechanism": "overnight_first30_confirmed_by_cojump_index_share",
        "hypothesis": "A=同上；B=共跳指数份额（round_049体检：disc-0.064/审计-0.045）。假设：延续性稳定(A高)且跳跃与市场同步(B高)=延续在系统性跳跃环境中被放大，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW10",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _DIR_SKEW,
        "mechanism": "overnight_first30_confirmed_by_bigbar_dir_skew",
        "hypothesis": "A=同上；B=大bar方向偏斜（round_018体检：disc-0.0117/审计+0.0254）。假设：延续性稳定(A高)且大单方向一致偏斜(B高)=延续伴随方向性大单流，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW11",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CAT_BREADTH,
        "mechanism": "overnight_first30_confirmed_by_category_breadth",
        "hypothesis": "A=同上；B=类别广度均值（category_state家族，本线尚无独立单腿数字记录）。假设：延续性稳定(A高)且所属类别参与广度低(B低，少数票领涨)=延续在窄幅领涨环境中被放大，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW12",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CAT_MOM60,
        "mechanism": "overnight_first30_confirmed_by_category_mom60",
        "hypothesis": "A=同上；B=类别60日动量（category_state家族，本线尚无独立单腿数字记录）。假设：延续性稳定(A高)且所属类别中期动量强(B高)=延续伴随板块层面的趋势性支撑，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GW13",
        "operator": "rank_spread",
        "left": {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"},
        "right": _ULCER,
        "mechanism": "overnight_first30_confirmed_by_ulcer",
        "hypothesis": "A=同上；B=溃疡指数（round_079单腿：disc-0.0415/审计-0.0607/t=0.76/审超+10.7bp）。假设：延续性稳定(A高)且无慢性失血(B低)=延续发生在健康推进资产上，本轮完成该atom对全部已知partner的穷尽覆盖。",
        "expected_sign": 1,
    },
    # ---- Group B: INTRADAY_MOM_CORR_20 x 10 largest remaining gaps ----
    {
        "id": "GX1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_TREND,
        "mechanism": "intraday_momentum_confirmed_by_bigbar_trend",
        "hypothesis": "A=首末30分钟收益相关性（round_513已admit与VOL_PROFILE_DISTANCE配对，t=3.50；round_515已admit与PEER_OU_HALFLIFE_20配对）；B=大bar量占比趋势（round_079单腿：disc+0.0426/审计+0.0206/t=0.82/审超+23.7bp）。假设：日内动量关系强(A高)且大单活动升温(B高)=关系伴随知情流入渐进增强，延续。",
        "expected_sign": 1,
    },
    {
        "id": "GX2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CAT_DISP,
        "mechanism": "intraday_momentum_confirmed_by_category_dispersion",
        "hypothesis": "同GX1，B=类别内离散度（round_071复盘：货架16门7独立通过的3个之一，审计超额+23.3bp）。假设：日内动量关系强(A高)且类别内分化大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GX3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LOG_AMT,
        "mechanism": "intraday_momentum_confirmed_by_high_activity",
        "hypothesis": "同GX1，B=对数成交额（round_079单腿：disc+0.0661/审计+0.0701/t=2.23/审超+36.8bp，本线历史最强单腿之一）。假设：日内动量关系强(A高)且活跃度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GX4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _GRANGER_IN,
        "mechanism": "intraday_momentum_confirmed_by_granger_in_degree",
        "hypothesis": "同GX1，B=Granger网络入度（round_052体检：disc-0.079/审计-0.044，本cross_dependence_1m家族相关性最高原子）。假设：日内动量关系强(A高)且接受外部溢出弱(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GX5",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _NET_SPILL,
        "mechanism": "intraday_momentum_confirmed_by_net_spillover",
        "hypothesis": "同GX1，B=净溢出（round_052体检：disc+0.048/审计-0.016，本cross_dependence_1m家族发现IC最高原子）。假设：日内动量关系强(A高)且净溢出为正(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GX6",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _VOL_ENTROPY,
        "mechanism": "intraday_momentum_confirmed_by_volume_entropy",
        "hypothesis": "同GX1，B=日内成交量分布熵（round_024体检：disc+0.0070/审计+0.0229）。假设：日内动量关系强(A高)且成交分布分散(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GX7",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CLOSE30,
        "mechanism": "intraday_momentum_confirmed_by_close30_vol_share",
        "hypothesis": "同GX1，B=收盘30分钟成交占比（round_024体检：disc+0.0468/审计-0.0044）。假设：日内动量关系强(A高)且尾盘集中交易(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GX8",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _SHARE_CORR,
        "mechanism": "intraday_momentum_confirmed_by_share_ret_corr",
        "hypothesis": "同GX1，B=份额变化与收益相关性（round_034体检：disc+0.0137/审计+0.0320，出现在5个admitted组合）。假设：日内动量关系强(A高)且份额-收益同向性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GX9",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _STREAK,
        "mechanism": "intraday_momentum_confirmed_by_streak_days",
        "hypothesis": "同GX1，B=份额连续净申购天数（同GW6）。假设：日内动量关系强(A高)且份额持续净申购(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GX10",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _DEP_DRIFT,
        "mechanism": "intraday_momentum_confirmed_by_dep_drift",
        "hypothesis": "同GX1，B=依赖度漂移（round_052体检：disc-0.018/审计-0.015）。假设：日内动量关系强(A高)且与池依赖度下降(B低)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
