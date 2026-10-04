#!/usr/bin/env python3
"""Round 680 driver: S66b stage (main controller directive, 2026-09-21) --
price-position/momentum control pairs for S66's 3 CGO admissions
(UW_SHARE_V2_250 x R2_VOL_SPIKE_FREQ_20, RP_CHANGE_V2_20 x R2_VOL_SPIKE_
FREQ_20, GAIN_OVERHANG_V2_60 x VT_AUTOCORR_20 -- all have a left leg with
0.49-0.71 rank corr against price-position/momentum series per atom_health).

New family `price_position_controls` (RET_20, RET_60, PRICE_POSITION_250,
NEG_RET_20, NEG_RET_250, NEG_PRICE_POSITION_250). Only-round stage per
directive; exactly the 6 named control pairs, not subject to the 12-line
floor (explicit exception in the directive text, mirroring S14/S26-style
replication rounds). Directive named RET_20/RET_250/PRICE_POSITION_250 as
the family's atoms but pair #6 needs RET_60 (not RET_250) -- added RET_60
to the family as a documented fix rather than deviate from the literal
pair list.

Sign convention: the CGO admissions' left legs (UW_SHARE_V2_250,
RP_CHANGE_V2_20 negative-branch, GAIN_OVERHANG_V2_60) are expected to
correlate negatively with price position / positively with drawdown, so
the NEG_ prefixed atoms give the same expected sign as the original
admission for a fair t-comparison; #4 and #6 use the plain (non-negated)
atom to match RP_CHANGE_V2_20's and GAIN_OVERHANG_V2_60's own positive
correlation with recent momentum."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_680"

_NEG_RET_250 = {"name": "NEG_RET_250", "source": "price_position_controls"}
_NEG_PRICE_POSITION_250 = {"name": "NEG_PRICE_POSITION_250", "source": "price_position_controls"}
_NEG_RET_20 = {"name": "NEG_RET_20", "source": "price_position_controls"}
_RET_20 = {"name": "RET_20", "source": "price_position_controls"}
_PRICE_POSITION_250 = {"name": "PRICE_POSITION_250", "source": "price_position_controls"}
_RET_60 = {"name": "RET_60", "source": "price_position_controls"}

_R2_VOL_SPIKE_FREQ = {"name": "R2_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_v2a"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}

CANDIDATES = [
    {
        "id": "S66bC_NEGRET250_R2VS", "operator": "rank_spread", "left": _NEG_RET_250, "right": _R2_VOL_SPIKE_FREQ,
        "mechanism": "s66b_control_neg_ret250_x_r2_vol_spike_freq_20",
        "hypothesis": "对照 S66P_UWSHARE250_R2VS：CGO 左腿换成纯 250 日负动量。",
        "expected_sign": 1,
    },
    {
        "id": "S66bC_NEGPP250_R2VS", "operator": "rank_spread", "left": _NEG_PRICE_POSITION_250, "right": _R2_VOL_SPIKE_FREQ,
        "mechanism": "s66b_control_neg_price_position_250_x_r2_vol_spike_freq_20",
        "hypothesis": "对照 S66P_UWSHARE250_R2VS：CGO 左腿换成纯 250 日价格位置(取负，价格越低分越高，方向匹配 UW_SHARE)。",
        "expected_sign": 1,
    },
    {
        "id": "S66bC_NEGRET20_R2VS", "operator": "rank_spread", "left": _NEG_RET_20, "right": _R2_VOL_SPIKE_FREQ,
        "mechanism": "s66b_control_neg_ret20_x_r2_vol_spike_freq_20",
        "hypothesis": "对照 S66P_UWSHARE250_R2VS：CGO 左腿换成纯 20 日负动量。",
        "expected_sign": 1,
    },
    # S66bC_RET20_R2VS = rank(RET_20) - rank(R2_VOL_SPIKE_FREQ_20) intentionally
    # omitted: canonical-hash collision with round_676's S65C_RET20_R2VS (same
    # expression, RET_20 there sourced from "directional_trend" -- the engine's
    # dedup keys off atom name not family). Already-computed result reused in
    # REPORT instead of re-registering (disc t=-0.009, audit bp=12.5).
    {
        "id": "S66bC_PP250_VTAC", "operator": "rank_spread", "left": _PRICE_POSITION_250, "right": _VT_AUTOCORR,
        "mechanism": "s66b_control_price_position_250_x_vt_autocorr_20",
        "hypothesis": "对照 S66P2_GAIN60_VTAC：CGO 左腿(GAIN_OVERHANG_V2_60)换成纯 250 日价格位置。",
        "expected_sign": 1,
    },
    {
        "id": "S66bC_RET60_VTAC", "operator": "rank_spread", "left": _RET_60, "right": _VT_AUTOCORR,
        "mechanism": "s66b_control_ret60_x_vt_autocorr_20",
        "hypothesis": "对照 S66P2_GAIN60_VTAC：CGO 左腿(GAIN_OVERHANG_V2_60)换成纯 60 日动量（指令列表未含 RET_60，本轮按第 6 条对照对需要补充该原子）。",
        "expected_sign": 1,
    },
]

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
