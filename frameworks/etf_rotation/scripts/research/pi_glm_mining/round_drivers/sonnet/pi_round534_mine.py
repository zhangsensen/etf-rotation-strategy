#!/usr/bin/env python3
"""Round 534 driver: S5 stage step 4 -- microstructure_noise_1m pairing,
round 4 (final legal round for this family). This round opens the last
two unpaired atoms: NOISE_VAR_20 and ROLL_NOISE_PROXY_20 (both flagged
shadow in atom_health, 0.74/0.73 vs microstructure_1m:ROLL_SPREAD_20 --
but per the S4 precedent (JB2 was atom-health-shadow yet cleared the
official dedup gate, which only checks shelf16+prior-admitted), shadow
status alone does not preclude testing).

Unlike round_533's liquidity/co-jump/spillover/peer-value theme (which
uniformly failed against the "ratio/slope" atoms), this round returns to
activity/spread/impact-level themes -- more plausibly matched to these two
LEVEL (not trend/change) noise constructs, including a direct same-concept
cross-check (daily ROLL_SPREAD_20 from microstructure_1m vs this family's
intraday ROLL_NOISE_PROXY_20).

After this round, all 8 atoms will have used their one legal pairing
batch -- no legal candidates remain for this family regardless of this
round's outcome. Combined with round_532/533's two consecutive zero
rounds, a third zero here would trigger the contract's 3-consecutive-zero
exhaustion condition."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_534"

_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_LBAR_CLOCK = {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"}
_ROLL_SPREAD_DAILY = {"name": "ROLL_SPREAD_20", "source": "microstructure_1m"}
_OFI_AUTOCORR = {"name": "OFI_AUTOCORR_20", "source": "microstructure_1m"}
_RS_MINUS20 = {"name": "RS_MINUS_20", "source": "realized_measures_1m"}
_TICK_IMB = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}
_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_CLOSE5_CONSIST = {"name": "CLOSE5_DAY_CONSIST_20", "source": "bar_size_order_flow"}

_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_KYLE_LAMBDA = {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"}
_IMPACT_ASYM = {"name": "IMPACT_ASYM_20", "source": "microstructure_1m"}
_VPIN_CLOSE = {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"}
_GAP_VOL_RATIO = {"name": "GAP_VOL_RATIO_20", "source": "gap_volatility"}
_BPV_RV_RATIO = {"name": "BPV_RV_RATIO_20", "source": "realized_measures_1m"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}

_NOISE_VAR = {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"}
_ROLL_NOISE = {"name": "ROLL_NOISE_PROXY_20", "source": "microstructure_noise_1m"}

base.CANDIDATES = [
    # ---- NOISE_VAR_20 (shadow vs microstructure_1m:ROLL_SPREAD_20 at
    # atom-health, but official dedup only checks shelf16+prior-admitted;
    # activity/spread-level partner theme) ----
    {
        "id": "MH1",
        "operator": "rank_spread",
        "left": _NOISE_VAR,
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "noise_var_confirmed_by_bigbar_vol_share",
        "hypothesis": "A=噪声方差水平（Bandi-Russell 2008，体检审计-0.0437，atom-health shadow=True vs microstructure_1m:ROLL_SPREAD_20，但官方去重只比shelf16+此前入选，不预先排除）。B=大bar成交量占比（bar_size_order_flow，本族首次配对）。假设：噪声方差高(A高)且大bar贡献成交量占比高(B高)=噪声主要由大额冲击驱动而非纯粹报价噪声，延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "MH2",
        "operator": "rank_spread",
        "left": _NOISE_VAR,
        "right": _LBAR_CLOCK,
        "mechanism": "noise_var_confirmed_by_bigbar_clock_std",
        "hypothesis": "A=同上。B=大bar发生时点的20日标准差（largebar_footprint_1m，本族首次配对）。假设：噪声方差高(A高)且大bar发生时点分散(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MH3",
        "operator": "rank_spread",
        "left": _NOISE_VAR,
        "right": _ROLL_SPREAD_DAILY,
        "mechanism": "noise_var_confirmed_by_daily_roll_spread",
        "hypothesis": "A=同上。B=日频Roll隐含价差（microstructure_1m，本族首次配对；与A同源理论但不同频率——日频收盘价序列相关估计 vs 1m噪声方差分解，直接同概念交叉验证）。假设：1m噪声方差高(A高)且日频隐含价差也大(B高)=两个频率的噪声度量一致确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "MH4",
        "operator": "rank_spread",
        "left": _NOISE_VAR,
        "right": _OFI_AUTOCORR,
        "mechanism": "noise_var_confirmed_by_ofi_autocorr",
        "hypothesis": "A=同上。B=订单流不平衡自相关（microstructure_1m，本族首次配对）。假设：噪声方差高(A高)且订单流不平衡持续性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MH5",
        "operator": "rank_spread",
        "left": _NOISE_VAR,
        "right": _RS_MINUS20,
        "mechanism": "noise_var_confirmed_by_realized_semivariance_minus",
        "hypothesis": "A=同上。B=已实现负半方差占比（realized_measures_1m，S4阶段CONTINUOUS_BETA_60命中partner，t=2.34，本族首次配对）。假设：噪声方差高(A高)且下行半方差占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MH6",
        "operator": "rank_spread",
        "left": _NOISE_VAR,
        "right": _TICK_IMB,
        "mechanism": "noise_var_confirmed_by_tick_imbalance",
        "hypothesis": "A=同上。B=1m order flow不平衡（bar_size_order_flow，round_532曾与ROLL_NOISE_PROXY_CHG_20配对[MC4]未过，本次与本腿是全新组合）。假设：噪声方差高(A高)且订单流不平衡明显(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MH7",
        "operator": "rank_spread",
        "left": _NOISE_VAR,
        "right": _VOL_SPIKE,
        "mechanism": "noise_var_confirmed_by_volume_spike_freq",
        "hypothesis": "A=同上。B=成交量脉冲频率（intraday_volume_profile_1m，round_531/532与NOISE_VAR_CHG_20/ROLL_NOISE_PROXY_CHG_20配对均产生大额审计bp但t不足[+17.9~77.5bp, t 1.3~4.1]，本次是该partner第3次也是本阶段最后一次使用）。假设：噪声方差高(A高)且脉冲放量频繁(B高)=延续；测试该强partner对水平型(非变化型)噪声原子是否表现不同。",
        "expected_sign": 1,
    },
    {
        "id": "MH8",
        "operator": "rank_spread",
        "left": _NOISE_VAR,
        "right": _CLOSE5_CONSIST,
        "mechanism": "noise_var_confirmed_by_close5_day_consistency",
        "hypothesis": "A=同上。B=收盘前5分钟方向一致性（bar_size_order_flow，本族首次配对）。假设：噪声方差高(A高)且尾盘方向一致性低(B低，噪声主导缺乏方向性)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    # ---- ROLL_NOISE_PROXY_20 (shadow vs microstructure_1m:ROLL_SPREAD_20;
    # impact/liquidity-level partner theme) ----
    {
        "id": "MI1",
        "operator": "rank_spread",
        "left": _ROLL_NOISE,
        "right": _AMIHUD_1M,
        "mechanism": "roll_noise_confirmed_by_amihud_1m",
        "hypothesis": "A=日内Roll噪声代理水平（Roll 1984，1m版本，体检审计-0.0308，shadow=True vs microstructure_1m:ROLL_SPREAD_20，但官方去重不预先排除）。B=Amihud非流动性比率的1m版本（microstructure_1m，本族首次配对，与A理论上高度相关但衡量维度不同——价格冲击弹性vs收益自相关噪声）。假设：日内买卖价差噪声高(A高)且非流动性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MI2",
        "operator": "rank_spread",
        "left": _ROLL_NOISE,
        "right": _KYLE_LAMBDA,
        "mechanism": "roll_noise_confirmed_by_kyle_lambda",
        "hypothesis": "A=同上。B=Kyle价格冲击系数（microstructure_1m，S4阶段CONTINUOUS_BETA_60命中partner t=2.60，本族首次配对）。假设：日内价差噪声高(A高)且价格冲击系数高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MI3",
        "operator": "rank_spread",
        "left": _ROLL_NOISE,
        "right": _IMPACT_ASYM,
        "mechanism": "roll_noise_confirmed_by_impact_asymmetry",
        "hypothesis": "A=同上。B=价格冲击不对称性（microstructure_1m，本族首次配对）。假设：日内价差噪声高(A高)且冲击不对称明显(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MI4",
        "operator": "rank_spread",
        "left": _ROLL_NOISE,
        "right": _VPIN_CLOSE,
        "mechanism": "roll_noise_confirmed_by_vpin",
        "hypothesis": "A=同上。B=收盘时点VPIN（microstructure_1m，本族首次配对）。假设：日内价差噪声高(A高)且VPIN高(B高，知情交易占比高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MI5",
        "operator": "rank_spread",
        "left": _ROLL_NOISE,
        "right": _GAP_VOL_RATIO,
        "mechanism": "roll_noise_confirmed_by_gap_volatility_ratio",
        "hypothesis": "A=同上。B=跳空波动率比率（gap_volatility，本族首次配对）。假设：日内价差噪声高(A高)且跳空波动占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MI6",
        "operator": "rank_spread",
        "left": _ROLL_NOISE,
        "right": _BPV_RV_RATIO,
        "mechanism": "roll_noise_confirmed_by_bpv_rv_ratio",
        "hypothesis": "A=同上。B=双幂变差/已实现方差比（realized_measures_1m，Barndorff-Nielsen-Shephard 2004，与A同源跳跃检测文献但衡量自身收益连续性占比，本族首次配对）。假设：日内价差噪声高(A高)且自身收益连续分量占比低(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "MI7",
        "operator": "rank_spread",
        "left": _ROLL_NOISE,
        "right": _LOG_AMT,
        "mechanism": "roll_noise_confirmed_by_high_activity",
        "hypothesis": "A=同上。B=对数成交额（liquidity_variability，本线历史最强单腿之一，本次是该partner第3次也是本阶段最后一次使用）。假设：日内价差噪声高(A高)且整体活跃度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MI8",
        "operator": "rank_spread",
        "left": _ROLL_NOISE,
        "right": _OPEN30,
        "mechanism": "roll_noise_confirmed_by_open30_vol_share",
        "hypothesis": "A=同上。B=开盘30分钟成交占比（intraday_volume_profile_1m，本线历史最强confirming partner之一，本次是该partner第3次也是本阶段最后一次使用）。假设：日内价差噪声高(A高)且开盘集中放量(B高)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
