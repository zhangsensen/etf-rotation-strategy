#!/usr/bin/env python3
"""Round 584 driver: S19 stage step 2 -- range_contraction_cycle
pairing, round 2. Two new left-leg batches: BB_WIDTH_CHG_20 (this
family's strongest audit IC, +0.1194, though its discovery sign flips)
and LOW_RANGE_STREAK_20 (second atom with same-sign discovery/audit,
after TRUE_RANGE_RATIO_20 used in round_583). Deliberately limited to
2 new left legs this round (not all 6 remaining eligible atoms) --
learning from round_581/582's S18 mistake of spending most of a pool's
left-batch allowance in a single round and leaving the stage
under-12-candidates exhausted after only 2 rounds. 4 atoms remain
reserved for a possible round 3 (NR7_FLAG_FREQ_20, DAYS_SINCE_NR7_20,
BB_WIDTH_PCTL_120, CONTRACTION_DEPTH_60).

Right legs: 16 total, 15 distinct families (no repeats WITHIN either
batch), mostly atoms never yet paired against this family
(round_583 used RCOV_N_SHARE_20/PATH_EFFICIENCY_20/MARKET_BETA_20/
REL_MARKET_MOM_20/WICK_IMBALANCE/RET_ACF1_20/ULCER_20/
UNDERWATER_RUN_60 -- this round picks different atoms, several from the
SAME families via a different specific atom, to diversify right-leg
coverage without violating any rule (family reuse across different
left batches is permitted; only same-family-within-one-batch is
forbidden)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_584"

_BBC = {"name": "BB_WIDTH_CHG_20", "source": "range_contraction_cycle"}
_LRS = {"name": "LOW_RANGE_STREAK_20", "source": "range_contraction_cycle"}

_DOWNSIDE_COSKEW = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}
_OVERNIGHT_GAP = {"name": "OVERNIGHT_GAP", "source": "daily_candle"}
_MFI14 = {"name": "MFI_14_MEAN_20", "source": "accumulation_distribution_1m"}
_YZ_OVN = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_COHERENCE = {"name": "COHERENCE_LF_HF_DIFF_20", "source": "frequency_domain_beta_1m"}
_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_TRACKING_ERR = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}

_RCOV_P = {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"}
_VAR_RATIO = {"name": "VAR_RATIO_5_60", "source": "serial_dependence"}
_MAX_DD = {"name": "MAX_DD_20", "source": "downside_risk"}
_CLOSE_LOC = {"name": "CLOSE_LOCATION_DAILY", "source": "daily_candle"}
_AD_PRICE_CORR = {"name": "AD_PRICE_CORR_20", "source": "accumulation_distribution_1m"}
_GK_RATIO = {"name": "GK_RV_RATIO_20", "source": "range_based_vol_1m"}
_BETA_HF = {"name": "BETA_HF_20", "source": "frequency_domain_beta_1m"}
_RECOVERY_FRAC = {"name": "RECOVERY_TIME_FRAC_20", "source": "intraday_pain_recovery_1m"}

base.CANDIDATES = [
    # ---- BB_WIDTH_CHG_20: first pairing batch ----
    {"id": "BA1", "operator": "rank_spread", "left": _BBC, "right": _DOWNSIDE_COSKEW,
     "mechanism": "bb_width_chg_confirmed_by_downside_coskew_60_20",
     "hypothesis": "A=Bollinger带宽20日变化(体检disc-0.0344/审计+0.1194，本族审计最强但disc反号，469-579天覆盖)。B=下行共偏度60日(coskewness_risk,S1早期幸存原子,本族首次配对)。假设:带宽扩张(A高)且下行共偏度低(B低,尾部风险小)=一致确认，负相关。",
     "expected_sign": -1},
    {"id": "BA2", "operator": "rank_spread", "left": _BBC, "right": _OVERNIGHT_GAP,
     "mechanism": "bb_width_chg_confirmed_by_overnight_gap_20",
     "hypothesis": "A=同上。B=隔夜跳空(daily_candle:OVERNIGHT_GAP,本族首次配对，与round_583用过的WICK_IMBALANCE同族不同原子)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "BA3", "operator": "rank_spread", "left": _BBC, "right": _MFI14,
     "mechanism": "bb_width_chg_confirmed_by_mfi_14_mean_20_20",
     "hypothesis": "A=同上。B=1m级MFI(14bar)日均值20日均值(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "BA4", "operator": "rank_spread", "left": _BBC, "right": _YZ_OVN,
     "mechanism": "bb_width_chg_confirmed_by_yz_overnight_share_20_20",
     "hypothesis": "A=同上。B=Yang-Zhang隔夜份额(S9阶段配对最高t原子,range_based_vol_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "BA5", "operator": "rank_spread", "left": _BBC, "right": _COHERENCE,
     "mechanism": "bb_width_chg_confirmed_by_coherence_lf_hf_diff_20_20",
     "hypothesis": "A=同上。B=低频高频相干性之差(frequency_domain_beta_1m,S13阶段,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "BA6", "operator": "rank_spread", "left": _BBC, "right": _NOISE_VAR,
     "mechanism": "bb_width_chg_confirmed_by_noise_var_20_20",
     "hypothesis": "A=同上。B=微观结构噪声方差(S5阶段,microstructure_noise_1m,本族首次配对)。假设:带宽扩张(A高，波动增大)且噪声方差高(B高，信号纯净度下降)=一致确认，正相关。",
     "expected_sign": 1},
    {"id": "BA7", "operator": "rank_spread", "left": _BBC, "right": _SAMPEN,
     "mechanism": "bb_width_chg_confirmed_by_sampen_ret_20_20",
     "hypothesis": "A=同上。B=收益样本熵(S11阶段,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "BA8", "operator": "rank_spread", "left": _BBC, "right": _TRACKING_ERR,
     "mechanism": "bb_width_chg_confirmed_by_tracking_error_20_20",
     "hypothesis": "A=同上。B=对篮子跟踪误差20日(market_relative_strength,本族首次配对,与round_583用过的REL_MARKET_MOM_20同族不同原子)。假设:带宽扩张(A高)且跟踪误差高(B高,与篮子脱钩)=一致确认，正相关。本批最后一条。",
     "expected_sign": 1},
    # ---- LOW_RANGE_STREAK_20: first pairing batch ----
    {"id": "BB1", "operator": "rank_spread", "left": _LRS, "right": _RCOV_P,
     "mechanism": "low_range_streak_confirmed_by_rcov_p_share_20_20",
     "hypothesis": "A=区间低于20日中位数的连续天数(Crabel收缩框架,体检disc-0.0466/审计-0.0116同向,564天)。B=同正半协方差份额(realized_semicov_1m,与round_583用过的RCOV_N_SHARE_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "BB2", "operator": "rank_spread", "left": _LRS, "right": _VAR_RATIO,
     "mechanism": "low_range_streak_confirmed_by_var_ratio_5_60_20",
     "hypothesis": "A=同上。B=方差比5/60日(serial_dependence,本族首次配对)。假设:收缩持续越久(A高)且短期方差比低(B低,趋势性弱)=一致确认，负相关。",
     "expected_sign": -1},
    {"id": "BB3", "operator": "rank_spread", "left": _LRS, "right": _MAX_DD,
     "mechanism": "low_range_streak_confirmed_by_max_dd_20_20",
     "hypothesis": "A=同上。B=日频最大回撤20日(downside_risk,与round_583用过的ULCER_20同族不同原子,本族首次配对)。假设:收缩持续越久(A高)且日频回撤浅(B浅)=一致确认，负相关。",
     "expected_sign": -1},
    {"id": "BB4", "operator": "rank_spread", "left": _LRS, "right": _CLOSE_LOC,
     "mechanism": "low_range_streak_confirmed_by_close_location_daily_20",
     "hypothesis": "A=同上。B=当日收盘在区间内位置(daily_candle,与本轮BA2用过的OVERNIGHT_GAP同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "BB5", "operator": "rank_spread", "left": _LRS, "right": _AD_PRICE_CORR,
     "mechanism": "low_range_streak_confirmed_by_ad_price_corr_20_20",
     "hypothesis": "A=同上。B=A/D净流与当日收益的20日相关(accumulation_distribution_1m,与本轮BA3用过的MFI_14_MEAN_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "BB6", "operator": "rank_spread", "left": _LRS, "right": _GK_RATIO,
     "mechanism": "low_range_streak_confirmed_by_gk_rv_ratio_20_20",
     "hypothesis": "A=同上。B=Garman-Klass与RV比率20日(range_based_vol_1m,与本轮BA4用过的YZ_OVERNIGHT_SHARE_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "BB7", "operator": "rank_spread", "left": _LRS, "right": _BETA_HF,
     "mechanism": "low_range_streak_confirmed_by_beta_hf_20_20",
     "hypothesis": "A=同上。B=高频带beta20日(frequency_domain_beta_1m,与本轮BA5用过的COHERENCE_LF_HF_DIFF_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "BB8", "operator": "rank_spread", "left": _LRS, "right": _RECOVERY_FRAC,
     "mechanism": "low_range_streak_confirmed_by_recovery_time_frac_20_20",
     "hypothesis": "A=同上。B=日内回撤恢复时间占比(S12阶段,intraday_pain_recovery_1m,本族首次配对)。假设:收缩持续越久(A高)且恢复更快(B低)=一致确认，负相关。本批最后一条。",
     "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
