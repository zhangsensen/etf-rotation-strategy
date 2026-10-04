#!/usr/bin/env python3
"""Round 549 driver: S8 stage step 1 -- realized_semicov_1m family
(Bollerslev-Li-Patton-Quaedvlieg 2020 realized semicovariance;
Ang-Chen-Xing 2006 downside/upside beta; Patton-Sheppard 2015), main
controller's pre-specified S8 direction after S7's closure.

Atom health (round_549_atom_health, vs downside_risk/market_sensitivity/
cojump_1m/jump_continuous_beta): SEMICOV_DOWNSIDE_BETA_20 (0.76 vs MARKET_BETA_60),
SEMICOV_UPSIDE_BETA_20 (0.76 vs CONTINUOUS_BETA_20), MIXED_NET_20 (0.74 vs
MARKET_BETA_60) all shadow -- expected, all three are beta-like
quantities correlating with plain market beta. The other 5 atoms
non-shadow. RCOV_P_SHARE_20 has the strongest non-shadow audit IC
(-0.073) and is chosen as this round's sole left leg for the first
pairing batch, per the pairing-discipline rule."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_549"

_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}

base.CANDIDATES = [
    # ---- 8 atomic: new realized_semicov_1m atoms ----
    {
        "id": "RA1",
        "operator": "atomic",
        "left": {"name": "RCOV_N_SHARE_20", "source": "realized_semicov_1m"},
        "right": {"name": "RCOV_N_SHARE_20", "source": "realized_semicov_1m"},
        "mechanism": "rcov_n_share_20",
        "hypothesis": "Bollerslev-Li-Patton-Quaedvlieg 2020 已实现半协方差，同跌(N)分量占总绝对协方差比例，与14只等权篮子代理，20日均值。体检：disc-0.0805/579天/审计-0.0647，max|corr|=0.66（vs market_sensitivity:MARKET_BETA_60），非shadow（接近阈值）。假设：同跌集中度高(A高)=下行风险共振强，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "RA2",
        "operator": "atomic",
        "left": {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"},
        "right": {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"},
        "mechanism": "rcov_p_share_20",
        "hypothesis": "同涨(P)分量占总绝对协方差比例，20日均值。体检：disc-0.0636/审计-0.0731（本族非shadow原子里审计IC绝对值最大），max|corr|=0.69，非shadow（接近阈值）。假设：同涨集中度高(A高)=上行动量共振强，rank与未来收益负相关（此处发现期为负，符号按discovery定）。",
        "expected_sign": -1,
    },
    {
        "id": "RA3",
        "operator": "atomic",
        "left": {"name": "SEMICOV_DOWNSIDE_BETA_20", "source": "realized_semicov_1m"},
        "right": {"name": "SEMICOV_DOWNSIDE_BETA_20", "source": "realized_semicov_1m"},
        "mechanism": "semicov_downside_beta_20",
        "hypothesis": "Ang-Chen-Xing 2006 下行beta，仅用篮子下跌时的协变化，20日均值。体检：disc-0.1032/审计-0.0491，max|corr|=0.76（vs market_sensitivity:MARKET_BETA_60），**shadow=True**（下行beta与普通市场beta本质相关，重叠符合预期）。",
        "expected_sign": -1,
    },
    {
        "id": "RA4",
        "operator": "atomic",
        "left": {"name": "SEMICOV_UPSIDE_BETA_20", "source": "realized_semicov_1m"},
        "right": {"name": "SEMICOV_UPSIDE_BETA_20", "source": "realized_semicov_1m"},
        "mechanism": "semicov_upside_beta_20",
        "hypothesis": "上行beta，仅用篮子上涨时的协变化，20日均值。体检：disc-0.0967/审计-0.0646，max|corr|=0.76（vs jump_continuous_beta:CONTINUOUS_BETA_20），**shadow=True**（上行beta与S4阶段常态beta构造高度相关，重叠符合预期）。",
        "expected_sign": -1,
    },
    {
        "id": "RA5",
        "operator": "atomic",
        "left": {"name": "BETA_ASYM_20", "source": "realized_semicov_1m"},
        "right": {"name": "BETA_ASYM_20", "source": "realized_semicov_1m"},
        "mechanism": "beta_asymmetry_20",
        "hypothesis": "下行beta减上行beta（崩盘beta缺口的半协方差版本），20日均值。体检：disc-0.0092/审计+0.0113，max|corr|=0.31（vs downside_risk:ULCER_20），非shadow。假设：下行beta显著高于上行beta(A高)=危机敏感性强，rank与未来收益负相关（此处发现期为负，符号按discovery定）。",
        "expected_sign": -1,
    },
    {
        "id": "RA6",
        "operator": "atomic",
        "left": {"name": "MIXED_NET_20", "source": "realized_semicov_1m"},
        "right": {"name": "MIXED_NET_20", "source": "realized_semicov_1m"},
        "mechanism": "mixed_net_20",
        "hypothesis": "混合分量（篮子涨我跌/篮子跌我涨）净值占总绝对协方差比例，20日均值。体检：disc-0.0726/审计-0.0709，max|corr|=0.74（vs market_sensitivity:MARKET_BETA_60），**shadow=True**（混合分量净值本质上是负相关beta的代理，与普通市场beta重叠符合预期）。",
        "expected_sign": -1,
    },
    {
        "id": "RA7",
        "operator": "atomic",
        "left": {"name": "RCOV_N_SHARE_CHG_20", "source": "realized_semicov_1m"},
        "right": {"name": "RCOV_N_SHARE_CHG_20", "source": "realized_semicov_1m"},
        "mechanism": "rcov_n_share_change_20",
        "hypothesis": "同跌分量占比的20日变化（regime切换）。体检：disc-0.0297/审计-0.0432，max|corr|=0.21，非shadow。假设：同跌集中度正在上升(A高)=下行风险共振增强，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "RA8",
        "operator": "atomic",
        "left": {"name": "BETA_ASYM_CHG_20", "source": "realized_semicov_1m"},
        "right": {"name": "BETA_ASYM_CHG_20", "source": "realized_semicov_1m"},
        "mechanism": "beta_asymmetry_change_20",
        "hypothesis": "崩盘beta缺口的20日变化。体检：disc-0.0364/审计+0.0096，max|corr|=0.19，非shadow。假设：崩盘beta缺口正在扩大(A高)=危机敏感性增强，符号按discovery定。",
        "expected_sign": -1,
    },
    # ---- first pairing batch: RCOV_P_SHARE_20 as sole left leg this
    # stage (strongest non-shadow atom-health audit IC), <=8 partners,
    # per the pairing-discipline rule ----
    {
        "id": "RB1",
        "operator": "rank_spread",
        "left": {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"},
        "right": _OPEN30,
        "mechanism": "rcov_p_share_confirmed_by_open30_vol_share",
        "hypothesis": "A=同涨分量占比（体检审计-0.0731，本族最强非shadow原子）。B=开盘30分钟成交占比（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：同涨集中度高(A高)且开盘集中放量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RB2",
        "operator": "rank_spread",
        "left": {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"},
        "right": _VOL_SPIKE,
        "mechanism": "rcov_p_share_confirmed_by_volume_spike_freq",
        "hypothesis": "A=同上。B=成交量脉冲频率（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：同涨集中度高(A高)且脉冲放量频繁(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RB3",
        "operator": "rank_spread",
        "left": {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"},
        "right": _CATEGORY_VOL,
        "mechanism": "rcov_p_share_confirmed_by_category_vol",
        "hypothesis": "A=同上。B=同类别板块波动率（category_state，round_053门7全过史）。假设：同涨集中度高(A高)且所属板块高波动(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RB4",
        "operator": "rank_spread",
        "left": {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"},
        "right": _GAP_FILL60,
        "mechanism": "rcov_p_share_confirmed_by_gap_absorption",
        "hypothesis": "A=同上。B=60日窗缺口回补比例（gap_repair，round_053门7全过史）。假设：同涨集中度高(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RB5",
        "operator": "rank_spread",
        "left": {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"},
        "right": _LOG_AMT,
        "mechanism": "rcov_p_share_confirmed_by_high_activity",
        "hypothesis": "A=同上。B=对数成交额（liquidity_variability，本线历史最强单腿之一）。假设：同涨集中度高(A高)且整体活跃度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RB6",
        "operator": "rank_spread",
        "left": {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"},
        "right": _BIGBAR_DIR_SKEW,
        "mechanism": "rcov_p_share_confirmed_by_bigbar_dir_skew",
        "hypothesis": "A=同上。B=大bar方向偏斜（bar_size_order_flow，S4阶段CONTINUOUS_BETA_60最强confirming partner之一，t=3.48）。假设：同涨集中度高(A高)且大bar方向持续偏向一侧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RB7",
        "operator": "rank_spread",
        "left": {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"},
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "rcov_p_share_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=同伴OU回归半衰期（peer_relative_value，S4阶段本线最高命中率家族，t=3.75）。假设：同涨集中度高(A高)且相对同伴回复速度慢(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "RB8",
        "operator": "rank_spread",
        "left": {"name": "RCOV_P_SHARE_20", "source": "realized_semicov_1m"},
        "right": _DEP_DRIFT,
        "mechanism": "rcov_p_share_confirmed_by_dependency_drift",
        "hypothesis": "A=同上。B=依赖结构20日漂移（cross_dependence_1m，S10阶段MFI_EXTREME_FRAC_20最强命中partner，t=4.88）。假设：同涨集中度高(A高)且依赖结构正在漂移(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
