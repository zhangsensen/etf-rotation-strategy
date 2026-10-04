#!/usr/bin/env python3
"""Round 502 driver: stage 15 step 3 — directed pairing round 2. round_501
found DOWNSIDE_COSKEW_60 x VOL_USHAPE_20 closest to gate 7 (t_block5_disc
1.88, just under 2.0; audit excess +18.9bp, well above 5bp). This round
retries DOWNSIDE_COSKEW_60 against the four round_053-admitted atoms not
yet paired (BIGBAR_EDGE_CONC_20, CATEGORY_VOL_20, VOL_PROFILE_DISTANCE,
WORST_DAY_20), plus two more coskewness legs against VOL_PROFILE_DISTANCE
(round_053's highest-t single atom, t=4.04) and WORST_DAY_20."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_502"

base.CANDIDATES = [
    {
        "id": "RT1",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "mechanism": "downside_coskew_confirmed_by_edge_concentration",
        "hypothesis": "两腿角色：A=下行条件化协偏度（round_500体检 disc +0.0319/579天/审计+0.0404，identity通过，仅topk未过）；B=大bar价格边缘集中度（round_053门7全过：disc -0.0971/审计-0.0459/t=2.55/审超+30.7bp，7个admitted原子里t值第二高）。假设：崩盘暴露高(A高)且大单价格冲击集中在边缘(B高)=暴露伴随激进冲击型订单，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RT2",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "downside_coskew_confirmed_by_category_vol",
        "hypothesis": "两腿角色：A=下行协偏度（同上）；B=同类别板块波动率（round_053门7全过：disc -0.0711/审计-0.0653/t=2.42/审超+19.0bp）。假设：崩盘暴露高(A高)且所属类别本身高波动(B高)=系统性风险来自板块层面共振，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RT3",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "downside_coskew_confirmed_by_volume_profile_shift",
        "hypothesis": "两腿角色：A=下行协偏度（同上）；B=日内成交量分布对同伴均值的偏离（round_053门7全过：disc +0.0952/审计+0.0442/t=4.04/审超+10.1bp，7个admitted原子里t值最高）。假设：崩盘暴露高(A高)且日内成交结构偏离常态(B高)=暴露伴随异常成交时点结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RT4",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "downside_coskew_confirmed_by_own_worst_day",
        "hypothesis": "两腿角色：A=下行协偏度（同上，系统性/协同尾部）；B=自身20日最差单日收益（round_053门7全过：disc +0.0635/审计+0.0648/t=2.18/审超+16.2bp，自身独立尾部）。假设：系统性崩盘暴露高(A高)且自身独立尾部也重(B高)=系统性与特质性尾部风险叠加，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RT5",
        "operator": "rank_spread",
        "left": {"name": "COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "coskew60_confirmed_by_volume_profile_shift",
        "hypothesis": "两腿角色：A=60日协偏度（round_500体检 disc +0.0078/551天/审计-0.0310，未过audit/topk）；B=日内成交量分布偏离（同RT3，t=4.04本线最强单腿之一）。假设：协偏度状态(A高)叠加异常日内结构(B高)确认，延续。与RT3对照同一强partner下不同coskew窗口的表现差异。",
        "expected_sign": 1,
    },
    {
        "id": "RT6",
        "operator": "rank_spread",
        "left": {"name": "COSKEW_CHG_20", "source": "coskewness_risk"},
        "right": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "mechanism": "coskew_regime_shift_confirmed_by_own_worst_day",
        "hypothesis": "两腿角色：A=协偏度20日变化（round_500体检 disc +0.0051/531天/审计+0.0341，未过identity/topk）；B=自身20日最差单日收益（同RT4，t=2.18）。假设：协偏度状态正在切换(A高)且自身尾部已重(B高)=状态切换发生在已有特质尾部风险的资产上，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
