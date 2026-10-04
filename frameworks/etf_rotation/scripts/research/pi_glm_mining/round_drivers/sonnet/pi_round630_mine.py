#!/usr/bin/env python3
"""Round 630 driver: S31 stage, second pairing batch. round_629 already
gave all 8 gap_absorption_path_1m atoms their one left-leg batch (2
pairs each) per the standing pairing-discipline rule; none of them can
be a new left leg again this stage. This round uses 8 FRESH left atoms
(not yet used as S31 left legs) paired against the 8 gap_absorption_path_1m
atoms as RIGHT legs -- none were used as a right leg in round_629, so
each has its full quota of <=3 distinct left-leg partners. 8 lefts x 2
rights = 16 pairs, round-robin balanced so each gap atom is used as
right leg exactly 2 times (within its <=3 quota) and each new left atom
is used exactly 2 times (within its <=8 batch cap). Mirrors the pattern
that worked for S29 (round_625->626) and S30 (round_627->628).

Left atoms (previously validated, redundancy-magnet atoms excluded):
YZ_OVERNIGHT_SHARE_20 (S9), PASSAGE_ASYM_20 (S17), NOISE_VAR_20 (S5),
R_BIGBAR_VOL_SHARE_20 (S26R), UNDERWATER_FRAC_Z_60 (S12),
CATEGORY_DISPERSION_20 (category_state), S28_VOV_HAR_RESID_20 (S28),
PV_ELASTICITY_20 (S14)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_630"

_G1 = {"name": "GAP_FILL_TIMING_20", "source": "gap_absorption_path_1m"}
_G2 = {"name": "GAP_REMAIN_10AM_20", "source": "gap_absorption_path_1m"}
_G3 = {"name": "GAP_REMAIN_1130_20", "source": "gap_absorption_path_1m"}
_G4 = {"name": "GAP_REMAIN_CLOSE_20", "source": "gap_absorption_path_1m"}
_G5 = {"name": "GAP_DD_DIRECTION_MATCH_20", "source": "gap_absorption_path_1m"}
_G6 = {"name": "GAP_SHARE_OF_RANGE_20", "source": "gap_absorption_path_1m"}
_G7 = {"name": "GAP_FILL_TIMING_CHG_20", "source": "gap_absorption_path_1m"}
_G8 = {"name": "GAP_DD_DIRECTION_MATCH_CHG_20", "source": "gap_absorption_path_1m"}

_L1 = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_L2 = {"name": "PASSAGE_ASYM_20", "source": "first_passage_times_1m"}
_L3 = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_L4 = {"name": "R_BIGBAR_VOL_SHARE_20", "source": "repl_volume_core_b"}
_L5 = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}
_L6 = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_L7 = {"name": "S28_VOV_HAR_RESID_20", "source": "pi_repl_s28"}
_L8 = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}

base.CANDIDATES = [
    {"id": "S31Q1", "operator": "rank_spread", "left": _L1, "right": _G1,
     "mechanism": "s31_q1", "hypothesis": "YZ_OVERNIGHT_SHARE_20（S9） × GAP_FILL_TIMING_20（作右腿首次使用）。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q2", "operator": "rank_spread", "left": _L1, "right": _G2,
     "mechanism": "s31_q2", "hypothesis": "YZ_OVERNIGHT_SHARE_20 × GAP_REMAIN_10AM_20（round_629 唯一入选原子 S31P7 的右腿）。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q3", "operator": "rank_spread", "left": _L2, "right": _G2,
     "mechanism": "s31_q3", "hypothesis": "PASSAGE_ASYM_20（S17） × GAP_REMAIN_10AM_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S31Q4", "operator": "rank_spread", "left": _L2, "right": _G3,
     "mechanism": "s31_q4", "hypothesis": "PASSAGE_ASYM_20 × GAP_REMAIN_1130_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S31Q5", "operator": "rank_spread", "left": _L3, "right": _G3,
     "mechanism": "s31_q5", "hypothesis": "NOISE_VAR_20（S5） × GAP_REMAIN_1130_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q6", "operator": "rank_spread", "left": _L3, "right": _G4,
     "mechanism": "s31_q6", "hypothesis": "NOISE_VAR_20 × GAP_REMAIN_CLOSE_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q7", "operator": "rank_spread", "left": _L4, "right": _G4,
     "mechanism": "s31_q7", "hypothesis": "R_BIGBAR_VOL_SHARE_20（S26R） × GAP_REMAIN_CLOSE_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q8", "operator": "rank_spread", "left": _L4, "right": _G5,
     "mechanism": "s31_q8", "hypothesis": "R_BIGBAR_VOL_SHARE_20 × GAP_DD_DIRECTION_MATCH_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q9", "operator": "rank_spread", "left": _L5, "right": _G5,
     "mechanism": "s31_q9", "hypothesis": "UNDERWATER_FRAC_Z_60（S12） × GAP_DD_DIRECTION_MATCH_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q10", "operator": "rank_spread", "left": _L5, "right": _G6,
     "mechanism": "s31_q10", "hypothesis": "UNDERWATER_FRAC_Z_60 × GAP_SHARE_OF_RANGE_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q11", "operator": "rank_spread", "left": _L6, "right": _G6,
     "mechanism": "s31_q11", "hypothesis": "CATEGORY_DISPERSION_20 × GAP_SHARE_OF_RANGE_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S31Q12", "operator": "rank_spread", "left": _L6, "right": _G7,
     "mechanism": "s31_q12", "hypothesis": "CATEGORY_DISPERSION_20 × GAP_FILL_TIMING_CHG_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S31Q13", "operator": "rank_spread", "left": _L7, "right": _G7,
     "mechanism": "s31_q13", "hypothesis": "S28_VOV_HAR_RESID_20（S28） × GAP_FILL_TIMING_CHG_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q14", "operator": "rank_spread", "left": _L7, "right": _G8,
     "mechanism": "s31_q14", "hypothesis": "S28_VOV_HAR_RESID_20 × GAP_DD_DIRECTION_MATCH_CHG_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q15", "operator": "rank_spread", "left": _L8, "right": _G8,
     "mechanism": "s31_q15", "hypothesis": "PV_ELASTICITY_20（S14） × GAP_DD_DIRECTION_MATCH_CHG_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S31Q16", "operator": "rank_spread", "left": _L8, "right": _G1,
     "mechanism": "s31_q16", "hypothesis": "PV_ELASTICITY_20 × GAP_FILL_TIMING_20。本轮末条。方向由发现期定。", "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
