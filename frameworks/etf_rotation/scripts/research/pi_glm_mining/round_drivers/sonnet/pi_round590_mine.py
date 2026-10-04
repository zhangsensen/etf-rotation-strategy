#!/usr/bin/env python3
"""Round 590 driver: S20 stage step 4 (final) -- price_delay pairing,
round 4. Uses the family's final 2 unused atoms as left legs:
LAG1_COEF_60 (shadow vs cross_etf_lead_lag:PEER_LEAD_CORR_60, corr 0.81,
still pairing-eligible) and LAG_COEF_SIGN_FREQ_20 (weakest atom-health
signal, disc+0.0105/audit+0.0053). After this round all 8
price_delay atoms will have used their one legal pairing batch each, so
this is the family's last pairing round regardless of outcome.

Right legs: 16 total, reusing atoms from round_587-589 at their 2nd use
(all still well under the 3-lefts-per-right cap)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_590"

_LAG1 = {"name": "LAG1_COEF_60", "source": "price_delay"}
_LAG_SIGN = {"name": "LAG_COEF_SIGN_FREQ_20", "source": "price_delay"}

_DOWNSIDE_COSKEW = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}
_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENT = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_CONT_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_YZ_OVN = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_MSPE5 = {"name": "MSPE_5M_20", "source": "complexity_measures_1m"}
_TRR = {"name": "TRUE_RANGE_RATIO_20", "source": "range_contraction_cycle"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}

_RCOV_N = {"name": "RCOV_N_SHARE_20", "source": "realized_semicov_1m"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_PATH_EFF = {"name": "PATH_EFFICIENCY_20", "source": "path_efficiency"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_WICK_IMB = {"name": "WICK_IMBALANCE", "source": "daily_candle"}
_ULCER = {"name": "ULCER_20", "source": "downside_risk"}
_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_BEST_DAY = {"name": "BEST_DAY_20", "source": "upside_tail"}

base.CANDIDATES = [
    # ---- LAG1_COEF_60: first (and last) pairing batch ----
    {"id": "GA1", "operator": "rank_spread", "left": _LAG1, "right": _DOWNSIDE_COSKEW,
     "mechanism": "lag1_coef_confirmed_by_downside_coskew_60",
     "hypothesis": "A=Mech 1993单滞后系数(体检disc-0.0250/审计+0.0042弱反号,shadow=True vs cross_etf_lead_lag,corr0.81,仍可作左腿)。B=下行共偏度60日(coskewness_risk,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA2", "operator": "rank_spread", "left": _LAG1, "right": _UF_CHG,
     "mechanism": "lag1_coef_confirmed_by_underwater_frac_chg_20",
     "hypothesis": "A=同上。B=主动水下时长20日变化(intraday_drawdown_1m,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA3", "operator": "rank_spread", "left": _LAG1, "right": _PERM_ENT,
     "mechanism": "lag1_coef_confirmed_by_perm_entropy_ret_20",
     "hypothesis": "A=同上。B=收益排列熵(permutation_entropy_1m,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA4", "operator": "rank_spread", "left": _LAG1, "right": _CONT_BETA,
     "mechanism": "lag1_coef_confirmed_by_continuous_beta_60",
     "hypothesis": "A=同上。B=对篮子连续beta(jump_continuous_beta,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA5", "operator": "rank_spread", "left": _LAG1, "right": _YZ_OVN,
     "mechanism": "lag1_coef_confirmed_by_yz_overnight_share_20",
     "hypothesis": "A=同上。B=Yang-Zhang隔夜份额(range_based_vol_1m,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA6", "operator": "rank_spread", "left": _LAG1, "right": _MSPE5,
     "mechanism": "lag1_coef_confirmed_by_mspe_5m_20",
     "hypothesis": "A=同上。B=5分钟多尺度排列熵(complexity_measures_1m,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA7", "operator": "rank_spread", "left": _LAG1, "right": _TRR,
     "mechanism": "lag1_coef_confirmed_by_true_range_ratio_20",
     "hypothesis": "A=同上。B=真实区间比率(range_contraction_cycle,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GA8", "operator": "rank_spread", "left": _LAG1, "right": _AD_NET_FLOW,
     "mechanism": "lag1_coef_confirmed_by_ad_net_flow_20",
     "hypothesis": "A=同上。B=A/D净流20日(accumulation_distribution_1m,本轮第2次使用)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- LAG_COEF_SIGN_FREQ_20: first (and last) pairing batch ----
    {"id": "GB1", "operator": "rank_spread", "left": _LAG_SIGN, "right": _RCOV_N,
     "mechanism": "lag_coef_sign_freq_confirmed_by_rcov_n_share_20",
     "hypothesis": "A=滞后系数和为正的20日频率(体检disc+0.0105/审计+0.0053弱同向)。B=同负半协方差份额(realized_semicov_1m,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GB2", "operator": "rank_spread", "left": _LAG_SIGN, "right": _WORST_DAY,
     "mechanism": "lag_coef_sign_freq_confirmed_by_worst_day_20",
     "hypothesis": "A=同上。B=20日最差单日收益(return_tail_shape,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GB3", "operator": "rank_spread", "left": _LAG_SIGN, "right": _PATH_EFF,
     "mechanism": "lag_coef_sign_freq_confirmed_by_path_efficiency_20",
     "hypothesis": "A=同上。B=20日路径效率(path_efficiency,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GB4", "operator": "rank_spread", "left": _LAG_SIGN, "right": _MARKET_BETA20,
     "mechanism": "lag_coef_sign_freq_confirmed_by_market_beta_20",
     "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GB5", "operator": "rank_spread", "left": _LAG_SIGN, "right": _WICK_IMB,
     "mechanism": "lag_coef_sign_freq_confirmed_by_wick_imbalance_20",
     "hypothesis": "A=同上。B=日频上下影线不平衡(daily_candle,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GB6", "operator": "rank_spread", "left": _LAG_SIGN, "right": _ULCER,
     "mechanism": "lag_coef_sign_freq_confirmed_by_ulcer_20",
     "hypothesis": "A=同上。B=日频溃疡指数20日(downside_risk,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GB7", "operator": "rank_spread", "left": _LAG_SIGN, "right": _REL_MOM20,
     "mechanism": "lag_coef_sign_freq_confirmed_by_rel_market_mom_20",
     "hypothesis": "A=同上。B=相对篮子动量20日(market_relative_strength,本轮第2次使用)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "GB8", "operator": "rank_spread", "left": _LAG_SIGN, "right": _BEST_DAY,
     "mechanism": "lag_coef_sign_freq_confirmed_by_best_day_20",
     "hypothesis": "A=同上。B=20日最佳单日收益(upside_tail,本轮第2次使用)。假设方向由发现期定。本批最后一条，price_delay全部8个原子的合法配对将全部用尽。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
