#!/usr/bin/env python3
"""Round 669 driver: S62 continuation (same stage as round_668, main
controller directive unchanged). round_668 built the volume_tail_shape_1m
family (4 atoms) and used VOL_Q95_MED_20's full pairing batch (7 right
legs) plus VOL_HILL_TAIL_20's mandatory swap pairing (1 right leg, its
"one batch this stage" already exercised, even though not full).
LOG_VOL_CV_20 and VOL_MAX_SHARE_20 had not yet used their pairing batch.

This round: gives LOG_VOL_CV_20 and VOL_MAX_SHARE_20 each a full
pairing batch, reusing round_668's exact 8-atom right-leg pool (each
right leg was used once in round_668 with VOL_Q95_MED_20; this round
brings them to 2 uses via LOG_VOL_CV_20 and 3 uses -- the pairing-
discipline cap -- via VOL_MAX_SHARE_20). After this round every atom in
volume_tail_shape_1m has used its one batch this stage, and every right
leg in the pool is at the <=3-lefts cap -- S62 will be pairing-discipline
exhausted (0 legal pairs remaining) once this round's results are in."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_669"

_LOG_VOL_CV = {"name": "LOG_VOL_CV_20", "source": "volume_tail_shape_1m"}
_VOL_MAX_SHARE = {"name": "VOL_MAX_SHARE_20", "source": "volume_tail_shape_1m"}

_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_R2_VOL_AUTOCORR = {"name": "R2_VOL_AUTOCORR_20", "source": "repl_volume_core_v2b"}
_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_YZ_OVERNIGHT_SHARE = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}

_RIGHT_LEG_POOL = [
    ("A", _VT_AUTOCORR),
    ("B", _R_ULCER),
    ("C", _R2_VOL_AUTOCORR),
    ("D", _CONTINUOUS_BETA),
    ("E", _GAP_DD_CONSUMPTION),
    ("F", _YZ_OVERNIGHT_SHARE),
    ("G", _PERM_ENTROPY),
    ("H", _RESILIENCY),
]

CANDIDATES = []

for tag, right in _RIGHT_LEG_POOL:
    CANDIDATES.append({
        "id": f"S62P_CV_{tag}", "operator": "rank_spread", "left": _LOG_VOL_CV, "right": right,
        "mechanism": f"s62_log_vol_cv_x_{right['name'].lower()}",
        "hypothesis": f"LOG_VOL_CV_20（log成交量日内变异系数，无阈值）x {right['name']}："
                      "量节奏不均匀度是否比量尾肥厚度(VOL_Q95_MED_20,round_668已测)携带独立信息。",
        "expected_sign": 1,
    })

for tag, right in _RIGHT_LEG_POOL:
    CANDIDATES.append({
        "id": f"S62P_MS_{tag}", "operator": "rank_spread", "left": _VOL_MAX_SHARE, "right": right,
        "mechanism": f"s62_vol_max_share_x_{right['name'].lower()}",
        "hypothesis": f"VOL_MAX_SHARE_20（全日最大单bar成交量占比，唯一带'哪根bar'指代但无量级阈值）"
                      f"x {right['name']}。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
