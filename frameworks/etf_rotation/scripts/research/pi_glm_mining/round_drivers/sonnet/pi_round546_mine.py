#!/usr/bin/env python3
"""Round 546 driver: S7 stage step 2 -- intraday_drawdown_1m pairing,
round 2. Two independent first-pairing batches, per the pairing-
discipline rule:

1. INTRADAY_MAXDD_CHG_20 (round_545 atomic: t=0.23, weak alone, but audit
   IC +0.0600 was the second-strongest non-shadow reading in atom_health
   -- the atomic test failed mainly on audit-sign instability + identity,
   the same failure pattern that AD_NET_FLOW_SLOPE_20 showed in S10
   before a confirming partner (VOL_PROFILE_DISTANCE) rescued it. Testing
   whether the same rescue pattern applies here.

2. INTRADAY_MAXDD_20 (atom-health shadow vs downside_risk, 0.80; atomic
   test QA1 had t=2.85 but audit excess essentially zero, -1.0bp --
   failed the bp floor, not redundancy). Per the S4/S6/S10 precedent
   (JB2, PA1-adjacent CEP_DISTANCE_20, MFI_EXTREME_FRAC_20 all cleared
   the official dedup gate despite atom-health shadow flags), this
   round tests whether a confirming partner can push the bp excess over
   the +5bp floor while keeping the already-strong discovery t.

All right-leg partners below are new to this family's S7 pairing history
(round_545's 8 partners, all already used with UNDERWATER_FRAC_20, are
not repeated here). No same-family pairs, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_546"

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

_MAXDD_CHG = {"name": "INTRADAY_MAXDD_CHG_20", "source": "intraday_drawdown_1m"}
_MAXDD = {"name": "INTRADAY_MAXDD_20", "source": "intraday_drawdown_1m"}

base.CANDIDATES = [
    # ---- INTRADAY_MAXDD_CHG_20: first pairing batch (weak alone, second-
    # strongest non-shadow audit IC, testing the confirming-partner rescue
    # pattern) ----
    {
        "id": "QC1",
        "operator": "rank_spread",
        "left": _MAXDD_CHG,
        "right": _TICK_IMB,
        "mechanism": "maxdd_chg_confirmed_by_tick_imbalance",
        "hypothesis": "A=日内最大回撤20日变化（体检审计+0.0600，本族第二强非shadow原子；atomic测试QA7因audit符号翻转+identity不稳定未过）。B=1m order flow不平衡（bar_size_order_flow，本族首次配对）。假设：日内回撤正在扩大(A高)且订单流不平衡加剧(B高)=回撤扩大有订单流确认，可能筛选出更稳定的子集，延续。",
        "expected_sign": 1,
    },
    {
        "id": "QC2",
        "operator": "rank_spread",
        "left": _MAXDD_CHG,
        "right": _VOL_AUTOCORR,
        "mechanism": "maxdd_chg_confirmed_by_volume_autocorr",
        "hypothesis": "A=同上。B=成交量自相关（intraday_volume_profile_1m，本族首次配对）。假设：日内回撤扩大(A高)且成交量呈现持续性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QC3",
        "operator": "rank_spread",
        "left": _MAXDD_CHG,
        "right": _RSKEW20,
        "mechanism": "maxdd_chg_confirmed_by_return_skew_20",
        "hypothesis": "A=同上。B=20日收益偏度（return_tail_shape，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：日内回撤扩大(A高)且收益分布偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QC4",
        "operator": "rank_spread",
        "left": _MAXDD_CHG,
        "right": _CLOSE30,
        "mechanism": "maxdd_chg_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上。B=收盘30分钟成交占比（intraday_volume_profile_1m，本族首次配对）。假设：日内回撤扩大(A高)且尾盘集中放量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QC5",
        "operator": "rank_spread",
        "left": _MAXDD_CHG,
        "right": _LBAR_OVERNIGHT,
        "mechanism": "maxdd_chg_confirmed_by_bigbar_overnight",
        "hypothesis": "A=同上。B=大bar隔夜分量（largebar_footprint_1m，S4阶段JUMP_BETA_STABILITY_20命中partner，本族首次配对）。假设：日内回撤扩大(A高)且隔夜大bar分量高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QC6",
        "operator": "rank_spread",
        "left": _MAXDD_CHG,
        "right": _MAX5_MEAN20,
        "mechanism": "maxdd_chg_confirmed_by_max5_mean",
        "hypothesis": "A=同上。B=最大5日收益均值（upside_tail，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：日内回撤扩大(A高)且近期有强正向单日(B高)=矛盾信号或反转确认，延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "QC7",
        "operator": "rank_spread",
        "left": _MAXDD_CHG,
        "right": _RET_ACF1_20,
        "mechanism": "maxdd_chg_confirmed_by_ret_acf1_20",
        "hypothesis": "A=同上。B=20日收益一阶自相关（serial_dependence，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：日内回撤扩大(A高)且自身收益呈现动量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QC8",
        "operator": "rank_spread",
        "left": _MAXDD_CHG,
        "right": _KYLE_LAMBDA,
        "mechanism": "maxdd_chg_confirmed_by_kyle_lambda",
        "hypothesis": "A=同上。B=Kyle价格冲击系数（microstructure_1m，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：日内回撤扩大(A高)且价格冲击系数高(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- INTRADAY_MAXDD_20: first pairing batch (atom-health shadow vs
    # downside_risk, but atomic QA1 had t=2.85 killed only by the bp
    # floor -- testing whether a partner pushes bp over +5) ----
    {
        "id": "QD1",
        "operator": "rank_spread",
        "left": _MAXDD,
        "right": _GRANGER_OUT,
        "mechanism": "maxdd_confirmed_by_granger_out_degree",
        "hypothesis": "A=日内最大回撤水平（atom-health shadow=True vs downside_risk 0.80，但官方去重只比shelf16+此前入选；atomic QA1 t=2.85，审计超额-1.0bp仅差bp门未过）。B=格兰杰因果出度（cross_dependence_1m，本族首次配对）。假设：日内最大回撤深(A高)且对同伴有更强领先性(B高)=延续，测试能否把t=2.85的discovery强度转化为正的审计超额。",
        "expected_sign": 1,
    },
    {
        "id": "QD2",
        "operator": "rank_spread",
        "left": _MAXDD,
        "right": _NET_SPILLOVER,
        "mechanism": "maxdd_confirmed_by_net_spillover",
        "hypothesis": "A=同上。B=净溢出效应（cross_dependence_1m，本族首次配对）。假设：日内回撤深(A高)且净溢出为正(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "QD3",
        "operator": "rank_spread",
        "left": _MAXDD,
        "right": _MKT_LEAD_CORR20,
        "mechanism": "maxdd_confirmed_by_market_lead_corr",
        "hypothesis": "A=同上。B=市场领先相关性（cross_etf_lead_lag，S4阶段CONTINUOUS_BETA_60命中partner，t=2.90，本族首次配对）。假设：日内回撤深(A高)且市场领先本资产(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QD4",
        "operator": "rank_spread",
        "left": _MAXDD,
        "right": _ASSET_LEAD_MKT20,
        "mechanism": "maxdd_confirmed_by_asset_lead_market_corr",
        "hypothesis": "A=同上。B=资产领先市场相关性（cross_etf_lead_lag，S4阶段CONTINUOUS_BETA_60命中partner，t=2.73，本族首次配对）。假设：日内回撤深(A高)且资产本身领先市场(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QD5",
        "operator": "rank_spread",
        "left": _MAXDD,
        "right": _REL_MOM20,
        "mechanism": "maxdd_confirmed_by_relative_market_momentum",
        "hypothesis": "A=同上。B=相对基准篮子动量，20日（market_relative_strength，本族首次配对）。假设：日内回撤深(A高)且相对基准动量弱(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "QD6",
        "operator": "rank_spread",
        "left": _MAXDD,
        "right": _IDIO_JUMP_SHARE,
        "mechanism": "maxdd_confirmed_by_idio_jump_share",
        "hypothesis": "A=同上。B=特异跳跃占比（cojump_1m，本族首次配对）。假设：日内回撤深(A高)且跳跃以特异性为主(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "QD7",
        "operator": "rank_spread",
        "left": _MAXDD,
        "right": _RESILIENCY,
        "mechanism": "maxdd_confirmed_by_liquidity_resiliency",
        "hypothesis": "A=同上。B=流动性恢复力（liquidity_commonality_1m，本族首次配对）。假设：日内回撤深(A高)且流动性恢复力弱(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "QD8",
        "operator": "rank_spread",
        "left": _MAXDD,
        "right": _COSKEW20,
        "mechanism": "maxdd_confirmed_by_coskewness_20",
        "hypothesis": "A=同上。B=20日协偏度（coskewness_risk，本族首次配对）。假设：日内回撤深(A高)且协偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
