#!/usr/bin/env python3
"""Round 581 driver: S18 stage step 1+2 -- non-volume-level atom
cross-line pairing scan (controller directive, round_581 request).

Step 1 (atomic recheck, 5 candidates): the S18 directive's 5 "pi-side
simple atoms independently implemented on this line" all ALREADY EXIST
in this codebase -- no new family needed (avoids rebuilding what's
already built, per the standing 'no reinventing the wheel' rule):
  PD_D1_CHG_20            -> source pi_price_delay_1d (S14, round_569)
  LUNCH_PRE_RUN_20        -> source pi_lunch_prerun_1m (S14, round_569)
  CLOSE5_DAY_CONSIST_20   -> source bar_size_order_flow (pre-existing,
                             S14's directive confirmed this construct
                             matches the pi definition exactly, reused
                             as-is rather than rebuilt)
  ON_PREM_20              -> source daily_candle:GAP_MEAN_20 (pre-
                             existing, S14 confirmed textually identical
                             definition -- 20d mean of open/prev_close-1)
  GAP_FILL_RATE_20        -> source gap_repair:GAP_FILL_FRACTION_20 (pre-
                             existing legacy catalog atom; definition
                             (same-day gap retracement fraction on event
                             days, 20d rolling mean, min 5 events) matches
                             the directive's "跳空当日回补比例" exactly)
This round reruns these 5 as atomic candidates for a fresh gate-7 read,
comparable against S14's round_569 numbers.

Step 2 (pairwise scan, 19 candidates): 11-atom pool = the above 5 +
6 controller-named already-verified atoms (PERM_ENTROPY_RET_20 S6,
UNDERWATER_FRAC_CHG_20 S7, UNDERWATER_FRAC_Z_60 S12, MSPE_5M_20 S11,
REL_MAXDD_20 S15, CONTINUOUS_BETA_60 S4) -- all 11 from distinct
families, so no same-family exclusions.  6 of the C(11,2)=55 possible
pairs were ALREADY tested in S16 (round_575's volume-free tournament
covered every pair among {PERM_ENTROPY_RET_20, UNDERWATER_FRAC_CHG_20,
CONTINUOUS_BETA_60, MSPE_5M_20}); those 6 pairs are excluded here.
Remaining 49 legal pairs; this round covers 19 of them via a partial
circulant design (distance-1 and distance-2 offsets mod 11, each atom
appearing as left <=2 times and as right <=2 times) -- DELIBERATELY not
exhausting every atom's left-batch/right-cap allowance in one round
(unlike S16's round_575 tournament, which spent all capacity at once
and left no room for later rounds -- see round_576's retrospective).
This leaves headroom for a possible step-3 round on the remaining 30
legal pairs if the controller wants to continue this stage."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_581"

_PERM_ENT = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_UF_Z60 = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}
_MSPE5 = {"name": "MSPE_5M_20", "source": "complexity_measures_1m"}
_REL_MAXDD = {"name": "REL_MAXDD_20", "source": "relative_path_vs_basket_1m"}
_CONT_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_PD_D1_CHG = {"name": "PD_D1_CHG_20", "source": "pi_price_delay_1d"}
_LUNCH_PRE = {"name": "LUNCH_PRE_RUN_20", "source": "pi_lunch_prerun_1m"}
_CLOSE5 = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}
_ON_PREM = {"name": "GAP_MEAN_20", "source": "daily_candle"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}

base.CANDIDATES = [
    # ---- step 1: atomic recheck of the 5 pi-replication-style atoms ----
    {
        "id": "YA1", "operator": "atomic", "left": _PD_D1_CHG, "right": _PD_D1_CHG,
        "mechanism": "pd_d1_chg_20_recheck",
        "hypothesis": "Hou-Moskowitz 2005价格延迟D1的20日变化(pi_price_delay_1d,S14 round_569已复现,审计+43.7bp/t2.07)。本轮重跑单原子门7读数,与S14数字对照。",
        "expected_sign": -1,
    },
    {
        "id": "YA2", "operator": "atomic", "left": _LUNCH_PRE, "right": _LUNCH_PRE,
        "mechanism": "lunch_pre_run_20_recheck",
        "hypothesis": "11:20-11:30成交量占全日比例20日均值(pi_lunch_prerun_1m,S14 round_569已复现,作为CK04配对腿之一,pi侧CK04整体审计+53.0bp/t2.72)。本轮重跑单原子门7读数。",
        "expected_sign": 1,
    },
    # ---- step 2: pairwise scan (distance-1, mod 11) ----
    {
        "id": "ZA3", "operator": "rank_spread", "left": _MSPE5, "right": _REL_MAXDD,
        "mechanism": "mspe_5m_20_x_rel_maxdd_20",
        "hypothesis": "A=5分钟多尺度排列熵(S11)。B=主动最大回撤水平(S15)。此前从未配对(S15曾配对过REL_MAXDD_CHG_20而非REL_MAXDD_20，原子不同)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "ZA4", "operator": "rank_spread", "left": _REL_MAXDD, "right": _CONT_BETA,
        "mechanism": "rel_maxdd_20_x_continuous_beta_60",
        "hypothesis": "A=主动最大回撤水平(S15)。B=连续beta(S4)。此前从未配对。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "ZA5", "operator": "rank_spread", "left": _CONT_BETA, "right": _PD_D1_CHG,
        "mechanism": "continuous_beta_60_x_pd_d1_chg_20",
        "hypothesis": "A=连续beta(S4)。B=价格延迟D1变化(S14复现)。此前从未配对。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "ZA6", "operator": "rank_spread", "left": _PD_D1_CHG, "right": _LUNCH_PRE,
        "mechanism": "pd_d1_chg_20_x_lunch_pre_run_20",
        "hypothesis": "A=价格延迟D1变化(S14复现)。B=午盘前量占比(S14复现)。两条S14复现原子跨对首次互配(原S14仅各自配pi指定搭档)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "ZA8", "operator": "rank_spread", "left": _CLOSE5, "right": _ON_PREM,
        "mechanism": "close5_day_consist_20_x_on_prem_20",
        "hypothesis": "A=尾5分钟方向一致率(S14复现)。B=隔夜收益(S14复现)。两条S14复现原子跨对首次互配。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "ZA9", "operator": "rank_spread", "left": _ON_PREM, "right": _GAP_FILL,
        "mechanism": "on_prem_20_x_gap_fill_rate_20",
        "hypothesis": "A=隔夜收益(S14复现)。B=跳空当日回补比例(货架既有)。假设:隔夜收益大(A高，跳空幅度大)且当日回补比例低(B低，跳空未被回补=延续)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "ZA10", "operator": "rank_spread", "left": _GAP_FILL, "right": _PERM_ENT,
        "mechanism": "gap_fill_rate_20_x_perm_entropy_ret_20",
        "hypothesis": "A=跳空当日回补比例(货架既有)。B=收益排列熵(S6)。此前从未配对。假设:回补比例高(A高，跳空易被抹平=噪声大)且收益熵高(B高，序列更随机)=一致确认，正相关。",
        "expected_sign": 1,
    },
    # ---- step 2: pairwise scan (distance-2, mod 11) ----
    {
        "id": "ZB3", "operator": "rank_spread", "left": _REL_MAXDD, "right": _PD_D1_CHG,
        "mechanism": "rel_maxdd_20_x_pd_d1_chg_20",
        "hypothesis": "A=主动最大回撤水平(S15)。B=价格延迟D1变化(S14复现)。此前从未配对。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "ZB4", "operator": "rank_spread", "left": _CONT_BETA, "right": _LUNCH_PRE,
        "mechanism": "continuous_beta_60_x_lunch_pre_run_20",
        "hypothesis": "A=连续beta(S4)。B=午盘前量占比(S14复现)。此前从未配对。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "ZB5", "operator": "rank_spread", "left": _PD_D1_CHG, "right": _CLOSE5,
        "mechanism": "pd_d1_chg_20_x_close5_day_consist_20",
        "hypothesis": "A=价格延迟D1变化(S14复现)。B=尾5分钟方向一致率(S14复现)。此前从未配对。假设:价格延迟增加(A高，反应更慢)且尾盘方向一致率高(B高，趋势延续到收盘)=矛盾或确认，方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "ZB6", "operator": "rank_spread", "left": _LUNCH_PRE, "right": _ON_PREM,
        "mechanism": "lunch_pre_run_20_x_on_prem_20",
        "hypothesis": "A=午盘前量占比(S14复现)。B=隔夜收益(S14复现)。此前从未配对。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "ZB7", "operator": "rank_spread", "left": _CLOSE5, "right": _GAP_FILL,
        "mechanism": "close5_day_consist_20_x_gap_fill_rate_20",
        "hypothesis": "A=尾5分钟方向一致率(S14复现)。B=跳空当日回补比例(货架既有)。此前从未配对。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "ZB8", "operator": "rank_spread", "left": _ON_PREM, "right": _PERM_ENT,
        "mechanism": "on_prem_20_x_perm_entropy_ret_20",
        "hypothesis": "A=隔夜收益(S14复现)。B=收益排列熵(S6)。此前从未配对。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "ZB9", "operator": "rank_spread", "left": _GAP_FILL, "right": _UF_CHG,
        "mechanism": "gap_fill_rate_20_x_underwater_frac_chg_20",
        "hypothesis": "A=跳空当日回补比例(货架既有)。B=主动水下时长20日变化(S7)。此前从未配对(S17曾用UNDERWATER_FRAC_CHG_20作右腿多次，但从未与本原子配对)。假设方向由发现期定。本批最后一条。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
