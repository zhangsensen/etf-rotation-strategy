#!/usr/bin/env python3
"""Round 665 driver: S60 stage (main controller directive, 2026-09-21) --
mechanism atoms distilled from the S44 second-tier rejected list's
volume-inclusive combos: MB2 (NOISE_VAR_CHG_20 x VOL_SPIKE_FREQ_20, H20
audit t 5.52), PB5 (PERM_ENTROPY_RET_20 x LOG_AMOUNT_VOL_20, t 5.31), DA1
(SAMPEN_RET_20 x LOG_AMOUNT_VOL_20, t 5.09), NI5 (MFI_EXTREME_FRAC_20 x
IDIO_LIQ_SHOCK_Z_20, t 4.58) -- see outputs/round_644/rejected_h20_profile.csv
for the exact source rounds/expressions. All four were cross-sectional
rank_spread constructs that never passed gate 7. This stage expresses
each pairing as a single time-series conditional-split statistic (new
family mechanism_atoms_v5, same "one conditional statistic, not a
product" pattern S36 established): VOLSPIKE_NOISECHG_SPLIT_20 (MB2),
TURNVOL_ENTROPY_SPLIT_20 (PB5+DA1, share the LOG_AMOUNT_VOL_20 right leg
-- PB5's target atom PERM_ENTROPY_RET_20 carried forward since its
source t (5.31) > DA1's (5.09)), LIQSHOCK_MFI_SPLIT_20 (NI5).

S60A1-A3: single-atom gate-7 re-adjudication (atomic operator) for the
three new mechanism atoms.

S60P_*: pairing batch, one per new left leg (pairing-discipline: each
left leg gets exactly one batch this stage, <=8 right legs each; the
same 8-atom right-leg pool as round_656 is reused across all 3 left legs,
so each right leg hits the <=3-lefts-per-stage cap exactly at the
boundary).

The 4th atom (20-day change of whichever of the three above is
strongest) is added in a follow-up pass after this batch's gate-7
results are in, per the S60 "plus the 20-day change of the strongest
one" instruction -- cannot be built until the strongest is known."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_665"

_VOLSPIKE_NOISECHG = {"name": "VOLSPIKE_NOISECHG_SPLIT_20", "source": "mechanism_atoms_v5"}
_TURNVOL_ENTROPY = {"name": "TURNVOL_ENTROPY_SPLIT_20", "source": "mechanism_atoms_v5"}
_LIQSHOCK_MFI = {"name": "LIQSHOCK_MFI_SPLIT_20", "source": "mechanism_atoms_v5"}

_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_GAP_DD_CONSUMPTION = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_PERM_ENTROPY = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_YZ_OVERNIGHT_SHARE = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_CONTINUOUS_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}

_RIGHT_LEG_POOL = [
    ("A", _R_LOG_AMOUNT_VOL),
    ("B", _MFI_EXTREME_FRAC),
    ("C", _GAP_DD_CONSUMPTION),
    ("D", _PERM_ENTROPY),
    ("E", _YZ_OVERNIGHT_SHARE),
    ("F", _CONTINUOUS_BETA),
    ("G", _VT_AUTOCORR),
    ("H", _RESILIENCY),
]

CANDIDATES = [
    {"id": "S60A1", "operator": "atomic", "left": _VOLSPIKE_NOISECHG, "right": _VOLSPIKE_NOISECHG,
     "mechanism": "s60_volspike_noisechg_split_atomic",
     "hypothesis": "MB2机制(NOISE_VAR_CHG_20 x VOL_SPIKE_FREQ_20, 源H20审计t=5.52)改写为时间序列条件切分:"
                   "20日滚动中位数切分原始日度量spike占比(未平滑,与VOL_SPIKE_FREQ_20的20日滚动均值区分),"
                   "spike日均值(NOISE_VAR_CHG_20)-非spike日均值。MB2原方向=-1(高NOISE_VAR_CHG排名/低VOL_SPIKE_FREQ排名"
                   "预测更低远期收益)，本构造沿用同向假设:spike日噪声方差异常上升是流动性压力/非知情交易噪声信号。",
     "expected_sign": -1},
    {"id": "S60A2", "operator": "atomic", "left": _TURNVOL_ENTROPY, "right": _TURNVOL_ENTROPY,
     "mechanism": "s60_turnvol_entropy_split_atomic",
     "hypothesis": "PB5(PERM_ENTROPY_RET_20 x LOG_AMOUNT_VOL_20, 源H20审计t=5.31)+DA1(SAMPEN_RET_20 x同右腿, t=5.09)"
                   "共享LOG_AMOUNT_VOL_20右腿，只留t更高的PB5目标(排列熵)。20日滚动中位数切分LOG_AMOUNT_VOL_20水平,"
                   "高换手波动日均值(PERM_ENTROPY_RET_20)-低换手波动日均值。PB5原方向=-1，本构造沿用:"
                   "高换手波动日排列熵异常升高=随机性主导，预测更低远期收益。",
     "expected_sign": -1},
    {"id": "S60A3", "operator": "atomic", "left": _LIQSHOCK_MFI, "right": _LIQSHOCK_MFI,
     "mechanism": "s60_liqshock_mfi_split_atomic",
     "hypothesis": "NI5(MFI_EXTREME_FRAC_20 x IDIO_LIQ_SHOCK_Z_20, 源H20审计t=4.58)改写为40日滚动符号切分:"
                   "IDIO_LIQ_SHOCK_Z_20(已z标准化，以0为自然阈值，无新增常量)>0为冲击日，均值(MFI_EXTREME_FRAC_20|冲击日)"
                   "-均值(...|非冲击日)。NI5原方向=+1(高MFI极值排名/低流动性冲击排名预测更高远期收益)，本构造沿用:"
                   "冲击日资金流极值更有信息量，预测更高远期收益。",
     "expected_sign": 1},
]

for tag, right in _RIGHT_LEG_POOL:
    CANDIDATES.append({
        "id": f"S60P_VS_{tag}", "operator": "rank_spread", "left": _VOLSPIKE_NOISECHG, "right": right,
        "mechanism": f"s60_volspike_noisechg_split_x_{right['name'].lower()}",
        "hypothesis": f"VOLSPIKE_NOISECHG_SPLIT_20 x {right['name']}：MB2机制的条件切分单原子配{right['name']}。",
        "expected_sign": -1,
    })

for tag, right in _RIGHT_LEG_POOL:
    CANDIDATES.append({
        "id": f"S60P_TE_{tag}", "operator": "rank_spread", "left": _TURNVOL_ENTROPY, "right": right,
        "mechanism": f"s60_turnvol_entropy_split_x_{right['name'].lower()}",
        "hypothesis": f"TURNVOL_ENTROPY_SPLIT_20 x {right['name']}：PB5/DA1共享机制的条件切分单原子配{right['name']}。",
        "expected_sign": -1,
    })

for tag, right in _RIGHT_LEG_POOL:
    CANDIDATES.append({
        "id": f"S60P_LM_{tag}", "operator": "rank_spread", "left": _LIQSHOCK_MFI, "right": right,
        "mechanism": f"s60_liqshock_mfi_split_x_{right['name'].lower()}",
        "hypothesis": f"LIQSHOCK_MFI_SPLIT_20 x {right['name']}：NI5机制的条件切分单原子配{right['name']}。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

# NOTE: this round's results (S60A2/TURNVOL_ENTROPY_SPLIT_20 was the only
# base atom to gate-7 pass standalone) identify it as the S60-mandated
# "strongest" atom whose 20-day change (TURNVOL_ENTROPY_SPLIT_CHG_20,
# already implemented in mechanism_atoms_v5.py) still needs its own
# gate-7 test + pairing batch. PLAN.json is immutable once locked (this
# round's 27 candidates are already locked), so that follow-up is a
# round_666 tail round (same pattern as S54's round_657 -> round_658/659
# tail rounds), not appended here.

if __name__ == "__main__":
    base.main()
