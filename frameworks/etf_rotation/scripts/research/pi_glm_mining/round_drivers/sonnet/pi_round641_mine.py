#!/usr/bin/env python3
"""Round 641 driver: S42 stage (main controller directive, 2026-09-21) --
second no-volume top-atom pairing scan (first was S18: round_5xx, only
1/16 admissions with both legs volume-free). Pool of no-volume atoms has
grown substantially since S18 (GAP_DD_CONSUMPTION_RATIO_20,
ON_SIGN_STREAK_20, YZ_OVERNIGHT_SHARE_20, REL_UNDERWATER_CATEGORY_*,
first-passage/pre-breakout atoms, S41 overnight-distribution atoms,
etc.) No new atoms built this round -- pure re-pairing of already-
validated atoms, same as S16/S25's pattern.

Pool construction (script-assisted, not hand-picked): took every unique
atom name appearing in any round_500+ gate_pass=True candidate (136
atoms total, via outputs/round_638/slow_signal_profile.csv), dropped
any atom whose name contains a volume-level keyword (VOL, BAR, MFI,
TURNOVER, AMOUNT, OBV, TICK, LBAR, AD_, ELASTICITY -- kept volume-TIMING
constructs like LUNCH_PRE_RUN_20 and VT_AUTOCORR_20 since they measure
WHEN/pattern, not volume magnitude), took the top 14 by best-recorded
audit block-t (H=5, K=3) with a <=2-per-source-family cap, then dropped
REL_UNDERWATER_CATEGORY_CHG_20 (rank corr 0.83 vs UNDERWATER_FRAC_CHG_20,
near-duplicate) and replaced it with the next-best atom
(UNDERWATER_FRAC_Z_60, corr <0.25 vs everything else in the pool,
confirmed via direct pairwise check).

Final pool (14 atoms, best audit t): GAP_DD_CONSUMPTION_RATIO_20 (3.89),
UNDERWATER_FRAC_CHG_20 (3.44), YZ_OVERNIGHT_SHARE_20 (3.08),
ON_SIGN_STREAK_20 (2.98), REL_UNDERWATER_CATEGORY_20 (2.84),
VT_AUTOCORR_20 (2.63), LUNCH_PRE_RUN_20 (2.59), CLOSE5_DAY_CONSIST_20
(2.59), NOISE_VAR_20 (2.48), D1_LEVEL_60 (2.44), ON_STREAK_UF_COV_20
(2.34), SAMPEN_RET_20 (2.34), MSPE_15M_20 (2.31), UNDERWATER_FRAC_Z_60
(2.31).

Enumerated all cross-family, never-before-tested (canonical-hash
checked against every round_*/PLAN.json in this workspace) pairs (68
legal combos), sorted by discovery-audit-t sum, greedily selected 26
respecting pairing discipline (each atom <=8 pairs as left leg, <=3
distinct left partners as right leg)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_641"

_GAP_DD = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_UWF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_YZ_ON = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_ON_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}
_REL_UW_CAT = {"name": "REL_UNDERWATER_CATEGORY_20", "source": "mechanism_atoms_v2"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_LUNCH_PRE = {"name": "LUNCH_PRE_RUN_20", "source": "pi_lunch_prerun_1m"}
_CLOSE5 = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}
_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_ON_STREAK_UF = {"name": "ON_STREAK_UF_COV_20", "source": "overnight_intraday_mismatch_v1"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_MSPE15 = {"name": "MSPE_15M_20", "source": "complexity_measures_1m"}
_UWF_Z = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}

base.CANDIDATES = [
    {"id": "S42P1", "operator": "rank_spread", "left": _GAP_DD, "right": _YZ_ON,
     "mechanism": "s42_p1", "hypothesis": "跳空吸收比例 × 隔夜方差占比，两条本线最强无量单原子首次互配，t 和最高(6.97)。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P2", "operator": "rank_spread", "left": _GAP_DD, "right": _ON_STREAK,
     "mechanism": "s42_p2", "hypothesis": "跳空吸收比例 × 隔夜符号连续。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P3", "operator": "rank_spread", "left": _GAP_DD, "right": _REL_UW_CAT,
     "mechanism": "s42_p3", "hypothesis": "跳空吸收比例 × 类别内相对水下占比。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P4", "operator": "rank_spread", "left": _GAP_DD, "right": _LUNCH_PRE,
     "mechanism": "s42_p4", "hypothesis": "跳空吸收比例 × 午前抢跑量占比（量的时间分布，允许）。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P5", "operator": "rank_spread", "left": _GAP_DD, "right": _CLOSE5,
     "mechanism": "s42_p5", "hypothesis": "跳空吸收比例 × 尾5分钟方向一致率。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P6", "operator": "rank_spread", "left": _GAP_DD, "right": _NOISE_VAR,
     "mechanism": "s42_p6", "hypothesis": "跳空吸收比例 × 噪声方差。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P7", "operator": "rank_spread", "left": _UWF_CHG, "right": _REL_UW_CAT,
     "mechanism": "s42_p7", "hypothesis": "水下占比变化（绝对）× 类别内相对水下占比——同一几何概念的绝对/相对两个切面首次互配。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P8", "operator": "rank_spread", "left": _GAP_DD, "right": _SAMPEN,
     "mechanism": "s42_p8", "hypothesis": "跳空吸收比例 × 收益样本熵。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P9", "operator": "rank_spread", "left": _GAP_DD, "right": _MSPE15,
     "mechanism": "s42_p9", "hypothesis": "跳空吸收比例 × 15分钟多尺度排列熵。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P10", "operator": "rank_spread", "left": _UWF_Z, "right": _GAP_DD,
     "mechanism": "s42_p10", "hypothesis": "水下占比60日z分数 × 跳空吸收比例（跳空吸收本轮末次作右腿，用满8条左腿配额）。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P11", "operator": "rank_spread", "left": _YZ_ON, "right": _ON_STREAK,
     "mechanism": "s42_p11", "hypothesis": "隔夜方差占比 × 隔夜符号连续——两个隔夜维度原子首次互配。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P12", "operator": "rank_spread", "left": _UWF_CHG, "right": _LUNCH_PRE,
     "mechanism": "s42_p12", "hypothesis": "水下占比变化 × 午前抢跑量占比。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P13", "operator": "rank_spread", "left": _UWF_CHG, "right": _CLOSE5,
     "mechanism": "s42_p13", "hypothesis": "水下占比变化 × 尾5分钟方向一致率。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P14", "operator": "rank_spread", "left": _ON_STREAK, "right": _REL_UW_CAT,
     "mechanism": "s42_p14", "hypothesis": "隔夜符号连续 × 类别内相对水下占比。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P15", "operator": "rank_spread", "left": _UWF_CHG, "right": _SAMPEN,
     "mechanism": "s42_p15", "hypothesis": "水下占比变化 × 收益样本熵。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P16", "operator": "rank_spread", "left": _UWF_CHG, "right": _MSPE15,
     "mechanism": "s42_p16", "hypothesis": "水下占比变化 × 15分钟多尺度排列熵。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P17", "operator": "rank_spread", "left": _UWF_CHG, "right": _UWF_Z,
     "mechanism": "s42_p17", "hypothesis": "水下占比变化（20日）× 水下占比60日z分数——同一回撤几何的不同滚动窗构造首次互配。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P18", "operator": "rank_spread", "left": _YZ_ON, "right": _LUNCH_PRE,
     "mechanism": "s42_p18", "hypothesis": "隔夜方差占比 × 午前抢跑量占比。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P19", "operator": "rank_spread", "left": _YZ_ON, "right": _CLOSE5,
     "mechanism": "s42_p19", "hypothesis": "隔夜方差占比 × 尾5分钟方向一致率。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P20", "operator": "rank_spread", "left": _LUNCH_PRE, "right": _ON_STREAK,
     "mechanism": "s42_p20", "hypothesis": "午前抢跑量占比 × 隔夜符号连续。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P21", "operator": "rank_spread", "left": _ON_STREAK, "right": _NOISE_VAR,
     "mechanism": "s42_p21", "hypothesis": "隔夜符号连续 × 噪声方差。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P22", "operator": "rank_spread", "left": _YZ_ON, "right": _SAMPEN,
     "mechanism": "s42_p22", "hypothesis": "隔夜方差占比 × 收益样本熵。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P23", "operator": "rank_spread", "left": _YZ_ON, "right": _ON_STREAK_UF,
     "mechanism": "s42_p23", "hypothesis": "隔夜方差占比 × 隔夜符号连续与水下占比的滚动协方差。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P24", "operator": "rank_spread", "left": _YZ_ON, "right": _MSPE15,
     "mechanism": "s42_p24", "hypothesis": "隔夜方差占比 × 15分钟多尺度排列熵。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P25", "operator": "rank_spread", "left": _YZ_ON, "right": _UWF_Z,
     "mechanism": "s42_p25", "hypothesis": "隔夜方差占比 × 水下占比60日z分数（隔夜方差占比本轮末次作左腿，用满7条）。方向由发现期定。", "expected_sign": 1},
    {"id": "S42P26", "operator": "rank_spread", "left": _ON_STREAK, "right": _ON_STREAK_UF,
     "mechanism": "s42_p26", "hypothesis": "隔夜符号连续 × 隔夜符号连续与水下占比协方差——同源不同统计量首次互配，本轮末条。方向由发现期定。", "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
