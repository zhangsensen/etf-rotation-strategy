#!/usr/bin/env python3
"""Round 657 driver: S54 stage continuation and closure (main controller
directive, 2026-09-21). S54 named 4 atoms: REL_ULCER_CATEGORY_CHG_20 and
REL_RECOVERY_TIME_CATEGORY_CHG_20 (genuinely new, built + paired in
round_656 -- 3 net admissions, all sharing the ULCER left leg);
REL_UNDERWATER_CATEGORY_CHG_20 (S32A1, already atomically tested in
round_631, only 2 of its 8 pairing slots used there --
R_LOG_AMOUNT_VOL_20 as S32P1, MFI_EXTREME_FRAC_20 as S32P2); and
REL_UNDERWATER_FRAC_CHG_20 (NA2, S15's full-basket-relative atom,
already got its full 8-right-leg pairing batch in round_571 as PA1-PA8,
all rejected -- no further legal pairs remain for it this stage since
its one-batch quota under the standing pairing-discipline rule was
already spent, even though that spend happened in an earlier stage;
re-mining an already-fully-tested weak left leg is not a genuinely new
hypothesis).

This round: REL_UNDERWATER_CATEGORY_CHG_20's ONE remaining stage batch
(<=8 right legs, excluding R_LOG_AMOUNT_VOL_20/MFI_EXTREME_FRAC_20
already tested against it in S32). After this batch, S54's legal
remaining pairs across all 4 named atoms = 0 (<12), so this round also
closes S54 per the "合法配对枚举为零/不足12" contract clause."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_657"

_REL_UW_CHG = {"name": "REL_UNDERWATER_CATEGORY_CHG_20", "source": "category_relative_geometry"}

_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_YZ_OVERNIGHT_SHARE = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_ON_SIGN_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}
_R_VOL_SPIKE_FREQ = {"name": "R_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_a"}

_RIGHT_LEG_POOL = [
    ("A", _GAP_DD_CONSUMPTION),
    ("B", _CONTINUOUS_BETA),
    ("C", _VT_AUTOCORR),
    ("D", _PERM_ENTROPY),
    ("E", _YZ_OVERNIGHT_SHARE),
    ("F", _RESILIENCY),
    ("G", _ON_SIGN_STREAK),
    ("H", _R_VOL_SPIKE_FREQ),
]

CANDIDATES = []
for tag, right in _RIGHT_LEG_POOL:
    CANDIDATES.append({
        "id": f"S54P_UWCAT_{tag}", "operator": "rank_spread", "left": _REL_UW_CHG, "right": right,
        "mechanism": f"s54_rel_underwater_category_chg_x_{right['name'].lower()}",
        "hypothesis": f"REL_UNDERWATER_CATEGORY_CHG_20 x {right['name']}：S32 只测过该左腿配 R_LOG_AMOUNT_VOL_20"
                      "(S32P1,净入选)与MFI_EXTREME_FRAC_20(S32P2,冗余拒绝)；本轮补测其余6个未配过的右腿"
                      "(沿S54机制加深原则)加2个新右腿(ON_SIGN_STREAK_20/R_VOL_SPIKE_FREQ_20)填满本阶段该左腿的唯一一批。",
        "expected_sign": -1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
