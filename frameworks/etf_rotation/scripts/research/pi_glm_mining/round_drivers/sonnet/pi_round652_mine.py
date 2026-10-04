#!/usr/bin/env python3
"""Round 652 driver: S50 stage (main controller directive, 2026-09-21) --
precise-definition reproduction of pi lane's stage-37 mechanism atoms
and pairings (MA27/MA14/DD48/DD49). New family repl_pi37_core_v1 (2
atoms: R_LUNCH_DIR_BET_20, R_VFP_ULCER_SHIFT_20). Small-sample pilot (3
symbols) ran 4.8s; full 14-symbol build extrapolated ~22.5s, ran
directly. atom_health: R_LUNCH_DIR_BET_20 vs this line's own S30
PM_POSTRUN_DAY_CONSIST_20 corr=0.18 (genuinely different construct,
confirms directive's "not a substitute" claim); R_VFP_ULCER_SHIFT_20 vs
S12 ULCER_INDEX_CHG_20 corr=0.72 (>=0.7 shadow flag -- expected, both
measure drawdown-magnitude change, but base differs: fixed-open vs
running-peak; reported, not excluded).

Reproduction fixed set only (5 candidates, per directive; not a
15-30-condition mining batch -- same convention as S14/S26R/S26R2/S28/
S38/S45/S46)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_652"

_PERM_ENT = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_R_LUNCH_DIR_BET = {"name": "R_LUNCH_DIR_BET_20", "source": "repl_pi37_core_v1"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_R_VFP_ULCER_SHIFT = {"name": "R_VFP_ULCER_SHIFT_20", "source": "repl_pi37_core_v1"}
_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_LUNCH_PRE_RUN = {"name": "LUNCH_PRE_RUN_20", "source": "pi_lunch_prerun_1m"}

base.CANDIDATES = [
    {"id": "R_LUNCH_DIR_BET_20_A", "operator": "atomic", "left": _R_LUNCH_DIR_BET, "right": _R_LUNCH_DIR_BET,
     "mechanism": "s50_r_lunch_dir_bet_atomic",
     "hypothesis": "R_LUNCH_DIR_BET_20（午后13:00-13:10成交量占比×当日日内收益符号，pi 精确定义）单原子门7重裁，作为对照。"
                   "pi 侧该原子单原子未入选。体检 disc_ic=+0.008，与本线 PM_POSTRUN_DAY_CONSIST_20 corr=0.18（独立构造，非替代）。",
     "expected_sign": 1},
    {"id": "R_MA27", "operator": "rank_spread", "left": _PERM_ENT, "right": _R_LUNCH_DIR_BET,
     "mechanism": "s50_r_ma27",
     "hypothesis": "PERM_ENTROPY_RET_20 × R_LUNCH_DIR_BET_20，复现 pi 第37阶段 MA27。pi 主控数字：审计 +47.1bp / t 2.12。",
     "expected_sign": 1},
    {"id": "R_MA14", "operator": "rank_spread", "left": _R_LUNCH_DIR_BET, "right": _RESILIENCY,
     "mechanism": "s50_r_ma14",
     "hypothesis": "R_LUNCH_DIR_BET_20 × RESILIENCY_20，复现 pi 第37阶段 MA14（对照组，pi 数字弱）。pi：审计 +16.5bp / t 0.86。",
     "expected_sign": 1},
    {"id": "R_DD48", "operator": "rank_spread", "left": _R_VFP_ULCER_SHIFT, "right": _UF_CHG,
     "mechanism": "s50_r_dd48",
     "hypothesis": "R_VFP_ULCER_SHIFT_20（固定开盘基准溃疡指数变化）× UNDERWATER_FRAC_CHG_20，复现 pi 第37阶段 DD48。"
                   "pi 主控数字：审计 +64.0bp / t 3.64（pi 侧本阶段最强候选）。",
     "expected_sign": 1},
    # R_DD49 = rank(UNDERWATER_FRAC_CHG_20) - rank(LUNCH_PRE_RUN_20) 未加入本轮预注册：
    # 哈希与 round_641:S42P12（同表达式）完全一致，plan 阶段被引擎拒绝为重复候选，
    # 说明本线在 S42 阶段就已经测过这个精确组合（disc t=3.56/audit +34.0bp，
    # topk_gate 过但被 rank_correlation_redundancy 拒），REPORT 直接引用该历史结果
    # 作为 DD49 的复现对照，不重复预注册。
]

if __name__ == "__main__":
    base.main()
