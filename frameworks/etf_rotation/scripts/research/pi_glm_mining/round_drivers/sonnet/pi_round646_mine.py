#!/usr/bin/env python3
"""Round 646 driver: S46 stage (main controller directive, 2026-09-21) --
precise-definition reproduction of pi's CR08 and CM06 (the last two
two-window-significant pi candidates on this line's docket not yet
reproduced under pi's exact code-level formulas).

CR08 = rank(VT_BUCKET_COUNT_SHIFT_20) - rank(OPEN30_VOL_SHARE_20):
  this line's own S24 (round_603) implementation of VT_BUCKET_COUNT_SHIFT_20
  used a level-difference-of-smoothed-series formula (its own reasonable
  construction, not pi's exact one) and got discovery t=1.79, audit
  +44.3bp -- same sign as pi's +36.5bp/t2.02 but not a definition match.
  The S46 directive gives pi's precise formula (same-day ratio to a
  trailing baseline, THEN smoothed -- not smoothed-then-differenced),
  rebuilt fresh here as R2_VT_BUCKET_COUNT_SHIFT_20 in the new family
  repl_vt_bucket_precise_v1 (pure daily-panel arithmetic, no 1m re-read,
  no pilot needed). The right leg (OPEN30_VOL_SHARE_20) is reused as-is
  from S45's R2_OPEN30_VOL_SHARE_20 (repl_overnight_core_v2b), per the
  directive ("复用 S45 实现") -- rebuilding it a second time under the
  same formula would not test anything new.

CM06 = rank(LUNCH_GAP_20) - rank(AUC_VARIANCE_RATIO_20): the directive's
  precise definitions for both legs are byte-identical to atoms this
  line already built independently from literature (not from pi's code)
  in earlier stages -- LUNCH_GAP_20 (S22 lunch_break_1m, round_596+) and
  AUC_VARIANCE_RATIO_20 (S14 pi_auc_variance_ratio_1m, round_569).
  Rebuilding a third copy of either under an R2_ alias would be pure
  bookkeeping duplication (same code, same numbers) -- both are reused
  directly. LUNCH_GAP_20 was already atomically tested standalone in
  round_596 (KA1: audit -14.9bp/t0.85, rejected); AUC_VARIANCE_RATIO_20
  has never been tested atomically on its own, so that gap is filled
  here. This pairing (LUNCH_GAP_20 x AUC_VARIANCE_RATIO_20) has never
  been registered before (checked candidate_metrics.csv across all
  rounds)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_646"

_R2_VT_BUCKET = {"name": "R2_VT_BUCKET_COUNT_SHIFT_20", "source": "repl_vt_bucket_precise_v1"}
_R2_OPEN30_SHARE = {"name": "R2_OPEN30_VOL_SHARE_20", "source": "repl_overnight_core_v2b"}
_LUNCH_GAP = {"name": "LUNCH_GAP_20", "source": "lunch_break_1m"}
_AUC_RATIO = {"name": "AUC_VARIANCE_RATIO_20", "source": "pi_auc_variance_ratio_1m"}

base.CANDIDATES = [
    {"id": "S46A1", "operator": "atomic", "left": _R2_VT_BUCKET, "right": _R2_VT_BUCKET,
     "mechanism": "s46_vt_bucket_precise_atomic",
     "hypothesis": "R2_VT_BUCKET_COUNT_SHIFT_20（成交量时间桶数相对20日基线的同日比率、再20日平滑，pi 精确定义）单原子门7重裁，"
                   "作为 CR08 左腿重写质量检验；对照 S24 旧公式（20日均值之差）在 round_603 XA7 的结果 audit -43.65bp/disc_t 未过门。",
     "expected_sign": -1},
    {"id": "S46A2", "operator": "atomic", "left": _AUC_RATIO, "right": _AUC_RATIO,
     "mechanism": "s46_auc_variance_ratio_atomic",
     "hypothesis": "AUC_VARIANCE_RATIO_20（首30分钟/尾30分钟1m收益RV之比，S14 精确定义，此前只作为 DA57/CM06 的右腿用过，"
                   "从未单独门7重裁）首次单原子测试。",
     "expected_sign": 1},
    {"id": "R2_CR08", "operator": "rank_spread", "left": _R2_VT_BUCKET, "right": _R2_OPEN30_SHARE,
     "mechanism": "s46_r2_cr08",
     "hypothesis": "R2_VT_BUCKET_COUNT_SHIFT_20（pi 精确定义重写）× R2_OPEN30_VOL_SHARE_20（复用 S45 实现），复现 CR08。"
                   "pi 主控数字：审计 +36.5bp / t 2.02。本线 S24 旧公式版本（VT_BUCKET_COUNT_SHIFT_20 × OPEN30_VOL_SHARE_20，"
                   "round_603 XC1）：审计 +44.3bp / 发现 t 1.79，未过门。",
     "expected_sign": 1},
    {"id": "R2_CM06", "operator": "rank_spread", "left": _LUNCH_GAP, "right": _AUC_RATIO,
     "mechanism": "s46_r2_cm06",
     "hypothesis": "LUNCH_GAP_20（S22 精确定义，直接复用）× AUC_VARIANCE_RATIO_20（S14 精确定义，直接复用），复现 CM06。"
                   "pi 主控数字：审计 +34.9bp / t 1.98。两腿定义均与主控本轮给出的精确定义逐字一致，未曾以此组合配对过。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
