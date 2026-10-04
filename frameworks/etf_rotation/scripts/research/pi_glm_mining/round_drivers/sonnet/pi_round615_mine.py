#!/usr/bin/env python3
"""Round 615 driver: S27 stage step 2 -- overnight_intraday_mismatch_v1
pairing, round 2. Remaining 4 left legs not yet used in round_614
(all with weak atom_health |disc_ic|<0.01, so a lower yield is expected
compared to round_614's strong GAP_DD_CONSUMPTION_RATIO_20/
ON_TROUGH_RECOVERY_MATCH_20 batches): ON_STREAK_UF_COV_20,
ON_SIGN_UF_DIFF_20, ON_TROUGH_RECOVERY_MATCH_CHG_20,
GAP_DD_CONSUMPTION_RATIO_CHG_20. This exhausts all 6 family atoms'
pairing-batch allowance for S27 (round_614 used 2, this round uses the
remaining 4).

Right legs: mostly reuse round_614's 16 rights at their 2nd use (still
under the 3x cap), plus a few fresh atoms (PEER_OU_HALFLIFE_20,
MFI_EXTREME_TOD_SKEW_20, R_VOL_SPIKE_FREQ_20 from S26R's
repl_volume_core_a, LUNCH_POST_RUN_20) for the last batch."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_615"

_COV = {"name": "ON_STREAK_UF_COV_20", "source": "overnight_intraday_mismatch_v1"}
_DIFF = {"name": "ON_SIGN_UF_DIFF_20", "source": "overnight_intraday_mismatch_v1"}
_MATCH_CHG = {"name": "ON_TROUGH_RECOVERY_MATCH_CHG_20", "source": "overnight_intraday_mismatch_v1"}
_RATIO_CHG = {"name": "GAP_DD_CONSUMPTION_RATIO_CHG_20", "source": "overnight_intraday_mismatch_v1"}

_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_LUNCH_PRERUN_POSTRUN = {"name": "LUNCH_PRERUN_POSTRUN_RATIO_20", "source": "lunch_break_1m"}
_TRR = {"name": "TRUE_RANGE_RATIO_20", "source": "range_contraction_cycle"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}

_D1_60 = {"name": "D1_LEVEL_60", "source": "price_delay"}
_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_COSKEW20 = {"name": "COSKEW_20", "source": "coskewness_risk"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_BEST_DAY = {"name": "BEST_DAY_20", "source": "upside_tail"}

_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}
_JUMP_BETA = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_YZ_OVERNIGHT = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}

_GRANGER = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_MFI_TOD_SKEW = {"name": "MFI_EXTREME_TOD_SKEW_20", "source": "money_flow_extremes_1m"}
_R_VOL_SPIKE_FREQ = {"name": "R_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_a"}
_LUNCH_POST_RUN = {"name": "LUNCH_POST_RUN_20", "source": "lunch_break_1m"}

base.CANDIDATES = [
    # ---- ON_STREAK_UF_COV_20: first pairing batch ----
    {"id": "S27D1", "operator": "rank_spread", "left": _COV, "right": _UF_CHG,
     "mechanism": "on_streak_uf_cov_confirmed_by_underwater_frac_chg_20",
     "hypothesis": "A=隔夜符号连续天数与日内水下占比的20日滚动协方差(体检disc+0.0043/审计+0.0274,弱)。B=日内水下占比20日变化(S7本线单原子审计最高,intraday_drawdown_1m,本族第2批首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27D2", "operator": "rank_spread", "left": _COV, "right": _LUNCH_PRERUN_POSTRUN,
     "mechanism": "on_streak_uf_cov_confirmed_by_lunch_prerun_postrun_ratio_20",
     "hypothesis": "A=同上。B=午前/午后抢跑成交量份额之比(S22原子级入选KA7,lunch_break_1m)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27D3", "operator": "rank_spread", "left": _COV, "right": _TRR,
     "mechanism": "on_streak_uf_cov_confirmed_by_true_range_ratio_20",
     "hypothesis": "A=同上。B=真实区间比率(S19唯一净入选原子AB1,range_contraction_cycle)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27D4", "operator": "rank_spread", "left": _COV, "right": _WORST_DAY,
     "mechanism": "on_streak_uf_cov_confirmed_by_worst_day_20",
     "hypothesis": "A=同上。B=20日最差单日收益(return_tail_shape)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27D5", "operator": "rank_spread", "left": _COV, "right": _SAMPEN,
     "mechanism": "on_streak_uf_cov_confirmed_by_sampen_ret_20",
     "hypothesis": "A=同上。B=收益样本熵(S11,complexity_measures_1m)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- ON_SIGN_UF_DIFF_20: first pairing batch ----
    {"id": "S27E1", "operator": "rank_spread", "left": _DIFF, "right": _D1_60,
     "mechanism": "on_sign_uf_diff_confirmed_by_d1_level_60",
     "hypothesis": "A=20日窗口内隔夜为正日水下占比均值−隔夜为负日均值(体检disc-0.0025/审计-0.0306,弱)。B=价格延迟D1水平(S20入选原子搭档,price_delay)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27E2", "operator": "rank_spread", "left": _DIFF, "right": _MFI_EXTREME_FRAC,
     "mechanism": "on_sign_uf_diff_confirmed_by_mfi_extreme_frac_20",
     "hypothesis": "A=同上。B=MFI极端占比(S23阶段最强候选WA1的右腿,accumulation_distribution_1m)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27E3", "operator": "rank_spread", "left": _DIFF, "right": _COSKEW20,
     "mechanism": "on_sign_uf_diff_confirmed_by_coskew_20",
     "hypothesis": "A=同上。B=共偏度20日(coskewness_risk)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27E4", "operator": "rank_spread", "left": _DIFF, "right": _MARKET_BETA20,
     "mechanism": "on_sign_uf_diff_confirmed_by_market_beta_20",
     "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27E5", "operator": "rank_spread", "left": _DIFF, "right": _BEST_DAY,
     "mechanism": "on_sign_uf_diff_confirmed_by_best_day_20",
     "hypothesis": "A=同上。B=20日最佳单日收益(S2,upside_tail)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- ON_TROUGH_RECOVERY_MATCH_CHG_20: first pairing batch ----
    {"id": "S27F1", "operator": "rank_spread", "left": _MATCH_CHG, "right": _VT_AUTOCORR,
     "mechanism": "on_trough_recovery_match_chg_confirmed_by_vt_autocorr_20",
     "hypothesis": "A=ON_TROUGH_RECOVERY_MATCH_20的20日变化(体检disc+0.0082/审计+0.0341,弱)。B=成交量时间收益1桶滞后自相关(S24净入选簇代表XB3的左腿,volume_time_1m)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27F2", "operator": "rank_spread", "left": _MATCH_CHG, "right": _AD_NET_FLOW,
     "mechanism": "on_trough_recovery_match_chg_confirmed_by_ad_net_flow_20",
     "hypothesis": "A=同上。B=A/D净流20日(accumulation_distribution_1m)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27F3", "operator": "rank_spread", "left": _MATCH_CHG, "right": _GAP_FILL,
     "mechanism": "on_trough_recovery_match_chg_confirmed_by_gap_fill_fraction_20",
     "hypothesis": "A=同上。B=跳空当日回补比例20日(gap_repair,S18/S22入选原子搭档)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27F4", "operator": "rank_spread", "left": _MATCH_CHG, "right": _JUMP_BETA,
     "mechanism": "on_trough_recovery_match_chg_confirmed_by_jump_beta_20",
     "hypothesis": "A=同上。B=跳跃beta(S4,jump_continuous_beta)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27F5", "operator": "rank_spread", "left": _MATCH_CHG, "right": _YZ_OVERNIGHT,
     "mechanism": "on_trough_recovery_match_chg_confirmed_by_yz_overnight_share_20",
     "hypothesis": "A=同上。B=Yang-Zhang隔夜方差份额(S9,range_based_vol_1m)。假设方向由发现期定。本批最后一条。",
     "expected_sign": 1},
    # ---- GAP_DD_CONSUMPTION_RATIO_CHG_20: first pairing batch ----
    {"id": "S27G1", "operator": "rank_spread", "left": _RATIO_CHG, "right": _GRANGER,
     "mechanism": "gap_dd_ratio_chg_confirmed_by_granger_in_degree_20",
     "hypothesis": "A=GAP_DD_CONSUMPTION_RATIO_20的20日变化(体检disc+0.0007/审计-0.0571,符号翻转不稳)。B=Granger因果入度(cross_dependence_1m)。假设方向由发现期定，本条方向不确定性高。",
     "expected_sign": 1},
    {"id": "S27G2", "operator": "rank_spread", "left": _RATIO_CHG, "right": _PEER_OU_HALFLIFE,
     "mechanism": "gap_dd_ratio_chg_confirmed_by_peer_ou_halflife_20",
     "hypothesis": "A=同上。B=同伴OU均值回归半衰期(peer_relative_value,S25顶级原子池,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27G3", "operator": "rank_spread", "left": _RATIO_CHG, "right": _MFI_TOD_SKEW,
     "mechanism": "gap_dd_ratio_chg_confirmed_by_mfi_extreme_tod_skew_20",
     "hypothesis": "A=同上。B=MFI极端值时段偏度(money_flow_extremes_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27G4", "operator": "rank_spread", "left": _RATIO_CHG, "right": _R_VOL_SPIKE_FREQ,
     "mechanism": "gap_dd_ratio_chg_confirmed_by_r_vol_spike_freq_20",
     "hypothesis": "A=同上。B=独立重写的成交量突增频率(S26R,repl_volume_core_a,本族首次配对)。假设方向由发现期定。",
     "expected_sign": 1},
    {"id": "S27G5", "operator": "rank_spread", "left": _RATIO_CHG, "right": _LUNCH_POST_RUN,
     "mechanism": "gap_dd_ratio_chg_confirmed_by_lunch_post_run_20",
     "hypothesis": "A=同上。B=13:00-13:10成交量占全日比例(S22入选原子搭档LB8,lunch_break_1m,本族首次配对)。假设方向由发现期定。本批最后一条，本轮末条，本族6原子左腿配额全部用尽。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
