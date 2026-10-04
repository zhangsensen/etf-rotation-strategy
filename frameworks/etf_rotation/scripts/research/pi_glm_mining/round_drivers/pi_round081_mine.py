#!/usr/bin/env python3
"""Round 081 driver: stage 15 step 2 — atomic gate-7 re-adjudication of the
remaining 5 impact_decay_1m atoms (CA1 PV_ELASTICITY_20 and CA2
IMP_PERM_SHARE_20 were adjudicated and admitted in round_080)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_081"

SRC = "impact_decay_1m"


def _atom(cid, name, mech, lit, note):
    return {
        "id": cid,
        "operator": "atomic",
        "left": {"name": name, "source": SRC},
        "right": {"name": name, "source": SRC},
        "mechanism": mech,
        "hypothesis": f"{note} 文献：{lit} 体检（round_080 atom_health.csv）：零 shadow。",
        "expected_sign": 0,
    }


base.CANDIDATES = [
    _atom("CB1", "IMP_DECAY_SLOPE_20", "impact_response_decay",
          "Hasbrouck 1991 VAR 冲击响应；Bouchaud–Farmer–Lillo 2009",
          "1m 收益对滞后 1–5 拍 signed volume 冲击响应衰减斜率。体检 disc +0.0498 / 审计 +0.0005 / 块 t 1.70 / 审超 +4.1bp。"),
    _atom("CB2", "PV_ELAST_SHIFT_20", "elasticity_migration",
          "Kyle–Obizhaeva 2016（弹性迁移）",
          "量价弹性 20 日均值 − 前 20 日均值。体检 disc −0.0734 / 审计 +0.0297 / 块 t 1.62 / 审超 −48.1bp（反号）。"),
    _atom("CB3", "PV_SIGNFLIP_20", "pv_regime_switch_freq",
          "主控指令量价结构构造",
          "日内 corr(Δp, vol) 符号翻转频率。体检 disc +0.0187 / 审计 +0.0029 / 块 t 0.72 / 审超 −20.7bp。"),
    _atom("CB4", "HIVOL_RET5_20", "high_volume_premium",
          "Gervais–Kaniel–Mingelgrin 2001 高量溢价（截面版）",
          "高量日后 5 日累计收益 20 日均值。体检 disc +0.0005 / 审计 −0.0092 / 块 t −0.40 / 审超 +13.7bp；覆盖 212<360 预计挂 discovery_days。"),
    _atom("CB5", "LOVOL_RET5_20", "low_volume_response",
          "Gervais–Kaniel–Mingelgrin 2001 对照组",
          "低量日后 5 日累计收益 20 日均值。体检 disc −0.0058 / 审计 +0.0122 / 块 t −0.45 / 审超 +57.4bp；覆盖 51<360 预计挂 discovery_days。"),
]

if __name__ == "__main__":
    base.main()
