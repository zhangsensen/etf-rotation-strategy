#!/usr/bin/env python3
"""Round 583 driver: S19 stage step 1 -- range_contraction_cycle family
(Crabel 1990 NR4/NR7; Bollinger 2001 squeeze; Taylor 1986 range
persistence), main controller's pre-specified S19 direction after S18's
closure (round_582), built as a parallel independent implementation
alongside pi lane's stage 32 (not built by reading pi's code).

Atom health (round_583_atom_health, vs range_memory / intraday_
volatility_structure / daily_candle / S9's range_based_vol_1m, all
registered in this catalog): all 8 atoms non-shadow (max |corr| 0.43,
TRUE_RANGE_RATIO_20 vs daily_candle:DAILY_RANGE_PCT). Note the
directive's "range ACF1" bullet duplicated the pre-existing
range_memory:RANGE_ACF1_20 atom and was dropped/replaced with
CONTRACTION_DEPTH_60 (see the family module docstring). BREAKOUT_DIR_
CONSIST_20 (conditional-on-breakout-day observation) has 0 discovery
days -- too sparse to clear the 360-day minimum, tested atomically here
for the record but never used as a pairing left leg (same failure mode
as S17's UP_FIRST_FRAC_20/SIGMA_CROSSING_COUNT_20).
TRUE_RANGE_RATIO_20 is the only atom with same-sign discovery/audit IC
and full 578-day coverage; it is this round's sole left leg for the
first pairing batch."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_583"

_TRR = {"name": "TRUE_RANGE_RATIO_20", "source": "range_contraction_cycle"}
_LRS = {"name": "LOW_RANGE_STREAK_20", "source": "range_contraction_cycle"}
_NR7 = {"name": "NR7_FLAG_FREQ_20", "source": "range_contraction_cycle"}
_DSN = {"name": "DAYS_SINCE_NR7_20", "source": "range_contraction_cycle"}
_BBP = {"name": "BB_WIDTH_PCTL_120", "source": "range_contraction_cycle"}
_BBC = {"name": "BB_WIDTH_CHG_20", "source": "range_contraction_cycle"}
_CD = {"name": "CONTRACTION_DEPTH_60", "source": "range_contraction_cycle"}
_BDC = {"name": "BREAKOUT_DIR_CONSIST_20", "source": "range_contraction_cycle"}

_RCOV_N = {"name": "RCOV_N_SHARE_20", "source": "realized_semicov_1m"}
_PATH_EFF = {"name": "PATH_EFFICIENCY_20", "source": "path_efficiency"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_WICK_IMB = {"name": "WICK_IMBALANCE", "source": "daily_candle"}
_RET_ACF1 = {"name": "RET_ACF1_20", "source": "serial_dependence"}
_ULCER = {"name": "ULCER_20", "source": "downside_risk"}
_UNDERWATER_RUN = {"name": "UNDERWATER_RUN_60", "source": "drawdown_duration"}

base.CANDIDATES = [
    # ---- 8 atomic: new range_contraction_cycle atoms ----
    {
        "id": "AA1", "operator": "atomic", "left": _TRR, "right": _TRR,
        "mechanism": "true_range_ratio_20",
        "hypothesis": "当日真实区间/20日均区间(Wilder TR比率)。体检:disc+0.0155/578天/审计+0.0083(同向)，max|corr|=0.43(vs daily_candle:DAILY_RANGE_PCT)，非shadow。区间扩张(A高)预期延续。",
        "expected_sign": 1,
    },
    {
        "id": "AA2", "operator": "atomic", "left": _LRS, "right": _LRS,
        "mechanism": "low_range_streak_20",
        "hypothesis": "区间低于20日中位数的连续天数(Crabel收缩框架)。体检:disc-0.0466/564天/审计-0.0116(同向)，max|corr|=0.21，非shadow。收缩持续越久(A高)预期越接近突破前夕。",
        "expected_sign": -1,
    },
    {
        "id": "AA3", "operator": "atomic", "left": _NR7, "right": _NR7,
        "mechanism": "nr7_flag_freq_20",
        "hypothesis": "NR7标志20日频率(Crabel 1990)。体检:disc-0.0152/审计+0.0161(反号)，max|corr|=0.14，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "AA4", "operator": "atomic", "left": _DSN, "right": _DSN,
        "mechanism": "days_since_nr7_20",
        "hypothesis": "最近一次NR7距今天数(封顶60)。体检:disc+0.0242/审计-0.0295(反号)，max|corr|=0.21，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "AA5", "operator": "atomic", "left": _BBP, "right": _BBP,
        "mechanism": "bb_width_pctl_120",
        "hypothesis": "Bollinger带宽120日百分位(Bollinger 2001 squeeze)。体检:disc-0.0007/审计+0.0161，接近零，max|corr|=0.17，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "AA6", "operator": "atomic", "left": _BBC, "right": _BBC,
        "mechanism": "bb_width_chg_20",
        "hypothesis": "Bollinger带宽20日变化。体检:disc-0.0344/审计+0.1194(审计强但反号)，max|corr|=0.16，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "AA7", "operator": "atomic", "left": _CD, "right": _CD,
        "mechanism": "contraction_depth_60",
        "hypothesis": "当前20日最小TR在过去60日TR分布中的分位(越高=本轮收缩越深)。体检:disc+0.0195/审计-0.0139(反号)，max|corr|=0.18，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "AA8", "operator": "atomic", "left": _BDC, "right": _BDC,
        "mechanism": "breakout_dir_consist_20",
        "hypothesis": "收缩后首个扩张日(突破日)方向与突破前5日趋势的一致率。体检:disc_days=0(条件观测过于稀疏，未达360天最低发现天数门槛，预计败于discovery_days)，为记录而测，不作后续配对左腿(同S17的UP_FIRST_FRAC_20/SIGMA_CROSSING_COUNT_20失败模式)。",
        "expected_sign": 1,
    },
    # ---- TRUE_RANGE_RATIO_20: first pairing batch (only same-sign disc/audit atom, full coverage) ----
    {
        "id": "AB1", "operator": "rank_spread", "left": _TRR, "right": _RCOV_N,
        "mechanism": "true_range_ratio_confirmed_by_rcov_n_share_20",
        "hypothesis": "A=真实区间比率(区间扩张)。B=同负半协方差份额(S8阶段入选原子RA1，realized_semicov_1m，本族首次配对)。假设:区间扩张(A高)且系统性下行共振高(B高)=一致确认，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "AB2", "operator": "rank_spread", "left": _TRR, "right": _PATH_EFF,
        "mechanism": "true_range_ratio_confirmed_by_path_efficiency_20",
        "hypothesis": "A=同上。B=20日路径效率(path_efficiency，本族首次配对)。假设:区间扩张(A高)且路径效率高(B高，直线突破而非震荡)=一致确认，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "AB3", "operator": "rank_spread", "left": _TRR, "right": _MARKET_BETA20,
        "mechanism": "true_range_ratio_confirmed_by_market_beta_20",
        "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity，本族首次配对)。假设:区间扩张(A高)且系统性beta高(B高，跟随大盘发力)=一致确认，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "AB4", "operator": "rank_spread", "left": _TRR, "right": _REL_MOM20,
        "mechanism": "true_range_ratio_confirmed_by_rel_market_mom_20",
        "hypothesis": "A=同上。B=相对篮子动量20日(market_relative_strength，本族首次配对)。假设:区间扩张(A高)且相对动量强(B高)=一致确认，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "AB5", "operator": "rank_spread", "left": _TRR, "right": _WICK_IMB,
        "mechanism": "true_range_ratio_confirmed_by_wick_imbalance_20",
        "hypothesis": "A=同上。B=日频上下影线不平衡(daily_candle，本族首次作为配对而非仅体检参照)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "AB6", "operator": "rank_spread", "left": _TRR, "right": _RET_ACF1,
        "mechanism": "true_range_ratio_confirmed_by_ret_acf1_20",
        "hypothesis": "A=同上。B=收益一阶自相关20日(serial_dependence，本族首次配对)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "AB7", "operator": "rank_spread", "left": _TRR, "right": _ULCER,
        "mechanism": "true_range_ratio_confirmed_by_ulcer_20",
        "hypothesis": "A=同上。B=日频溃疡指数20日(downside_risk，本族首次配对)。假设:区间扩张(A高)且日频溃疡指数低(B低，历史回撤温和)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "AB8", "operator": "rank_spread", "left": _TRR, "right": _UNDERWATER_RUN,
        "mechanism": "true_range_ratio_confirmed_by_underwater_run_60_20",
        "hypothesis": "A=同上。B=日频最长水下持续期60日(drawdown_duration，本族首次配对)。假设:区间扩张(A高)且水下持续期短(B低)=一致确认，负相关。本批最后一条。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
