#!/usr/bin/env python3
"""Round 036 driver: stage-6 round 2 (entering streak: 1 zero round, r035).
Deploys the five still-unused new-family legs (OFI_AUTOCORR_20, AMIHUD_1M_20,
BETA_CHG_20, TAIL30_BETA_GAP_20 + reuse of OFI/AMIHUD with fresh partners).
Six rank_spread pairs, all atom-level new; burnt legs declared. Gate 7 v2.1;
leak caches cover every atom (all built and leak-verified in r035/fund era)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_036"

base.CANDIDATES = [
    {
        "id": "M1",
        "operator": "rank_spread",
        "left": {"name": "OFI_AUTOCORR_20", "source": "microstructure_1m"},
        "right": {"name": "SHARE_RET_CORR_20", "source": "fund_flow"},
        "mechanism": "persistent_flow_not_primary_driven",
        "hypothesis": "两腿角色：A=订单流不平衡持续性（BVC 净买量 1m 一阶自相关，Cont–Kukanov–Stoikov 2014）；B=份额变化-收益 20 日相关（一级流对价格的解释力）。假设：订单流有记忆而一级流不解释价格（信号高）=持续性来自二级自身订单流（真实价格发现），延续；一级流主导（信号低）=持续性是申赎噪声。声明：OFI_AUTOCORR_20 首次价差腿；SHARE_RET_CORR_20(X6-032)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "M2",
        "operator": "rank_spread",
        "left": {"name": "AMIHUD_1M_20", "source": "microstructure_1m"},
        "right": {"name": "TAIL_Q10_20", "source": "return_tail_shape"},
        "mechanism": "thin_book_no_tail_damage",
        "hypothesis": "两腿角色：A=1m Amihud（单位成交额价格冲击，Amihud 2002 分钟版）；B=左尾深度（尾部损伤）。假设：冲击成本高而近期左尾浅（信号高）=薄簿是正常流动性消耗而非恐慌损伤，冲击定价合理，修复延续；薄簿+深左尾（信号低）=结构性失血。声明：AMIHUD_1M_20 首次价差腿；TAIL_Q10_20(S2/BB6/X5)第3次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "M3",
        "operator": "rank_spread",
        "left": {"name": "BETA_CHG_20", "source": "benchmark_leadlag_1m"},
        "right": {"name": "INTRADAY_RETURN_KURTOSIS", "source": "intraday_return_distribution"},
        "mechanism": "calm_decoupling_from_benchmark",
        "hypothesis": "两腿角色：A=对基准同步 β 的 20 日变化（1m 收盘段跟随度的边际变化）；B=日内收益峰度（极端事件密度）。假设：β 下降而峰度低（信号高）=在平静市况中走出基准（脱钩启动），独立行情延续；峰度高（信号低）=脱钩由极端事件驱动，不可信。声明：BETA_CHG_20 首次价差腿；INTRADAY_RETURN_KURTOSIS(Y3 左腿)第2次。出处：β 变化=20 日均值差（Morck–Yeung–Yu 2000 式同步性的边际）。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "M4",
        "operator": "rank_spread",
        "left": {"name": "TAIL30_BETA_GAP_20", "source": "benchmark_leadlag_1m"},
        "right": {"name": "PRIMARY_SHARE_20", "source": "fund_flow"},
        "mechanism": "close_session_secondary_following",
        "hypothesis": "两腿角色：A=尾 30 分钟 β − 全日 β（收盘段跟随度增强）；B=一级市场量占比（申赎扰动）。假设：收盘段跟随增强而一级占比低（信号高）=跟随由二级自身定价产生（收盘配置盘），延续；一级占比高（信号低）=跟随是申赎冲击的机械响应。声明：TAIL30_BETA_GAP_20 首次价差腿；PRIMARY_SHARE_20(Y6/X4)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "M5",
        "operator": "rank_spread",
        "left": {"name": "OFI_AUTOCORR_20", "source": "microstructure_1m"},
        "right": {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "disciplined_persistent_flow",
        "hypothesis": "两腿角色：A=订单流不平衡持续性（Cont–Kukanov–Stoikov 2014）；B=日内量分布熵（量的时间均匀度）。假设：订单流持续而量熵低（信号高）=量集中在固定节奏（机构化执行）的持续方向性流，延续；量熵高（信号低）=持续流被散户噪声稀释。声明：OFI_AUTOCORR_20 第2次（M1 为另一构造）；VOL_ENTROPY_20(AA1/AA5)第2次。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "M6",
        "operator": "rank_spread",
        "left": {"name": "AMIHUD_1M_20", "source": "microstructure_1m"},
        "right": {"name": "PREMIUM", "source": "nav_premium"},
        "mechanism": "clean_thinness_no_sentiment",
        "hypothesis": "两腿角色：A=1m Amihud（薄簿程度）；B=折溢价（情绪透支）。假设：薄簿而无情绪溢价（信号高）=干净薄簿，冲击补偿定价合理，配置盘进入成本低端，延续；薄簿+高溢价（信号低）=情绪推高的薄簿，回吐风险。声明：AMIHUD_1M_20 第2次（M2 为另一构造）；PREMIUM(X1/X3/N1)第3次。预期正方向。",
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
        "泄漏门物理截断/扰动副本含基准文件（round_035 修复已生效）"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_micro

if __name__ == "__main__":
    base.main()
