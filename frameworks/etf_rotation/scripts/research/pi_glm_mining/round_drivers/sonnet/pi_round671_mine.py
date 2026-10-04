#!/usr/bin/env python3
"""Round 671 driver: S63 continuation (same stage as round_670, main
controller directive unchanged). round_670 built capital_gains_overhang_1d
(4 tested atoms: CGO_60, GAIN_OVERHANG_60, LOSS_OVERHANG_60, RP_CHANGE_20)
and gave each a 3-right-leg pairing batch (VOL_SPIKE_FREQ_20 and
VT_AUTOCORR_20 -- the directive's mandatory "volume representative" right
legs -- each reached the <=3-lefts-per-right-leg cap across that first
batch). 3/16 admitted (S63P_CGO_1, S63P_GAIN_3, S63P_LOSS_3), all with
H20 audit t markedly stronger than H5.

This round: extends each of the 4 atoms' pairing batch with 3 more right
legs (bringing each atom's total batch to 6 of the <=8 cap), using a mix
of fresh right legs (0 uses in S63 so far) and right legs that still have
capacity under the <=3-lefts cap (currently at 1 use each from
round_670). Tally after this round: every right leg <=3 lefts, every left
leg's batch <=8 right legs -- no discipline violations.

Fresh right legs this round: MFI_EXTREME_FRAC_20 (accumulation_distribution_1m),
LOG_AMOUNT_VOL_20 (liquidity_variability), LUNCH_POST_RUN_20 (lunch_break_1m),
R_ULCER_20 (repl_volume_core_b), R2_VOL_AUTOCORR_20 (repl_volume_core_v2b)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_671"

_CGO_60 = {"name": "CGO_60", "source": "capital_gains_overhang_1d"}
_GAIN_OVERHANG = {"name": "GAIN_OVERHANG_60", "source": "capital_gains_overhang_1d"}
_LOSS_OVERHANG = {"name": "LOSS_OVERHANG_60", "source": "capital_gains_overhang_1d"}
_RP_CHANGE = {"name": "RP_CHANGE_20", "source": "capital_gains_overhang_1d"}

_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_LOG_AMOUNT_VOL = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_LUNCH_POST_RUN = {"name": "LUNCH_POST_RUN_20", "source": "lunch_break_1m"}
_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_R2_VOL_AUTOCORR = {"name": "R2_VOL_AUTOCORR_20", "source": "repl_volume_core_v2b"}

_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_YZ_OVERNIGHT_SHARE = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}

_BATCHES = [
    (_CGO_60, "CGO", [_MFI_EXTREME_FRAC, _LOG_AMOUNT_VOL, _LUNCH_POST_RUN]),
    (_GAIN_OVERHANG, "GAIN", [_R_ULCER, _R2_VOL_AUTOCORR, _RESILIENCY]),
    (_LOSS_OVERHANG, "LOSS", [_CONTINUOUS_BETA, _PERM_ENTROPY, _YZ_OVERNIGHT_SHARE]),
    (_RP_CHANGE, "RPCHG", [_UNDERWATER_FRAC_CHG, _GAP_DD_CONSUMPTION, _R_ULCER]),
]

CANDIDATES = []
for left, tag, rights in _BATCHES:
    for i, right in enumerate(rights, start=4):
        CANDIDATES.append({
            "id": f"S63P_{tag}_{i}", "operator": "rank_spread", "left": left, "right": right,
            "mechanism": f"s63_{left['name'].lower()}_x_{right['name'].lower()}",
            "hypothesis": f"{left['name']} x {right['name']}：CGO家族原子配对批第二轮（round_670续）。",
            "expected_sign": 1,
        })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
