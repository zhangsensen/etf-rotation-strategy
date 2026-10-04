#!/usr/bin/env python3
"""Round 684 driver: S69 stage (main controller directive, 2026-09-21) --
reproduce pi phase 57b's CGP17 (RP_CHANGE x MFI extreme) and profile
RP_CHANGE_V2_20 against momentum controls. Reproduction-exception round,
not subject to the 12-line floor.

Directive listed 4 conceptual tasks that would nominally be 5
candidates (RP_CHANGE x MFI_EXTREME, RET_20 x MFI_EXTREME control,
RP_CHANGE x UNDERWATER_FRAC_CHG_20, RP_CHANGE x GAP_DD_CONSUMPTION_
RATIO_20). The last of those (RP_CHANGE_V2_20 x GAP_DD_CONSUMPTION_
RATIO_20) is BYTE-IDENTICAL to round_678's already-evaluated
S66P_RPCHANGE20_GAPDD (rejected, disc t=1.77) -- re-registering it would
hit the engine's canonical-hash dedup (same failure mode as round_680's
RET_20 x R2VS collision). Skipped here; round_678's existing result is
cited directly in REPORT instead. Replaced with a matching RET_20 x
UNDERWATER_FRAC_CHG_20 control (symmetric with the MFI_EXTREME control
the directive did ask for), keeping n_preregistered=4 rather than
padding to a nominal 5."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_684"

_RP_CHANGE_V2_20 = {"name": "RP_CHANGE_V2_20", "source": "cgo_true_turnover_v2_sonnet"}
_RET_20 = {"name": "RET_20", "source": "directional_trend"}
_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_UNDERWATER_FRAC_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}

CANDIDATES = [
    {
        "id": "S69R_RPCHANGE_MFIEXT", "operator": "rank_spread", "left": _RP_CHANGE_V2_20, "right": _MFI_EXTREME_FRAC,
        "mechanism": "s69_repro_rp_change_v2_20_x_mfi_extreme_frac_20",
        "hypothesis": "复现 pi 第57b阶段 CGP17：RP_CHANGE_TT_20 x R_MFI_EXTREME_FRAC_20（pi 发现+25.2/t2.32，审计+41.4）。",
        "expected_sign": 1,
    },
    {
        "id": "S69C_RET20_MFIEXT", "operator": "rank_spread", "left": _RET_20, "right": _MFI_EXTREME_FRAC,
        "mechanism": "s69_control_ret20_x_mfi_extreme_frac_20",
        "hypothesis": "对照：CGO 左腿换成纯 20 日动量，差值=成本会计增量。",
        "expected_sign": 1,
    },
    {
        "id": "S69P_RPCHANGE_UWCHG", "operator": "rank_spread", "left": _RP_CHANGE_V2_20, "right": _UNDERWATER_FRAC_CHG,
        "mechanism": "s69_rp_change_v2_20_x_underwater_frac_chg_20",
        "hypothesis": "RP_CHANGE_V2_20 未配过 UNDERWATER_FRAC_CHG_20（round_678 只配了 GAPDD/R2VS/VTAC）。",
        "expected_sign": 1,
    },
    {
        "id": "S69C_RET20_UWCHG", "operator": "rank_spread", "left": _RET_20, "right": _UNDERWATER_FRAC_CHG,
        "mechanism": "s69_control_ret20_x_underwater_frac_chg_20",
        "hypothesis": "对照第3条：CGO 左腿换成纯 20 日动量。",
        "expected_sign": 1,
    },
]

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
