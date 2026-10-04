#!/usr/bin/env python3
"""Round 074 driver: stage 14 step 2 — atomic gate-7 re-adjudication of the
remaining 6 largebar_footprint_1m atoms (BF1 LBAR_CLOCK_STD_20 admitted and
BF2 LBAR_PERM15_20 rejected-topk were adjudicated in round_073). One atomic
batch, no combos."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_074"

SRC = "largebar_footprint_1m"


def _atom(cid, name, mech, lit, note):
    return {
        "id": cid,
        "operator": "atomic",
        "left": {"name": name, "source": SRC},
        "right": {"name": name, "source": SRC},
        "mechanism": mech,
        "hypothesis": f"{note} 文献：{lit} 体检（round_073 atom_health.csv）：零 shadow（通道最大 |corr| 0.39，货架 0.41）。",
        "expected_sign": 0,
    }


base.CANDIDATES = [
    _atom("BG1", "LBAR_TREND_20_60", "bigbar_share_trend",
          "主控指令趋势构造；Bouchaud–Farmer–Lillo 2009 活动性状态迁移",
          "大 bar 量占比 MA20−MA60（趋势而非窗口变体）。体检 disc +0.0426 / 审计 +0.0206 / 块 t 0.82 / 审超 +23.7bp。"),
    _atom("BG2", "LBAR_SILENT_20", "bigbar_silence_base_rate",
          "Kyle–Obizhaeva 2016 不变量（平静期基率）",
          "无大 bar 交易日占比（20 日）。体检 disc +0.0552 / 审计 +0.0209 / 块 t 0.87 / 审超 +5.6bp；有效日 290<360 预计挂 discovery_days 门。"),
    _atom("BG3", "LBAR_AMTSPLIT_20", "amount_volume_spike_split",
          "主控指令量额分离构造（高价位扫货）",
          "大额不大量 bar 占比。体检 disc −0.0506 / 审计 −0.0113 / 块 t −0.14 / 审超 +9.6bp；有效日 312<360 预计挂 discovery_days 门。"),
    _atom("BG4", "LBAR_OVERNIGHT_20", "overnight_absorption",
          "Chan–Lakonishok 1993/1995（机构单隔夜承接）",
          "大 bar 日次夜隔夜收益 20 日均值。体检 disc +0.0240 / 审计 −0.0017 / 块 t 0.34 / 审超 −3.0bp。"),
    _atom("BG5", "LBAR_RUN_MAX_20", "bigbar_run_consistency",
          "Lillo–Mike–Farmer 2005（metaorder 切分序列）",
          "日内连续同向大 bar 最长游程。体检 disc −0.0273 / 审计 −0.0140 / 块 t 0.27 / 审超 −1.6bp。"),
    _atom("BG6", "LBAR_RET_CONTRIB_20", "bigbar_return_contribution",
          "Bouchaud–Farmer–Lillo 2009（metaorder 收益承载）",
          "大 bar 内收益之和/|全日收益|。体检 disc −0.0164 / 审计 −0.0111 / 块 t 0.55 / 审超 +6.2bp。"),
]

if __name__ == "__main__":
    base.main()
