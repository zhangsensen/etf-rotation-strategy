#!/usr/bin/env python3
"""Round 096 driver: stage 17 step 2 — atomic gate-7 re-adjudication of the
remaining 4 volume_time_1m atoms (DA2 VT_AUTOCORR_20 admitted and DA1
VT_RV_RATIO_20 rejected-by-shadow were adjudicated in round_095 probes)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_096"

SRC = "volume_time_1m"


def _atom(cid, name, mech, lit, note):
    return {
        "id": cid,
        "operator": "atomic",
        "left": {"name": name, "source": SRC},
        "right": {"name": name, "source": SRC},
        "mechanism": mech,
        "hypothesis": f"{note} 文献：{lit} 体检（round_095 atom_health.csv）：零 shadow（最大 0.565 vs VPIN）。",
        "expected_sign": 0,
    }


base.CANDIDATES = [
    _atom("DB1", "VT_BUCKET_GINI_20", "bucket_arrival_gini",
          "Easley–O'Hara 2012 体量钟（交易到达不均匀度）",
          "桶间隔时长 Gini。体检 disc −0.0398 / 审计 −0.0649 / 块 t 1.61 / 审超 +24.5bp（审计 IC 强）。"),
    _atom("DB2", "VT_SKEW_20", "volume_time_skew",
          "Clark 1973 混合分布假说",
          "体量时间收益偏度。体检 disc +0.0158 / 审计 +0.0026 / 块 t 1.27 / 审超 +8.9bp。"),
    _atom("DB3", "VT_TAIL_MOM_20", "volume_time_tail_momentum",
          "主控指令（体量时间动量）",
          "最近 20% 体量桶累计收益 − 全日收益。体检 disc +0.0034 / 审计 +0.0067 / 块 t −0.49 / 审超 −4.7bp。"),
    _atom("DB4", "VT_BUCKET_COUNT_SHIFT_20", "bucket_count_trend",
          "主控指令（活跃度趋势）",
          "滚动基准桶计数 MA20 − MA60。体检 disc −0.0488 / 审计 +0.0781 / 块 t 0.44 / 审超 −47.1bp（审超强反号）。"),
]

if __name__ == "__main__":
    base.main()
