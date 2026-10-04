#!/usr/bin/env python3
"""Round 521 driver: S4 stage step 3 -- jump_continuous_beta pairing, round 3.

Two-round scoreboard so far for this family (round_519+520, 30 candidates,
3 admitted = 10% hit rate): JUMP_BETA_20 2/5 pairs admitted (JC1, KA2),
CONTINUOUS_BETA_60 1/6 (atomic JB2 only, 0/5 pairs), BETA_GAP_20 0/6,
JUMP_BETA_STABILITY_20 0/6, CONTINUOUS_BETA_20 0/6 (3 pairs failed on
rank_correlation_redundancy specifically, confirming its atom_health shadow
flag was directionally right). Per "direction determined by data, follow
the significant channel" (main controller / user standing rule): this round
concentrates fresh partner atoms on the two productive legs (JUMP_BETA_20,
CONTINUOUS_BETA_60), and gives the two flat-zero legs (BETA_GAP_20,
JUMP_BETA_STABILITY_20) exactly 2 more genuinely-new partners each as a
last diversity check rather than declaring them dead on n=6.
CONTINUOUS_BETA_20 gets no new candidates this round (0/6 including 3
redundancy fails -- structurally shadow, further pairing would not be new
information).

Every partner atom below is NEW to this family's pairing history (none of
round_519's or round_520's 11 already-used partners are repeated), drawn
from previously-validated channel/shelf atoms in largebar_footprint_1m,
bar_size_order_flow, intraday_volume_profile_1m, category_state,
intraday_profile_deviation, gap_repair, return_tail_shape -- no same-family
(jump_continuous_beta x jump_continuous_beta) pairs, no window variants of
an existing (left,right) combo."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_521"

_TICK_IMB = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}
_LBAR_RET = {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"}
_LBAR_RUNMAX = {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"}
_LBAR_PERM15 = {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"}
_LBAR_TREND = {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"}
_LBAR_OVERNIGHT = {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"}
_CLOSE30 = {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_VOL_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_CAT_DD20 = {"name": "CATEGORY_CURRENT_DD_20", "source": "category_state"}
_CAT_DD60 = {"name": "CATEGORY_CURRENT_DD_60", "source": "category_state"}
_TURNOVER_DIST = {"name": "TURNOVER_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_GAP_FILL20 = {"name": "GAP_FILL_FRACTION_20", "source": "gap_repair"}
_RSKEW20 = {"name": "RETURN_SKEW_20", "source": "return_tail_shape"}
_RSKEW60 = {"name": "RETURN_SKEW_60", "source": "return_tail_shape"}

_JB20 = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_BGAP20 = {"name": "BETA_GAP_20", "source": "jump_continuous_beta"}
_JBSTAB20 = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}
_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}

base.CANDIDATES = [
    # ---- JUMP_BETA_20: partners #6-11 (2/5 hit rate so far: JC1 t=4.10
    # +17.9bp, KA2 t=2.38 +7.6bp -- the productive leg, follow the channel) ----
    {
        "id": "KF1",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _TICK_IMB,
        "mechanism": "jump_beta_confirmed_by_tick_imbalance",
        "hypothesis": "A=跳跃分量beta（Todorov-Bollerslev 2010；round_519/520两个不同partner已各自独立入选，非退化单腿）。B=1m order flow不平衡（bar_size_order_flow，未与本族任何腿配对过）。假设：跳跃期系统性暴露高(A高)且同期买卖单不平衡明显(B高)=跳跃由真实定向流驱动而非噪声，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KF2",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _LBAR_RET,
        "mechanism": "jump_beta_confirmed_by_bigbar_return_contribution",
        "hypothesis": "A=同上。B=大bar对当日收益的贡献占比（largebar_footprint_1m，未配对过）。假设：跳跃期系统性暴露高(A高)且当日收益主要由少数大bar贡献(B高)=跳跃与可观测的大单事件同源，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KF3",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _LBAR_RUNMAX,
        "mechanism": "jump_beta_confirmed_by_bigbar_run_max",
        "hypothesis": "A=同上。B=最大连续大bar游程长度（largebar_footprint_1m，未配对过）。假设：跳跃期系统性暴露高(A高)且大bar呈连续游程而非孤立(B高)=跳跃期存在结构化的持续冲击，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KF4",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _CAT_DD20,
        "mechanism": "jump_beta_confirmed_by_category_drawdown",
        "hypothesis": "A=同上。B=所属板块当前回撤深度（category_state，未配对过）。假设：跳跃期系统性暴露高(A高)且板块正处深回撤(B高)=跳跃与板块层面的压力状态共振，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KF5",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _RSKEW20,
        "mechanism": "jump_beta_confirmed_by_return_skew_20",
        "hypothesis": "A=同上。B=20日收益偏度（return_tail_shape，未配对过；与coskewness_risk的协偏度不同，这是自身收益分布的偏度）。假设：跳跃期系统性暴露高(A高)且自身收益分布右偏(B高，正向极端更多)=跳跃更多来自正向冲击，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KF6",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _RSKEW60,
        "mechanism": "jump_beta_confirmed_by_return_skew_60",
        "hypothesis": "A=同上。B=60日收益偏度（同上，更长窗）。假设：同KF5，机制在更长窗口是否稳健。",
        "expected_sign": 1,
    },
    # ---- CONTINUOUS_BETA_60: partners #6-10 (atomic JB2 admitted, but 0/5
    # pairs so far all failed on redundancy/topk -- give 5 fresh partners
    # from families with no rank-corr history vs this leg yet) ----
    {
        "id": "KG1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _LBAR_PERM15,
        "mechanism": "continuous_beta60_confirmed_by_bigbar_perm15",
        "hypothesis": "A=连续分量beta，60日窗（JB2已atomic入选：disc-0.1155/审计-0.0875）。B=大bar冲击15分钟后的持久性（largebar_footprint_1m，未配对过；round_053门7全过史)。假设：常态系统性暴露高(A高)且大bar冲击持久(B高，非瞬时反转)=常态beta暴露伴随持久性冲击结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KG2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _LBAR_TREND,
        "mechanism": "continuous_beta60_confirmed_by_bigbar_trend",
        "hypothesis": "A=同上。B=大bar方向性趋势强度（largebar_footprint_1m，未配对过）。假设：常态系统性暴露高(A高)且大bar呈趋势性而非双向噪声(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KG3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CLOSE30,
        "mechanism": "continuous_beta60_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上。B=收盘30分钟成交占比（intraday_volume_profile_1m，与已用过的OPEN30_VOL_SHARE_20对称但未配对过）。假设：常态系统性暴露高(A高)且尾盘集中放量(B高)=常态beta暴露在收盘前被重新定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KG4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _TURNOVER_DIST,
        "mechanism": "continuous_beta60_confirmed_by_turnover_profile_shift",
        "hypothesis": "A=同上。B=日内换手分布偏离（intraday_profile_deviation，与已用过的VOL_PROFILE_DISTANCE同族不同字段，未配对过）。假设：常态系统性暴露高(A高)且日内换手结构异常(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KG5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _GAP_FILL20,
        "mechanism": "continuous_beta60_confirmed_by_gap_fill_20",
        "hypothesis": "A=同上。B=20日窗缺口回补比例（gap_repair，与已用的60日版本不同窗口但为独立预注册原子，未配对过）。假设：常态系统性暴露高(A高)且短窗缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- BETA_GAP_20: 0/6 so far (atomic+5 pairs), last 2-partner diversity
    # check before declaring this leg's pairing space null ----
    {
        "id": "KH1",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _VOL_AUTOCORR,
        "mechanism": "beta_gap_confirmed_by_volume_autocorr",
        "hypothesis": "A=崩盘beta缺口（Bollerslev-Li-Todorov 2016；0/6目前为止）。B=成交量自相关（intraday_volume_profile_1m，未配对过）。假设：缺口大(A高)且成交量呈现持续性(B高)=延续；本条为该腿最后一批诊断性测试，与前5次partner完全不同的信息面。",
        "expected_sign": 1,
    },
    {
        "id": "KH2",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _CAT_DD60,
        "mechanism": "beta_gap_confirmed_by_category_drawdown_60",
        "hypothesis": "A=同上。B=所属板块60日回撤深度（category_state，未配对过）。假设：缺口大(A高)且板块处深回撤(B高)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    # ---- JUMP_BETA_STABILITY_20: 0/6 so far, last 2-partner diversity check ----
    {
        "id": "KI1",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _LBAR_OVERNIGHT,
        "mechanism": "jump_beta_stability_confirmed_by_bigbar_overnight",
        "hypothesis": "A=跳跃beta估计不确定性（0/6目前为止）。B=大bar隔夜分量（largebar_footprint_1m，未配对过）。假设：估计不确定性高(A高)且隔夜大bar分量高(B高)=不确定性来自隔夜信息冲击，延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "KI2",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _TICK_IMB,
        "mechanism": "jump_beta_stability_confirmed_by_tick_imbalance",
        "hypothesis": "A=同上。B=1m order flow不平衡（bar_size_order_flow，与KF1相同partner但配不同左腿，非重复候选）。假设：估计不确定性高(A高)且买卖单不平衡明显(B高)=延续；诊断性测试，本腿最后一批。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
