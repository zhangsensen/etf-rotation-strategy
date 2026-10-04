#!/usr/bin/env python3
"""Round 626 driver: S29 stage, second pairing batch. round_625 already
gave all 6 mechanism_atoms_v2 atoms their one left-leg batch (3 pairs
each) per the standing pairing-discipline rule ('同一左腿一阶段只配一批');
none of them can be a new left leg again this stage. This round instead
uses 6 FRESH left atoms (not yet used as S29 left legs, each getting its
one S29 batch) paired against the 6 mechanism_atoms_v2 atoms as RIGHT
legs -- none of the mechanism atoms were used as a right leg in
round_625, so each has its full quota of <=3 distinct left-leg partners.
6 lefts x 3 rights = 18 pairs, a balanced round-robin so each mechanism
atom is used as right leg exactly 3 times (its full quota) and each new
left atom is used exactly 3 times (within its <=8 batch cap).

Left atoms (previously validated, redundancy-magnet atoms excluded per
standing memory): UNDERWATER_FRAC_CHG_20 (S7 intraday_drawdown_1m,
this line's strongest audit-excess single atom historically),
YZ_OVERNIGHT_SHARE_20 (S9 range_based_vol_1m), PASSAGE_ASYM_20 (S17
first_passage_times_1m), NOISE_VAR_20 (S5 microstructure_noise_1m),
R_BIGBAR_VOL_SHARE_20 (S26R repl_volume_core_b), VT_BUCKET_GINI_20 (S24
volume_time_1m).

After this round, S29's pairing space is fully exhausted in both
directions (mechanism atoms as left legs: round_625; as right legs:
this round) -- closure assessment deferred to round_627's inspection of
this round's results."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_626"

_M1 = {"name": "MFI_EXTREME_UNDERWATER_SKEW_20", "source": "mechanism_atoms_v2"}
_M2 = {"name": "MFI_EXTREME_FWD5_RET_20", "source": "mechanism_atoms_v2"}
_M3 = {"name": "ON_UNDERWATER_SPLIT_20", "source": "mechanism_atoms_v2"}
_M4 = {"name": "REL_UNDERWATER_CATEGORY_20", "source": "mechanism_atoms_v2"}
_M5 = {"name": "PM_FRONTRUN_RET_CONSIST_20", "source": "mechanism_atoms_v2"}
_M6 = {"name": "BESTDAY_BUCKET_COUNT_RATIO_20", "source": "mechanism_atoms_v2"}

_L1 = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_L2 = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_L3 = {"name": "PASSAGE_ASYM_20", "source": "first_passage_times_1m"}
_L4 = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_L5 = {"name": "R_BIGBAR_VOL_SHARE_20", "source": "repl_volume_core_b"}
_L6 = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}

base.CANDIDATES = [
    {"id": "S29Q1", "operator": "rank_spread", "left": _L1, "right": _M1,
     "mechanism": "s29_q1", "hypothesis": "UNDERWATER_FRAC_CHG_20（S7，本线历史最强单原子）× MFI_EXTREME_UNDERWATER_SKEW_20（S29 新原子，作右腿首次使用）。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q2", "operator": "rank_spread", "left": _L1, "right": _M2,
     "mechanism": "s29_q2", "hypothesis": "UNDERWATER_FRAC_CHG_20 × MFI_EXTREME_FWD5_RET_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q3", "operator": "rank_spread", "left": _L1, "right": _M3,
     "mechanism": "s29_q3", "hypothesis": "UNDERWATER_FRAC_CHG_20 × ON_UNDERWATER_SPLIT_20（S29 round_625 已入选原子 S29A3）。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q4", "operator": "rank_spread", "left": _L2, "right": _M2,
     "mechanism": "s29_q4", "hypothesis": "YZ_OVERNIGHT_SHARE_20（S9） × MFI_EXTREME_FWD5_RET_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q5", "operator": "rank_spread", "left": _L2, "right": _M3,
     "mechanism": "s29_q5", "hypothesis": "YZ_OVERNIGHT_SHARE_20 × ON_UNDERWATER_SPLIT_20（同源构造对照——ON_UNDERWATER_SPLIT_20 本身即用 YZ 2 分量简化代理构造，此配对检验原始 20 日均值版 vs 简化分半版是否互补）。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q6", "operator": "rank_spread", "left": _L2, "right": _M4,
     "mechanism": "s29_q6", "hypothesis": "YZ_OVERNIGHT_SHARE_20 × REL_UNDERWATER_CATEGORY_20（S29 round_625 已入选原子 S29P10 的左腿）。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q7", "operator": "rank_spread", "left": _L3, "right": _M3,
     "mechanism": "s29_q7", "hypothesis": "PASSAGE_ASYM_20（S17 首达时间不对称） × ON_UNDERWATER_SPLIT_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S29Q8", "operator": "rank_spread", "left": _L3, "right": _M4,
     "mechanism": "s29_q8", "hypothesis": "PASSAGE_ASYM_20 × REL_UNDERWATER_CATEGORY_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S29Q9", "operator": "rank_spread", "left": _L3, "right": _M5,
     "mechanism": "s29_q9", "hypothesis": "PASSAGE_ASYM_20 × PM_FRONTRUN_RET_CONSIST_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S29Q10", "operator": "rank_spread", "left": _L4, "right": _M4,
     "mechanism": "s29_q10", "hypothesis": "NOISE_VAR_20（S5 微观结构噪声方差） × REL_UNDERWATER_CATEGORY_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q11", "operator": "rank_spread", "left": _L4, "right": _M5,
     "mechanism": "s29_q11", "hypothesis": "NOISE_VAR_20 × PM_FRONTRUN_RET_CONSIST_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q12", "operator": "rank_spread", "left": _L4, "right": _M6,
     "mechanism": "s29_q12", "hypothesis": "NOISE_VAR_20 × BESTDAY_BUCKET_COUNT_RATIO_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q13", "operator": "rank_spread", "left": _L5, "right": _M5,
     "mechanism": "s29_q13", "hypothesis": "R_BIGBAR_VOL_SHARE_20（S26R 大 bar 成交量占比） × PM_FRONTRUN_RET_CONSIST_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q14", "operator": "rank_spread", "left": _L5, "right": _M6,
     "mechanism": "s29_q14", "hypothesis": "R_BIGBAR_VOL_SHARE_20 × BESTDAY_BUCKET_COUNT_RATIO_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q15", "operator": "rank_spread", "left": _L5, "right": _M1,
     "mechanism": "s29_q15", "hypothesis": "R_BIGBAR_VOL_SHARE_20 × MFI_EXTREME_UNDERWATER_SKEW_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q16", "operator": "rank_spread", "left": _L6, "right": _M6,
     "mechanism": "s29_q16", "hypothesis": "VT_BUCKET_GINI_20（S24 成交量时间桶 Gini） × BESTDAY_BUCKET_COUNT_RATIO_20（同为成交量时间桶概念，不同统计量，检验互补性）。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q17", "operator": "rank_spread", "left": _L6, "right": _M1,
     "mechanism": "s29_q17", "hypothesis": "VT_BUCKET_GINI_20 × MFI_EXTREME_UNDERWATER_SKEW_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S29Q18", "operator": "rank_spread", "left": _L6, "right": _M2,
     "mechanism": "s29_q18", "hypothesis": "VT_BUCKET_GINI_20 × MFI_EXTREME_FWD5_RET_20。本轮末条。方向由发现期定。", "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
