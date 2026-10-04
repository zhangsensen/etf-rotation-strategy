#!/usr/bin/env python3
"""Round 592 driver: S21 stage step 1 -- overnight_structure_1d family
(Lou-Polk-Skouras 2019 overnight/intraday tug-of-war; Berkman-Koch-
Tuttle-Zhang 2012; Aboody et al. 2018; Cliff-Cooper-Gulen 2008), main
controller's pre-specified S21 direction after S20's closure
(round_591), built as a parallel independent implementation alongside
pi lane's stage 22 (not built by reading pi's code).

Atom health (round_592_atom_health, vs S9's range_based_vol_1m,
intraday_momentum_30m, gap_repair, daily_candle, all registered in this
catalog): 3/8 shadow -- ON_PREM_RATIO_20_60 and ON_VOL_ADJ_RET_20 (both
vs daily_candle:GAP_MEAN_20, expected since both are built from the
overnight-return level) and ON_RV_SHARE_60 (vs gap_volatility, matching
the directive's own prediction of near-duplication with an existing
overnight-variance-share construct, though the specific matched atom
differs from S9's YZ_OVERNIGHT_SHARE_20). 5 non-shadow.
ON_SIGN_STREAK_20 has the strongest same-sign discovery/audit IC
(disc+0.0141/audit+0.0546, full 579-day coverage) and is this round's
sole left leg for the first pairing batch, per the pairing-discipline
rule -- deliberately limited to 1 new left leg (7 remain for future
rounds)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_592"

_SKEW = {"name": "ON_PREM_SKEW_20", "source": "overnight_structure_1d"}
_RATIO = {"name": "ON_PREM_RATIO_20_60", "source": "overnight_structure_1d"}
_CORR = {"name": "ON_INTRADAY_CORR_20", "source": "overnight_structure_1d"}
_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}
_RV_SHARE = {"name": "ON_RV_SHARE_60", "source": "overnight_structure_1d"}
_VOL_ADJ = {"name": "ON_VOL_ADJ_RET_20", "source": "overnight_structure_1d"}
_ABS_MEAN = {"name": "ON_ABS_MEAN_20", "source": "overnight_structure_1d"}
_CHG = {"name": "ON_PREM_CHG_20", "source": "overnight_structure_1d"}

_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENT = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_CONT_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_RCOV_N = {"name": "RCOV_N_SHARE_20", "source": "realized_semicov_1m"}
_MSPE5 = {"name": "MSPE_5M_20", "source": "complexity_measures_1m"}
_TRR = {"name": "TRUE_RANGE_RATIO_20", "source": "range_contraction_cycle"}
_D1_60 = {"name": "D1_LEVEL_60", "source": "price_delay"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}

base.CANDIDATES = [
    # ---- 8 atomic: new overnight_structure_1d atoms ----
    {
        "id": "HA1", "operator": "atomic", "left": _SKEW, "right": _SKEW,
        "mechanism": "on_prem_skew_20",
        "hypothesis": "隔夜收益20日偏度(Aboody et al. 2018情绪代理)。体检:disc+0.0176/审计-0.0205(反号)，max|corr|=0.34(vs daily_candle:GAP_MEAN_20)，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "HA2", "operator": "atomic", "left": _RATIO, "right": _RATIO,
        "mechanism": "on_prem_ratio_20_60",
        "hypothesis": "隔夜收益20/60日均值之比。体检:disc+0.0344/审计+0.0101(同向弱)，max|corr|=0.78(vs daily_candle:GAP_MEAN_20)，**shadow=True**（与隔夜收益水平构造本质重叠，符合预期）。",
        "expected_sign": 1,
    },
    {
        "id": "HA3", "operator": "atomic", "left": _CORR, "right": _CORR,
        "mechanism": "on_intraday_corr_20",
        "hypothesis": "隔夜收益与当日日内收益的20日相关(Berkman-Koch-Tuttle-Zhang 2012持续vs反转)。体检:disc+0.0154/审计+0.0372(同向)，max|corr|=0.60(vs intraday_momentum_30m:OVERNIGHT_FIRST30_CORR_20)，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "HA4", "operator": "atomic", "left": _STREAK, "right": _STREAK,
        "mechanism": "on_sign_streak_20",
        "hypothesis": "隔夜收益方向带符号连续天数20日均值(Aboody et al. 2018情绪持续性)。体检:disc+0.0141/审计+0.0546(同向,本族最强)，579天覆盖，max|corr|=0.67(vs daily_candle:GAP_MEAN_20)，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "HA5", "operator": "atomic", "left": _RV_SHARE, "right": _RV_SHARE,
        "mechanism": "on_rv_share_60",
        "hypothesis": "隔夜方差占总方差比例60日(Yang-Zhang风格)。体检:disc+0.0408/审计+0.0570(同向,数值上强)，max|corr|=0.80(vs gap_volatility同哈希原子)，**shadow=True**（指令预判的近似重复，命中的具体对手原子与S9的YZ_OVERNIGHT_SHARE_20不同但同样确认高度重叠）。",
        "expected_sign": 1,
    },
    {
        "id": "HA6", "operator": "atomic", "left": _VOL_ADJ, "right": _VOL_ADJ,
        "mechanism": "on_vol_adj_ret_20",
        "hypothesis": "首1m bar成交量占比加权后的隔夜收益20日均值(Cliff-Cooper-Gulen 2008)。体检:disc+0.0152/审计-0.0305(反号)，max|corr|=0.73(vs daily_candle:GAP_MEAN_20)，**shadow=True**（量加权后仍与原始隔夜收益水平高度相关，符合预期）。",
        "expected_sign": 1,
    },
    {
        "id": "HA7", "operator": "atomic", "left": _ABS_MEAN, "right": _ABS_MEAN,
        "mechanism": "on_abs_mean_20",
        "hypothesis": "隔夜收益绝对值20日均值(幅度维度，与带符号均值不同)。体检:disc-0.0061/审计+0.0077(接近零)，max|corr|=0.58(vs range_based_vol_1m:YZ_OVERNIGHT_SHARE_20)，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "HA8", "operator": "atomic", "left": _CHG, "right": _CHG,
        "mechanism": "on_prem_chg_20",
        "hypothesis": "隔夜收益20日均值的20日变化。体检:disc+0.0191/审计-0.0193(反号)，max|corr|=0.56(vs daily_candle:GAP_MEAN_20)，非shadow。",
        "expected_sign": 1,
    },
    # ---- ON_SIGN_STREAK_20: first pairing batch (strongest same-sign atom, full coverage) ----
    {
        "id": "HB1", "operator": "rank_spread", "left": _STREAK, "right": _UF_CHG,
        "mechanism": "on_sign_streak_confirmed_by_underwater_frac_chg_20",
        "hypothesis": "A=隔夜方向带符号连续天数(情绪持续性,A高=连续正隔夜)。B=主动水下时长20日变化(S7阶段本线单原子审计最高,intraday_drawdown_1m,本族首次配对)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "HB2", "operator": "rank_spread", "left": _STREAK, "right": _PERM_ENT,
        "mechanism": "on_sign_streak_confirmed_by_perm_entropy_ret_20",
        "hypothesis": "A=同上。B=收益排列熵(S6阶段,permutation_entropy_1m,本族首次配对)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "HB3", "operator": "rank_spread", "left": _STREAK, "right": _CONT_BETA,
        "mechanism": "on_sign_streak_confirmed_by_continuous_beta_60",
        "hypothesis": "A=同上。B=对篮子连续beta(S4阶段,jump_continuous_beta,本族首次配对)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "HB4", "operator": "rank_spread", "left": _STREAK, "right": _RCOV_N,
        "mechanism": "on_sign_streak_confirmed_by_rcov_n_share_20",
        "hypothesis": "A=同上。B=同负半协方差份额(S8入选原子,realized_semicov_1m,本族首次配对)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "HB5", "operator": "rank_spread", "left": _STREAK, "right": _MSPE5,
        "mechanism": "on_sign_streak_confirmed_by_mspe_5m_20",
        "hypothesis": "A=同上。B=5分钟多尺度排列熵(S11阶段,complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "HB6", "operator": "rank_spread", "left": _STREAK, "right": _TRR,
        "mechanism": "on_sign_streak_confirmed_by_true_range_ratio_20",
        "hypothesis": "A=同上。B=真实区间比率(S19唯一净入选原子,range_contraction_cycle,本族首次配对)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "HB7", "operator": "rank_spread", "left": _STREAK, "right": _D1_60,
        "mechanism": "on_sign_streak_confirmed_by_d1_level_60",
        "hypothesis": "A=同上。B=价格延迟D1水平(S20入选原子,price_delay,本族首次配对)。假设方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "HB8", "operator": "rank_spread", "left": _STREAK, "right": _AD_NET_FLOW,
        "mechanism": "on_sign_streak_confirmed_by_ad_net_flow_20",
        "hypothesis": "A=同上。B=A/D净流20日(S20入选原子搭档,accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。本批最后一条。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
