#!/usr/bin/env python3
"""Round 081 driver: stage 15 step 2 — directed pairing round 1. New
coskewness_risk atoms (round_080, non-shadow: COSKEW_20/60, COSKEW_CHG_20,
DOWNSIDE_COSKEW_60) x already-admitted single atoms from other families
(round_053 atomic winners BIGBAR_VOL_SHARE_20/GAP_FILL_FRACTION_60/
VOL_USHAPE_20; round_079-referenced TICK_IMBALANCE_20/CHIP_RANGE_90_60/
LOG_AMOUNT_VOL_20). Both legs' single-atom gate-7 four numbers are recorded
in the hypothesis field and restated in REPORT.md per the directed-pairing
contract."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_501"

base.CANDIDATES = [
    {
        "id": "RS1",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "mechanism": "downside_coskew_confirmed_by_bigbar_flow",
        "hypothesis": "两腿角色：A=下行条件化协偏度（round_080体检 disc +0.0319/579天 / 审计 +0.0404，identity通过，仅topk未过：t=0.61/审超-8.7bp）；B=大bar成交量占比（round_053 门7全过：disc +0.0832/审计 +0.0548/t=2.92/审超+41.6bp）。假设：系统性崩盘暴露(A高)且大单/知情流入活跃(B高)=暴露有真实资金承接确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RS2",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "mechanism": "downside_coskew_paired_with_gap_absorption",
        "hypothesis": "两腿角色：A=下行协偏度（同上，disc +0.0319/审计+0.0404）；B=缺口回补比例（round_053 门7全过：disc -0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：崩盘暴露高(A高)且缺口易回补(B高，即缺口吸收能力强)=系统性风险被流动性缓冲，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RS3",
        "operator": "rank_spread",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "downside_coskew_paired_with_session_ushape",
        "hypothesis": "两腿角色：A=下行协偏度（同上）；B=日内成交量U型集中度（round_053 门7全过：disc -0.0832/审计-0.0891/t=2.12/审超+33.9bp）。假设：崩盘暴露高(A高)且开收盘成交集中(B高，即两端有主力进出)=暴露伴随主力时点操作，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RS4",
        "operator": "rank_spread",
        "left": {"name": "COSKEW_20", "source": "coskewness_risk"},
        "right": {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"},
        "mechanism": "shortterm_coskew_confirmed_by_orderflow",
        "hypothesis": "两腿角色：A=20日协偏度（round_080体检 disc +0.0016/559天/审计-0.0075，未过abs_ic/audit/identity/topk）；B=主买不平衡（round_079 BM6 单腿读数：disc +0.0240/审计-0.0017/t=0.34/审超-3.0bp）。假设：短窗协偏度高(A高)且日内买流强(B高)=短期协同风险有主动买盘确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RS5",
        "operator": "rank_spread",
        "left": {"name": "COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"},
        "mechanism": "coskew60_locked_by_chip_concentration",
        "hypothesis": "两腿角色：A=60日协偏度（round_080体检 disc +0.0078/551天/审计-0.0310）；B=筹码区间宽度（round_079 BM2 单腿读数：disc -0.0574/审计-0.0620/t=0.70/审超+14.6bp）。假设：协偏度高(A高)且筹码集中(B高即区间窄，锁仓)=系统性风险暴露被锁仓盘固化，延续。",
        "expected_sign": 1,
    },
    {
        "id": "RS6",
        "operator": "rank_spread",
        "left": {"name": "COSKEW_CHG_20", "source": "coskewness_risk"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "coskew_regime_shift_in_liquid_environment",
        "hypothesis": "两腿角色：A=协偏度20日变化（round_080体检 disc +0.0051/531天/审计+0.0341，未过identity/topk）；B=对数成交额（round_079 BM3 单腿读数：disc +0.0661/审计+0.0701/t=2.23/审超+36.8bp，本线最强单腿之一）。假设：协偏度状态正在恶化(A高，即向更负漂移的反向标记)且活跃度高(B高)=状态切换发生在有承接的环境，延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
