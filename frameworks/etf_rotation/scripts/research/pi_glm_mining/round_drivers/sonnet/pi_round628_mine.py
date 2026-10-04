#!/usr/bin/env python3
"""Round 628 driver: S30 stage, second pairing batch. round_627 already
gave all 5 mechanism_atoms_v3 atoms their one left-leg batch (3 pairs
each) per the standing pairing-discipline rule; none of them can be a
new left leg again this stage. This round uses 5 FRESH left atoms (not
yet used as S30 left legs) paired against the 5 mechanism_atoms_v3
atoms as RIGHT legs -- none were used as a right leg in round_627, so
each has its full quota of <=3 distinct left-leg partners. 5 lefts x 3
rights = 15 pairs, balanced round-robin, mirroring the pattern that
worked for S29 (round_625 left-batch -> round_626 right-batch,
producing 2 of S29's 4 admissions).

Left atoms (previously validated, redundancy-magnet atoms excluded):
UNDERWATER_FRAC_Z_60 (S12 intraday_pain_recovery_1m), YZ_OVERNIGHT_SHARE_20
(S9 range_based_vol_1m), PASSAGE_ASYM_20 (S17 first_passage_times_1m),
R_BIGBAR_DIR_SKEW_20 (S26R repl_volume_core_a), R_GAP_FILL_FRACTION_60
(S26R repl_volume_core_b).

After this round, S30's pairing space is fully exhausted in both
directions -- closure assessment deferred to round_629's inspection."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_628"

_M1 = {"name": "VT_AUTOCORR_ACTIVITY_SPLIT_20", "source": "mechanism_atoms_v3"}
_M2 = {"name": "AM_PRERUN_CLOSE5_CONSIST_20", "source": "mechanism_atoms_v3"}
_M3 = {"name": "PM_POSTRUN_DAY_CONSIST_20", "source": "mechanism_atoms_v3"}
_M4 = {"name": "FIRST30_BUCKET_SHARE_20", "source": "mechanism_atoms_v3"}
_M5 = {"name": "HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20", "source": "mechanism_atoms_v3"}

_L1 = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}
_L2 = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_L3 = {"name": "PASSAGE_ASYM_20", "source": "first_passage_times_1m"}
_L4 = {"name": "R_BIGBAR_DIR_SKEW_20", "source": "repl_volume_core_a"}
_L5 = {"name": "R_GAP_FILL_FRACTION_60", "source": "repl_volume_core_b"}

base.CANDIDATES = [
    {"id": "S30Q1", "operator": "rank_spread", "left": _L1, "right": _M1,
     "mechanism": "s30_q1", "hypothesis": "UNDERWATER_FRAC_Z_60（S12） × VT_AUTOCORR_ACTIVITY_SPLIT_20（作右腿首次使用）。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q2", "operator": "rank_spread", "left": _L1, "right": _M2,
     "mechanism": "s30_q2", "hypothesis": "UNDERWATER_FRAC_Z_60 × AM_PRERUN_CLOSE5_CONSIST_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q3", "operator": "rank_spread", "left": _L1, "right": _M3,
     "mechanism": "s30_q3", "hypothesis": "UNDERWATER_FRAC_Z_60 × PM_POSTRUN_DAY_CONSIST_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q4", "operator": "rank_spread", "left": _L2, "right": _M2,
     "mechanism": "s30_q4", "hypothesis": "YZ_OVERNIGHT_SHARE_20（S9） × AM_PRERUN_CLOSE5_CONSIST_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q5", "operator": "rank_spread", "left": _L2, "right": _M3,
     "mechanism": "s30_q5", "hypothesis": "YZ_OVERNIGHT_SHARE_20 × PM_POSTRUN_DAY_CONSIST_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q6", "operator": "rank_spread", "left": _L2, "right": _M4,
     "mechanism": "s30_q6", "hypothesis": "YZ_OVERNIGHT_SHARE_20 × FIRST30_BUCKET_SHARE_20（round_627 唯一入选原子 S30P11 的右腿）。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q7", "operator": "rank_spread", "left": _L3, "right": _M3,
     "mechanism": "s30_q7", "hypothesis": "PASSAGE_ASYM_20（S17 首达时间不对称） × PM_POSTRUN_DAY_CONSIST_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S30Q8", "operator": "rank_spread", "left": _L3, "right": _M4,
     "mechanism": "s30_q8", "hypothesis": "PASSAGE_ASYM_20 × FIRST30_BUCKET_SHARE_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S30Q9", "operator": "rank_spread", "left": _L3, "right": _M5,
     "mechanism": "s30_q9", "hypothesis": "PASSAGE_ASYM_20 × HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S30Q10", "operator": "rank_spread", "left": _L4, "right": _M4,
     "mechanism": "s30_q10", "hypothesis": "R_BIGBAR_DIR_SKEW_20（S26R） × FIRST30_BUCKET_SHARE_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q11", "operator": "rank_spread", "left": _L4, "right": _M5,
     "mechanism": "s30_q11", "hypothesis": "R_BIGBAR_DIR_SKEW_20 × HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q12", "operator": "rank_spread", "left": _L4, "right": _M1,
     "mechanism": "s30_q12", "hypothesis": "R_BIGBAR_DIR_SKEW_20 × VT_AUTOCORR_ACTIVITY_SPLIT_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q13", "operator": "rank_spread", "left": _L5, "right": _M5,
     "mechanism": "s30_q13", "hypothesis": "R_GAP_FILL_FRACTION_60（S26R） × HAR_RESID_SIGN_PV_ELASTICITY_SPLIT_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q14", "operator": "rank_spread", "left": _L5, "right": _M1,
     "mechanism": "s30_q14", "hypothesis": "R_GAP_FILL_FRACTION_60 × VT_AUTOCORR_ACTIVITY_SPLIT_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S30Q15", "operator": "rank_spread", "left": _L5, "right": _M2,
     "mechanism": "s30_q15", "hypothesis": "R_GAP_FILL_FRACTION_60 × AM_PRERUN_CLOSE5_CONSIST_20。本轮末条。方向由发现期定。", "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
