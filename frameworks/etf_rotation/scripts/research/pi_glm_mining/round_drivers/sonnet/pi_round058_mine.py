#!/usr/bin/env python3
"""Round 058 driver: stage 11 round 3 (AF6 admitted in r057, streak = 0).
Six NEW cross-family pairs from the 20-atom verified pool; all mechanism
names new; W3/Z1/7-atomic admitted vectors in the dedup reference set.
Gate 7 v2.1; atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_058"

base.CANDIDATES = [
    {
        "id": "AG1",
        "operator": "rank_spread",
        "left": {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"},
        "right": {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"},
        "mechanism": "bigbar_activity_profile_anomaly",
        "hypothesis": "两腿角色：A=大 bar 量占比（异常活动强度，r053 门 7 入选：+0.083/+0.055/t=2.92）；B=量分布距离（活动轮廓异常，r053 门 7 最强：+0.095/+0.044/t=4.04）。假设：高强度活动与轮廓异常并存（信号高）=事件驱动的定向活动（非噪声），延续；两者背离（信号低）=活动或轮廓由噪声主导。声明：BIGBAR_VOL_SHARE_20(AE1)第2次；VOL_PROFILE_DISTANCE(AE3)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AG2",
        "operator": "rank_spread",
        "left": {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"},
        "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"},
        "mechanism": "trend_gap_ushape_confirmed",
        "hypothesis": "两腿角色：A=缺口修复率 60 日（趋势持续强度，r053 门 7 入选：−0.060/−0.043/t=2.59）；B=日内 U 形 RV 占比（配置节律，r053 门 7 入选：−0.083/−0.089/t=2.12）。假设：缺口不修复（趋势持续）而 U 形节律存在（信号高）=配置节律确认趋势，延续；缺口快速修复（信号低）=趋势无节律支持。声明：GAP_FILL_FRACTION_60(AE4)第2次；VOL_USHAPE_20(AE2/AF1)第4次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AG3",
        "operator": "rank_spread",
        "left": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"},
        "mechanism": "spikes_with_directional_skew",
        "hypothesis": "两腿角色：A=量 spike 频率（事件密集度，BB1 左腿）；B=大 bar 方向偏度（大单方向一致性，Z2 左腿）。假设：spike 频繁且方向偏度明确（信号高）=密集事件有方向（知情执行），延续；spike 密集而无方向（信号低）=噪声爆发。声明：VOL_SPIKE_FREQ_20(BB1 左腿/AF5)第3次；BIGBAR_DIR_SKEW_20(Z2 左腿)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AG4",
        "operator": "rank_spread",
        "left": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "right": {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"},
        "mechanism": "calm_category_high_activity",
        "hypothesis": "两腿角色：A=类别 20 日波动（环境噪声，r053 门 7 入选：−0.071/−0.065/t=2.42）；B=对数成交额（活跃水平，T5 右腿）。假设：类别平静而活跃水平高（信号高）=平静环境中的高活跃（配置活跃而非投机），延续；类别高波动（信号低）=活跃是投机噪声。声明：CATEGORY_VOL_20(T4/Y3/N4/U2/AE3/AF4)第7次；LOG_AMOUNT_VOL_20(T5 右腿/AC6/AF6 入选)第4次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "AG5",
        "operator": "rank_spread",
        "left": {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"},
        "right": {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"},
        "mechanism": "persistent_volume_resilient",
        "hypothesis": "两腿角色：A=量自相关（量的持续性，Z2 右腿）；B=流动性回复力（冲击后 5 分钟回复，Kyle–Obizhaeva 2016 代理）。假设：量持续而回复力高（信号高）=持续活动落在深度流动性上（吸收良好），延续；回复力低（信号低）=持续活动造成持久冲击。声明：VOL_AUTOCORR_20(AE6)第3次；RESILIENCY_20(U5/V4/X4/AB3)第8次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "AG6",
        "operator": "rank_spread",
        "left": {"name": "WORST_DAY_20", "source": "return_tail_shape"},
        "right": {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "open_config_no_damage",
        "hypothesis": "两腿角色：A=最差单日收益（极端损伤，r053 门 7 入选：+0.064/+0.065/t=2.18）；B=开盘 30 分钟量占比（开盘配置机制，F1 右腿）。假设：最差单日不极端而开盘量占比高（信号高）=开盘配置机制运行且无极端损伤，延续；开盘占比低（信号低）=无配置锚点。声明：WORST_DAY_20(AE1/AF1)第3次；OPEN30_VOL_SHARE_20(F1 右腿/AF6 入选)第3次。预期正方向。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_stage11(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage11_verified_atom_pairing"
    plan["pairing_note"] = (
        "第 11 阶段：仅在已通过门 7 的原子与历史入选组合腿（共 20 原子）之间定向配对；"
        "REPORT 每条并列两腿单原子的门 7 数字与增量 = 组合 − max(两腿)；"
        "去重参照集含 9 组合 + 7 atomic 入选向量"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_stage11

if __name__ == "__main__":
    base.main()
