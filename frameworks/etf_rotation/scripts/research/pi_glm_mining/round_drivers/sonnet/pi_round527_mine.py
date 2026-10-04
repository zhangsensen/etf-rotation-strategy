#!/usr/bin/env python3
"""Round 527 driver: S4 stage step 9 -- jump_continuous_beta pairing, round 9.

Eight-round scoreboard (round_519-526, 123 candidates, 11 net admissions,
no three-zero streak). CONTINUOUS_BETA_60 is the sole leg still producing
admissions (7 net hits across asymmetry, serial-dependence/ACF1, and
realized-measures/microstructure channels); JUMP_BETA_20, BETA_GAP_20,
JUMP_BETA_STABILITY_20, CONTINUOUS_BETA_20 are all closed after 6-9 rounds
of diverse-theme diagnostics each.

This round exhausts the remaining catalog families that have NEVER been
paired with CONTINUOUS_BETA_60 (or, for a few specific atoms, with any
jump_continuous_beta leg at all): cross_dependence_1m (Granger causality /
net spillover -- directly about systemic linkage structure, conceptually
close to a systematic-beta leg), peer_relative_value (cointegration-style
residual/half-life vs peers), intraday_periodicity (time-of-day patterns,
including TAIL30_BETA_FULL_20 which is itself a beta-shaped construct --
worth testing for genuine complementarity vs redundancy), the one
never-paired cojump_1m atom (COJUMP_INDEX_SHARE_20 -- the other two atoms
in this family were already used with JUMP_BETA_STABILITY_20 in round_522,
but this one was skipped), the two never-paired liquidity_commonality_1m
atoms (LIQ_COMMON_BETA_20/R2_20 -- RESILIENCY_20/IDIO_LIQ_SHOCK_Z_20 from
the same family were used with JUMP_BETA_STABILITY_20 in round_522, but
these two beta/R2 atoms were never paired with any jump_continuous_beta
leg), and a subset of fund_flow/nav_premium (fund-share and NAV-premium
flow atoms, never touched by this family).

After this round, essentially every catalog family will have been tested
against CONTINUOUS_BETA_60 at least once -- if this round returns few/no
admissions, the next round should assess whether the stage's productive
channel is genuinely thinning toward a 3-zero exhaustion read rather than
continuing to add marginal families.

All (left,right) combos below are new. No same-family pairs, no window
variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_527"

_GRANGER_OUT = {"name": "GRANGER_OUT_DEGREE_20", "source": "cross_dependence_1m"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_NET_SPILLOVER = {"name": "NET_SPILLOVER_20", "source": "cross_dependence_1m"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}

_PEER_RESID_Z = {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"}
_PEER_RESID_MOM = {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_PEER_RELSTR_Z = {"name": "PEER_RELSTR_Z_20", "source": "peer_relative_value"}

_HKS_SLOT = {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"}
_OVERNIGHT_DIFF = {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"}
_TAIL30_BETA_FULL = {"name": "TAIL30_BETA_FULL_20", "source": "intraday_periodicity"}

_COJUMP_INDEX = {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"}
_LIQ_COMMON_BETA = {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"}
_LIQ_COMMON_R2 = {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"}

_SHARE_CHG20 = {"name": "SHARE_CHG_20", "source": "fund_flow"}
_SHARE_Z60 = {"name": "SHARE_Z_60", "source": "fund_flow"}
_SHARE_RET_CORR = {"name": "SHARE_RET_CORR_20", "source": "fund_flow"}

_PREMIUM_Z20 = {"name": "PREMIUM_Z_20", "source": "nav_premium"}
_PREM_SHARE_ALIGNED = {"name": "PREM_SHARE_ALIGNED_20", "source": "nav_premium"}

_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}

base.CANDIDATES = [
    # ---- cross_dependence_1m: Granger causality / spillover, conceptually
    # close to a systematic-beta leg's information content ----
    {
        "id": "KW1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _GRANGER_OUT,
        "mechanism": "continuous_beta60_confirmed_by_granger_out_degree",
        "hypothesis": "A=连续分量beta，60日窗（7次净入选，横跨asymmetry/serial-dependence/realized-measures/microstructure四个渠道）。B=格兰杰因果出度（cross_dependence_1m，本族首次使用；衡量该ETF对其他篮子成员的领先影响力）。假设：常态系统性暴露高(A高)且对同伴有更强格兰杰领先性(B高)=该资产是系统性信息的传导源而非被动接受者，延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KW2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _GRANGER_IN,
        "mechanism": "continuous_beta60_confirmed_by_granger_in_degree",
        "hypothesis": "A=同上。B=格兰杰因果入度（本族首次使用；衡量该ETF被其他篮子成员领先影响的程度）。假设：常态系统性暴露高(A高)且被同伴领先影响强(B高，被动接受系统性信息)=延续；与KW1互补（领先vs滞后两个方向）。",
        "expected_sign": 1,
    },
    {
        "id": "KW3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _NET_SPILLOVER,
        "mechanism": "continuous_beta60_confirmed_by_net_spillover",
        "hypothesis": "A=同上。B=净溢出效应（出度减入度的净方向，本族首次使用）。假设：常态系统性暴露高(A高)且净溢出为正(B高，净输出信息)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KW4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _DEP_DRIFT,
        "mechanism": "continuous_beta60_confirmed_by_dependency_drift",
        "hypothesis": "A=同上。B=依赖结构20日漂移（跨资产依赖关系的时变性，本族首次使用）。假设：常态系统性暴露高(A高)且依赖结构正在漂移(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    # ---- peer_relative_value: cointegration-style residual vs peers ----
    {
        "id": "KX1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PEER_RESID_Z,
        "mechanism": "continuous_beta60_confirmed_by_peer_resid_z",
        "hypothesis": "A=同上。B=相对同伴的协整残差z值（peer_relative_value，本族首次使用）。假设：常态系统性暴露高(A高)且相对同伴出现正向偏离(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KX2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PEER_RESID_MOM,
        "mechanism": "continuous_beta60_confirmed_by_peer_resid_momentum",
        "hypothesis": "A=同上。B=协整残差的动量（残差是否持续扩大，本族首次使用）。假设：常态系统性暴露高(A高)且残差动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KX3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "continuous_beta60_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=OU过程回归半衰期（残差均值回复速度，本族首次使用）。假设：常态系统性暴露高(A高)且回复速度慢(B高，半衰期长)=定价偏离更持久，延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KX4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PEER_RELSTR_Z,
        "mechanism": "continuous_beta60_confirmed_by_peer_relative_strength",
        "hypothesis": "A=同上。B=相对同伴强弱的z值（peer_relative_value，本族首次使用）。假设：常态系统性暴露高(A高)且相对强弱异常(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- intraday_periodicity: time-of-day patterns; TAIL30_BETA_FULL_20
    # is itself a beta-shaped construct, direct redundancy test ----
    {
        "id": "KY1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _HKS_SLOT,
        "mechanism": "continuous_beta60_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=同上。B=日内时段模式持续性（intraday_periodicity，本族首次使用）。假设：常态系统性暴露高(A高)且日内时段模式稳定(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KY2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _OVERNIGHT_DIFF,
        "mechanism": "continuous_beta60_confirmed_by_overnight_intra_diff",
        "hypothesis": "A=同上。B=隔夜与日内收益差异（intraday_periodicity，本族首次使用）。假设：常态系统性暴露高(A高)且隔夜/日内收益分化明显(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KY3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _TAIL30_BETA_FULL,
        "mechanism": "continuous_beta60_confirmed_by_tail30_beta_full",
        "hypothesis": "A=同上。B=尾盘30分钟beta相对全天beta的比值（intraday_periodicity，本族首次使用；本身也是beta构造，与A是同概念不同时段切片的直接冗余检验)。假设：常态系统性暴露高(A高)且尾盘beta占比高(B高)=系统性暴露集中在尾盘定价，用rank_spread测试是否有增量而非纯冗余（预期本条最可能被redundancy拒绝，作为诊断性对照）。",
        "expected_sign": 1,
    },
    # ---- one never-paired cojump_1m atom, two never-paired
    # liquidity_commonality_1m atoms ----
    {
        "id": "KZ1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _COJUMP_INDEX,
        "mechanism": "continuous_beta60_confirmed_by_cojump_index_share",
        "hypothesis": "A=同上。B=共跳占指数跳跃比例（cojump_1m，该家族另两个原子已与JUMP_BETA_STABILITY_20配过，此原子对本族任何腿都是首次；契约明确将cojump_1m列为本家族的shadow参照家族之一）。假设：常态系统性暴露高(A高)且与指数共跳比例高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KZ2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _LIQ_COMMON_BETA,
        "mechanism": "continuous_beta60_confirmed_by_liquidity_common_beta",
        "hypothesis": "A=同上。B=流动性共性beta（liquidity_commonality_1m，本族任何腿首次使用；同族的RESILIENCY_20/IDIO_LIQ_SHOCK_Z_20此前只配过JUMP_BETA_STABILITY_20）。假设：常态系统性暴露高(A高)且流动性共性beta高(B高，流动性也随大盘系统性变化)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KZ3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _LIQ_COMMON_R2,
        "mechanism": "continuous_beta60_confirmed_by_liquidity_common_r2",
        "hypothesis": "A=同上。B=流动性共性回归R2（liquidity_commonality_1m，本族任何腿首次使用）。假设：常态系统性暴露高(A高)且流动性共性解释力强(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- fund_flow / nav_premium: fund-share and NAV-premium flow, never
    # touched by this family ----
    {
        "id": "LA1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _SHARE_CHG20,
        "mechanism": "continuous_beta60_confirmed_by_share_change_20",
        "hypothesis": "A=同上。B=基金份额20日变化（fund_flow，本族首次使用）。假设：常态系统性暴露高(A高)且份额扩张(B高，资金净申购)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LA2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _SHARE_Z60,
        "mechanism": "continuous_beta60_confirmed_by_share_z_60",
        "hypothesis": "A=同上。B=份额变化60日z值（fund_flow，本族首次使用）。假设：常态系统性暴露高(A高)且份额异常扩张(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LA3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _SHARE_RET_CORR,
        "mechanism": "continuous_beta60_confirmed_by_share_return_corr",
        "hypothesis": "A=同上。B=份额变化与收益的相关性（fund_flow，本族首次使用）。假设：常态系统性暴露高(A高)且份额与收益同步性强(B高，资金追涨)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LB1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PREMIUM_Z20,
        "mechanism": "continuous_beta60_confirmed_by_premium_z_20",
        "hypothesis": "A=同上。B=净值溢价20日z值（nav_premium，本族首次使用）。假设：常态系统性暴露高(A高)且溢价异常走高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LB2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PREM_SHARE_ALIGNED,
        "mechanism": "continuous_beta60_confirmed_by_premium_share_aligned",
        "hypothesis": "A=同上。B=溢价与份额变化的一致性（nav_premium，本族首次使用；衡量套利机制是否有效运作）。假设：常态系统性暴露高(A高)且溢价-份额一致性强(B高，套利机制活跃)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
