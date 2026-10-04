#!/usr/bin/env python3
"""Round 575 driver: S16 stage step 1 -- cross-stage top-atom pairwise
scan (CONTROLLER_DIRECTIVE.md, appended at round_575's request).

Screening (pi_round575_screen.py) pulled the highest-audit-t atom per
this line's admissions, <=3 per family, and computed a 12x12 rank-corr
matrix. RECURRENCE_RATE_20 (complexity_measures_1m) was dropped: it hit
|corr|>=0.7 against BOTH MFI_EXTREME_FRAC_20 (0.75, its own atom-health
generation cousin -- MFI decomposition and recurrence-rate both trace
autocorrelation structure in the same rank series) and
PERM_ENTROPY_RET_20 (-0.82, both are entropy/regularity measures of the
same return series at the same 20d window) -- dropping it clears both
conflicts. The remaining 11-atom pool has all pairwise |corr|<0.7 and
spans 9 distinct families (accumulation_distribution_1m x3,
complexity_measures_1m x1 after the drop, others x1 each).

Per the directive, this round tests the volume-free subset first: 7 of
the 11 atoms involve no 1m/daily volume in their construction
(UNDERWATER_FRAC_CHG_20 [S7, price-drawdown-path], PERM_ENTROPY_RET_20
[S6, return-entropy], CONTINUOUS_BETA_60 [S4, jump/continuous return
beta], NOISE_VAR_20 [S5, return-autocovariance microstructure noise],
YZ_OVERNIGHT_SHARE_20 [S9, OHLC-only Yang-Zhang decomposition],
MSPE_5M_20 [S11, return multiscale permutation entropy],
REL_MAXDD_CHG_20 [S15, active-return drawdown change]) -- the other 4
(MFI_EXTREME_FRAC_20, AD_PRICE_CORR_20, AD_NET_FLOW_SLOPE_20,
MFI_EXTREME_TOD_SKEW_20) all derive from money-flow/volume constructs
and are deferred to a later batch.

C(7,2)=21 cross-family pairs exist among the 7 volume-free atoms (all
pairs are cross-family since each atom is from a distinct family); none
of these specific atom x atom combinations have been tested as a pair
anywhere in this line's history (cross-checked against S1-S15's
admission/rejection records -- these are all first-time cross-stage
pairings). To respect the standing pairing-discipline rule (each
left-leg atom gets exactly one batch per stage; each right-leg atom
partners with <=3 different left legs), all 21 pairs are enumerated via
a rotational tournament on 7 vertices (offsets {1,2,3} mod 7): each atom
is a left leg exactly 3 times (batch size 3, well under the 8 cap) and a
right leg exactly 3 times (exactly at the 3-lefts-per-right cap) --
every unordered pair among the 7 appears exactly once, so no duplicate
canonical hashes are possible within this batch."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_575"

_UF_CHG = {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}
_PERM_ENT = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_CONT_BETA = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_YZ_OVN = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_MSPE5 = {"name": "MSPE_5M_20", "source": "complexity_measures_1m"}
_REL_MAXDD_CHG = {"name": "REL_MAXDD_CHG_20", "source": "relative_path_vs_basket_1m"}

ATOMS = [
    ("UA", _UF_CHG, "主动水下时长变化(S7 QA8, atomic t=2.88, 本线最高审计bp之一)"),
    ("UB", _PERM_ENT, "收益排列熵(S6 PA1, atomic t=2.09)"),
    ("UC", _CONT_BETA, "连续跳跃beta(S4, pairing t~2.15)"),
    ("UD", _NOISE_VAR, "微观结构噪声方差(S5, pairing t~2.2)"),
    ("UE", _YZ_OVN, "Yang-Zhang隔夜份额(S9 TB6, pairing t=3.53)"),
    ("UF", _MSPE5, "5分钟多尺度排列熵(S11 CA4, atomic t=3.15)"),
    ("UG", _REL_MAXDD_CHG, "主动最大回撤20日变化(S15 PB8, pairing t=2.85)"),
]

N = len(ATOMS)
CANDIDATES = []
for i in range(N):
    left_code, left_slot, left_desc = ATOMS[i]
    for offset in (1, 2, 3):
        j = (i + offset) % N
        right_code, right_slot, right_desc = ATOMS[j]
        cid = f"{left_code}{offset}"
        CANDIDATES.append({
            "id": cid,
            "operator": "rank_spread",
            "left": left_slot,
            "right": right_slot,
            "mechanism": f"s16_cross_stage_top_atom_{left_slot['name'].lower()}_x_{right_slot['name'].lower()}",
            "hypothesis": (
                f"S16跨阶段顶级原子互配扫描(volume-free子集,7原子环形锦标赛设计,"
                f"每原子左腿1批/右腿<=3次)。A={left_desc},来自{left_slot['source']}。"
                f"B={right_desc},来自{right_slot['source']}。两腿此前从未在本线配对过。"
                f"两腿均不含1m成交量/资金流构造。弱先验:两腿均为风险/不规则性上升型构造,"
                f"沿用本线S7/S15一贯的'确认型延续'框架(A高确认B高=延续,负相关);"
                f"这是系统性扫描而非逐对专门假设,符号由发现期实际确定,不符处如实标注。"
            ),
            "expected_sign": -1,
        })

base.CANDIDATES = CANDIDATES

if __name__ == "__main__":
    base.main()
