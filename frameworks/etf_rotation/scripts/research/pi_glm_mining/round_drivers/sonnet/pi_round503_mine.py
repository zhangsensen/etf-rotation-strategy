#!/usr/bin/env python3
"""Round 503 driver: stage 15 step 4 — directed pairing round 3 (final
sweep for DOWNSIDE_COSKEW_60 before declaring this leg exhausted). Pairs
DOWNSIDE_COSKEW_60 against the three legs of the two two-window-significant
admitted combos (Z2 = BIGBAR_DIR_SKEW_20 - VOL_AUTOCORR_20; BB1 =
VOL_SPIKE_FREQ_20 - ULCER_20; single-leg readings from round_018
atom_health.csv and round_079's BM4 hypothesis note), plus two
cross-checks pairing COSKEW_20/COSKEW_60 with strong partners not yet
tried on those specific legs (BIGBAR_EDGE_CONC_20, CATEGORY_VOL_20)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_503"

base.CANDIDATES = [
    {
        "id": "RU1",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "mechanism": "downside_coskew_confirmed_by_bigbar_dir_skew",
        "hypothesis": "两腿角色：A=下行条件化协偏度（round_500体检 disc +0.0319/579天/审计+0.0404，identity通过，仅topk未过）；B=大bar方向偏斜（round_018体检单腿：disc -0.0117/579天/审计+0.0254，本身是Z2入选组合的一条腿，topk历史数字未见单腿记录）。假设：崩盘暴露高(A高)且大单方向一致性偏斜(B高)=暴露伴随方向性大单流，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RU2",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "downside_coskew_confirmed_by_volume_autocorr",
        "hypothesis": "两腿角色：A=下行协偏度（同上）；B=日内成交量自相关（round_018体检单腿：disc -0.0722/579天/审计-0.0551，Z2入选组合的另一条腿，topk历史数字未见单腿记录）。假设：崩盘暴露高(A高)且日内成交呈现持续性模式(B高，即自相关强)=暴露伴随有规律的流动性节奏，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RU3",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "downside_coskew_confirmed_by_volume_spike_freq",
        "hypothesis": "两腿角色：A=下行协偏度（同上）；B=成交量脉冲频率（round_018体检单腿：disc +0.0661/579天/审计+0.0460，BB1入选组合的一条腿，topk历史数字未见单腿记录）。假设：崩盘暴露高(A高)且脉冲式放量频繁(B高)=暴露伴随间歇性冲击型交易，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RU4",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "ULCER_20", "source": "downside_risk"},
        "mechanism": "downside_coskew_confirmed_by_ulcer",
        "hypothesis": "两腿角色：A=下行协偏度（系统性/协同尾部，同上）；B=溃疡指数（round_079 BM4单腿读数：disc -0.0415/审计-0.0607/t0.76/审超+10.7bp，BB1入选组合的另一条腿）。假设：系统性崩盘暴露高(A高)且自身慢性失血低(B高即无长期阴跌)=系统性风险发生在健康推进的资产上而非已阴跌资产，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RU5",
        "operator": "rank_spread",
        "left": {"name": "COSKEW_20", "source": "coskewness_risk"},
        "right": {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"},
        "mechanism": "shortterm_coskew_confirmed_by_edge_concentration",
        "hypothesis": "两腿角色：A=20日协偏度（round_500体检 disc +0.0016/559天/审计-0.0075，未过abs_ic/audit/identity/topk）；B=大bar价格边缘集中度（round_053门7全过：disc -0.0971/审计-0.0459/t=2.55/审超+30.7bp，round_502 RT1已证明与60日下行协偏度强配对）。假设：短窗协偏度高(A高)且边缘集中冲击强(B高)=短期系统性风险有激进订单确认，延续。对照RT1（60日窗）看20日窗是否同样成立。",
        "expected_sign": 1,
    },
    {
        "id": "RU6",
        "operator": "rank_spread",
        "left": {"name": "COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "coskew60_confirmed_by_category_vol",
        "hypothesis": "两腿角色：A=60日协偏度（round_500体检 disc +0.0078/551天/审计-0.0310，未过audit/topk）；B=同类别板块波动率（round_053门7全过：disc -0.0711/审计-0.0653/t=2.42/审超+19.0bp，round_502 RT2已证明与下行协偏度强配对）。假设：60日协偏度状态(A高)叠加板块层面高波动(B高)=系统性风险来自板块共振，延续。对照RT2（下行条件化窗）看无条件60日窗是否同样成立。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
