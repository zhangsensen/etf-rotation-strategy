#!/usr/bin/env python3
"""Round 647 driver: S47 stage (main controller directive, 2026-09-21) --
fifth mechanism-atom batch, sourced from the head of S44's
REJECTED_H20_PROFILE list (H=5-gate rejects that are two-window
significant at H=20, both legs volume-free, independent of already-
admitted clusters): PH1 (round_543, H20 audit t=4.83), BA7 (round_584,
H20 audit t=4.70), S30Q5 (round_628, H20 audit t=4.34). New family
mechanism_atoms_v4 (5 atoms: 3 base conditional-split statistics + 20d
CHG companions for the strongest 2 by H20 audit-t, per directive).

Small-sample pilot (3 symbols) ran 82.9s; full 14-symbol run
extrapolated to ~6.5 minutes (83s * 14/3), under the 10-minute
threshold -- ran directly in foreground, no nohup needed. The cost
driver is resolve_family() re-triggering full 1m rebuilds of
permutation_entropy_1m / complexity_measures_1m for the reused legs
(SampEn/ApEn-style per-day loops), not this module's own lightweight
close5_ret extraction.

This round combines atomic tests + first pairing batch in one round
(per the standing "connect atom_health -> validate -> atomic -> first
pairing batch in one round" convention, same as S27's round_614): 5
atomic candidates (S47A1-5) + 3 left legs (the base atoms only, not the
CHG companions -- pairing discipline reserves one batch per left leg
per stage, and the 3 base statistics are the directive's primary
targets) x 7 already-validated cross-family right legs = 21 pairing
candidates (S47B/C/D 1-7), total 26, within the 15-30 band. The same 7
right legs are reused across all 3 left legs (each right leg thus used
exactly 3 times, at the pairing-discipline cap)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_647"

_L1 = {"name": "CLOSE5_CONSIST_PERMENT_SPLIT_20", "source": "mechanism_atoms_v4"}
_L2 = {"name": "BBWIDTH_CHG_SAMPEN_SPLIT_20", "source": "mechanism_atoms_v4"}
_L3 = {"name": "OVERNIGHT_SHARE_PMCONSIST_SPLIT_20", "source": "mechanism_atoms_v4"}
_L1CHG = {"name": "CLOSE5_CONSIST_PERMENT_SPLIT_CHG_20", "source": "mechanism_atoms_v4"}
_L2CHG = {"name": "BBWIDTH_CHG_SAMPEN_SPLIT_CHG_20", "source": "mechanism_atoms_v4"}

_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_GAP_DD = {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"}
_MFI_EXT = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_BIGBAR = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_GAPMEAN = {"name": "GAP_MEAN_20", "source": "daily_candle"}
_FPUPCHG = {"name": "FIRST_PASSAGE_UP_CHG_20", "source": "first_passage_times_1m"}

_RIGHT_POOL = [
    ("UF_CHG", _UF_CHG),
    ("GAP_DD", _GAP_DD),
    ("MFI_EXT", _MFI_EXT),
    ("CBETA60", _CBETA60),
    ("BIGBAR", _BIGBAR),
    ("GAPMEAN", _GAPMEAN),
    ("FPUPCHG", _FPUPCHG),
]

base.CANDIDATES = [
    {"id": "S47A1", "operator": "atomic", "left": _L1, "right": _L1,
     "mechanism": "s47_close5_permentropy_split_atomic",
     "hypothesis": "尾5分钟方向与全日方向一致日 vs 不一致日的排列熵之差（源自 PH1，H20 discovery t=4.15/audit t=4.83，"
                   "本条测试该机制在现行 H=5 门下是否也站得住）单原子门7重裁。",
     "expected_sign": 1},
    {"id": "S47A2", "operator": "atomic", "left": _L2, "right": _L2,
     "mechanism": "s47_bbwidth_sampen_split_atomic",
     "hypothesis": "带宽收缩日 vs 扩张日的样本熵之差（源自 BA7，H20 discovery t=3.19/audit t=4.70）单原子门7重裁。",
     "expected_sign": -1},
    {"id": "S47A3", "operator": "atomic", "left": _L3, "right": _L3,
     "mechanism": "s47_overnight_pmconsist_split_atomic",
     "hypothesis": "隔夜方差占比高日 vs 低日的午后抢跑方向一致率之差（源自 S30Q5，H20 discovery t=2.50/audit t=4.34）单原子门7重裁。",
     "expected_sign": 1},
    {"id": "S47A4", "operator": "atomic", "left": _L1CHG, "right": _L1CHG,
     "mechanism": "s47_close5_permentropy_split_chg_atomic",
     "hypothesis": "S47A1 的 20 日变化，单原子门7重裁（H20 audit t 最高的两条之一，按指令附带 CHG 版本）。",
     "expected_sign": 1},
    {"id": "S47A5", "operator": "atomic", "left": _L2CHG, "right": _L2CHG,
     "mechanism": "s47_bbwidth_sampen_split_chg_atomic",
     "hypothesis": "S47A2 的 20 日变化，单原子门7重裁。",
     "expected_sign": -1},
]

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S47B{i}", "operator": "rank_spread", "left": _L1, "right": right,
        "mechanism": f"s47_close5_permentropy_split_x_{tag.lower()}",
        "hypothesis": f"CLOSE5_CONSIST_PERMENT_SPLIT_20（PH1 机制原子）× {right['name']}，配对纪律首批（{tag} 右腿）。",
        "expected_sign": 1,
    })

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S47C{i}", "operator": "rank_spread", "left": _L2, "right": right,
        "mechanism": f"s47_bbwidth_sampen_split_x_{tag.lower()}",
        "hypothesis": f"BBWIDTH_CHG_SAMPEN_SPLIT_20（BA7 机制原子）× {right['name']}，配对纪律首批（{tag} 右腿）。",
        "expected_sign": 1,
    })

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S47D{i}", "operator": "rank_spread", "left": _L3, "right": right,
        "mechanism": f"s47_overnight_pmconsist_split_x_{tag.lower()}",
        "hypothesis": f"OVERNIGHT_SHARE_PMCONSIST_SPLIT_20（S30Q5 机制原子）× {right['name']}，配对纪律首批（{tag} 右腿）。",
        "expected_sign": 1,
    })

if __name__ == "__main__":
    base.main()
