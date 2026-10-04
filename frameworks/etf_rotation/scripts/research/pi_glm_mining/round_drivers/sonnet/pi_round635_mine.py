#!/usr/bin/env python3
"""Round 635 driver: S36 stage (main controller directive, 2026-09-21) --
merge this line's two strongest mechanisms into conditional-statistic
atoms: volume-free "overnight direction x intraday drawdown"
(UE3/HB1/S27B5, audit t 2.98-3.89) and volume-bearing "volume extremes
inside intraday drawdowns" (S29Q1/S33, audit t 3.4-3.9). New family
overnight_conditioned_drawdown_volume (4 atoms, time-series conditional
statistics only, no new 1m derivation -- reuses S27/S33's own raw daily
frames directly).

Small-sample pilot (3 symbols) ran 8.05s (two 1m passes, both already
paid for by S27/S33's own families); full 14-symbol run extrapolated
~38s, ran directly.

Atom health (round_635_atom_health): no shadow flags (all corr_vs_ref
<0.7); highest is ON_POS_TROUGH_PREPOST_RATIO_20 vs its own unconditioned
source TROUGH_PREPOST_VOL_RATIO_20 (0.55, expected since it's a
conditional subset of the same raw daily statistic, still independent
enough to test)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_635"

_SIGN_DIFF = {"name": "OVERNIGHT_SIGN_DDVOL_EXCESS_DIFF_20", "source": "overnight_conditioned_drawdown_volume"}
_GAP_SPLIT = {"name": "GAP_MAGNITUDE_UNDERWATER_SPLIT_20", "source": "overnight_conditioned_drawdown_volume"}
_ON_POS_PREPOST = {"name": "ON_POS_TROUGH_PREPOST_RATIO_20", "source": "overnight_conditioned_drawdown_volume"}
_GAP_DDVOL_CORR = {"name": "GAP_CONSUMPTION_DDVOL_CORR_20", "source": "overnight_conditioned_drawdown_volume"}

_PV_ELASTICITY = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}
_MFI_EXTREME = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_HAR_RESID = {"name": "S28_VOV_HAR_RESID_20", "source": "pi_repl_s28"}
_VT_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_FP_UP = {"name": "FIRST_PASSAGE_UP_20", "source": "first_passage_times_1m"}
_R2_BIGBAR = {"name": "R2_BIGBAR_VOL_SHARE_20", "source": "repl_volume_core_v2b"}
_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_EXTREME_ORDER = {"name": "EXTREME_TIME_ORDER", "source": "intraday_extremes_timing"}
_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_ON_SIGN_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}

base.CANDIDATES = [
    # ---- 4 atomic tests ----
    {"id": "S36A1", "operator": "atomic", "left": _SIGN_DIFF, "right": _SIGN_DIFF,
     "mechanism": "s36_sign_diff_atomic",
     "hypothesis": "OVERNIGHT_SIGN_DDVOL_EXCESS_DIFF_20（隔夜为正日的回撤段放量超额均值 − 隔夜为负日的均值，40日窗口）单原子门7重裁。"
                   "体检 disc_ic=+0.0010（近零），与 DD_VOL_SHARE_EXCESS_20 corr=0.24（独立）。"
                   "经济假设：隔夜上涨后遇到日内回撤若伴随放量=承接意愿强，正方向；隔夜下跌后回撤放量=延续抛压，也支持正方向（两种情形均指向差值为正更健康）。",
     "expected_sign": 1},
    {"id": "S36A2", "operator": "atomic", "left": _GAP_SPLIT, "right": _GAP_SPLIT,
     "mechanism": "s36_gap_split_atomic",
     "hypothesis": "GAP_MAGNITUDE_UNDERWATER_SPLIT_20（按隔夜跳空幅度/σ的20日中位数分半，高跳空幅度日水下占比均值 − 低跳空幅度日均值）单原子门7重裁。"
                   "体检 disc_ic=-0.0236，与 UNDERWATER_FRAC_20 corr=0.04（几乎独立，切面不同）。经济假设：大跳空后日内更易陷入回撤，正方向不确定，标记为待发现期验证。",
     "expected_sign": -1},
    {"id": "S36A3", "operator": "atomic", "left": _ON_POS_PREPOST, "right": _ON_POS_PREPOST,
     "mechanism": "s36_on_pos_prepost_atomic",
     "hypothesis": "ON_POS_TROUGH_PREPOST_RATIO_20（仅隔夜为正的日子，谷底前后量比的40日条件均值）单原子门7重裁。"
                   "体检 disc_ic=+0.0222，与无条件版 TROUGH_PREPOST_VOL_RATIO_20 corr=0.55（独立但偏高，条件化后信息部分保留）。"
                   "经济假设：隔夜上涨后若谷底前恐慌放量大于谷底后=浅尝辄止的洗盘，正方向。",
     "expected_sign": 1},
    {"id": "S36A4", "operator": "atomic", "left": _GAP_DDVOL_CORR, "right": _GAP_DDVOL_CORR,
     "mechanism": "s36_gap_ddvol_corr_atomic",
     "hypothesis": "GAP_CONSUMPTION_DDVOL_CORR_20（跳空被吃掉比例与回撤段放量占比的20日滚动相关）单原子门7重裁。"
                   "体检 disc_ic=-0.0344，与 GAP_DD_CONSUMPTION_RATIO_20 corr=-0.02（独立）。"
                   "经济假设：跳空被日内回撤吃得越多、同时回撤段越放量=真实抛压主导，负方向。",
     "expected_sign": -1},
    # ---- 11 pairs ----
    {"id": "S36P1", "operator": "rank_spread", "left": _SIGN_DIFF, "right": _PV_ELASTICITY,
     "mechanism": "s36_p1", "hypothesis": "OVERNIGHT_SIGN_DDVOL_EXCESS_DIFF_20 × PV_ELASTICITY_20（S14，量价弹性）。方向由发现期定。", "expected_sign": 1},
    {"id": "S36P2", "operator": "rank_spread", "left": _SIGN_DIFF, "right": _MFI_EXTREME,
     "mechanism": "s36_p2", "hypothesis": "OVERNIGHT_SIGN_DDVOL_EXCESS_DIFF_20 × MFI_EXTREME_FRAC_20（S10）。方向由发现期定。", "expected_sign": 1},
    {"id": "S36P3", "operator": "rank_spread", "left": _SIGN_DIFF, "right": _D1_LEVEL,
     "mechanism": "s36_p3", "hypothesis": "OVERNIGHT_SIGN_DDVOL_EXCESS_DIFF_20 × D1_LEVEL_60（S20，价格延迟）。方向由发现期定。", "expected_sign": 1},
    {"id": "S36P4", "operator": "rank_spread", "left": _GAP_SPLIT, "right": _HAR_RESID,
     "mechanism": "s36_p4", "hypothesis": "GAP_MAGNITUDE_UNDERWATER_SPLIT_20 × S28_VOV_HAR_RESID_20（S28）。方向由发现期定。", "expected_sign": -1},
    {"id": "S36P5", "operator": "rank_spread", "left": _GAP_SPLIT, "right": _VT_GINI,
     "mechanism": "s36_p5", "hypothesis": "GAP_MAGNITUDE_UNDERWATER_SPLIT_20 × VT_BUCKET_GINI_20（S24）。方向由发现期定。", "expected_sign": -1},
    {"id": "S36P6", "operator": "rank_spread", "left": _GAP_SPLIT, "right": _FP_UP,
     "mechanism": "s36_p6", "hypothesis": "GAP_MAGNITUDE_UNDERWATER_SPLIT_20 × FIRST_PASSAGE_UP_20（S17，同属首达/回撤框架）。方向由发现期定。", "expected_sign": -1},
    {"id": "S36P7", "operator": "rank_spread", "left": _ON_POS_PREPOST, "right": _R2_BIGBAR,
     "mechanism": "s36_p7", "hypothesis": "ON_POS_TROUGH_PREPOST_RATIO_20 × R2_BIGBAR_VOL_SHARE_20（S26R2）。方向由发现期定。", "expected_sign": 1},
    {"id": "S36P8", "operator": "rank_spread", "left": _ON_POS_PREPOST, "right": _R_ULCER,
     "mechanism": "s36_p8", "hypothesis": "ON_POS_TROUGH_PREPOST_RATIO_20 × R_ULCER_20（S26R）。方向由发现期定。", "expected_sign": 1},
    {"id": "S36P9", "operator": "rank_spread", "left": _ON_POS_PREPOST, "right": _EXTREME_ORDER,
     "mechanism": "s36_p9", "hypothesis": "ON_POS_TROUGH_PREPOST_RATIO_20 × EXTREME_TIME_ORDER（日内极值时序）。方向由发现期定。", "expected_sign": 1},
    {"id": "S36P10", "operator": "rank_spread", "left": _GAP_DDVOL_CORR, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s36_p10", "hypothesis": "GAP_CONSUMPTION_DDVOL_CORR_20 × R_LOG_AMOUNT_VOL_20（S26R）。方向由发现期定。", "expected_sign": -1},
    {"id": "S36P11", "operator": "rank_spread", "left": _GAP_DDVOL_CORR, "right": _ON_SIGN_STREAK,
     "mechanism": "s36_p11", "hypothesis": "GAP_CONSUMPTION_DDVOL_CORR_20 × ON_SIGN_STREAK_20（S21，本轮末条）。方向由发现期定。", "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
