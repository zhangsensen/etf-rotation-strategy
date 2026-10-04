#!/usr/bin/env python3
"""Round 547 driver: S7 stage step 3 -- intraday_drawdown_1m pairing,
round 3 (covers the remaining left-leg space). Four independent
first-pairing batches for the 4 atoms not yet used as a left leg:

1-2. DD_RUNUP_ASYM_20 and DD_TROUGH_TIMING_20 (8 partners each) -- the
   two remaining non-shadow atoms.

3-4. INTRADAY_MAXRUNUP_20 and INTRADAY_CDAR_20 (8 partners each) -- both
   atom-health shadow vs downside_risk (0.79-0.80), same theme as
   INTRADAY_MAXDD_20 which round_546 showed can still clear the official
   dedup gate with the right confirming partner (QD5, t=2.17, +29.0bp).
   This is the 4th and 5th test of that "shadow-atom-rescue" pattern in
   this family alone (after MAXDD's success), following the session-wide
   pattern already confirmed 5 times (S4/S5/S6/S7/S10).

After this round, all 8 intraday_drawdown_1m atoms will have used their
one legal pairing batch -- no legal candidates remain for this family
regardless of outcome, so S7 will need formal closure next round.

All right-leg partners below are new to this family's S7 pairing history
(round_545/546's 24 partners are not repeated). No same-family pairs, no
window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_547"

_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_LBAR_CLOCK = {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"}
_ROLL_SPREAD_DAILY = {"name": "ROLL_SPREAD_20", "source": "microstructure_1m"}
_OFI_AUTOCORR = {"name": "OFI_AUTOCORR_20", "source": "microstructure_1m"}
_RS_MINUS20 = {"name": "RS_MINUS_20", "source": "realized_measures_1m"}
_CLOSE5_CONSIST = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_PEER_RESID_MOM = {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"}

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

_DD_RUNUP_ASYM = {"name": "DD_RUNUP_ASYM_20", "source": "intraday_drawdown_1m"}
_DD_TROUGH_TIMING = {"name": "DD_TROUGH_TIMING_20", "source": "intraday_drawdown_1m"}
_MAXRUNUP = {"name": "INTRADAY_MAXRUNUP_20", "source": "intraday_drawdown_1m"}
_CDAR = {"name": "INTRADAY_CDAR_20", "source": "intraday_drawdown_1m"}

base.CANDIDATES = [
    # ---- DD_RUNUP_ASYM_20: first pairing batch (non-shadow) ----
    {
        "id": "QE1",
        "operator": "rank_spread",
        "left": _DD_RUNUP_ASYM,
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "dd_runup_asym_confirmed_by_bigbar_vol_share",
        "hypothesis": "A=最大回撤减最大反弹（日内路径不对称性，体检审计+0.0018，非shadow）。B=大bar成交量占比（bar_size_order_flow，本族首次配对）。假设：回撤显著大于反弹(A高)且大bar贡献成交量占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QE2",
        "operator": "rank_spread",
        "left": _DD_RUNUP_ASYM,
        "right": _LBAR_CLOCK,
        "mechanism": "dd_runup_asym_confirmed_by_lbar_clock_std",
        "hypothesis": "A=同上。B=大bar发生时点的20日标准差（largebar_footprint_1m，本族首次配对）。假设：回撤主导(A高)且大bar发生时点分散(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QE3",
        "operator": "rank_spread",
        "left": _DD_RUNUP_ASYM,
        "right": _ROLL_SPREAD_DAILY,
        "mechanism": "dd_runup_asym_confirmed_by_daily_roll_spread",
        "hypothesis": "A=同上。B=日频Roll隐含价差（microstructure_1m，本族首次配对）。假设：回撤主导(A高)且日频隐含价差大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QE4",
        "operator": "rank_spread",
        "left": _DD_RUNUP_ASYM,
        "right": _OFI_AUTOCORR,
        "mechanism": "dd_runup_asym_confirmed_by_ofi_autocorr",
        "hypothesis": "A=同上。B=订单流不平衡自相关（microstructure_1m，本族首次配对）。假设：回撤主导(A高)且订单流不平衡持续性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QE5",
        "operator": "rank_spread",
        "left": _DD_RUNUP_ASYM,
        "right": _RS_MINUS20,
        "mechanism": "dd_runup_asym_confirmed_by_realized_semivariance_minus",
        "hypothesis": "A=同上。B=已实现负半方差占比（realized_measures_1m，S4阶段CONTINUOUS_BETA_60命中partner，t=2.34，本族首次配对）。假设：回撤主导(A高)且下行半方差占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QE6",
        "operator": "rank_spread",
        "left": _DD_RUNUP_ASYM,
        "right": _CLOSE5_CONSIST,
        "mechanism": "dd_runup_asym_confirmed_by_close5_day_consistency",
        "hypothesis": "A=同上。B=收盘前5分钟方向一致性（bar_size_order_flow，本族首次配对）。假设：回撤主导(A高)且尾盘方向一致性高(B高，尾盘继续下行)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QE7",
        "operator": "rank_spread",
        "left": _DD_RUNUP_ASYM,
        "right": _VOL_ENTROPY,
        "mechanism": "dd_runup_asym_confirmed_by_volume_entropy",
        "hypothesis": "A=同上。B=日内成交量分布熵（intraday_volume_profile_1m，本族首次配对）。假设：回撤主导(A高)且成交量分布熵低(B低，集中于下跌时段)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QE8",
        "operator": "rank_spread",
        "left": _DD_RUNUP_ASYM,
        "right": _PEER_RESID_MOM,
        "mechanism": "dd_runup_asym_confirmed_by_peer_resid_momentum",
        "hypothesis": "A=同上。B=同伴协整残差动量（peer_relative_value，S4阶段CONTINUOUS_BETA_60命中partner，t=2.93，本族首次配对）。假设：回撤主导(A高)且相对同伴偏离扩大(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- DD_TROUGH_TIMING_20: first pairing batch (non-shadow) ----
    {
        "id": "QF1",
        "operator": "rank_spread",
        "left": _DD_TROUGH_TIMING,
        "right": _BPV_RV_RATIO,
        "mechanism": "dd_trough_timing_confirmed_by_bpv_rv_ratio",
        "hypothesis": "A=最大回撤谷底出现的相对位置（体检审计-0.0244，非shadow）。B=双幂变差/已实现方差比（realized_measures_1m，本族首次配对）。假设：谷底出现较晚(A高，尾盘探底)且自身收益连续分量占比低(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "QF2",
        "operator": "rank_spread",
        "left": _DD_TROUGH_TIMING,
        "right": _JV_RV_SHARE,
        "mechanism": "dd_trough_timing_confirmed_by_jump_variation_share",
        "hypothesis": "A=同上。B=跳跃变差占已实现方差比例（realized_measures_1m，本族首次配对）。假设：谷底靠后(A高)且自身跳跃占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QF3",
        "operator": "rank_spread",
        "left": _DD_TROUGH_TIMING,
        "right": _VOL_USHAPE20,
        "mechanism": "dd_trough_timing_confirmed_by_vol_ushape",
        "hypothesis": "A=同上。B=日内成交量U型强度（realized_measures_1m，round_053门7已admitted原子，本族首次配对）。假设：谷底靠后(A高)且U型强度高(B高，尾盘放量)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QF4",
        "operator": "rank_spread",
        "left": _DD_TROUGH_TIMING,
        "right": _VPIN_CLOSE,
        "mechanism": "dd_trough_timing_confirmed_by_vpin",
        "hypothesis": "A=同上。B=收盘时点VPIN（microstructure_1m，本族首次配对）。假设：谷底靠后(A高)且收盘VPIN高(B高，知情交易占比高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QF5",
        "operator": "rank_spread",
        "left": _DD_TROUGH_TIMING,
        "right": _AMIHUD_1M,
        "mechanism": "dd_trough_timing_confirmed_by_amihud_1m",
        "hypothesis": "A=同上。B=Amihud非流动性比率的1m版本（microstructure_1m，本族首次配对）。假设：谷底靠后(A高)且非流动性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QF6",
        "operator": "rank_spread",
        "left": _DD_TROUGH_TIMING,
        "right": _IMPACT_ASYM,
        "mechanism": "dd_trough_timing_confirmed_by_impact_asymmetry",
        "hypothesis": "A=同上。B=价格冲击不对称性（microstructure_1m，本族首次配对）。假设：谷底靠后(A高)且冲击不对称明显(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QF7",
        "operator": "rank_spread",
        "left": _DD_TROUGH_TIMING,
        "right": _GRANGER_IN,
        "mechanism": "dd_trough_timing_confirmed_by_granger_in_degree",
        "hypothesis": "A=同上。B=格兰杰因果入度（cross_dependence_1m，本族首次配对）。假设：谷底靠后(A高)且被同伴领先影响强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QF8",
        "operator": "rank_spread",
        "left": _DD_TROUGH_TIMING,
        "right": _PEER_RESID_Z,
        "mechanism": "dd_trough_timing_confirmed_by_peer_resid_z",
        "hypothesis": "A=同上。B=相对同伴的协整残差z值（peer_relative_value，本族首次配对）。假设：谷底靠后(A高)且相对同伴出现正向偏离(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- INTRADAY_MAXRUNUP_20: first pairing batch (shadow, following
    # MAXDD's successful rescue pattern in round_546) ----
    {
        "id": "QG1",
        "operator": "rank_spread",
        "left": _MAXRUNUP,
        "right": _HKS_SLOT,
        "mechanism": "maxrunup_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=对称的日内最大反弹（atom-health shadow=True vs downside_risk 0.79；本族INTRADAY_MAXDD_20已证明shadow原子仍可清官方去重门[round_546 QD5]）。B=日内时段模式持续性（intraday_periodicity，S4阶段命中partner，本族首次配对）。假设：日内反弹深(A高)且日内时段模式稳定(B高)=延续，测试能否复现MAXDD的rescue模式。",
        "expected_sign": 1,
    },
    {
        "id": "QG2",
        "operator": "rank_spread",
        "left": _MAXRUNUP,
        "right": _OVERNIGHT_DIFF,
        "mechanism": "maxrunup_confirmed_by_overnight_intra_diff",
        "hypothesis": "A=同上。B=隔夜与日内收益差异（intraday_periodicity，本族首次配对）。假设：日内反弹深(A高)且隔夜/日内收益分化明显(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QG3",
        "operator": "rank_spread",
        "left": _MAXRUNUP,
        "right": _TAIL30_BETA_FULL,
        "mechanism": "maxrunup_confirmed_by_tail30_beta_full",
        "hypothesis": "A=同上。B=尾盘30分钟beta相对全天beta的比值（intraday_periodicity，本族首次配对）。假设：日内反弹深(A高)且尾盘beta占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QG4",
        "operator": "rank_spread",
        "left": _MAXRUNUP,
        "right": _REL_MOM60,
        "mechanism": "maxrunup_confirmed_by_relative_market_momentum_60",
        "hypothesis": "A=同上。B=相对基准篮子动量，60日（market_relative_strength，本族首次配对）。假设：日内反弹深(A高)且相对基准动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QG5",
        "operator": "rank_spread",
        "left": _MAXRUNUP,
        "right": _TRACK_ERR20,
        "mechanism": "maxrunup_confirmed_by_tracking_error_20",
        "hypothesis": "A=同上。B=相对基准跟踪误差，20日（market_relative_strength，本族首次配对）。假设：日内反弹深(A高)且跟踪误差高(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "QG6",
        "operator": "rank_spread",
        "left": _MAXRUNUP,
        "right": _CAT_MOM20,
        "mechanism": "maxrunup_confirmed_by_category_momentum_20",
        "hypothesis": "A=同上。B=板块20日动量（category_state，本族首次配对）。假设：日内反弹深(A高)且板块动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QG7",
        "operator": "rank_spread",
        "left": _MAXRUNUP,
        "right": _CAT_DISP20,
        "mechanism": "maxrunup_confirmed_by_category_dispersion_20",
        "hypothesis": "A=同上。B=板块内部20日收益离散度（category_state，本族首次配对）。假设：日内反弹深(A高)且板块内部分化大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QG8",
        "operator": "rank_spread",
        "left": _MAXRUNUP,
        "right": _SHARE_CHG20,
        "mechanism": "maxrunup_confirmed_by_share_change_20",
        "hypothesis": "A=同上。B=基金份额20日变化（fund_flow，本族首次配对）。假设：日内反弹深(A高)且份额扩张(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- INTRADAY_CDAR_20: first pairing batch (shadow) ----
    {
        "id": "QH1",
        "operator": "rank_spread",
        "left": _CDAR,
        "right": _PREMIUM_Z20,
        "mechanism": "cdar_confirmed_by_premium_z_20",
        "hypothesis": "A=条件回撤风险CDaR（atom-health shadow=True vs downside_risk 0.80）。B=净值溢价20日z值（nav_premium，本族首次配对）。假设：CDaR深(A高)且溢价异常走高(B高)=延续；测试能否复现MAXDD的rescue模式。",
        "expected_sign": 1,
    },
    {
        "id": "QH2",
        "operator": "rank_spread",
        "left": _CDAR,
        "right": _GAP_SESSION_CORR,
        "mechanism": "cdar_confirmed_by_gap_session_correlation",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性（gap_response，S4阶段最强命中partner，t=3.89，本族首次配对）。假设：CDaR深(A高)且跳空延续性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QH3",
        "operator": "rank_spread",
        "left": _CDAR,
        "right": _GAP_VOL_RATIO,
        "mechanism": "cdar_confirmed_by_gap_volatility_ratio",
        "hypothesis": "A=同上。B=跳空波动率比率（gap_volatility，本族首次配对）。假设：CDaR深(A高)且跳空波动占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QH4",
        "operator": "rank_spread",
        "left": _CDAR,
        "right": _RANGE_ACF1,
        "mechanism": "cdar_confirmed_by_range_acf1",
        "hypothesis": "A=同上。B=日内振幅一阶自相关（range_memory，本族首次配对）。假设：CDaR深(A高)且振幅呈现持续性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QH5",
        "operator": "rank_spread",
        "left": _CDAR,
        "right": _CHIP_RANGE,
        "mechanism": "cdar_confirmed_by_chip_range",
        "hypothesis": "A=同上。B=90分位筹码分布宽度（cost_distribution，本族首次配对）。假设：CDaR深(A高)且筹码分布宽(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QH6",
        "operator": "rank_spread",
        "left": _CDAR,
        "right": _PRICE_AVGCOST,
        "mechanism": "cdar_confirmed_by_price_vs_avgcost",
        "hypothesis": "A=同上。B=现价相对平均成本偏离（cost_distribution，本族首次配对）。假设：CDaR深(A高)且现价明显低于平均成本(B低，套牢盘厚)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "QH7",
        "operator": "rank_spread",
        "left": _CDAR,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "cdar_confirmed_by_idio_liquidity_shock",
        "hypothesis": "A=同上。B=特异流动性冲击z值（liquidity_commonality_1m，本族首次配对）。假设：CDaR深(A高)且特异流动性冲击大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QH8",
        "operator": "rank_spread",
        "left": _CDAR,
        "right": _COJUMP_INDEX,
        "mechanism": "cdar_confirmed_by_cojump_index_share",
        "hypothesis": "A=同上。B=共跳占指数跳跃比例（cojump_1m，本族首次配对）。假设：CDaR深(A高)且与指数共跳比例高(B高)=延续；本族最后一批。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
