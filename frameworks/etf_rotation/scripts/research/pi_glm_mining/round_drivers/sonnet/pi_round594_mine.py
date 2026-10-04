#!/usr/bin/env python3
"""Round 594 driver: S21 stage step 3 (final atoms) --
overnight_structure_1d pairing, round 3. Uses all 5 remaining atoms as
left legs (ON_PREM_RATIO_20_60, ON_RV_SHARE_60, ON_VOL_ADJ_RET_20 --
all 3 shadow but still pairing-eligible -- plus ON_ABS_MEAN_20 and
ON_PREM_CHG_20), each with a smaller 3-right batch (15 total) to finish
the family's left-leg allowance in one round. After this round all 8
overnight_structure_1d atoms will have used their one legal pairing
batch, so this is the family's last pairing round regardless of
outcome.

Right legs deliberately avoid PERM_ENTROPY_RET_20/CONTINUOUS_BETA_60/
RCOV_N_SHARE_20/MSPE_5M_20/BETA_HF_20 (round_592/593 showed these are
'redundancy magnets' against this family's prior admissions)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_594"

_RATIO = {"name": "ON_PREM_RATIO_20_60", "source": "overnight_structure_1d"}
_RV_SHARE = {"name": "ON_RV_SHARE_60", "source": "overnight_structure_1d"}
_VOL_ADJ = {"name": "ON_VOL_ADJ_RET_20", "source": "overnight_structure_1d"}
_ABS_MEAN = {"name": "ON_ABS_MEAN_20", "source": "overnight_structure_1d"}
_CHG = {"name": "ON_PREM_CHG_20", "source": "overnight_structure_1d"}

_TRR = {"name": "TRUE_RANGE_RATIO_20", "source": "range_contraction_cycle"}
_D1_60 = {"name": "D1_LEVEL_60", "source": "price_delay"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}

_GK_RATIO = {"name": "GK_RV_RATIO_20", "source": "range_based_vol_1m"}
_CLOSE_LOC = {"name": "CLOSE_LOCATION_DAILY", "source": "daily_candle"}
_RECOVERY_FRAC = {"name": "RECOVERY_TIME_FRAC_20", "source": "intraday_pain_recovery_1m"}

_TRACKING_ERR = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}
_DOWNSIDE_COSKEW = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}
_UNDERWATER_RUN = {"name": "UNDERWATER_RUN_60", "source": "drawdown_duration"}

_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_VAR_RATIO = {"name": "VAR_RATIO_5_60", "source": "serial_dependence"}
_MAX_DD = {"name": "MAX_DD_20", "source": "downside_risk"}

_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_PATH_EFF = {"name": "PATH_EFFICIENCY_20", "source": "path_efficiency"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}

base.CANDIDATES = [
    # ---- ON_PREM_RATIO_20_60 (shadow, still eligible) ----
    {"id": "JA1", "operator": "rank_spread", "left": _RATIO, "right": _TRR,
     "mechanism": "on_prem_ratio_confirmed_by_true_range_ratio_20",
     "hypothesis": "A=隔夜收益20/60日均值之比(体检shadow=True vs daily_candle:GAP_MEAN_20,仍可作左腿)。B=真实区间比率(S19唯一净入选原子,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "JA2", "operator": "rank_spread", "left": _RATIO, "right": _D1_60,
     "mechanism": "on_prem_ratio_confirmed_by_d1_level_60",
     "hypothesis": "A=同上。B=价格延迟D1水平(S20入选原子,price_delay,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "JA3", "operator": "rank_spread", "left": _RATIO, "right": _AD_NET_FLOW,
     "mechanism": "on_prem_ratio_confirmed_by_ad_net_flow_20",
     "hypothesis": "A=同上。B=A/D净流20日(S20入选原子搭档,accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- ON_RV_SHARE_60 (shadow, still eligible) ----
    {"id": "JB1", "operator": "rank_spread", "left": _RV_SHARE, "right": _GK_RATIO,
     "mechanism": "on_rv_share_confirmed_by_gk_rv_ratio_20",
     "hypothesis": "A=隔夜方差占总方差比例60日(体检shadow=True vs gap_volatility,仍可作左腿)。B=Garman-Klass与RV比率20日(range_based_vol_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "JB2", "operator": "rank_spread", "left": _RV_SHARE, "right": _CLOSE_LOC,
     "mechanism": "on_rv_share_confirmed_by_close_location_daily",
     "hypothesis": "A=同上。B=当日收盘在区间内位置(daily_candle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "JB3", "operator": "rank_spread", "left": _RV_SHARE, "right": _RECOVERY_FRAC,
     "mechanism": "on_rv_share_confirmed_by_recovery_time_frac_20",
     "hypothesis": "A=同上。B=日内回撤恢复时间占比(S12阶段,intraday_pain_recovery_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- ON_VOL_ADJ_RET_20 (shadow, still eligible) ----
    {"id": "JC1", "operator": "rank_spread", "left": _VOL_ADJ, "right": _TRACKING_ERR,
     "mechanism": "on_vol_adj_ret_confirmed_by_tracking_error_20",
     "hypothesis": "A=首1m bar成交量占比调整后的隔夜收益(体检shadow=True vs daily_candle:GAP_MEAN_20,仍可作左腿)。B=对篮子跟踪误差20日(market_relative_strength,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "JC2", "operator": "rank_spread", "left": _VOL_ADJ, "right": _DOWNSIDE_COSKEW,
     "mechanism": "on_vol_adj_ret_confirmed_by_downside_coskew_60",
     "hypothesis": "A=同上。B=下行共偏度60日(coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "JC3", "operator": "rank_spread", "left": _VOL_ADJ, "right": _UNDERWATER_RUN,
     "mechanism": "on_vol_adj_ret_confirmed_by_underwater_run_60",
     "hypothesis": "A=同上。B=日频最长水下持续期60日(drawdown_duration,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- ON_ABS_MEAN_20 ----
    {"id": "JD1", "operator": "rank_spread", "left": _ABS_MEAN, "right": _SAMPEN,
     "mechanism": "on_abs_mean_confirmed_by_sampen_ret_20",
     "hypothesis": "A=隔夜收益绝对值20日均值(体检disc-0.0061/审计+0.0077接近零)。B=收益样本熵(S11阶段,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "JD2", "operator": "rank_spread", "left": _ABS_MEAN, "right": _VAR_RATIO,
     "mechanism": "on_abs_mean_confirmed_by_var_ratio_5_60",
     "hypothesis": "A=同上。B=方差比5/60日(serial_dependence,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "JD3", "operator": "rank_spread", "left": _ABS_MEAN, "right": _MAX_DD,
     "mechanism": "on_abs_mean_confirmed_by_max_dd_20",
     "hypothesis": "A=同上。B=日频最大回撤20日(downside_risk,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- ON_PREM_CHG_20 ----
    {"id": "JE1", "operator": "rank_spread", "left": _CHG, "right": _WORST_DAY,
     "mechanism": "on_prem_chg_confirmed_by_worst_day_20",
     "hypothesis": "A=隔夜收益20日均值的20日变化(体检disc+0.0191/审计-0.0193反号)。B=20日最差单日收益(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "JE2", "operator": "rank_spread", "left": _CHG, "right": _PATH_EFF,
     "mechanism": "on_prem_chg_confirmed_by_path_efficiency_20",
     "hypothesis": "A=同上。B=20日路径效率(path_efficiency,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "JE3", "operator": "rank_spread", "left": _CHG, "right": _MARKET_BETA20,
     "mechanism": "on_prem_chg_confirmed_by_market_beta_20",
     "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。本批最后一条，overnight_structure_1d 全部8个原子的合法配对将全部用尽。",
     "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
