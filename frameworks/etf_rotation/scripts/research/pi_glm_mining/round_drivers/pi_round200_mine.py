#!/usr/bin/env python3
"""Round 200 driver: stage 57 — 1m cost distribution / capital gains overhang
(cost_distribution_1m, Grinblatt–Han 2005), 6 atoms + 16 pairs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_200"

CD = "cost_distribution_1m"


def _atom(cid, name, sign, hyp):
    return {"id": cid, "operator": "atomic",
            "left": {"name": name, "source": CD},
            "right": {"name": name, "source": CD},
            "mechanism": f"s57_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


def _pair(cid, left, right, rsrc, sign, hyp):
    return {"id": cid, "operator": "rank_spread",
            "left": {"name": left, "source": CD},
            "right": {"name": right, "source": rsrc},
            "mechanism": f"s57_{cid.lower()}", "hypothesis": hyp, "expected_sign": sign}


CANDS = [
    _atom("CDA", "CGO_20", 1,
     "资本利得悬垂 20 日：处置效应下高未实现盈利 → 抛压被消化后延续（Grinblatt–Han 2005；Frazzini 2006）。"),
    _atom("CDB", "CGO_60", 1,
     "资本利得悬垂 60 日（GHN 递推，换手=日量/60 日均量）。"),
    _atom("CDC", "UW_VOL_SHARE_60", -1,
     "被套体量占比 60 日：存活成交量中成本高于现价的比例，越高越弱。"),
    _atom("CDE", "COST_CONC_60", 1,
     "成本分布 Herfindahl（20 等宽价格档）：成本集中=关键价位支撑清晰。"),
    _atom("CDF", "MODE_DIST_60", -1,
     "现价相对成本众数档的偏离：负=下方套牢盘密集。"),
    _atom("CDG", "COST_SKEW_60", 1,
     "成本分布偏度：右偏=低成本筹码多、上方抛压轻。"),

    _pair("CDP1", "CGO_20", "RP_UW_CHG_20", "replication_volume_free_v1", 1,
     "成本悬垂 × 水下改善（QA8 同右腿；成本机制 vs 路径机制）。"),
    _pair("CDP2", "CGO_20", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", 1,
     "成本悬垂 × 量事件密集（BB1 同右腿）。"),
    _pair("CDP3", "CGO_20", "MA_LUNCH_DIR_BET", "mechanism_atoms_v1", 1,
     "成本悬垂 × 午后押对。"),
    _pair("CDP4", "CGO_60", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", 1,
     "60 日成本悬垂 × 量事件。"),
    _pair("CDP5", "CGO_60", "R_GAP_DD_CONSUMPTION_20", "sonnet_repl_r2_gapdd", -1,
     "成本悬垂 × 跳空被吃低（S27B5 左腿）。"),
    _pair("CDP6", "CGO_60", "LOG_AMOUNT_VOL_20", "liquidity_variability", -1,
     "成本悬垂 × 规模小（S32P1 模式）。"),
    _pair("CDP7", "UW_VOL_SHARE_60", "RP_UW_CHG_20", "replication_volume_free_v1", -1,
     "被套体量 × 水下改善。"),
    _pair("CDP8", "UW_VOL_SHARE_60", "VT_AUTOCORR_20", "volume_time_1m", -1,
     "被套体量 × 量钟自相关低（CO36 左腿）。"),
    _pair("CDP9", "UW_VOL_SHARE_60", "ON_PREM_20", "overnight_structure_1d", -1,
     "被套体量 × 隔夜溢价低。"),
    _pair("CDP10", "COST_CONC_60", "RP_PERM_ENT_D3_20", "replication_volume_free_v1", -1,
     "成本集中 × 排列熵低（PA1 右腿）。"),
    _pair("CDP11", "COST_CONC_60", "R_MFI_EXTREME_FRAC_20", "sonnet_repl_r2_mfi", -1,
     "成本集中 × MFI 极值低。"),
    _pair("CDP12", "MODE_DIST_60", "RP_UW_CHG_20", "replication_volume_free_v1", -1,
     "众数距离负（下方成本密集）× 水下改善。"),
    _pair("CDP13", "MODE_DIST_60", "VOL_SPIKE_FREQ_20", "intraday_volume_profile_1m", -1,
     "众数距离负 × 量事件低。"),
    _pair("CDP14", "COST_SKEW_60", "CLOSE5_DAY_CONSIST_20", "bar_size_order_flow", 1,
     "成本右偏 × 尾盘一致（CK04 同右腿）。"),
    _pair("CDP15", "COST_SKEW_60", "R_ON_SIGN_STREAK_20", "sonnet_repl_r2_misc", 1,
     "成本右偏 × 隔夜符号连续（HB1 右腿）。"),
]

base.CANDIDATES = CANDS

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_s57(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage57_cost_distribution_1m"
    plan["family_note"] = (
        "第 57 阶段：1m 成本分布/资本利得悬垂（cost_distribution_1m，Grinblatt–Han 2005，"
        "GHN 递推换手代理=日量/60 日均量），6 原子 + 16 配对。")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_s57

if __name__ == "__main__":
    base.main()
