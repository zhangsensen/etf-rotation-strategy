#!/usr/bin/env python3
"""Round 585 driver: S19 stage step 3 (final atoms) --
range_contraction_cycle pairing, round 3. Uses the family's remaining 4
atoms as left legs, none yet used (NR7_FLAG_FREQ_20, DAYS_SINCE_NR7_20,
BB_WIDTH_PCTL_120, CONTRACTION_DEPTH_60) -- all 8 atoms in the family
will have used their one legal pairing batch after this round, so this
is the family's last pairing round regardless of outcome.

Right legs: 4 per left leg (16 total), reusing atoms from round_583/584
at their 2nd use (all still under the 3-lefts-per-right cap) since this
family's right-leg pool is being deliberately kept small and
well-understood rather than constantly introducing fresh atoms -- each
pair is still a genuinely new combination (none of these exact
left-right pairs were tested before, since all 4 left atoms are new
this round)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_585"

_NR7 = {"name": "NR7_FLAG_FREQ_20", "source": "range_contraction_cycle"}
_DSN = {"name": "DAYS_SINCE_NR7_20", "source": "range_contraction_cycle"}
_BBP = {"name": "BB_WIDTH_PCTL_120", "source": "range_contraction_cycle"}
_CD = {"name": "CONTRACTION_DEPTH_60", "source": "range_contraction_cycle"}

_RCOV_N = {"name": "RCOV_N_SHARE_20", "source": "realized_semicov_1m"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_SESSION_RET = {"name": "SESSION_RETURN", "source": "daily_candle"}
_RET_ACF1 = {"name": "RET_ACF1_20", "source": "serial_dependence"}

_PATH_EFF = {"name": "PATH_EFFICIENCY_20", "source": "path_efficiency"}
_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_ULCER = {"name": "ULCER_20", "source": "downside_risk"}
_WICK_IMB = {"name": "WICK_IMBALANCE", "source": "daily_candle"}

_UNDERWATER_RUN = {"name": "UNDERWATER_RUN_60", "source": "drawdown_duration"}
_DOWNSIDE_COSKEW = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}
_OVERNIGHT_GAP = {"name": "OVERNIGHT_GAP", "source": "daily_candle"}
_MFI14 = {"name": "MFI_14_MEAN_20", "source": "accumulation_distribution_1m"}

_YZ_OVN = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_COHERENCE = {"name": "COHERENCE_LF_HF_DIFF_20", "source": "frequency_domain_beta_1m"}
_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}

base.CANDIDATES = [
    # ---- NR7_FLAG_FREQ_20 ----
    {"id": "CA1", "operator": "rank_spread", "left": _NR7, "right": _RCOV_N,
     "mechanism": "nr7_flag_freq_confirmed_by_rcov_n_share_20",
     "hypothesis": "A=NR7标志20日频率(体检disc-0.0152/审计+0.0161反号)。B=同负半协方差份额(realized_semicov_1m,round_583已配过TRUE_RANGE_RATIO_20,本轮换左腿,右腿第2次使用)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "CA2", "operator": "rank_spread", "left": _NR7, "right": _MARKET_BETA20,
     "mechanism": "nr7_flag_freq_confirmed_by_market_beta_20",
     "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity,右腿第2次使用)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "CA3", "operator": "rank_spread", "left": _NR7, "right": _SESSION_RET,
     "mechanism": "nr7_flag_freq_confirmed_by_session_return_20",
     "hypothesis": "A=同上。B=当日session收益(daily_candle,本族首次以该原子配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "CA4", "operator": "rank_spread", "left": _NR7, "right": _RET_ACF1,
     "mechanism": "nr7_flag_freq_confirmed_by_ret_acf1_20",
     "hypothesis": "A=同上。B=收益一阶自相关20日(serial_dependence,右腿第2次使用)。假设:NR7频率高(A高,持续窄幅整理)且收益自相关低(B低,随机游走特征强)=一致确认，负相关。本批最后一条。",
     "expected_sign": -1},
    # ---- DAYS_SINCE_NR7_20 ----
    {"id": "CB1", "operator": "rank_spread", "left": _DSN, "right": _PATH_EFF,
     "mechanism": "days_since_nr7_confirmed_by_path_efficiency_20",
     "hypothesis": "A=最近一次NR7距今天数(体检disc+0.0242/审计-0.0295反号)。B=20日路径效率(path_efficiency,右腿第2次使用)。假设:距上次NR7越久(A高,远离收缩状态)且路径效率高(B高,趋势直线化)=一致确认，正相关。",
     "expected_sign": 1},
    {"id": "CB2", "operator": "rank_spread", "left": _DSN, "right": _REL_MOM20,
     "mechanism": "days_since_nr7_confirmed_by_rel_market_mom_20",
     "hypothesis": "A=同上。B=相对篮子动量20日(market_relative_strength,右腿第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "CB3", "operator": "rank_spread", "left": _DSN, "right": _ULCER,
     "mechanism": "days_since_nr7_confirmed_by_ulcer_20",
     "hypothesis": "A=同上。B=日频溃疡指数20日(downside_risk,右腿第2次使用)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "CB4", "operator": "rank_spread", "left": _DSN, "right": _WICK_IMB,
     "mechanism": "days_since_nr7_confirmed_by_wick_imbalance_20",
     "hypothesis": "A=同上。B=日频上下影线不平衡(daily_candle,右腿第2次使用)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- BB_WIDTH_PCTL_120 ----
    {"id": "CC1", "operator": "rank_spread", "left": _BBP, "right": _UNDERWATER_RUN,
     "mechanism": "bb_width_pctl_confirmed_by_underwater_run_60",
     "hypothesis": "A=Bollinger带宽120日百分位(体检disc-0.0007/审计+0.0161接近零)。B=日频最长水下持续期60日(drawdown_duration,右腿第2次使用)。假设:带宽百分位低(A低,squeeze状态)且水下持续期短(B低,近期强势)=一致确认，正相关。",
     "expected_sign": 1},
    {"id": "CC2", "operator": "rank_spread", "left": _BBP, "right": _DOWNSIDE_COSKEW,
     "mechanism": "bb_width_pctl_confirmed_by_downside_coskew_60",
     "hypothesis": "A=同上。B=下行共偏度60日(coskewness_risk,右腿第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "CC3", "operator": "rank_spread", "left": _BBP, "right": _OVERNIGHT_GAP,
     "mechanism": "bb_width_pctl_confirmed_by_overnight_gap_20",
     "hypothesis": "A=同上。B=隔夜跳空(daily_candle,右腿第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "CC4", "operator": "rank_spread", "left": _BBP, "right": _MFI14,
     "mechanism": "bb_width_pctl_confirmed_by_mfi_14_mean_20",
     "hypothesis": "A=同上。B=1m级MFI(14bar)日均值20日均值(accumulation_distribution_1m,右腿第2次使用)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- CONTRACTION_DEPTH_60 ----
    {"id": "CD1", "operator": "rank_spread", "left": _CD, "right": _YZ_OVN,
     "mechanism": "contraction_depth_confirmed_by_yz_overnight_share_20",
     "hypothesis": "A=当前20日最小TR在过去60日TR分布中的分位(体检disc+0.0195/审计-0.0139反号)。B=Yang-Zhang隔夜份额(range_based_vol_1m,右腿第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "CD2", "operator": "rank_spread", "left": _CD, "right": _COHERENCE,
     "mechanism": "contraction_depth_confirmed_by_coherence_lf_hf_diff_20",
     "hypothesis": "A=同上。B=低频高频相干性之差(frequency_domain_beta_1m,右腿第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "CD3", "operator": "rank_spread", "left": _CD, "right": _NOISE_VAR,
     "mechanism": "contraction_depth_confirmed_by_noise_var_20",
     "hypothesis": "A=同上。B=微观结构噪声方差(microstructure_noise_1m,右腿第2次使用)。假设:收缩越深(A高)且噪声方差低(B低,信号纯净)=一致确认，负相关。",
     "expected_sign": -1},
    {"id": "CD4", "operator": "rank_spread", "left": _CD, "right": _SAMPEN,
     "mechanism": "contraction_depth_confirmed_by_sampen_ret_20",
     "hypothesis": "A=同上。B=收益样本熵(complexity_measures_1m,右腿第2次使用)。假设方向由发现期定。本批最后一条，range_contraction_cycle全部8个原子的合法配对将全部用尽。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
