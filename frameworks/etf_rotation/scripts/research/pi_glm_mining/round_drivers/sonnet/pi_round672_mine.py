#!/usr/bin/env python3
"""Round 672 driver: S63 final batch (same stage as round_670/671, main
controller directive unchanged). After round_670+671, each of the 4
CGO-family atoms had used 6 of its <=8-right-leg pairing-batch cap, and
this round's 8 candidates below use every remaining legal right-leg slot
for all 4 atoms simultaneously -- after this round each left leg reaches
exactly 8/8 and no further legal pairs exist for any of them (confirmed
by tally below). Per the standing rule ("一轮里如果剩余合法配对不足12
条，就按合同宣布本阶段穷尽，不要凑数"), 8 < 12 is the exact remaining
legal-pair count, so this round both completes the batch AND triggers
S63's exhaustion -- MECHANISM_EXHAUSTED.json is written this round.

Right-leg cap tally after this round (all <=3, all lefts <=8):
  VOL_SPIKE_FREQ_20=3(full,untouched this round), VT_AUTOCORR_20=3(full,
  untouched), UNDERWATER_FRAC_CHG_20=2+1(LOSS)=3, CONTINUOUS_BETA_60=2+1
  (CGO)=3, PERM_ENTROPY_RET_20=2+1(RPCHG)=3, RESILIENCY_20=2+1(RPCHG)=3,
  GAP_DD_CONSUMPTION_RATIO_20=2(untouched), YZ_OVERNIGHT_SHARE_20=2
  (untouched), MFI_EXTREME_FRAC_20=1+1(GAIN)=2, LOG_AMOUNT_VOL_20=1+1
  (GAIN)=2, LUNCH_POST_RUN_20=1+1(LOSS)=2, R_ULCER_20=2(untouched),
  R2_VOL_AUTOCORR_20=1+1(CGO)=2.
  CGO_60=8/8, GAIN_OVERHANG_60=8/8, LOSS_OVERHANG_60=8/8, RP_CHANGE_20=8/8."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_672"

_CGO_60 = {"name": "CGO_60", "source": "capital_gains_overhang_1d"}
_GAIN_OVERHANG = {"name": "GAIN_OVERHANG_60", "source": "capital_gains_overhang_1d"}
_LOSS_OVERHANG = {"name": "LOSS_OVERHANG_60", "source": "capital_gains_overhang_1d"}
_RP_CHANGE = {"name": "RP_CHANGE_20", "source": "capital_gains_overhang_1d"}

_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_R2_VOL_AUTOCORR = {"name": "R2_VOL_AUTOCORR_20", "source": "repl_volume_core_v2b"}
_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_LOG_AMOUNT_VOL = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_LUNCH_POST_RUN = {"name": "LUNCH_POST_RUN_20", "source": "lunch_break_1m"}
_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}

_BATCHES = [
    (_CGO_60, "CGO", [_CONTINUOUS_BETA, _R2_VOL_AUTOCORR]),
    (_GAIN_OVERHANG, "GAIN", [_MFI_EXTREME_FRAC, _LOG_AMOUNT_VOL]),
    (_LOSS_OVERHANG, "LOSS", [_LUNCH_POST_RUN, _UNDERWATER_FRAC_CHG]),
    (_RP_CHANGE, "RPCHG", [_PERM_ENTROPY, _RESILIENCY]),
]

CANDIDATES = []
for left, tag, rights in _BATCHES:
    for i, right in enumerate(rights, start=7):
        CANDIDATES.append({
            "id": f"S63P_{tag}_{i}", "operator": "rank_spread", "left": left, "right": right,
            "mechanism": f"s63_{left['name'].lower()}_x_{right['name'].lower()}",
            "hypothesis": f"{left['name']} x {right['name']}：CGO家族配对批第三轮（本原子的最后2个右腿名额）。",
            "expected_sign": 1,
        })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
