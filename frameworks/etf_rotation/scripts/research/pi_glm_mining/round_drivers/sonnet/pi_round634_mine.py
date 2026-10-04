#!/usr/bin/env python3
"""Round 634 driver: S35 stage (main controller directive, 2026-09-21) --
mechanism atom fourth batch: pre_breakout_drawdown_1m (pi stage-34 DB09's
"how much drawdown before an upward breakout" mechanism, the only
first-passage-time pairing that survived audit: +31.9bp/t2.06). New
family pre_breakout_drawdown_1m (5 atoms, self-contained single 1m pass,
sigma-calibrated, no fixed threshold).

Small-sample pilot (3 symbols) ran 3.57s; POST_TROUGH_RECOVERY_20's
rolling min_periods was lowered 8->4 after the pilot showed daily
-1sigma touch rate is only ~18.5% (too rare for min_periods=8 in a
20-day window); full 14-symbol run extrapolated ~17s, ran directly.

Atom health (round_634_atom_health): no shadow flags (all corr_vs_ref
<0.7); closest are PRE_BREAKOUT_UNDERWATER_FRAC_20 vs UNDERWATER_FRAC_20
(0.69) and PRE_BREAKOUT_UNDERWATER_FRAC_CHG_20 vs UNDERWATER_FRAC_CHG_20
(0.64) -- both near but under threshold, noted as elevated-but-passing.
POST_TROUGH_RECOVERY_20 has thin discovery sample (100 days) since it is
conditioned on the rare -1sigma touch event.

5 atomic tests + 10 pairs (2 right legs per left atom, all distinct
right legs so no right-leg reuse cap is at risk, pairing discipline
respected)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_634"

_MAXDD_SIGMA = {"name": "PRE_BREAKOUT_MAXDD_SIGMA_20", "source": "pre_breakout_drawdown_1m"}
_UWF = {"name": "PRE_BREAKOUT_UNDERWATER_FRAC_20", "source": "pre_breakout_drawdown_1m"}
_RECOVERY = {"name": "POST_TROUGH_RECOVERY_20", "source": "pre_breakout_drawdown_1m"}
_MAXDD_SIGMA_CHG = {"name": "PRE_BREAKOUT_MAXDD_SIGMA_CHG_20", "source": "pre_breakout_drawdown_1m"}
_UWF_CHG = {"name": "PRE_BREAKOUT_UNDERWATER_FRAC_CHG_20", "source": "pre_breakout_drawdown_1m"}

_FP_UP = {"name": "FIRST_PASSAGE_UP_20", "source": "first_passage_times_1m"}
_EXTREME_ORDER = {"name": "EXTREME_TIME_ORDER", "source": "intraday_extremes_timing"}
_PV_ELASTICITY = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}
_HAR_RESID = {"name": "S28_VOV_HAR_RESID_20", "source": "pi_repl_s28"}
_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_VT_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_MFI_EXTREME = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_ON_SIGN_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}
_D1_LEVEL = {"name": "D1_LEVEL_60", "source": "price_delay"}
_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}

base.CANDIDATES = [
    # ---- 5 atomic tests ----
    {"id": "S35A1", "operator": "atomic", "left": _MAXDD_SIGMA, "right": _MAXDD_SIGMA,
     "mechanism": "s35_maxdd_sigma_atomic",
     "hypothesis": "PRE_BREAKOUT_MAXDD_SIGMA_20（首次触及+1sigma前的最大回撤/sigma，未触及记全日）单原子门7重裁。"
                   "体检 disc_ic=-0.0315，与 INTRADAY_MAXDD_20 corr=0.54（独立）。经济假设：击穿前承受的回撤越深（相对当日sigma标定），"
                   "越像洗盘充分后的真突破，预期正方向。",
     "expected_sign": 1},
    {"id": "S35A2", "operator": "atomic", "left": _UWF, "right": _UWF,
     "mechanism": "s35_underwater_frac_atomic",
     "hypothesis": "PRE_BREAKOUT_UNDERWATER_FRAC_20（击穿前水下 bar 占比）单原子门7重裁。"
                   "体检 disc_ic=-0.0406，与 UNDERWATER_FRAC_20 corr=0.69（独立但偏高，非 shadow）。"
                   "经济假设同 S35A1，预期正方向。",
     "expected_sign": 1},
    {"id": "S35A3", "operator": "atomic", "left": _RECOVERY, "right": _RECOVERY,
     "mechanism": "s35_recovery_atomic",
     "hypothesis": "POST_TROUGH_RECOVERY_20（触及-1sigma后到收盘的恢复比例，仅在触及日计算）单原子门7重裁。"
                   "体检 disc_ic=+0.0268（样本仅100天，触及-1sigma是稀有事件），与 RECOVERY_TIME_FRAC_20 corr=0.06（独立）。"
                   "经济假设：触及后恢复越充分=承接越强，预期正方向。",
     "expected_sign": 1},
    {"id": "S35A4", "operator": "atomic", "left": _MAXDD_SIGMA_CHG, "right": _MAXDD_SIGMA_CHG,
     "mechanism": "s35_maxdd_sigma_chg_atomic",
     "hypothesis": "PRE_BREAKOUT_MAXDD_SIGMA_CHG_20（S35A1 的20日变化）单原子门7重裁。"
                   "体检 disc_ic=+0.0043，与 PASSAGE_ASYM_20 corr=-0.19（独立）。经济假设：击穿前忍耐力增强=延续，预期正方向。",
     "expected_sign": 1},
    {"id": "S35A5", "operator": "atomic", "left": _UWF_CHG, "right": _UWF_CHG,
     "mechanism": "s35_underwater_frac_chg_atomic",
     "hypothesis": "PRE_BREAKOUT_UNDERWATER_FRAC_CHG_20（S35A2 的20日变化）单原子门7重裁。"
                   "体检 disc_ic=-0.0219，与 UNDERWATER_FRAC_CHG_20 corr=0.64（独立但偏高，非 shadow）。"
                   "经济假设同 S35A4，预期正方向。",
     "expected_sign": 1},
    # ---- 10 pairs (2 distinct right legs per left atom, no right-leg reuse) ----
    {"id": "S35P1", "operator": "rank_spread", "left": _MAXDD_SIGMA, "right": _FP_UP,
     "mechanism": "s35_p1", "hypothesis": "PRE_BREAKOUT_MAXDD_SIGMA_20 × FIRST_PASSAGE_UP_20（S17）。"
                   "同属首达时间框架，检验\"击穿前忍痛深度\"与\"击穿速度\"是否互补。方向由发现期定。", "expected_sign": 1},
    {"id": "S35P2", "operator": "rank_spread", "left": _MAXDD_SIGMA, "right": _EXTREME_ORDER,
     "mechanism": "s35_p2", "hypothesis": "PRE_BREAKOUT_MAXDD_SIGMA_20 × EXTREME_TIME_ORDER（日内极值时序）。方向由发现期定。",
     "expected_sign": 1},
    {"id": "S35P3", "operator": "rank_spread", "left": _UWF, "right": _PV_ELASTICITY,
     "mechanism": "s35_p3", "hypothesis": "PRE_BREAKOUT_UNDERWATER_FRAC_20 × PV_ELASTICITY_20（S14，量价弹性）。方向由发现期定。",
     "expected_sign": 1},
    {"id": "S35P4", "operator": "rank_spread", "left": _UWF, "right": _HAR_RESID,
     "mechanism": "s35_p4", "hypothesis": "PRE_BREAKOUT_UNDERWATER_FRAC_20 × S28_VOV_HAR_RESID_20（S28）。方向由发现期定。",
     "expected_sign": 1},
    {"id": "S35P5", "operator": "rank_spread", "left": _RECOVERY, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s35_p5", "hypothesis": "POST_TROUGH_RECOVERY_20 × R_LOG_AMOUNT_VOL_20（S26R，触及后恢复是否与流动性水平共振）。方向由发现期定。",
     "expected_sign": 1},
    {"id": "S35P6", "operator": "rank_spread", "left": _RECOVERY, "right": _VT_GINI,
     "mechanism": "s35_p6", "hypothesis": "POST_TROUGH_RECOVERY_20 × VT_BUCKET_GINI_20（S24）。方向由发现期定。",
     "expected_sign": 1},
    {"id": "S35P7", "operator": "rank_spread", "left": _MAXDD_SIGMA_CHG, "right": _MFI_EXTREME,
     "mechanism": "s35_p7", "hypothesis": "PRE_BREAKOUT_MAXDD_SIGMA_CHG_20 × MFI_EXTREME_FRAC_20（S10，量能极值是否伴随忍耐力变化）。方向由发现期定。",
     "expected_sign": 1},
    {"id": "S35P8", "operator": "rank_spread", "left": _MAXDD_SIGMA_CHG, "right": _ON_SIGN_STREAK,
     "mechanism": "s35_p8", "hypothesis": "PRE_BREAKOUT_MAXDD_SIGMA_CHG_20 × ON_SIGN_STREAK_20（S21，隔夜方向连续性）。方向由发现期定。",
     "expected_sign": 1},
    {"id": "S35P9", "operator": "rank_spread", "left": _UWF_CHG, "right": _D1_LEVEL,
     "mechanism": "s35_p9", "hypothesis": "PRE_BREAKOUT_UNDERWATER_FRAC_CHG_20 × D1_LEVEL_60（S20，价格延迟）。方向由发现期定。",
     "expected_sign": 1},
    {"id": "S35P10", "operator": "rank_spread", "left": _UWF_CHG, "right": _R_ULCER,
     "mechanism": "s35_p10", "hypothesis": "PRE_BREAKOUT_UNDERWATER_FRAC_CHG_20 × R_ULCER_20（S26R，本轮末条）。方向由发现期定。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
