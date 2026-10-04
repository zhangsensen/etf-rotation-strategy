#!/usr/bin/env python3
"""Round 614 driver: S27 stage step 1 -- overnight_intraday_mismatch_v1
family (Lou-Polk-Skouras 2019 tug-of-war; Barclay-Hendershott 2003;
Bogousslavsky 2021 -- deepening the mechanism shared by S21's UE3
[+53.3bp/t3.08], S16's HB1 [+56.5bp/t2.98] and pi's CY95 [t1.76]:
overnight-direction vs intraday-drawdown mismatch), main controller's
pre-specified S27 direction after S26R's closure (round_612-613).
This family builds 4 NEW single-statistic atoms (not a recombination
of existing atoms) that directly encode the mismatch as one number per
day, plus 2 20d-change variants of the two most interpretable atoms.

Atom health (round_614_atom_health, vs intraday_drawdown_1m,
overnight_structure_1d, range_based_vol_1m, gap_response): 0/6 atoms
shadow (max corr 0.65, GAP_DD_CONSUMPTION_RATIO_20 vs
YZ_OVERNIGHT_SHARE_20 -- close but below threshold, confirming genuine
novelty). GAP_DD_CONSUMPTION_RATIO_20 has by far the strongest and most
consistent same-sign IC (disc-0.0851/audit-0.0711); ON_TROUGH_RECOVERY_
MATCH_20 is the second most consistent (disc-0.0317/audit-0.0126). This
round: 6 atomic tests + first pairing batches for these two atoms (8
rights each), per the pairing-discipline rule -- deliberately limited
to 2 new left legs (4 more remain for a future round)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_614"

_MATCH = {"name": "ON_TROUGH_RECOVERY_MATCH_20", "source": "overnight_intraday_mismatch_v1"}
_RATIO = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_COV = {"name": "ON_STREAK_UF_COV_20", "source": "overnight_intraday_mismatch_v1"}
_DIFF = {"name": "ON_SIGN_UF_DIFF_20", "source": "overnight_intraday_mismatch_v1"}
_MATCH_CHG = {"name": "ON_TROUGH_RECOVERY_MATCH_CHG_20", "source": "overnight_intraday_mismatch_v1"}
_RATIO_CHG = {"name": "GAP_DD_CONSUMPTION_RATIO_CHG_20", "source": "overnight_intraday_mismatch_v1"}

_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_LUNCH_PRERUN_POSTRUN = {"name": "LUNCH_PRERUN_POSTRUN_RATIO_20", "source": "lunch_break_1m"}
_TRR = {"name": "TRUE_RANGE_RATIO_20", "source": "range_contraction_cycle"}
_D1_60 = {"name": "D1_LEVEL_60", "source": "price_delay"}
_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_COSKEW20 = {"name": "COSKEW_20", "source": "coskewness_risk"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}

_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_BEST_DAY = {"name": "BEST_DAY_20", "source": "upside_tail"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}
_JUMP_BETA = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_YZ_OVERNIGHT = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_GRANGER = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}

base.CANDIDATES = [
    # ---- 6 atomic: new overnight_intraday_mismatch_v1 atoms ----
    {
        "id": "S27A1", "operator": "atomic", "left": _MATCH, "right": _MATCH,
        "mechanism": "on_trough_recovery_match_20",
        "hypothesis": "隔夜跳空方向与日内先逆后顺（dip/pop-then-recover-toward-gap）模式的一致率20日均值(Lou-Polk-Skouras 2019隔夜/日内拉锯)。体检:disc-0.0317/审计-0.0126(同向弱)，非shadow(corr 0.45)。",
        "expected_sign": -1,
    },
    {
        "id": "S27A2", "operator": "atomic", "left": _RATIO, "right": _RATIO,
        "mechanism": "gap_dd_consumption_ratio_20",
        "hypothesis": "日内最大回撤(以开盘为基)/|隔夜跳空|，截断[0,3]，20日均值(隔夜信号被日内自身回撤吃掉的比例)。体检:disc-0.0851/审计-0.0711(同向强，本族最强)，非shadow(corr 0.65，与YZ_OVERNIGHT_SHARE_20接近但未达阈值)，本轮首个配对左腿。",
        "expected_sign": -1,
    },
    {
        "id": "S27A3", "operator": "atomic", "left": _COV, "right": _COV,
        "mechanism": "on_streak_uf_cov_20",
        "hypothesis": "隔夜符号连续天数序列与日内水下占比序列的20日滚动协方差(单一统计量，非两原子乘积)。体检:disc+0.0043/审计+0.0274(弱)，非shadow(corr 0.18)。",
        "expected_sign": 1,
    },
    {
        "id": "S27A4", "operator": "atomic", "left": _DIFF, "right": _DIFF,
        "mechanism": "on_sign_uf_diff_20",
        "hypothesis": "20日窗口内隔夜为正日的日内水下占比均值−隔夜为负日的均值。体检:disc-0.0025/审计-0.0306(弱)，非shadow(corr 0.23)。",
        "expected_sign": -1,
    },
    {
        "id": "S27A5", "operator": "atomic", "left": _MATCH_CHG, "right": _MATCH_CHG,
        "mechanism": "on_trough_recovery_match_chg_20",
        "hypothesis": "ON_TROUGH_RECOVERY_MATCH_20的20日变化。体检:disc+0.0082/审计+0.0341(弱)，非shadow(corr 0.22)。",
        "expected_sign": 1,
    },
    {
        "id": "S27A6", "operator": "atomic", "left": _RATIO_CHG, "right": _RATIO_CHG,
        "mechanism": "gap_dd_consumption_ratio_chg_20",
        "hypothesis": "GAP_DD_CONSUMPTION_RATIO_20的20日变化。体检:disc+0.0007/审计-0.0571(符号翻转，不稳)，非shadow(corr 0.22)。",
        "expected_sign": 1,
    },
    # ---- GAP_DD_CONSUMPTION_RATIO_20: first pairing batch (strongest atom) ----
    {"id": "S27B1", "operator": "rank_spread", "left": _RATIO, "right": _UF_CHG,
     "mechanism": "gap_dd_ratio_confirmed_by_underwater_frac_chg_20",
     "hypothesis": "A=日内最大回撤/隔夜跳空之比20日均值(体检disc-0.0851/审计-0.0711同向强)。B=日内水下占比20日变化(S7本线单原子审计最高,intraday_drawdown_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27B2", "operator": "rank_spread", "left": _RATIO, "right": _LUNCH_PRERUN_POSTRUN,
     "mechanism": "gap_dd_ratio_confirmed_by_lunch_prerun_postrun_ratio_20",
     "hypothesis": "A=同上。B=午前/午后抢跑成交量份额之比(S22原子级入选KA7,lunch_break_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27B3", "operator": "rank_spread", "left": _RATIO, "right": _TRR,
     "mechanism": "gap_dd_ratio_confirmed_by_true_range_ratio_20",
     "hypothesis": "A=同上。B=真实区间比率(S19唯一净入选原子AB1,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27B4", "operator": "rank_spread", "left": _RATIO, "right": _D1_60,
     "mechanism": "gap_dd_ratio_confirmed_by_d1_level_60",
     "hypothesis": "A=同上。B=价格延迟D1水平(S20入选原子搭档,price_delay,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27B5", "operator": "rank_spread", "left": _RATIO, "right": _MFI_EXTREME_FRAC,
     "mechanism": "gap_dd_ratio_confirmed_by_mfi_extreme_frac_20",
     "hypothesis": "A=同上。B=MFI极端占比(S23阶段最强候选WA1的右腿,accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27B6", "operator": "rank_spread", "left": _RATIO, "right": _COSKEW20,
     "mechanism": "gap_dd_ratio_confirmed_by_coskew_20",
     "hypothesis": "A=同上。B=共偏度20日(coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27B7", "operator": "rank_spread", "left": _RATIO, "right": _VT_AUTOCORR,
     "mechanism": "gap_dd_ratio_confirmed_by_vt_autocorr_20",
     "hypothesis": "A=同上。B=成交量时间收益1桶滞后自相关(S24净入选簇代表XB3的左腿,volume_time_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27B8", "operator": "rank_spread", "left": _RATIO, "right": _AD_NET_FLOW,
     "mechanism": "gap_dd_ratio_confirmed_by_ad_net_flow_20",
     "hypothesis": "A=同上。B=A/D净流20日(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- ON_TROUGH_RECOVERY_MATCH_20: first pairing batch ----
    {"id": "S27C1", "operator": "rank_spread", "left": _MATCH, "right": _WORST_DAY,
     "mechanism": "on_trough_recovery_match_confirmed_by_worst_day_20",
     "hypothesis": "A=隔夜跳空方向与日内逆-顺模式一致率20日均值(体检disc-0.0317/审计-0.0126同向)。B=20日最差单日收益(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27C2", "operator": "rank_spread", "left": _MATCH, "right": _SAMPEN,
     "mechanism": "on_trough_recovery_match_confirmed_by_sampen_ret_20",
     "hypothesis": "A=同上。B=收益样本熵(S11,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27C3", "operator": "rank_spread", "left": _MATCH, "right": _MARKET_BETA20,
     "mechanism": "on_trough_recovery_match_confirmed_by_market_beta_20",
     "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27C4", "operator": "rank_spread", "left": _MATCH, "right": _BEST_DAY,
     "mechanism": "on_trough_recovery_match_confirmed_by_best_day_20",
     "hypothesis": "A=同上。B=20日最佳单日收益(S2,upside_tail,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27C5", "operator": "rank_spread", "left": _MATCH, "right": _GAP_FILL,
     "mechanism": "on_trough_recovery_match_confirmed_by_gap_fill_fraction_20",
     "hypothesis": "A=同上。B=跳空当日回补比例20日(gap_repair,S18/S22入选原子搭档,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27C6", "operator": "rank_spread", "left": _MATCH, "right": _JUMP_BETA,
     "mechanism": "on_trough_recovery_match_confirmed_by_jump_beta_20",
     "hypothesis": "A=同上。B=跳跃beta(S4,jump_continuous_beta,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27C7", "operator": "rank_spread", "left": _MATCH, "right": _YZ_OVERNIGHT,
     "mechanism": "on_trough_recovery_match_confirmed_by_yz_overnight_share_20",
     "hypothesis": "A=同上。B=Yang-Zhang隔夜方差份额(S9,range_based_vol_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "S27C8", "operator": "rank_spread", "left": _MATCH, "right": _GRANGER,
     "mechanism": "on_trough_recovery_match_confirmed_by_granger_in_degree_20",
     "hypothesis": "A=同上。B=Granger因果入度(cross_dependence_1m,本族首次配对)。假设方向由发现期定。本批最后一条，本轮末条。",
     "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
