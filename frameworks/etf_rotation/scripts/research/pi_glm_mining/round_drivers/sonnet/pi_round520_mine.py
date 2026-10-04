#!/usr/bin/env python3
"""Round 520 driver: S4 stage step 2 -- jump_continuous_beta pairing expansion.

round_519 tested 5 atomic + 9 directed pairings (3 partners each for the 3
non-shadow atoms JUMP_BETA_20/BETA_GAP_20/JUMP_BETA_STABILITY_20; 0 partners
for the 2 shadow-flagged atoms CONTINUOUS_BETA_20/60). Result: 2/14 admitted
(JB2=CONTINUOUS_BETA_60 atomic, JC1=JUMP_BETA_20 x VOL_SPIKE_FREQ_20,
t=4.10) -- unlike S3's intraday_momentum_30m cluster (11/11 reskinned
admissions, controller audit found 0 significant), this family's first
pairing batch produced one of its strongest hits of the whole S-stage
history. That is evidence the leg carries real information, not a
degenerate single-leg artifact, so this round extends (does not repeat) the
per-leg partner set: cap raised from 3 to 5 partners per left leg, and the
previously-atomic-only CONTINUOUS_BETA_20/60 legs get their first pairings.
No pair below duplicates a round_519 pair; no same-family pairs (both legs
from jump_continuous_beta); no window variants.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_520"

_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_VOL_PROFILE_DIST = {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_LBAR_CLOCK = {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"}
_BIGBAR_VOL = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_WORST_DAY = {"name": "WORST_DAY_20", "source": "return_tail_shape"}

_JB20 = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_BGAP20 = {"name": "BETA_GAP_20", "source": "jump_continuous_beta"}
_JBSTAB20 = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}
_CBETA20 = {"name": "CONTINUOUS_BETA_20", "source": "jump_continuous_beta"}
_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}

base.CANDIDATES = [
    # ---- JUMP_BETA_20: partners #4-5 (round_519 already used VOL_SPIKE_FREQ_20,
    # CATEGORY_VOL_20, GAP_FILL_FRACTION_60 -- all excluded here) ----
    {
        "id": "KA1",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _OPEN30,
        "mechanism": "jump_beta_confirmed_by_open30_vol_share",
        "hypothesis": "A=跳跃分量beta（round_519体检disc-0.0612/审计-0.0183，非shadow；round_519配对JC1[x VOL_SPIKE_FREQ_20]t=4.10审超+17.9bp入选，证明该腿非退化）。B=开盘30分钟成交占比（round_507/508本线最强confirming partner，disc-0.1173/审计-0.0476）。假设：跳跃期系统性暴露高(A高)且开盘集中放量(B高)=暴露在开盘即被快速定价确认，延续。第4个partner，非round_519重复。",
        "expected_sign": 1,
    },
    {
        "id": "KA2",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _LOG_AMT,
        "mechanism": "jump_beta_confirmed_by_high_activity",
        "hypothesis": "A=同上。B=对数成交额（本线历史最强单腿之一，disc+0.0661/审计+0.0701/t=2.23/审超+36.8bp）。假设：跳跃期系统性暴露高(A高)且整体活跃度高(B高)=暴露有充分流动性支持定价效率，延续。第5个partner。",
        "expected_sign": 1,
    },
    # ---- BETA_GAP_20: partners #4-5 (round_519 used OPEN30_VOL_SHARE_20,
    # VOL_PROFILE_DISTANCE, CATEGORY_VOL_20 -- all excluded here) ----
    {
        "id": "KB1",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _GAP_FILL,
        "mechanism": "beta_gap_confirmed_by_gap_absorption",
        "hypothesis": "A=崩盘beta缺口（round_519体检disc-0.0459/审计+0.0148，非shadow）。B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：缺口大(A高)且缺口易回补(B高)=系统性风险差异连同流动性缺口一起被快速吸收，延续。第4个partner。",
        "expected_sign": 1,
    },
    {
        "id": "KB2",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _VOL_SPIKE,
        "mechanism": "beta_gap_confirmed_by_volume_spike_freq",
        "hypothesis": "A=同上。B=成交量脉冲频率（round_519同一partner曾与JUMP_BETA_20配对产出本轮最强入选JC1，t=4.10，验证该partner与跳跃/beta机制族有真实confirming关系）。假设：缺口大(A高)且脉冲放量频繁(B高)=延续。第5个partner；不同左腿避免重skin。",
        "expected_sign": 1,
    },
    # ---- JUMP_BETA_STABILITY_20: partners #4-5 (round_519 used GAP_FILL_FRACTION_60,
    # LOG_AMOUNT_VOL_20, VOL_SPIKE_FREQ_20 -- all excluded here) ----
    {
        "id": "KC1",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _OPEN30,
        "mechanism": "jump_beta_stability_confirmed_by_open30_vol_share",
        "hypothesis": "A=跳跃beta估计不确定性（round_519体检disc-0.0679/审计-0.0160，非shadow）。B=开盘30分钟成交占比（本线最强confirming partner之一）。假设：估计不确定性高(A高)且开盘集中放量(B高)=不确定性在开盘时段被快速纠正，延续。第4个partner。",
        "expected_sign": 1,
    },
    {
        "id": "KC2",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _VOL_PROFILE_DIST,
        "mechanism": "jump_beta_stability_confirmed_by_volume_profile_shift",
        "hypothesis": "A=同上。B=日内成交量分布偏离（round_053门7全过，本线最高t单原子t=4.04）。假设：估计不确定性高(A高)且日内成交结构异常(B高)=延续。第5个partner。",
        "expected_sign": 1,
    },
    # ---- CONTINUOUS_BETA_20: first pairing batch (atomic-only in round_519,
    # shadow-flagged vs benchmark_leadlag_1m:SYNC_BETA_20 at 0.74 in atom_health,
    # but the OFFICIAL dedup gate only checks shelf16+prior-admitted; JB2
    # (CONTINUOUS_BETA_60 atomic) already cleared that gate at 0.646<0.70
    # despite an analogous atom_health shadow flag, so pairing is still worth
    # testing empirically rather than pre-excluding on the diagnostic alone) ----
    {
        "id": "KD1",
        "operator": "rank_spread",
        "left": _CBETA20,
        "right": _VOL_SPIKE,
        "mechanism": "continuous_beta20_confirmed_by_volume_spike_freq",
        "hypothesis": "A=连续分量beta，20日窗（Todorov-Bollerslev 2010；去噪版市场beta）。B=成交量脉冲频率。假设：常态系统性暴露高(A高)且脉冲放量频繁(B高)=常态beta暴露有交易活动确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KD2",
        "operator": "rank_spread",
        "left": _CBETA20,
        "right": _CATEGORY_VOL,
        "mechanism": "continuous_beta20_confirmed_by_category_vol",
        "hypothesis": "A=同上。B=同类别板块波动率（round_053门7全过）。假设：常态系统性暴露高(A高)且所属板块高波动(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KD3",
        "operator": "rank_spread",
        "left": _CBETA20,
        "right": _GAP_FILL,
        "mechanism": "continuous_beta20_confirmed_by_gap_absorption",
        "hypothesis": "A=同上。B=缺口回补比例。假设：常态系统性暴露高(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KD4",
        "operator": "rank_spread",
        "left": _CBETA20,
        "right": _LBAR_CLOCK,
        "mechanism": "continuous_beta20_confirmed_by_lbar_clock_std",
        "hypothesis": "A=同上。B=大bar发生时点的20日标准差（largebar_footprint_1m通道原子，已验证）。假设：常态系统性暴露高(A高)且大bar发生时点分散度低(B低，时点集中)反映规律性冲击结构，本条用B原始方向（不反号）：B高(时点分散)=噪声更多，延续方向按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KD5",
        "operator": "rank_spread",
        "left": _CBETA20,
        "right": _BIGBAR_VOL,
        "mechanism": "continuous_beta20_confirmed_by_bigbar_vol_share",
        "hypothesis": "A=同上。B=大bar成交量占比（bar_size_order_flow通道原子，已验证，round_053系入选史)。假设：常态系统性暴露高(A高)且大bar贡献成交量占比高(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- CONTINUOUS_BETA_60: first pairing batch ----
    {
        "id": "KE1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _OPEN30,
        "mechanism": "continuous_beta60_confirmed_by_open30_vol_share",
        "hypothesis": "A=连续分量beta，60日窗（JB2在round_519以atomic形式已入选：disc-0.1155/审计-0.0875）。B=开盘30分钟成交占比。假设：常态系统性暴露高(A高)且开盘集中放量(B高)=延续。JB2已入选表明该腿本身携带真实信息，此处测试是否有confirming partner能提升门7边际。",
        "expected_sign": 1,
    },
    {
        "id": "KE2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _VOL_PROFILE_DIST,
        "mechanism": "continuous_beta60_confirmed_by_volume_profile_shift",
        "hypothesis": "A=同上。B=日内成交量分布偏离（本线最高t单原子）。假设：延续。",
        "expected_sign": 1,
    },
    {
        "id": "KE3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _LOG_AMT,
        "mechanism": "continuous_beta60_confirmed_by_high_activity",
        "hypothesis": "A=同上。B=对数成交额。假设：延续。",
        "expected_sign": 1,
    },
    {
        "id": "KE4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _LBAR_CLOCK,
        "mechanism": "continuous_beta60_confirmed_by_lbar_clock_std",
        "hypothesis": "A=同上。B=大bar发生时点的20日标准差。假设：延续，方向按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KE5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _WORST_DAY,
        "mechanism": "continuous_beta60_confirmed_by_worst_day",
        "hypothesis": "A=同上。B=20日最差单日收益（return_tail_shape已验证原子，下行尾代表）。假设：常态系统性暴露高(A高)且下行尾更极端(B更负，即rank更低)=A高B低应更延续下修；用rank_spread(A,B)，符号按discovery定，不预设强先验，仅作探索性confirming测试。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
