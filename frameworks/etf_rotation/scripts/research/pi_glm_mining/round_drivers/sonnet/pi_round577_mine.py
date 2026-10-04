#!/usr/bin/env python3
"""Round 577 driver: S17 stage step 1 -- first_passage_times_1m family
(Zumbach 2007 / Guillaume et al. 1997 directional-change and
first-passage-time framing, Karatzas-Shreve first passage times,
Bollerslev-Todorov 2011 extreme-arrival timing), main controller's
pre-specified S17 direction after S16's closure (round_576).

Atom health (round_577_atom_health, vs intraday_extremes_timing /
intraday_return_path / path_efficiency / S7's intraday_drawdown_1m, all
registered in this catalog): all 8 atoms non-shadow (max |corr| 0.58,
FIRST_PASSAGE_UP_20 vs gap_volatility). FIRST_PASSAGE_UP_20 has the
strongest and most stable discovery/audit IC with full 579-day discovery
coverage (disc +0.0631, audit +0.0256, same sign) and is chosen as this
round's sole left leg for the first pairing batch, per the
pairing-discipline rule. Right legs are 8 atoms from 8 distinct
established families, all but one volume-free (per S17's "no fixed
threshold, no volume" design intent -- DOWNSIDE_COSKEW_60 is the sole
volume-adjacent-family exception, included for family diversity)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_577"

_UP20 = {"name": "FIRST_PASSAGE_UP_20", "source": "first_passage_times_1m"}
_DOWN20 = {"name": "FIRST_PASSAGE_DOWN_20", "source": "first_passage_times_1m"}
_ASYM = {"name": "PASSAGE_ASYM_20", "source": "first_passage_times_1m"}
_UPFIRST = {"name": "UP_FIRST_FRAC_20", "source": "first_passage_times_1m"}
_FALSEBRK = {"name": "FALSE_BREAK_RATE_20", "source": "first_passage_times_1m"}
_CROSSCNT = {"name": "SIGMA_CROSSING_COUNT_20", "source": "first_passage_times_1m"}
_UPCHG = {"name": "FIRST_PASSAGE_UP_CHG_20", "source": "first_passage_times_1m"}
_DOWNCHG = {"name": "FIRST_PASSAGE_DOWN_CHG_20", "source": "first_passage_times_1m"}

_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENT = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_CONT_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_YZ_OVN = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_MSPE5 = {"name": "MSPE_5M_20", "source": "complexity_measures_1m"}
_REL_MAXDD_CHG = {"name": "REL_MAXDD_CHG_20", "source": "relative_path_vs_basket_1m"}
_DOWNSIDE_COSKEW = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}

base.CANDIDATES = [
    # ---- 8 atomic: new first_passage_times_1m atoms ----
    {
        "id": "VA1",
        "operator": "atomic",
        "left": _UP20,
        "right": _UP20,
        "mechanism": "first_passage_up_20",
        "hypothesis": "Karatzas-Shreve首达时间框架，价格首次触及+sigma_prev(前20日日收益std标定，无固定阈值)的bar序号，未触及记全日bar数，20日均值。体检:disc+0.0631/579天/审计+0.0256(同向)，max|corr|=0.58(vs gap_volatility)，非shadow。首达越快=动量越强，预期负相关(首达早=后续收益更高，值越小越好)。",
        "expected_sign": -1,
    },
    {
        "id": "VA2",
        "operator": "atomic",
        "left": _DOWN20,
        "right": _DOWN20,
        "mechanism": "first_passage_down_20",
        "hypothesis": "对称的下行首达时间(首次触及-sigma_prev的bar序号)，20日均值。体检:disc+0.0227/审计-0.0074(弱且反号)，max|corr|=0.58，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "VA3",
        "operator": "atomic",
        "left": _ASYM,
        "right": _ASYM,
        "mechanism": "passage_asym_20",
        "hypothesis": "下行首达-上行首达(方向性首达不对称)。体检:disc-0.0344/审计-0.0128(同向)，max|corr|=0.43(vs intraday_drawdown_1m:DD_RUNUP_ASYM_20)，非shadow。值越大=上行越容易触发=看多信号,预期负相关。",
        "expected_sign": -1,
    },
    {
        "id": "VA4",
        "operator": "atomic",
        "left": _UPFIRST,
        "right": _UPFIRST,
        "mechanism": "up_first_frac_20",
        "hypothesis": "Zumbach 2007方向框架，先触+sigma的天数占比，20日均值(仅164天有效，两阈值均触及的日子才计入)。体检:disc+0.0434/审计+0.0492(同向且更强)，max|corr|=0.46，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "VA5",
        "operator": "atomic",
        "left": _FALSEBRK,
        "right": _FALSEBRK,
        "mechanism": "false_break_rate_20",
        "hypothesis": "触及0.5sigma后回撤到开盘价的假突破率，20日均值(468天有效)。体检:disc+0.0148/审计+0.0409(同向增强)，max|corr|=0.27(vs intraday_drawdown_1m:INTRADAY_MAXRUNUP_20)，非shadow。假突破率高=趋势不可持续，预期正相关(高假突破率预示反转，与未来收益关系需由发现期定)。",
        "expected_sign": 1,
    },
    {
        "id": "VA6",
        "operator": "atomic",
        "left": _CROSSCNT,
        "right": _CROSSCNT,
        "mechanism": "sigma_crossing_count_20",
        "hypothesis": "Zumbach/Guillaume方向变化事件计数(threshold=sigma_prev)，20日均值(202天有效)。体检:disc+0.0830(本族最高)/审计-0.0636(反号，样本少)，max|corr|=0.40(vs liquidity_variability)，非shadow。穿越次数多=日内噪声/震荡多，预期负相关。",
        "expected_sign": -1,
    },
    {
        "id": "VA7",
        "operator": "atomic",
        "left": _UPCHG,
        "right": _UPCHG,
        "mechanism": "first_passage_up_chg_20",
        "hypothesis": "上行首达时间的20日变化(体检:disc-0.0084/审计-0.0378，max|corr|=0.38，非shadow)。首达时间变长(动量减弱)预期负相关。",
        "expected_sign": -1,
    },
    {
        "id": "VA8",
        "operator": "atomic",
        "left": _DOWNCHG,
        "right": _DOWNCHG,
        "mechanism": "first_passage_down_chg_20",
        "hypothesis": "下行首达时间的20日变化(体检:disc+0.0189/审计-0.0371，max|corr|=0.24，非shadow)。",
        "expected_sign": 1,
    },
    # ---- FIRST_PASSAGE_UP_20: first pairing batch (best non-shadow atom, full-coverage, same-sign disc/audit) ----
    {
        "id": "VB1",
        "operator": "rank_spread",
        "left": _UP20,
        "right": _UF_CHG,
        "mechanism": "first_passage_up_confirmed_by_underwater_frac_chg_20",
        "hypothesis": "A=上行首达时间(首达越快=越强)。B=主动水下时长20日变化(S7阶段本线单原子审计最高，intraday_drawdown_1m，本族首次配对)。假设:上行首达快(A低)且水下时长在恶化(B高，与A方向相悖)=矛盾信号减弱；若两者同向确认(A低B低=强势未恶化)则延续。方向由发现期定。",
        "expected_sign": 1,
    },
    {
        "id": "VB2",
        "operator": "rank_spread",
        "left": _UP20,
        "right": _PERM_ENT,
        "mechanism": "first_passage_up_confirmed_by_perm_entropy_ret_20",
        "hypothesis": "A=同上。B=收益排列熵(S6阶段本线首个不含成交量两窗口显著原子，permutation_entropy_1m，本族首次配对)。假设:上行首达快(A低)且收益序列更规律(B低，非随机趋势更强)=延续，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "VB3",
        "operator": "rank_spread",
        "left": _UP20,
        "right": _CONT_BETA,
        "mechanism": "first_passage_up_confirmed_by_continuous_beta_60_20",
        "hypothesis": "A=同上。B=对14只篮子的连续beta(S4阶段，jump_continuous_beta，本族首次配对)。假设:上行首达快(A低)且系统性beta高(B高，跟随大盘发力)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "VB4",
        "operator": "rank_spread",
        "left": _UP20,
        "right": _NOISE_VAR,
        "mechanism": "first_passage_up_confirmed_by_noise_var_20",
        "hypothesis": "A=同上。B=微观结构噪声方差(S5阶段，microstructure_noise_1m，本族首次配对)。假设:上行首达快(A低)且噪声低(B低，信号纯净)=延续，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "VB5",
        "operator": "rank_spread",
        "left": _UP20,
        "right": _YZ_OVN,
        "mechanism": "first_passage_up_confirmed_by_yz_overnight_share_20",
        "hypothesis": "A=同上。B=Yang-Zhang隔夜波动份额(S9阶段本线配对最高t原子，range_based_vol_1m，本族首次配对)。假设:上行首达快(A低)且隔夜份额高(B高，隔夜驱动为主)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "VB6",
        "operator": "rank_spread",
        "left": _UP20,
        "right": _MSPE5,
        "mechanism": "first_passage_up_confirmed_by_mspe_5m_20",
        "hypothesis": "A=同上。B=5分钟多尺度排列熵(S11阶段，complexity_measures_1m，本族首次配对)。假设:上行首达快(A低)且5m尺度熵低(B低，结构规律)=延续，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "VB7",
        "operator": "rank_spread",
        "left": _UP20,
        "right": _REL_MAXDD_CHG,
        "mechanism": "first_passage_up_confirmed_by_rel_maxdd_chg_20",
        "hypothesis": "A=同上。B=主动最大回撤20日变化(S15阶段，relative_path_vs_basket_1m，本族首次配对)。假设:上行首达快(A低)且相对篮子回撤在改善(B低，跑赢篮子)=延续，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "VB8",
        "operator": "rank_spread",
        "left": _UP20,
        "right": _DOWNSIDE_COSKEW,
        "mechanism": "first_passage_up_confirmed_by_downside_coskew_60_20",
        "hypothesis": "A=同上。B=下行共偏度(Ang-Chen-Xing 2006，coskewness_risk，S1早期阶段幸存原子，本族首次配对)。假设:上行首达快(A低)且下行共偏度低(B低，下行风险小)=延续，正相关。本批最后一条，本族8个原子已各自用尽1批。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
