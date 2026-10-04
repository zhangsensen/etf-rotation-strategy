#!/usr/bin/env python3
"""Round 650 driver: S48 stage continuation (round_649 found 1 net
admission -- S48C2, +56.7bp/t3.16 -- stage not exhausted; main
controller directive, 2026-09-21).

round_649 used 3 left legs (OVERNIGHT_UNDERWATER_SPEARMAN_20,
OVERNIGHT_VARSHARE_UNDERWATER_CORR_60, GAP_SIGMA_MAXDD_SIGMA_CORR_20)
for their one pairing batch each (pairing discipline), and all 7 right
legs used (MFI_EXTREME_FRAC_20, CONTINUOUS_BETA_60, BIGBAR_VOL_SHARE_20,
PERM_ENTROPY_RET_20, SAMPEN_RET_20, VT_BUCKET_GINI_20, ON_SIGN_STREAK_20)
hit their 3-distinct-left-leg cap. The remaining legal left legs in
overnight_underwater_covariance are OVERNIGHT_SIGN_UNDERWATERCHG_CORR_20
(atomic-only in round_649) plus the two CHG companions
(OVERNIGHT_UNDERWATER_SPEARMAN_CHG_20, OVERNIGHT_VARSHARE_UNDERWATER_
CORR_CHG_20) -- this round gives all three their one pairing batch
each, using 8 FRESH right-leg atoms (none of the 7 already-capped
ones).

3 left legs x 8 right legs = 24 candidates, within the 15-30 band."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_650"

_L_SIGNCHG = {"name": "OVERNIGHT_SIGN_UNDERWATERCHG_CORR_20", "source": "overnight_underwater_covariance"}
_L_SPEARMAN_CHG = {"name": "OVERNIGHT_UNDERWATER_SPEARMAN_CHG_20", "source": "overnight_underwater_covariance"}
_L_VARSHARE_CHG = {"name": "OVERNIGHT_VARSHARE_UNDERWATER_CORR_CHG_20", "source": "overnight_underwater_covariance"}

_ULCER = {"name": "ULCER_20", "source": "downside_risk"}
_UF_Z60 = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}
_MFI_SKEW = {"name": "MFI_EXTREME_UNDERWATER_SKEW_20", "source": "mechanism_atoms_v2"}
_PV_ELAST = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}
_PRICE_POS = {"name": "S28_PRICE_POSITION_20", "source": "pi_repl_s28"}
_FP_DOWN_CHG = {"name": "FIRST_PASSAGE_DOWN_CHG_20", "source": "first_passage_times_1m"}
_GAP_MEAN = {"name": "GAP_MEAN_20", "source": "daily_candle"}
_LOG_AMT_VOL = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}

_RIGHT_POOL = [
    ("ULCER", _ULCER),
    ("UFZ60", _UF_Z60),
    ("MFISKEW", _MFI_SKEW),
    ("PVELAST", _PV_ELAST),
    ("PRICEPOS", _PRICE_POS),
    ("FPDOWNCHG", _FP_DOWN_CHG),
    ("GAPMEAN", _GAP_MEAN),
    ("LOGAMTVOL", _LOG_AMT_VOL),
]

base.CANDIDATES = []

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S48E{i}", "operator": "rank_spread", "left": _L_SIGNCHG, "right": right,
        "mechanism": f"s48_overnight_sign_underwaterchg_x_{tag.lower()}",
        "hypothesis": f"OVERNIGHT_SIGN_UNDERWATERCHG_CORR_20 × {right['name']}，配对纪律首批（round_649 只做了单原子测试）。",
        "expected_sign": 1,
    })

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S48F{i}", "operator": "rank_spread", "left": _L_SPEARMAN_CHG, "right": right,
        "mechanism": f"s48_overnight_underwater_spearman_chg_x_{tag.lower()}",
        "hypothesis": f"OVERNIGHT_UNDERWATER_SPEARMAN_CHG_20 × {right['name']}，配对纪律首批。",
        "expected_sign": 1,
    })

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S48G{i}", "operator": "rank_spread", "left": _L_VARSHARE_CHG, "right": right,
        "mechanism": f"s48_overnight_varshare_underwater_chg_x_{tag.lower()}",
        "hypothesis": f"OVERNIGHT_VARSHARE_UNDERWATER_CORR_CHG_20 × {right['name']}，配对纪律首批。",
        "expected_sign": 1,
    })

if __name__ == "__main__":
    base.main()
