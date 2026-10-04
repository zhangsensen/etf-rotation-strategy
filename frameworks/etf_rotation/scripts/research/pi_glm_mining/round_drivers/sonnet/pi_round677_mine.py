#!/usr/bin/env python3
"""Round 677 driver: S65 pairing-space closeout (main controller directive,
2026-09-21). round_676 gave CGO_1M_20/CGO_1M_60 their one batch each (3
right legs: R2_VOL_SPIKE_FREQ_20, VT_AUTOCORR_20, LUNCH_PRE_RUN_20) and
gave the other 4 atoms (UNDERWATER_VOL_SHARE_1M_60, COST_CONC_1M_60,
MODE_DIST_1M_60, COST_SKEW_1M_60) one pairing each, all against
UNDERWATER_FRAC_CHG_20.

PROCESS CORRECTION (self-caught): round_676 paired UNDERWATER_FRAC_CHG_20
against 4 distinct left legs, exceeding the standing <=3-distinct-lefts-
per-right-leg cap by 1. None of those 4 candidates passed gate 7 anyway
(2 rejected for topk_gate, 2 for rank_correlation_redundancy against
prior:round_545:QA8), so no admission is affected, but the violation is
noted here and UNDERWATER_FRAC_CHG_20 is NOT used again this round.

This round closes out the remaining right-leg slots from round_676's
partially-used right legs (each at 2/3 after round_676) with the 4
non-CGO left legs, giving each of those left legs one more pairing (its
second, keeping it within a reasonable batch size) and closing R2_VOL_
SPIKE_FREQ_20 / VT_AUTOCORR_20 / LUNCH_PRE_RUN_20 to their 3-left cap.
UNDERWATER_VOL_SHARE_1M_60 gets one fresh right leg (GAP_DD_CONSUMPTION_
RATIO_20, S31/S60-proven, 0 lefts used this stage) to close its own
one-more-pairing allotment without reopening the over-cap right leg.

After this round: all 6 atoms have had their pairing batch (CGO's =3
each; the other 4 = 2 each); R2_VOL_SPIKE_FREQ_20/VT_AUTOCORR_20/
LUNCH_PRE_RUN_20 close to 3/3; UNDERWATER_FRAC_CHG_20 stays at its
(over-cap, frozen) 4; GAP_DD_CONSUMPTION_RATIO_20 opens at 1/3 but has
no further legal left leg this stage (all 6 atoms closed) -> 0 legal
pairs remain -> S65 pairing space exhausted this round."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_677"

_UW_VOL_SHARE = {"name": "UNDERWATER_VOL_SHARE_1M_60", "source": "cost_distribution_1m_sonnet"}
_COST_CONC = {"name": "COST_CONC_1M_60", "source": "cost_distribution_1m_sonnet"}
_MODE_DIST = {"name": "MODE_DIST_1M_60", "source": "cost_distribution_1m_sonnet"}
_COST_SKEW = {"name": "COST_SKEW_1M_60", "source": "cost_distribution_1m_sonnet"}

_R2_VOL_SPIKE_FREQ = {"name": "R2_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_v2a"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_LUNCH_PRE_RUN = {"name": "LUNCH_PRE_RUN_20", "source": "pi_lunch_prerun_1m"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}

_PAIRS = [
    ("S65P2_COST_CONC_1M_60_R2VS", _COST_CONC, _R2_VOL_SPIKE_FREQ),
    ("S65P2_MODE_DIST_1M_60_VTAC", _MODE_DIST, _VT_AUTOCORR),
    ("S65P2_COST_SKEW_1M_60_LPR", _COST_SKEW, _LUNCH_PRE_RUN),
    ("S65P2_UNDERWATER_VOL_SHARE_1M_60_GAPDD", _UW_VOL_SHARE, _GAP_DD_CONSUMPTION),
]

CANDIDATES = []
for cid, left, right in _PAIRS:
    CANDIDATES.append({
        "id": cid, "operator": "rank_spread", "left": left, "right": right,
        "mechanism": f"s65_{left['name'].lower()}_x_{right['name'].lower()}_closeout",
        "hypothesis": f"{left['name']} x {right['name']}：S65收官批，填满该左腿第二个配对名额。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
