#!/usr/bin/env python3
"""Round 073 driver: stage 14 step 1 — largebar_footprint_1m family probe.
Single atomic candidate through --mode validate (1m leak hard gate). This is
a validation probe, not a search batch; full atomic re-adjudication of the 8
new atoms happens next round per directive."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_073"

base.CANDIDATES = [
    {
        "id": "BF1",
        "operator": "atomic",
        "left": {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"},
        "right": {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"},
        "mechanism": "volume_clock_dispersion_probe",
        "hypothesis": "验证探针：成交量钟桶到时离散度（Easley–O'Hara 2012 体量钟）。体检 disc IC −0.0883 / 审计 −0.0259 / 块 t 3.12 / 审超 +9.6bp。单候选 validate 用于打通 1m 泄漏硬门（截断/扰动副本含新家族 1m 路径）。",
        "expected_sign": -1,
    },
    {
        "id": "BF2",
        "operator": "atomic",
        "left": {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"},
        "right": {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"},
        "mechanism": "impact_permanence_probe",
        "hypothesis": "验证探针：大 bar 后 15 分钟延续比例（Bouchaud–Farmer–Lillo 2009 冲击永久性）。体检 disc IC −0.0949 / 审计 −0.0356 / 块 t 2.56 / 审超 +0.04bp。用于 validate 1m 泄漏路径第二机制。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
