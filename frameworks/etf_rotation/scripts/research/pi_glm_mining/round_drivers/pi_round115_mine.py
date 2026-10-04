#!/usr/bin/env python3
"""Round 115 driver: stage 18 step 1 — lunch_break_1m family probe.
Two atomic probes (AM/PM RV ratio / lunch pre-run volume share) through
validate (1m leak hard gate) + batch on the same locked plan."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_115"

base.CANDIDATES = [
    {
        "id": "DA1",
        "operator": "atomic",
        "left": {"name": "AM_PM_RV_RATIO_20", "source": "lunch_break_1m"},
        "right": {"name": "AM_PM_RV_RATIO_20", "source": "lunch_break_1m"},
        "mechanism": "am_pm_rv_ratio_probe",
        "hypothesis": "验证探针：上午 RV / 下午 RV（Amihud–Mendelson 1987 开盘/收盘方差分解的 A 股午休版；Hong–Wang 2000 周期闭合）。体检 disc −0.0633 / 审计 −0.0672 / 块 t 2.23 / 审超 +16.9bp。validate 打通新家族 1m 泄漏路径。",
        "expected_sign": -1,
    },
    {
        "id": "DA2",
        "operator": "atomic",
        "left": {"name": "LUNCH_PRE_RUN_20", "source": "lunch_break_1m"},
        "right": {"name": "LUNCH_PRE_RUN_20", "source": "lunch_break_1m"},
        "mechanism": "lunch_prerun_probe",
        "hypothesis": "验证探针：午前抢跑量占比（11:20–11:30 尾段 / 全日；Barclay–Hendershott 2003 交易中断前抢跑）。体检 disc +0.0166 / 审计 +0.0618 / 块 t 1.61 / 审超 +13.6bp。validate 第二机制。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
