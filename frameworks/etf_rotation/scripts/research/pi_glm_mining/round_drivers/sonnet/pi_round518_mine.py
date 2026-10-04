#!/usr/bin/env python3
"""Round 518 driver: S3 stage step 6 -- exhaustive completion pass for
INTRADAY_MOM_CORR_20 (2 admissions so far: VOL_PROFILE_DISTANCE round_513,
PEER_OU_HALFLIFE_20 round_515) against its last 14 untested partners --
after this round both of the family's two strongest atoms
(OVERNIGHT_FIRST30_CORR_20 completed round_517) will have been paired
against essentially the full validated-partner catalog. Plus 8 more
pairings for the remaining 3 atoms using the two atoms that proved
strongest for OVERNIGHT_FIRST30_CORR_20 last round (LBAR_RUN_MAX_20 t=2.96,
COJUMP_INDEX_SHARE_20 t=3.16)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_518"

_LBAR_RUNMAX = {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"}
_LBAR_ON = {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"}
_LBAR_PERM = {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"}
_AVGCOST = {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"}
_PROFIT_RATIO = {"name": "PROFIT_RATIO_60", "source": "cost_distribution"}
_LIQ_BETA = {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"}
_LIQ_R2 = {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"}
_COJUMP_IDX = {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"}
_COJUMP_DIR = {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"}
_IDIO_JUMP = {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"}
_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_ULCER = {"name": "ULCER_20", "source": "downside_risk"}
_CAT_BREADTH = {"name": "CATEGORY_BREADTH_MA20", "source": "category_state"}
_CAT_MOM60 = {"name": "CATEGORY_MOM_60", "source": "category_state"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}

base.CANDIDATES = [
    # ---- Group A: INTRADAY_MOM_CORR_20 x 14 last untested atoms (completes exhaustive coverage) ----
    {
        "id": "GY1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_RUNMAX,
        "mechanism": "intraday_momentum_confirmed_by_bigbar_run_max",
        "hypothesis": "A=首末30分钟收益相关性（round_513/515已admit2个partner）；B=大bar同向游程（round_517 GW1已证明该原子对OVERNIGHT_FIRST30_CORR_20有效，t=2.96）。假设：日内动量关系强(A高)且大单连续同向(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_ON,
        "mechanism": "intraday_momentum_confirmed_by_bigbar_overnight",
        "hypothesis": "同GY1，B=大bar后隔夜承接（round_079单腿：disc+0.0240/审计-0.0017/t=0.34/审超-3.0bp）。假设：日内动量关系强(A高)且隔夜有承接(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_PERM,
        "mechanism": "intraday_momentum_confirmed_by_bigbar_perm15",
        "hypothesis": "同GY1，B=大bar后15分钟延续比例（round_073体检：disc-0.0949/审计-0.0356/t=2.56/审超+0.04bp）。假设：日内动量关系强(A高)且冲击延续性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _AVGCOST,
        "mechanism": "intraday_momentum_confirmed_by_price_vs_avgcost",
        "hypothesis": "同GY1，B=现价相对平均成本位置（cost_distribution家族，本线尚无独立单腿数字记录）。假设：日内动量关系强(A高)且现价远高于平均成本(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY5",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _PROFIT_RATIO,
        "mechanism": "intraday_momentum_confirmed_by_profit_ratio",
        "hypothesis": "同GY1，B=获利盘比例（cost_distribution家族，本线尚无独立单腿数字记录）。假设：日内动量关系强(A高)且获利盘比例高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY6",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LIQ_BETA,
        "mechanism": "intraday_momentum_confirmed_by_liq_common_beta",
        "hypothesis": "同GY1，B=流动性共性beta（round_049体检：disc-0.007/审计-0.003）。假设：日内动量关系强(A高)且流动性共性弱(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY7",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LIQ_R2,
        "mechanism": "intraday_momentum_confirmed_by_liq_common_r2",
        "hypothesis": "同GY1，B=流动性共性拟合优度（round_049体检：disc-0.009/审计+0.002）。假设：日内动量关系强(A高)且流动性共性弱(B低)=延续，同GY6。",
        "expected_sign": 1,
    },
    {
        "id": "GY8",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _COJUMP_IDX,
        "mechanism": "intraday_momentum_confirmed_by_cojump_index_share",
        "hypothesis": "同GY1，B=共跳指数份额（round_517 GW9已证明该原子对OVERNIGHT_FIRST30_CORR_20有效，t=3.16，本线S3阶段最强partner之一）。假设：日内动量关系强(A高)且跳跃与市场同步(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY9",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _COJUMP_DIR,
        "mechanism": "intraday_momentum_confirmed_by_cojump_dir_agree",
        "hypothesis": "同GY1，B=共跳方向一致度（round_049体检：disc-0.080/审计-0.068）。假设：日内动量关系强(A高)且跳跃方向与市场一致(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY10",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _IDIO_JUMP,
        "mechanism": "intraday_momentum_confirmed_by_idio_jump_share",
        "hypothesis": "同GY1，B=特质跳跃份额（round_049体检，Jacod-Todorov 2009：disc+0.047/审计+0.014）。假设：日内动量关系强(A高)且跳跃为特质性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY11",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _DIR_SKEW,
        "mechanism": "intraday_momentum_confirmed_by_bigbar_dir_skew",
        "hypothesis": "同GY1，B=大bar方向偏斜（round_018体检：disc-0.0117/审计+0.0254）。假设：日内动量关系强(A高)且大单方向一致偏斜(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY12",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _ULCER,
        "mechanism": "intraday_momentum_confirmed_by_ulcer",
        "hypothesis": "同GY1，B=溃疡指数（round_079单腿：disc-0.0415/审计-0.0607/t=0.76/审超+10.7bp）。假设：日内动量关系强(A高)且无慢性失血(B低)=延续。本轮完成该atom对全部已知partner的穷尽覆盖。",
        "expected_sign": 1,
    },
    {
        "id": "GY13",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CAT_BREADTH,
        "mechanism": "intraday_momentum_confirmed_by_category_breadth",
        "hypothesis": "同GY1，B=类别广度均值（category_state家族，本线尚无独立单腿数字记录）。假设：日内动量关系强(A高)且所属类别参与广度低(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GY14",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_20", "source": "intraday_momentum_30m"},
        "right": _CAT_MOM60,
        "mechanism": "intraday_momentum_confirmed_by_category_mom60",
        "hypothesis": "同GY1，B=类别60日动量（category_state家族，本线尚无独立单腿数字记录）。假设：日内动量关系强(A高)且所属类别中期动量强(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- Group B: INTRADAY_MOM_CORR_60 x 4 new (using the two proven-strongest partners) ----
    {
        "id": "GZ1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _LBAR_RUNMAX,
        "mechanism": "intraday_momentum60_confirmed_by_bigbar_run_max",
        "hypothesis": "60日窗版本。A=首末30分钟收益相关性60日窗（round_514已admit与OPEN30_VOL_SHARE_20配对）；B=大bar同向游程（round_517证明对本家族有效，t=2.96）。假设：长窗关系强(A高)且大单连续同向(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GZ2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _COJUMP_IDX,
        "mechanism": "intraday_momentum60_confirmed_by_cojump_index_share",
        "hypothesis": "同GZ1，B=共跳指数份额（round_517证明对本家族有效，t=3.16）。假设：长窗关系强(A高)且跳跃与市场同步(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GZ3",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _GRANGER_IN,
        "mechanism": "intraday_momentum60_confirmed_by_granger_in_degree",
        "hypothesis": "同GZ1，B=Granger网络入度（round_052体检：disc-0.079/审计-0.044）。假设：长窗关系强(A高)且接受外部溢出弱(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "GZ4",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_CORR_60", "source": "intraday_momentum_30m"},
        "right": _LOG_AMT,
        "mechanism": "intraday_momentum60_confirmed_by_high_activity",
        "hypothesis": "同GZ1，B=对数成交额（round_517 GX3已证明该原子对INTRADAY_MOM_CORR_20有效，t=2.19；本线历史最强单腿之一）。假设：长窗关系强(A高)且活跃度高(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- Group C: LAST30_NEXTOPEN_CORR_20 x 2 new ----
    {
        "id": "HA1",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_RUNMAX,
        "mechanism": "last30_nextopen_confirmed_by_bigbar_run_max",
        "hypothesis": "A=尾盘30分钟收益与次日隔夜跳空相关（已按信号时点错位对齐）；B=大bar同向游程（round_517证明对本家族有效，t=2.96）。假设：尾盘-次日关系强(A高)且大单连续同向(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "HA2",
        "operator": "rank_spread",
        "left": {"name": "LAST30_NEXTOPEN_CORR_20", "source": "intraday_momentum_30m"},
        "right": _COJUMP_IDX,
        "mechanism": "last30_nextopen_confirmed_by_cojump_index_share",
        "hypothesis": "同HA1，B=共跳指数份额（round_517证明对本家族有效，t=3.16）。假设：尾盘-次日关系强(A高)且跳跃与市场同步(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- Group D: INTRADAY_MOM_BETA_20 x 2 new ----
    {
        "id": "HB1",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _LBAR_RUNMAX,
        "mechanism": "intraday_momentum_beta_confirmed_by_bigbar_run_max",
        "hypothesis": "A=末30分钟对首30分钟收益回归斜率；B=大bar同向游程（round_517证明对本家族有效，t=2.96）。假设：传导斜率大(A高)且大单连续同向(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "HB2",
        "operator": "rank_spread",
        "left": {"name": "INTRADAY_MOM_BETA_20", "source": "intraday_momentum_30m"},
        "right": _COJUMP_IDX,
        "mechanism": "intraday_momentum_beta_confirmed_by_cojump_index_share",
        "hypothesis": "同HB1，B=共跳指数份额（round_517证明对本家族有效，t=3.16）。假设：传导斜率大(A高)且跳跃与市场同步(B高)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
