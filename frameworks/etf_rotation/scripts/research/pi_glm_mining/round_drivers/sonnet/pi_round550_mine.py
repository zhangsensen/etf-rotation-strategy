#!/usr/bin/env python3
"""Round 550 driver: S8 stage step 2 -- realized_semicov_1m pairing,
round 2. Three independent first-pairing batches for the three
atom-health-shadow atoms not yet paired: SEMICOV_DOWNSIDE_BETA_20 (0.76
vs market_sensitivity:MARKET_BETA_60), SEMICOV_UPSIDE_BETA_20 (0.76 vs
jump_continuous_beta:CONTINUOUS_BETA_20), MIXED_NET_20 (0.74 vs
market_sensitivity:MARKET_BETA_60). Their round_549 atomic tests all had
strong discovery block-t (2.5-3.2) but failed on the audit-bp floor
(+1 to +6bp, below the +5bp gate) or redundancy -- the same failure
pattern that RCOV_N_SHARE_20's sibling atoms showed. Per the session-wide
"shadow-atom-rescue" pattern (6 confirmed instances across S4/S5/S6/S7/
S10), this round tests whether a confirming partner can push each atom's
bp excess over the floor while preserving the already-strong discovery t.

All right-leg partners below are new to this family's S8 pairing history
(round_549's 8 partners, all already used with RCOV_P_SHARE_20, are not
repeated here). No same-family pairs, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_550"

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

_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_LBAR_CLOCK = {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"}
_ROLL_SPREAD_DAILY = {"name": "ROLL_SPREAD_20", "source": "microstructure_1m"}
_OFI_AUTOCORR = {"name": "OFI_AUTOCORR_20", "source": "microstructure_1m"}
_RS_MINUS20 = {"name": "RS_MINUS_20", "source": "realized_measures_1m"}
_CLOSE5_CONSIST = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_PEER_RESID_MOM = {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"}

_SEMICOV_DOWN = {"name": "SEMICOV_DOWNSIDE_BETA_20", "source": "realized_semicov_1m"}
_SEMICOV_UP = {"name": "SEMICOV_UPSIDE_BETA_20", "source": "realized_semicov_1m"}
_MIXED_NET = {"name": "MIXED_NET_20", "source": "realized_semicov_1m"}

base.CANDIDATES = [
    # ---- SEMICOV_DOWNSIDE_BETA_20: first pairing batch (shadow, atomic
    # RA3 had t=3.20 but audit bp only +1.0, failed the floor) ----
    {
        "id": "RC1",
        "operator": "rank_spread",
        "left": _SEMICOV_DOWN,
        "right": _TICK_IMB,
        "mechanism": "semicov_downside_beta_confirmed_by_tick_imbalance",
        "hypothesis": "A=下行beta（Ang-Chen-Xing 2006，atom-health shadow=True vs market_sensitivity:MARKET_BETA_60；round_549 atomic RA3 discovery t=3.20为本族最高，但审计超额仅+1.0bp未过bp门）。B=1m order flow不平衡（bar_size_order_flow，本族首次配对）。假设：下行beta高(A高)且订单流不平衡加剧(B高)=延续，测试能否把discovery强度转化为正的审计超额。",
        "expected_sign": 1,
    },
    {
        "id": "RC2",
        "operator": "rank_spread",
        "left": _SEMICOV_DOWN,
        "right": _VOL_AUTOCORR,
        "mechanism": "semicov_downside_beta_confirmed_by_volume_autocorr",
        "hypothesis": "A=同上。B=成交量自相关（intraday_volume_profile_1m，本族首次配对）。假设：下行beta高(A高)且成交量呈现持续性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RC3",
        "operator": "rank_spread",
        "left": _SEMICOV_DOWN,
        "right": _RSKEW20,
        "mechanism": "semicov_downside_beta_confirmed_by_return_skew_20",
        "hypothesis": "A=同上。B=20日收益偏度（return_tail_shape，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：下行beta高(A高)且收益分布偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RC4",
        "operator": "rank_spread",
        "left": _SEMICOV_DOWN,
        "right": _CLOSE30,
        "mechanism": "semicov_downside_beta_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上。B=收盘30分钟成交占比（intraday_volume_profile_1m，本族首次配对）。假设：下行beta高(A高)且尾盘集中放量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RC5",
        "operator": "rank_spread",
        "left": _SEMICOV_DOWN,
        "right": _LBAR_OVERNIGHT,
        "mechanism": "semicov_downside_beta_confirmed_by_bigbar_overnight",
        "hypothesis": "A=同上。B=大bar隔夜分量（largebar_footprint_1m，S4阶段JUMP_BETA_STABILITY_20命中partner，本族首次配对）。假设：下行beta高(A高)且隔夜大bar分量高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RC6",
        "operator": "rank_spread",
        "left": _SEMICOV_DOWN,
        "right": _MAX5_MEAN20,
        "mechanism": "semicov_downside_beta_confirmed_by_max5_mean",
        "hypothesis": "A=同上。B=最大5日收益均值（upside_tail，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：下行beta高(A高)且近期有强正向单日(B高)=矛盾信号，延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "RC7",
        "operator": "rank_spread",
        "left": _SEMICOV_DOWN,
        "right": _RET_ACF1_20,
        "mechanism": "semicov_downside_beta_confirmed_by_ret_acf1_20",
        "hypothesis": "A=同上。B=20日收益一阶自相关（serial_dependence，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：下行beta高(A高)且自身收益呈现动量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RC8",
        "operator": "rank_spread",
        "left": _SEMICOV_DOWN,
        "right": _KYLE_LAMBDA,
        "mechanism": "semicov_downside_beta_confirmed_by_kyle_lambda",
        "hypothesis": "A=同上。B=Kyle价格冲击系数（microstructure_1m，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：下行beta高(A高)且价格冲击系数高(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- SEMICOV_UPSIDE_BETA_20: first pairing batch (shadow) ----
    {
        "id": "RD1",
        "operator": "rank_spread",
        "left": _SEMICOV_UP,
        "right": _GRANGER_OUT,
        "mechanism": "semicov_upside_beta_confirmed_by_granger_out_degree",
        "hypothesis": "A=上行beta（atom-health shadow=True vs jump_continuous_beta:CONTINUOUS_BETA_20；round_549 atomic RA4 t=2.47，审计超额+3.0bp仅差bp门）。B=格兰杰因果出度（cross_dependence_1m，本族首次配对）。假设：上行beta高(A高)且对同伴有更强领先性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RD2",
        "operator": "rank_spread",
        "left": _SEMICOV_UP,
        "right": _NET_SPILLOVER,
        "mechanism": "semicov_upside_beta_confirmed_by_net_spillover",
        "hypothesis": "A=同上。B=净溢出效应（cross_dependence_1m，本族首次配对）。假设：上行beta高(A高)且净溢出为正(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "RD3",
        "operator": "rank_spread",
        "left": _SEMICOV_UP,
        "right": _MKT_LEAD_CORR20,
        "mechanism": "semicov_upside_beta_confirmed_by_market_lead_corr",
        "hypothesis": "A=同上。B=市场领先相关性（cross_etf_lead_lag，S4阶段CONTINUOUS_BETA_60命中partner，t=2.90，本族首次配对）。假设：上行beta高(A高)且市场领先本资产(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RD4",
        "operator": "rank_spread",
        "left": _SEMICOV_UP,
        "right": _ASSET_LEAD_MKT20,
        "mechanism": "semicov_upside_beta_confirmed_by_asset_lead_market_corr",
        "hypothesis": "A=同上。B=资产领先市场相关性（cross_etf_lead_lag，S4阶段CONTINUOUS_BETA_60命中partner，t=2.73，本族首次配对）。假设：上行beta高(A高)且资产本身领先市场(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RD5",
        "operator": "rank_spread",
        "left": _SEMICOV_UP,
        "right": _REL_MOM20,
        "mechanism": "semicov_upside_beta_confirmed_by_relative_market_momentum",
        "hypothesis": "A=同上。B=相对基准篮子动量，20日（market_relative_strength，本族首次配对）。假设：上行beta高(A高)且相对基准动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RD6",
        "operator": "rank_spread",
        "left": _SEMICOV_UP,
        "right": _IDIO_JUMP_SHARE,
        "mechanism": "semicov_upside_beta_confirmed_by_idio_jump_share",
        "hypothesis": "A=同上。B=特异跳跃占比（cojump_1m，本族首次配对）。假设：上行beta高(A高)且跳跃以特异性为主(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "RD7",
        "operator": "rank_spread",
        "left": _SEMICOV_UP,
        "right": _RESILIENCY,
        "mechanism": "semicov_upside_beta_confirmed_by_liquidity_resiliency",
        "hypothesis": "A=同上。B=流动性恢复力（liquidity_commonality_1m，本族首次配对）。假设：上行beta高(A高)且流动性恢复力强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RD8",
        "operator": "rank_spread",
        "left": _SEMICOV_UP,
        "right": _COSKEW20,
        "mechanism": "semicov_upside_beta_confirmed_by_coskewness_20",
        "hypothesis": "A=同上。B=20日协偏度（coskewness_risk，本族首次配对）。假设：上行beta高(A高)且协偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    # ---- MIXED_NET_20: first pairing batch (shadow, atomic RA6 had
    # t=2.23 but audit bp only +6.4, and pairing RB2 in round_549 was
    # redundant against RCOV_N_SHARE_20 rather than this atom) ----
    {
        "id": "RE1",
        "operator": "rank_spread",
        "left": _MIXED_NET,
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "mixed_net_confirmed_by_bigbar_vol_share",
        "hypothesis": "A=混合分量净值占比（atom-health shadow=True vs market_sensitivity:MARKET_BETA_60；round_549 atomic RA6 t=2.23，审计超额+6.4bp已过门但discovery受BLPQ框架内相关atoms稀释，未跑pairing）。B=大bar成交量占比（bar_size_order_flow，本族首次配对）。假设：混合分量占比高(A高)且大bar贡献成交量占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RE2",
        "operator": "rank_spread",
        "left": _MIXED_NET,
        "right": _LBAR_CLOCK,
        "mechanism": "mixed_net_confirmed_by_lbar_clock_std",
        "hypothesis": "A=同上。B=大bar发生时点的20日标准差（largebar_footprint_1m，本族首次配对）。假设：混合分量占比高(A高)且大bar发生时点分散(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RE3",
        "operator": "rank_spread",
        "left": _MIXED_NET,
        "right": _ROLL_SPREAD_DAILY,
        "mechanism": "mixed_net_confirmed_by_daily_roll_spread",
        "hypothesis": "A=同上。B=日频Roll隐含价差（microstructure_1m，本族首次配对）。假设：混合分量占比高(A高)且日频隐含价差大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RE4",
        "operator": "rank_spread",
        "left": _MIXED_NET,
        "right": _OFI_AUTOCORR,
        "mechanism": "mixed_net_confirmed_by_ofi_autocorr",
        "hypothesis": "A=同上。B=订单流不平衡自相关（microstructure_1m，本族首次配对）。假设：混合分量占比高(A高)且订单流不平衡持续性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RE5",
        "operator": "rank_spread",
        "left": _MIXED_NET,
        "right": _RS_MINUS20,
        "mechanism": "mixed_net_confirmed_by_realized_semivariance_minus",
        "hypothesis": "A=同上。B=已实现负半方差占比（realized_measures_1m，S4阶段CONTINUOUS_BETA_60命中partner，t=2.34，本族首次配对）。假设：混合分量占比高(A高)且下行半方差占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RE6",
        "operator": "rank_spread",
        "left": _MIXED_NET,
        "right": _CLOSE5_CONSIST,
        "mechanism": "mixed_net_confirmed_by_close5_day_consistency",
        "hypothesis": "A=同上。B=收盘前5分钟方向一致性（bar_size_order_flow，本族首次配对）。假设：混合分量占比高(A高)且尾盘方向一致性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RE7",
        "operator": "rank_spread",
        "left": _MIXED_NET,
        "right": _VOL_ENTROPY,
        "mechanism": "mixed_net_confirmed_by_volume_entropy",
        "hypothesis": "A=同上。B=日内成交量分布熵（intraday_volume_profile_1m，本族首次配对）。假设：混合分量占比高(A高)且成交量分布熵低(B低，集中)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RE8",
        "operator": "rank_spread",
        "left": _MIXED_NET,
        "right": _PEER_RESID_MOM,
        "mechanism": "mixed_net_confirmed_by_peer_resid_momentum",
        "hypothesis": "A=同上。B=同伴协整残差动量（peer_relative_value，S4阶段CONTINUOUS_BETA_60命中partner，t=2.93，本族首次配对）。假设：混合分量占比高(A高)且相对同伴偏离扩大(B高)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
