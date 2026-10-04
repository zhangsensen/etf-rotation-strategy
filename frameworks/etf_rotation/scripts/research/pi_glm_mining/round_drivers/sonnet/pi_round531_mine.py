#!/usr/bin/env python3
"""Round 531 driver: S5 stage step 1 -- microstructure_noise_1m family
(Bandi-Russell 2008 / Zhang-Mykland-Ait-Sahalia 2005 / Andersen-Bollerslev-
Diebold-Labys 2000 / Hansen-Lunde 2006), main controller's pre-specified
S5 direction after S4's closure under the new pairing-discipline rule.

Atom health (round_531_atom_health, vs microstructure_1m/realized_measures_1m):
NOISE_VAR_20 and ROLL_NOISE_PROXY_20 shadow (0.74/0.73 vs microstructure_1m:
ROLL_SPREAD_20 -- both are noise/spread constructs, overlap expected).
The other 6 atoms non-shadow. NOISE_VAR_CHG_20 has the strongest raw audit
IC among non-shadow atoms (-0.148) and is chosen as this round's single
left leg for the first pairing batch, per the new rule (one batch of <=8,
right legs all cross-family, no repeats within the batch)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_531"

_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_WORST_DAY20 = {"name": "WORST_DAY_20", "source": "return_tail_shape"}

base.CANDIDATES = [
    # ---- 8 atomic: new microstructure_noise_1m atoms ----
    {
        "id": "MA1",
        "operator": "atomic",
        "left": {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"},
        "right": {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"},
        "mechanism": "noise_variance_20",
        "hypothesis": "Bandi-Russell 2008 噪声方差估计，(RV_1m-RV_5m)/(2n)，20日均值。体检：disc-0.0480/579天/审计-0.0437，max|corr|=0.74（vs microstructure_1m:ROLL_SPREAD_20），**shadow=True**（噪声方差与日频隐含价差本质上都在度量微观结构噪声，重叠符合预期）。",
        "expected_sign": -1,
    },
    {
        "id": "MA2",
        "operator": "atomic",
        "left": {"name": "NOISE_SIGNAL_RATIO_20", "source": "microstructure_noise_1m"},
        "right": {"name": "NOISE_SIGNAL_RATIO_20", "source": "microstructure_noise_1m"},
        "mechanism": "noise_signal_ratio_20",
        "hypothesis": "Hansen-Lunde 2006 噪声/信号比框架，噪声方差/粗尺度(5m)已实现方差代理，20日均值。体检：disc+0.0454/审计+0.0346，max|corr|=0.37，非shadow。假设：噪声占比高(A高)=价格中信息含量被噪声稀释，rank与未来收益负相关（此处发现期为正，符号按discovery定）。",
        "expected_sign": 1,
    },
    {
        "id": "MA3",
        "operator": "atomic",
        "left": {"name": "SIG_PLOT_SLOPE_20", "source": "microstructure_noise_1m"},
        "right": {"name": "SIG_PLOT_SLOPE_20", "source": "microstructure_noise_1m"},
        "mechanism": "signature_plot_slope_20",
        "hypothesis": "Andersen-Bollerslev-Diebold-Labys 2000 已实现方差签名图，log(RV)对log(采样间隔)在{1m,5m,15m}上的OLS斜率，20日均值。体检：disc-0.0377/审计-0.0342，max|corr|=0.48，非shadow。假设：斜率越陡(绝对值越大，A更负)=高频噪声膨胀效应越强，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "MA4",
        "operator": "atomic",
        "left": {"name": "TSRV_RV1M_RATIO_20", "source": "microstructure_noise_1m"},
        "right": {"name": "TSRV_RV1M_RATIO_20", "source": "microstructure_noise_1m"},
        "mechanism": "tsrv_rv1m_ratio_20",
        "hypothesis": "Zhang-Mykland-Ait-Sahalia 2005 两尺度直觉，粗/细尺度已实现方差比（简化单粗尺度代理），20日均值。体检：disc-0.0504/审计-0.0301，max|corr|=0.59，非shadow。假设：比值低(A低，1m方差远高于5m，噪声吸收多)=定价噪声大，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "MA5",
        "operator": "atomic",
        "left": {"name": "ROLL_NOISE_PROXY_20", "source": "microstructure_noise_1m"},
        "right": {"name": "ROLL_NOISE_PROXY_20", "source": "microstructure_noise_1m"},
        "mechanism": "roll_noise_proxy_20",
        "hypothesis": "Roll 1984 买卖价差噪声代理，应用于全日1m收益序列的负一阶自协方差，20日均值（与本线microstructure_1m的日频ROLL_SPREAD_20不同数据频率的独立预注册原子）。体检：disc-0.0228/审计-0.0308，max|corr|=0.73（vs microstructure_1m:ROLL_SPREAD_20），**shadow=True**（日内版本与日频版本的Roll价差本质相关，重叠符合预期）。",
        "expected_sign": -1,
    },
    {
        "id": "MA6",
        "operator": "atomic",
        "left": {"name": "NOISE_VAR_CHG_20", "source": "microstructure_noise_1m"},
        "right": {"name": "NOISE_VAR_CHG_20", "source": "microstructure_noise_1m"},
        "mechanism": "noise_variance_change_20",
        "hypothesis": "噪声方差20日变化（噪声regime切换）。体检：disc-0.0164/审计**-0.1475**（非shadow原子里审计IC绝对值最大），max|corr|=0.15，非shadow。假设：噪声方差正在上升(A高)=微观结构质量恶化，定价效率下降，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "MA7",
        "operator": "atomic",
        "left": {"name": "NOISE_SIGNAL_RATIO_CHG_20", "source": "microstructure_noise_1m"},
        "right": {"name": "NOISE_SIGNAL_RATIO_CHG_20", "source": "microstructure_noise_1m"},
        "mechanism": "noise_signal_ratio_change_20",
        "hypothesis": "噪声/信号比20日变化。体检：disc-0.0224/审计+0.0069，max|corr|=0.17，非shadow。假设：噪声占比正在上升(A高)=延续，符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "MA8",
        "operator": "atomic",
        "left": {"name": "ROLL_NOISE_PROXY_CHG_20", "source": "microstructure_noise_1m"},
        "right": {"name": "ROLL_NOISE_PROXY_CHG_20", "source": "microstructure_noise_1m"},
        "mechanism": "roll_noise_proxy_change_20",
        "hypothesis": "日内Roll噪声代理20日变化。体检：disc-0.0153/审计-0.1147（非shadow原子里审计IC绝对值第二大），max|corr|=0.20，非shadow。假设：日内买卖价差噪声正在扩大(A高)=延续，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    # ---- first pairing batch: NOISE_VAR_CHG_20 as sole left leg this
    # stage (strongest non-shadow atom-health audit IC), <=8 partners,
    # all cross-family, per the new pairing-discipline rule ----
    {
        "id": "MB1",
        "operator": "rank_spread",
        "left": {"name": "NOISE_VAR_CHG_20", "source": "microstructure_noise_1m"},
        "right": _OPEN30,
        "mechanism": "noise_var_chg_confirmed_by_open30_vol_share",
        "hypothesis": "A=噪声方差20日变化（体检审计-0.1475，本族最强非shadow原子）。B=开盘30分钟成交占比（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：噪声方差正在上升(A高)且开盘集中放量(B高)=噪声上升在开盘时段被交易活动放大确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB2",
        "operator": "rank_spread",
        "left": {"name": "NOISE_VAR_CHG_20", "source": "microstructure_noise_1m"},
        "right": _VOL_SPIKE,
        "mechanism": "noise_var_chg_confirmed_by_volume_spike_freq",
        "hypothesis": "A=同上。B=成交量脉冲频率（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：噪声方差上升(A高)且脉冲放量频繁(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB3",
        "operator": "rank_spread",
        "left": {"name": "NOISE_VAR_CHG_20", "source": "microstructure_noise_1m"},
        "right": _CATEGORY_VOL,
        "mechanism": "noise_var_chg_confirmed_by_category_vol",
        "hypothesis": "A=同上。B=同类别板块波动率（category_state，round_053门7全过史）。假设：噪声方差上升(A高)且所属板块高波动(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB4",
        "operator": "rank_spread",
        "left": {"name": "NOISE_VAR_CHG_20", "source": "microstructure_noise_1m"},
        "right": _GAP_FILL60,
        "mechanism": "noise_var_chg_confirmed_by_gap_absorption",
        "hypothesis": "A=同上。B=60日窗缺口回补比例（gap_repair，round_053门7全过史）。假设：噪声方差上升(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB5",
        "operator": "rank_spread",
        "left": {"name": "NOISE_VAR_CHG_20", "source": "microstructure_noise_1m"},
        "right": _LOG_AMT,
        "mechanism": "noise_var_chg_confirmed_by_high_activity",
        "hypothesis": "A=同上。B=对数成交额（liquidity_variability，本线历史最强单腿之一）。假设：噪声方差上升(A高)且整体活跃度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB6",
        "operator": "rank_spread",
        "left": {"name": "NOISE_VAR_CHG_20", "source": "microstructure_noise_1m"},
        "right": _BIGBAR_DIR_SKEW,
        "mechanism": "noise_var_chg_confirmed_by_bigbar_dir_skew",
        "hypothesis": "A=同上。B=大bar方向偏斜（bar_size_order_flow，S4阶段CONTINUOUS_BETA_60的最强confirming partner，t=3.48）。假设：噪声方差上升(A高)且大bar方向持续偏向一侧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB7",
        "operator": "rank_spread",
        "left": {"name": "NOISE_VAR_CHG_20", "source": "microstructure_noise_1m"},
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "noise_var_chg_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=同伴OU回归半衰期（peer_relative_value，S4阶段本线最高命中率家族，t=3.75）。假设：噪声方差上升(A高)且相对同伴回复速度慢(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "MB8",
        "operator": "rank_spread",
        "left": {"name": "NOISE_VAR_CHG_20", "source": "microstructure_noise_1m"},
        "right": _WORST_DAY20,
        "mechanism": "noise_var_chg_confirmed_by_worst_day",
        "hypothesis": "A=同上。B=20日最差单日收益（return_tail_shape，已验证原子）。假设：噪声方差上升(A高)且下行尾更极端(B更负)=噪声上升伴随极端下行风险，延续；符号按discovery定。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
