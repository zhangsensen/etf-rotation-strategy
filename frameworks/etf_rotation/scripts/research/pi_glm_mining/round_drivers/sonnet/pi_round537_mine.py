#!/usr/bin/env python3
"""Round 537 driver: S10 stage step 2 -- accumulation_distribution_1m
pairing, round 2. Two independent first-pairing batches, per the
pairing-discipline rule:

1. MFI_14_MEAN_20 (round_536 atomic: t=2.04, closest-to-threshold
   non-shadow atom after OBV_SLOPE_CHG_20's batch produced nothing).
   Money-flow/volume theme, paired with volume/liquidity-level partners.

2. AD_PRICE_CORR_20 (round_536's sole admission, atomic t=2.09 +13.0bp --
   "follow the significant channel"). Volume-price lead/lag theme, paired
   with other co-movement/lead-lag constructs (cross_dependence_1m,
   cross_etf_lead_lag) that are conceptually the closest match to what
   this atom measures.

All right-leg partners below are new to this family's S10 pairing history
(round_536's 8 partners are not repeated). No same-family pairs, no
window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_537"

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

_MFI_MEAN = {"name": "MFI_14_MEAN_20", "source": "accumulation_distribution_1m"}
_AD_PRICE_CORR = {"name": "AD_PRICE_CORR_20", "source": "accumulation_distribution_1m"}

base.CANDIDATES = [
    # ---- MFI_14_MEAN_20: first pairing batch (round_536 atomic t=2.04,
    # closest non-shadow atom to threshold) ----
    {
        "id": "NC1",
        "operator": "rank_spread",
        "left": _MFI_MEAN,
        "right": _TICK_IMB,
        "mechanism": "mfi_confirmed_by_tick_imbalance",
        "hypothesis": "A=资金流量指标MFI(14 bar)日均值（Quong-Soudack 1989，round_536体检disc+0.0284/审计+0.0105，atomic门7 t=2.04仅差bp）。B=1m order flow不平衡（bar_size_order_flow，本族首次配对）。假设：资金流入占优(A高)且订单流不平衡加剧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NC2",
        "operator": "rank_spread",
        "left": _MFI_MEAN,
        "right": _VOL_AUTOCORR,
        "mechanism": "mfi_confirmed_by_volume_autocorr",
        "hypothesis": "A=同上。B=成交量自相关（intraday_volume_profile_1m，本族首次配对）。假设：资金流入占优(A高)且成交量呈现持续性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NC3",
        "operator": "rank_spread",
        "left": _MFI_MEAN,
        "right": _RSKEW20,
        "mechanism": "mfi_confirmed_by_return_skew_20",
        "hypothesis": "A=同上。B=20日收益偏度（return_tail_shape，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：资金流入占优(A高)且收益分布偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NC4",
        "operator": "rank_spread",
        "left": _MFI_MEAN,
        "right": _CLOSE30,
        "mechanism": "mfi_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上。B=收盘30分钟成交占比（intraday_volume_profile_1m，本族首次配对）。假设：资金流入占优(A高)且尾盘集中放量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NC5",
        "operator": "rank_spread",
        "left": _MFI_MEAN,
        "right": _LBAR_OVERNIGHT,
        "mechanism": "mfi_confirmed_by_bigbar_overnight",
        "hypothesis": "A=同上。B=大bar隔夜分量（largebar_footprint_1m，S4阶段JUMP_BETA_STABILITY_20命中partner，本族首次配对）。假设：资金流入占优(A高)且隔夜大bar分量高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NC6",
        "operator": "rank_spread",
        "left": _MFI_MEAN,
        "right": _MAX5_MEAN20,
        "mechanism": "mfi_confirmed_by_max5_mean",
        "hypothesis": "A=同上。B=最大5日收益均值（upside_tail，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：资金流入占优(A高)且近期有强正向单日(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NC7",
        "operator": "rank_spread",
        "left": _MFI_MEAN,
        "right": _RET_ACF1_20,
        "mechanism": "mfi_confirmed_by_ret_acf1_20",
        "hypothesis": "A=同上。B=20日收益一阶自相关（serial_dependence，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：资金流入占优(A高)且自身收益呈现动量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NC8",
        "operator": "rank_spread",
        "left": _MFI_MEAN,
        "right": _KYLE_LAMBDA,
        "mechanism": "mfi_confirmed_by_kyle_lambda",
        "hypothesis": "A=同上。B=Kyle价格冲击系数（microstructure_1m，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：资金流入占优(A高)且价格冲击系数高(B高，流动性薄，资金流影响力大)=延续。",
        "expected_sign": 1,
    },
    # ---- AD_PRICE_CORR_20: first pairing batch, follow the significant
    # channel (round_536's sole admission, atomic t=2.09 +13.0bp) ----
    {
        "id": "ND1",
        "operator": "rank_spread",
        "left": _AD_PRICE_CORR,
        "right": _GRANGER_OUT,
        "mechanism": "ad_price_corr_confirmed_by_granger_out_degree",
        "hypothesis": "A=量流与同期收益的相关性（Blume-Easley-O'Hara 1994，round_536已atomic入选，t=2.09 +13.0bp）。B=格兰杰因果出度（cross_dependence_1m，本族首次配对；理论上量价同步性与信息传导方向应相关）。假设：量价同步性低(A低，量价背离)且对同伴有更强领先性(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "ND2",
        "operator": "rank_spread",
        "left": _AD_PRICE_CORR,
        "right": _NET_SPILLOVER,
        "mechanism": "ad_price_corr_confirmed_by_net_spillover",
        "hypothesis": "A=同上。B=净溢出效应（cross_dependence_1m，本族首次配对）。假设：量价同步性低(A低)且净溢出为正(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "ND3",
        "operator": "rank_spread",
        "left": _AD_PRICE_CORR,
        "right": _MKT_LEAD_CORR20,
        "mechanism": "ad_price_corr_confirmed_by_market_lead_corr",
        "hypothesis": "A=同上。B=市场领先相关性（cross_etf_lead_lag，S4阶段CONTINUOUS_BETA_60命中partner，t=2.90，本族首次配对）。假设：量价背离(A低)且市场领先本资产(B高，价格发现滞后)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "ND4",
        "operator": "rank_spread",
        "left": _AD_PRICE_CORR,
        "right": _ASSET_LEAD_MKT20,
        "mechanism": "ad_price_corr_confirmed_by_asset_lead_market_corr",
        "hypothesis": "A=同上。B=资产领先市场相关性（cross_etf_lead_lag，S4阶段CONTINUOUS_BETA_60命中partner，t=2.73，本族首次配对）。假设：量价背离(A低)且资产本身领先市场(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "ND5",
        "operator": "rank_spread",
        "left": _AD_PRICE_CORR,
        "right": _REL_MOM20,
        "mechanism": "ad_price_corr_confirmed_by_relative_market_momentum",
        "hypothesis": "A=同上。B=相对基准篮子动量，20日（market_relative_strength，本族首次配对）。假设：量价背离(A低)且相对基准动量异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "ND6",
        "operator": "rank_spread",
        "left": _AD_PRICE_CORR,
        "right": _IDIO_JUMP_SHARE,
        "mechanism": "ad_price_corr_confirmed_by_idio_jump_share",
        "hypothesis": "A=同上。B=特异跳跃占比（cojump_1m，本族首次配对）。假设：量价背离(A低)且跳跃以特异性为主(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "ND7",
        "operator": "rank_spread",
        "left": _AD_PRICE_CORR,
        "right": _RESILIENCY,
        "mechanism": "ad_price_corr_confirmed_by_liquidity_resiliency",
        "hypothesis": "A=同上。B=流动性恢复力（liquidity_commonality_1m，S5阶段MH6候选partner，本族首次配对）。假设：量价背离(A低)且流动性恢复力弱(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "ND8",
        "operator": "rank_spread",
        "left": _AD_PRICE_CORR,
        "right": _COSKEW20,
        "mechanism": "ad_price_corr_confirmed_by_coskewness_20",
        "hypothesis": "A=同上。B=20日协偏度（coskewness_risk，本族首次配对）。假设：量价背离(A低)且协偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
