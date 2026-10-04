#!/usr/bin/env python3
"""Round 668 driver: S62 stage (main controller directive, 2026-09-21) --
threshold-free rewrite of the "volume spike" leg. S39/S51 identified
VOL_SPIKE_FREQ_20 as the largest definition-sensitivity source in this
line (rank corr as low as 0.58 across mean+3sigma vs median*5x
rewrites). New family volume_tail_shape_1m (4 atoms, all scale-free /
threshold-free: quantile ratio, Hill tail index, log-volume CV, max-bar
share).

S62A1-A4: single-atom gate-7 re-adjudication for the 4 new atoms.

S62SWAP_*: the 3 mandatory "spike-leg replacement" pairs specified by
the directive -- take an existing admitted candidate that uses a
threshold-based volume-tail leg and substitute it with a new
threshold-free atom, keeping the other leg unchanged:
  - XB1 (this line's CO36 reproduction) = rank(VT_AUTOCORR_20) -
    rank(VOL_SPIKE_FREQ_20) -> swap VOL_SPIKE_FREQ_20 for VOL_Q95_MED_20.
  - R2_BB1 = rank(R2_VOL_SPIKE_FREQ_20) - rank(R_ULCER_20) -> swap
    R2_VOL_SPIKE_FREQ_20 for VOL_Q95_MED_20.
  - R2_Z2 = rank(R2_BIGBAR_DIR_SKEW_20) - rank(R2_VOL_AUTOCORR_20) ->
    R2_BIGBAR_DIR_SKEW_20 is also a median*5x-threshold volume-tail
    construct (big-bar direction skew); swap it for VOL_HILL_TAIL_20
    (a genuine tail-index measure, closer in spirit to a "skew of the
    tail" than the quantile-ratio atom).

S62P_*: pairing batch for VOL_Q95_MED_20 as left leg (the atom most
directly analogous to VOL_SPIKE_FREQ_20's semantics), 5 additional
already-verified right legs not used in the mandatory swaps, respecting
pairing discipline (VOL_Q95_MED_20 used in 2 mandatory pairs + 5 here =
7, within the <=8-right-legs-per-left-leg-per-stage cap)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_668"

_VOL_Q95_MED = {"name": "VOL_Q95_MED_20", "source": "volume_tail_shape_1m"}
_VOL_HILL_TAIL = {"name": "VOL_HILL_TAIL_20", "source": "volume_tail_shape_1m"}
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

CANDIDATES = [
    {"id": "S62A1", "operator": "atomic", "left": _VOL_Q95_MED, "right": _VOL_Q95_MED,
     "mechanism": "s62_vol_q95_med_atomic",
     "hypothesis": "1m成交量95分位/中位数(日内)的20日均值——无固定倍数阈值的量尾肥厚度代理，"
                   "替代VOL_SPIKE_FREQ_20的'均值+3sigma'/'中位数x5'任意阈值。",
     "expected_sign": 1},
    {"id": "S62A2", "operator": "atomic", "left": _VOL_HILL_TAIL, "right": _VOL_HILL_TAIL,
     "mechanism": "s62_vol_hill_tail_atomic",
     "hypothesis": "Hill尾指数(取日内1m成交量上10%order statistics)的20日均值——"
                   "值越小尾部越肥(越像spike)，Gabaix et al. 2003量的幂律尾。",
     "expected_sign": -1},
    {"id": "S62A3", "operator": "atomic", "left": _LOG_VOL_CV, "right": _LOG_VOL_CV,
     "mechanism": "s62_log_vol_cv_atomic",
     "hypothesis": "log(1m成交量)日内变异系数(std/mean)的20日均值——成交节奏不均匀度的无阈值代理。",
     "expected_sign": 1},
    {"id": "S62A4", "operator": "atomic", "left": _VOL_MAX_SHARE, "right": _VOL_MAX_SHARE,
     "mechanism": "s62_vol_max_share_atomic",
     "hypothesis": "全日最大单根1m bar成交量占全日总量比例的20日均值——唯一带'哪根bar'指代但无量级阈值的原子。",
     "expected_sign": 1},
    {"id": "S62SWAP_XB1", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _VOL_Q95_MED,
     "mechanism": "s62_swap_xb1_vt_autocorr_x_vol_q95_med",
     "hypothesis": "XB1(本线CO36复现,rank(VT_AUTOCORR_20)-rank(VOL_SPIKE_FREQ_20))的spike腿替换为"
                   "VOL_Q95_MED_20，检验去阈值化后原配对是否仍站得住。",
     "expected_sign": -1},
    {"id": "S62SWAP_R2BB1", "operator": "rank_spread", "left": _VOL_Q95_MED, "right": _R_ULCER,
     "mechanism": "s62_swap_r2bb1_vol_q95_med_x_r_ulcer",
     "hypothesis": "R2_BB1(rank(R2_VOL_SPIKE_FREQ_20)-rank(R_ULCER_20))的spike腿替换为VOL_Q95_MED_20。",
     "expected_sign": 1},
    {"id": "S62SWAP_R2Z2", "operator": "rank_spread", "left": _VOL_HILL_TAIL, "right": _R2_VOL_AUTOCORR,
     "mechanism": "s62_swap_r2z2_vol_hill_tail_x_r2_vol_autocorr",
     "hypothesis": "R2_Z2(rank(R2_BIGBAR_DIR_SKEW_20)-rank(R2_VOL_AUTOCORR_20))的大bar阈值腿"
                   "(同样是median x5阈值构造)替换为VOL_HILL_TAIL_20(真正的尾指数，语义上更贴近'尾部形状'而非分位比)。",
     "expected_sign": -1},
]

_Q95_MED_RIGHT_LEGS = [
    ("A", _CONTINUOUS_BETA),
    ("B", _GAP_DD_CONSUMPTION),
    ("C", _YZ_OVERNIGHT_SHARE),
    ("D", _PERM_ENTROPY),
    ("E", _RESILIENCY),
]

for tag, right in _Q95_MED_RIGHT_LEGS:
    CANDIDATES.append({
        "id": f"S62P_{tag}", "operator": "rank_spread", "left": _VOL_Q95_MED, "right": right,
        "mechanism": f"s62_vol_q95_med_x_{right['name'].lower()}",
        "hypothesis": f"VOL_Q95_MED_20 x {right['name']}：无阈值量尾肥厚度原子配已验证原子。",
        "expected_sign": 1,
    })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
