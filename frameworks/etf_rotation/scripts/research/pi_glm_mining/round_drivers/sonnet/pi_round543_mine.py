#!/usr/bin/env python3
"""Round 543 driver: S6 stage step 3 -- permutation_entropy_1m pairing,
round 3 (final round covering the remaining left-leg space). Five
independent first-pairing batches for the 5 atoms not yet used as a left
leg:

1-2. STAT_COMPLEXITY_CHG_20 and PERM_ENTROPY_VOL_CHG_20 (8 partners each)
   -- both 20-day-change constructs, following round_542's finding that
   the _CHG atoms (PERM_ENTROPY_RET_CHG_20 admitted cleanly, no
   redundancy against PA1) are temporally distinct enough from the
   admitted level atom to be worth a full batch.

3-5. STAT_COMPLEXITY_20, CEP_DISTANCE_20, ENTROPY_RET_VOL_DIFF_20
   (4 partners each, smaller diagnostic batches) -- round_541's
   atom_health and gate-7 results both showed these three sharing PA1's
   core H_ret component (rank corr 0.77-0.96 against PA1 in round_541's
   same-batch dedup check), so a full 8-partner batch is unlikely to be
   worth the compute; a smaller diagnostic batch checks whether any
   partner is strong enough to overcome that redundancy before writing
   these three off.

After this round, all 8 permutation_entropy_1m atoms will have used
their one legal pairing batch -- no legal candidates remain for this
family regardless of outcome, so S6 will need formal closure next round
unless this round produces a run of admissions that changes that
calculus (it won't change the legal-space-exhausted fact, only the
admission count).

All right-leg partners below are new to this family's S6 pairing history
(round_541/542's 24 partners are not repeated). No same-family pairs, no
window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_543"

_WORST_DAY20 = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_CAT_MOM20 = {"name": "CATEGORY_MOM_20", "source": "category_state"}
_TAILQ10_20 = {"name": "TAIL_Q10_20", "source": "return_tail_shape"}
_SHARE_CHG20 = {"name": "SHARE_CHG_20", "source": "fund_flow"}
_PREMIUM_Z20 = {"name": "PREMIUM_Z_20", "source": "nav_premium"}
_HKS_SLOT = {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"}
_VOL_USHAPE20 = {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"}
_BPV_RV_RATIO = {"name": "BPV_RV_RATIO_20", "source": "realized_measures_1m"}

_JV_RV_SHARE = {"name": "JV_RV_SHARE_20", "source": "realized_measures_1m"}
_COJUMP_DIR_AGREE = {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"}
_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_OVERNIGHT_DIFF = {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"}
_TAIL30_BETA_FULL = {"name": "TAIL30_BETA_FULL_20", "source": "intraday_periodicity"}
_VOL_PROFILE_DIST = {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_TURNOVER_DIST = {"name": "TURNOVER_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_PROFIT_RATIO = {"name": "PROFIT_RATIO_60", "source": "cost_distribution"}

_PEER_RESID_MOM = {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_LBAR_CLOCK = {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"}
_ROLL_SPREAD_DAILY = {"name": "ROLL_SPREAD_20", "source": "microstructure_1m"}

_CLOSE5_CONSIST = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_LIQ_COMMON_BETA = {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}

_BIGBAR_EDGE = {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"}
_COJUMP_INDEX = {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"}
_PEER_LEAD_NET60 = {"name": "PEER_LEAD_NETWORK_CORR_60", "source": "cross_etf_lead_lag"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}

_STAT_COMPLEXITY_CHG = {"name": "STAT_COMPLEXITY_CHG_20", "source": "permutation_entropy_1m"}
_PE_VOL_CHG = {"name": "PERM_ENTROPY_VOL_CHG_20", "source": "permutation_entropy_1m"}
_STAT_COMPLEXITY = {"name": "STAT_COMPLEXITY_20", "source": "permutation_entropy_1m"}
_CEP_DIST = {"name": "CEP_DISTANCE_20", "source": "permutation_entropy_1m"}
_ENTROPY_DIFF = {"name": "ENTROPY_RET_VOL_DIFF_20", "source": "permutation_entropy_1m"}

base.CANDIDATES = [
    # ---- STAT_COMPLEXITY_CHG_20: first pairing batch (20d change,
    # temporally distinct from the level atoms) ----
    {
        "id": "PE1",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY_CHG,
        "right": _WORST_DAY20,
        "mechanism": "stat_complexity_chg_confirmed_by_worst_day",
        "hypothesis": "A=统计复杂度C_JS的20日变化（体检审计-0.0161）。B=20日最差单日收益（return_tail_shape，S10阶段候选，本族首次配对）。假设：复杂度正在上升(A高)且下行尾更极端(B更负)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "PE2",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY_CHG,
        "right": _CAT_MOM20,
        "mechanism": "stat_complexity_chg_confirmed_by_category_momentum_20",
        "hypothesis": "A=同上。B=板块20日动量（category_state，本族首次配对）。假设：复杂度上升(A高)且板块动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PE3",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY_CHG,
        "right": _TAILQ10_20,
        "mechanism": "stat_complexity_chg_confirmed_by_tail_q10_20",
        "hypothesis": "A=同上。B=20日收益分布10%分位数（return_tail_shape，本族首次配对）。假设：复杂度上升(A高)且下尾更浅(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "PE4",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY_CHG,
        "right": _SHARE_CHG20,
        "mechanism": "stat_complexity_chg_confirmed_by_share_change_20",
        "hypothesis": "A=同上。B=基金份额20日变化（fund_flow，本族首次配对）。假设：复杂度上升(A高)且份额扩张(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PE5",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY_CHG,
        "right": _PREMIUM_Z20,
        "mechanism": "stat_complexity_chg_confirmed_by_premium_z_20",
        "hypothesis": "A=同上。B=净值溢价20日z值（nav_premium，本族首次配对）。假设：复杂度上升(A高)且溢价异常走高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PE6",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY_CHG,
        "right": _HKS_SLOT,
        "mechanism": "stat_complexity_chg_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=同上。B=日内时段模式持续性（intraday_periodicity，S4阶段命中partner，本族首次配对）。假设：复杂度上升(A高)且日内时段模式稳定(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PE7",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY_CHG,
        "right": _VOL_USHAPE20,
        "mechanism": "stat_complexity_chg_confirmed_by_vol_ushape",
        "hypothesis": "A=同上。B=日内成交量U型强度（realized_measures_1m，round_053门7已admitted原子，本族首次配对）。假设：复杂度上升(A高)且U型强度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PE8",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY_CHG,
        "right": _BPV_RV_RATIO,
        "mechanism": "stat_complexity_chg_confirmed_by_bpv_rv_ratio",
        "hypothesis": "A=同上。B=双幂变差/已实现方差比（realized_measures_1m，本族首次配对）。假设：复杂度上升(A高)且自身收益连续分量占比低(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    # ---- PERM_ENTROPY_VOL_CHG_20: first pairing batch ----
    {
        "id": "PF1",
        "operator": "rank_spread",
        "left": _PE_VOL_CHG,
        "right": _JV_RV_SHARE,
        "mechanism": "perm_entropy_vol_chg_confirmed_by_jump_variation_share",
        "hypothesis": "A=成交量排列熵的20日变化（体检审计-0.0244）。B=跳跃变差占已实现方差比例（realized_measures_1m，本族首次配对）。假设：成交量到达模式正在随机化(A高)且自身跳跃占比高(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "PF2",
        "operator": "rank_spread",
        "left": _PE_VOL_CHG,
        "right": _COJUMP_DIR_AGREE,
        "mechanism": "perm_entropy_vol_chg_confirmed_by_cojump_dir_agree",
        "hypothesis": "A=同上。B=共跳方向一致性（cojump_1m，本族首次配对）。假设：成交量到达随机化(A高)且共跳方向一致性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PF3",
        "operator": "rank_spread",
        "left": _PE_VOL_CHG,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "perm_entropy_vol_chg_confirmed_by_idio_liquidity_shock",
        "hypothesis": "A=同上。B=特异流动性冲击z值（liquidity_commonality_1m，本族首次配对）。假设：成交量到达随机化(A高)且特异流动性冲击大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PF4",
        "operator": "rank_spread",
        "left": _PE_VOL_CHG,
        "right": _OVERNIGHT_DIFF,
        "mechanism": "perm_entropy_vol_chg_confirmed_by_overnight_intra_diff",
        "hypothesis": "A=同上。B=隔夜与日内收益差异（intraday_periodicity，本族首次配对）。假设：成交量到达随机化(A高)且隔夜/日内收益分化明显(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PF5",
        "operator": "rank_spread",
        "left": _PE_VOL_CHG,
        "right": _TAIL30_BETA_FULL,
        "mechanism": "perm_entropy_vol_chg_confirmed_by_tail30_beta_full",
        "hypothesis": "A=同上。B=尾盘30分钟beta相对全天beta的比值（intraday_periodicity，本族首次配对）。假设：成交量到达随机化(A高)且尾盘beta占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PF6",
        "operator": "rank_spread",
        "left": _PE_VOL_CHG,
        "right": _VOL_PROFILE_DIST,
        "mechanism": "perm_entropy_vol_chg_confirmed_by_volume_profile_shift",
        "hypothesis": "A=同上。B=日内成交量分布偏离（intraday_profile_deviation，本线最高t单原子历史，本族首次配对）。假设：成交量到达随机化(A高)且日内成交结构异常(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PF7",
        "operator": "rank_spread",
        "left": _PE_VOL_CHG,
        "right": _TURNOVER_DIST,
        "mechanism": "perm_entropy_vol_chg_confirmed_by_turnover_profile_shift",
        "hypothesis": "A=同上。B=日内换手分布偏离（intraday_profile_deviation，本族首次配对）。假设：成交量到达随机化(A高)且日内换手结构异常(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PF8",
        "operator": "rank_spread",
        "left": _PE_VOL_CHG,
        "right": _PROFIT_RATIO,
        "mechanism": "perm_entropy_vol_chg_confirmed_by_profit_ratio",
        "hypothesis": "A=同上。B=60日获利比例（cost_distribution，本族首次配对）。假设：成交量到达随机化(A高)且获利盘占比高(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- STAT_COMPLEXITY_20: 4-partner diagnostic (round_541 gate-7
    # showed 0.84-0.85 corr vs the admitted PA1 -- checking if this
    # channel has any life left before writing it off) ----
    {
        "id": "PG1",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY,
        "right": _PEER_RESID_MOM,
        "mechanism": "stat_complexity_confirmed_by_peer_resid_momentum",
        "hypothesis": "A=统计复杂度C_JS水平（round_541 gate-7阶段与PA1(PERM_ENTROPY_RET_20)corr=0.84，因redundancy被拒；本条测试全新partner是否能拉开与PA1的相关性）。B=同伴协整残差动量（peer_relative_value，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：复杂度高(A高)且相对同伴偏离扩大(B高)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "PG2",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY,
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "stat_complexity_confirmed_by_bigbar_vol_share",
        "hypothesis": "A=同上。B=大bar成交量占比（bar_size_order_flow，本族首次配对）。假设：复杂度高(A高)且大bar贡献成交量占比高(B高)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "PG3",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY,
        "right": _LBAR_CLOCK,
        "mechanism": "stat_complexity_confirmed_by_lbar_clock_std",
        "hypothesis": "A=同上。B=大bar发生时点的20日标准差（largebar_footprint_1m，本族首次配对）。假设：复杂度高(A高)且大bar发生时点分散(B高)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "PG4",
        "operator": "rank_spread",
        "left": _STAT_COMPLEXITY,
        "right": _ROLL_SPREAD_DAILY,
        "mechanism": "stat_complexity_confirmed_by_daily_roll_spread",
        "hypothesis": "A=同上。B=日频Roll隐含价差（microstructure_1m，本族首次配对）。假设：复杂度高(A高)且日频隐含价差大(B高)=延续；诊断性测试，本腿最后一批。",
        "expected_sign": 1,
    },
    # ---- CEP_DISTANCE_20: 4-partner diagnostic ----
    {
        "id": "PH1",
        "operator": "rank_spread",
        "left": _CEP_DIST,
        "right": _CLOSE5_CONSIST,
        "mechanism": "cep_distance_confirmed_by_close5_day_consistency",
        "hypothesis": "A=复杂度-熵平面到白噪声点距离水平（round_541 gate-7阶段与PA1 corr=0.85，因redundancy被拒）。B=收盘前5分钟方向一致性（bar_size_order_flow，本族首次配对）。假设：无效率程度高(A高)且尾盘方向一致性低(B低)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "PH2",
        "operator": "rank_spread",
        "left": _CEP_DIST,
        "right": _VOL_ENTROPY,
        "mechanism": "cep_distance_confirmed_by_volume_entropy",
        "hypothesis": "A=同上。B=日内成交量分布熵（intraday_volume_profile_1m，本族首次配对）。假设：无效率程度高(A高)且成交量分布熵低(B低，集中)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "PH3",
        "operator": "rank_spread",
        "left": _CEP_DIST,
        "right": _LIQ_COMMON_BETA,
        "mechanism": "cep_distance_confirmed_by_liquidity_common_beta",
        "hypothesis": "A=同上。B=流动性共性beta（liquidity_commonality_1m，本族首次配对）。假设：无效率程度高(A高)且流动性共性beta高(B高)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "PH4",
        "operator": "rank_spread",
        "left": _CEP_DIST,
        "right": _GRANGER_IN,
        "mechanism": "cep_distance_confirmed_by_granger_in_degree",
        "hypothesis": "A=同上。B=格兰杰因果入度（cross_dependence_1m，本族首次配对）。假设：无效率程度高(A高)且被同伴领先影响强(B高)=延续；诊断性测试，本腿最后一批。",
        "expected_sign": 1,
    },
    # ---- ENTROPY_RET_VOL_DIFF_20: 4-partner diagnostic ----
    {
        "id": "PI1",
        "operator": "rank_spread",
        "left": _ENTROPY_DIFF,
        "right": _BIGBAR_EDGE,
        "mechanism": "entropy_ret_vol_diff_confirmed_by_bigbar_edge_concentration",
        "hypothesis": "A=收益排列熵与成交量排列熵之差水平（round_541 gate-7阶段与PA1 corr=0.96，因redundancy被拒，本族相关性最高的诊断对象）。B=大bar集中于日内边缘时段的程度（bar_size_order_flow，本族首次配对）。假设：收益比成交量更随机(A高)且大bar集中在开盘/收盘边缘(B高)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "PI2",
        "operator": "rank_spread",
        "left": _ENTROPY_DIFF,
        "right": _COJUMP_INDEX,
        "mechanism": "entropy_ret_vol_diff_confirmed_by_cojump_index_share",
        "hypothesis": "A=同上。B=共跳占指数跳跃比例（cojump_1m，本族首次配对）。假设：收益比成交量更随机(A高)且与指数共跳比例高(B高)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "PI3",
        "operator": "rank_spread",
        "left": _ENTROPY_DIFF,
        "right": _PEER_LEAD_NET60,
        "mechanism": "entropy_ret_vol_diff_confirmed_by_peer_lead_network_corr",
        "hypothesis": "A=同上。B=同伴网络领先相关性，60日（cross_etf_lead_lag，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：收益比成交量更随机(A高)且网络领先关系强(B高)=延续；诊断性测试。",
        "expected_sign": 1,
    },
    {
        "id": "PI4",
        "operator": "rank_spread",
        "left": _ENTROPY_DIFF,
        "right": _GAP_SESSION_CORR,
        "mechanism": "entropy_ret_vol_diff_confirmed_by_gap_session_correlation",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性（gap_response，S4阶段最强命中partner，本族首次配对）。假设：收益比成交量更随机(A高)且跳空延续性强(B高)=延续；诊断性测试，本腿最后一批，也是本族最后一批。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
