#!/usr/bin/env python3
"""Round 085 driver: stage 16 step 1 — auction_1m family probe.
Two atomic probes (variance-ratio structure / open volume share) through
validate (1m leak hard gate) + batch on the same locked plan."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_085"

base.CANDIDATES = [
    {
        "id": "AD1",
        "operator": "atomic",
        "left": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "right": {"name": "AUC_VARIANCE_RATIO_20", "source": "auction_1m"},
        "mechanism": "open_close_variance_ratio_probe",
        "hypothesis": "验证探针：开盘/收盘方差比（首 30 分钟 RV / 尾 30 分钟 RV，20 日；Amihud–Mendelson 1987）。体检 disc −0.1123 / 审计 −0.0926 / 块 t 1.46 / 审超 +38.0bp（两窗 IC 同号且强，审超高）。validate 打通新家族 1m 泄漏路径。",
        "expected_sign": -1,
    },
    {
        "id": "AD2",
        "operator": "atomic",
        "left": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "right": {"name": "AUC_OPEN_VOLSHARE_20", "source": "auction_1m"},
        "mechanism": "call_auction_share_probe",
        "hypothesis": "验证探针：首 bar（含 9:25 集合竞价成交）量占全日比例 20 日均值（Barclay–Hendershott 2003 开盘价格发现）。体检 disc −0.0329 / 审计 −0.0035 / 块 t 2.22 / 审超 −8.6bp。validate 第二机制。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
