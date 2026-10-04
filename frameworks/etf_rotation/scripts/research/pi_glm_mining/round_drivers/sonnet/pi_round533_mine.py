#!/usr/bin/env python3
"""Round 533 driver: S5 stage step 3 -- microstructure_noise_1m pairing,
round 3. Three independent first-pairing batches, per the pairing-
discipline rule (one batch of <=8 per left leg):

round_531 (1/16) and round_532 (0/16, first zero round) both showed the
"_CHG_20" noise-trend atoms landing large audit bp against activity/volume
partners but failing the block-t=2.0 floor by a small margin (t=1.34-1.92
across four such near-misses). Rather than continuing to probe the same
activity-theme partners against the two already-used _CHG legs (both used
up their one batch), this round opens the three remaining unused atoms
(SIG_PLOT_SLOPE_20, TSRV_RV1M_RATIO_20, NOISE_SIGNAL_RATIO_CHG_20) with a
genuinely different partner theme mix: liquidity-shock/resiliency,
co-jump-share, cross-dependence/spillover, and peer-relative-value --
families conceptually adjacent to microstructure noise (noise should
plausibly co-move with liquidity shocks, co-jump structure, and
information-flow spillovers) but never yet tried against ANY
microstructure_noise_1m atom.

All right-leg partners below are new to this family's cumulative S5
pairing history (round_531/532's ~16 partners are not repeated). No
same-family pairs, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_533"

_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_COJUMP_INDEX = {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"}
_BIGBAR_EDGE = {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"}
_VOL_PROFILE_DIST = {"name": "VOL_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_PROFIT_RATIO = {"name": "PROFIT_RATIO_60", "source": "cost_distribution"}
_GRANGER_OUT = {"name": "GRANGER_OUT_DEGREE_20", "source": "cross_dependence_1m"}
_PEER_RESID_Z = {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"}

_IDIO_JUMP_SHARE = {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"}
_COJUMP_DIR_AGREE = {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"}
_LBAR_SILENT = {"name": "LBAR_SILENT_20", "source": "largebar_footprint_1m"}
_TURNOVER_DIST = {"name": "TURNOVER_PROFILE_DISTANCE", "source": "intraday_profile_deviation"}
_VPIN_CLOSE = {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"}
_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_NET_SPILLOVER = {"name": "NET_SPILLOVER_20", "source": "cross_dependence_1m"}
_HKS_SLOT = {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"}

_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_LBAR_TREND = {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"}
_COSKEW60 = {"name": "COSKEW_60", "source": "coskewness_risk"}
_DOWNSIDE_COSKEW60 = {"name": "DOWNSIDE_COSKEW_60", "source": "coskewness_risk"}
_RET_ACF1_5 = {"name": "RET_ACF1_5", "source": "serial_dependence"}
_PEER_RESID_MOM = {"name": "PEER_RESID_MOM_20", "source": "peer_relative_value"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}
_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}

_SIG_SLOPE = {"name": "SIG_PLOT_SLOPE_20", "source": "microstructure_noise_1m"}
_TSRV_RATIO = {"name": "TSRV_RV1M_RATIO_20", "source": "microstructure_noise_1m"}
_NOISE_SIGNAL_CHG = {"name": "NOISE_SIGNAL_RATIO_CHG_20", "source": "microstructure_noise_1m"}

base.CANDIDATES = [
    # ---- SIG_PLOT_SLOPE_20: first pairing batch, liquidity/jump/spillover
    # theme (conceptually adjacent to microstructure noise, never tried) ----
    {
        "id": "ME1",
        "operator": "rank_spread",
        "left": _SIG_SLOPE,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "sig_plot_slope_confirmed_by_idio_liquidity_shock",
        "hypothesis": "A=已实现方差签名图斜率（ABDL 2000，体检审计-0.0342，非shadow）。B=特异流动性冲击z值（liquidity_commonality_1m，本族首次配对；噪声理论上应与流动性冲击同源）。假设：签名图斜率越陡(A更负)且特异流动性冲击大(B高)=高频噪声膨胀与流动性冲击同期发生，延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "ME2",
        "operator": "rank_spread",
        "left": _SIG_SLOPE,
        "right": _RESILIENCY,
        "mechanism": "sig_plot_slope_confirmed_by_liquidity_resiliency",
        "hypothesis": "A=同上。B=流动性恢复力（liquidity_commonality_1m，本族首次配对）。假设：签名图斜率越陡(A更负)且流动性恢复力弱(B低)=噪声持续更久缺乏快速修复，延续。",
        "expected_sign": 1,
    },
    {
        "id": "ME3",
        "operator": "rank_spread",
        "left": _SIG_SLOPE,
        "right": _COJUMP_INDEX,
        "mechanism": "sig_plot_slope_confirmed_by_cojump_index_share",
        "hypothesis": "A=同上。B=共跳占指数跳跃比例（cojump_1m，本族首次配对）。假设：签名图斜率越陡(A更负)且与指数共跳比例高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "ME4",
        "operator": "rank_spread",
        "left": _SIG_SLOPE,
        "right": _BIGBAR_EDGE,
        "mechanism": "sig_plot_slope_confirmed_by_bigbar_edge_concentration",
        "hypothesis": "A=同上。B=大bar集中于日内边缘时段的程度（bar_size_order_flow，本族首次配对）。假设：签名图斜率越陡(A更负)且大bar集中在开盘/收盘边缘(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "ME5",
        "operator": "rank_spread",
        "left": _SIG_SLOPE,
        "right": _VOL_PROFILE_DIST,
        "mechanism": "sig_plot_slope_confirmed_by_volume_profile_shift",
        "hypothesis": "A=同上。B=日内成交量分布偏离（intraday_profile_deviation，本线最高t单原子历史，本族首次配对）。假设：签名图斜率越陡(A更负)且日内成交结构异常(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "ME6",
        "operator": "rank_spread",
        "left": _SIG_SLOPE,
        "right": _PROFIT_RATIO,
        "mechanism": "sig_plot_slope_confirmed_by_profit_ratio",
        "hypothesis": "A=同上。B=60日获利比例（cost_distribution，本族首次配对）。假设：签名图斜率越陡(A更负)且获利盘占比低(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "ME7",
        "operator": "rank_spread",
        "left": _SIG_SLOPE,
        "right": _GRANGER_OUT,
        "mechanism": "sig_plot_slope_confirmed_by_granger_out_degree",
        "hypothesis": "A=同上。B=格兰杰因果出度（cross_dependence_1m，本族首次配对；噪声结构可能与信息传导方向相关）。假设：签名图斜率越陡(A更负)且对同伴有更强领先性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "ME8",
        "operator": "rank_spread",
        "left": _SIG_SLOPE,
        "right": _PEER_RESID_Z,
        "mechanism": "sig_plot_slope_confirmed_by_peer_resid_z",
        "hypothesis": "A=同上。B=相对同伴的协整残差z值（peer_relative_value，S4阶段本线最高命中率家族，本族首次配对）。假设：签名图斜率越陡(A更负)且相对同伴出现正向偏离(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- TSRV_RV1M_RATIO_20: first pairing batch ----
    {
        "id": "MF1",
        "operator": "rank_spread",
        "left": _TSRV_RATIO,
        "right": _IDIO_JUMP_SHARE,
        "mechanism": "tsrv_ratio_confirmed_by_idio_jump_share",
        "hypothesis": "A=两尺度RV比值（Zhang-Mykland-Ait-Sahalia 2005简化代理，体检审计-0.0301，非shadow）。B=特异跳跃占比（cojump_1m，本族首次配对）。假设：粗/细尺度比值低(A低，噪声吸收多)且特异跳跃占比低(B低，跳跃以共振为主)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "MF2",
        "operator": "rank_spread",
        "left": _TSRV_RATIO,
        "right": _COJUMP_DIR_AGREE,
        "mechanism": "tsrv_ratio_confirmed_by_cojump_dir_agree",
        "hypothesis": "A=同上。B=共跳方向一致性（cojump_1m，本族首次配对）。假设：比值低(A低)且共跳方向一致性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MF3",
        "operator": "rank_spread",
        "left": _TSRV_RATIO,
        "right": _LBAR_SILENT,
        "mechanism": "tsrv_ratio_confirmed_by_bigbar_silent",
        "hypothesis": "A=同上。B=大bar沉寂期长度（largebar_footprint_1m，本族首次配对）。假设：比值低(A低)且近期大bar沉寂(B高，冲击稀疏)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MF4",
        "operator": "rank_spread",
        "left": _TSRV_RATIO,
        "right": _TURNOVER_DIST,
        "mechanism": "tsrv_ratio_confirmed_by_turnover_profile_shift",
        "hypothesis": "A=同上。B=日内换手分布偏离（intraday_profile_deviation，本族首次配对）。假设：比值低(A低)且日内换手结构异常(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MF5",
        "operator": "rank_spread",
        "left": _TSRV_RATIO,
        "right": _VPIN_CLOSE,
        "mechanism": "tsrv_ratio_confirmed_by_vpin",
        "hypothesis": "A=同上。B=收盘时点VPIN（microstructure_1m，本族首次配对；知情交易概率与噪声吸收度理论上相关）。假设：比值低(A低)且VPIN高(B高，知情交易占比高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MF6",
        "operator": "rank_spread",
        "left": _TSRV_RATIO,
        "right": _AMIHUD_1M,
        "mechanism": "tsrv_ratio_confirmed_by_amihud_1m",
        "hypothesis": "A=同上。B=Amihud非流动性比率的1m版本（microstructure_1m，本族首次配对）。假设：比值低(A低)且非流动性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MF7",
        "operator": "rank_spread",
        "left": _TSRV_RATIO,
        "right": _NET_SPILLOVER,
        "mechanism": "tsrv_ratio_confirmed_by_net_spillover",
        "hypothesis": "A=同上。B=净溢出效应（cross_dependence_1m，本族首次配对）。假设：比值低(A低)且净溢出为正(B高，净输出信息)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "MF8",
        "operator": "rank_spread",
        "left": _TSRV_RATIO,
        "right": _HKS_SLOT,
        "mechanism": "tsrv_ratio_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=同上。B=日内时段模式持续性（intraday_periodicity，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：比值低(A低)且日内时段模式稳定(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- NOISE_SIGNAL_RATIO_CHG_20: first pairing batch ----
    {
        "id": "MG1",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL_CHG,
        "right": _VOL_ENTROPY,
        "mechanism": "noise_signal_ratio_chg_confirmed_by_volume_entropy",
        "hypothesis": "A=噪声/信号比20日变化（体检审计+0.0069，非shadow）。B=日内成交量分布熵（intraday_volume_profile_1m，本族首次配对）。假设：噪声占比正在上升(A高)且成交量分布熵高(B高，分散无规律)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MG2",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL_CHG,
        "right": _LBAR_TREND,
        "mechanism": "noise_signal_ratio_chg_confirmed_by_bigbar_trend",
        "hypothesis": "A=同上。B=大bar方向性趋势强度（largebar_footprint_1m，本族首次配对）。假设：噪声占比上升(A高)且大bar呈趋势性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MG3",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL_CHG,
        "right": _COSKEW60,
        "mechanism": "noise_signal_ratio_chg_confirmed_by_coskewness_60",
        "hypothesis": "A=同上。B=60日协偏度（coskewness_risk，本族首次配对）。假设：噪声占比上升(A高)且协偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MG4",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL_CHG,
        "right": _DOWNSIDE_COSKEW60,
        "mechanism": "noise_signal_ratio_chg_confirmed_by_downside_coskewness",
        "hypothesis": "A=同上。B=条件协偏度，仅用市场下跌日计算（coskewness_risk，本族首次配对）。假设：噪声占比上升(A高)且下行协偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MG5",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL_CHG,
        "right": _RET_ACF1_5,
        "mechanism": "noise_signal_ratio_chg_confirmed_by_ret_acf1_5",
        "hypothesis": "A=同上。B=5日收益一阶自相关（serial_dependence，本族首次配对）。假设：噪声占比上升(A高)且短期收益呈现动量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MG6",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL_CHG,
        "right": _PEER_RESID_MOM,
        "mechanism": "noise_signal_ratio_chg_confirmed_by_peer_resid_momentum",
        "hypothesis": "A=同上。B=同伴协整残差动量（peer_relative_value，S4阶段CONTINUOUS_BETA_60命中partner，t=2.93，本族首次配对）。假设：噪声占比上升(A高)且相对同伴偏离扩大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MG7",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL_CHG,
        "right": _GAP_SESSION_CORR,
        "mechanism": "noise_signal_ratio_chg_confirmed_by_gap_session_correlation",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性（gap_response，S4阶段CONTINUOUS_BETA_60最强命中partner，t=3.89，本族首次配对）。假设：噪声占比上升(A高)且跳空延续性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MG8",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL_CHG,
        "right": _REL_MOM20,
        "mechanism": "noise_signal_ratio_chg_confirmed_by_relative_market_momentum",
        "hypothesis": "A=同上。B=相对基准篮子动量，20日（market_relative_strength，本族首次配对）。假设：噪声占比上升(A高)且相对基准动量异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
