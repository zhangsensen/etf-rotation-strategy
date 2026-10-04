#!/usr/bin/env python3
"""Round 659 driver: S54 stage continuation (main controller directive,
2026-09-21). round_658 covered atomic/rank_spread/rank_interaction for
3 of the 4 S54-named left legs (REL_ULCER_CATEGORY_CHG_20,
REL_RECOVERY_TIME_CATEGORY_CHG_20, REL_UNDERWATER_CATEGORY_CHG_20). The
4th named atom, REL_UNDERWATER_FRAC_CHG_20 (S15's full-basket-relative
version, source relative_path_vs_basket_1m), had only ever been tested
with rank_spread (PA1-PA8, round_571, all rejected) -- rank_interaction
was never tried for it. This round closes that remaining operator gap.

Right-leg selection respects the standing "same right leg <=3 distinct
left legs per stage" cap: R_LOG_AMOUNT_VOL_20, MFI_EXTREME_FRAC_20,
GAP_DD_CONSUMPTION_RATIO_20, CONTINUOUS_BETA_60, VT_AUTOCORR_20,
PERM_ENTROPY_RET_20, YZ_OVERNIGHT_SHARE_20, RESILIENCY_20 have already
been used with 2-3 distinct left legs in round_656/657/658 -- only
ON_SIGN_STREAK_20 and R_VOL_SPIKE_FREQ_20 from that shared pool still
have room (1 use so far, in round_657's UWCAT batch). The remaining 6
right legs here are drawn fresh from families never touched in S54
(intraday_pain_recovery_1m, lunch_break_1m, pi_price_delay_1d,
first_passage_times_1m), giving a full, cap-compliant 8-right-leg
batch."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_659"

_REL_UW_FRAC_CHG = {"name": "REL_UNDERWATER_FRAC_CHG_20", "source": "relative_path_vs_basket_1m"}

_RIGHT_LEG_POOL = [
    ("A", {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}),
    ("B", {"name": "R_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_a"}),
    ("C", {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}),
    ("D", {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}),
    ("E", {"name": "ULCER_INDEX_CHG_20", "source": "intraday_pain_recovery_1m"}),
    ("F", {"name": "LUNCH_POST_RUN_20", "source": "lunch_break_1m"}),
    ("G", {"name": "PD_D1_CHG_20", "source": "pi_price_delay_1d"}),
    ("H", {"name": "FIRST_PASSAGE_UP_20", "source": "first_passage_times_1m"}),
]

CANDIDATES = []
for tag, right in _RIGHT_LEG_POOL:
    CANDIDATES.append({
        "id": f"S54I_UWFRAC_{tag}", "operator": "rank_interaction", "left": _REL_UW_FRAC_CHG, "right": right,
        "mechanism": f"s54_interaction_rel_underwater_frac_chg_x_{right['name'].lower()}",
        "hypothesis": f"rank_interaction(REL_UNDERWATER_FRAC_CHG_20, {right['name']})：S15/round_571 只测过该左腿的"
                      "rank_spread（PA1-PA8，全拒），从未测过 rank_interaction 算子；这是 S54 阶段算子空间"
                      "补测的最后一个左腿缺口。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
