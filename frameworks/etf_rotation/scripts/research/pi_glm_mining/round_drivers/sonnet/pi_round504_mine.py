#!/usr/bin/env python3
"""Round 504 driver: S2 stage step 1 — upside_tail family atomic gate-7
readjudication (all 6 atoms submitted; atom_health flagged 5/6 as shadow
>=0.70 vs a downside_risk shelf factor or RETURN_SKEW_20, so this batch
also serves as the pipeline-native redundancy-dedup demonstration for
those five — only POS_DAY_FRAC_Z_20 is non-shadow). Bali-Cakici-Whitelaw
(2011) MAX effect / Barberis-Huang (2008) / Kumar (2009): lottery-like
upside-tail exposure is overpriced and subsequently underperforms, so
expected_sign=-1 (high rank(atom) -> lower subsequent relative return)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_504"

base.CANDIDATES = [
    {
        "id": "UT1",
        "operator": "atomic",
        "left": {"name": "BEST_DAY_20", "source": "upside_tail"},
        "right": {"name": "BEST_DAY_20", "source": "upside_tail"},
        "mechanism": "max_effect_best_day_20",
        "hypothesis": "Bali-Cakici-Whitelaw MAX 效应，20日窗。体检：disc -0.0941/559天/审计-0.0736，**shadow=True**（max|corr|=0.724 vs downside_risk 货架因子哈希 e5ad3afc...，即该原子实质是波动率水平的代理，非独立的彩票偏好信号）。方向已与假设匹配（负），但预期会在去重门被货架相关性拒绝。",
        "expected_sign": -1,
    },
    {
        "id": "UT2",
        "operator": "atomic",
        "left": {"name": "BEST_DAY_60", "source": "upside_tail"},
        "right": {"name": "BEST_DAY_60", "source": "upside_tail"},
        "mechanism": "max_effect_best_day_60",
        "hypothesis": "同UT1，60日窗。体检：disc -0.1143/551天/审计-0.0767，**shadow=True**（max|corr|=0.838，本批最高相关，vs同一downside_risk货架因子）。",
        "expected_sign": -1,
    },
    {
        "id": "UT3",
        "operator": "atomic",
        "left": {"name": "MAX5_MEAN_20", "source": "upside_tail"},
        "right": {"name": "MAX5_MEAN_20", "source": "upside_tail"},
        "mechanism": "max_effect_top5_mean_20",
        "hypothesis": "Bali-Cakici-Whitelaw MAX(5)稳健变体，取20日窗内最大5日收益均值。体检：disc -0.0929/559天/审计-0.0544，**shadow=True**（max|corr|=0.743，同一downside_risk货架因子）。",
        "expected_sign": -1,
    },
    {
        "id": "UT4",
        "operator": "atomic",
        "left": {"name": "TAIL_RATIO_20", "source": "upside_tail"},
        "right": {"name": "TAIL_RATIO_20", "source": "upside_tail"},
        "mechanism": "upside_downside_tail_ratio_20",
        "hypothesis": "Barberis-Huang 2008 概率加权：上行尾/|下行尾|比值，比值越高=正偏好资产越被追捧。体检：disc +0.0110/559天/审计+0.0251，**shadow=True**（max|corr|=0.778 vs return_tail_shape:RETURN_SKEW_20，即该原子基本重复了已有的偏度原子）。",
        "expected_sign": -1,
    },
    {
        "id": "UT5",
        "operator": "atomic",
        "left": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "right": {"name": "POS_DAY_FRAC_Z_20", "source": "upside_tail"},
        "mechanism": "positive_day_fraction_regime_z_20",
        "hypothesis": "Kumar 2009 彩票需求状态切换：20日正收益日占比相对自身120日基线的z分数。体检：disc -0.0139/579天/审计-0.0209，max|corr|=0.236（vs realized_measures_1m:RS_MINUS_20），**非shadow**，本批唯一独立信号。",
        "expected_sign": -1,
    },
    {
        "id": "UT6",
        "operator": "atomic",
        "left": {"name": "INTRADAY_MAXBAR_RET_20", "source": "upside_tail"},
        "right": {"name": "INTRADAY_MAXBAR_RET_20", "source": "upside_tail"},
        "mechanism": "intraday_maxbar_lottery_proxy_20",
        "hypothesis": "MAX效应的1m日内延伸：单日最大1分钟bar收益，20日均值。体检：disc -0.0860/579天/审计-0.0611，**shadow=True**（max|corr|=0.747，同一downside_risk货架因子），说明日内极端bar同样主要反映波动率水平。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
