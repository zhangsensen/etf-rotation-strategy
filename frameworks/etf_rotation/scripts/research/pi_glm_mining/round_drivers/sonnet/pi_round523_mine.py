#!/usr/bin/env python3
"""Round 523 driver: S4 stage step 5 -- jump_continuous_beta pairing, round 5.

Four-round scoreboard (round_519-522, 59 candidates, 6 admitted):
CONTINUOUS_BETA_60 is now the leading channel: 2/15 (atomic JB2 +
round_522's KK1 = CONTINUOUS_BETA_60 x BIGBAR_DIR_SKEW_20, t=3.48,
+35.1bp -- the strongest hit of the whole family so far). Its previous 13
pairing attempts (round_520/521/522) spanned volume-share, big-bar-clock,
turnover, gap-fill, and concentration themes with 0 hits except the
direction-skew one -- suggesting the productive dimension for this leg is
asymmetry/skew/dispersion, not raw activity level. This round follows that
channel with 12 fresh partners drawn from every unused
asymmetry/dispersion/cost-basis atom in the catalog (return_tail_shape's
skew/tail-quantile atoms, category_state's dispersion/breadth atoms,
bar_size_order_flow's remaining consistency atom, cost_distribution's
profit-ratio/cost-basis atoms).

JUMP_BETA_STABILITY_20 (1/15, round_521's single hit did not generalize in
round_522's 7-partner follow-up) gets one small final 3-partner check with
completely fresh atoms before this round's scoreboard decides whether to
keep sampling it.

JUMP_BETA_20 (2/11, flat since round_520) and BETA_GAP_20 (0/9, effectively
closed) and CONTINUOUS_BETA_20 (0/6, structurally shadow) get no new
candidates this round -- per "follow the significant channel" the compute
goes to CONTINUOUS_BETA_60 instead of re-diagnosing legs already sampled
broadly with flat/negative results.

Note on data gap (does not block this round): round_522's macro_hedge_
sensitivity atoms (GOLD/BOND_PARTIAL_CORR_20) returned 0 discovery_days --
a data/engine issue in that family, not evaluated here or in this round.

All partners below are new to this family's cumulative pairing history."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_523"

_RSKEW20 = {"name": "RETURN_SKEW_20", "source": "return_tail_shape"}
_RSKEW60 = {"name": "RETURN_SKEW_60", "source": "return_tail_shape"}
_TAILQ10_20 = {"name": "TAIL_Q10_20", "source": "return_tail_shape"}
_TAILQ10_60 = {"name": "TAIL_Q10_60", "source": "return_tail_shape"}
_CLOSE5_CONSIST = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}
_CAT_DISP20 = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_CAT_DISP60 = {"name": "CATEGORY_DISPERSION_60", "source": "category_state"}
_CAT_BREADTH20 = {"name": "CATEGORY_BREADTH_MA20", "source": "category_state"}
_CAT_BREADTH60 = {"name": "CATEGORY_BREADTH_MA60", "source": "category_state"}
_PROFIT_RATIO = {"name": "PROFIT_RATIO_60", "source": "cost_distribution"}
_PRICE_AVGCOST = {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"}
_COST_SHIFT = {"name": "COST_CENTER_SHIFT_20", "source": "cost_distribution"}
_LBAR_AMTSPLIT = {"name": "LBAR_AMTSPLIT_20", "source": "largebar_footprint_1m"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_BIGBAR_EDGE = {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"}

_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_JBSTAB20 = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}

base.CANDIDATES = [
    # ---- CONTINUOUS_BETA_60: follow the asymmetry/dispersion channel
    # (round_522 KK1 x BIGBAR_DIR_SKEW_20 t=3.48 +35.1bp -- the family's
    # strongest hit; prior activity-level partners all flat) ----
    {
        "id": "KN1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RSKEW20,
        "mechanism": "continuous_beta60_confirmed_by_return_skew_20",
        "hypothesis": "A=连续分量beta，60日窗（round_522 KK1已证明该腿的方向偏斜/不对称信息面是productive channel：×BIGBAR_DIR_SKEW_20 t=3.48 +35.1bp）。B=20日收益偏度（return_tail_shape，自身收益分布不对称性，本族对CBETA60首次使用；已与JUMP_BETA_20配过但从未与CBETA60配）。假设：常态系统性暴露高(A高)且收益分布右偏(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KN2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RSKEW60,
        "mechanism": "continuous_beta60_confirmed_by_return_skew_60",
        "hypothesis": "A=同上。B=60日收益偏度（同上，更长窗，与A同窗对齐）。假设：同KN1，机制在与A同窗时是否更强。",
        "expected_sign": 1,
    },
    {
        "id": "KN3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _TAILQ10_20,
        "mechanism": "continuous_beta60_confirmed_by_tail_q10_20",
        "hypothesis": "A=同上。B=20日收益分布10%分位数（return_tail_shape，尾部厚度的另一种度量，本族首次使用）。假设：常态系统性暴露高(A高)且下尾更浅(B高，10分位数不那么负)=风险暴露常态化而非极端化，延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KN4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _TAILQ10_60,
        "mechanism": "continuous_beta60_confirmed_by_tail_q10_60",
        "hypothesis": "A=同上。B=60日版本（同上）。假设：同KN3，长窗是否更稳健。",
        "expected_sign": 1,
    },
    {
        "id": "KN5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CLOSE5_CONSIST,
        "mechanism": "continuous_beta60_confirmed_by_close5_day_consistency",
        "hypothesis": "A=同上。B=收盘前5分钟方向一致性（bar_size_order_flow，与已证明有效的BIGBAR_DIR_SKEW_20同族但不同字段，聚焦尾盘时段的方向持续性，本族首次使用）。假设：常态系统性暴露高(A高)且尾盘方向高度一致(B高)=延续，与KK1同一方向偏斜主题的近邻测试。",
        "expected_sign": 1,
    },
    {
        "id": "KN6",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CAT_DISP20,
        "mechanism": "continuous_beta60_confirmed_by_category_dispersion_20",
        "hypothesis": "A=同上。B=板块内部20日收益离散度（category_state，本族首次使用；衡量板块内部个股分化程度）。假设：常态系统性暴露高(A高)且板块内部分化大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KN7",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CAT_DISP60,
        "mechanism": "continuous_beta60_confirmed_by_category_dispersion_60",
        "hypothesis": "A=同上。B=60日版本（同上）。假设：同KN6，长窗是否更稳健。",
        "expected_sign": 1,
    },
    {
        "id": "KN8",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CAT_BREADTH20,
        "mechanism": "continuous_beta60_confirmed_by_category_breadth_20",
        "hypothesis": "A=同上。B=板块20日广度均值（category_state，本族首次使用；板块内上涨家数占比的均值）。假设：常态系统性暴露高(A高)且板块广度弱(B低，少数票带动)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KN9",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CAT_BREADTH60,
        "mechanism": "continuous_beta60_confirmed_by_category_breadth_60",
        "hypothesis": "A=同上。B=60日版本（同上）。假设：同KN8，长窗是否更稳健。",
        "expected_sign": 1,
    },
    {
        "id": "KN10",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PROFIT_RATIO,
        "mechanism": "continuous_beta60_confirmed_by_profit_ratio",
        "hypothesis": "A=同上。B=60日获利比例（cost_distribution，持仓者浮盈占比，本族首次使用）。假设：常态系统性暴露高(A高)且获利盘占比低(B低，套牢盘主导)=定价对系统性因子的反应受套牢盘抑制而延迟，用rank_spread方向按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KN11",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PRICE_AVGCOST,
        "mechanism": "continuous_beta60_confirmed_by_price_vs_avgcost",
        "hypothesis": "A=同上。B=现价相对平均成本偏离（cost_distribution，本族首次使用；round_510曾与upside_tail的BEST_DAY_60_XVOL配过，从未与jump_continuous_beta配）。假设：常态系统性暴露高(A高)且现价明显高于平均成本(B高，获利盘厚)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KN12",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _COST_SHIFT,
        "mechanism": "continuous_beta60_confirmed_by_cost_center_shift",
        "hypothesis": "A=同上。B=成本中枢20日迁移速度（cost_distribution，本族首次使用）。假设：常态系统性暴露高(A高)且成本中枢快速上移(B高，筹码正在换手上移)=延续。",
        "expected_sign": 1,
    },
    # ---- JUMP_BETA_STABILITY_20: small final check with 3 fresh atoms
    # before deciding whether to keep sampling this leg (1/15 so far,
    # round_521's single hit did not generalize in round_522's follow-up) ----
    {
        "id": "KO1",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _LBAR_AMTSPLIT,
        "mechanism": "jump_beta_stability_confirmed_by_bigbar_amount_split",
        "hypothesis": "A=跳跃beta估计不确定性（1/15，round_521 KI1×LBAR_OVERNIGHT_20 t=2.47 +17.3bp是唯一命中）。B=大bar成交额分割结构（largebar_footprint_1m，本族首次使用）。假设：估计不确定性高(A高)且大bar成交额分割异常(B高)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "KO2",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _VOL_ENTROPY,
        "mechanism": "jump_beta_stability_confirmed_by_volume_entropy",
        "hypothesis": "A=同上。B=日内成交量分布熵（intraday_volume_profile_1m，本族首次使用；衡量成交量在日内的分散/集中程度）。假设：估计不确定性高(A高)且成交量分布熵高(B高，成交分散无规律)=跳跃beta的估计缺乏稳定的日内锚点，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KO3",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _BIGBAR_EDGE,
        "mechanism": "jump_beta_stability_confirmed_by_bigbar_edge_concentration",
        "hypothesis": "A=同上。B=大bar集中于日内边缘时段的程度（bar_size_order_flow，已与CONTINUOUS_BETA_60配过[round_522 KK2, topk_gate拒绝]，未与本腿配过）。假设：估计不确定性高(A高)且大bar集中在开盘/收盘边缘(B高)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
