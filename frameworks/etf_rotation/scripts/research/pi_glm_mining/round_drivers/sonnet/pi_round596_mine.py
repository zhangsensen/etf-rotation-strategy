#!/usr/bin/env python3
"""Round 596 driver: S22 stage step 1 -- lunch_break_1m family
(Barclay-Hendershott 2003/2004 price discovery around trading halts;
Hong-Wang 2000 periodic-closure volatility asymmetry), main controller's
pre-specified S22 direction after S21's closure (round_595), built as a
parallel independent implementation alongside pi lane's stage 18, its
densest stage (14 admissions) -- not built by reading pi's code.

Atom health (round_596_atom_health, vs intraday_periodicity, intraday_
turnover_shape, intraday_volatility_structure, pi_lunch_prerun_1m,
intraday_return_path, all registered in this catalog): all 8 atoms
non-shadow (max |corr| 0.58). AM_PM_RV_RATIO_20 has the strongest same-
sign discovery/audit IC (disc-0.0943/audit-0.0861, full 579-day
coverage) and is this round's sole left leg for the first pairing
batch, per the pairing-discipline rule -- deliberately limited to 1 new
left leg (7 remain for future rounds). LUNCH_GAP_FILL_15M_20 has only
315 discovery days (conditional-on-nontrivial-gap observation, same
failure mode as S17/S19's sparse atoms) -- tested atomically for the
record but expected to fail discovery_days and never used as a left
leg."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_596"

_GAP = {"name": "LUNCH_GAP_20", "source": "lunch_break_1m"}
_GAP_ABS = {"name": "LUNCH_GAP_ABS_20", "source": "lunch_break_1m"}
_GAP_CHG = {"name": "LUNCH_GAP_CHG_20", "source": "lunch_break_1m"}
_GAP_FILL = {"name": "LUNCH_GAP_FILL_15M_20", "source": "lunch_break_1m"}
_RV_RATIO = {"name": "AM_PM_RV_RATIO_20", "source": "lunch_break_1m"}
_POST_RUN = {"name": "LUNCH_POST_RUN_20", "source": "lunch_break_1m"}
_PRERUN_POSTRUN = {"name": "LUNCH_PRERUN_POSTRUN_RATIO_20", "source": "lunch_break_1m"}
_RET_CORR = {"name": "AM_PM_RET_CORR_20", "source": "lunch_break_1m"}

_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_TRR = {"name": "TRUE_RANGE_RATIO_20", "source": "range_contraction_cycle"}
_D1_60 = {"name": "D1_LEVEL_60", "source": "price_delay"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}
_YZ_OVN = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_COSKEW20 = {"name": "COSKEW_20", "source": "coskewness_risk"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_PATH_EFF = {"name": "PATH_EFFICIENCY_20", "source": "path_efficiency"}

base.CANDIDATES = [
    # ---- 8 atomic: new lunch_break_1m atoms ----
    {
        "id": "KA1", "operator": "atomic", "left": _GAP, "right": _GAP,
        "mechanism": "lunch_gap_20",
        "hypothesis": "午间跳空(13:00首bar开/11:30收-1)20日均值。体检:disc+0.0126/审计+0.0101(同向)，max|corr|=0.16，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "KA2", "operator": "atomic", "left": _GAP_ABS, "right": _GAP_ABS,
        "mechanism": "lunch_gap_abs_20",
        "hypothesis": "午间跳空绝对值20日均值(幅度维度)。体检:disc-0.0239/审计-0.0234(同向)，max|corr|=0.46，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "KA3", "operator": "atomic", "left": _GAP_CHG, "right": _GAP_CHG,
        "mechanism": "lunch_gap_chg_20",
        "hypothesis": "午间跳空20日均值的20日变化。体检:disc+0.0174/审计+0.0128(同向)，max|corr|=0.16，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "KA4", "operator": "atomic", "left": _GAP_FILL, "right": _GAP_FILL,
        "mechanism": "lunch_gap_fill_15m_20",
        "hypothesis": "午间跳空后15分钟内回补比例20日均值(条件于非零跳空日)。体检:disc_days=315(条件观测稀疏，预计未达360天最低发现天数门槛)，为记录而测，不作后续配对左腿(同S17/S19失败模式)。",
        "expected_sign": 1,
    },
    {
        "id": "KA5", "operator": "atomic", "left": _RV_RATIO, "right": _RV_RATIO,
        "mechanism": "am_pm_rv_ratio_20",
        "hypothesis": "上午RV/下午RV比率20日均值(Hong-Wang 2000周期性休市)。体检:disc-0.0943/审计-0.0861(同向,本族最强)，579天覆盖，max|corr|=0.58，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "KA6", "operator": "atomic", "left": _POST_RUN, "right": _POST_RUN,
        "mechanism": "lunch_post_run_20",
        "hypothesis": "13:00-13:10成交量占全日比例20日均值(对称于既有LUNCH_PRE_RUN_20)。体检:disc+0.0198/审计+0.0441(同向增强)，max|corr|=0.21，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "KA7", "operator": "atomic", "left": _PRERUN_POSTRUN, "right": _PRERUN_POSTRUN,
        "mechanism": "lunch_prerun_postrun_ratio_20",
        "hypothesis": "午前抢跑/午后抢跑成交量份额之比20日均值。体检:disc+0.0528/审计+0.0456(同向)，max|corr|=0.48(vs既有pi_lunch_prerun_1m:LUNCH_PRE_RUN_20，未达shadow)，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "KA8", "operator": "atomic", "left": _RET_CORR, "right": _RET_CORR,
        "mechanism": "am_pm_ret_corr_20",
        "hypothesis": "上午收益与下午收益的20日滚动相关(跨日持续性，区别于既有同日MORNING_AFTERNOON_SPREAD水平)。体检:disc-0.0089/审计-0.0310(同向弱)，max|corr|=0.19，非shadow。",
        "expected_sign": -1,
    },
    # ---- AM_PM_RV_RATIO_20: first pairing batch (strongest same-sign atom, full coverage) ----
    {
        "id": "KB1", "operator": "rank_spread", "left": _RV_RATIO, "right": _UF_CHG,
        "mechanism": "am_pm_rv_ratio_confirmed_by_underwater_frac_chg_20",
        "hypothesis": "A=上午RV/下午RV比率(A低=下午波动主导)。B=主动水下时长20日变化(S7阶段本线单原子审计最高,intraday_drawdown_1m,本族首次配对)。假设方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "KB2", "operator": "rank_spread", "left": _RV_RATIO, "right": _TRR,
        "mechanism": "am_pm_rv_ratio_confirmed_by_true_range_ratio_20",
        "hypothesis": "A=同上。B=真实区间比率(S19唯一净入选原子,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "KB3", "operator": "rank_spread", "left": _RV_RATIO, "right": _D1_60,
        "mechanism": "am_pm_rv_ratio_confirmed_by_d1_level_60",
        "hypothesis": "A=同上。B=价格延迟D1水平(S20入选原子,price_delay,本族首次配对)。假设方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "KB4", "operator": "rank_spread", "left": _RV_RATIO, "right": _AD_NET_FLOW,
        "mechanism": "am_pm_rv_ratio_confirmed_by_ad_net_flow_20",
        "hypothesis": "A=同上。B=A/D净流20日(S20入选原子搭档,accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "KB5", "operator": "rank_spread", "left": _RV_RATIO, "right": _YZ_OVN,
        "mechanism": "am_pm_rv_ratio_confirmed_by_yz_overnight_share_20",
        "hypothesis": "A=同上。B=Yang-Zhang隔夜份额(S9阶段配对最高t原子,range_based_vol_1m,本族首次配对)。假设方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "KB6", "operator": "rank_spread", "left": _RV_RATIO, "right": _COSKEW20,
        "mechanism": "am_pm_rv_ratio_confirmed_by_coskew_20",
        "hypothesis": "A=同上。B=共偏度20日(coskewness_risk,本族首次配对)。假设方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "KB7", "operator": "rank_spread", "left": _RV_RATIO, "right": _WORST_DAY,
        "mechanism": "am_pm_rv_ratio_confirmed_by_worst_day_20",
        "hypothesis": "A=同上。B=20日最差单日收益(return_tail_shape,本族首次配对)。假设方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "KB8", "operator": "rank_spread", "left": _RV_RATIO, "right": _PATH_EFF,
        "mechanism": "am_pm_rv_ratio_confirmed_by_path_efficiency_20",
        "hypothesis": "A=同上。B=20日路径效率(path_efficiency,本族首次配对)。假设方向由发现期定。本批最后一条。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
