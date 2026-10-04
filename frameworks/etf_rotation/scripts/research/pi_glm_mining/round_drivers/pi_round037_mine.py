#!/usr/bin/env python3
"""Round 037 driver: stage-6 round 3. Entering streak: 2 consecutive gate-7
zero rounds (r035, r036) — a third zero round triggers contract exhaustion.
Six rank_spread pairs, each with >=1 microstructure_1m/benchmark_leadlag_1m
leg (second/third deployment of those legs, all pairs atom-level new, all
mechanism names new). Gate 7 v2.1; all atoms leak-cached."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_037"

base.CANDIDATES = [
    {
        "id": "K1",
        "operator": "rank_spread",
        "left": {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"},
        "right": {"name": "PRIMARY_SHARE_20", "source": "fund_flow"},
        "mechanism": "vpin_secondary_informed",
        "hypothesis": "两腿角色：A=VPIN（知情交易概率，Easley–López de Prado–O'Hara 2012）；B=一级市场量占比（申赎套利盘）。假设：VPIN 高而一级占比低（信号高）=知情交易发生在二级（方向性吸筹），延续；一级占比高（信号低）=知情沿一级套利实现，二级 VPIN 被申赎噪声稀释。声明：VPIN_CLOSE_20(N1-035)第2次；PRIMARY_SHARE_20(Y6/X4/M4)第3次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "K2",
        "operator": "rank_spread",
        "left": {"name": "ROLL_SPREAD_20", "source": "microstructure_1m"},
        "right": {"name": "PREMIUM_Z_20", "source": "nav_premium"},
        "mechanism": "low_friction_no_overhang",
        "hypothesis": "两腿角色：A=Roll 隐性价差（交易摩擦，Roll 1984）；B=折溢价 20 日 z（情绪透支度）。假设：摩擦小而溢价 z 低（信号高）=低成本且无透支的干净环境，配置流入不付摩擦不接情绪，延续；高摩擦或高溢价（信号低）=成本/透支吞噬回报。声明：ROLL_SPREAD_20(N3-035)第2次；PREMIUM_Z_20(N5-035)第2次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "K3",
        "operator": "rank_spread",
        "left": {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"},
        "right": {"name": "STREAK_DAYS", "source": "fund_flow"},
        "mechanism": "impactful_primary_inflow",
        "hypothesis": "两腿角色：A=Kyle λ 代理（单位净流价格冲击，Kyle 1985/Hasbrouck 2009）；B=连续净申购天数（一级承接方向）。假设：λ 高且连续净申购（信号高）=持续一级流入撞上高冲击系数，流量真实推动价格，延续；连续净赎回（信号低）=高冲击下的流出放大失血。声明：KYLE_LAMBDA_20(N2-035)第2次；STREAK_DAYS(T5/N3)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "K4",
        "operator": "rank_spread",
        "left": {"name": "IMPACT_ASYM_20", "source": "microstructure_1m"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "buy_impact_secondary_origin",
        "hypothesis": "两腿角色：A=买卖 bar 冲击非对称（买侧 |Δp|/量 优势）；B=份额变化-收益相关（一级流解释力）。假设：买侧冲击强而一级流不解释价格（信号高）=买方冲击源于二级知情买盘，延续；一级解释力强（信号低）=冲击是申赎的机械映射，无信息。声明：IMPACT_ASYM_20(N4-035)第2次；SHARE_RET_CORR_20(X6/M1)第3次。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "K5",
        "operator": "rank_spread",
        "left": {"name": "LAG1_BENCH_CORR_20", "source": "benchmark_leadlag_1m"},
        "right": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "intraday_natural_lag",
        "hypothesis": "两腿角色：A=对基准的滞后 1 拍相关（价格发现滞后，Lo–MacKinlay 1990 式）；B=尾 30 分钟量占比（收盘标记型参与）。假设：滞后相关高而尾盘集中低（信号高）=滞后发生在盘中自然交易时段（信息传导延迟），基准延续时补涨；尾盘集中高（信号低）=滞后是收盘标记噪声。声明：LAG1_BENCH_CORR_20(N5-035)第2次；CLOSE30_VOL_SHARE_20(N2-035)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "K6",
        "operator": "rank_spread",
        "left": {"name": "OFI_AUTOCORR_20", "source": "microstructure_1m"},
        "right": {"name": "ULCER_60", "source": "downside_risk"},
        "mechanism": "persistent_flow_healthy_structure",
        "hypothesis": "两腿角色：A=订单流不平衡持续性（Cont–Kukanov–Stoikov 2014）；B=60 日溃疡指数（慢性失血）。假设：订单流持续而溃疡浅（信号高）=健康结构中的持续性方向流（机构配置节奏），延续；溃疡深（信号低）=持续流是失血中的对倒噪声。声明：OFI_AUTOCORR_20(M1/M5)第3次；ULCER_60(Y1/Z4)第2次。预期正方向。",
        "expected_sign": 1,
    },
]

_orig_cmd_plan = base.cmd_plan


def _cmd_plan_with_micro(args):
    _orig_cmd_plan(args)
    plan_path = Path(args.output).resolve() / "PLAN.json"
    plan = json.loads(plan_path.read_text())
    plan["stage"] = "stage6_microstructure_1m_literature"
    plan["pit_note"] = (
        "1m 微观结构/基准原子只用 <=D 的完整交易日 1m bar；基准 510300.SH/510500.SH 仅作参照腿；"
        "泄漏门物理截断/扰动副本含基准文件；全部原子泄漏缓存命中"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_micro

if __name__ == "__main__":
    base.main()
