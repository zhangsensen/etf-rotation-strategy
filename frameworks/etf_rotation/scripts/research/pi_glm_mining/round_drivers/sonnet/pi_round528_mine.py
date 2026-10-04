#!/usr/bin/env python3
"""Round 528 driver: S4 stage step 10 -- jump_continuous_beta pairing, round 10.

Nine-round scoreboard (round_519-527, 142 candidates, 15 net admissions,
no three-zero streak; round_527 was the stage's best round at 4/19).
CONTINUOUS_BETA_60 remains the sole productive leg, now with hits across
seven distinct channels (asymmetry, serial-dependence/ACF1, realized-
measures, microstructure, cross-dependence[none yet], peer-relative-value,
intraday-periodicity, nav-premium). peer_relative_value had this stage's
best per-family hit rate (2/4) but was only ever tested against
CONTINUOUS_BETA_60.

Two moves this round:
1. CONTINUOUS_BETA_60 x cross_etf_lead_lag (12 atoms, all first use for
   this family): a pre-S4 catalog family with MARKET_LEAD_BETA_20/60 --
   literally lagged-beta constructs, but capturing whether the asset LEADS
   or LAGS the market by one period, a temporally distinct dimension from
   jump_continuous_beta's same-day jump/continuous split. Also
   gap_response, gap_volatility, range_memory (1 atom each, also
   first-time use for this family) -- the last remaining pre-S4 single-
   atom families in the catalog never tested against any jump_continuous_
   beta leg.
2. The three closed legs (JUMP_BETA_20, BETA_GAP_20, JUMP_BETA_STABILITY_20)
   each get PEER_RESID_MOM_20 and PEER_OU_HALFLIFE_20 -- round_527's two
   peer_relative_value winners, paired against a DIFFERENT left leg (not a
   repeat of round_527's CONTINUOUS_BETA_60 combo) as one more diagnostic
   before treating those legs as permanently closed.

CONTINUOUS_BETA_20 stays closed (0/6, structurally shadow), no new
candidates. All (left,right) combos below are new. No same-family pairs,
no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_528"

_MKT_LEAD_BETA20 = {"name": "MARKET_LEAD_BETA_20", "source": "cross_etf_lead_lag"}
_MKT_LEAD_BETA60 = {"name": "MARKET_LEAD_BETA_60", "source": "cross_etf_lead_lag"}
_MKT_LEAD_CORR20 = {"name": "MARKET_LEAD_CORR_20", "source": "cross_etf_lead_lag"}
_MKT_LEAD_CORR60 = {"name": "MARKET_LEAD_CORR_60", "source": "cross_etf_lead_lag"}
_ASSET_LEAD_MKT20 = {"name": "ASSET_LEAD_MARKET_CORR_20", "source": "cross_etf_lead_lag"}
_ASSET_LEAD_MKT60 = {"name": "ASSET_LEAD_MARKET_CORR_60", "source": "cross_etf_lead_lag"}
_PEER_LEAD_BETA20 = {"name": "PEER_LEAD_BETA_20", "source": "cross_etf_lead_lag"}
_PEER_LEAD_BETA60 = {"name": "PEER_LEAD_BETA_60", "source": "cross_etf_lead_lag"}
_PEER_LEAD_CORR20 = {"name": "PEER_LEAD_CORR_20", "source": "cross_etf_lead_lag"}
_PEER_LEAD_CORR60 = {"name": "PEER_LEAD_CORR_60", "source": "cross_etf_lead_lag"}
_PEER_LEAD_NET20 = {"name": "PEER_LEAD_NETWORK_CORR_20", "source": "cross_etf_lead_lag"}
_PEER_LEAD_NET60 = {"name": "PEER_LEAD_NETWORK_CORR_60", "source": "cross_etf_lead_lag"}

_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}
_GAP_VOL_RATIO = {"name": "GAP_VOL_RATIO_20", "source": "gap_volatility"}
_RANGE_ACF1 = {"name": "RANGE_ACF1_20", "source": "range_memory"}

_PEER_RESID_MOM = {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}

_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_JB20 = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_BGAP20 = {"name": "BETA_GAP_20", "source": "jump_continuous_beta"}
_JBSTAB20 = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}

base.CANDIDATES = [
    # ---- CONTINUOUS_BETA_60 x cross_etf_lead_lag: lead/lag beta is a
    # temporally distinct dimension from same-day jump/continuous split ----
    {
        "id": "LC1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _MKT_LEAD_BETA20,
        "mechanism": "continuous_beta60_confirmed_by_market_lead_beta_20",
        "hypothesis": "A=连续分量beta，60日窗（本轮为止8个渠道净15次入选中的核心腿）。B=市场领先beta，20日（cross_etf_lead_lag，本族首次使用；衡量该ETF对滞后一期市场收益的beta，与A的同期jump/continuous分解是完全不同的时间维度）。假设：常态系统性暴露高(A高)且领先beta高(B高，价格发现领先)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "LC2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _MKT_LEAD_BETA60,
        "mechanism": "continuous_beta60_confirmed_by_market_lead_beta_60",
        "hypothesis": "A=同上。B=60日版本（同上，与A同窗对齐）。假设：同LC1，同窗对齐是否更强。",
        "expected_sign": 1,
    },
    {
        "id": "LC3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _MKT_LEAD_CORR20,
        "mechanism": "continuous_beta60_confirmed_by_market_lead_corr_20",
        "hypothesis": "A=同上。B=市场领先相关性，20日（本族首次使用）。假设：常态系统性暴露高(A高)且领先相关性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LC4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _MKT_LEAD_CORR60,
        "mechanism": "continuous_beta60_confirmed_by_market_lead_corr_60",
        "hypothesis": "A=同上。B=60日版本（同上）。假设：同LC3。",
        "expected_sign": 1,
    },
    {
        "id": "LC5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _ASSET_LEAD_MKT20,
        "mechanism": "continuous_beta60_confirmed_by_asset_lead_market_corr_20",
        "hypothesis": "A=同上。B=该资产领先市场的相关性，20日（本族首次使用；与LC3方向相反——资产领先市场而非市场领先资产）。假设：常态系统性暴露高(A高)且资产本身领先市场(B高)=该资产是系统性信息的价格发现来源，延续。",
        "expected_sign": 1,
    },
    {
        "id": "LC6",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _ASSET_LEAD_MKT60,
        "mechanism": "continuous_beta60_confirmed_by_asset_lead_market_corr_60",
        "hypothesis": "A=同上。B=60日版本（同上）。假设：同LC5。",
        "expected_sign": 1,
    },
    {
        "id": "LC7",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PEER_LEAD_BETA20,
        "mechanism": "continuous_beta60_confirmed_by_peer_lead_beta_20",
        "hypothesis": "A=同上。B=同伴领先beta，20日（本族首次使用；对滞后一期同伴组合收益的beta，而非对市场基准）。假设：常态系统性暴露高(A高)且对同伴的领先beta高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LC8",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PEER_LEAD_BETA60,
        "mechanism": "continuous_beta60_confirmed_by_peer_lead_beta_60",
        "hypothesis": "A=同上。B=60日版本（同上）。假设：同LC7。",
        "expected_sign": 1,
    },
    {
        "id": "LC9",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PEER_LEAD_CORR20,
        "mechanism": "continuous_beta60_confirmed_by_peer_lead_corr_20",
        "hypothesis": "A=同上。B=同伴领先相关性，20日（本族首次使用）。假设：常态系统性暴露高(A高)且同伴领先相关性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LC10",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PEER_LEAD_CORR60,
        "mechanism": "continuous_beta60_confirmed_by_peer_lead_corr_60",
        "hypothesis": "A=同上。B=60日版本（同上）。假设：同LC9。",
        "expected_sign": 1,
    },
    {
        "id": "LC11",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PEER_LEAD_NET20,
        "mechanism": "continuous_beta60_confirmed_by_peer_lead_network_corr_20",
        "hypothesis": "A=同上。B=同伴网络领先相关性，20日（本族首次使用；网络层面的领先关系而非双边）。假设：常态系统性暴露高(A高)且网络领先关系强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LC12",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _PEER_LEAD_NET60,
        "mechanism": "continuous_beta60_confirmed_by_peer_lead_network_corr_60",
        "hypothesis": "A=同上。B=60日版本（同上）。假设：同LC11。",
        "expected_sign": 1,
    },
    # ---- CONTINUOUS_BETA_60 x last remaining single-atom pre-S4 families ----
    {
        "id": "LD1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _GAP_SESSION_CORR,
        "mechanism": "continuous_beta60_confirmed_by_gap_session_correlation",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性（gap_response，本族首次使用；本线预S4阶段建的单原子家族）。假设：常态系统性暴露高(A高)且跳空延续性强(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "LD2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _GAP_VOL_RATIO,
        "mechanism": "continuous_beta60_confirmed_by_gap_volatility_ratio",
        "hypothesis": "A=同上。B=跳空波动率比率（gap_volatility，本族首次使用）。假设：常态系统性暴露高(A高)且跳空波动占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LD3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RANGE_ACF1,
        "mechanism": "continuous_beta60_confirmed_by_range_acf1",
        "hypothesis": "A=同上。B=日内振幅一阶自相关（range_memory，本族首次使用；振幅记忆效应）。假设：常态系统性暴露高(A高)且振幅呈现持续性(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- closed legs: peer_relative_value's two round_527 winners against
    # a different left leg (fresh combo, not a repeat) ----
    {
        "id": "LE1",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _PEER_RESID_MOM,
        "mechanism": "jump_beta_confirmed_by_peer_resid_momentum",
        "hypothesis": "A=跳跃分量beta（2/11，round_520后再无新命中）。B=同伴协整残差动量（peer_relative_value，round_527与CONTINUOUS_BETA_60配对时t=2.93 +39.5bp命中，本族最高命中率家族，此处首次与本腿配对）。假设：跳跃期系统性暴露高(A高)且相对同伴的偏离正在扩大(B高)=延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "LE2",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "jump_beta_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=同伴OU回归半衰期（peer_relative_value，round_527 t=3.75 +29.5bp命中，本腿首次配对）。假设：延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "LE3",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _PEER_RESID_MOM,
        "mechanism": "beta_gap_confirmed_by_peer_resid_momentum",
        "hypothesis": "A=崩盘beta缺口（0/9）。B=同上，本腿首次配对。假设：缺口大(A高)且相对同伴偏离扩大(B高)=延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "LE4",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "beta_gap_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=同上，本腿首次配对。假设：延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "LE5",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _PEER_RESID_MOM,
        "mechanism": "jump_beta_stability_confirmed_by_peer_resid_momentum",
        "hypothesis": "A=跳跃beta估计不确定性（1/18）。B=同上，本腿首次配对。假设：估计不确定性高(A高)且相对同伴偏离扩大(B高)=延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "LE6",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "jump_beta_stability_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=同上，本腿首次配对。假设：延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
