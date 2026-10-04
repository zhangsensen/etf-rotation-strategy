#!/usr/bin/env python3
"""Round 645 driver: S45 stage (main controller directive, 2026-09-21) --
reproduce pi's overnight_structure_1d family's three admitted candidates
(CZ01/CY07/CY17) using pi's own PRECISE code-level definition of
BIGBAR_EDGE_CONC_20 ("share of big-bar volume in its MODAL 30-minute
slot"), not the CONTROLLER-PARAPHRASED "first/last 30 minutes" version
S14 used (which failed to reproduce: +6.8bp/t0.34 here vs pi's
+55.2bp/t2.76). New family repl_overnight_core_v2 (R2_ prefix, distinct
namespace from S26R2's repl_volume_core_v2 -- no name collision).

Small-sample pilot (3 symbols) ran 3.88s; full 14-symbol run
extrapolated ~18s, ran directly.

Atom health (round_645_atom_health): no shadow flags. R2_ON_PREM_20 vs
ON_PREM_20 and R2_PRICE_POSITION_20 vs ON_PREM_20 both show NaN
corr_vs_ref (insufficient discovery-window overlap for the 500-pair
minimum, not a shadow signal -- reported as N/A).

Reproduction fixed set only (5 candidates, per directive; not a
15-30-condition mining batch -- reproduction rounds test a pre-specified
list, same convention as S14/S26R/S26R2/S28/S38)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_645"

_R2_BIGBAR_EDGE = {"name": "R2_BIGBAR_EDGE_CONC_20", "source": "repl_overnight_core_v2b"}
_R2_ON_PREM = {"name": "R2_ON_PREM_20", "source": "repl_overnight_core_v2a"}
_R2_GAP_FILL_RATE = {"name": "R2_GAP_FILL_RATE_20", "source": "repl_overnight_core_v2a"}
_R2_OPEN30_SHARE = {"name": "R2_OPEN30_VOL_SHARE_20", "source": "repl_overnight_core_v2b"}
_R2_PRICE_POS = {"name": "R2_PRICE_POSITION_20", "source": "repl_overnight_core_v2b"}

base.CANDIDATES = [
    {"id": "S45A1", "operator": "atomic", "left": _R2_BIGBAR_EDGE, "right": _R2_BIGBAR_EDGE,
     "mechanism": "s45_bigbar_edge_atomic",
     "hypothesis": "R2_BIGBAR_EDGE_CONC_20（大bar成交量在其众数30分钟时段的份额，pi 代码级精确定义）单原子门7重裁，作为 R2_CZ01 的构造质量检验。"
                   "体检 disc_ic=-0.0810，与 GAP_DD_CONSUMPTION_RATIO_20 corr=0.12（独立）。",
     "expected_sign": -1},
    {"id": "S45A2", "operator": "atomic", "left": _R2_ON_PREM, "right": _R2_ON_PREM,
     "mechanism": "s45_on_prem_atomic",
     "hypothesis": "R2_ON_PREM_20（隔夜收益20日均值，pi 精确定义）单原子门7重裁，作为 R2_CZ01/R2_CY07 的构造质量检验。体检 disc_ic=+0.0213。",
     "expected_sign": 1},
    {"id": "R2_CZ01", "operator": "rank_spread", "left": _R2_ON_PREM, "right": _R2_BIGBAR_EDGE,
     "mechanism": "s45_r2_cz01",
     "hypothesis": "R2_ON_PREM_20 × R2_BIGBAR_EDGE_CONC_20，用 pi 代码级精确定义（大bar成交量众数时段集中度，非 S14 转述的'首尾30分钟'）复现 CZ01。"
                   "pi 主控数字：审计 +55.2bp / t 2.76。S14 用转述定义复现失败（+6.8bp/t0.34）。",
     "expected_sign": 1},
    {"id": "R2_CY07", "operator": "rank_spread", "left": _R2_ON_PREM, "right": _R2_OPEN30_SHARE,
     "mechanism": "s45_r2_cy07",
     "hypothesis": "R2_ON_PREM_20 × R2_OPEN30_VOL_SHARE_20，复现 CY07。pi 主控数字：审计 +28.9bp / t 1.41。", "expected_sign": 1},
    {"id": "R2_CY17", "operator": "rank_spread", "left": _R2_GAP_FILL_RATE, "right": _R2_PRICE_POS,
     "mechanism": "s45_r2_cy17",
     "hypothesis": "R2_GAP_FILL_RATE_20 × R2_PRICE_POSITION_20，复现 CY17。pi 主控数字：审计 +31.9bp / t 1.93。", "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
