#!/usr/bin/env python3
"""Round 095 driver: stage 17 step 1 — volume_time_1m family probe.
Two atomic probes (volume-clock RV ratio / volume-time autocorrelation)
through validate (1m leak hard gate) + batch on the same locked plan."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_095"

base.CANDIDATES = [
    {
        "id": "DA1",
        "operator": "atomic",
        "left": {"name": "VT_RV_RATIO_20", "source": "volume_time_1m"},
        "right": {"name": "VT_RV_RATIO_20", "source": "volume_time_1m"},
        "mechanism": "volume_time_rv_ratio_probe",
        "hypothesis": "验证探针：成交量时间 RV_v / 日历时间 RV（Clark 1973 混合分布假说；波动在体量时间中的集中度）。体检 disc −0.1182 / 审计 −0.0415 / 块 t 2.80 / 审超 +21.2bp。validate 打通新家族 1m 泄漏路径。",
        "expected_sign": -1,
    },
    {
        "id": "DA2",
        "operator": "atomic",
        "left": {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"},
        "right": {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"},
        "mechanism": "volume_time_autocorr_probe",
        "hypothesis": "验证探针：体量时间下收益 1 桶滞后自相关（Ane–Geman 2000；Easley–O'Hara 2012）。体检 disc −0.0822 / 审计 −0.0363 / 块 t 2.32 / 审超 +17.9bp。validate 第二机制。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
