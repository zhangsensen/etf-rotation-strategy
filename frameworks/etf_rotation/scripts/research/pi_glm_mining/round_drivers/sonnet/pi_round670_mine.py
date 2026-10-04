#!/usr/bin/env python3
"""Round 670 driver: S63 stage (main controller directive, 2026-09-21) --
capital-gains overhang (Grinblatt-Han 2005), 1d-only, the literature-
original disposition-effect mechanism (distinct from this line's
price-path-only drawdown atoms DD48/CR08/UE3/CK04, none of which weight
by holding-period turnover). New family capital_gains_overhang_1d.

IMPORTANT finding from the pilot build: CGO_60, CGO_120 and CGO_250 are
numerically IDENTICAL (rank corr 1.000 to many decimal places) under the
directive's specified turnover proxy (V_t / Vbar_t, Vbar_t = trailing
60d mean volume). Root cause: this proxy centers at ~1.0 by construction
(median ~0.89, mean ~0.997 empirically), so (1-turnover) averages near
zero and the survival-weighted reference price collapses to ~lag-1
dominance regardless of window length N -- the specified proxy does not
behave like a real turnover rate (typically <5%/day for real share
turnover), so the N=60/120/250 distinction the directive asked for does
not materialize. Reported as-is (matches this line's "implement exactly
as specified, then report the empirical finding" norm) rather than
silently substituting a different turnover source (fund_share exists
locally but only covers 2023-07 onward for these symbols -- insufficient
for the 2020-2023 discovery window -- so a fix was not attempted this
round). Only CGO_60 is registered as a candidate; CGO_120/CGO_250 are
left in the family code for transparency but not separately tested
(confirmed duplicates carry zero incremental information).

Atom health (rank corr vs UNDERWATER_FRAC_CHG_20, VOL_SPIKE_FREQ_20,
VT_AUTOCORR_20, LUNCH_POST_RUN_20): all |corr| <= 0.17, no shadow flags
-- genuinely independent of this line's existing drawdown/volume/lunch
atoms.

S63A1-A4: single-atom gate-7 re-adjudication (CGO_60, GAIN_OVERHANG_60,
LOSS_OVERHANG_60, RP_CHANGE_20).

S63P_*: pairing batches, 3 right legs per left leg (respecting pairing
discipline's <=3-lefts-per-right-leg cap): VOL_SPIKE_FREQ_20 and
VT_AUTOCORR_20 (the directive's mandatory "volume representative" right
legs) each land in 3 of the 4 batches; the remaining right legs
(UNDERWATER_FRAC_CHG_20, CONTINUOUS_BETA_60, PERM_ENTROPY_RET_20,
RESILIENCY_20, GAP_DD_CONSUMPTION_RATIO_20, YZ_OVERNIGHT_SHARE_20) round
out each left leg's batch to exactly 3 right legs, none exceeding the
cap."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_670"

_CGO_60 = {"name": "CGO_60", "source": "capital_gains_overhang_1d"}
_GAIN_OVERHANG = {"name": "GAIN_OVERHANG_60", "source": "capital_gains_overhang_1d"}
_LOSS_OVERHANG = {"name": "LOSS_OVERHANG_60", "source": "capital_gains_overhang_1d"}
_RP_CHANGE = {"name": "RP_CHANGE_20", "source": "capital_gains_overhang_1d"}

_VOL_SPIKE_FREQ = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_YZ_OVERNIGHT_SHARE = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}

CANDIDATES = [
    {"id": "S63A1", "operator": "atomic", "left": _CGO_60, "right": _CGO_60,
     "mechanism": "s63_cgo_60_atomic",
     "hypothesis": "Grinblatt-Han 2005资本利得悬臵(N=60，成交量加权持仓成本参考价)。"
                   "CGO_120/CGO_250与其数值完全相同(corr=1.000，见家族docstring)，不重复注册。",
     "expected_sign": 1},
    {"id": "S63A2", "operator": "atomic", "left": _GAIN_OVERHANG, "right": _GAIN_OVERHANG,
     "mechanism": "s63_gain_overhang_60_atomic",
     "hypothesis": "An 2016 V型处置效应正部分：成交量加权的浮盈占比(N=60)。",
     "expected_sign": 1},
    {"id": "S63A3", "operator": "atomic", "left": _LOSS_OVERHANG, "right": _LOSS_OVERHANG,
     "mechanism": "s63_loss_overhang_60_atomic",
     "hypothesis": "An 2016 V型处置效应负部分：成交量加权的浮亏占比(N=60)。",
     "expected_sign": -1},
    {"id": "S63A4", "operator": "atomic", "left": _RP_CHANGE, "right": _RP_CHANGE,
     "mechanism": "s63_rp_change_20_atomic",
     "hypothesis": "参考价(N=60)本身的20日变化率——慢信号候选，指令要求H=20列跟踪。",
     "expected_sign": 1},
]

_BATCHES = [
    (_CGO_60, "CGO", [_VOL_SPIKE_FREQ, _VT_AUTOCORR, _UNDERWATER_FRAC_CHG]),
    (_GAIN_OVERHANG, "GAIN", [_VOL_SPIKE_FREQ, _CONTINUOUS_BETA, _PERM_ENTROPY]),
    (_LOSS_OVERHANG, "LOSS", [_VT_AUTOCORR, _RESILIENCY, _GAP_DD_CONSUMPTION]),
    (_RP_CHANGE, "RPCHG", [_VOL_SPIKE_FREQ, _VT_AUTOCORR, _YZ_OVERNIGHT_SHARE]),
]

for left, tag, rights in _BATCHES:
    for i, right in enumerate(rights, start=1):
        CANDIDATES.append({
            "id": f"S63P_{tag}_{i}", "operator": "rank_spread", "left": left, "right": right,
            "mechanism": f"s63_{left['name'].lower()}_x_{right['name'].lower()}",
            "hypothesis": f"{left['name']} x {right['name']}：CGO家族原子配已验证原子。",
            "expected_sign": 1,
        })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
