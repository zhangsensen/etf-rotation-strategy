#!/usr/bin/env python3
"""Round 551 driver: S8 stage step 3 -- realized_semicov_1m pairing,
round 3 (covers the remaining left-leg space). Three independent
first-pairing batches for the 3 atoms not yet used as a left leg:
BETA_ASYM_20, RCOV_N_SHARE_CHG_20, BETA_ASYM_CHG_20 (all non-shadow;
round_549 atomic tests all failed cleanly on the bp/identity floor with
no redundancy issue, so this round tests whether a confirming partner can
surface a signal these atoms' own atomic tests didn't show).

After this round, all 8 realized_semicov_1m atoms will have used their
one legal pairing batch -- no legal candidates remain for this family
regardless of outcome, so S8 will need formal closure next round.

All right-leg partners below are new to this family's S8 pairing history
(round_549/550's 32 partners are not repeated). No same-family pairs, no
window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_551"

_BPV_RV_RATIO = {"name": "BPV_RV_RATIO_20", "source": "realized_measures_1m"}
_JV_RV_SHARE = {"name": "JV_RV_SHARE_20", "source": "realized_measures_1m"}
_VOL_USHAPE20 = {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"}
_VPIN_CLOSE = {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"}
_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_IMPACT_ASYM = {"name": "IMPACT_ASYM_20", "source": "microstructure_1m"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_PEER_RESID_Z = {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"}

_HKS_SLOT = {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"}
_OVERNIGHT_DIFF = {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"}
_TAIL30_BETA_FULL = {"name": "TAIL30_BETA_FULL_20", "source": "intraday_periodicity"}
_REL_MOM60 = {"name": "REL_MARKET_MOM_60", "source": "market_relative_strength"}
_TRACK_ERR20 = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}
_CAT_MOM20 = {"name": "CATEGORY_MOM_20", "source": "category_state"}
_CAT_DISP20 = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_SHARE_CHG20 = {"name": "SHARE_CHG_20", "source": "fund_flow"}

_PREMIUM_Z20 = {"name": "PREMIUM_Z_20", "source": "nav_premium"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}
_GAP_VOL_RATIO = {"name": "GAP_VOL_RATIO_20", "source": "gap_volatility"}
_RANGE_ACF1 = {"name": "RANGE_ACF1_20", "source": "range_memory"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_PRICE_AVGCOST = {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"}
_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_COJUMP_INDEX = {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"}

_BETA_ASYM = {"name": "BETA_ASYM_20", "source": "realized_semicov_1m"}
_RCOV_N_CHG = {"name": "RCOV_N_SHARE_CHG_20", "source": "realized_semicov_1m"}
_BETA_ASYM_CHG = {"name": "BETA_ASYM_CHG_20", "source": "realized_semicov_1m"}

base.CANDIDATES = [
    # ---- BETA_ASYM_20: first pairing batch (non-shadow, atomic weak) ----
    {
        "id": "RF1",
        "operator": "rank_spread",
        "left": _BETA_ASYM,
        "right": _BPV_RV_RATIO,
        "mechanism": "beta_asym_confirmed_by_bpv_rv_ratio",
        "hypothesis": "A=下行beta减上行beta（崩盘beta缺口的半协方差版本，体检审计+0.0113，非shadow）。B=双幂变差/已实现方差比（realized_measures_1m，本族首次配对）。假设：崩盘beta缺口大(A高)且自身收益连续分量占比低(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "RF2",
        "operator": "rank_spread",
        "left": _BETA_ASYM,
        "right": _JV_RV_SHARE,
        "mechanism": "beta_asym_confirmed_by_jump_variation_share",
        "hypothesis": "A=同上。B=跳跃变差占已实现方差比例（realized_measures_1m，本族首次配对）。假设：崩盘beta缺口大(A高)且自身跳跃占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RF3",
        "operator": "rank_spread",
        "left": _BETA_ASYM,
        "right": _VOL_USHAPE20,
        "mechanism": "beta_asym_confirmed_by_vol_ushape",
        "hypothesis": "A=同上。B=日内成交量U型强度（realized_measures_1m，round_053门7已admitted原子，本族首次配对）。假设：崩盘beta缺口大(A高)且U型强度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RF4",
        "operator": "rank_spread",
        "left": _BETA_ASYM,
        "right": _VPIN_CLOSE,
        "mechanism": "beta_asym_confirmed_by_vpin",
        "hypothesis": "A=同上。B=收盘时点VPIN（microstructure_1m，本族首次配对）。假设：崩盘beta缺口大(A高)且收盘VPIN高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RF5",
        "operator": "rank_spread",
        "left": _BETA_ASYM,
        "right": _AMIHUD_1M,
        "mechanism": "beta_asym_confirmed_by_amihud_1m",
        "hypothesis": "A=同上。B=Amihud非流动性比率的1m版本（microstructure_1m，本族首次配对）。假设：崩盘beta缺口大(A高)且非流动性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RF6",
        "operator": "rank_spread",
        "left": _BETA_ASYM,
        "right": _IMPACT_ASYM,
        "mechanism": "beta_asym_confirmed_by_impact_asymmetry",
        "hypothesis": "A=同上。B=价格冲击不对称性（microstructure_1m，本族首次配对；与A的beta不对称主题呼应但衡量微观结构层面）。假设：崩盘beta缺口大(A高)且冲击不对称明显(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RF7",
        "operator": "rank_spread",
        "left": _BETA_ASYM,
        "right": _GRANGER_IN,
        "mechanism": "beta_asym_confirmed_by_granger_in_degree",
        "hypothesis": "A=同上。B=格兰杰因果入度（cross_dependence_1m，本族首次配对）。假设：崩盘beta缺口大(A高)且被同伴领先影响强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RF8",
        "operator": "rank_spread",
        "left": _BETA_ASYM,
        "right": _PEER_RESID_Z,
        "mechanism": "beta_asym_confirmed_by_peer_resid_z",
        "hypothesis": "A=同上。B=相对同伴的协整残差z值（peer_relative_value，本族首次配对）。假设：崩盘beta缺口大(A高)且相对同伴出现正向偏离(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- RCOV_N_SHARE_CHG_20: first pairing batch ----
    {
        "id": "RG1",
        "operator": "rank_spread",
        "left": _RCOV_N_CHG,
        "right": _HKS_SLOT,
        "mechanism": "rcov_n_share_chg_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=同跌分量占比的20日变化（regime切换，体检审计-0.0432）。B=日内时段模式持续性（intraday_periodicity，S4阶段命中partner，本族首次配对）。假设：同跌集中度正在上升(A高)且日内时段模式稳定(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RG2",
        "operator": "rank_spread",
        "left": _RCOV_N_CHG,
        "right": _OVERNIGHT_DIFF,
        "mechanism": "rcov_n_share_chg_confirmed_by_overnight_intra_diff",
        "hypothesis": "A=同上。B=隔夜与日内收益差异（intraday_periodicity，本族首次配对）。假设：同跌集中度上升(A高)且隔夜/日内收益分化明显(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RG3",
        "operator": "rank_spread",
        "left": _RCOV_N_CHG,
        "right": _TAIL30_BETA_FULL,
        "mechanism": "rcov_n_share_chg_confirmed_by_tail30_beta_full",
        "hypothesis": "A=同上。B=尾盘30分钟beta相对全天beta的比值（intraday_periodicity，本族首次配对）。假设：同跌集中度上升(A高)且尾盘beta占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RG4",
        "operator": "rank_spread",
        "left": _RCOV_N_CHG,
        "right": _REL_MOM60,
        "mechanism": "rcov_n_share_chg_confirmed_by_relative_market_momentum_60",
        "hypothesis": "A=同上。B=相对基准篮子动量，60日（market_relative_strength，本族首次配对）。假设：同跌集中度上升(A高)且相对基准动量弱(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "RG5",
        "operator": "rank_spread",
        "left": _RCOV_N_CHG,
        "right": _TRACK_ERR20,
        "mechanism": "rcov_n_share_chg_confirmed_by_tracking_error_20",
        "hypothesis": "A=同上。B=相对基准跟踪误差，20日（market_relative_strength，本族首次配对）。假设：同跌集中度上升(A高)且跟踪误差高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RG6",
        "operator": "rank_spread",
        "left": _RCOV_N_CHG,
        "right": _CAT_MOM20,
        "mechanism": "rcov_n_share_chg_confirmed_by_category_momentum_20",
        "hypothesis": "A=同上。B=板块20日动量（category_state，本族首次配对）。假设：同跌集中度上升(A高)且板块动量弱(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "RG7",
        "operator": "rank_spread",
        "left": _RCOV_N_CHG,
        "right": _CAT_DISP20,
        "mechanism": "rcov_n_share_chg_confirmed_by_category_dispersion_20",
        "hypothesis": "A=同上。B=板块内部20日收益离散度（category_state，本族首次配对）。假设：同跌集中度上升(A高)且板块内部分化大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RG8",
        "operator": "rank_spread",
        "left": _RCOV_N_CHG,
        "right": _SHARE_CHG20,
        "mechanism": "rcov_n_share_chg_confirmed_by_share_change_20",
        "hypothesis": "A=同上。B=基金份额20日变化（fund_flow，本族首次配对）。假设：同跌集中度上升(A高)且份额收缩(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    # ---- BETA_ASYM_CHG_20: first pairing batch ----
    {
        "id": "RH1",
        "operator": "rank_spread",
        "left": _BETA_ASYM_CHG,
        "right": _PREMIUM_Z20,
        "mechanism": "beta_asym_chg_confirmed_by_premium_z_20",
        "hypothesis": "A=崩盘beta缺口的20日变化（体检审计+0.0096）。B=净值溢价20日z值（nav_premium，本族首次配对）。假设：崩盘beta缺口正在扩大(A高)且溢价异常走高(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "RH2",
        "operator": "rank_spread",
        "left": _BETA_ASYM_CHG,
        "right": _GAP_SESSION_CORR,
        "mechanism": "beta_asym_chg_confirmed_by_gap_session_correlation",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性（gap_response，S4阶段最强命中partner，t=3.89，本族首次配对）。假设：崩盘beta缺口扩大(A高)且跳空延续性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RH3",
        "operator": "rank_spread",
        "left": _BETA_ASYM_CHG,
        "right": _GAP_VOL_RATIO,
        "mechanism": "beta_asym_chg_confirmed_by_gap_volatility_ratio",
        "hypothesis": "A=同上。B=跳空波动率比率（gap_volatility，本族首次配对）。假设：崩盘beta缺口扩大(A高)且跳空波动占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RH4",
        "operator": "rank_spread",
        "left": _BETA_ASYM_CHG,
        "right": _RANGE_ACF1,
        "mechanism": "beta_asym_chg_confirmed_by_range_acf1",
        "hypothesis": "A=同上。B=日内振幅一阶自相关（range_memory，S7阶段QH4命中partner，t=2.13，本族首次配对）。假设：崩盘beta缺口扩大(A高)且振幅呈现持续性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RH5",
        "operator": "rank_spread",
        "left": _BETA_ASYM_CHG,
        "right": _CHIP_RANGE,
        "mechanism": "beta_asym_chg_confirmed_by_chip_range",
        "hypothesis": "A=同上。B=90分位筹码分布宽度（cost_distribution，本族首次配对）。假设：崩盘beta缺口扩大(A高)且筹码分布宽(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RH6",
        "operator": "rank_spread",
        "left": _BETA_ASYM_CHG,
        "right": _PRICE_AVGCOST,
        "mechanism": "beta_asym_chg_confirmed_by_price_vs_avgcost",
        "hypothesis": "A=同上。B=现价相对平均成本偏离（cost_distribution，本族首次配对）。假设：崩盘beta缺口扩大(A高)且现价明显低于平均成本(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "RH7",
        "operator": "rank_spread",
        "left": _BETA_ASYM_CHG,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "beta_asym_chg_confirmed_by_idio_liquidity_shock",
        "hypothesis": "A=同上。B=特异流动性冲击z值（liquidity_commonality_1m，本族首次配对）。假设：崩盘beta缺口扩大(A高)且特异流动性冲击大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RH8",
        "operator": "rank_spread",
        "left": _BETA_ASYM_CHG,
        "right": _COJUMP_INDEX,
        "mechanism": "beta_asym_chg_confirmed_by_cojump_index_share",
        "hypothesis": "A=同上。B=共跳占指数跳跃比例（cojump_1m，本族首次配对）。假设：崩盘beta缺口扩大(A高)且与指数共跳比例高(B高)=延续；本族最后一批。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
