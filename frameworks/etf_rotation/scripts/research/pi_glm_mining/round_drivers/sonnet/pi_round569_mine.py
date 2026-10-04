#!/usr/bin/env python3
"""Round 569 driver: S14 stage -- cross-lane independent replication of
4 pi-lane non-volume-only significant candidates (DA57, CZ01, CA1, CK04),
built strictly from the S14 directive's literature definitions (pi
workspace code NOT read). Per directive, this stage is "only this one
round" -- 4 candidates, not the usual 15-30, no pairing-discipline
batches; REPORT lists a replication-comparison table against pi's
reported numbers, then the stage is declared exhausted regardless of
outcome.

Atom mapping:
  DA57 = rank(PD_D1_CHG_20) - rank(AUC_VARIANCE_RATIO_20), both newly
    built in pi_replication_s14 (Hou-Moskowitz 2005 price delay;
    Amihud-Mendelson 1987 open/close vol asymmetry). pi: audit +43.7bp/t 2.07.
  CZ01 = rank(ON_PREM_20) - rank(BIGBAR_EDGE_CONC_20). ON_PREM_20 is
    textually identical to the pre-existing daily_candle:GAP_MEAN_20
    (Lou-Polk-Skouras 2019 overnight return, 20d mean) -- reused as-is,
    not rebuilt. BIGBAR_EDGE_CONC_20's directive definition does NOT
    match this line's pre-existing same-named atom (which uses a
    different modal-slot-concentration formula) -- the correctly
    matching construct is newly built as EDGE_BIGBAR_VOLSHARE_20. pi:
    audit +55.2bp/t 2.76.
  CA1 = PV_ELASTICITY_20 (atomic, Karpoff 1987 volume-price elasticity),
    newly built in pi_replication_s14. pi: audit +52.3bp/t 2.75.
  CK04 = rank(LUNCH_PRE_RUN_20) - rank(CLOSE5_DAY_CONSIST_20).
    LUNCH_PRE_RUN_20 newly built in pi_replication_s14.
    CLOSE5_DAY_CONSIST_20 is textually identical to the pre-existing
    bar_size_order_flow:CLOSE5_DAY_CONSIST_20 (tail-5-min direction vs
    full-day direction, 20d mean = fraction of matching days) -- reused
    as-is, not rebuilt. pi: audit +53.0bp/t 2.72."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_569"

_PD_D1_CHG = {"name": "PD_D1_CHG_20", "source": "pi_price_delay_1d"}
_AUC_RATIO = {"name": "AUC_VARIANCE_RATIO_20", "source": "pi_auc_variance_ratio_1m"}
_PV_ELASTICITY = {"name": "PV_ELASTICITY_20", "source": "pi_pv_elasticity_1m"}
_EDGE_BIGBAR = {"name": "EDGE_BIGBAR_VOLSHARE_20", "source": "pi_edge_bigbar_volshare_1m"}
_LUNCH_PRE_RUN = {"name": "LUNCH_PRE_RUN_20", "source": "pi_lunch_prerun_1m"}
_ON_PREM = {"name": "GAP_MEAN_20", "source": "daily_candle"}
_CLOSE5_CONSIST = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}

base.CANDIDATES = [
    {
        "id": "S14_DA57",
        "operator": "rank_spread",
        "left": _PD_D1_CHG,
        "right": _AUC_RATIO,
        "mechanism": "pi_replication_da57_price_delay_chg_vs_auc_variance_ratio",
        "hypothesis": "pi 线 DA57 独立复现。A=Hou-Moskowitz(2005)价格延迟D1(60日滚动日频回归,14只等权篮子当期vs当期+4期滞后)的20日变化,本线新建。B=Amihud-Mendelson(1987)首/尾30分钟1m已实现方差之比,20日均值,本线新建。体检:A disc-0.0062(576天)/审计+0.0729;B disc-0.1080(510天)/审计-0.0938。pi报告:审计+43.7bp/t=2.07。假设:价格延迟正在扩大(A高)且开盘相对收盘波动占比低(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "S14_CZ01",
        "operator": "rank_spread",
        "left": _ON_PREM,
        "right": _EDGE_BIGBAR,
        "mechanism": "pi_replication_cz01_overnight_vs_edge_bigbar_volshare",
        "hypothesis": "pi 线 CZ01 独立复现。A=隔夜收益(开盘/前收-1)20日均值(Lou-Polk-Skouras 2019),与本线已有daily_candle:GAP_MEAN_20公式完全一致,直接复用不重建。B=最大10%成交量1m bar且位于首尾30分钟的成交量占全日成交量比例,20日均值,本线新建为EDGE_BIGBAR_VOLSHARE_20(本线原有同名bar_size_order_flow:BIGBAR_EDGE_CONC_20公式不同[大单modal时段集中度],故改名避免误用)。体检:A disc+0.0252(559天)/审计+0.0135;B disc-0.0422(510天)/审计-0.0281。pi报告:审计+55.2bp/t=2.76。假设:隔夜收益高(A高)且大单尾盘边缘集中度低(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "S14_CA1",
        "operator": "atomic",
        "left": _PV_ELASTICITY,
        "right": _PV_ELASTICITY,
        "mechanism": "pi_replication_ca1_pv_elasticity",
        "hypothesis": "pi 线 CA1 独立复现(单原子)。日内1m |收益|对log(1m成交量)OLS斜率的20日均值(Karpoff 1987量价弹性),本线新建。体检:disc-0.1288(510天)/审计-0.1004。pi报告:审计+52.3bp/t=2.75。假设:量价弹性高(A高,量增价响应强)=延续,负相关(按本线体检符号)。",
        "expected_sign": -1,
    },
    {
        "id": "S14_CK04",
        "operator": "rank_spread",
        "left": _LUNCH_PRE_RUN,
        "right": _CLOSE5_CONSIST,
        "mechanism": "pi_replication_ck04_lunch_pre_run_vs_close5_consistency",
        "hypothesis": "pi 线 CK04 独立复现。A=11:20-11:30成交量占全日比例,20日均值,本线新建为LUNCH_PRE_RUN_20。B=尾5分钟收益方向与全日方向一致的天数占比,20日,与本线已有bar_size_order_flow:CLOSE5_DAY_CONSIST_20公式完全一致,直接复用不重建。体检:A disc+0.0300(510天)/审计+0.0646;B disc-0.0233(544天)/审计-0.0313。pi报告:审计+53.0bp/t=2.72。假设:午休前尾盘成交占比高(A高)且尾盘方向一致性低(B低)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
