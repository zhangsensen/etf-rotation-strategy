#!/usr/bin/env python3
"""Round 164 driver: stage 34 — first-passage time structure of the 1m path
(no thresholds, no volume; sigma calibrated from prior 20d daily ret std).
Literature: Zumbach 2007; Cont 2001; Bollerslev-Todorov 2011.
8 clean atoms (health max corr 0.505, no shadows) + 11 pairs (volume-free
legs prioritized per directive). Pairing discipline: one batch per left leg."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_164"

FP = "first_passage_times_1m"
RP = "replication_volume_free_v1"
OS = "overnight_structure_1d"
DR = "downside_risk"
PL = "price_location"
SM = "scaling_memory_1m"
LC = "liquidity_commonality_1m"
BF = "bar_size_order_flow"
CD = "cost_distribution"
VF = "volume_free_path_v1"


def _atom(cid, name, mech, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": FP},
        "right": {"name": name, "source": FP},
        "mechanism": mech, "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp, sign=1):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": FP},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"fp_{left.lower()}", "hypothesis": hyp, "expected_sign": sign,
    }


CANDS = [
    # === 8 single atoms (first-passage structure) ===
    _atom("DB01", "FP_UP_20", "fp_time",
          "首触 +1σ 慢（bar 数大）= 上行犹豫 → 后续超额", -1),
    _atom("DB02", "FP_DOWN_20", "fp_time",
          "首触 −1σ 慢 = 下行抵抗 → 后续超额", 1),
    _atom("DB03", "FP_ASYM_20", "fp_asym",
          "上行先触早于下行（不对称负）= 买压 → 后续超额", 1),
    _atom("DB04", "FP_UP_FRAC_20", "fp_dir",
          "先触 +1σ 天数占比高 = 日内买方主导 → 后续超额", 1),
    _atom("DB05", "FP_FALSE_20", "fp_false",
          "假突破率高（触半σ回开盘）= 无趋势承接 → 反转", -1),
    _atom("DB06", "FP_CROSS_20", "fp_cross",
          "±1σ 穿越频繁 = 日内震荡 → 均值回复环境", -1),
    _atom("DB07", "FP_CHG_UP_20", "fp_regime",
          "上行首达时间近期变慢 = 动能衰减", -1),
    _atom("DB08", "FP_CHG_CROSS_20", "fp_regime",
          "穿越频率上升 = 震荡加剧 → 回复", -1),
    # === 11 pairs (volume-free legs prioritized) ===
    _pair("DB09", "FP_UP_20", "RP_UW_CHG_20", RP,
          "簇 FP_UP：上行首达慢 × 水下改善（双无量）", -1),
    _pair("DB10", "FP_UP_20", "ON_PREM_20", OS,
          "簇 FP_UP：上行首达慢 × 隔夜溢价", -1),
    _pair("DB11", "FP_UP_20", "CHIP_RANGE_90_60", CD,
          "簇 FP_UP：上行首达慢 × 筹码区间", -1),
    _pair("DB12", "FP_DOWN_20", "ULCER_20", DR,
          "簇 FP_DOWN：下行首达慢 × 溃疡低（健康回撤）", 1),
    _pair("DB13", "FP_DOWN_20", "PRICE_POSITION_20", PL,
          "簇 FP_DOWN：下行首达慢 × 价格位置高", 1),
    _pair("DB14", "FP_ASYM_20", "SCL_DFA_RET_20", SM,
          "簇 FP_ASYM：方向不对称 × 路径趋势度", 1),
    _pair("DB15", "FP_ASYM_20", "GAP_FILL_RATE_20", OS,
          "簇 FP_ASYM：方向不对称 × 跳空回补", 1),
    _pair("DB16", "FP_CROSS_20", "VFP_RECOVERY_20", VF,
          "簇 FP_CROSS：震荡 × 回撤恢复快", -1),
    _pair("DB17", "FP_CROSS_20", "RESILIENCY_20", LC,
          "簇 FP_CROSS：震荡 × 微结构弹性", -1),
    _pair("DB18", "FP_FALSE_20", "TICK_IMBALANCE_20", BF,
          "簇 FP_FALSE：假突破 × 主买不平衡", -1),
    _pair("DB19", "FP_UP_FRAC_20", "ULCER_20", DR,
          "簇 FP_UP_FRAC：买方主导 × 溃疡低", 1),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage34(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage34_first_passage_times"
    plan["family_note"] = (
        "第 34 阶段 first_passage_times_1m：无阈值无量，σ=前 20 日日收益 std 标定（Zumbach 2007/Cont 2001/"
        "Bollerslev-Todorov 2011）。8 原子体检全清洁（max 0.505 vs DOWNSIDE_UPSIDE_RATIO，无影子）。"
        "修复记录：FP_UP_FRAC 初版要求同日双触（覆盖 0.001，±1σ 双触仅 16/1607 天），改为至少一侧触及时按"
        "先触方向计数（覆盖 0.15），删缓存重建，PLAN 未锁前完成。8 单原子 + 11 配对 = 19；"
        "配对优先无量右腿（RP_UW_CHG/ON_PREM/GAP_FILL/ULCER/PRICE_POSITION/SCL_DFA/VFP_RECOVERY）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage34

if __name__ == "__main__":
    base.main()
