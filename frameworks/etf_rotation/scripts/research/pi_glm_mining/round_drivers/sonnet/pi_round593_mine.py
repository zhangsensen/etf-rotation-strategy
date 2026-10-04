#!/usr/bin/env python3
"""Round 593 driver: S21 stage step 2 -- overnight_structure_1d pairing,
round 2. Two new left-leg batches: ON_INTRADAY_CORR_20 (best-remaining
same-sign atom, disc+0.0154/audit+0.0372) and ON_PREM_SKEW_20 (strongest
remaining raw discovery IC despite a sign flip, disc+0.0176/audit
-0.0205). Deliberately limited to 2 new left legs (5 remain: ON_PREM_
RATIO_20_60 [shadow], ON_RV_SHARE_60 [shadow], ON_VOL_ADJ_RET_20
[shadow], ON_ABS_MEAN_20, ON_PREM_CHG_20).

Right legs: 16 total, deliberately AVOIDING PERM_ENTROPY_RET_20/
CONTINUOUS_BETA_60/RCOV_N_SHARE_20/MSPE_5M_20 (round_592's
ON_SIGN_STREAK_20 batch showed these 4 produce heavy rank_correlation_
redundancy against prior admissions when paired with an overnight-
structure left leg) to diversify and test whether that redundancy is
atom-specific (ON_SIGN_STREAK_20) or a general property of this
family's overlap with those 4 atoms."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_593"

_CORR = {"name": "ON_INTRADAY_CORR_20", "source": "overnight_structure_1d"}
_SKEW = {"name": "ON_PREM_SKEW_20", "source": "overnight_structure_1d"}

_YZ_OVN = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}
_COSKEW20 = {"name": "COSKEW_20", "source": "coskewness_risk"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_PATH_EFF = {"name": "PATH_EFFICIENCY_20", "source": "path_efficiency"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_BETA_HF = {"name": "BETA_HF_20", "source": "frequency_domain_beta_1m"}
_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}

_RCOV_P = {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"}
_VAR_RATIO = {"name": "VAR_RATIO_5_60", "source": "serial_dependence"}
_MAX_DD = {"name": "MAX_DD_20", "source": "downside_risk"}
_SESSION_MEAN = {"name": "SESSION_MEAN_20", "source": "daily_candle"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_UNDERWATER_RUN = {"name": "UNDERWATER_RUN_60", "source": "drawdown_duration"}
_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_BEST_DAY = {"name": "BEST_DAY_20", "source": "upside_tail"}

base.CANDIDATES = [
    # ---- ON_INTRADAY_CORR_20: first pairing batch ----
    {"id": "IA1", "operator": "rank_spread", "left": _CORR, "right": _YZ_OVN,
     "mechanism": "on_intraday_corr_confirmed_by_yz_overnight_share_20",
     "hypothesis": "A=隔夜收益与当日日内收益的20日相关(体检disc+0.0154/审计+0.0372同向,579天)。B=Yang-Zhang隔夜份额(S9阶段配对最高t原子,range_based_vol_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "IA2", "operator": "rank_spread", "left": _CORR, "right": _GAP_FILL,
     "mechanism": "on_intraday_corr_confirmed_by_gap_fill_fraction_20",
     "hypothesis": "A=同上。B=跳空当日回补比例20日(gap_repair,S18入选原子搭档,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "IA3", "operator": "rank_spread", "left": _CORR, "right": _COSKEW20,
     "mechanism": "on_intraday_corr_confirmed_by_coskew_20",
     "hypothesis": "A=同上。B=共偏度20日(coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "IA4", "operator": "rank_spread", "left": _CORR, "right": _WORST_DAY,
     "mechanism": "on_intraday_corr_confirmed_by_worst_day_20",
     "hypothesis": "A=同上。B=20日最差单日收益(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "IA5", "operator": "rank_spread", "left": _CORR, "right": _PATH_EFF,
     "mechanism": "on_intraday_corr_confirmed_by_path_efficiency_20",
     "hypothesis": "A=同上。B=20日路径效率(path_efficiency,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "IA6", "operator": "rank_spread", "left": _CORR, "right": _MARKET_BETA20,
     "mechanism": "on_intraday_corr_confirmed_by_market_beta_20",
     "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "IA7", "operator": "rank_spread", "left": _CORR, "right": _BETA_HF,
     "mechanism": "on_intraday_corr_confirmed_by_beta_hf_20",
     "hypothesis": "A=同上。B=高频带beta20日(S20入选原子,frequency_domain_beta_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "IA8", "operator": "rank_spread", "left": _CORR, "right": _NOISE_VAR,
     "mechanism": "on_intraday_corr_confirmed_by_noise_var_20",
     "hypothesis": "A=同上。B=微观结构噪声方差(S5阶段,microstructure_noise_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- ON_PREM_SKEW_20: first pairing batch ----
    {"id": "IB1", "operator": "rank_spread", "left": _SKEW, "right": _RCOV_P,
     "mechanism": "on_prem_skew_confirmed_by_rcov_p_share_20",
     "hypothesis": "A=隔夜收益20日偏度(体检disc+0.0176/审计-0.0205反号)。B=同正半协方差份额(realized_semicov_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "IB2", "operator": "rank_spread", "left": _SKEW, "right": _VAR_RATIO,
     "mechanism": "on_prem_skew_confirmed_by_var_ratio_5_60",
     "hypothesis": "A=同上。B=方差比5/60日(serial_dependence,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "IB3", "operator": "rank_spread", "left": _SKEW, "right": _MAX_DD,
     "mechanism": "on_prem_skew_confirmed_by_max_dd_20",
     "hypothesis": "A=同上。B=日频最大回撤20日(downside_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "IB4", "operator": "rank_spread", "left": _SKEW, "right": _SESSION_MEAN,
     "mechanism": "on_prem_skew_confirmed_by_session_mean_20",
     "hypothesis": "A=同上。B=session收益20日均值(daily_candle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "IB5", "operator": "rank_spread", "left": _SKEW, "right": _SAMPEN,
     "mechanism": "on_prem_skew_confirmed_by_sampen_ret_20",
     "hypothesis": "A=同上。B=收益样本熵(S11阶段,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "IB6", "operator": "rank_spread", "left": _SKEW, "right": _UNDERWATER_RUN,
     "mechanism": "on_prem_skew_confirmed_by_underwater_run_60",
     "hypothesis": "A=同上。B=日频最长水下持续期60日(drawdown_duration,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "IB7", "operator": "rank_spread", "left": _SKEW, "right": _REL_MOM20,
     "mechanism": "on_prem_skew_confirmed_by_rel_market_mom_20",
     "hypothesis": "A=同上。B=相对篮子动量20日(market_relative_strength,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "IB8", "operator": "rank_spread", "left": _SKEW, "right": _BEST_DAY,
     "mechanism": "on_prem_skew_confirmed_by_best_day_20",
     "hypothesis": "A=同上。B=20日最佳单日收益(upside_tail,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
