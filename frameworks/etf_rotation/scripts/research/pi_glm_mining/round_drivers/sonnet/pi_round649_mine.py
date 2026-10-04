#!/usr/bin/env python3
"""Round 649 driver: S48 stage (main controller directive, 2026-09-21) --
overnight behavior x intraday drawdown written directly as a rolling
covariation statistic. New family overnight_underwater_covariance (6
atoms). Small-sample pilot (3 symbols) ran 8.24s; full 14-symbol build
extrapolated ~38.5s, ran directly. atom_health: no shadow flags (max
|corr| vs reference atoms = 0.20).

This round combines atomic tests + first pairing batch (per the
standing one-round convention): 6 atomic candidates (S48A1-6) + 3 left
legs (the two atoms slated for CHG companions plus GAP_SIGMA_MAXDD -
these three are the directive's primary targets) x 7 already-validated
cross-family right legs = 21 pairing candidates, total 27, within the
15-30 band."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_649"

_L_SPEARMAN = {"name": "OVERNIGHT_UNDERWATER_SPEARMAN_20", "source": "overnight_underwater_covariance"}
_L_SIGNCHG = {"name": "OVERNIGHT_SIGN_UNDERWATERCHG_CORR_20", "source": "overnight_underwater_covariance"}
_L_VARSHARE = {"name": "OVERNIGHT_VARSHARE_UNDERWATER_CORR_60", "source": "overnight_underwater_covariance"}
_L_GAPSIGMA = {"name": "GAP_SIGMA_MAXDD_SIGMA_CORR_20", "source": "overnight_underwater_covariance"}
_L_SPEARMAN_CHG = {"name": "OVERNIGHT_UNDERWATER_SPEARMAN_CHG_20", "source": "overnight_underwater_covariance"}
_L_VARSHARE_CHG = {"name": "OVERNIGHT_VARSHARE_UNDERWATER_CORR_CHG_20", "source": "overnight_underwater_covariance"}

_MFI_EXT = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_BIGBAR = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_PERM_ENT = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_VT_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_ON_STREAK = {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"}

_RIGHT_POOL = [
    ("MFIEXT", _MFI_EXT),
    ("CBETA60", _CBETA60),
    ("BIGBAR", _BIGBAR),
    ("PERMENT", _PERM_ENT),
    ("SAMPEN", _SAMPEN),
    ("VTGINI", _VT_GINI),
    ("ONSTREAK", _ON_STREAK),
]

base.CANDIDATES = [
    {"id": "S48A1", "operator": "atomic", "left": _L_SPEARMAN, "right": _L_SPEARMAN,
     "mechanism": "s48_overnight_underwater_spearman_atomic",
     "hypothesis": "隔夜收益与当日原始水下占比的20日滚动Spearman相关，单原子门7重裁。"
                   "体检 disc_ic=+0.020，与参照原子最大corr=0.06（独立）。",
     "expected_sign": 1},
    {"id": "S48A2", "operator": "atomic", "left": _L_SIGNCHG, "right": _L_SIGNCHG,
     "mechanism": "s48_overnight_sign_underwaterchg_atomic",
     "hypothesis": "隔夜收益符号与当日水下占比变化的20日滚动相关，单原子门7重裁。体检 disc_ic=-0.010。",
     "expected_sign": -1},
    {"id": "S48A3", "operator": "atomic", "left": _L_VARSHARE, "right": _L_VARSHARE,
     "mechanism": "s48_overnight_varshare_underwater_atomic",
     "hypothesis": "隔夜方差占比(Yang-Zhang)与原始水下占比的60日滚动相关，单原子门7重裁。体检 disc_ic=+0.040（本族最强单原子）。",
     "expected_sign": 1},
    {"id": "S48A4", "operator": "atomic", "left": _L_GAPSIGMA, "right": _L_GAPSIGMA,
     "mechanism": "s48_gap_sigma_maxdd_sigma_atomic",
     "hypothesis": "标准化隔夜跳空幅度与标准化日内最大回撤的20日滚动相关，单原子门7重裁。体检 disc_ic=+0.004。",
     "expected_sign": 1},
    {"id": "S48A5", "operator": "atomic", "left": _L_SPEARMAN_CHG, "right": _L_SPEARMAN_CHG,
     "mechanism": "s48_overnight_underwater_spearman_chg_atomic",
     "hypothesis": "S48A1 的 20 日变化，单原子门7重裁。", "expected_sign": -1},
    {"id": "S48A6", "operator": "atomic", "left": _L_VARSHARE_CHG, "right": _L_VARSHARE_CHG,
     "mechanism": "s48_overnight_varshare_underwater_chg_atomic",
     "hypothesis": "S48A3 的 20 日变化，单原子门7重裁。", "expected_sign": -1},
]

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S48B{i}", "operator": "rank_spread", "left": _L_SPEARMAN, "right": right,
        "mechanism": f"s48_overnight_underwater_spearman_x_{tag.lower()}",
        "hypothesis": f"OVERNIGHT_UNDERWATER_SPEARMAN_20 × {right['name']}，配对纪律首批。",
        "expected_sign": 1,
    })

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S48C{i}", "operator": "rank_spread", "left": _L_VARSHARE, "right": right,
        "mechanism": f"s48_overnight_varshare_underwater_x_{tag.lower()}",
        "hypothesis": f"OVERNIGHT_VARSHARE_UNDERWATER_CORR_60 × {right['name']}，配对纪律首批。",
        "expected_sign": 1,
    })

for i, (tag, right) in enumerate(_RIGHT_POOL, start=1):
    base.CANDIDATES.append({
        "id": f"S48D{i}", "operator": "rank_spread", "left": _L_GAPSIGMA, "right": right,
        "mechanism": f"s48_gap_sigma_maxdd_sigma_x_{tag.lower()}",
        "hypothesis": f"GAP_SIGMA_MAXDD_SIGMA_CORR_20 × {right['name']}，配对纪律首批。",
        "expected_sign": 1,
    })

if __name__ == "__main__":
    base.main()
