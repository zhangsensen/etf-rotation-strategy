#!/usr/bin/env python3
"""Round 612 driver: S26 stage, CORRECTED per main controller's
2026-09-20 23:35 note (round_609's hash-collision check was wrong --
that just proved the atoms were pi lane's own pre-existing shelf code,
not an independent reproduction). This round uses the brand-new family
`repl_volume_core_v1` (7 atoms, all prefixed R_, written from the S26
literature definitions without importing or copying any existing
family's code -- see families/repl_volume_core_v1.py for the full
from-scratch implementation).

Atom health (round_612_atom_health): rank corr vs the pre-existing
shelf atoms of the same concept ranges 0.45-0.89 (R_VOL_SPIKE_FREQ_20
0.53, R_BIGBAR_VOL_SHARE_20 0.89, R_BIGBAR_DIR_SKEW_20 0.45,
R_VOL_AUTOCORR_20 0.86, R_LOG_AMOUNT_VOL_20 0.77,
R_GAP_FILL_FRACTION_60 0.76) -- related but NONE equal to 1.000,
confirming genuinely independent construction per the controller's
explicit check (corr==1.000 would indicate a copy). R_ULCER_20's old
counterpart lives under a shelf family whose config file could not be
resolved by name ('ohlcv'), so no corr check was possible for that one
atom; its own disc/audit IC was still computed normally.

This round: 7 atomic tests (one per R_ atom) + 4 pair reproductions
using R_ atoms in place of the original shelf atoms (R_CO36 keeps
VT_AUTOCORR_20 from S24's already-independently-built volume_time_1m
family, since that side of the pair was never in question -- only the
VOL_SPIKE_FREQ_20 side needed the R_ rewrite)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_612"

_R_VOL_SPIKE_FREQ = {"name": "R_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_a"}
_R_BIGBAR_VOL_SHARE = {"name": "R_BIGBAR_VOL_SHARE_20", "source": "repl_volume_core_b"}
_R_BIGBAR_DIR_SKEW = {"name": "R_BIGBAR_DIR_SKEW_20", "source": "repl_volume_core_a"}
_R_VOL_AUTOCORR = {"name": "R_VOL_AUTOCORR_20", "source": "repl_volume_core_b"}
_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_R_ULCER_20 = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_R_GAP_FILL_60 = {"name": "R_GAP_FILL_FRACTION_60", "source": "repl_volume_core_b"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}

base.CANDIDATES = [
    # ---- 7 atomic reproductions (independent rewrite, R_ prefix) ----
    {"id": "S26RA1", "operator": "atomic", "left": _R_VOL_SPIKE_FREQ, "right": _R_VOL_SPIKE_FREQ,
     "mechanism": "s26_r_vol_spike_freq_20",
     "hypothesis": "独立重写 VOL_SPIKE_FREQ_20（1m 成交量超过当日均量+3σ 的 bar 占比 20 日均值，全新代码，无 import）。体检 disc+0.0377/审计+0.0085，与既有原子 corr=0.53（非拷贝）。pi 单原子审计 +50.7bp。",
     "expected_sign": 1},
    {"id": "S26RA2", "operator": "atomic", "left": _R_BIGBAR_VOL_SHARE, "right": _R_BIGBAR_VOL_SHARE,
     "mechanism": "s26_r_bigbar_vol_share_20",
     "hypothesis": "独立重写 BIGBAR_VOL_SHARE_20（成交量最大 10% bar 的成交量占全日比例 20 日均值）。体检 disc+0.0661/审计+0.0382，与既有原子 corr=0.89（非拷贝）。pi 主控验证 +41.6bp/t2.26。",
     "expected_sign": 1},
    {"id": "S26RA3", "operator": "atomic", "left": _R_BIGBAR_DIR_SKEW, "right": _R_BIGBAR_DIR_SKEW,
     "mechanism": "s26_r_bigbar_dir_skew_20",
     "hypothesis": "独立重写 BIGBAR_DIR_SKEW_20（大 bar 中收益为正的比例−0.5，20 日均值）。体检 disc−0.1133/审计−0.0566，与既有原子 corr=0.45（非拷贝，相关性最低的一条）。",
     "expected_sign": -1},
    {"id": "S26RA4", "operator": "atomic", "left": _R_VOL_AUTOCORR, "right": _R_VOL_AUTOCORR,
     "mechanism": "s26_r_vol_autocorr_20",
     "hypothesis": "独立重写 VOL_AUTOCORR_20（1m 成交量序列 1 阶自相关，日内估计，20 日均值）。体检 disc−0.0723/审计−0.0548，与既有原子 corr=0.86（非拷贝）。",
     "expected_sign": -1},
    {"id": "S26RA5", "operator": "atomic", "left": _R_LOG_AMOUNT_VOL, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s26_r_log_amount_vol_20",
     "hypothesis": "独立重写 LOG_AMOUNT_VOL_20（log 日成交额的 20 日标准差）。体检 disc+0.0327/审计+0.0526，与既有原子 corr=0.77（非拷贝）。",
     "expected_sign": 1},
    {"id": "S26RA6", "operator": "atomic", "left": _R_ULCER_20, "right": _R_ULCER_20,
     "mechanism": "s26_r_ulcer_20",
     "hypothesis": "独立重写 ULCER_20（Martin-McCann 1989 溃疡指数，20 日收盘价窗口）。体检 disc−0.0297/审计−0.0607；既有同名原子所在族 config 未能按名解析，无法算相关性，但本原子是全新代码独立实现。",
     "expected_sign": -1},
    {"id": "S26RA7", "operator": "atomic", "left": _R_GAP_FILL_60, "right": _R_GAP_FILL_60,
     "mechanism": "s26_r_gap_fill_fraction_60",
     "hypothesis": "独立重写 GAP_FILL_FRACTION_60（跳空当日被回补比例 60 日均值）。体检 disc−0.0411/审计−0.0376，与既有原子 corr=0.76（非拷贝）。",
     "expected_sign": -1},
    # ---- 4 pair reproductions (原表达式，用 R_ 原子重写) ----
    {"id": "S26RZ2", "operator": "rank_spread", "left": _R_BIGBAR_DIR_SKEW, "right": _R_VOL_AUTOCORR,
     "mechanism": "s26_r_z2",
     "hypothesis": "复现 pi Z2 = rank(BIGBAR_DIR_SKEW_20) - rank(VOL_AUTOCORR_20)，两腿均用本轮独立重写的 R_ 原子。pi +49.2bp/t3.02。",
     "expected_sign": 1},
    {"id": "S26RCO36", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _R_VOL_SPIKE_FREQ,
     "mechanism": "s26_r_co36",
     "hypothesis": "复现 pi CO36 = rank(VT_AUTOCORR_20) - rank(VOL_SPIKE_FREQ_20)。左腿用 S24 已独立实现的 VT_AUTOCORR_20（volume_time_1m，未读 pi 代码建成），右腿用本轮独立重写的 R_VOL_SPIKE_FREQ_20。pi +47.7bp/t3.14。",
     "expected_sign": 1},
    {"id": "S26RBB1", "operator": "rank_spread", "left": _R_VOL_SPIKE_FREQ, "right": _R_ULCER_20,
     "mechanism": "s26_r_bb1",
     "hypothesis": "复现 pi BB1 = rank(VOL_SPIKE_FREQ_20) - rank(ULCER_20)，两腿均用本轮独立重写的 R_ 原子。pi +36.3bp/t2.46。",
     "expected_sign": 1},
    {"id": "S26RAI4", "operator": "rank_spread", "left": _R_GAP_FILL_60, "right": _R_VOL_SPIKE_FREQ,
     "mechanism": "s26_r_ai4",
     "hypothesis": "复现 pi AI4 = rank(GAP_FILL_FRACTION_60) - rank(VOL_SPIKE_FREQ_20)，两腿均用本轮独立重写的 R_ 原子。pi +42.7bp/t2.58。本轮末条。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
