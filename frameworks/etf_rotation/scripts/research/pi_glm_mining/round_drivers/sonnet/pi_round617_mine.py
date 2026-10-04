#!/usr/bin/env python3
"""Round 617 driver: S26R2 stage (only round) -- re-reproduction of pi
lane's core volume-channel atoms using pi's PRECISE definitions (5x
median-amount/volume threshold for big-bar/spike detection, tick-rule
direction), distinct from S26R's controller-paraphrased definitions
(top-10%-by-volume, mean+3*std threshold, positive-fraction-minus-0.5).
Main controller's pre-specified S26R2 direction after S27's closure
(round_616).

Atom health (round_617_atom_health): 4 new atoms in the new family
repl_volume_core_v2a/v2b. corr vs the corresponding S26R/shelf atoms:
R2_VOL_SPIKE_FREQ_20 0.57 (vs R_VOL_SPIKE_FREQ_20 -- meaningfully
different from the threshold change), R2_BIGBAR_DIR_SKEW_20 0.62 (vs
shelf BIGBAR_DIR_SKEW_20), R2_BIGBAR_VOL_SHARE_20 0.72 (vs shelf
BIGBAR_VOL_SHARE_20), R2_VOL_AUTOCORR_20 1.000 (vs S26R's
R_VOL_AUTOCORR_20 -- EXPECTED, since this atom's definition was never
changed by the pi-precise-definition correction, only the big-bar/
spike-frequency definitions changed; this is a legitimately identical
construct by design, not a copied implementation of a DIFFERENT atom).

This round: 4 atomic tests + 4 pair reproductions (R2_Z2, R2_CO36,
R2_BB1, R2_AI4), reusing S26R's R_ULCER_20/R_GAP_FILL_FRACTION_60
directly per the directive ('复用 S26R 的 R_ 版本')."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_617"

_R2_SPIKE = {"name": "R2_VOL_SPIKE_FREQ_20", "source": "repl_volume_core_v2a"}
_R2_SKEW = {"name": "R2_BIGBAR_DIR_SKEW_20", "source": "repl_volume_core_v2a"}
_R2_SHARE = {"name": "R2_BIGBAR_VOL_SHARE_20", "source": "repl_volume_core_v2b"}
_R2_AUTOCORR = {"name": "R2_VOL_AUTOCORR_20", "source": "repl_volume_core_v2b"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_R_GAP_FILL_60 = {"name": "R_GAP_FILL_FRACTION_60", "source": "repl_volume_core_b"}

base.CANDIDATES = [
    # ---- 4 atomic reproductions (pi's precise definitions) ----
    {"id": "S26R2A1", "operator": "atomic", "left": _R2_SPIKE, "right": _R2_SPIKE,
     "mechanism": "s26r2_r2_vol_spike_freq_20",
     "hypothesis": "按 pi 精确定义重写 VOL_SPIKE_FREQ_20（1m 成交量 > 当日成交量中位数×5 的 bar 占比，20 日均值）。体检 disc+0.0617/审计+0.0453，与 S26R 的 R_VOL_SPIKE_FREQ_20（不同阈值定义）corr=0.57（有意义地不同）。pi 单原子审计 +50.7bp。",
     "expected_sign": 1},
    {"id": "S26R2A2", "operator": "atomic", "left": _R2_SKEW, "right": _R2_SKEW,
     "mechanism": "s26r2_r2_bigbar_dir_skew_20",
     "hypothesis": "按 pi 精确定义重写 BIGBAR_DIR_SKEW_20（大 bar=成交额>当日中位数×5；方向用 tick rule；(买量−卖量)/大bar总量，20 日均值）。体检 disc−0.0084/审计+0.0042（接近零，弱），与既有 shelf BIGBAR_DIR_SKEW_20 corr=0.62。",
     "expected_sign": -1},
    {"id": "S26R2A3", "operator": "atomic", "left": _R2_SHARE, "right": _R2_SHARE,
     "mechanism": "s26r2_r2_bigbar_vol_share_20",
     "hypothesis": "按 pi 精确定义重写 BIGBAR_VOL_SHARE_20（大bar成交量/全日成交量，20 日均值）。体检 disc+0.0457/审计+0.0434（同向），与既有 shelf BIGBAR_VOL_SHARE_20 corr=0.72。pi 主控验证 +41.6bp/t2.26。",
     "expected_sign": 1},
    {"id": "S26R2A4", "operator": "atomic", "left": _R2_AUTOCORR, "right": _R2_AUTOCORR,
     "mechanism": "s26r2_r2_vol_autocorr_20",
     "hypothesis": "重写 VOL_AUTOCORR_20（1m成交量序列1阶自相关，日内估计，20日均值）——该原子定义未被 pi 精确定义修正影响（仅大bar/量突增定义变了），体检 disc−0.0723/审计−0.0548，与 S26R 的 R_VOL_AUTOCORR_20 corr=1.000（预期内，同一构造的合法重复，非误抄不同原子）。",
     "expected_sign": -1},
    # ---- 4 pair reproductions (原表达式，pi 精确定义版本) ----
    {"id": "S26R2Z2", "operator": "rank_spread", "left": _R2_SKEW, "right": _R2_AUTOCORR,
     "mechanism": "s26r2_z2",
     "hypothesis": "复现 pi Z2 = rank(BIGBAR_DIR_SKEW_20) - rank(VOL_AUTOCORR_20)，两腿均用 pi 精确定义。pi +49.2bp/t3.02。",
     "expected_sign": -1},
    {"id": "S26R2CO36", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _R2_SPIKE,
     "mechanism": "s26r2_co36",
     "hypothesis": "复现 pi CO36 = rank(VT_AUTOCORR_20) - rank(VOL_SPIKE_FREQ_20)。左腿沿用 S24 已独立实现的 VT_AUTOCORR_20，右腿用 pi 精确定义的 R2_VOL_SPIKE_FREQ_20。pi +47.7bp/t3.14。",
     "expected_sign": 1},
    {"id": "S26R2BB1", "operator": "rank_spread", "left": _R2_SPIKE, "right": _R_ULCER,
     "mechanism": "s26r2_bb1",
     "hypothesis": "复现 pi BB1 = rank(VOL_SPIKE_FREQ_20) - rank(ULCER_20)。左腿用 pi 精确定义的 R2_VOL_SPIKE_FREQ_20，右腿复用 S26R 的 R_ULCER_20（该原子定义无需 pi 精确修正）。pi +36.3bp/t2.46。",
     "expected_sign": 1},
    {"id": "S26R2AI4", "operator": "rank_spread", "left": _R_GAP_FILL_60, "right": _R2_SPIKE,
     "mechanism": "s26r2_ai4",
     "hypothesis": "复现 pi AI4 = rank(GAP_FILL_FRACTION_60) - rank(VOL_SPIKE_FREQ_20)。左腿复用 S26R 的 R_GAP_FILL_FRACTION_60，右腿用 pi 精确定义的 R2_VOL_SPIKE_FREQ_20。pi +42.7bp/t2.58。本轮末条。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
