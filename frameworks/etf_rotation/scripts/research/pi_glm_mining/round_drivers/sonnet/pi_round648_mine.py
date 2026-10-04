#!/usr/bin/env python3
"""Round 648 driver: S47 stage continuation (round_647 found 4 net
admissions, stage not exhausted; main controller directive, 2026-09-21).

round_647 used its 3 base left legs (CLOSE5_CONSIST_PERMENT_SPLIT_20,
BBWIDTH_CHG_SAMPEN_SPLIT_20, OVERNIGHT_SHARE_PMCONSIST_SPLIT_20) for
their one pairing batch each (pairing discipline), and all 7 right legs
used (UNDERWATER_FRAC_CHG_20, GAP_DD_CONSUMPTION_RATIO_20,
MFI_EXTREME_FRAC_20, CONTINUOUS_BETA_60, BIGBAR_VOL_SHARE_20,
GAP_MEAN_20, FIRST_PASSAGE_UP_CHG_20) hit their 3-distinct-left-leg cap
(each paired with exactly the 3 base left legs). The only remaining
legal left legs in mechanism_atoms_v4 are the two CHG companions
(CLOSE5_CONSIST_PERMENT_SPLIT_CHG_20, BBWIDTH_CHG_SAMPEN_SPLIT_CHG_20),
which were only atomic-tested in round_647, never paired -- this round
gives them their one pairing batch each, using 8 FRESH right-leg atoms
(none of the 7 already-capped ones) shared across both left legs (each
right leg thus used exactly 2 times, under the cap of 3).

16 candidates total (2 left legs x 8 right legs), within the pairing-
discipline-driven range (below the 15-30 mining-round default because
only 2 legal left legs remain in this family; the "legal pairs < 12"
exhaustion trigger does not apply since 16 >= 12)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_648"

_L1CHG = {"name": "CLOSE5_CONSIST_PERMENT_SPLIT_CHG_20", "source": "mechanism_atoms_v4"}
_L2CHG = {"name": "BBWIDTH_CHG_SAMPEN_SPLIT_CHG_20", "source": "mechanism_atoms_v4"}

_ULCER = {"name": "ULCER_20", "source": "downside_risk"}
_UF_Z60 = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}
_MFI_SKEW = {"name": "MFI_EXTREME_UNDERWATER_SKEW_20", "source": "mechanism_atoms_v2"}
_VT_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_PV_ELAST = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}
_PRICE_POS = {"name": "S28_PRICE_POSITION_20", "source": "pi_repl_s28"}
_ON_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}
_FP_DOWN_CHG = {"name": "FIRST_PASSAGE_DOWN_CHG_20", "source": "first_passage_times_1m"}

_RIGHT_POOL = [
    ("ULCER", _ULCER),
    ("UFZ60", _UF_Z60),
    ("MFISKEW", _MFI_SKEW),
    ("VTGINI", _VT_GINI),
    ("PVELAST", _PV_ELAST),
    ("PRICEPOS", _PRICE_POS),
    ("ONSTREAK", _ON_STREAK),
    ("FPDOWNCHG", _FP_DOWN_CHG),
]

base.CANDIDATES = []

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S47E{i}", "operator": "rank_spread", "left": _L1CHG, "right": right,
        "mechanism": f"s47_close5_permentropy_split_chg_x_{tag.lower()}",
        "hypothesis": f"CLOSE5_CONSIST_PERMENT_SPLIT_CHG_20（PH1 机制原子的 20 日变化）× {right['name']}，"
                       "配对纪律首批（round_647 只做了单原子测试，本轮首次配对，右腿均为本阶段未用过的新原子）。",
        "expected_sign": 1,
    })

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S47F{i}", "operator": "rank_spread", "left": _L2CHG, "right": right,
        "mechanism": f"s47_bbwidth_sampen_split_chg_x_{tag.lower()}",
        "hypothesis": f"BBWIDTH_CHG_SAMPEN_SPLIT_CHG_20（BA7 机制原子的 20 日变化）× {right['name']}，"
                       "配对纪律首批。",
        "expected_sign": 1,
    })

if __name__ == "__main__":
    base.main()
