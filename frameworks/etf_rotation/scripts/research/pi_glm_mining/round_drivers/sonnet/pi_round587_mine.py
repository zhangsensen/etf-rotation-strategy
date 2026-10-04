#!/usr/bin/env python3
"""Round 587 driver: S20 stage step 1 -- price_delay family (Hou-Moskowitz
2005 D1/D2, Mech 1993 single-lag coefficient, Boehmer-Wu 2013 daily-vs-
intraday delay comparison), main controller's pre-specified S20
direction after S19's closure (round_586), built as a parallel
independent implementation alongside pi lane's stage 29 (not built by
reading pi's code).

Atom health (round_587_atom_health, vs benchmark_leadlag_1m /
cross_etf_lead_lag / intraday_systematic_share / S13's frequency_domain_
beta_1m / S14's pi_price_delay_1d, all registered in this catalog):
2/8 atoms shadow -- LAG1_COEF_60 (0.81 vs cross_etf_lead_lag:
PEER_LEAD_CORR_60) and D2_LAGSHARE_CHG_20 (0.82 vs
pi_price_delay_1d:PD_D1_CHG_20, confirming this new construct correctly
tracks the SAME underlying delay signal as the pre-existing S14 atom --
expected and reassuring, not a bug). The other 6 non-shadow.
D1_1M_20 has the strongest same-sign discovery/audit IC (disc+0.0912/
audit+0.0741, full 579-day coverage) and is this round's sole left leg
for the first pairing batch, per the pairing-discipline rule --
deliberately limited to 1 new left leg this round (7 remain for future
rounds), learning from S18's mistake of spending a pool's left-batch
allowance too fast."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_587"

_D1_60 = {"name": "D1_LEVEL_60", "source": "price_delay"}
_D2_60 = {"name": "D2_LAGSHARE_60", "source": "price_delay"}
_LAG1 = {"name": "LAG1_COEF_60", "source": "price_delay"}
_LAG_SIGN = {"name": "LAG_COEF_SIGN_FREQ_20", "source": "price_delay"}
_D2_CHG = {"name": "D2_LAGSHARE_CHG_20", "source": "price_delay"}
_D1_1M = {"name": "D1_1M_20", "source": "price_delay"}
_D1_1M_CHG = {"name": "D1_1M_CHG_20", "source": "price_delay"}
_D1_DIFF = {"name": "D1_DIFF_1D_1M_20", "source": "price_delay"}

_COSKEW20 = {"name": "COSKEW_20", "source": "coskewness_risk"}
_SESSION_MEAN = {"name": "SESSION_MEAN_20", "source": "daily_candle"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}
_BETA_LF_CHG = {"name": "BETA_LF_CHG_20", "source": "frequency_domain_beta_1m"}
_RECURRENCE = {"name": "RECURRENCE_RATE_20", "source": "complexity_measures_1m"}
_MAX5_MEAN = {"name": "MAX5_MEAN_20", "source": "upside_tail"}
_DOWNSIDE_DEV = {"name": "DOWNSIDE_DEV_20", "source": "downside_risk"}
_TAIL_Q10 = {"name": "TAIL_Q10_20", "source": "return_tail_shape"}

base.CANDIDATES = [
    # ---- 8 atomic: new price_delay atoms ----
    {
        "id": "DA1", "operator": "atomic", "left": _D1_60, "right": _D1_60,
        "mechanism": "d1_level_60",
        "hypothesis": "Hou-Moskowitz D1水平(60日滚动日频回归vs14ETF等权篮子,含滞后1-4期)。体检:disc+0.0569/578天/审计+0.0722(同向)，max|corr|=0.49，非shadow。D1高=延迟大，预期负相关(延迟大的票未来收益更低,因信息未充分反映)。",
        "expected_sign": -1,
    },
    {
        "id": "DA2", "operator": "atomic", "left": _D2_60, "right": _D2_60,
        "mechanism": "d2_lagshare_60",
        "hypothesis": "Hou-Moskowitz D2(滞后系数绝对值份额)。体检:disc+0.0499/审计+0.0612(同向)，max|corr|=0.50，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "DA3", "operator": "atomic", "left": _LAG1, "right": _LAG1,
        "mechanism": "lag1_coef_60",
        "hypothesis": "Mech 1993单滞后系数。体检:disc-0.0250/审计+0.0042(弱反号)，max|corr|=0.81(vs cross_etf_lead_lag:PEER_LEAD_CORR_60)，**shadow=True**（与同伴领先-滞后相关性构造本质重叠，符合预期）。",
        "expected_sign": 1,
    },
    {
        "id": "DA4", "operator": "atomic", "left": _LAG_SIGN, "right": _LAG_SIGN,
        "mechanism": "lag_coef_sign_freq_20",
        "hypothesis": "滞后系数和为正的20日频率(延迟vs过度反应后反转)。体检:disc+0.0105/审计+0.0053(弱同向)，max|corr|=0.49，非shadow。",
        "expected_sign": 1,
    },
    {
        "id": "DA5", "operator": "atomic", "left": _D2_CHG, "right": _D2_CHG,
        "mechanism": "d2_lagshare_chg_20",
        "hypothesis": "D2的20日变化。体检:disc+0.0007/审计+0.0430(接近零但同向)，max|corr|=0.82(vs pi_price_delay_1d:PD_D1_CHG_20)，**shadow=True**（新构造正确追踪与S14既有原子同源的延迟信号，符合预期，验证实现正确性）。",
        "expected_sign": -1,
    },
    {
        "id": "DA6", "operator": "atomic", "left": _D1_1M, "right": _D1_1M,
        "mechanism": "d1_1m_20",
        "hypothesis": "D1的1m日内类比(篮子滞后1-5bar,按日估计后20日均值)。体检:disc+0.0912/审计+0.0741(同向，本族最强)，579天覆盖，max|corr|=0.66(vs benchmark_leadlag_1m:SYNC_BETA_20)，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "DA7", "operator": "atomic", "left": _D1_1M_CHG, "right": _D1_1M_CHG,
        "mechanism": "d1_1m_chg_20",
        "hypothesis": "D1_1M_20的20日变化。体检:disc+0.0603/审计+0.0097(同向但审计弱)，max|corr|=0.21，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "DA8", "operator": "atomic", "left": _D1_DIFF, "right": _D1_DIFF,
        "mechanism": "d1_diff_1d_1m_20",
        "hypothesis": "日频D1与1m D1之差(Boehmer-Wu 2013框架:哪个频段延迟更慢)。体检:disc-0.0347/审计+0.0242(反号)，max|corr|=0.32，非shadow。",
        "expected_sign": -1,
    },
    # ---- D1_1M_20: first pairing batch (strongest same-sign atom, full coverage) ----
    {
        "id": "DB1", "operator": "rank_spread", "left": _D1_1M, "right": _COSKEW20,
        "mechanism": "d1_1m_confirmed_by_coskew_20",
        "hypothesis": "A=D1的1m日内类比(延迟大=A高)。B=共偏度20日(coskewness_risk,本族首次配对)。假设:延迟大(A高)且共偏度低(B低,尾部风险高)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "DB2", "operator": "rank_spread", "left": _D1_1M, "right": _SESSION_MEAN,
        "mechanism": "d1_1m_confirmed_by_session_mean_20",
        "hypothesis": "A=同上。B=session收益20日均值(daily_candle,本族首次配对)。假设:延迟大(A高)且近期收益弱(B低)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "DB3", "operator": "rank_spread", "left": _D1_1M, "right": _AD_NET_FLOW,
        "mechanism": "d1_1m_confirmed_by_ad_net_flow_20",
        "hypothesis": "A=同上。B=A/D净流20日(accumulation_distribution_1m,本族首次配对)。假设方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "DB4", "operator": "rank_spread", "left": _D1_1M, "right": _BETA_LF_CHG,
        "mechanism": "d1_1m_confirmed_by_beta_lf_chg_20",
        "hypothesis": "A=同上。B=低频带beta20日变化(frequency_domain_beta_1m,本族首次配对)。假设方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "DB5", "operator": "rank_spread", "left": _D1_1M, "right": _RECURRENCE,
        "mechanism": "d1_1m_confirmed_by_recurrence_rate_20",
        "hypothesis": "A=同上。B=递归率20日(complexity_measures_1m,本族首次配对)。假设方向由发现期定。",
        "expected_sign": -1,
    },
    {
        "id": "DB6", "operator": "rank_spread", "left": _D1_1M, "right": _MAX5_MEAN,
        "mechanism": "d1_1m_confirmed_by_max5_mean_20",
        "hypothesis": "A=同上。B=最大5日均值(upside_tail,本族首次配对)。假设:延迟大(A高)且近期无强势上行日(B低)=一致确认，负相关。",
        "expected_sign": -1,
    },
    {
        "id": "DB7", "operator": "rank_spread", "left": _D1_1M, "right": _DOWNSIDE_DEV,
        "mechanism": "d1_1m_confirmed_by_downside_dev_20",
        "hypothesis": "A=同上。B=下行标准差20日(downside_risk,本族首次配对)。假设:延迟大(A高)且下行风险高(B高)=一致确认，正相关。",
        "expected_sign": 1,
    },
    {
        "id": "DB8", "operator": "rank_spread", "left": _D1_1M, "right": _TAIL_Q10,
        "mechanism": "d1_1m_confirmed_by_tail_q10_20",
        "hypothesis": "A=同上。B=收益分布10%分位20日(return_tail_shape,本族首次配对)。假设:延迟大(A高)且10%分位差(B低)=一致确认，正相关。本批最后一条。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
