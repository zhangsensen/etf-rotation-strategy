#!/usr/bin/env python3
"""Round 579 driver: S17 stage step 3 (final) -- first_passage_times_1m
pairing, round 3. Uses the family's 3 remaining full-sample (>=360
discovery days), never-yet-paired-as-left atoms: PASSAGE_ASYM_20,
FIRST_PASSAGE_UP_CHG_20, FIRST_PASSAGE_DOWN_CHG_20. After this round all
8 atoms will have exhausted their one legal pairing batch each (the two
short-sample atoms UP_FIRST_FRAC_20/SIGMA_CROSSING_COUNT_20 were skipped
as left legs in round_577/578 since they failed their own atomic test on
discovery_days) -- this is therefore the family's last pairing round
regardless of outcome, per the pairing-discipline rule.

Round_577 = 0/16 (redundancy-driven: 4 candidates passed topk_gate but
were killed by rank_correlation_redundancy against prior admissions).
Round_578 = 0/16 (clean zero: no candidate passed topk_gate at all,
t<=1.96 throughout). If this round is also 0, three consecutive
zero-gate-pass rounds triggers the contract's exhaustion clause
regardless of the underlying cause differing each time.

Right legs: batches 1-2 draw fresh (never used as a right leg in S17)
atoms from established families (accumulation_distribution_1m,
realized_semicov_1m, market_sensitivity, daily_candle, serial_dependence,
downside_risk, frequency_domain_beta_1m, intraday_pain_recovery_1m,
coskewness_risk, return_tail_shape, path_efficiency,
market_relative_strength, gap_repair, upside_tail, drawdown_duration).
Batch 3 reuses 8 atoms from round_577/578 (their 2nd use, still under
the 3-lefts-per-right cap) since the fresh-atom well from established
single-digit-atom families is running low relative to 24 total
candidates needed this round."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_579"

_ASYM = {"name": "PASSAGE_ASYM_20", "source": "first_passage_times_1m"}
_UPCHG = {"name": "FIRST_PASSAGE_UP_CHG_20", "source": "first_passage_times_1m"}
_DOWNCHG = {"name": "FIRST_PASSAGE_DOWN_CHG_20", "source": "first_passage_times_1m"}

_AD_PRICE_CORR = {"name": "AD_PRICE_CORR_20", "source": "accumulation_distribution_1m"}
_SEMICOV_UP = {"name": "SEMICOV_UPSIDE_BETA_20", "source": "realized_semicov_1m"}
_MARKET_CORR = {"name": "MARKET_CORR_20", "source": "market_sensitivity"}
_WICK_IMB = {"name": "WICK_IMBALANCE", "source": "daily_candle"}
_VAR_RATIO = {"name": "VAR_RATIO_5_60", "source": "serial_dependence"}
_MAX_DD = {"name": "MAX_DD_20", "source": "downside_risk"}
_BETA_HF = {"name": "BETA_HF_20", "source": "frequency_domain_beta_1m"}
_RECOVERY_FRAC = {"name": "RECOVERY_TIME_FRAC_20", "source": "intraday_pain_recovery_1m"}

_COSKEW_CHG = {"name": "COSKEW_CHG_20", "source": "coskewness_risk"}
_RETURN_SKEW = {"name": "RETURN_SKEW_20", "source": "return_tail_shape"}
_PATH_EFF60 = {"name": "PATH_EFFICIENCY_60", "source": "path_efficiency"}
_TRACKING_ERR = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}
_GAP_FILL20 = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}
_MAX5_MEAN = {"name": "MAX5_MEAN_20", "source": "upside_tail"}
_UNDERWATER_RUN = {"name": "UNDERWATER_RUN_60", "source": "drawdown_duration"}
_RCOV_P = {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"}

_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENT = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_CONT_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_MSPE5 = {"name": "MSPE_5M_20", "source": "complexity_measures_1m"}
_RCOV_N = {"name": "RCOV_N_SHARE_20", "source": "realized_semicov_1m"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_BEST_DAY = {"name": "BEST_DAY_20", "source": "upside_tail"}

base.CANDIDATES = [
    # ---- PASSAGE_ASYM_20: first pairing batch ----
    {"id": "XA1", "operator": "rank_spread", "left": _ASYM, "right": _AD_PRICE_CORR,
     "mechanism": "passage_asym_confirmed_by_ad_price_corr_20",
     "hypothesis": "A=下行首达-上行首达(方向性首达不对称,体检disc-0.0344/审计-0.0128,同向)。B=A/D净流与当日收益的20日相关(accumulation_distribution_1m,S10阶段,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "XA2", "operator": "rank_spread", "left": _ASYM, "right": _SEMICOV_UP,
     "mechanism": "passage_asym_confirmed_by_semicov_upside_beta_20",
     "hypothesis": "A=同上。B=对篮子上行半协方差beta(realized_semicov_1m,S8阶段,本族首次配对)。假设:A大(上行更易触发)且上行beta高(B高,跟随大盘上涨更敏感)=一致确认，负相关。",
     "expected_sign": -1},
    {"id": "XA3", "operator": "rank_spread", "left": _ASYM, "right": _MARKET_CORR,
     "mechanism": "passage_asym_confirmed_by_market_corr_20",
     "hypothesis": "A=同上。B=对篮子相关性20日(market_sensitivity,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "XA4", "operator": "rank_spread", "left": _ASYM, "right": _WICK_IMB,
     "mechanism": "passage_asym_confirmed_by_wick_imbalance_20",
     "hypothesis": "A=同上。B=日频上下影线不平衡(daily_candle,本族首次配对)。假设:A大(日内偏上行)且日频影线也偏多头形态(B高)=一致确认，负相关。",
     "expected_sign": -1},
    {"id": "XA5", "operator": "rank_spread", "left": _ASYM, "right": _VAR_RATIO,
     "mechanism": "passage_asym_confirmed_by_var_ratio_5_60_20",
     "hypothesis": "A=同上。B=方差比5/60日(serial_dependence,本族首次配对)。假设方向由发现期定，二者均刻画路径的趋势/均值回归特征。",
     "expected_sign": 1},
    {"id": "XA6", "operator": "rank_spread", "left": _ASYM, "right": _MAX_DD,
     "mechanism": "passage_asym_confirmed_by_max_dd_20",
     "hypothesis": "A=同上。B=日频最大回撤20日(downside_risk,本族首次配对)。假设:A大(上行更易触发)且日频回撤浅(B浅,即回撤值小)=一致确认，负相关(回撤值越小信号越弱，需按实际符号定义核实)。",
     "expected_sign": -1},
    {"id": "XA7", "operator": "rank_spread", "left": _ASYM, "right": _BETA_HF,
     "mechanism": "passage_asym_confirmed_by_beta_hf_20",
     "hypothesis": "A=同上。B=高频带beta20日(frequency_domain_beta_1m,S13阶段,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "XA8", "operator": "rank_spread", "left": _ASYM, "right": _RECOVERY_FRAC,
     "mechanism": "passage_asym_confirmed_by_recovery_time_frac_20",
     "hypothesis": "A=同上。B=日内回撤恢复时间占比(intraday_pain_recovery_1m,S12阶段,本族首次配对)。假设:A大(上行更易触发)且恢复快(B低)=一致确认，负相关。本批最后一条。",
     "expected_sign": -1},
    # ---- FIRST_PASSAGE_UP_CHG_20: first pairing batch ----
    {"id": "XB1", "operator": "rank_spread", "left": _UPCHG, "right": _COSKEW_CHG,
     "mechanism": "first_passage_up_chg_confirmed_by_coskew_chg_20",
     "hypothesis": "A=上行首达时间的20日变化(体检disc-0.0084/审计-0.0378,同向)。B=共偏度20日变化(coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "XB2", "operator": "rank_spread", "left": _UPCHG, "right": _RETURN_SKEW,
     "mechanism": "first_passage_up_chg_confirmed_by_return_skew_20",
     "hypothesis": "A=同上。B=收益偏度20日(return_tail_shape,本族首次配对)。假设:A升高(上行首达变慢,动量减弱)且偏度下降(B降,右尾变薄)=一致确认，正相关。",
     "expected_sign": 1},
    {"id": "XB3", "operator": "rank_spread", "left": _UPCHG, "right": _PATH_EFF60,
     "mechanism": "first_passage_up_chg_confirmed_by_path_efficiency_60_20",
     "hypothesis": "A=同上。B=60日路径效率(path_efficiency,本族首次配对)。假设:A升高(动量减弱)且路径效率下降(B降)=一致确认，正相关。",
     "expected_sign": 1},
    {"id": "XB4", "operator": "rank_spread", "left": _UPCHG, "right": _TRACKING_ERR,
     "mechanism": "first_passage_up_chg_confirmed_by_tracking_error_20",
     "hypothesis": "A=同上。B=对篮子跟踪误差20日(market_relative_strength,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XB5", "operator": "rank_spread", "left": _UPCHG, "right": _GAP_FILL20,
     "mechanism": "first_passage_up_chg_confirmed_by_gap_fill_fraction_20_20",
     "hypothesis": "A=同上。B=缺口回补比例20日(gap_repair,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "XB6", "operator": "rank_spread", "left": _UPCHG, "right": _MAX5_MEAN,
     "mechanism": "first_passage_up_chg_confirmed_by_max5_mean_20_20",
     "hypothesis": "A=同上。B=最大5日均值(upside_tail,本族首次配对)。假设:A升高(上行动量减弱)且近期最大5日均值走弱(B低)=一致确认，负相关。",
     "expected_sign": -1},
    {"id": "XB7", "operator": "rank_spread", "left": _UPCHG, "right": _UNDERWATER_RUN,
     "mechanism": "first_passage_up_chg_confirmed_by_underwater_run_60_20",
     "hypothesis": "A=同上。B=日频最长水下持续期60日(drawdown_duration,本族首次配对)。假设:A升高(动量减弱)且水下持续期变长(B高)=一致确认，负相关。",
     "expected_sign": -1},
    {"id": "XB8", "operator": "rank_spread", "left": _UPCHG, "right": _RCOV_P,
     "mechanism": "first_passage_up_chg_confirmed_by_rcov_p_share_20_20",
     "hypothesis": "A=同上。B=同正半协方差份额20日(realized_semicov_1m,与XA2用过的SEMICOV_UPSIDE_BETA_20为同族不同原子,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- FIRST_PASSAGE_DOWN_CHG_20: final pairing batch (S17's last, reuses S17 rights at their 2nd use) ----
    {"id": "XC1", "operator": "rank_spread", "left": _DOWNCHG, "right": _UF_CHG,
     "mechanism": "first_passage_down_chg_confirmed_by_underwater_frac_chg_20",
     "hypothesis": "A=下行首达时间的20日变化(体检disc+0.0189/审计-0.0371,反号)。B=主动水下时长20日变化(intraday_drawdown_1m,round_577已配过一次UP_20，本轮为第2次使用，仍在≤3lefts上限内)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XC2", "operator": "rank_spread", "left": _DOWNCHG, "right": _PERM_ENT,
     "mechanism": "first_passage_down_chg_confirmed_by_perm_entropy_ret_20",
     "hypothesis": "A=同上。B=收益排列熵(permutation_entropy_1m，第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "XC3", "operator": "rank_spread", "left": _DOWNCHG, "right": _CONT_BETA,
     "mechanism": "first_passage_down_chg_confirmed_by_continuous_beta_60_20",
     "hypothesis": "A=同上。B=对篮子连续beta(jump_continuous_beta，第2次使用)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XC4", "operator": "rank_spread", "left": _DOWNCHG, "right": _MSPE5,
     "mechanism": "first_passage_down_chg_confirmed_by_mspe_5m_20_20",
     "hypothesis": "A=同上。B=5分钟多尺度排列熵(complexity_measures_1m，第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "XC5", "operator": "rank_spread", "left": _DOWNCHG, "right": _RCOV_N,
     "mechanism": "first_passage_down_chg_confirmed_by_rcov_n_share_20_20",
     "hypothesis": "A=同上。B=同负半协方差份额(realized_semicov_1m，本轮第3次出现该家族但不同原子，此原子为第2次使用)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XC6", "operator": "rank_spread", "left": _DOWNCHG, "right": _WORST_DAY,
     "mechanism": "first_passage_down_chg_confirmed_by_worst_day_20_20",
     "hypothesis": "A=同上。B=20日最差单日收益(return_tail_shape，第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "XC7", "operator": "rank_spread", "left": _DOWNCHG, "right": _MARKET_BETA20,
     "mechanism": "first_passage_down_chg_confirmed_by_market_beta_20_20",
     "hypothesis": "A=同上。B=对篮子beta(market_sensitivity，第2次使用)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "XC8", "operator": "rank_spread", "left": _DOWNCHG, "right": _BEST_DAY,
     "mechanism": "first_passage_down_chg_confirmed_by_best_day_20_20",
     "hypothesis": "A=同上。B=20日最佳单日收益(upside_tail，第2次使用)。假设方向由发现期定。本批最后一条，first_passage_times_1m 全部8个原子的合法配对将全部用尽。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
