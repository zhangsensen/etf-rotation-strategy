#!/usr/bin/env python3
"""Round 666 driver: S60 tail round (same pattern as S54's round_657 ->
round_658/659 tail rounds). round_665's main S60 batch (27 candidates)
identified TURNVOL_ENTROPY_SPLIT_20 (S60A2) as the only base mechanism
atom to gate-7 pass standalone (H5 disc t 2.45, positive audit IC/excess;
the other two -- VOLSPIKE_NOISECHG_SPLIT_20, LIQSHOCK_MFI_SPLIT_20 --
both flipped sign discovery-to-audit and failed atomically). Per S60's
"plus the 20-day change of the strongest one" instruction, its 20-day
change (TURNVOL_ENTROPY_SPLIT_CHG_20) was already implemented in
mechanism_atoms_v5.py during round_665 but could not be tested there
because PLAN.json is immutable once locked.

This round: single-atom gate-7 re-adjudication for TURNVOL_ENTROPY_SPLIT_CHG_20
+ a 6-candidate pairing batch. All 8 right legs from round_665's S60
batch already hit the <=3-lefts-per-stage pairing-discipline cap (each
used once per S60A1/A2/A3), so this batch uses a fresh 6-atom right-leg
pool that saw no use in round_665's S60 batch."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_666"

_TURNVOL_CHG = {"name": "TURNVOL_ENTROPY_SPLIT_CHG_20", "source": "mechanism_atoms_v5"}

_ULCER_INDEX = {"name": "ULCER_INDEX_20", "source": "intraday_pain_recovery_1m"}
_RECOVERY_TIME_FRAC = {"name": "RECOVERY_TIME_FRAC_20", "source": "intraday_pain_recovery_1m"}
_INTRADAY_MAXDD = {"name": "INTRADAY_MAXDD_20", "source": "intraday_drawdown_1m"}
_LUNCH_POST_RUN = {"name": "LUNCH_POST_RUN_20", "source": "lunch_break_1m"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}

_RIGHT_LEG_POOL_2 = [
    ("I1", _ULCER_INDEX),
    ("I2", _RECOVERY_TIME_FRAC),
    ("I3", _INTRADAY_MAXDD),
    ("I4", _LUNCH_POST_RUN),
    ("I5", _VOL_ENTROPY),
    ("I6", _BIGBAR_VOL_SHARE),
]

CANDIDATES = [
    {"id": "S60A4", "operator": "atomic", "left": _TURNVOL_CHG, "right": _TURNVOL_CHG,
     "mechanism": "s60_turnvol_entropy_split_chg_atomic",
     "hypothesis": "S60的'最强者20日变化'要求：TURNVOL_ENTROPY_SPLIT_20(round_665唯一单原子门7通过者，"
                   "H5发现t2.45)的20日差分。若切分差值本身在持续走阔/收窄，可能比水平值更早捕捉"
                   "换手波动-复杂度关系的转折方向。",
     "expected_sign": 1},
]

for tag, right in _RIGHT_LEG_POOL_2:
    CANDIDATES.append({
        "id": f"S60P_TEC_{tag}", "operator": "rank_spread", "left": _TURNVOL_CHG, "right": right,
        "mechanism": f"s60_turnvol_entropy_split_chg_x_{right['name'].lower()}",
        "hypothesis": f"TURNVOL_ENTROPY_SPLIT_CHG_20 x {right['name']}：round_665最强机制原子的"
                      "20日变化配已验证原子，完成S60指令的第4个原子。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
