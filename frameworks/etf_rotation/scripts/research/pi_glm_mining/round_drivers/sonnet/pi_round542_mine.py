#!/usr/bin/env python3
"""Round 542 driver: S6 stage step 2 -- permutation_entropy_1m pairing,
round 2. Two independent first-pairing batches, per the pairing-
discipline rule:

1. PERM_ENTROPY_VOL_20 (volume-domain ordinal-pattern entropy, atom-health
   audit -0.032 -- weaker than PERM_ENTROPY_RET_20 but structurally
   distinct: computed from the 1m VOLUME sequence, not returns, so it
   should carry much lower rank-correlation with round_541's admitted
   PA1 than STAT_COMPLEXITY_20/CEP_DISTANCE_20/ENTROPY_RET_VOL_DIFF_20
   did (those three all mathematically share PA1's H_ret component and
   got blocked on redundancy at 0.77-0.96).

2. PERM_ENTROPY_RET_CHG_20 (20-day change/detrended version of the
   admitted atom -- a different temporal aspect, plausibly much less
   correlated with the raw level than the other same-domain atoms were).

All right-leg partners below are new to this family's S6 pairing history
(round_541's 8 partners, all already used with PERM_ENTROPY_RET_20, are
not repeated here). No same-family pairs, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_542"

_TICK_IMB = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}
_VOL_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_RSKEW20 = {"name": "RETURN_SKEW_20", "source": "return_tail_shape"}
_CLOSE30 = {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_LBAR_OVERNIGHT = {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"}
_MAX5_MEAN20 = {"name": "MAX5_MEAN_20", "source": "upside_tail"}
_RET_ACF1_20 = {"name": "RET_ACF1_20", "source": "serial_dependence"}
_KYLE_LAMBDA = {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"}

_GRANGER_OUT = {"name": "GRANGER_OUT_DEGREE_20", "source": "cross_dependence_1m"}
_NET_SPILLOVER = {"name": "NET_SPILLOVER_20", "source": "cross_dependence_1m"}
_MKT_LEAD_CORR20 = {"name": "MARKET_LEAD_CORR_20", "source": "cross_etf_lead_lag"}
_ASSET_LEAD_MKT20 = {"name": "ASSET_LEAD_MARKET_CORR_20", "source": "cross_etf_lead_lag"}
_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_IDIO_JUMP_SHARE = {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_COSKEW20 = {"name": "COSKEW_20", "source": "coskewness_risk"}

_PE_VOL = {"name": "PERM_ENTROPY_VOL_20", "source": "permutation_entropy_1m"}
_PE_RET_CHG = {"name": "PERM_ENTROPY_RET_CHG_20", "source": "permutation_entropy_1m"}

base.CANDIDATES = [
    # ---- PERM_ENTROPY_VOL_20: first pairing batch (volume-domain,
    # structurally distinct from the admitted PA1) ----
    {
        "id": "PC1",
        "operator": "rank_spread",
        "left": _PE_VOL,
        "right": _TICK_IMB,
        "mechanism": "perm_entropy_vol_confirmed_by_tick_imbalance",
        "hypothesis": "A=1m成交量序列排列熵（Bandt-Pompe 2002应用于成交量到达，体检审计-0.0321，与round_541已入选的PA1(收益域)结构上不同，相关性应显著更低）。B=1m order flow不平衡（bar_size_order_flow，本族首次配对）。假设：成交量到达序型熵高(A高，到达模式随机)且订单流不平衡加剧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC2",
        "operator": "rank_spread",
        "left": _PE_VOL,
        "right": _VOL_AUTOCORR,
        "mechanism": "perm_entropy_vol_confirmed_by_volume_autocorr",
        "hypothesis": "A=同上。B=成交量自相关（intraday_volume_profile_1m，本族首次配对；与A互补——A测序型复杂度，B测线性自相关）。假设：成交量到达熵高(A高)且成交量呈现持续性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC3",
        "operator": "rank_spread",
        "left": _PE_VOL,
        "right": _RSKEW20,
        "mechanism": "perm_entropy_vol_confirmed_by_return_skew_20",
        "hypothesis": "A=同上。B=20日收益偏度（return_tail_shape，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：成交量到达熵高(A高)且收益分布偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC4",
        "operator": "rank_spread",
        "left": _PE_VOL,
        "right": _CLOSE30,
        "mechanism": "perm_entropy_vol_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上。B=收盘30分钟成交占比（intraday_volume_profile_1m，本族首次配对）。假设：成交量到达熵高(A高)且尾盘集中放量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC5",
        "operator": "rank_spread",
        "left": _PE_VOL,
        "right": _LBAR_OVERNIGHT,
        "mechanism": "perm_entropy_vol_confirmed_by_bigbar_overnight",
        "hypothesis": "A=同上。B=大bar隔夜分量（largebar_footprint_1m，S4阶段JUMP_BETA_STABILITY_20命中partner，本族首次配对）。假设：成交量到达熵高(A高)且隔夜大bar分量高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC6",
        "operator": "rank_spread",
        "left": _PE_VOL,
        "right": _MAX5_MEAN20,
        "mechanism": "perm_entropy_vol_confirmed_by_max5_mean",
        "hypothesis": "A=同上。B=最大5日收益均值（upside_tail，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：成交量到达熵高(A高)且近期有强正向单日(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC7",
        "operator": "rank_spread",
        "left": _PE_VOL,
        "right": _RET_ACF1_20,
        "mechanism": "perm_entropy_vol_confirmed_by_ret_acf1_20",
        "hypothesis": "A=同上。B=20日收益一阶自相关（serial_dependence，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：成交量到达熵高(A高)且自身收益呈现动量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PC8",
        "operator": "rank_spread",
        "left": _PE_VOL,
        "right": _KYLE_LAMBDA,
        "mechanism": "perm_entropy_vol_confirmed_by_kyle_lambda",
        "hypothesis": "A=同上。B=Kyle价格冲击系数（microstructure_1m，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：成交量到达熵高(A高)且价格冲击系数高(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- PERM_ENTROPY_RET_CHG_20: first pairing batch (20d change,
    # temporally distinct from the admitted level atom) ----
    {
        "id": "PD1",
        "operator": "rank_spread",
        "left": _PE_RET_CHG,
        "right": _GRANGER_OUT,
        "mechanism": "perm_entropy_ret_chg_confirmed_by_granger_out_degree",
        "hypothesis": "A=收益排列熵20日变化（效率regime切换，体检审计+0.0102）。B=格兰杰因果出度（cross_dependence_1m，本族首次配对）。假设：排列熵正在上升(A高，效率提高)且对同伴有更强领先性(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "PD2",
        "operator": "rank_spread",
        "left": _PE_RET_CHG,
        "right": _NET_SPILLOVER,
        "mechanism": "perm_entropy_ret_chg_confirmed_by_net_spillover",
        "hypothesis": "A=同上。B=净溢出效应（cross_dependence_1m，本族首次配对）。假设：排列熵上升(A高)且净溢出为正(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "PD3",
        "operator": "rank_spread",
        "left": _PE_RET_CHG,
        "right": _MKT_LEAD_CORR20,
        "mechanism": "perm_entropy_ret_chg_confirmed_by_market_lead_corr",
        "hypothesis": "A=同上。B=市场领先相关性（cross_etf_lead_lag，S4阶段CONTINUOUS_BETA_60命中partner，t=2.90，本族首次配对）。假设：排列熵上升(A高)且市场领先本资产(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PD4",
        "operator": "rank_spread",
        "left": _PE_RET_CHG,
        "right": _ASSET_LEAD_MKT20,
        "mechanism": "perm_entropy_ret_chg_confirmed_by_asset_lead_market_corr",
        "hypothesis": "A=同上。B=资产领先市场相关性（cross_etf_lead_lag，S4阶段CONTINUOUS_BETA_60命中partner，t=2.73，本族首次配对）。假设：排列熵上升(A高)且资产本身领先市场(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PD5",
        "operator": "rank_spread",
        "left": _PE_RET_CHG,
        "right": _REL_MOM20,
        "mechanism": "perm_entropy_ret_chg_confirmed_by_relative_market_momentum",
        "hypothesis": "A=同上。B=相对基准篮子动量，20日（market_relative_strength，本族首次配对）。假设：排列熵上升(A高)且相对基准动量异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PD6",
        "operator": "rank_spread",
        "left": _PE_RET_CHG,
        "right": _IDIO_JUMP_SHARE,
        "mechanism": "perm_entropy_ret_chg_confirmed_by_idio_jump_share",
        "hypothesis": "A=同上。B=特异跳跃占比（cojump_1m，本族首次配对）。假设：排列熵上升(A高)且跳跃以特异性为主(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "PD7",
        "operator": "rank_spread",
        "left": _PE_RET_CHG,
        "right": _RESILIENCY,
        "mechanism": "perm_entropy_ret_chg_confirmed_by_liquidity_resiliency",
        "hypothesis": "A=同上。B=流动性恢复力（liquidity_commonality_1m，S10阶段候选partner，本族首次配对）。假设：排列熵上升(A高)且流动性恢复力强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PD8",
        "operator": "rank_spread",
        "left": _PE_RET_CHG,
        "right": _COSKEW20,
        "mechanism": "perm_entropy_ret_chg_confirmed_by_coskewness_20",
        "hypothesis": "A=同上。B=20日协偏度（coskewness_risk，本族首次配对）。假设：排列熵上升(A高)且协偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
