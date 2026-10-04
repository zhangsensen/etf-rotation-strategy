#!/usr/bin/env python3
"""Round 588 driver: S20 stage step 2 -- price_delay pairing, round 2.
Two new left-leg batches: D1_LEVEL_60 (second-strongest same-sign atom,
disc+0.0569/audit+0.0722, full 578-day coverage) and D2_LAGSHARE_60
(third same-sign atom, disc+0.0499/audit+0.0612). Deliberately limited
to 2 new left legs (5 remain: LAG1_COEF_60 [shadow, still usable as
left], LAG_COEF_SIGN_FREQ_20, D2_LAGSHARE_CHG_20 [shadow], D1_1M_CHG_20,
D1_DIFF_1D_1M_20), learning from S18's over-spending mistake."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_588"

_D1_60 = {"name": "D1_LEVEL_60", "source": "price_delay"}
_D2_60 = {"name": "D2_LAGSHARE_60", "source": "price_delay"}

_RCOV_N = {"name": "RCOV_N_SHARE_20", "source": "realized_semicov_1m"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_PATH_EFF = {"name": "PATH_EFFICIENCY_20", "source": "path_efficiency"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENT = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_YZ_OVN = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_MSPE5 = {"name": "MSPE_5M_20", "source": "complexity_measures_1m"}

_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_ULCER = {"name": "ULCER_20", "source": "downside_risk"}
_WICK_IMB = {"name": "WICK_IMBALANCE", "source": "daily_candle"}
_UNDERWATER_RUN = {"name": "UNDERWATER_RUN_60", "source": "drawdown_duration"}
_CONT_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}
_TRR = {"name": "TRUE_RANGE_RATIO_20", "source": "range_contraction_cycle"}
_BEST_DAY = {"name": "BEST_DAY_20", "source": "upside_tail"}

base.CANDIDATES = [
    # ---- D1_LEVEL_60: first pairing batch ----
    {"id": "EA1", "operator": "rank_spread", "left": _D1_60, "right": _RCOV_N,
     "mechanism": "d1_level_confirmed_by_rcov_n_share_20",
     "hypothesis": "A=D1水平值(体检disc+0.0569/审计+0.0722同向,578天)。B=同负半协方差份额(S8入选原子,realized_semicov_1m,本族首次配对)。假设:延迟大(A高)且系统性同跌集中度高(B高)=一致确认，负相关(延迟大且系统共振时未来收益更弱)。",
     "expected_sign": -1},
    {"id": "EA2", "operator": "rank_spread", "left": _D1_60, "right": _WORST_DAY,
     "mechanism": "d1_level_confirmed_by_worst_day_20",
     "hypothesis": "A=同上。B=20日最差单日收益(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "EA3", "operator": "rank_spread", "left": _D1_60, "right": _PATH_EFF,
     "mechanism": "d1_level_confirmed_by_path_efficiency_20",
     "hypothesis": "A=同上。B=20日路径效率(path_efficiency,本族首次配对)。假设:延迟大(A高)且路径效率低(B低,震荡而非趋势)=一致确认，负相关。",
     "expected_sign": -1},
    {"id": "EA4", "operator": "rank_spread", "left": _D1_60, "right": _MARKET_BETA20,
     "mechanism": "d1_level_confirmed_by_market_beta_20",
     "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "EA5", "operator": "rank_spread", "left": _D1_60, "right": _UF_CHG,
     "mechanism": "d1_level_confirmed_by_underwater_frac_chg_20",
     "hypothesis": "A=同上。B=主动水下时长20日变化(S7阶段本线单原子审计最高,intraday_drawdown_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "EA6", "operator": "rank_spread", "left": _D1_60, "right": _PERM_ENT,
     "mechanism": "d1_level_confirmed_by_perm_entropy_ret_20",
     "hypothesis": "A=同上。B=收益排列熵(S6阶段,permutation_entropy_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "EA7", "operator": "rank_spread", "left": _D1_60, "right": _YZ_OVN,
     "mechanism": "d1_level_confirmed_by_yz_overnight_share_20",
     "hypothesis": "A=同上。B=Yang-Zhang隔夜份额(S9阶段配对最高t原子,range_based_vol_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "EA8", "operator": "rank_spread", "left": _D1_60, "right": _MSPE5,
     "mechanism": "d1_level_confirmed_by_mspe_5m_20",
     "hypothesis": "A=同上。B=5分钟多尺度排列熵(S11阶段,complexity_measures_1m,本族首次配对,与round_587用过的RECURRENCE_RATE_20同族不同原子)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- D2_LAGSHARE_60: first pairing batch ----
    {"id": "EB1", "operator": "rank_spread", "left": _D2_60, "right": _REL_MOM20,
     "mechanism": "d2_lagshare_confirmed_by_rel_market_mom_20",
     "hypothesis": "A=D2滞后系数份额(体检disc+0.0499/审计+0.0612同向)。B=相对篮子动量20日(market_relative_strength,本族首次配对)。假设:延迟大(A高)且相对动量弱(B低)=一致确认，负相关。",
     "expected_sign": -1},
    {"id": "EB2", "operator": "rank_spread", "left": _D2_60, "right": _ULCER,
     "mechanism": "d2_lagshare_confirmed_by_ulcer_20",
     "hypothesis": "A=同上。B=日频溃疡指数20日(downside_risk,与round_587用过的DOWNSIDE_DEV_20同族不同原子,本族首次配对)。假设:延迟大(A高)且溃疡指数高(B高)=一致确认，正相关。",
     "expected_sign": 1},
    {"id": "EB3", "operator": "rank_spread", "left": _D2_60, "right": _WICK_IMB,
     "mechanism": "d2_lagshare_confirmed_by_wick_imbalance_20",
     "hypothesis": "A=同上。B=日频上下影线不平衡(daily_candle,与round_587用过的SESSION_MEAN_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "EB4", "operator": "rank_spread", "left": _D2_60, "right": _UNDERWATER_RUN,
     "mechanism": "d2_lagshare_confirmed_by_underwater_run_60",
     "hypothesis": "A=同上。B=日频最长水下持续期60日(drawdown_duration,本族首次配对)。假设:延迟大(A高)且水下持续期长(B高)=一致确认，正相关。",
     "expected_sign": 1},
    {"id": "EB5", "operator": "rank_spread", "left": _D2_60, "right": _CONT_BETA,
     "mechanism": "d2_lagshare_confirmed_by_continuous_beta_60",
     "hypothesis": "A=同上。B=对篮子连续beta(S4阶段,jump_continuous_beta,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "EB6", "operator": "rank_spread", "left": _D2_60, "right": _GAP_FILL,
     "mechanism": "d2_lagshare_confirmed_by_gap_fill_fraction_20",
     "hypothesis": "A=同上。B=跳空当日回补比例20日(gap_repair,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "EB7", "operator": "rank_spread", "left": _D2_60, "right": _TRR,
     "mechanism": "d2_lagshare_confirmed_by_true_range_ratio_20",
     "hypothesis": "A=同上。B=真实区间比率(S19唯一净入选原子,range_contraction_cycle,本族首次配对)。假设:延迟大(A高)且区间扩张(B高,系统共振/信息集中释放)=一致确认，正相关。",
     "expected_sign": 1},
    {"id": "EB8", "operator": "rank_spread", "left": _D2_60, "right": _BEST_DAY,
     "mechanism": "d2_lagshare_confirmed_by_best_day_20",
     "hypothesis": "A=同上。B=20日最佳单日收益(upside_tail,与round_587用过的MAX5_MEAN_20同族不同原子,本族首次配对)。假设:延迟大(A高)且近期缺乏强势上行日(B低)=一致确认，负相关。本批最后一条。",
     "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
