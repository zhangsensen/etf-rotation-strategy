#!/usr/bin/env python3
"""Round 086 driver: stage 16 step 2 — atomic gate-7 re-adjudication of the
remaining 5 auction_1m atoms (AD1 AUC_VARIANCE_RATIO_20 and AD2
AUC_OPEN_VOLSHARE_20 were adjudicated in round_085 probes)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_086"

SRC = "auction_1m"


def _atom(cid, name, mech, lit, note):
    return {
        "id": cid,
        "operator": "atomic",
        "left": {"name": name, "source": SRC},
        "right": {"name": name, "source": SRC},
        "mechanism": mech,
        "hypothesis": f"{note} 文献：{lit} 体检（round_085 atom_health.csv）：零 shadow。",
        "expected_sign": 0,
    }


base.CANDIDATES = [
    _atom("AE1", "AUC_OPEN_ABSORB_20", "open_gap_absorption",
          "Barclay–Hendershott 2003（开盘信息消化）",
          "首 bar 后 30 分钟收益/首 bar 收益（开盘吸收度）。体检 disc −0.0295 / 审计 −0.0518 / 块 t 0.93 / 审超 +11.7bp。"),
    _atom("AE2", "AUC_CLOSE_VOLSHARE_20", "close_auction_share",
          "Bogousslavsky–Muravyev 2023（收盘竞价）",
          "尾 bar（14:57–15:00）量占全日比。体检 disc +0.0075 / 审计 −0.0540 / 块 t 0.77 / 审超 −11.5bp。"),
    _atom("AE3", "AUC_CLOSE_CONSIST_20", "close_direction_consistency",
          "Bogousslavsky–Muravyev 2023",
          "尾 bar 方向与全日方向一致度。体检 disc −0.0154 / 审计 +0.0111 / 块 t 1.12 / 审超 −23.9bp。"),
    _atom("AE4", "AUC_DISCOVERY_SHIFT_20", "discovery_center_shift",
          "Barclay–Hendershott 2003（价格发现重心）",
          "首 bar 量占比 − 尾 bar 量占比。体检 disc −0.0086 / 审计 +0.0262 / 块 t 0.54 / 审超 −0.7bp。"),
    _atom("AE5", "AUC_POST_OPEN_REVERT_20", "post_open_revert",
          "主控指令（开盘冲击永久性）",
          "开盘后 5 分钟回复比例（60 日窗）。体检 disc −0.0324 / 审计 +0.0215 / 块 t 0.68 / 审超 −16.8bp。"),
]

if __name__ == "__main__":
    base.main()
