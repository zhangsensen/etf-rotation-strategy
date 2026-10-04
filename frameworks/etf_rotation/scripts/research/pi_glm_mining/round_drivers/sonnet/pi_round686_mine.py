#!/usr/bin/env python3
"""Round 686 driver: S70 stage second batch (main controller directive,
2026-09-20 17:00 pairing-discipline rule) -- fill remaining right-leg
slots for the 8 mechanism_atoms_v8_split_tier2 left atoms from round_685.

round_685 gave each of the 8 left atoms exactly 1 pairing (with 1 of the
4 preferred right legs UNDERWATER_FRAC_CHG_20/PERM_ENTROPY_RET_20/
CONTINUOUS_BETA_60/R2_VOL_SPIKE_FREQ_20), using each right leg twice
(2/3 of its 3-left cap). This round: (a) fill the 1 remaining slot on
each of those 4 preferred right legs (4 pairs), assigned to left atoms
that have NOT yet used that specific right leg; (b) introduce 3 fresh
right legs at 3-left cap each (ULCER_INDEX_20, GAP_DD_CONSUMPTION_
RATIO_20, RESILIENCY_20 -- all already-validated atoms from other
families, none of them this family's own unsplit base statistic for the
left atom they're paired with, i.e. GAPDD_TURNOVER_SPLIT_20 never pairs
GAP_DD_CONSUMPTION_RATIO_20 and RESIL_ONGAP/RESIL_AMIHUD never pair
RESILIENCY_20). Total 13 new pair candidates (>=12 floor), no left atom
exceeds its 3-pairing cap, no right leg exceeds its 3-left cap. Atomic
candidates are not retested (all 8 rejected in round_685; family
definitions unchanged)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_686"

_LUNCHPR_TURNOVER = {"name": "LUNCHPR_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_LUNCHPR_ONGAP_B = {"name": "LUNCHPR_ONGAP_SPLIT_20B", "source": "mechanism_atoms_v8_split_tier2"}
_VFPULCER_TURNOVER = {"name": "VFPULCER_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_VFPULCER_NOISECHG = {"name": "VFPULCER_NOISECHG_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_RESIL_ONGAP = {"name": "RESIL_ONGAP_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_RESIL_AMIHUD = {"name": "RESIL_AMIHUD_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_GAPDD_TURNOVER = {"name": "GAPDD_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}
_CLOSE5_NOISECHG = {"name": "CLOSE5_NOISECHG_SPLIT_20", "source": "mechanism_atoms_v8_split_tier2"}

_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_R2_VOL_SPIKE_FREQ = {"name": "R2_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_v2a"}
_ULCER_INDEX = {"name": "ULCER_INDEX_20", "source": "intraday_pain_recovery_1m"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}

_PAIRS = [
    # (a) fill remaining slot on the 4 preferred right legs from round_685
    (_VFPULCER_TURNOVER, _UNDERWATER_FRAC_CHG, "fill_uwfc"),
    (_LUNCHPR_TURNOVER, _PERM_ENTROPY, "fill_perment"),
    (_GAPDD_TURNOVER, _CONTINUOUS_BETA, "fill_cbeta"),
    (_CLOSE5_NOISECHG, _R2_VOL_SPIKE_FREQ, "fill_r2vs"),
    # (b) fresh right leg ULCER_INDEX_20 (3-left cap)
    (_LUNCHPR_ONGAP_B, _ULCER_INDEX, "ulcer_index_new"),
    (_RESIL_ONGAP, _ULCER_INDEX, "ulcer_index_new"),
    (_RESIL_AMIHUD, _ULCER_INDEX, "ulcer_index_new"),
    # (b) fresh right leg GAP_DD_CONSUMPTION_RATIO_20 (3-left cap; excludes GAPDD_TURNOVER self-ref)
    (_VFPULCER_NOISECHG, _GAP_DD_CONSUMPTION, "gapdd_new"),
    (_LUNCHPR_TURNOVER, _GAP_DD_CONSUMPTION, "gapdd_new"),
    (_VFPULCER_TURNOVER, _GAP_DD_CONSUMPTION, "gapdd_new"),
    # (b) fresh right leg RESILIENCY_20 (3-left cap; excludes RESIL_ONGAP/RESIL_AMIHUD self-ref)
    (_GAPDD_TURNOVER, _RESILIENCY, "resiliency_new"),
    (_CLOSE5_NOISECHG, _RESILIENCY, "resiliency_new"),
    (_VFPULCER_NOISECHG, _RESILIENCY, "resiliency_new"),
]

CANDIDATES = []
for left, right, tag in _PAIRS:
    CANDIDATES.append({
        "id": f"S70P2_{left['name']}_{right['name']}",
        "operator": "rank_spread", "left": left, "right": right,
        "mechanism": f"s70_{left['name'].lower()}_x_{right['name'].lower()}_{tag}",
        "hypothesis": f"{left['name']} x {right['name']}：S70第二批，按配对纪律补齐右腿名额（{tag}）。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
