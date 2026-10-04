#!/usr/bin/env python3
"""Round 597 driver: S22 stage step 2 -- lunch_break_1m pairing, round 2.
Two new left-leg batches: LUNCH_PRERUN_POSTRUN_RATIO_20 (already
atomically admitted in round_596 as KA7; atomic admission does not
consume its separate pairing-batch allowance, per this line's S4/S6/S7
precedent) and LUNCH_POST_RUN_20 (second-strongest same-sign atom,
disc+0.0198/audit+0.0441).

Right legs: avoid the atoms round_596 showed cause heavy
rank_correlation_redundancy against AM_PM_RV_RATIO_20 (TRUE_RANGE_
RATIO_20, D1_LEVEL_60, YZ_OVERNIGHT_SHARE_20) and this line's known
'redundancy magnets' from S21 (PERM_ENTROPY_RET_20, CONTINUOUS_BETA_60,
RCOV_N_SHARE_20, MSPE_5M_20, BETA_HF_20); reuse the 5 atoms round_596
tested against AM_PM_RV_RATIO_20 without redundancy issues
(UNDERWATER_FRAC_CHG_20, AD_NET_FLOW_20, COSKEW_20, WORST_DAY_20,
PATH_EFFICIENCY_20) plus fresh atoms for the rest."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_597"

_PRERUN_POSTRUN = {"name": "LUNCH_PRERUN_POSTRUN_RATIO_20", "source": "lunch_break_1m"}
_POST_RUN = {"name": "LUNCH_POST_RUN_20", "source": "lunch_break_1m"}

_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}
_COSKEW20 = {"name": "COSKEW_20", "source": "coskewness_risk"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_PATH_EFF = {"name": "PATH_EFFICIENCY_20", "source": "path_efficiency"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_RECOVERY_FRAC = {"name": "RECOVERY_TIME_FRAC_20", "source": "intraday_pain_recovery_1m"}

_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_VAR_RATIO = {"name": "VAR_RATIO_5_60", "source": "serial_dependence"}
_MAX_DD = {"name": "MAX_DD_20", "source": "downside_risk"}
_SESSION_MEAN = {"name": "SESSION_MEAN_20", "source": "daily_candle"}
_UNDERWATER_RUN = {"name": "UNDERWATER_RUN_60", "source": "drawdown_duration"}
_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_BEST_DAY = {"name": "BEST_DAY_20", "source": "upside_tail"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}

base.CANDIDATES = [
    # ---- LUNCH_PRERUN_POSTRUN_RATIO_20: pairing batch (atomic-admitted KA7, first pairing batch) ----
    {"id": "LA1", "operator": "rank_spread", "left": _PRERUN_POSTRUN, "right": _UF_CHG,
     "mechanism": "lunch_prerun_postrun_confirmed_by_underwater_frac_chg_20",
     "hypothesis": "A=午前/午后抢跑成交量份额之比(round_596原子级入选KA7,t=3.53,+16.8bp)。B=主动水下时长20日变化(S7阶段本线单原子审计最高,intraday_drawdown_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LA2", "operator": "rank_spread", "left": _PRERUN_POSTRUN, "right": _AD_NET_FLOW,
     "mechanism": "lunch_prerun_postrun_confirmed_by_ad_net_flow_20",
     "hypothesis": "A=同上。B=A/D净流20日(S20入选原子搭档,accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LA3", "operator": "rank_spread", "left": _PRERUN_POSTRUN, "right": _COSKEW20,
     "mechanism": "lunch_prerun_postrun_confirmed_by_coskew_20",
     "hypothesis": "A=同上。B=共偏度20日(coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LA4", "operator": "rank_spread", "left": _PRERUN_POSTRUN, "right": _WORST_DAY,
     "mechanism": "lunch_prerun_postrun_confirmed_by_worst_day_20",
     "hypothesis": "A=同上。B=20日最差单日收益(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LA5", "operator": "rank_spread", "left": _PRERUN_POSTRUN, "right": _PATH_EFF,
     "mechanism": "lunch_prerun_postrun_confirmed_by_path_efficiency_20",
     "hypothesis": "A=同上。B=20日路径效率(path_efficiency,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LA6", "operator": "rank_spread", "left": _PRERUN_POSTRUN, "right": _MARKET_BETA20,
     "mechanism": "lunch_prerun_postrun_confirmed_by_market_beta_20",
     "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LA7", "operator": "rank_spread", "left": _PRERUN_POSTRUN, "right": _NOISE_VAR,
     "mechanism": "lunch_prerun_postrun_confirmed_by_noise_var_20",
     "hypothesis": "A=同上。B=微观结构噪声方差(S5阶段,microstructure_noise_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LA8", "operator": "rank_spread", "left": _PRERUN_POSTRUN, "right": _RECOVERY_FRAC,
     "mechanism": "lunch_prerun_postrun_confirmed_by_recovery_time_frac_20",
     "hypothesis": "A=同上。B=日内回撤恢复时间占比(S12阶段,intraday_pain_recovery_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- LUNCH_POST_RUN_20: first pairing batch ----
    {"id": "LB1", "operator": "rank_spread", "left": _POST_RUN, "right": _SAMPEN,
     "mechanism": "lunch_post_run_confirmed_by_sampen_ret_20",
     "hypothesis": "A=13:00-13:10成交量占全日比例(体检disc+0.0198/审计+0.0441同向)。B=收益样本熵(S11阶段,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LB2", "operator": "rank_spread", "left": _POST_RUN, "right": _VAR_RATIO,
     "mechanism": "lunch_post_run_confirmed_by_var_ratio_5_60",
     "hypothesis": "A=同上。B=方差比5/60日(serial_dependence,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LB3", "operator": "rank_spread", "left": _POST_RUN, "right": _MAX_DD,
     "mechanism": "lunch_post_run_confirmed_by_max_dd_20",
     "hypothesis": "A=同上。B=日频最大回撤20日(downside_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LB4", "operator": "rank_spread", "left": _POST_RUN, "right": _SESSION_MEAN,
     "mechanism": "lunch_post_run_confirmed_by_session_mean_20",
     "hypothesis": "A=同上。B=session收益20日均值(daily_candle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LB5", "operator": "rank_spread", "left": _POST_RUN, "right": _UNDERWATER_RUN,
     "mechanism": "lunch_post_run_confirmed_by_underwater_run_60",
     "hypothesis": "A=同上。B=日频最长水下持续期60日(drawdown_duration,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LB6", "operator": "rank_spread", "left": _POST_RUN, "right": _REL_MOM20,
     "mechanism": "lunch_post_run_confirmed_by_rel_market_mom_20",
     "hypothesis": "A=同上。B=相对篮子动量20日(market_relative_strength,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LB7", "operator": "rank_spread", "left": _POST_RUN, "right": _BEST_DAY,
     "mechanism": "lunch_post_run_confirmed_by_best_day_20",
     "hypothesis": "A=同上。B=20日最佳单日收益(upside_tail,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "LB8", "operator": "rank_spread", "left": _POST_RUN, "right": _GAP_FILL,
     "mechanism": "lunch_post_run_confirmed_by_gap_fill_fraction_20",
     "hypothesis": "A=同上。B=跳空当日回补比例20日(gap_repair,S18入选原子搭档,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
