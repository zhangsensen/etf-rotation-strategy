#!/usr/bin/env python3
"""Round 578 driver: S17 stage step 2 -- first_passage_times_1m pairing,
round 2. Two new left-leg batches from the family's remaining atoms:
FALSE_BREAK_RATE_20 (468 discovery days, disc+0.0148/audit+0.0409, same
sign, sufficient sample) and FIRST_PASSAGE_DOWN_20 (579 days,
disc+0.0227/audit-0.0074, sign flips but ample sample). UP_FIRST_FRAC_20
and SIGMA_CROSSING_COUNT_20 are skipped as left legs: both failed their
own atomic test on discovery_days (164 and 202 days respectively, below
the 360-day minimum) in round_577, so pairing would only shrink the
overlap further -- not worth a batch.

Round_577 found FIRST_PASSAGE_UP_20's pairing batch heavily redundant
(rank_correlation_redundancy) against UNDERWATER_FRAC_CHG_20 /
PERM_ENTROPY_RET_20 / CONTINUOUS_BETA_60 / MSPE_5M_20 partners specifically
(corr 0.74-0.77 with prior admissions sharing those same right legs).
This round's right legs are drawn from 16 different established families
not used in round_577's batch (realized_semicov_1m, return_tail_shape,
path_efficiency, intraday_extremes_timing, market_sensitivity,
gap_repair, market_relative_strength, upside_tail, drawdown_duration,
serial_dependence, downside_risk, daily_candle, frequency_domain_beta_1m,
intraday_pain_recovery_1m, coskewness_risk, return_tail_shape again with
a different atom) to test whether the redundancy pattern is specific to
those four atoms or general to the first_passage_times_1m construct."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_578"

_FALSEBRK = {"name": "FALSE_BREAK_RATE_20", "source": "first_passage_times_1m"}
_DOWN20 = {"name": "FIRST_PASSAGE_DOWN_20", "source": "first_passage_times_1m"}

_RCOV_N = {"name": "RCOV_N_SHARE_20", "source": "realized_semicov_1m"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_PATH_EFF = {"name": "PATH_EFFICIENCY_20", "source": "path_efficiency"}
_EXTREME_TIME = {"name": "EXTREME_TIME_ORDER", "source": "intraday_extremes_timing"}
_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_BEST_DAY = {"name": "BEST_DAY_20", "source": "upside_tail"}

_UNDERWATER_FRACTION = {"name": "UNDERWATER_FRACTION_20", "source": "drawdown_duration"}
_RET_ACF1 = {"name": "RET_ACF1_20", "source": "serial_dependence"}
_ULCER = {"name": "ULCER_20", "source": "downside_risk"}
_SESSION_RET = {"name": "SESSION_RETURN", "source": "daily_candle"}
_BETA_LF = {"name": "BETA_LF_20", "source": "frequency_domain_beta_1m"}
_PAIN_INDEX = {"name": "PAIN_INDEX_20", "source": "intraday_pain_recovery_1m"}
_COSKEW60 = {"name": "COSKEW_60", "source": "coskewness_risk"}
_TAIL_Q10 = {"name": "TAIL_Q10_20", "source": "return_tail_shape"}

base.CANDIDATES = [
    # ---- FALSE_BREAK_RATE_20: first pairing batch ----
    {
        "id": "WA1",
        "operator": "rank_spread",
        "left": _FALSEBRK,
        "right": _RCOV_N,
        "mechanism": "false_break_rate_confirmed_by_rcov_n_share_20",
        "hypothesis": "A=触及0.5sigma后回撤到开盘价的假突破率(体检disc+0.0148/审计+0.0409,468天,同向)。B=同负半协方差份额(S8阶段入选原子RA1,realized_semicov_1m,本族首次配对)。假设:假突破率高(A高,趋势难持续)且同跌集中度高(B高,系统性下行共振)=延续(假突破反映噪声而非趋势，配合系统性下行共振时更可信)。",
        "expected_sign": 1,
    },
    {
        "id": "WA2",
        "operator": "rank_spread",
        "left": _FALSEBRK,
        "right": _WORST_DAY,
        "mechanism": "false_break_rate_confirmed_by_worst_day_20",
        "hypothesis": "A=同上。B=20日最差单日收益(return_tail_shape,本族首次配对)。假设:假突破率高(A高)且近期无严重下行尾部(B高,即最差日不那么差)=延续，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "WA3",
        "operator": "rank_spread",
        "left": _FALSEBRK,
        "right": _PATH_EFF,
        "mechanism": "false_break_rate_confirmed_by_path_efficiency_20",
        "hypothesis": "A=同上。B=20日路径效率(path_efficiency,本族首次配对,体检参照族未曾配对)。假设:假突破率高(A高,日内震荡)且路径效率低(B低,来回震荡而非直线)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "WA4",
        "operator": "rank_spread",
        "left": _FALSEBRK,
        "right": _EXTREME_TIME,
        "mechanism": "false_break_rate_confirmed_by_extreme_time_order_20",
        "hypothesis": "A=同上。B=日内极值出现顺序(intraday_extremes_timing,本族首次配对)。假设方向由发现期定,两者均刻画日内路径形态的不同切面。",
        "expected_sign": 1,
    },
    {
        "id": "WA5",
        "operator": "rank_spread",
        "left": _FALSEBRK,
        "right": _MARKET_BETA20,
        "mechanism": "false_break_rate_confirmed_by_market_beta_20",
        "hypothesis": "A=同上。B=对篮子beta,20日(market_sensitivity,本族首次配对)。假设:假突破率高(A高,弱势)且系统性beta低(B低,非跟随大盘)=一致确认。",
        "expected_sign": -1,
    },
    {
        "id": "WA6",
        "operator": "rank_spread",
        "left": _FALSEBRK,
        "right": _GAP_FILL60,
        "mechanism": "false_break_rate_confirmed_by_gap_fill_fraction_60_20",
        "hypothesis": "A=同上。B=缺口回补比例60日(gap_repair,本族首次配对)。假设:假突破率高(A高)且缺口回补率高(B高,价格倾向均值回归)=一致确认，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "WA7",
        "operator": "rank_spread",
        "left": _FALSEBRK,
        "right": _REL_MOM20,
        "mechanism": "false_break_rate_confirmed_by_rel_market_mom_20",
        "hypothesis": "A=同上。B=相对篮子动量20日(market_relative_strength,本族首次配对)。假设:假突破率高(A高,弱势)且相对动量低(B低)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "WA8",
        "operator": "rank_spread",
        "left": _FALSEBRK,
        "right": _BEST_DAY,
        "mechanism": "false_break_rate_confirmed_by_best_day_20_20",
        "hypothesis": "A=同上。B=20日最佳单日收益(upside_tail,S2阶段家族,本族首次配对)。假设:假突破率高(A高)且近期缺乏强势上行日(B低)=一致确认，正相关。本批最后一条。",
        "expected_sign": 1,
    },
    # ---- FIRST_PASSAGE_DOWN_20: first pairing batch ----
    {
        "id": "WB1",
        "operator": "rank_spread",
        "left": _DOWN20,
        "right": _UNDERWATER_FRACTION,
        "mechanism": "first_passage_down_confirmed_by_underwater_fraction_20",
        "hypothesis": "A=下行首达时间(首次触及-sigma_prev的bar序号,体检disc+0.0227/审计-0.0074,579天,较弱)。B=日频水下时长占比20日(drawdown_duration,与S7的intraday_drawdown_1m不同实现,本族首次配对)。假设:下行触发慢(A高,抗跌)且日频水下时间少(B低)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "WB2",
        "operator": "rank_spread",
        "left": _DOWN20,
        "right": _RET_ACF1,
        "mechanism": "first_passage_down_confirmed_by_ret_acf1_20",
        "hypothesis": "A=同上。B=收益一阶自相关20日(serial_dependence,本族首次配对)。假设方向由发现期定，二者均刻画收益序列的持续性/反转结构。",
        "expected_sign": 1,
    },
    {
        "id": "WB3",
        "operator": "rank_spread",
        "left": _DOWN20,
        "right": _ULCER,
        "mechanism": "first_passage_down_confirmed_by_ulcer_20",
        "hypothesis": "A=同上。B=日频溃疡指数20日(downside_risk,本族首次配对)。假设:下行触发慢(A高,抗跌)且日频溃疡指数低(B低,历史回撤温和)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "WB4",
        "operator": "rank_spread",
        "left": _DOWN20,
        "right": _SESSION_RET,
        "mechanism": "first_passage_down_confirmed_by_session_return_20",
        "hypothesis": "A=同上。B=当日session收益(daily_candle,本族首次配对)。假设:下行触发慢(A高)且当日收益为正(B高)=一致确认，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "WB5",
        "operator": "rank_spread",
        "left": _DOWN20,
        "right": _BETA_LF,
        "mechanism": "first_passage_down_confirmed_by_beta_lf_20",
        "hypothesis": "A=同上。B=低频带beta20日(frequency_domain_beta_1m,S13阶段家族,本族首次配对)。假设:下行触发慢(A高)且低频系统性beta低(B低,非跟随大盘长周期波动)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "WB6",
        "operator": "rank_spread",
        "left": _DOWN20,
        "right": _PAIN_INDEX,
        "mechanism": "first_passage_down_confirmed_by_pain_index_20",
        "hypothesis": "A=同上。B=日内痛苦指数20日(intraday_pain_recovery_1m,S12阶段家族,本族首次配对)。假设:下行触发慢(A高)且日内痛苦指数低(B低)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "WB7",
        "operator": "rank_spread",
        "left": _DOWN20,
        "right": _COSKEW60,
        "mechanism": "first_passage_down_confirmed_by_coskew_60_20",
        "hypothesis": "A=同上。B=共偏度60日(coskewness_risk,与round_577用过的DOWNSIDE_COSKEW_60为同族不同原子,本族首次配对)。假设:下行触发慢(A高)且共偏度正(B高,尾部风险低)=一致确认，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "WB8",
        "operator": "rank_spread",
        "left": _DOWN20,
        "right": _TAIL_Q10,
        "mechanism": "first_passage_down_confirmed_by_tail_q10_20",
        "hypothesis": "A=同上。B=收益分布10%分位20日(return_tail_shape,与本轮WA2用过的WORST_DAY_20为同族不同原子,本族首次配对)。假设:下行触发慢(A高)且10%分位不那么差(B高)=一致确认，正相关。本批最后一条，本轮结束。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
