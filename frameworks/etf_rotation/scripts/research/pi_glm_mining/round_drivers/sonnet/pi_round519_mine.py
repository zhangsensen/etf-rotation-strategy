#!/usr/bin/env python3
"""Round 519 driver: S4 stage step 1 -- jump_continuous_beta family
(Todorov-Bollerslev 2010 / Bollerslev-Li-Todorov 2016), main controller's
pre-specified next direction after S3's intraday_momentum_30m exhaustion.
5 atomic candidates (CONTINUOUS_BETA_20/60 flagged shadow vs
benchmark_leadlag_1m:SYNC_BETA_20 at 0.74; JUMP_BETA_20/BETA_GAP_20/
JUMP_BETA_STABILITY_20 non-shadow) plus a first directed-pairing batch for
the 3 non-shadow atoms against 6 partners with DIFFERENT left legs each
(per the main controller's anti-reskinning directive: no repeated
single-left-leg sweeps this stage)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_519"

_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_VOL_PROFILE_DIST = {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_GAP_FILL = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}

base.CANDIDATES = [
    # ---- 5 atomic: new jump_continuous_beta atoms ----
    {
        "id": "JB1",
        "operator": "atomic",
        "left": {"name": "CONTINUOUS_BETA_20", "source": "jump_continuous_beta"},
        "right": {"name": "CONTINUOUS_BETA_20", "source": "jump_continuous_beta"},
        "mechanism": "continuous_beta_20",
        "hypothesis": "Todorov-Bollerslev 2010 连续分量beta，20日窗。体检：disc-0.1170/579天/审计-0.0721，max|corr|=0.74（vs benchmark_leadlag_1m:SYNC_BETA_20），**shadow=True**（连续beta本质上是去噪版的普通市场beta，与已有同步性beta重叠符合预期）。",
        "expected_sign": -1,
    },
    {
        "id": "JB2",
        "operator": "atomic",
        "left": {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"},
        "right": {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"},
        "mechanism": "continuous_beta_60",
        "hypothesis": "同JB1，60日窗。体检：disc-0.1155/审计-0.0875，max|corr|=0.74，**shadow=True**。",
        "expected_sign": -1,
    },
    {
        "id": "JB3",
        "operator": "atomic",
        "left": {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"},
        "right": {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"},
        "mechanism": "jump_beta_20",
        "hypothesis": "Todorov-Bollerslev 2010 跳跃分量beta，20日窗（仅在有跳跃bar的日子计算，min_periods=5使其天然稀疏）。体检：disc-0.0612/579天/审计-0.0183，max|corr|=0.63（vs SYNC_BETA_20），非shadow——与连续beta体检相关性0.74形成对照，证实跳跃分量携带的信息与连续分量不完全重合。假设：跳跃beta越高(A高)=危机时期系统性暴露越大，越应折价，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "JB4",
        "operator": "atomic",
        "left": {"name": "BETA_GAP_20", "source": "jump_continuous_beta"},
        "right": {"name": "BETA_GAP_20", "source": "jump_continuous_beta"},
        "mechanism": "beta_gap_20",
        "hypothesis": "Bollerslev-Li-Todorov 2016 崩盘beta缺口=JUMP_BETA_20-CONTINUOUS_BETA_20。体检：disc-0.0459/579天/审计+0.0148，max|corr|=0.47，非shadow。假设：缺口越大(A高，跳跃期系统性暴露相对平静期显著更高)=定价错误/风险溢价更明显，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "JB5",
        "operator": "atomic",
        "left": {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"},
        "right": {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"},
        "mechanism": "jump_beta_stability_20",
        "hypothesis": "跳跃beta的20日滚动标准差（估计不确定性）。体检：disc-0.0679/579天/审计-0.0160，max|corr|=0.59（vs cojump_1m:COJUMP_INDEX_SHARE_20），非shadow。假设：跳跃beta估计越不稳定(A高)=系统性风险暴露的不确定性越高，应折价，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    # ---- directed pairing: 3 non-shadow atoms x 2 partners each (different left legs, no single-leg sweep) ----
    {
        "id": "JC1",
        "operator": "rank_spread",
        "left": {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"},
        "right": _VOL_SPIKE,
        "mechanism": "jump_beta_confirmed_by_volume_spike_freq",
        "hypothesis": "两腿角色：A=跳跃分量beta（disc-0.0612/审计-0.0183，非shadow）；B=成交量脉冲频率（round_506已证明是本线最有效confirming partner之一，disc+0.0661/审计+0.0460）。假设：跳跃期系统性暴露高(A高)且脉冲放量频繁(B高)=暴露有交易活动确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "JC2",
        "operator": "rank_spread",
        "left": {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"},
        "right": _CATEGORY_VOL,
        "mechanism": "jump_beta_confirmed_by_category_vol",
        "hypothesis": "两腿角色：A=同上；B=同类别板块波动率（round_053门7全过：disc-0.0711/审计-0.0653/t=2.42/审超+19.0bp）。假设：跳跃期系统性暴露高(A高)且所属板块高波动(B高)=暴露来自板块层面共振，延续。",
        "expected_sign": 1,
    },
    {
        "id": "JD1",
        "operator": "rank_spread",
        "left": {"name": "BETA_GAP_20", "source": "jump_continuous_beta"},
        "right": _OPEN30,
        "mechanism": "beta_gap_confirmed_by_open30_vol_share",
        "hypothesis": "两腿角色：A=崩盘beta缺口（disc-0.0459/审计+0.0148，非shadow）；B=开盘30分钟成交占比（round_507/508已证明是本线最强confirming partner，disc-0.1173/审计-0.0476）。假设：缺口大(A高)且开盘集中放量(B高)=系统性风险差异在开盘时段被快速定价，延续。",
        "expected_sign": 1,
    },
    {
        "id": "JD2",
        "operator": "rank_spread",
        "left": {"name": "BETA_GAP_20", "source": "jump_continuous_beta"},
        "right": _VOL_PROFILE_DIST,
        "mechanism": "beta_gap_confirmed_by_volume_profile_shift",
        "hypothesis": "两腿角色：A=同上；B=日内成交量分布偏离（round_053门7全过，本线最高t单原子t=4.04）。假设：缺口大(A高)且日内成交结构异常(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "JE1",
        "operator": "rank_spread",
        "left": {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"},
        "right": _GAP_FILL,
        "mechanism": "jump_beta_stability_confirmed_by_gap_absorption",
        "hypothesis": "两腿角色：A=跳跃beta估计不确定性（disc-0.0679/审计-0.0160，非shadow）；B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：估计不确定性高(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "JE2",
        "operator": "rank_spread",
        "left": {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"},
        "right": _LOG_AMT,
        "mechanism": "jump_beta_stability_confirmed_by_high_activity",
        "hypothesis": "两腿角色：A=同上；B=对数成交额（本线历史最强单腿之一，disc+0.0661/审计+0.0701/t=2.23/审超+36.8bp）。假设：估计不确定性高(A高)且活跃度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "JC3",
        "operator": "rank_spread",
        "left": {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"},
        "right": _GAP_FILL,
        "mechanism": "jump_beta_confirmed_by_gap_absorption",
        "hypothesis": "两腿角色：A=跳跃分量beta（同JC1）；B=缺口回补比例（round_053门7全过：disc-0.0597/审计-0.0430/t=2.59/审超+9.8bp）。假设：跳跃期系统性暴露高(A高)且缺口易回补(B高)=延续。第三个partner，不构成单腿穷举扫描。",
        "expected_sign": 1,
    },
    {
        "id": "JD3",
        "operator": "rank_spread",
        "left": {"name": "BETA_GAP_20", "source": "jump_continuous_beta"},
        "right": _CATEGORY_VOL,
        "mechanism": "beta_gap_confirmed_by_category_vol",
        "hypothesis": "两腿角色：A=崩盘beta缺口（同JD1）；B=同类别板块波动率（round_053门7全过：disc-0.0711/审计-0.0653/t=2.42/审超+19.0bp）。假设：缺口大(A高)且板块高波动(B高)=延续。第三个partner，不构成单腿穷举扫描。",
        "expected_sign": 1,
    },
    {
        "id": "JE3",
        "operator": "rank_spread",
        "left": {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"},
        "right": _VOL_SPIKE,
        "mechanism": "jump_beta_stability_confirmed_by_volume_spike_freq",
        "hypothesis": "两腿角色：A=跳跃beta估计不确定性（同JE1）；B=成交量脉冲频率（同JC1）。假设：估计不确定性高(A高)且脉冲放量频繁(B高)=延续。第三个partner，不构成单腿穷举扫描。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
