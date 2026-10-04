#!/usr/bin/env python3
"""Round 184 driver: stage 46 — relative-category underwater-change single
re-adjudication + threshold-free variants (rel_category_v1, 4 atoms).
4 singles + 12 confirmed-leg pairs = 16. Consistency: r184 impl vs r180 impl
corr 1.000; vs RP_UW_CHG_20 corr 0.46 (different cluster)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_184"

RC = "rel_category_v1"


def _atom(cid, name, hyp):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": RC},
        "right": {"name": name, "source": RC},
        "mechanism": "rel_cat_chg", "hypothesis": hyp, "expected_sign": 1,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": RC},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"s46_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _atom("TF01", "R_REL_UW_CATEGORY_CHG_20",
     "类内相对水下占比 20 日变化单独重裁（第 43 阶段 R_S32P1 左腿首次单裁）。"),
    _atom("TF02", "R_REL_ULCER_CHG_20",
     "类内相对溃疡指数 20 日变化（Martin–McCann 1989；类别减法 S32 机制变体）。"),
    _atom("TF03", "R_REL_RECOVERY_CHG_20",
     "类内相对回撤恢复时间占比 20 日变化（Magdon-Ismail–Atiya 2004；机制变体）。"),
    _atom("TF04", "R_REL_UW_BASKET_CHG_20",
     "相对全篮子（14 等权）水下占比 20 日变化——S15 对照，只验证一次。"),
    _pair("TF05", "R_REL_UW_CATEGORY_CHG_20", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m",
     "簇 REL_UW_CHG：类内水下变化 × 事件密集。"),
    _pair("TF06", "R_REL_UW_CATEGORY_CHG_20", "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi",
     "簇 REL_UW_CHG：类内水下变化 × MFI 极端。"),
    _pair("TF07", "R_REL_UW_CATEGORY_CHG_20", "MA_GAP_DD_EAT", "mechanism_atoms_v1",
     "簇 REL_UW_CHG：类内水下变化 × 跳空被吃比例。"),
    _pair("TF08", "R_REL_ULCER_CHG_20", "ON_PREM_20", "overnight_structure_1d",
     "簇 REL_ULCER：类内溃疡变化 × 隔夜溢价。"),
    _pair("TF09", "R_REL_ULCER_CHG_20", "SCL_DFA_RET_20", "scaling_memory_1m",
     "簇 REL_ULCER：类内溃疡变化 × 路径趋势。"),
    _pair("TF10", "R_REL_ULCER_CHG_20", "ULCER_20", "downside_risk",
     "簇 REL_ULCER：类内溃疡变化 × 绝对溃疡。"),
    _pair("TF11", "R_REL_RECOVERY_CHG_20", "RP_PERM_ENT_D3_20", "replication_volume_free_v1",
     "簇 REL_RECOVERY：类内恢复变化 × 排列熵。"),
    _pair("TF12", "R_REL_RECOVERY_CHG_20", "TICK_IMBALANCE_20", "bar_size_order_flow",
     "簇 REL_RECOVERY：类内恢复变化 × 主买不平衡。"),
    _pair("TF13", "R_REL_RECOVERY_CHG_20", "PRICE_POSITION_20", "price_location",
     "簇 REL_RECOVERY：类内恢复变化 × 价格位置。"),
    _pair("TF14", "R_REL_UW_BASKET_CHG_20", "RESILIENCY_20", "liquidity_commonality_1m",
     "簇 UW_BASKET：篮子相对水下变化 × 微结构弹性。"),
    _pair("TF15", "R_REL_UW_BASKET_CHG_20", "RCC_BB_SQUEEZE_20", "range_contraction_cycle",
     "簇 UW_BASKET：篮子相对水下变化 × squeeze。"),
    _pair("TF16", "R_REL_UW_BASKET_CHG_20", "AUC_VARIANCE_RATIO_20", "auction_1m",
     "簇 UW_BASKET：篮子相对水下变化 × 开盘方差比。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s46(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage46_rel_category"
    plan["family_note"] = (
        "第 46 阶段 rel_category_v1（≤4 原子无阈值；S32 机制加深）。"
        "一致性核验：R_REL_UW_CATEGORY_CHG 本实现 vs r180 实现 corr 1.000；vs RP_UW_CHG_20 corr 0.46（不同簇）。"
        "TF04 为相对全篮子对照（S15 只验一次）。4 单原子 + 12 配对 = 16。"
        "REPORT 单列「相对类别 vs 绝对 vs 相对篮子」三栏对照。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s46

if __name__ == "__main__":
    base.main()
