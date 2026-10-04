#!/usr/bin/env python3
"""Round 618 driver: S28 stage (only round) -- third-batch cross-line
reproduction of pi lane's remaining two-window-significant pairs.
Main controller's pre-specified S28 direction after S27's closure
(round_616) and S26R2's closure (round_617).

Reproduction discipline: both legs of each pair independently built
from the directive's literature/formula definitions, no reading of pi
workspace code. 4 of the 6 legs reuse atoms this line already built
independently in earlier stages (documented in pi_repl_s28.py's
module docstring): LUNCH_GAP_20/LUNCH_POST_RUN_20 (S22
lunch_break_1m), R_ULCER_20/R_LOG_AMOUNT_VOL_20 (S26R
repl_volume_core_a/b), VT_BUCKET_GINI_20 (S24 volume_time_1m),
PD_D1_CHG_20 (S14 pi_price_delay_1d -- price_delay.py's own docstring
documents this atom as "reused as-is, not rebuilt" for S20, so it is
reused a second time here rather than rebuilt a third time), and
PV_ELASTICITY_20 (S14 pi_pv_elasticity_1m). Only S28_PRICE_POSITION_20
and S28_VOV_HAR_RESID_20 are newly built (pi_repl_s28.py, round_618).

Atom health (round_618_atom_health): S28_PRICE_POSITION_20 disc_ic
0.012/audit_ic 0.028 (579 disc days, 23121 finite); S28_VOV_HAR_RESID_20
disc_ic -0.020/audit_ic 0.007 (579 disc days, 22241 finite). Both build
cleanly, no NaN collapse.

6 pair reproductions, no atomic-only candidates (S28 directive lists
pairs only)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_618"

_LUNCH_POST_RUN = {"name": "LUNCH_POST_RUN_20", "source": "lunch_break_1m"}
_LUNCH_GAP = {"name": "LUNCH_GAP_20", "source": "lunch_break_1m"}
_R_LOG_AMOUNT_VOL = {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}
_R_ULCER = {"name": "R_ULCER_20", "source": "repl_volume_core_b"}
_VT_BUCKET_GINI = {"name": "VT_BUCKET_GINI_20", "source": "volume_time_1m"}
_VOV_HAR_RESID = {"name": "S28_VOV_HAR_RESID_20", "source": "pi_repl_s28"}
_PV_ELASTICITY = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}
_PD_D1_CHG = {"name": "PD_D1_CHG_20", "source": "pi_price_delay_1d"}
_PRICE_POSITION = {"name": "S28_PRICE_POSITION_20", "source": "pi_repl_s28"}

base.CANDIDATES = [
    {"id": "S28CJ16", "operator": "rank_spread", "left": _LUNCH_POST_RUN, "right": _R_LOG_AMOUNT_VOL,
     "mechanism": "s28_cj16",
     "hypothesis": "复现 pi CJ16 = rank(LUNCH_POST_RUN_20) − rank(LOG_AMOUNT_VOL_20)。左腿复用 S22 lunch_break_1m 的 LUNCH_POST_RUN_20（13:00–13:10 成交量占全日比例 20 日均值），右腿复用 S26R 的 R_LOG_AMOUNT_VOL_20（log 日成交额 20 日标准差）。pi 主控验证 +42.3 / t 2.30。",
     "expected_sign": -1},
    {"id": "S28CK20", "operator": "rank_spread", "left": _LUNCH_GAP, "right": _R_ULCER,
     "mechanism": "s28_ck20",
     "hypothesis": "复现 pi CK20 = rank(LUNCH_GAP_20) − rank(ULCER_20)。左腿复用 S22 的 LUNCH_GAP_20（午间跳空 20 日均值），右腿复用 S26R 的 R_ULCER_20（20 日收盘价溃疡指数）。pi：+38.8 / t 1.99。",
     "expected_sign": -1},
    {"id": "S28CN08", "operator": "rank_spread", "left": _LUNCH_GAP, "right": _VT_BUCKET_GINI,
     "mechanism": "s28_cn08",
     "hypothesis": "复现 pi CN08 = rank(LUNCH_GAP_20) − rank(VT_BUCKET_GINI_20)。左腿同上，右腿复用 S24 volume_time_1m 的 VT_BUCKET_GINI_20（成交量时间桶间隔时长 Gini）。pi：+30.1 / t 2.17。",
     "expected_sign": -1},
    {"id": "S28CQ31", "operator": "rank_spread", "left": _VOV_HAR_RESID, "right": _PV_ELASTICITY,
     "mechanism": "s28_cq31",
     "hypothesis": "复现 pi CQ31 = rank(VOV_HAR_RESID_20) − rank(PV_ELASTICITY_20)。左腿为本轮新建 S28_VOV_HAR_RESID_20（Corsi 2009 HAR-RV 60 日滚动回归当日残差 20 日均值），右腿复用 S14 pi_pv_elasticity_1m 的 PV_ELASTICITY_20（日内 |收益| 对 log 成交量回归斜率 20 日均值）。pi：+35.9 / t 2.03。",
     "expected_sign": -1},
    {"id": "S28CZ60", "operator": "rank_spread", "left": _VT_BUCKET_GINI, "right": _PD_D1_CHG,
     "mechanism": "s28_cz60",
     "hypothesis": "复现 pi CZ60 = rank(VT_BUCKET_GINI_20) − rank(PD_D1_CHG_20)。左腿同上，右腿复用 S14 pi_price_delay_1d 的 PD_D1_CHG_20（price_delay.py 自身文档已确认该原子'复用不重建'用于 S20）。pi：+55.7 / t 2.72；主控预计不成立，作对照。",
     "expected_sign": 1},
    {"id": "S28CO09", "operator": "rank_spread", "left": _VT_BUCKET_GINI, "right": _PRICE_POSITION,
     "mechanism": "s28_co09",
     "hypothesis": "复现 pi CO09 = rank(VT_BUCKET_GINI_20) − rank(PRICE_POSITION_20)。左腿同上，右腿为本轮新建 S28_PRICE_POSITION_20（Stochastic %K 式 20 日高低价位置）。pi：+25.6 / t 1.27（过门不显著，作幅度对照）。本轮末条。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
