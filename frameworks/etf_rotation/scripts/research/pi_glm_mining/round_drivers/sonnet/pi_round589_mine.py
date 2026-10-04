#!/usr/bin/env python3
"""Round 589 driver: S20 stage step 3 -- price_delay pairing, round 3.
Two more left-leg batches: D1_1M_CHG_20 (best-remaining same-sign atom,
disc+0.0603/audit+0.0097) and D2_LAGSHARE_CHG_20 (shadow vs S14's
PD_D1_CHG_20, but strongest remaining raw audit IC +0.0430 -- still
pairing-eligible since shadow only flags atom-health correlation, not a
pairing ban). After this round only 2 price_delay atoms remain unused
as left legs (LAG1_COEF_60, LAG_COEF_SIGN_FREQ_20).

Right legs: 16 total, mostly atoms not yet used in this stage (right-leg
caps reset per-stage per the '在一阶段最多与3个不同左腿配对' rule, so
S16-S19's usage does not constrain S20)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_589"

_D1_1M_CHG = {"name": "D1_1M_CHG_20", "source": "price_delay"}
_D2_CHG = {"name": "D2_LAGSHARE_CHG_20", "source": "price_delay"}

_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_COHERENCE = {"name": "COHERENCE_LF_HF_DIFF_20", "source": "frequency_domain_beta_1m"}
_OVERNIGHT_GAP = {"name": "OVERNIGHT_GAP", "source": "daily_candle"}
_RCOV_P = {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"}
_VAR_RATIO = {"name": "VAR_RATIO_5_60", "source": "serial_dependence"}
_MAX_DD = {"name": "MAX_DD_20", "source": "downside_risk"}
_AD_PRICE_CORR = {"name": "AD_PRICE_CORR_20", "source": "accumulation_distribution_1m"}
_GK_RATIO = {"name": "GK_RV_RATIO_20", "source": "range_based_vol_1m"}

_BETA_HF = {"name": "BETA_HF_20", "source": "frequency_domain_beta_1m"}
_RECOVERY_FRAC = {"name": "RECOVERY_TIME_FRAC_20", "source": "intraday_pain_recovery_1m"}
_CLOSE_LOC = {"name": "CLOSE_LOCATION_DAILY", "source": "daily_candle"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_LRS = {"name": "LOW_RANGE_STREAK_20", "source": "range_contraction_cycle"}
_DOWNSIDE_COSKEW = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}
_MFI14 = {"name": "MFI_14_MEAN_20", "source": "accumulation_distribution_1m"}
_TRACKING_ERR = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}

base.CANDIDATES = [
    # ---- D1_1M_CHG_20: first pairing batch ----
    {"id": "FA1", "operator": "rank_spread", "left": _D1_1M_CHG, "right": _NOISE_VAR,
     "mechanism": "d1_1m_chg_confirmed_by_noise_var_20",
     "hypothesis": "A=D1的1m日内类比的20日变化(体检disc+0.0603/审计+0.0097同向,578天)。B=微观结构噪声方差(microstructure_noise_1m,本族首次配对)。假设:延迟在加剧(A高)且噪声方差高(B高,信号质量下降)=一致确认，正相关。",
     "expected_sign": 1},
    {"id": "FA2", "operator": "rank_spread", "left": _D1_1M_CHG, "right": _COHERENCE,
     "mechanism": "d1_1m_chg_confirmed_by_coherence_lf_hf_diff_20",
     "hypothesis": "A=同上。B=低频高频相干性之差(frequency_domain_beta_1m,与round_588用过的BETA_LF_CHG_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "FA3", "operator": "rank_spread", "left": _D1_1M_CHG, "right": _OVERNIGHT_GAP,
     "mechanism": "d1_1m_chg_confirmed_by_overnight_gap_20",
     "hypothesis": "A=同上。B=隔夜跳空(daily_candle,与round_588用过的WICK_IMBALANCE同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "FA4", "operator": "rank_spread", "left": _D1_1M_CHG, "right": _RCOV_P,
     "mechanism": "d1_1m_chg_confirmed_by_rcov_p_share_20",
     "hypothesis": "A=同上。B=同正半协方差份额(realized_semicov_1m,与round_588用过的RCOV_N_SHARE_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "FA5", "operator": "rank_spread", "left": _D1_1M_CHG, "right": _VAR_RATIO,
     "mechanism": "d1_1m_chg_confirmed_by_var_ratio_5_60",
     "hypothesis": "A=同上。B=方差比5/60日(serial_dependence,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "FA6", "operator": "rank_spread", "left": _D1_1M_CHG, "right": _MAX_DD,
     "mechanism": "d1_1m_chg_confirmed_by_max_dd_20",
     "hypothesis": "A=同上。B=日频最大回撤20日(downside_risk,与round_588用过的ULCER_20同族不同原子,本族首次配对)。假设:延迟在加剧(A高)且日频回撤深(B深)=一致确认，正相关。",
     "expected_sign": 1},
    {"id": "FA7", "operator": "rank_spread", "left": _D1_1M_CHG, "right": _AD_PRICE_CORR,
     "mechanism": "d1_1m_chg_confirmed_by_ad_price_corr_20",
     "hypothesis": "A=同上。B=A/D净流与当日收益的20日相关(accumulation_distribution_1m,与round_587用过的AD_NET_FLOW_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "FA8", "operator": "rank_spread", "left": _D1_1M_CHG, "right": _GK_RATIO,
     "mechanism": "d1_1m_chg_confirmed_by_gk_rv_ratio_20",
     "hypothesis": "A=同上。B=Garman-Klass与RV比率20日(range_based_vol_1m,与round_587用过的YZ_OVERNIGHT_SHARE_20同族不同原子,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- D2_LAGSHARE_CHG_20: first pairing batch (shadow atom, still pairing-eligible) ----
    {"id": "FB1", "operator": "rank_spread", "left": _D2_CHG, "right": _BETA_HF,
     "mechanism": "d2_lagshare_chg_confirmed_by_beta_hf_20",
     "hypothesis": "A=D2的20日变化(体检disc+0.0007接近零/审计+0.0430,shadow=vs S14 PD_D1_CHG_20,corr0.82,仍可作左腿)。B=高频带beta20日(frequency_domain_beta_1m,与本轮FA2用过的COHERENCE_LF_HF_DIFF_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "FB2", "operator": "rank_spread", "left": _D2_CHG, "right": _RECOVERY_FRAC,
     "mechanism": "d2_lagshare_chg_confirmed_by_recovery_time_frac_20",
     "hypothesis": "A=同上。B=日内回撤恢复时间占比(S12阶段,intraday_pain_recovery_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "FB3", "operator": "rank_spread", "left": _D2_CHG, "right": _CLOSE_LOC,
     "mechanism": "d2_lagshare_chg_confirmed_by_close_location_daily",
     "hypothesis": "A=同上。B=当日收盘在区间内位置(daily_candle,与本轮FA3用过的OVERNIGHT_GAP同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "FB4", "operator": "rank_spread", "left": _D2_CHG, "right": _SAMPEN,
     "mechanism": "d2_lagshare_chg_confirmed_by_sampen_ret_20",
     "hypothesis": "A=同上。B=收益样本熵(S11阶段,complexity_measures_1m,与round_587用过的RECURRENCE_RATE_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "FB5", "operator": "rank_spread", "left": _D2_CHG, "right": _LRS,
     "mechanism": "d2_lagshare_chg_confirmed_by_low_range_streak_20",
     "hypothesis": "A=同上。B=区间低于20日中位数的连续天数(S19阶段,range_contraction_cycle,与round_588用过的TRUE_RANGE_RATIO_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "FB6", "operator": "rank_spread", "left": _D2_CHG, "right": _DOWNSIDE_COSKEW,
     "mechanism": "d2_lagshare_chg_confirmed_by_downside_coskew_60",
     "hypothesis": "A=同上。B=下行共偏度60日(coskewness_risk,与round_587用过的COSKEW_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "FB7", "operator": "rank_spread", "left": _D2_CHG, "right": _MFI14,
     "mechanism": "d2_lagshare_chg_confirmed_by_mfi_14_mean_20",
     "hypothesis": "A=同上。B=1m级MFI(14bar)日均值20日均值(accumulation_distribution_1m,与本轮FA7用过的AD_PRICE_CORR_20同族不同原子,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "FB8", "operator": "rank_spread", "left": _D2_CHG, "right": _TRACKING_ERR,
     "mechanism": "d2_lagshare_chg_confirmed_by_tracking_error_20",
     "hypothesis": "A=同上。B=对篮子跟踪误差20日(market_relative_strength,与round_588用过的REL_MARKET_MOM_20同族不同原子,本族首次配对)。假设方向由发现期定。本批最后一条，price_delay 8个原子中已有6个用尽左腿配额。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
