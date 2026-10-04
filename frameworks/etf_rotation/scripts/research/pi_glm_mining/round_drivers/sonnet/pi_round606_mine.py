#!/usr/bin/env python3
"""Round 606 driver: S25 stage step 1 -- second cross-stage top-atom
pairing scan (main controller's pre-specified S25 direction after S24's
closure, round_605), covering S17-S24 new-family atoms that did not
exist during S16's first scan.

Atom pool construction: scanned every gate_pass=True row across all
outputs/round_*/candidate_metrics.csv this line has ever produced
(138 admitted rows), extracted each unique left/right atom name, took
its best (highest) block-t across all admissions, then built a 15-atom
pool with family cap <=2 and the 5 known 'redundancy magnet' atoms
(PERM_ENTROPY_RET_20, CONTINUOUS_BETA_60, RCOV_N_SHARE_20, MSPE_5M_20,
BETA_HF_20) deliberately excluded (per S21+'s established finding that
these dominate rank_correlation_redundancy rejections rather than
producing new admissions). One atom (VOL_PROFILE_DISTANCE) was dropped
for having no resolvable family config (legacy pi/GLM-line shelf atom).

Pool (15 atoms, family in parens, t = best block-t ever achieved):
LUNCH_PRERUN_POSTRUN_RATIO_20 (lunch_break_1m, t=5.48 as right leg of
S25's own XB3 -- reused here as an atom, not a repeat of that exact
pair), VT_AUTOCORR_20 (volume_time_1m, t=5.48), MFI_EXTREME_FRAC_20
(accumulation_distribution_1m, t=4.88), DEP_DRIFT_20
(cross_dependence_1m, t=4.88), OVERNIGHT_FIRST30_CORR_20
(intraday_momentum_30m, t=4.25), GRANGER_IN_DEGREE_20
(cross_dependence_1m, t=4.25), VT_UNDERWATER_FRAC_20
(volume_time_drawdown, t=4.11), VOL_SPIKE_FREQ_20
(intraday_volume_profile_1m, t=4.10), JUMP_BETA_20
(jump_continuous_beta_1m, t=4.10), D1_1M_20 (price_delay, t=3.96),
AD_NET_FLOW_20 (accumulation_distribution_1m, t=3.96),
YZ_OVERNIGHT_SHARE_20 (range_based_vol_1m, t=3.95),
MFI_EXTREME_TOD_SKEW_20 (money_flow_extremes_1m, t=3.95),
GAP_SESSION_CORR_20 (gap_response, t=3.89), PEER_OU_HALFLIFE_20
(peer_relative_value, t=3.75).

Volume-free classification (per this line's established convention:
the SIGNAL VALUE is a return/price/path statistic, not a volume level/
share/count, even if volume defines a clock): VT_AUTOCORR_20,
DEP_DRIFT_20, OVERNIGHT_FIRST30_CORR_20, GRANGER_IN_DEGREE_20,
VT_UNDERWATER_FRAC_20, JUMP_BETA_20, D1_1M_20, YZ_OVERNIGHT_SHARE_20,
GAP_SESSION_CORR_20, PEER_OU_HALFLIFE_20 (10 atoms). Volume-level:
LUNCH_PRERUN_POSTRUN_RATIO_20, MFI_EXTREME_FRAC_20, VOL_SPIKE_FREQ_20,
AD_NET_FLOW_20, MFI_EXTREME_TOD_SKEW_20 (5 atoms).

This round: 5 left-leg batches (5 rights each = 25 candidates),
volume-free x volume-free prioritized for the first 4 batches
(VT_AUTOCORR_20, VT_UNDERWATER_FRAC_20, DEP_DRIFT_20,
GRANGER_IN_DEGREE_20 as left legs), batch 5 (YZ_OVERNIGHT_SHARE_20 as
left) mixes in the 3 untouched volume-level atoms to start covering
them. Every (left,right) unordered pair checked by hand for no repeats
across the 5 batches; right-leg usage tracked to respect the 3x cap
(OVERNIGHT_FIRST30_CORR_20, JUMP_BETA_20, YZ_OVERNIGHT_SHARE_20,
D1_1M_20, GAP_SESSION_CORR_20, PEER_OU_HALFLIFE_20 each reach exactly
3 uses across this round)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_606"

_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}
_VT_UNDERWATER = {"name": "VT_UNDERWATER_FRAC_20", "source": "volume_time_drawdown"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_GRANGER = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_YZ_OVERNIGHT = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}

_OVERNIGHT_FIRST30 = {"name": "OVERNIGHT_FIRST30_CORR_20", "source": "intraday_momentum_30m"}
_JUMP_BETA = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_D1_1M = {"name": "D1_1M_20", "source": "price_delay"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_VOL_SPIKE_FREQ = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_AD_NET_FLOW = {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"}
_MFI_TOD_SKEW = {"name": "MFI_EXTREME_TOD_SKEW_20", "source": "money_flow_extremes_1m"}
_LUNCH_PRERUN_POSTRUN = {"name": "LUNCH_PRERUN_POSTRUN_RATIO_20", "source": "lunch_break_1m"}

base.CANDIDATES = [
    # ---- VT_AUTOCORR_20: S25 first pairing batch (fresh rights vs S24's) ----
    {"id": "ZA1", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _DEP_DRIFT,
     "mechanism": "s25_vt_autocorr_vs_dep_drift",
     "hypothesis": "A=成交量时间收益1桶滞后自相关(S24净入选簇代表XB3的左腿,t最高达5.48)。B=跨ETF依赖漂移(cross_dependence_1m,本线历史最高t原子之一,t=4.88)。两条均为全线顶级无量原子，此前从未配过。假设方向探索性，由发现期定。",
     "expected_sign": -1},
    {"id": "ZA2", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _OVERNIGHT_FIRST30,
     "mechanism": "s25_vt_autocorr_vs_overnight_first30_corr",
     "hypothesis": "A=同上。B=隔夜收益与首30分钟收益相关(intraday_momentum_30m,本线历史高t原子,t=4.25，此前多轮同左腿换右腿已被主控判定为同簇，此处作右腿是全新角色)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZA3", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _GRANGER,
     "mechanism": "s25_vt_autocorr_vs_granger_in_degree",
     "hypothesis": "A=同上。B=Granger因果入度(cross_dependence_1m,t=4.25)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZA4", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _JUMP_BETA,
     "mechanism": "s25_vt_autocorr_vs_jump_beta",
     "hypothesis": "A=同上。B=跳跃beta(S4,jump_continuous_beta_1m,t=4.10)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZA5", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _YZ_OVERNIGHT,
     "mechanism": "s25_vt_autocorr_vs_yz_overnight_share",
     "hypothesis": "A=同上。B=Yang-Zhang隔夜方差份额(S9,range_based_vol_1m,t=3.95)。假设方向探索性。本批最后一条。",
     "expected_sign": -1},
    # ---- VT_UNDERWATER_FRAC_20: S25 first pairing batch (fresh rights vs S23's) ----
    {"id": "ZB1", "operator": "rank_spread", "left": _VT_UNDERWATER, "right": _DEP_DRIFT,
     "mechanism": "s25_vt_underwater_frac_vs_dep_drift",
     "hypothesis": "A=成交量时间水下占比(S23阶段最强候选WA1的左腿,t=4.11)。B=跨ETF依赖漂移(cross_dependence_1m,t=4.88)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZB2", "operator": "rank_spread", "left": _VT_UNDERWATER, "right": _GRANGER,
     "mechanism": "s25_vt_underwater_frac_vs_granger_in_degree",
     "hypothesis": "A=同上。B=Granger因果入度(cross_dependence_1m,t=4.25)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZB3", "operator": "rank_spread", "left": _VT_UNDERWATER, "right": _D1_1M,
     "mechanism": "s25_vt_underwater_frac_vs_d1_1m",
     "hypothesis": "A=同上。B=1m频价格延迟D1水平(S20,price_delay,t=3.96)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZB4", "operator": "rank_spread", "left": _VT_UNDERWATER, "right": _GAP_SESSION_CORR,
     "mechanism": "s25_vt_underwater_frac_vs_gap_session_corr",
     "hypothesis": "A=同上。B=跳空与session收益相关(gap_response,t=3.89)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZB5", "operator": "rank_spread", "left": _VT_UNDERWATER, "right": _PEER_OU_HALFLIFE,
     "mechanism": "s25_vt_underwater_frac_vs_peer_ou_halflife",
     "hypothesis": "A=同上。B=同伴OU均值回归半衰期(peer_relative_value,t=3.75)。假设方向探索性。本批最后一条。",
     "expected_sign": -1},
    # ---- DEP_DRIFT_20: S25 first pairing batch ----
    {"id": "ZC1", "operator": "rank_spread", "left": _DEP_DRIFT, "right": _JUMP_BETA,
     "mechanism": "s25_dep_drift_vs_jump_beta",
     "hypothesis": "A=跨ETF依赖漂移(cross_dependence_1m,本线历史最高t原子之一,t=4.88)。B=跳跃beta(S4,jump_continuous_beta_1m,t=4.10)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZC2", "operator": "rank_spread", "left": _DEP_DRIFT, "right": _D1_1M,
     "mechanism": "s25_dep_drift_vs_d1_1m",
     "hypothesis": "A=同上。B=1m频价格延迟D1水平(S20,price_delay,t=3.96)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZC3", "operator": "rank_spread", "left": _DEP_DRIFT, "right": _YZ_OVERNIGHT,
     "mechanism": "s25_dep_drift_vs_yz_overnight_share",
     "hypothesis": "A=同上。B=Yang-Zhang隔夜方差份额(S9,range_based_vol_1m,t=3.95)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZC4", "operator": "rank_spread", "left": _DEP_DRIFT, "right": _GAP_SESSION_CORR,
     "mechanism": "s25_dep_drift_vs_gap_session_corr",
     "hypothesis": "A=同上。B=跳空与session收益相关(gap_response,t=3.89)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZC5", "operator": "rank_spread", "left": _DEP_DRIFT, "right": _PEER_OU_HALFLIFE,
     "mechanism": "s25_dep_drift_vs_peer_ou_halflife",
     "hypothesis": "A=同上。B=同伴OU均值回归半衰期(peer_relative_value,t=3.75)。假设方向探索性。本批最后一条。",
     "expected_sign": -1},
    # ---- GRANGER_IN_DEGREE_20: S25 first pairing batch ----
    {"id": "ZD1", "operator": "rank_spread", "left": _GRANGER, "right": _JUMP_BETA,
     "mechanism": "s25_granger_in_degree_vs_jump_beta",
     "hypothesis": "A=Granger因果入度(cross_dependence_1m,t=4.25)。B=跳跃beta(S4,jump_continuous_beta_1m,t=4.10)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZD2", "operator": "rank_spread", "left": _GRANGER, "right": _D1_1M,
     "mechanism": "s25_granger_in_degree_vs_d1_1m",
     "hypothesis": "A=同上。B=1m频价格延迟D1水平(S20,price_delay,t=3.96)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZD3", "operator": "rank_spread", "left": _GRANGER, "right": _MFI_TOD_SKEW,
     "mechanism": "s25_granger_in_degree_vs_mfi_extreme_tod_skew",
     "hypothesis": "A=同上。B=MFI极端值时段偏度(money_flow_extremes_1m,t=3.95，含量原子)。假设方向探索性。（原计划的YZ_OVERNIGHT_SHARE_20搭档在plan锁定时命中既有哈希碰撞，已替换为本条）",
     "expected_sign": -1},
    {"id": "ZD4", "operator": "rank_spread", "left": _GRANGER, "right": _VOL_SPIKE_FREQ,
     "mechanism": "s25_granger_in_degree_vs_vol_spike_freq",
     "hypothesis": "A=同上。B=成交量突增频率(intraday_volume_profile_1m,t=4.10，含量原子)。假设方向探索性。（原计划的OVERNIGHT_FIRST30_CORR_20搭档在plan锁定时命中既有哈希碰撞，已替换为本条）",
     "expected_sign": -1},
    {"id": "ZD5", "operator": "rank_spread", "left": _GRANGER, "right": _PEER_OU_HALFLIFE,
     "mechanism": "s25_granger_in_degree_vs_peer_ou_halflife",
     "hypothesis": "A=同上。B=同伴OU均值回归半衰期(peer_relative_value,t=3.75)。假设方向探索性。本批最后一条。",
     "expected_sign": -1},
    # ---- YZ_OVERNIGHT_SHARE_20: S25 first pairing batch (mixes in untouched volume-level atoms) ----
    {"id": "ZE1", "operator": "rank_spread", "left": _YZ_OVERNIGHT, "right": _GAP_SESSION_CORR,
     "mechanism": "s25_yz_overnight_share_vs_gap_session_corr",
     "hypothesis": "A=Yang-Zhang隔夜方差份额(S9,range_based_vol_1m,t=3.95)。B=跳空与session收益相关(gap_response,t=3.89)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZE2", "operator": "rank_spread", "left": _YZ_OVERNIGHT, "right": _OVERNIGHT_FIRST30,
     "mechanism": "s25_yz_overnight_share_vs_overnight_first30_corr",
     "hypothesis": "A=同上。B=隔夜收益与首30分钟收益相关(intraday_momentum_30m,t=4.25)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZE3", "operator": "rank_spread", "left": _YZ_OVERNIGHT, "right": _VOL_SPIKE_FREQ,
     "mechanism": "s25_yz_overnight_share_vs_vol_spike_freq",
     "hypothesis": "A=同上。B=成交量突增频率(intraday_volume_profile_1m,t=4.10，含量原子，本轮起纳入)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZE4", "operator": "rank_spread", "left": _YZ_OVERNIGHT, "right": _AD_NET_FLOW,
     "mechanism": "s25_yz_overnight_share_vs_ad_net_flow",
     "hypothesis": "A=同上。B=A/D净流(accumulation_distribution_1m,t=3.96，含量原子)。假设方向探索性。",
     "expected_sign": -1},
    {"id": "ZE5", "operator": "rank_spread", "left": _YZ_OVERNIGHT, "right": _LUNCH_PRERUN_POSTRUN,
     "mechanism": "s25_yz_overnight_share_vs_lunch_prerun_postrun_ratio",
     "hypothesis": "A=同上。B=午前/午后抢跑成交量份额之比(S22原子级入选KA7,lunch_break_1m,t=5.48，含量原子)。假设方向探索性。（原计划的MFI_EXTREME_TOD_SKEW_20搭档在plan锁定时命中既有哈希碰撞，已替换为本条）本批最后一条，本轮末条。",
     "expected_sign": -1},
]

if __name__ == "__main__":
    base.main()
