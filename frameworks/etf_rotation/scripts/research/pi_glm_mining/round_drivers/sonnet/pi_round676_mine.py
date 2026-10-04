#!/usr/bin/env python3
"""Round 676 driver: S65 stage (main controller directive, 2026-09-21) --
1m-resolution capital-gains overhang / holding-cost distribution family
`cost_distribution_1m_sonnet` (E30-corrected: real PIT turnover from
fund_share/<sym>.parquet, not the S63 1d family's voided V/Vbar proxy).

atom_health (outputs/round_676/atom_health.csv, run before this driver)
confirms all 6 atoms clean: max |rank corr| vs ret1/max(-ret1,0)/ret20/
ret60/PRICE_POSITION_20/DD48-leg/CR08-leg/UE3-leg/CK04-leg/S63's 1d CGO
atoms is 0.45 (CGO_1M_60 vs RP_CHANGE_20_1d), well under the 0.7 shadow
threshold. Critically: corr(CGO_1M_60, CGO_60_1d) = 0.174 << 0.9, so the
1m version is NOT "no-increment" vs the voided 1d family -- it is a
materially different signal (real turnover + intraday cost distribution
vs the degenerate V/Vbar proxy). Also: corr(CGO_1M_N, ret20) = 0.29-0.32,
well below the 0.52-0.88 the controller's 2026-09-21 recompute found for
the 1d family's real-turnover CGO_60 -- the 1m version carries much less
of a disguised-momentum signature, but the addendum's "ret20-replacement"
control pairs are still run below to quantify any residual overlap.

S65's directive text says pairing must include R2_BB1/XB1/S14_CK04;
those are composite rank_spread candidates, not atoms, so (documented
choice) each is represented here by its most volume/time-characteristic
underlying atom: R2_BB1 -> R2_VOL_SPIKE_FREQ_20, XB1 -> VT_AUTOCORR_20,
S14_CK04 -> LUNCH_PRE_RUN_20.

Pairing batch: CGO_1M_20 and CGO_1M_60 each x {R2_VOL_SPIKE_FREQ_20,
VT_AUTOCORR_20, LUNCH_PRE_RUN_20} (6 pairs) + a RET_20-replaces-left-leg
control pair for each of those 6 (6 more) -- t-difference between a CGO
pair and its RET_20 control is the "cost accounting increment" over
plain 20-day momentum the controller asked for. The other 4 atoms
(UNDERWATER_VOL_SHARE_1M_60, COST_CONC_1M_60, MODE_DIST_1M_60,
COST_SKEW_1M_60) each get one pairing against UNDERWATER_FRAC_CHG_20
(S7's strongest right leg, also this family's own health-check anchor).
GAIN/LOSS split atoms were not built this round (not in S65's named
atom list; the addendum's GAIN/LOSS-collapse note is noted but has no
atom to apply to here)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_676"

_CGO_1M_20 = {"name": "CGO_1M_20", "source": "cost_distribution_1m_sonnet"}
_CGO_1M_60 = {"name": "CGO_1M_60", "source": "cost_distribution_1m_sonnet"}
_UW_VOL_SHARE = {"name": "UNDERWATER_VOL_SHARE_1M_60", "source": "cost_distribution_1m_sonnet"}
_COST_CONC = {"name": "COST_CONC_1M_60", "source": "cost_distribution_1m_sonnet"}
_MODE_DIST = {"name": "MODE_DIST_1M_60", "source": "cost_distribution_1m_sonnet"}
_COST_SKEW = {"name": "COST_SKEW_1M_60", "source": "cost_distribution_1m_sonnet"}

_ATOMS = [_CGO_1M_20, _CGO_1M_60, _UW_VOL_SHARE, _COST_CONC, _MODE_DIST, _COST_SKEW]

_R2_VOL_SPIKE_FREQ = {"name": "R2_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_v2a"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_LUNCH_PRE_RUN = {"name": "LUNCH_PRE_RUN_20", "source": "pi_lunch_prerun_1m"}
_RET_20 = {"name": "RET_20", "source": "directional_trend"}
_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}

CANDIDATES = []
for atom in _ATOMS:
    CANDIDATES.append({
        "id": f"S65A_{atom['name']}", "operator": "atomic", "left": atom, "right": atom,
        "mechanism": f"s65_{atom['name'].lower()}_atomic",
        "hypothesis": f"1m成本分布/资本利得悬垂原子(真PIT换手率)：{atom['name']}。",
        "expected_sign": 1,
    })

_CGO_PAIR_RIGHT_LEGS = [
    ("R2VS", _R2_VOL_SPIKE_FREQ),
    ("VTAC", _VT_AUTOCORR),
    ("LPR", _LUNCH_PRE_RUN),
]

for cgo_atom, tag_prefix in ((_CGO_1M_20, "20"), (_CGO_1M_60, "60")):
    for tag, right in _CGO_PAIR_RIGHT_LEGS:
        CANDIDATES.append({
            "id": f"S65P_CGO1M{tag_prefix}_{tag}", "operator": "rank_spread", "left": cgo_atom, "right": right,
            "mechanism": f"s65_cgo_1m_{tag_prefix}_x_{right['name'].lower()}",
            "hypothesis": f"{cgo_atom['name']} x {right['name']}：1m成本悬垂配右腿。",
            "expected_sign": 1,
        })

# RET_20 x right-leg control pairs -- one per right leg (not per CGO window,
# since RET_20 doesn't depend on the CGO window and would otherwise duplicate
# the same expression); serves as the momentum-only control for BOTH
# CGO_1M_20 and CGO_1M_60 pairings against that right leg.
for tag, right in _CGO_PAIR_RIGHT_LEGS:
    CANDIDATES.append({
        "id": f"S65C_RET20_{tag}", "operator": "rank_spread", "left": _RET_20, "right": right,
        "mechanism": f"s65_ret20_control_x_{right['name'].lower()}",
        "hypothesis": f"RET_20 x {right['name']}：CGO_1M_20/60配对的ret20替代对照，差值=成本会计增量。",
        "expected_sign": 1,
    })

for atom in (_UW_VOL_SHARE, _COST_CONC, _MODE_DIST, _COST_SKEW):
    CANDIDATES.append({
        "id": f"S65P_{atom['name']}", "operator": "rank_spread", "left": atom, "right": _UNDERWATER_FRAC_CHG,
        "mechanism": f"s65_{atom['name'].lower()}_x_underwater_frac_chg_20",
        "hypothesis": f"{atom['name']} x UNDERWATER_FRAC_CHG_20：1m成本分布形状配S7回撤右腿。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
