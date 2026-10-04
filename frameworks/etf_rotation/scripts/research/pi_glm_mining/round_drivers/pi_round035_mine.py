#!/usr/bin/env python3
"""Round 035 driver: stage 6 = 1m market microstructure (literature-backed).
Two new families built and health-checked (outputs/round_035/atom_health.csv,
SYNC_BETA_20 flagged shadow at |corr|=0.76 vs downside_risk -> excluded).
Six rank_spread candidates, each with >=1 leg from microstructure_1m or
benchmark_leadlag_1m (benchmark leg = 510300.SH/510500.SH reference only,
never in the candidate population). All pairs atom-level new; burnt legs
declared. Gate 7 v2.1; leak gates include physical 1m truncation/perturbation
(temp root now also carries the benchmark reference files)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402  (corrected runner, frozen contract)

base.ROUND_ID = "round_035"

base.CANDIDATES = [
    {
        "id": "N1",
        "operator": "rank_spread",
        "left": {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"},
        "right": {"name": "PREMIUM", "source": "nav_premium"},
        "mechanism": "vpin_informed_discount",
        "hypothesis": "两腿角色：A=VPIN(知情交易概率，Easley–López de Prado–O'Hara 2012, BVC 体积桶)；B=折溢价(二级情绪/净值偏离)。假设：VPIN 高而溢价低(信号高)=知情资金在折价处吸筹，延续；VPIN 低而溢价高(信号低)=无知情支撑的情绪溢价，回吐。声明：VPIN 首次价差腿；PREMIUM(X1/X3-032)第2次。出处：Easley, López de Prado & O'Hara (2012) Flow Toxicity and Liquidity in a High-frequency World。预期负方向。",
        "expected_sign": -1,
    },
    {
        "id": "N2",
        "operator": "rank_spread",
        "left": {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"},
        "right": {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"},
        "mechanism": "continuous_flow_price_discovery",
        "hypothesis": "两腿角色：A=Kyle λ 代理(单位净流的价格冲击，Kyle 1985/Hasbrouck 2009)；B=尾30分钟量占比(收盘标记型参与)。假设：λ 高而尾盘集中低(信号高)=冲击来自连续真实流量而非收盘标记，价格发现真实，延续；尾盘集中高(信号低)=标记型冲击，不可信。声明：KYLE_LAMBDA_20 首次价差腿；CLOSE30_VOL_SHARE_20(V2/V3-031 条件腿)第2次。出处：Kyle (1985)；Hasbrouck (2009)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "N3",
        "operator": "rank_spread",
        "left": {"name": "ROLL_SPREAD_20", "source": "microstructure_1m"},
        "right": {"name": "STREAK_DAYS", "source": "fund_flow"},
        "mechanism": "low_friction_primary_streak",
        "hypothesis": "两腿角色：A=Roll 隐性价差(交易摩擦，Roll 1984)；B=连续净申购天数(一级承接方向)。假设：价差低而连续净申购(信号高)=低摩擦环境+持续一级配置流入，健康延续；价差高(信号低)=摩擦吞噬申赎推动。声明：ROLL_SPREAD_20 首次价差腿；STREAK_DAYS(T5 左腿)第2次。出处：Roll (1984) A Simple Implicit Measure of the Effective Bid-Ask Spread。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "N4",
        "operator": "rank_spread",
        "left": {"name": "IMPACT_ASYM_20", "source": "microstructure_1m"},
        "right": {"name": "CATEGORY_VOL_20", "source": "category_state"},
        "mechanism": "buy_impact_in_calm_category",
        "hypothesis": "两腿角色：A=买卖 bar 冲击非对称(买侧|Δp|/量 相对卖侧之比)；B=类别20日波动(环境条件)。假设：买侧冲击强而类别平静(信号高)=逆类别噪声的定向买方冲击(知情)，延续；类别高波动(信号低)=冲击被环境噪声淹没。声明：IMPACT_ASYM_20 首次价差腿；CATEGORY_VOL_20(T4/Y3)第2次。出处：价格冲击非对称 = 买/卖 bar |Δp|/volume 之比(日)，20 日均值。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "N5",
        "operator": "rank_spread",
        "left": {"name": "LAG1_BENCH_CORR_20", "source": "benchmark_leadlag_1m"},
        "right": {"name": "PREMIUM_Z_20", "source": "nav_premium"},
        "mechanism": "bench_lag_no_overhang",
        "hypothesis": "两腿角色：A=对基准(510300/510500)1m 收益的滞后 1 拍相关(价格发现滞后于基准)；B=折溢价 20 日 z(情绪透支度)。假设：滞后相关高而溢价 z 低(信号高)=滞后定价且无情绪透支，基准延续时补涨，漂移；溢价 z 高(信号低)=情绪透支的滞后。声明：LAG1_BENCH_CORR_20 首次价差腿；PREMIUM_Z_20(X6 左腿)第2次。出处：滞后互相关的领先/滞后构造(Lo–MacKinlay 1990 式 lead-lag)。预期正方向。",
        "expected_sign": 1,
    },
    {
        "id": "N6",
        "operator": "rank_spread",
        "left": {"name": "SYNC_R2_20", "source": "benchmark_leadlag_1m"},
        "right": {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"},
        "mechanism": "beta_dominance_clean_overhang",
        "hypothesis": "两腿角色：A=对基准同步 β 的 R²(基准主导定价程度)；B=上方套牢厚度(结构包袱)。假设：R² 高而套牢薄(信号高)=干净贝塔(无结构包袱的市场敞口)，贝塔延续时延续；套牢厚(信号低)=结构包袱扭曲贝塔响应。声明：SYNC_R2_20 首次价差腿；OVERHAND_THICKNESS_60(D2/D3/E1/AA1/AA2)第5次。出处：同步 R²=日内 1m 对基准回归的拟合优度(Morck–Yeung–Yu 2000 式同步性)。预期正方向。",
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
        "1m 微观结构/基准原子只用 <=D 的完整交易日 1m bar（引擎 complete-day 读取器）；"
        "基准 510300.SH/510500.SH 仅作参照腿，不入候选人口；泄漏门物理截断/扰动副本含基准文件"
    )
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


base.cmd_plan = _cmd_plan_with_micro

if __name__ == "__main__":
    base.main()
