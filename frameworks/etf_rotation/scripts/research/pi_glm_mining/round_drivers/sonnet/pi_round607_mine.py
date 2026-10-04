#!/usr/bin/env python3
"""Round 607 driver: S25 stage step 2 -- second cross-stage top-atom
pairing scan, round 2. Uses 5 of the pool's remaining 10 not-yet-left
atoms as this round's left legs -- specifically the 4 atoms that hit
their 3x right-leg usage cap in round_606 (JUMP_BETA_20, D1_1M_20,
GAP_SESSION_CORR_20, PEER_OU_HALFLIFE_20) plus OVERNIGHT_FIRST30_CORR_20
(2/3 used) -- since these atoms have little or no remaining right-leg
capacity, using them as LEFT legs now is the most capacity-efficient
way to keep mining them. Right legs drawn from the atoms with spare
capacity (DEP_DRIFT_20, GRANGER_IN_DEGREE_20, YZ_OVERNIGHT_SHARE_20,
MFI_EXTREME_TOD_SKEW_20, VOL_SPIKE_FREQ_20, AD_NET_FLOW_20,
LUNCH_PRERUN_POSTRUN_RATIO_20, MFI_EXTREME_FRAC_20, VT_AUTOCORR_20,
VT_UNDERWATER_FRAC_20), all checked by hand against both round_606's
pairs AND this line's full prior-round history (D1_1M_20 x
AD_NET_FLOW_20 was excluded as it duplicates round_587's admitted DB3;
VT_AUTOCORR_20 x LUNCH_PRERUN_POSTRUN_RATIO_20 excluded as it duplicates
round_603's admitted XB3) to avoid exact-duplicate candidates. Batch
sizes vary (2-4 rights) to respect each right atom's remaining 3x cap
exactly. Remaining 5 pool atoms (VOL_SPIKE_FREQ_20, AD_NET_FLOW_20,
MFI_EXTREME_TOD_SKEW_20, LUNCH_PRERUN_POSTRUN_RATIO_20,
MFI_EXTREME_FRAC_20) still need their own left-leg batch in a future
round to fully exhaust the pool."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_607"

_OVERNIGHT_FIRST30 = {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"}
_JUMP_BETA = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_D1_1M = {"name": "D1_1M_20", "source": "price_delay"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}

_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_GRANGER = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_YZ_OVERNIGHT = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_MFI_TOD_SKEW = {"name": "MFI_EXTREME_TOD_SKEW_20", "source": "money_flow_extremes_1m"}
_VOL_SPIKE_FREQ = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}
_LUNCH_PRERUN_POSTRUN = {"name": "LUNCH_PRERUN_POSTRUN_RATIO_20", "source": "lunch_break_1m"}
_MFI_EXTREME_FRAC = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_VT_UNDERWATER = {"name": "VT_UNDERWATER_FRAC_20", "source": "volume_time_drawdown"}

base.CANDIDATES = [
    # ---- VOL_SPIKE_FREQ_20: S25 second-batch left leg (OVERNIGHT_FIRST30_CORR_20 dropped as
    # left -- its extensive S3-era pairing history made every attempted right leg here collide
    # with an already-tested combo; substituted with a fresher pool atom instead) ----
    {"id": "ZF1", "operator": "rank_spread", "left": _VOL_SPIKE_FREQ, "right": _DEP_DRIFT,
     "mechanism": "s25_vol_spike_freq_vs_dep_drift",
     "hypothesis": "A=成交量突增频率(intraday_volume_profile_1m,t=4.10，含量原子)。B=跨ETF依赖漂移(cross_dependence_1m,本线历史最高t原子之一,t=4.88)。假设方向探索性，由发现期定。（原计划的左腿OVERNIGHT_FIRST30_CORR_20因历史配对饱和连续两次命中哈希碰撞，已整体改用VOL_SPIKE_FREQ_20作左腿）",
     "expected_sign": -1},
    {"id": "ZF2", "operator": "rank_spread", "left": _VOL_SPIKE_FREQ, "right": _MFI_EXTREME_FRAC,
     "mechanism": "s25_vol_spike_freq_vs_mfi_extreme_frac",
     "hypothesis": "A=同上。B=MFI极端占比(accumulation_distribution_1m,t=4.88，含量原子，与A不同族)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZF3", "operator": "rank_spread", "left": _VOL_SPIKE_FREQ, "right": _LUNCH_PRERUN_POSTRUN,
     "mechanism": "s25_vol_spike_freq_vs_lunch_prerun_postrun_ratio",
     "hypothesis": "A=同上。B=午前/午后抢跑成交量份额之比(S22原子级入选KA7,lunch_break_1m,t=5.48，含量原子)。假设方向探索性。本批最后一条。",
     "expected_sign": -1},
    # ---- JUMP_BETA_20: S25 second-batch left leg ----
    {"id": "ZG1", "operator": "rank_spread", "left": _JUMP_BETA, "right": _YZ_OVERNIGHT,
     "mechanism": "s25_jump_beta_vs_yz_overnight_share",
     "hypothesis": "A=跳跃beta(S4,jump_continuous_beta,t=4.10)。B=Yang-Zhang隔夜方差份额(S9,range_based_vol_1m,t=3.95)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZG2", "operator": "rank_spread", "left": _JUMP_BETA, "right": _VT_UNDERWATER,
     "mechanism": "s25_jump_beta_vs_vt_underwater_frac",
     "hypothesis": "A=同上。B=成交量时间水下占比(S23阶段最强候选WA1的左腿,volume_time_drawdown,t=4.11)。假设方向探索性。（原计划的VOL_SPIKE_FREQ_20搭档在plan锁定时命中既有哈希碰撞，已替换为本条）",
     "expected_sign": -1},
    {"id": "ZG3", "operator": "rank_spread", "left": _JUMP_BETA, "right": _AD_NET_FLOW,
     "mechanism": "s25_jump_beta_vs_ad_net_flow",
     "hypothesis": "A=同上。B=A/D净流(accumulation_distribution_1m,t=3.96，含量原子)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZG4", "operator": "rank_spread", "left": _JUMP_BETA, "right": _LUNCH_PRERUN_POSTRUN,
     "mechanism": "s25_jump_beta_vs_lunch_prerun_postrun_ratio",
     "hypothesis": "A=同上。B=午前/午后抢跑成交量份额之比(S22原子级入选KA7,lunch_break_1m,t=5.48，含量原子)。假设方向探索性。本批最后一条。",
     "expected_sign": -1},
    # ---- D1_1M_20: S25 second-batch left leg ----
    {"id": "ZH1", "operator": "rank_spread", "left": _D1_1M, "right": _MFI_TOD_SKEW,
     "mechanism": "s25_d1_1m_vs_mfi_extreme_tod_skew",
     "hypothesis": "A=1m频价格延迟D1水平(S20,price_delay,t=3.96)。B=MFI极端值时段偏度(money_flow_extremes_1m,t=3.95，含量原子)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZH2", "operator": "rank_spread", "left": _D1_1M, "right": _MFI_EXTREME_FRAC,
     "mechanism": "s25_d1_1m_vs_mfi_extreme_frac",
     "hypothesis": "A=同上。B=MFI极端占比(accumulation_distribution_1m,t=4.88，含量原子；本轮避开与AD_NET_FLOW_20配对，因该组合已在round_587以DB3入选，属重复候选)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZH3", "operator": "rank_spread", "left": _D1_1M, "right": _LUNCH_PRERUN_POSTRUN,
     "mechanism": "s25_d1_1m_vs_lunch_prerun_postrun_ratio",
     "hypothesis": "A=同上。B=午前/午后抢跑成交量份额之比(S22原子级入选KA7,lunch_break_1m,t=5.48，含量原子)。假设方向探索性。本批最后一条。",
     "expected_sign": -1},
    # ---- GAP_SESSION_CORR_20: S25 second-batch left leg ----
    {"id": "ZI1", "operator": "rank_spread", "left": _GAP_SESSION_CORR, "right": _MFI_EXTREME_FRAC,
     "mechanism": "s25_gap_session_corr_vs_mfi_extreme_frac",
     "hypothesis": "A=跳空与session收益相关(gap_response,t=3.89)。B=MFI极端占比(accumulation_distribution_1m,t=4.88，含量原子)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZI2", "operator": "rank_spread", "left": _GAP_SESSION_CORR, "right": _VT_AUTOCORR,
     "mechanism": "s25_gap_session_corr_vs_vt_autocorr",
     "hypothesis": "A=同上。B=成交量时间收益1桶滞后自相关(S24净入选簇代表XB3的左腿,volume_time_1m,t=5.48)。假设方向探索性。本批最后一条。",
     "expected_sign": -1},
    # ---- PEER_OU_HALFLIFE_20: S25 second-batch left leg ----
    {"id": "ZJ1", "operator": "rank_spread", "left": _PEER_OU_HALFLIFE, "right": _VT_AUTOCORR,
     "mechanism": "s25_peer_ou_halflife_vs_vt_autocorr",
     "hypothesis": "A=同伴OU均值回归半衰期(peer_relative_value,t=3.75)。B=成交量时间收益1桶滞后自相关(volume_time_1m,t=5.48)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZJ2", "operator": "rank_spread", "left": _PEER_OU_HALFLIFE, "right": _AD_NET_FLOW,
     "mechanism": "s25_peer_ou_halflife_vs_ad_net_flow",
     "hypothesis": "A=同上。B=A/D净流(accumulation_distribution_1m,t=3.96，含量原子)。假设方向探索性。本批最后一条，本轮末条。",
     "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
