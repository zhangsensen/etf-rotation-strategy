#!/usr/bin/env python3
"""Round 675 driver: S64 closeout (main controller directive, 2026-09-21).

This round first backfills round_673's missing atom_health.csv (done via a
standalone script, pi_round675_atom_health.py, run before this driver --
all 8 mechanism_atoms_v6_split atoms show corr vs their unsplit original
<=0.23 and corr vs ret1 <=0.07, both well under the 0.7 shadow threshold
and the E30 red-flag zone; no admitted S64 candidate needs a shadow flag).

Then this round closes S64's pairing space. Exact tally of round_673+674
pairings (verified against both driver files):
  left legs at cap 3: UWCHG_TURNOVER, PERMENT_AMIHUD, LUNCHPR_ONGAP, ULCER_TURNOVER
  left legs with 1 slot left: UWCHG_ONGAP(2), PERMENT_TURNOVER(2),
    ULCER_NOISERATIO(2), YZSHARE_AMIHUD(2)
  right legs at cap 3: CONTINUOUS_BETA_60, GAP_DD_CONSUMPTION_RATIO_20,
    ULCER_INDEX_20, VOL_SPIKE_FREQ_20, R2_VOL_AUTOCORR_20
  right legs with slots left: RESILIENCY_20(1), PERM_ENTROPY_RET_20(1),
    UNDERWATER_FRAC_CHG_20(2)

Only 4 legal pairs remain that (a) fill every left leg to exactly 3 and
(b) avoid pairing a split atom with its own unsplit base statistic:
  UWCHG_ONGAP x RESILIENCY_20            (closes RESILIENCY_20)
  PERMENT_TURNOVER x UNDERWATER_FRAC_CHG_20
  ULCER_NOISERATIO x PERM_ENTROPY_RET_20 (closes PERM_ENTROPY_RET_20)
  YZSHARE_AMIHUD x UNDERWATER_FRAC_CHG_20 (closes UNDERWATER_FRAC_CHG_20)

4 < 12 -> per standing pairing discipline this closes S64 outright this
round (no padding with fresh right legs); MECHANISM_EXHAUSTED.json for
S64 follows in this round's output directory."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_675"

_UWCHG_ONGAP = {"name": "UWCHG_ONGAP_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_PERMENT_TURNOVER = {"name": "PERMENT_TURNOVER_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_ULCER_NOISERATIO = {"name": "ULCER_NOISERATIO_SPLIT_20", "source": "mechanism_atoms_v6_split"}
_YZSHARE_AMIHUD = {"name": "YZSHARE_AMIHUD_SPLIT_20", "source": "mechanism_atoms_v6_split"}

_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}

_PAIRS = [
    (_UWCHG_ONGAP, _RESILIENCY),
    (_PERMENT_TURNOVER, _UNDERWATER_FRAC_CHG),
    (_ULCER_NOISERATIO, _PERM_ENTROPY),
    (_YZSHARE_AMIHUD, _UNDERWATER_FRAC_CHG),
]

CANDIDATES = []
for left, right in _PAIRS:
    CANDIDATES.append({
        "id": f"S64P3_{left['name']}", "operator": "rank_spread", "left": left, "right": right,
        "mechanism": f"s64_{left['name'].lower()}_x_{right['name'].lower()}_closeout",
        "hypothesis": f"{left['name']} x {right['name']}：S64收官批，填满该左腿最后1个配对名额。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
