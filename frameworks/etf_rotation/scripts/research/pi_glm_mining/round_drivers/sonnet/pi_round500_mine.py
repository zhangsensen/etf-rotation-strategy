#!/usr/bin/env python3
"""Round 080 driver: stage 15 step 1 — coskewness_risk family atomic
gate-7 readjudication (4 non-shadow atoms; COKURT_60 excluded, shadow 0.87
vs market_sensitivity:MARKET_CORR_60 per outputs/round_500/atom_health.csv).
Harvey-Siddique (2000) / Ang-Chen-Xing (2006): assets with lower (more
negative) coskewness/downside-coskewness against the market carry
crash-risk exposure and command a return premium, so expected_sign=-1
(high rank(atom) -> lower subsequent relative return)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_500"

base.CANDIDATES = [
    {
        "id": "CK1",
        "operator": "atomic",
        "left": {"name": "COSKEW_20", "source": "coskewness_risk"},
        "right": {"name": "COSKEW_20", "source": "coskewness_risk"},
        "mechanism": "coskewness_risk_premium_20",
        "hypothesis": "Harvey & Siddique (2000) 协偏度定价：与基准的 20 日协偏度越低（更负）=崩盘风险暴露越高=应获风险溢价，故 rank(COSKEW_20) 与未来相对收益负相关。体检：发现IC +0.0016（559天）/ 审计IC −0.0075，max|shelf corr| 0.45（vs return_tail_shape:RETURN_SKEW_20），非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "CK2",
        "operator": "atomic",
        "left": {"name": "COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "COSKEW_60", "source": "coskewness_risk"},
        "mechanism": "coskewness_risk_premium_60",
        "hypothesis": "同 CK1，60 日窗口协偏度。体检：发现IC +0.0078（551天）/ 审计IC −0.0310，max|shelf corr| 0.51（vs return_tail_shape:RETURN_SKEW_60），非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "CK3",
        "operator": "atomic",
        "left": {"name": "COSKEW_CHG_20", "source": "coskewness_risk"},
        "right": {"name": "COSKEW_CHG_20", "source": "coskewness_risk"},
        "mechanism": "coskewness_risk_regime_shift",
        "hypothesis": "协偏度风险状态切换：COSKEW_60 的 20 日变化。假设协偏度快速下行（更负）=崩盘风险暴露正在上升=应获溢价上升，rank 与未来收益负相关。体检：发现IC +0.0051（531天）/ 审计IC +0.0341，max|shelf corr| 0.27，非shadow。",
        "expected_sign": -1,
    },
    {
        "id": "CK4",
        "operator": "atomic",
        "left": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "right": {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"},
        "mechanism": "downside_coskewness_risk_premium",
        "hypothesis": "Ang, Chen & Xing (2006) 下行条件化协偏度（仅市场下行日）：越负=下行崩盘暴露越高=应获溢价，rank 与未来收益负相关。体检：发现IC +0.0319（579天）/ 审计IC +0.0404，max|shelf corr| 0.48（vs intraday_volume_profile_1m:VOL_ENTROPY_20），非shadow。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
