#!/usr/bin/env python3
"""Round 674 driver: S64 continuation (same stage as round_673, main
controller directive unchanged) -- ALSO the round that voids S63 per
error E30 (see CONTROLLER_VOID.json in this round's output directory):
the capital_gains_overhang_1d family's specified turnover proxy
degenerates the reference price to ~lag-1, making CGO_60/GAIN_OVERHANG_60/
LOSS_OVERHANG_60 a re-expression of same-day return (ret1) rather than a
genuine disposition-effect mechanism (rank corr vs ret1: 0.94/0.78/-0.67).
mechanism_atoms_v6_split (this stage's family) was retroactively checked
against ret1 and is clean (all |corr| <= 0.07) -- unaffected.

This round extends S64's pairing batches: round_673 gave each of the 8
new atoms exactly 1 right leg (using up CONTINUOUS_BETA_60 and
GAP_DD_CONSUMPTION_RATIO_20's <=3-lefts cap; ULCER_INDEX_20 had 1 slot
left). This round adds fresh right legs not yet used in S64 (VOL_SPIKE_FREQ_20,
R2_VOL_AUTOCORR_20, RESILIENCY_20, PERM_ENTROPY_RET_20,
UNDERWATER_FRAC_CHG_20) plus ULCER_INDEX_20's last slot, giving each atom
1-2 more pairings (avoiding pairing any atom with its own base
statistic)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_674"

_UWCHG_TURNOVER = {"name": "UWCHG_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_UWCHG_ONGAP = {"name": "UWCHG_ONGAP_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_PERMENT_TURNOVER = {"name": "PERMENT_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_PERMENT_AMIHUD = {"name": "PERMENT_AMIHUD_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_LUNCHPR_ONGAP = {"name": "LUNCHPR_ONGAP_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_ULCER_NOISERATIO = {"name": "ULCER_NOISERATIO_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_ULCER_TURNOVER = {"name": "ULCER_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_YZSHARE_AMIHUD = {"name": "YZSHARE_AMIHUD_SPLIT_20", "source": "mechanism_atoms_v6_split"}

_VOL_SPIKE_FREQ = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_R2_VOL_AUTOCORR = {"name": "R2_VOL_AUTOCORR_20", "source": "repl_volume_core_v2b"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_ULCER_INDEX = {"name": "ULCER_INDEX_20", "source": "intraday_pain_recovery_1m"}

_PAIRS = [
    (_UWCHG_TURNOVER, "1", _VOL_SPIKE_FREQ),
    (_UWCHG_TURNOVER, "2", _RESILIENCY),
    (_UWCHG_ONGAP, "1", _R2_VOL_AUTOCORR),
    (_PERMENT_TURNOVER, "1", _RESILIENCY),
    (_PERMENT_AMIHUD, "1", _UNDERWATER_FRAC_CHG),
    (_PERMENT_AMIHUD, "2", _VOL_SPIKE_FREQ),
    (_LUNCHPR_ONGAP, "1", _ULCER_INDEX),
    (_LUNCHPR_ONGAP, "2", _PERM_ENTROPY),
    (_ULCER_NOISERATIO, "1", _VOL_SPIKE_FREQ),
    (_ULCER_TURNOVER, "1", _PERM_ENTROPY),
    (_ULCER_TURNOVER, "2", _R2_VOL_AUTOCORR),
    (_YZSHARE_AMIHUD, "1", _R2_VOL_AUTOCORR),
]

CANDIDATES = []
for left, tag, right in _PAIRS:
    CANDIDATES.append({
        "id": f"S64P2_{left['name']}_{tag}", "operator": "rank_spread", "left": left, "right": right,
        "mechanism": f"s64_{left['name'].lower()}_x_{right['name'].lower()}_batch2",
        "hypothesis": f"{left['name']} x {right['name']}：S64拆分条件化原子配对批第二轮（round_673续，"
                      "右腿池换为新原子避免与右腿基础统计量重复）。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
