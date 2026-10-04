#!/usr/bin/env python3
"""Round 106 driver: stage 17 extension — overnight_structure_1d family probe.
Two atomic probes (gap-fill rate / overnight premium) through validate (1d
leak hard gate) + batch on the same locked plan."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_106"

base.CANDIDATES = [
    {
        "id": "AF1",
        "operator": "atomic",
        "left": {"name": "GAP_FILL_RATE_20", "source": "overnight_structure_1d"},
        "right": {"name": "GAP_FILL_RATE_20", "source": "overnight_structure_1d"},
        "mechanism": "gap_fill_rate_probe",
        "hypothesis": "验证探针：隔夜跳空被当日盘中反向消化的频率（20 日；Cliff–Cooper–Gulen 2008 隔夜/日内分解；Lou–Polk–Skouras 2019）。体检 disc −0.0437 / 审计 −0.0320 / 块 t 1.48 / 审超 +19.9bp（审超达标）。validate 打通新家族 1d 泄漏路径。",
        "expected_sign": -1,
    },
    {
        "id": "AF2",
        "operator": "atomic",
        "left": {"name": "ON_PREM_20", "source": "overnight_structure_1d"},
        "right": {"name": "ON_PREM_20", "source": "overnight_structure_1d"},
        "mechanism": "overnight_premium_probe",
        "hypothesis": "验证探针：隔夜收益 20 日均值（Lou–Polk–Skouras 2019 隔夜溢价）。体检 disc +0.0213 / 审计 +0.0135 / 块 t 0.86 / 审超 +1.6bp。validate 第二机制。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
