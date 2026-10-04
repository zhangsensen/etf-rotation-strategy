#!/usr/bin/env python3
"""Round 678 driver: S66 stage (main controller directive, 2026-09-21) --
E30-corrected 1d capital-gains overhang. S63's original family (round_670-
672, 5 admissions) used the directive-specified turnover proxy V_t/Vbar_t;
the controller's own recompute found rank corr(CGO_60, ret1)=0.87-0.99 and
corr(LOSS_OVERHANG_V2_60, max(-ret1,0))=0.72-0.92 -- all 5 S63 admissions are
DEGENERATE_RET1_SHADOW, voided, excluded from the forward ledger (this
supersedes S63's original round_674 CONTROLLER_VOID.json scope: that void
already covered CGO_60/GAIN_OVERHANG_60/LOSS_OVERHANG_V2_60 for the same
reason; this directive text re-confirms it as an S66 preamble).

New family `cgo_true_turnover_v2_sonnet` keeps S63's exact Grinblatt-Han
math but replaces the turnover proxy with real PIT turnover (fund_share
parquet, usable_from_date-aligned) -- reusing the already-verified
`_cgo_stats` recursion (capital_gains_overhang_1d.py) and `_pit_fund_shares`
helper (cost_distribution_1m_sonnet.py). 6 atoms: CGO_60, CGO_250,
GAIN_OVERHANG_60, LOSS_OVERHANG_V2_60, UW_SHARE_V2_250, RP_CHANGE_V2_20.

atom_health (outputs/round_678/atom_health.csv, run before this driver)
finding: CGO_60/CGO_250/GAIN_OVERHANG_60 are NOT a ret1 shadow this time
(|corr| <= 0.36 vs ret1) but ARE a shadow of an existing atom --
R2_PRICE_POSITION_20 (corr 0.70-0.74) -- because with real (small)
turnover the mean holding period is long (~1/TO ~= 15-35 days), so RP_N
approximates a long-run average price and CGO_N collapses to "where is
close within its recent range", the same information PRICE_POSITION_20
already provides. Those 3 atoms are flagged shadow and not pursued
further with new pairings this round (still atomically re-adjudicated
for completeness). LOSS_OVERHANG_V2_60, UW_SHARE_V2_250, RP_CHANGE_V2_20 are
clean (max |corr| vs all reference series 0.36, 0.62, 0.68 respectively;
LOSS_OVERHANG_V2_60 vs ret20 -0.51 is the highest but well under 0.7).

Pairing: the 3 mandatory LOSS_OVERHANG_V2_60 re-test pairs (GAP_DD_
CONSUMPTION_RATIO_20, PERM_ENTROPY_RET_20, UNDERWATER_FRAC_CHG_20) plus
one more (R2_VOL_SPIKE_FREQ_20, within its <=8 batch cap); UW_SHARE_V2_250
and RP_CHANGE_V2_20 each get 3 pairings with fresh right legs (this is a
new stage, S66, so pairing-discipline right-leg counters reset)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_678"

_CGO_60 = {"name": "CGO_V2_60", "source": "cgo_true_turnover_v2_sonnet"}
_CGO_250 = {"name": "CGO_V2_250", "source": "cgo_true_turnover_v2_sonnet"}
_GAIN_60 = {"name": "GAIN_OVERHANG_V2_60", "source": "cgo_true_turnover_v2_sonnet"}
_LOSS_60 = {"name": "LOSS_OVERHANG_V2_60", "source": "cgo_true_turnover_v2_sonnet"}
_UW_SHARE_V2_250 = {"name": "UW_SHARE_V2_250", "source": "cgo_true_turnover_v2_sonnet"}
_RP_CHANGE_V2_20 = {"name": "RP_CHANGE_V2_20", "source": "cgo_true_turnover_v2_sonnet"}

_ATOMS = [_CGO_60, _CGO_250, _GAIN_60, _LOSS_60, _UW_SHARE_V2_250, _RP_CHANGE_V2_20]

_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_R2_VOL_SPIKE_FREQ = {"name": "R2_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_v2a"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}

CANDIDATES = []
for atom in _ATOMS:
    CANDIDATES.append({
        "id": f"S66A_{atom['name']}", "operator": "atomic", "left": atom, "right": atom,
        "mechanism": f"s66_{atom['name'].lower()}_atomic",
        "hypothesis": f"CGO真换手率修正版(E30)：{atom['name']}。",
        "expected_sign": 1,
    })

_LOSS_PAIRS = [
    ("GAPDD", _GAP_DD_CONSUMPTION),
    ("PERMENT", _PERM_ENTROPY),
    ("UWCHG", _UNDERWATER_FRAC_CHG),
    ("R2VS", _R2_VOL_SPIKE_FREQ),
]
for tag, right in _LOSS_PAIRS:
    CANDIDATES.append({
        "id": f"S66P_LOSS60_{tag}", "operator": "rank_spread", "left": _LOSS_60, "right": right,
        "mechanism": f"s66_loss_overhang_60_x_{right['name'].lower()}",
        "hypothesis": f"LOSS_OVERHANG_V2_60 x {right['name']}：E30修正后重测S63原配对假设。",
        "expected_sign": 1,
    })

_UW_PAIRS = [
    ("GAPDD", _GAP_DD_CONSUMPTION),
    ("R2VS", _R2_VOL_SPIKE_FREQ),
    ("VTAC", _VT_AUTOCORR),
]
for tag, right in _UW_PAIRS:
    CANDIDATES.append({
        "id": f"S66P_UWSHARE250_{tag}", "operator": "rank_spread", "left": _UW_SHARE_V2_250, "right": right,
        "mechanism": f"s66_uw_share_250_x_{right['name'].lower()}",
        "hypothesis": f"UW_SHARE_V2_250 x {right['name']}：N=250存活权重之上悬垂配右腿。",
        "expected_sign": 1,
    })

_RP_PAIRS = [
    ("GAPDD", _GAP_DD_CONSUMPTION),
    ("R2VS", _R2_VOL_SPIKE_FREQ),
    ("VTAC", _VT_AUTOCORR),
]
for tag, right in _RP_PAIRS:
    CANDIDATES.append({
        "id": f"S66P_RPCHANGE20_{tag}", "operator": "rank_spread", "left": _RP_CHANGE_V2_20, "right": right,
        "mechanism": f"s66_rp_change_20_x_{right['name'].lower()}",
        "hypothesis": f"RP_CHANGE_V2_20 x {right['name']}：参考价变化率(慢信号候选)配右腿。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
