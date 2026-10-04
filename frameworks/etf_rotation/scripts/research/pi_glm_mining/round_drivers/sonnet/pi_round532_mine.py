#!/usr/bin/env python3
"""Round 532 driver: S5 stage step 2 -- microstructure_noise_1m pairing,
round 2. Two independent first-pairing batches this round, per the
pairing-discipline rule (one batch of <=8 per left leg, right legs all
cross-family within a batch):

1. ROLL_NOISE_PROXY_CHG_20 (round_531 atom_health: audit -0.1147, second
   strongest non-shadow atom after NOISE_VAR_CHG_20 which used its one
   batch last round). Structurally similar to NOISE_VAR_CHG_20 (both are
   20-day noise-trend/change constructs), and round_531's activity-themed
   partners (VOL_SPIKE_FREQ_20, LOG_AMOUNT_VOL_20) produced large audit bp
   (+73bp/+76bp) but sub-2.0 block-t against NOISE_VAR_CHG_20 -- worth
   testing whether the same partner theme fares better against this
   related-but-distinct atom.

2. NOISE_SIGNAL_RATIO_20 (round_531 atom_health: audit +0.035, non-shadow,
   Hansen-Lunde 2006 noise-to-signal framing) -- its first pairing batch,
   using a fresh right-leg mix.

Right-leg reuse stays within the <=3-different-left-legs cap (round_531
used 8 atoms once each; this round reuses several a second time, all
staying at 2/3)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_532"

_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_TICK_IMB = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}
_VOL_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_RSKEW20 = {"name": "RETURN_SKEW_20", "source": "return_tail_shape"}
_CLOSE30 = {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}

_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_WORST_DAY20 = {"name": "WORST_DAY_20", "source": "return_tail_shape"}
_LBAR_OVERNIGHT = {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"}
_MAX5_MEAN20 = {"name": "MAX5_MEAN_20", "source": "upside_tail"}
_RET_ACF1_20 = {"name": "RET_ACF1_20", "source": "serial_dependence"}
_KYLE_LAMBDA = {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"}

_ROLL_CHG = {"name": "ROLL_NOISE_PROXY_CHG_20", "source": "microstructure_noise_1m"}
_NOISE_SIGNAL = {"name": "NOISE_SIGNAL_RATIO_20", "source": "microstructure_noise_1m"}

base.CANDIDATES = [
    # ---- ROLL_NOISE_PROXY_CHG_20: second-strongest non-shadow atom
    # (audit -0.1147), first pairing batch ----
    {
        "id": "MC1",
        "operator": "rank_spread",
        "left": _ROLL_CHG,
        "right": _VOL_SPIKE,
        "mechanism": "roll_noise_chg_confirmed_by_volume_spike_freq",
        "hypothesis": "A=日内Roll噪声代理20日变化（体检审计-0.1147，本族第二强非shadow原子）。B=成交量脉冲频率（intraday_volume_profile_1m；与NOISE_VAR_CHG_20配对时[round_531 MB2]审计+73.2bp但t=1.34未过）。假设：日内买卖价差噪声正在扩大(A高)且脉冲放量频繁(B高)=噪声扩大有交易活动确认，延续；测试同一partner主题对结构相似的另一原子是否更稳健。",
        "expected_sign": 1,
    },
    {
        "id": "MC2",
        "operator": "rank_spread",
        "left": _ROLL_CHG,
        "right": _LOG_AMT,
        "mechanism": "roll_noise_chg_confirmed_by_high_activity",
        "hypothesis": "A=同上。B=对数成交额（liquidity_variability；与NOISE_VAR_CHG_20配对时[round_531 MB5]审计+76.2bp但t=1.29未过）。假设：噪声扩大(A高)且整体活跃度高(B高)=延续；同一测试逻辑。",
        "expected_sign": 1,
    },
    {
        "id": "MC3",
        "operator": "rank_spread",
        "left": _ROLL_CHG,
        "right": _OPEN30,
        "mechanism": "roll_noise_chg_confirmed_by_open30_vol_share",
        "hypothesis": "A=同上。B=开盘30分钟成交占比（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：噪声扩大(A高)且开盘集中放量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MC4",
        "operator": "rank_spread",
        "left": _ROLL_CHG,
        "right": _TICK_IMB,
        "mechanism": "roll_noise_chg_confirmed_by_tick_imbalance",
        "hypothesis": "A=同上。B=1m order flow不平衡（bar_size_order_flow，本腿首次配对；与Roll价差噪声理论上同源——买卖不平衡是价差噪声的成因之一）。假设：噪声扩大(A高)且订单流不平衡加剧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MC5",
        "operator": "rank_spread",
        "left": _ROLL_CHG,
        "right": _VOL_AUTOCORR,
        "mechanism": "roll_noise_chg_confirmed_by_volume_autocorr",
        "hypothesis": "A=同上。B=成交量自相关（intraday_volume_profile_1m，本腿首次配对）。假设：噪声扩大(A高)且成交量呈现持续性(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MC6",
        "operator": "rank_spread",
        "left": _ROLL_CHG,
        "right": _CATEGORY_VOL,
        "mechanism": "roll_noise_chg_confirmed_by_category_vol",
        "hypothesis": "A=同上。B=同类别板块波动率（category_state，round_053门7全过史）。假设：噪声扩大(A高)且所属板块高波动(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MC7",
        "operator": "rank_spread",
        "left": _ROLL_CHG,
        "right": _RSKEW20,
        "mechanism": "roll_noise_chg_confirmed_by_return_skew_20",
        "hypothesis": "A=同上。B=20日收益偏度（return_tail_shape，本腿首次配对；S4阶段CONTINUOUS_BETA_60的确认partner之一）。假设：噪声扩大(A高)且收益分布偏度异常(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MC8",
        "operator": "rank_spread",
        "left": _ROLL_CHG,
        "right": _CLOSE30,
        "mechanism": "roll_noise_chg_confirmed_by_close30_vol_share",
        "hypothesis": "A=同上。B=收盘30分钟成交占比（intraday_volume_profile_1m，本腿首次配对，与开盘对称）。假设：噪声扩大(A高)且尾盘集中放量(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- NOISE_SIGNAL_RATIO_20: first pairing batch ----
    {
        "id": "MD1",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL,
        "right": _GAP_FILL60,
        "mechanism": "noise_signal_ratio_confirmed_by_gap_absorption",
        "hypothesis": "A=噪声/信号比（Hansen-Lunde 2006框架，体检审计+0.0346，非shadow）。B=60日窗缺口回补比例（gap_repair，round_053门7全过史）。假设：噪声占比高(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MD2",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL,
        "right": _BIGBAR_DIR_SKEW,
        "mechanism": "noise_signal_ratio_confirmed_by_bigbar_dir_skew",
        "hypothesis": "A=同上。B=大bar方向偏斜（bar_size_order_flow，S4阶段最强confirming partner之一，t=3.48）。假设：噪声占比高(A高)且大bar方向持续偏向一侧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MD3",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL,
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "noise_signal_ratio_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=同伴OU回归半衰期（peer_relative_value，S4阶段本线最高命中率家族，t=3.75）。假设：噪声占比高(A高)且相对同伴回复速度慢(B高)=价格发现效率低，延续。",
        "expected_sign": 1,
    },
    {
        "id": "MD4",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL,
        "right": _WORST_DAY20,
        "mechanism": "noise_signal_ratio_confirmed_by_worst_day",
        "hypothesis": "A=同上。B=20日最差单日收益（return_tail_shape；本线唯一S5命中partner，round_531 MB8与NOISE_VAR_CHG_20配对t=2.63 +43.3bp）。假设：噪声占比高(A高)且下行尾更极端(B更负)=延续；测试同一强partner对本族另一原子是否也有效。",
        "expected_sign": 1,
    },
    {
        "id": "MD5",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL,
        "right": _LBAR_OVERNIGHT,
        "mechanism": "noise_signal_ratio_confirmed_by_bigbar_overnight",
        "hypothesis": "A=同上。B=大bar隔夜分量（largebar_footprint_1m，S4阶段JUMP_BETA_STABILITY_20的唯一命中partner，t=2.47）。假设：噪声占比高(A高)且隔夜大bar分量高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MD6",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL,
        "right": _MAX5_MEAN20,
        "mechanism": "noise_signal_ratio_confirmed_by_max5_mean",
        "hypothesis": "A=同上。B=最大5日收益均值（upside_tail，S4阶段CONTINUOUS_BETA_60命中partner，t=2.00 +44.2bp）。假设：噪声占比高(A高)且近期有强正向单日(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MD7",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL,
        "right": _RET_ACF1_20,
        "mechanism": "noise_signal_ratio_confirmed_by_ret_acf1_20",
        "hypothesis": "A=同上。B=20日收益一阶自相关（serial_dependence，S4阶段CONTINUOUS_BETA_60命中partner，t=3.60）。假设：噪声占比高(A高)且自身收益呈现动量(B高)=噪声主导下定价缺乏效率但仍有可预测的惯性，延续。",
        "expected_sign": 1,
    },
    {
        "id": "MD8",
        "operator": "rank_spread",
        "left": _NOISE_SIGNAL,
        "right": _KYLE_LAMBDA,
        "mechanism": "noise_signal_ratio_confirmed_by_kyle_lambda",
        "hypothesis": "A=同上。B=Kyle价格冲击系数（microstructure_1m，S4阶段CONTINUOUS_BETA_60命中partner，t=2.60；与噪声/信号比同为微观结构主题，理论上高度相关但衡量维度不同——冲击成本vs噪声占比）。假设：噪声占比高(A高)且价格冲击系数高(B高)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
