#!/usr/bin/env python3
"""Round 172 driver: stage 37 — mechanism atoms (Sonnet S27 insight: atomize
the mechanism implied by significant pairs). 6 singles + 12 pairs = 18."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_172"

MA = "mechanism_atoms_v1"


def _atom(cid, name, hyp, sign):
    return {
        "id": cid, "operator": "atomic",
        "left": {"name": name, "source": MA},
        "right": {"name": name, "source": MA},
        "mechanism": "mech_atom", "hypothesis": hyp, "expected_sign": sign,
    }


def _pair(cid, left, right, rsrc, hyp):
    return {
        "id": cid, "operator": "rank_spread",
        "left": {"name": left, "source": MA},
        "right": {"name": right, "source": rsrc},
        "mechanism": f"s37_{cid.lower()}", "hypothesis": hyp, "expected_sign": 1,
    }


CANDS = [
    _atom("MA06", "MA_VTAC_SPLIT", "量钟自相关在高/低活动日的差：活动驱动延续（CO36 机制化）。", 1),
    _atom("MA07", "MA_LUNCH_DIR_BET", "午后首 10 分钟抢跑量 × 日内方向符号：抢跑押对（CK04/CJ16 机制化）。", 1),
    _atom("MA08", "MA_PRERUN_TAIL_MATCH", "午前抢跑量 × 尾 5 分钟方向一致（CK04 机制化）。", 1),
    _atom("MA09", "MA_GAP_DD_EAT", "隔夜跳空被日内最大回撤吃掉比例截断[0,3]（CZ01/CY95 机制化；Sonnet GAP_DD_CONSUMPTION_RATIO 跨线复现）。", -1),
    _atom("MA10", "MA_OPEN_BUCKET_SHARE", "首 30 分钟成交量桶占比：开盘集中度（CR08 机制化）。", 1),
    _atom("MA11", "MA_HAR_ELAST_SPLIT", "HAR 意外日 vs 平常日的量价弹性差（CQ31 机制化）。", 1),
    _pair("MA12", "MA_VTAC_SPLIT", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m",
     "簇 MA_VTAC：量钟自相关活动分裂 × 事件密集。"),
    _pair("MA13", "MA_VTAC_SPLIT", "ON_PREM_20", "overnight_structure_1d",
     "簇 MA_VTAC：量钟自相关活动分裂 × 隔夜溢价。"),
    _pair("MA14", "MA_LUNCH_DIR_BET", "RESILIENCY_20", "liquidity_commonality_1m",
     "簇 MA_LUNCH_BET：抢跑押对 × 微结构弹性。"),
    _pair("MA15", "MA_LUNCH_DIR_BET", "SCL_DFA_RET_20", "scaling_memory_1m",
     "簇 MA_LUNCH_BET：抢跑押对 × 路径趋势。"),
    _pair("MA16", "MA_PRERUN_TAIL_MATCH", "TICK_IMBALANCE_20", "bar_size_order_flow",
     "簇 MA_PRERUN：午前抢跑一致 × 主买不平衡。"),
    _pair("MA17", "MA_PRERUN_TAIL_MATCH", "ON_SKEW_20", "overnight_structure_1d",
     "簇 MA_PRERUN：午前抢跑一致 × 隔夜偏度。"),
    _pair("MA18", "MA_GAP_DD_EAT", "RP_UW_CHG_20", "replication_volume_free_v1",
     "簇 MA_GAP_DD：跳空被吃 × 水下改善。"),
    _pair("MA19", "MA_GAP_DD_EAT", "PRICE_POSITION_20", "price_location",
     "簇 MA_GAP_DD：跳空被吃 × 价格位置。"),
    _pair("MA20", "MA_OPEN_BUCKET_SHARE", "PD_D1_CHG_20", "price_delay",
     "簇 MA_OPEN_BUCKET：开盘桶集中 × 延迟改善。"),
    _pair("MA21", "MA_OPEN_BUCKET_SHARE", "ULCER_20", "downside_risk",
     "簇 MA_OPEN_BUCKET：开盘桶集中 × 溃疡低。"),
    _pair("MA22", "MA_HAR_ELAST_SPLIT", "RCC_BB_SQUEEZE_20", "range_contraction_cycle",
     "簇 MA_HAR_ELAST：意外日弹性分裂 × squeeze。"),
    _pair("MA23", "MA_HAR_ELAST_SPLIT", "VFP_RECOVERY_20", "volume_free_path_v1",
     "簇 MA_HAR_ELAST：意外日弹性分裂 × 回撤恢复。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s37(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage37_mechanism_atoms"
    plan["family_note"] = (
        "第 37 阶段 mechanism_atoms_v1（Sonnet S27 启示：机制原子化）。6 原子来源：CO36→MA_VTAC_SPLIT、"
        "CK04/CJ16→MA_LUNCH_DIR_BET+MA_PRERUN_TAIL_MATCH、CZ01/CY95→MA_GAP_DD_EAT"
        "（GAP_DD_CONSUMPTION_RATIO 跨线复现）、CR08→MA_OPEN_BUCKET_SHARE、CQ31→MA_HAR_ELAST_SPLIT。"
        "体检 6/6 清洁（max 0.66）。6 单原子 + 12 确认腿配对 = 18。REPORT 对照单原子 vs 来源配对。"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s37

if __name__ == "__main__":
    base.main()
