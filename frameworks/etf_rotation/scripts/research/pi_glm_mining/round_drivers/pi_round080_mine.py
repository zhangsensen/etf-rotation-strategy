#!/usr/bin/env python3
"""Round 080 driver: stage 15 step 1 — impact_decay_1m family probe.
Two atomic probes through validate (1m leak hard gate) + batch on the same
locked plan; full atomic re-adjudication of remaining atoms next round."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_080"

base.CANDIDATES = [
    {
        "id": "CA1",
        "operator": "atomic",
        "left": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "right": {"name": "PV_ELASTICITY_20", "source": "impact_decay_1m"},
        "mechanism": "volume_price_elasticity_probe",
        "hypothesis": "验证探针：|Δp| 对 volume 的对数回归弹性 20 日均值（Kyle 1985 / Hasbrouck 2009 价格冲击；Kyle–Obizhaeva 2016 不变量）。体检 disc −0.1249 / 审计 −0.0638 / 块 t 4.00 / 审超 +52.3bp（全程序最强单原子读数）。validate 打通新家族 1m 泄漏路径。",
        "expected_sign": -1,
    },
    {
        "id": "CA2",
        "operator": "atomic",
        "left": {"name": "IMP_PERM_SHARE_20", "source": "impact_decay_1m"},
        "right": {"name": "IMP_PERM_SHARE_20", "source": "impact_decay_1m"},
        "mechanism": "impact_permanence_share_probe",
        "hypothesis": "验证探针：15 分钟后残留冲击/即时冲击（Bouchaud–Farmer–Lillo 2009 永久冲击份额）。体检 disc −0.1050 / 审计 −0.0476 / 块 t 2.67 / 审超 +22.1bp。validate 第二机制。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
