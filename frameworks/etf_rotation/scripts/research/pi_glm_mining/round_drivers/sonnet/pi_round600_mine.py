#!/usr/bin/env python3
"""Round 600 driver: S23 stage step 1 -- volume_time_drawdown family
(Ane-Geman 2000 volume clock; Easley-Lopez de Prado-O'Hara 2012; same
drawdown-geometry primitives as S7's intraday_drawdown_1m, reapplied to
a 50-bucket volume-time resampled 1m path instead of calendar time),
main controller's pre-specified S23 direction after S22's closure
(round_599).

Atom health (round_600_atom_health, vs intraday_drawdown_1m,
relative_path_vs_basket_1m, path_efficiency, intraday_pain_recovery_1m):
4/8 atoms shadow (VT_UNDERWATER_FRAC_20 corr 0.72, VT_MAXDD_20 corr 0.93,
VT_MAXDD_CHG_20 corr 0.90, VT_RECOVERY_FRAC_20 corr 0.72 -- all vs their
calendar-time counterparts, confirming volume-time reclocking mostly
recovers the SAME signal for level/maxdd atoms). The 4 non-shadow atoms
are the genuinely new slices: VT_UNDERWATER_FRAC_CHG_20 (corr 0.68,
disc-0.046/audit-0.080, same-sign, amplifying), CAL_VT_UF_DIFF_20 (corr
0.37, disc-0.041/audit-0.059, same-sign, the calendar-vs-volume-time
diff construct with the lowest shelf correlation), VT_PATH_EFFICIENCY_20
(corr 0.35, disc+0.020/audit-0.028, sign flip, weak), VT_TROUGH_VOL_POS_20
(corr 0.68 borderline, disc-0.079/audit-0.043, same-sign).

Per the standing 'deepen the strongest channel' pattern (S11/S12 after
S6/S7), this round tests all 8 atomically, then runs the first pairing
batch for the 2 atoms with the cleanest same-sign disc/audit consistency
AND non-shadow status: VT_UNDERWATER_FRAC_CHG_20 (strongest audit
magnitude among non-shadow atoms) and CAL_VT_UF_DIFF_20 (the most novel
construct, lowest shelf corr). VT_MAXDD_CHG_20 and VT_PATH_EFFICIENCY_20
are skipped for this round's pairing batches due to disc/audit sign
flips (unreliable direction); they remain eligible for a future round
per the pairing-discipline rule (2 of 8 atoms' pairing slots still
unused after this round)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_600"

_VT_UF = {"name": "VT_UNDERWATER_FRAC_20", "source": "volume_time_drawdown"}
_VT_UF_CHG = {"name": "VT_UNDERWATER_FRAC_CHG_20", "source": "volume_time_drawdown"}
_VT_MAXDD = {"name": "VT_MAXDD_20", "source": "volume_time_drawdown"}
_VT_MAXDD_CHG = {"name": "VT_MAXDD_CHG_20", "source": "volume_time_drawdown"}
_VT_RECOVERY = {"name": "VT_RECOVERY_FRAC_20", "source": "volume_time_drawdown"}
_CAL_VT_DIFF = {"name": "CAL_VT_UF_DIFF_20", "source": "volume_time_drawdown"}
_VT_PATH_EFF = {"name": "VT_PATH_EFFICIENCY_20", "source": "volume_time_drawdown"}
_VT_TROUGH_POS = {"name": "VT_TROUGH_VOL_POS_20", "source": "volume_time_drawdown"}

_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}
_LUNCH_PRERUN_POSTRUN = {"name": "LUNCH_PRERUN_POSTRUN_RATIO_20", "source": "lunch_break_1m"}
_ON_SIGN_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}
_LAG_COEF_SIGN_FREQ = {"name": "LAG_COEF_SIGN_FREQ_20", "source": "price_delay"}
_TRR = {"name": "TRUE_RANGE_RATIO_20", "source": "range_contraction_cycle"}
_FP_DOWN_CHG = {"name": "FIRST_PASSAGE_DOWN_CHG_20", "source": "first_passage_times_1m"}
_SEMICOV_DOWN_BETA = {"name": "SEMICOV_DOWNSIDE_BETA_20", "source": "realized_semicov_1m"}
_BEST_DAY = {"name": "BEST_DAY_20", "source": "upside_tail"}

_COSKEW20 = {"name": "COSKEW_20", "source": "coskewness_risk"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_VAR_RATIO = {"name": "VAR_RATIO_5_60", "source": "serial_dependence"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_BETA_LF = {"name": "BETA_LF_20", "source": "frequency_domain_beta_1m"}
_MFI_HI_FRAC = {"name": "MFI_EXTREME_HI_FRAC_20", "source": "money_flow_extremes_1m"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}

base.CANDIDATES = [
    # ---- 8 atomic: new volume_time_drawdown atoms ----
    {
        "id": "VA1", "operator": "atomic", "left": _VT_UF, "right": _VT_UF,
        "mechanism": "vt_underwater_frac_20",
        "hypothesis": "成交量时间(50桶/日)下水下占比20日均值(Ane-Geman 2000量钟; Easley-LdP-OHara 2012)。体检:disc-0.0640/审计-0.0245(同向)，shadow(corr 0.72 vs calendar UNDERWATER_FRAC_20)。",
        "expected_sign": -1,
    },
    {
        "id": "VA2", "operator": "atomic", "left": _VT_UF_CHG, "right": _VT_UF_CHG,
        "mechanism": "vt_underwater_frac_chg_20",
        "hypothesis": "成交量时间水下占比20日变化。体检:disc-0.0459/审计-0.0796(同向增强)，非shadow(corr 0.68 vs calendar版)，本轮首个配对左腿。",
        "expected_sign": -1,
    },
    {
        "id": "VA3", "operator": "atomic", "left": _VT_MAXDD, "right": _VT_MAXDD,
        "mechanism": "vt_maxdd_20",
        "hypothesis": "成交量时间最大回撤20日均值(Magdon-Ismail-Atiya 2004,量钟版)。体检:disc-0.1020/审计-0.0712(同向)，shadow(corr 0.93 vs calendar INTRADAY_MAXDD_20，基本同一信号)。",
        "expected_sign": -1,
    },
    {
        "id": "VA4", "operator": "atomic", "left": _VT_MAXDD_CHG, "right": _VT_MAXDD_CHG,
        "mechanism": "vt_maxdd_chg_20",
        "hypothesis": "成交量时间最大回撤20日变化。体检:disc-0.0226/审计+0.0634(符号翻转，不稳)，shadow(corr 0.90)，仅记录不作配对左腿。",
        "expected_sign": -1,
    },
    {
        "id": "VA5", "operator": "atomic", "left": _VT_RECOVERY, "right": _VT_RECOVERY,
        "mechanism": "vt_recovery_frac_20",
        "hypothesis": "成交量时间回撤恢复桶数占比20日均值(Bacon 2008恢复度量,量钟版)。体检:disc-0.0669/审计-0.0600(同向)，shadow(corr 0.72 vs pain_recovery RECOVERY_TIME_FRAC_20)。",
        "expected_sign": -1,
    },
    {
        "id": "VA6", "operator": "atomic", "left": _CAL_VT_DIFF, "right": _CAL_VT_DIFF,
        "mechanism": "cal_vt_uf_diff_20",
        "hypothesis": "日历时间水下占比−成交量时间水下占比(同日)20日均值(检验回撤是否集中在高成交量段)。体检:disc-0.0406/审计-0.0587(同向增强)，非shadow(corr 0.37，本族相关性最低、最新颖的构造)，本轮第二个配对左腿。",
        "expected_sign": -1,
    },
    {
        "id": "VA7", "operator": "atomic", "left": _VT_PATH_EFF, "right": _VT_PATH_EFF,
        "mechanism": "vt_path_efficiency_20",
        "hypothesis": "成交量时间路径效率(|净位移|/路径长度)20日均值。体检:disc+0.0197/审计−0.0276(符号翻转，不稳)，非shadow(corr 0.35)，仅记录不作配对左腿。",
        "expected_sign": 1,
    },
    {
        "id": "VA8", "operator": "atomic", "left": _VT_TROUGH_POS, "right": _VT_TROUGH_POS,
        "mechanism": "vt_trough_vol_pos_20",
        "hypothesis": "成交量时间最大回撤谷底所在的累计成交量相对位置(0=早，1=晚)20日均值。体检:disc-0.0786/审计-0.0434(同向)，非shadow(corr 0.68边界)。",
        "expected_sign": -1,
    },
    # ---- VT_UNDERWATER_FRAC_CHG_20: first pairing batch ----
    {"id": "VB1", "operator": "rank_spread", "left": _VT_UF_CHG, "right": _AD_NET_FLOW,
     "mechanism": "vt_underwater_frac_chg_confirmed_by_ad_net_flow_20",
     "hypothesis": "A=成交量时间水下占比20日变化(体检disc-0.0459/审计-0.0796同向增强)。B=A/D净流20日(S20入选原子搭档,accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VB2", "operator": "rank_spread", "left": _VT_UF_CHG, "right": _LUNCH_PRERUN_POSTRUN,
     "mechanism": "vt_underwater_frac_chg_confirmed_by_lunch_prerun_postrun_ratio_20",
     "hypothesis": "A=同上。B=午前/午后抢跑成交量份额之比(S22原子级入选KA7,t=3.53,lunch_break_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VB3", "operator": "rank_spread", "left": _VT_UF_CHG, "right": _ON_SIGN_STREAK,
     "mechanism": "vt_underwater_frac_chg_confirmed_by_on_sign_streak_20",
     "hypothesis": "A=同上。B=隔夜收益符号连续天数(S21入选原子HB1的左腿,overnight_structure_1d,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VB4", "operator": "rank_spread", "left": _VT_UF_CHG, "right": _LAG_COEF_SIGN_FREQ,
     "mechanism": "vt_underwater_frac_chg_confirmed_by_lag_coef_sign_freq_20",
     "hypothesis": "A=同上。B=价格延迟滞后系数符号频率(S20入选原子GB1的左腿,price_delay,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VB5", "operator": "rank_spread", "left": _VT_UF_CHG, "right": _TRR,
     "mechanism": "vt_underwater_frac_chg_confirmed_by_true_range_ratio_20",
     "hypothesis": "A=同上。B=真实区间比率(S19唯一净入选原子AB1的右腿,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VB6", "operator": "rank_spread", "left": _VT_UF_CHG, "right": _FP_DOWN_CHG,
     "mechanism": "vt_underwater_frac_chg_confirmed_by_first_passage_down_chg_20",
     "hypothesis": "A=同上。B=首达-1σ时间20日变化(S17,first_passage_times_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VB7", "operator": "rank_spread", "left": _VT_UF_CHG, "right": _SEMICOV_DOWN_BETA,
     "mechanism": "vt_underwater_frac_chg_confirmed_by_semicov_downside_beta_20",
     "hypothesis": "A=同上。B=已实现下行半协方差beta(S8,realized_semicov_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VB8", "operator": "rank_spread", "left": _VT_UF_CHG, "right": _BEST_DAY,
     "mechanism": "vt_underwater_frac_chg_confirmed_by_best_day_20",
     "hypothesis": "A=同上。B=20日最佳单日收益(S2,upside_tail,本族首次配对)。假设方向由发现期定。本批最后一条。",
     "expected_sign": -1},
    # ---- CAL_VT_UF_DIFF_20: first pairing batch ----
    {"id": "VC1", "operator": "rank_spread", "left": _CAL_VT_DIFF, "right": _COSKEW20,
     "mechanism": "cal_vt_uf_diff_confirmed_by_coskew_20",
     "hypothesis": "A=日历-成交量时间水下占比之差20日均值(检验回撤是否集中在高成交量段;体检disc-0.0406/审计-0.0587同向增强，本族相关性最低)。B=共偏度20日(coskewness_risk,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VC2", "operator": "rank_spread", "left": _CAL_VT_DIFF, "right": _WORST_DAY,
     "mechanism": "cal_vt_uf_diff_confirmed_by_worst_day_20",
     "hypothesis": "A=同上。B=20日最差单日收益(return_tail_shape,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VC3", "operator": "rank_spread", "left": _CAL_VT_DIFF, "right": _SAMPEN,
     "mechanism": "cal_vt_uf_diff_confirmed_by_sampen_ret_20",
     "hypothesis": "A=同上。B=收益样本熵(S11,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VC4", "operator": "rank_spread", "left": _CAL_VT_DIFF, "right": _VAR_RATIO,
     "mechanism": "cal_vt_uf_diff_confirmed_by_var_ratio_5_60",
     "hypothesis": "A=同上。B=方差比5/60日(serial_dependence,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VC5", "operator": "rank_spread", "left": _CAL_VT_DIFF, "right": _MARKET_BETA20,
     "mechanism": "cal_vt_uf_diff_confirmed_by_market_beta_20",
     "hypothesis": "A=同上。B=对篮子beta20日(market_sensitivity,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VC6", "operator": "rank_spread", "left": _CAL_VT_DIFF, "right": _BETA_LF,
     "mechanism": "cal_vt_uf_diff_confirmed_by_beta_lf_20",
     "hypothesis": "A=同上。B=低频带beta(S13,frequency_domain_beta_1m,本族首次配对，避开冗余磁体BETA_HF_20)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VC7", "operator": "rank_spread", "left": _CAL_VT_DIFF, "right": _MFI_HI_FRAC,
     "mechanism": "cal_vt_uf_diff_confirmed_by_mfi_extreme_hi_frac_20",
     "hypothesis": "A=同上。B=MFI极端高值占比(money_flow_extremes_1m,本族首次配对)。假设方向由发现期定。",
     "expected_sign": -1},
    {"id": "VC8", "operator": "rank_spread", "left": _CAL_VT_DIFF, "right": _GAP_FILL,
     "mechanism": "cal_vt_uf_diff_confirmed_by_gap_fill_fraction_20",
     "hypothesis": "A=同上。B=跳空当日回补比例20日(gap_repair,S18/S22入选原子搭档,本族首次配对)。假设方向由发现期定。本批最后一条，本轮末条。",
     "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
