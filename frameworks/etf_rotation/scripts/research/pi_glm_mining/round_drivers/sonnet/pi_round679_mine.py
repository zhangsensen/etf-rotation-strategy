#!/usr/bin/env python3
"""Round 679 driver: S66 pairing-space closeout (main controller directive,
2026-09-21). round_678 gave LOSS_OVERHANG_V2_60 its one batch (4 right
legs: GAP_DD_CONSUMPTION_RATIO_20, PERM_ENTROPY_RET_20, UNDERWATER_FRAC_
CHG_20, R2_VOL_SPIKE_FREQ_20 -- all rejected) and gave UW_SHARE_V2_250 /
RP_CHANGE_V2_20 each a 3-right-leg batch (GAP_DD_CONSUMPTION_RATIO_20,
R2_VOL_SPIKE_FREQ_20, VT_AUTOCORR_20 -- 2 admissions, both vs
R2_VOL_SPIKE_FREQ_20). CGO_V2_60/CGO_V2_250/GAIN_OVERHANG_V2_60 were
flagged shadow (corr 0.70-0.74 vs R2_PRICE_POSITION_20) and deliberately
not paired in round_678.

Right-leg tally after round_678 (this stage, S66): GAP_DD_CONSUMPTION_
RATIO_20 and R2_VOL_SPIKE_FREQ_20 are both at their 3-left cap;
PERM_ENTROPY_RET_20 and UNDERWATER_FRAC_CHG_20 are each at 1/3 (2 slots
left, only used by LOSS_OVERHANG_V2_60); VT_AUTOCORR_20 is at 2/3 (1 slot
left). This round gives the 3 shadow atoms their one fairness pairing
batch against these remaining slots (rather than skip them outright --
gate-7's own redundancy dedup vs PRICE_POSITION_20-correlated priors
will independently catch genuine redundancy), which exactly exhausts
every remaining right-leg slot: CGO_V2_60 x {PERM_ENTROPY_RET_20,
UNDERWATER_FRAC_CHG_20}, CGO_V2_250 x {PERM_ENTROPY_RET_20 (2nd slot),
UNDERWATER_FRAC_CHG_20 (2nd slot)}, GAIN_OVERHANG_V2_60 x VT_AUTOCORR_20
(last slot). 5 candidates. After this round all 6 atoms have had their
pairing batch and every right leg used this stage is at cap -> 0 legal
pairs remain -> S66 pairing space exhausted."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_679"

_CGO_60 = {"name": "CGO_V2_60", "source": "cgo_true_turnover_v2_sonnet"}
_CGO_250 = {"name": "CGO_V2_250", "source": "cgo_true_turnover_v2_sonnet"}
_GAIN_60 = {"name": "GAIN_OVERHANG_V2_60", "source": "cgo_true_turnover_v2_sonnet"}

_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}

_PAIRS = [
    ("S66P2_CGOV260_PERMENT", _CGO_60, _PERM_ENTROPY),
    ("S66P2_CGOV260_UWCHG", _CGO_60, _UNDERWATER_FRAC_CHG),
    ("S66P2_CGOV2250_PERMENT", _CGO_250, _PERM_ENTROPY),
    ("S66P2_CGOV2250_UWCHG", _CGO_250, _UNDERWATER_FRAC_CHG),
    ("S66P2_GAIN60_VTAC", _GAIN_60, _VT_AUTOCORR),
]

CANDIDATES = []
for cid, left, right in _PAIRS:
    CANDIDATES.append({
        "id": cid, "operator": "rank_spread", "left": left, "right": right,
        "mechanism": f"s66_{left['name'].lower()}_x_{right['name'].lower()}_closeout",
        "hypothesis": f"{left['name']} x {right['name']}：S66收官批，PRICE_POSITION_20影子原子的公平配对测试。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
