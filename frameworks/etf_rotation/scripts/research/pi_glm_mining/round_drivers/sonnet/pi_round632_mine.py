#!/usr/bin/env python3
"""Round 632 driver: S33 stage (main controller directive, 2026-09-21) --
deepen the "MFI extremes inside intraday drawdowns" mechanism (this
line's strongest content channel: S27B5 t3.89, S29Q1 t3.60). New family
volume_extremes_in_drawdown_1m (7 atoms, self-contained single 1m pass,
no cross-family imports).

Small-sample pilot (3 symbols) ran 4.22s, all atoms 100% finite; full
14-symbol run extrapolated ~20s, ran directly.

Atom health (round_632_atom_health): 6 of 7 atoms independent (corr
<0.26 vs reference). Only DD_BIGBAR_VOL_SHARE_20 shadow-flagged
(corr=0.85 vs MFI_EXTREME_FRAC_20) -- pairings avoid using
MFI_EXTREME_FRAC_20 as its right leg to sidestep tautological
redundancy. Strongest disc_ic: RECOVERY_VOL_SHARE_EXCESS_20 (0.088),
DD_VOL_SHARE_EXCESS_20 (0.086).

7 atomic tests + 14 pairs (2 right legs per left atom, pairing
discipline respected). Right legs: strong previously-validated atoms
not yet used this stage, redundancy-magnet atoms excluded."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_632"

_DD_VOL_EXCESS = {"name": "DD_VOL_SHARE_EXCESS_20", "source": "volume_extremes_in_drawdown_1m"}
_PREPOST_RATIO = {"name": "TROUGH_PREPOST_VOL_RATIO_20", "source": "volume_extremes_in_drawdown_1m"}
_DD_RET_VOL_CORR = {"name": "DD_RET_VOL_CORR_20", "source": "volume_extremes_in_drawdown_1m"}
_DD_BIGBAR = {"name": "DD_BIGBAR_VOL_SHARE_20", "source": "volume_extremes_in_drawdown_1m"}
_RECOVERY_VOL = {"name": "RECOVERY_VOL_SHARE_EXCESS_20", "source": "volume_extremes_in_drawdown_1m"}
_DD_VOL_EXCESS_CHG = {"name": "DD_VOL_SHARE_EXCESS_CHG_20", "source": "volume_extremes_in_drawdown_1m"}
_DD_RET_VOL_CORR_CHG = {"name": "DD_RET_VOL_CORR_CHG_20", "source": "volume_extremes_in_drawdown_1m"}

_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_VT_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_HAR_RESID = {"name": "S28_VOV_HAR_RESID_20", "source": "pi_repl_s28"}
_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_PV_ELASTICITY = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}

base.CANDIDATES = [
    # ---- 7 atomic tests ----
    {"id": "S33A1", "operator": "atomic", "left": _DD_VOL_EXCESS, "right": _DD_VOL_EXCESS,
     "mechanism": "s33_dd_vol_excess_atomic",
     "hypothesis": "DD_VOL_SHARE_EXCESS_20（水下 bar 成交量占比 − 水下 bar 数占比，20 日均值）单原子门 7 重裁。体检 disc_ic 0.086，与 MFI_EXTREME_UNDERWATER_SKEW_20 corr=0.25（独立）。",
     "expected_sign": 1},
    {"id": "S33A2", "operator": "atomic", "left": _PREPOST_RATIO, "right": _PREPOST_RATIO,
     "mechanism": "s33_prepost_ratio_atomic",
     "hypothesis": "TROUGH_PREPOST_VOL_RATIO_20（谷底前5bar/后5bar成交量对数比，20 日均值）单原子门 7 重裁。体检 disc_ic 0.028，corr_vs_ref=0.06（独立）。",
     "expected_sign": 1},
    {"id": "S33A3", "operator": "atomic", "left": _DD_RET_VOL_CORR, "right": _DD_RET_VOL_CORR,
     "mechanism": "s33_dd_ret_vol_corr_atomic",
     "hypothesis": "DD_RET_VOL_CORR_20（水下 bar 内收益与成交量相关，20 日均值）单原子门 7 重裁。体检 disc_ic 0.062，与 AD_PRICE_CORR_20 corr=−0.12（独立）。",
     "expected_sign": 1},
    {"id": "S33A4", "operator": "atomic", "left": _DD_BIGBAR, "right": _DD_BIGBAR,
     "mechanism": "s33_dd_bigbar_atomic",
     "hypothesis": "DD_BIGBAR_VOL_SHARE_20（水下段大 bar 成交量占水下段总量比例，pi 精确定义，20 日均值）单原子门 7 重裁。体检 disc_ic 0.077，与 MFI_EXTREME_FRAC_20 corr=0.85（shadow，冗余风险高）。",
     "expected_sign": 1},
    {"id": "S33A5", "operator": "atomic", "left": _RECOVERY_VOL, "right": _RECOVERY_VOL,
     "mechanism": "s33_recovery_vol_atomic",
     "hypothesis": "RECOVERY_VOL_SHARE_EXCESS_20（恢复段成交量占比 − 恢复段 bar 数占比，20 日均值）单原子门 7 重裁。体检 disc_ic 0.088（本批最强），与 RECOVERY_TIME_FRAC_20 corr=−0.12（独立）。",
     "expected_sign": 1},
    {"id": "S33A6", "operator": "atomic", "left": _DD_VOL_EXCESS_CHG, "right": _DD_VOL_EXCESS_CHG,
     "mechanism": "s33_dd_vol_excess_chg_atomic",
     "hypothesis": "DD_VOL_SHARE_EXCESS_CHG_20（DD_VOL_SHARE_EXCESS_20 的 20 日变化）单原子门 7 重裁。体检 disc_ic −0.003，corr_vs_ref=0.13（独立）。",
     "expected_sign": -1},
    {"id": "S33A7", "operator": "atomic", "left": _DD_RET_VOL_CORR_CHG, "right": _DD_RET_VOL_CORR_CHG,
     "mechanism": "s33_dd_ret_vol_corr_chg_atomic",
     "hypothesis": "DD_RET_VOL_CORR_CHG_20（DD_RET_VOL_CORR_20 的 20 日变化）单原子门 7 重裁。体检 disc_ic −0.026，corr_vs_ref=0.04（独立）。",
     "expected_sign": -1},
    # ---- 14 pairs (2 right legs per left atom, avoiding tautological MFI_EXTREME_FRAC_20 pairing) ----
    {"id": "S33P1", "operator": "rank_spread", "left": _DD_VOL_EXCESS, "right": _R_ULCER,
     "mechanism": "s33_p1", "hypothesis": "DD_VOL_SHARE_EXCESS_20 × R_ULCER_20（S26R）。方向由发现期定。", "expected_sign": 1},
    {"id": "S33P2", "operator": "rank_spread", "left": _DD_VOL_EXCESS, "right": _D1_LEVEL,
     "mechanism": "s33_p2", "hypothesis": "DD_VOL_SHARE_EXCESS_20 × D1_LEVEL_60（S20）。方向由发现期定。", "expected_sign": 1},
    {"id": "S33P3", "operator": "rank_spread", "left": _PREPOST_RATIO, "right": _VT_GINI,
     "mechanism": "s33_p3", "hypothesis": "TROUGH_PREPOST_VOL_RATIO_20 × VT_BUCKET_GINI_20（S24）。方向由发现期定。", "expected_sign": 1},
    {"id": "S33P4", "operator": "rank_spread", "left": _PREPOST_RATIO, "right": _HAR_RESID,
     "mechanism": "s33_p4", "hypothesis": "TROUGH_PREPOST_VOL_RATIO_20 × S28_VOV_HAR_RESID_20（S28）。方向由发现期定。", "expected_sign": 1},
    {"id": "S33P5", "operator": "rank_spread", "left": _DD_RET_VOL_CORR, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s33_p5", "hypothesis": "DD_RET_VOL_CORR_20 × R_LOG_AMOUNT_VOL_20（S26R）。方向由发现期定。", "expected_sign": 1},
    {"id": "S33P6", "operator": "rank_spread", "left": _DD_RET_VOL_CORR, "right": _PV_ELASTICITY,
     "mechanism": "s33_p6", "hypothesis": "DD_RET_VOL_CORR_20 × PV_ELASTICITY_20（S14）。方向由发现期定。", "expected_sign": 1},
    {"id": "S33P7", "operator": "rank_spread", "left": _DD_BIGBAR, "right": _R_ULCER,
     "mechanism": "s33_p7", "hypothesis": "DD_BIGBAR_VOL_SHARE_20 × R_ULCER_20（避免与 MFI_EXTREME_FRAC_20 自身配对造成同源冗余）。方向由发现期定。", "expected_sign": 1},
    {"id": "S33P8", "operator": "rank_spread", "left": _DD_BIGBAR, "right": _VT_GINI,
     "mechanism": "s33_p8", "hypothesis": "DD_BIGBAR_VOL_SHARE_20 × VT_BUCKET_GINI_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S33P9", "operator": "rank_spread", "left": _RECOVERY_VOL, "right": _D1_LEVEL,
     "mechanism": "s33_p9", "hypothesis": "RECOVERY_VOL_SHARE_EXCESS_20 × D1_LEVEL_60。方向由发现期定。", "expected_sign": 1},
    {"id": "S33P10", "operator": "rank_spread", "left": _RECOVERY_VOL, "right": _HAR_RESID,
     "mechanism": "s33_p10", "hypothesis": "RECOVERY_VOL_SHARE_EXCESS_20 × S28_VOV_HAR_RESID_20。方向由发现期定。", "expected_sign": 1},
    {"id": "S33P11", "operator": "rank_spread", "left": _DD_VOL_EXCESS_CHG, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s33_p11", "hypothesis": "DD_VOL_SHARE_EXCESS_CHG_20 × R_LOG_AMOUNT_VOL_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S33P12", "operator": "rank_spread", "left": _DD_VOL_EXCESS_CHG, "right": _R_ULCER,
     "mechanism": "s33_p12", "hypothesis": "DD_VOL_SHARE_EXCESS_CHG_20 × R_ULCER_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S33P13", "operator": "rank_spread", "left": _DD_RET_VOL_CORR_CHG, "right": _PV_ELASTICITY,
     "mechanism": "s33_p13", "hypothesis": "DD_RET_VOL_CORR_CHG_20 × PV_ELASTICITY_20。方向由发现期定。", "expected_sign": -1},
    {"id": "S33P14", "operator": "rank_spread", "left": _DD_RET_VOL_CORR_CHG, "right": _D1_LEVEL,
     "mechanism": "s33_p14", "hypothesis": "DD_RET_VOL_CORR_CHG_20 × D1_LEVEL_60。本轮末条。方向由发现期定。", "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
