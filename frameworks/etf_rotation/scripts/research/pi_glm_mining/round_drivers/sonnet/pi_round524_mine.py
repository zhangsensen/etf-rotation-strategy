#!/usr/bin/env python3
"""Round 524 driver: S4 stage step 6 -- jump_continuous_beta pairing, round 6.

Five-round scoreboard (round_519-523, 74 candidates, 7 admitted):
CONTINUOUS_BETA_60 is now confirmed as the productive channel with 3
independent hits, all on asymmetry-themed partners: atomic (JB2),
BIGBAR_DIR_SKEW_20 (round_522, t=3.48 +35.1bp), RETURN_SKEW_20 (round_523,
t=2.86 +15.8bp). Round_523's broader dispersion/breadth/cost-basis sweep
came up empty (0/12) except for that one skew hit -- the signal is
specifically about directional asymmetry / co-moment shape, not general
activity dispersion.

This round pairs CONTINUOUS_BETA_60 against the two families in this line's
catalog that are DIRECTLY about return-distribution asymmetry and have
never once been paired with any jump_continuous_beta atom: coskewness_risk
(Harvey-Siddique 2000 coskewness, Ang-Chen-Xing 2006 downside coskewness,
Dittmar 2002 cokurtosis -- built in this line's own S1 stage) and
upside_tail (Bali-Cakici-Whitelaw 2011 MAX effect, Barberis-Huang 2008
tail-ratio, Kumar 2009 lottery demand -- built in S2). Both were built
specifically to measure asymmetry/tail-shape, making them the most direct
test of the hypothesis that CONTINUOUS_BETA_60's productive dimension is
co-moment asymmetry. TAIL_RATIO_20 (upside/downside tail ratio) is the
single most theory-aligned partner in the whole catalog for this leg.

JUMP_BETA_STABILITY_20 (1/18, flat across 4 follow-up rounds after its one
hit), JUMP_BETA_20 (2/11, flat since round_520), BETA_GAP_20 (0/9) and
CONTINUOUS_BETA_20 (0/6, structurally shadow) get no new candidates --
compute stays on the confirmed channel. No same-family pairs, no repeated
(left,right) combos, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_524"

_COSKEW20 = {"name": "COSKEW_20", "source": "coskewness_risk"}
_COSKEW60 = {"name": "COSKEW_60", "source": "coskewness_risk"}
_COSKEW_CHG20 = {"name": "COSKEW_CHG_20", "source": "coskewness_risk"}
_DOWNSIDE_COSKEW60 = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}
_COKURT60 = {"name": "COKURT_60", "source": "coskewness_risk"}

_BEST_DAY20 = {"name": "BEST_DAY_20", "source": "upside_tail"}
_BEST_DAY60 = {"name": "BEST_DAY_60", "source": "upside_tail"}
_MAX5_MEAN20 = {"name": "MAX5_MEAN_20", "source": "upside_tail"}
_TAIL_RATIO20 = {"name": "TAIL_RATIO_20", "source": "upside_tail"}
_POS_DAY_FRAC_Z20 = {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"}
_INTRADAY_MAXBAR20 = {"name": "INTRADAY_MAXBAR_RET_20", "source": "upside_tail"}
_BEST_DAY20_XVOL = {"name": "BEST_DAY_20_XVOL", "source": "upside_tail"}
_BEST_DAY60_XVOL = {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"}
_MAX5_MEAN20_XVOL = {"name": "MAX5_MEAN_20_XVOL", "source": "upside_tail"}
_INTRADAY_MAXBAR20_XVOL = {"name": "INTRADAY_MAXBAR_RET_20_XVOL", "source": "upside_tail"}

_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}

base.CANDIDATES = [
    # ---- coskewness_risk x CONTINUOUS_BETA_60: direct co-moment-shape test ----
    {
        "id": "KP1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _COSKEW20,
        "mechanism": "continuous_beta60_confirmed_by_coskewness_20",
        "hypothesis": "A=连续分量beta，60日窗（3次asymmetry主题partner命中：atomic, BIGBAR_DIR_SKEW_20 t=3.48, RETURN_SKEW_20 t=2.86）。B=20日协偏度（Harvey-Siddique 2000，本线S1建的家族，从未与本族任何腿配对）。假设：常态系统性暴露高(A高)且协偏度低(B低，crash-sensitive)=常态beta暴露伴随对市场下行的非对称敏感性，延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KP2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _COSKEW60,
        "mechanism": "continuous_beta60_confirmed_by_coskewness_60",
        "hypothesis": "A=同上。B=60日版本（同上，与A同窗对齐）。假设：同KP1，同窗对齐是否更强。",
        "expected_sign": 1,
    },
    {
        "id": "KP3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _COSKEW_CHG20,
        "mechanism": "continuous_beta60_confirmed_by_coskewness_regime_shift",
        "hypothesis": "A=同上。B=协偏度20日变化（Harvey-Siddique衍生，协偏度风险机制切换）。假设：常态系统性暴露高(A高)且协偏度正在恶化(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KP4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _DOWNSIDE_COSKEW60,
        "mechanism": "continuous_beta60_confirmed_by_downside_coskewness",
        "hypothesis": "A=同上。B=条件协偏度，仅用市场下跌日计算（Ang-Chen-Xing 2006 Downside Risk，本族首次使用；与常规coskew相比更直接捕捉危机敏感性）。假设：常态系统性暴露高(A高)且下行协偏度指示危机敏感(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KP5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _COKURT60,
        "mechanism": "continuous_beta60_confirmed_by_cokurtosis",
        "hypothesis": "A=同上。B=协峰度（Dittmar 2002，衡量与市场共同的尾部厚度）。假设：常态系统性暴露高(A高)且协峰度高(B高，共同尾部风险大)=延续。",
        "expected_sign": 1,
    },
    # ---- upside_tail x CONTINUOUS_BETA_60: MAX-effect / lottery-preference
    # asymmetry test; TAIL_RATIO_20 is the single most theory-aligned atom
    # in the whole catalog for this leg (direct upside/downside tail ratio) ----
    {
        "id": "KQ1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _TAIL_RATIO20,
        "mechanism": "continuous_beta60_confirmed_by_tail_ratio",
        "hypothesis": "A=同上。B=上行/下行尾部比率 BEST_DAY_20/|WORST_DAY_20|（Barberis-Huang 2008；本族首次使用，是全目录里与'常态beta的方向不对称'假设最直接对齐的原子）。假设：常态系统性暴露高(A高)且尾部比率偏向上行(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KQ2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _BEST_DAY20,
        "mechanism": "continuous_beta60_confirmed_by_best_day_20",
        "hypothesis": "A=同上。B=20日最佳单日收益（Bali-Cakici-Whitelaw 2011 MAX效应，原始未residualize版本，本族首次使用）。假设：常态系统性暴露高(A高)且近期有强正向单日(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KQ3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _BEST_DAY60,
        "mechanism": "continuous_beta60_confirmed_by_best_day_60",
        "hypothesis": "A=同上。B=60日版本（同上，与A同窗对齐）。假设：同KQ2，同窗是否更强。",
        "expected_sign": 1,
    },
    {
        "id": "KQ4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _MAX5_MEAN20,
        "mechanism": "continuous_beta60_confirmed_by_max5_mean_20",
        "hypothesis": "A=同上。B=最大5日收益均值（Bali-Cakici-Whitelaw稳健MAX(5)变体，原始未residualize版本，本族首次使用）。假设：延续，同KQ2但更稳健的MAX估计。",
        "expected_sign": 1,
    },
    {
        "id": "KQ5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _POS_DAY_FRAC_Z20,
        "mechanism": "continuous_beta60_confirmed_by_pos_day_frac_z",
        "hypothesis": "A=同上。B=正收益日占比的20日z值（Kumar 2009彩票需求regime切换，本族首次使用）。假设：常态系统性暴露高(A高)且正收益日占比异常偏高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KQ6",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _INTRADAY_MAXBAR20,
        "mechanism": "continuous_beta60_confirmed_by_intraday_maxbar_ret",
        "hypothesis": "A=同上。B=日内最大单bar收益20日均值（1m彩票代理，原始未residualize版本，本族首次使用）。假设：延续，日内粒度版本的MAX效应。",
        "expected_sign": 1,
    },
    {
        "id": "KQ7",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _BEST_DAY20_XVOL,
        "mechanism": "continuous_beta60_confirmed_by_best_day_20_xvol",
        "hypothesis": "A=同上。B=BEST_DAY_20对REALIZED_VOL_60的截面残差（round_505去混淆版本，剔除纯波动率水平后的彩票偏好分量，本族首次使用）。假设：延续，测试残差化后信号是否比原始版本更纯净。",
        "expected_sign": 1,
    },
    {
        "id": "KQ8",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _BEST_DAY60_XVOL,
        "mechanism": "continuous_beta60_confirmed_by_best_day_60_xvol",
        "hypothesis": "A=同上。B=BEST_DAY_60对REALIZED_VOL_60的截面残差（同上，60日窗与A对齐）。假设：同KQ7，同窗对齐版本。",
        "expected_sign": 1,
    },
    {
        "id": "KQ9",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _MAX5_MEAN20_XVOL,
        "mechanism": "continuous_beta60_confirmed_by_max5_mean_20_xvol",
        "hypothesis": "A=同上。B=MAX5_MEAN_20残差化版本（同上）。假设：延续，测试稳健MAX估计的残差化版本。",
        "expected_sign": 1,
    },
    {
        "id": "KQ10",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _INTRADAY_MAXBAR20_XVOL,
        "mechanism": "continuous_beta60_confirmed_by_intraday_maxbar_ret_xvol",
        "hypothesis": "A=同上。B=INTRADAY_MAXBAR_RET_20残差化版本（同上，日内粒度）。假设：延续，测试日内MAX效应残差化版本。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
