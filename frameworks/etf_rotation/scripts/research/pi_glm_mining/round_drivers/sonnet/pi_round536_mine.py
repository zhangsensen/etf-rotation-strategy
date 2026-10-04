#!/usr/bin/env python3
"""Round 536 driver: S10 stage step 1 -- accumulation_distribution_1m
family (Chaikin 1966/1982 CLV/A-D line; Granville 1963 OBV; Quong-Soudack
1989 MFI; Blume-Easley-O'Hara 1994), main controller's pre-specified S10
direction after S5's closure.

Atom health (round_536_atom_health, vs bar_size_order_flow since
price_volume_coupling/intraday_vwap_position families do not exist in
this line's catalog): OBV_SLOPE_20 (0.78 vs TICK_IMBALANCE_20) and
MFI_EXTREME_FRAC_20 (0.86 vs BIGBAR_VOL_SHARE_20) shadow. The other 6
atoms non-shadow. OBV_SLOPE_CHG_20 has the strongest non-shadow audit IC
(+0.047) and is chosen as this round's sole left leg for the first
pairing batch, per the pairing-discipline rule (one batch of <=8, right
legs all cross-family)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_536"

_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_WORST_DAY20 = {"name": "WORST_DAY_20", "source": "return_tail_shape"}

base.CANDIDATES = [
    # ---- 8 atomic: new accumulation_distribution_1m atoms ----
    {
        "id": "NA1",
        "operator": "atomic",
        "left": {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"},
        "right": {"name": "AD_NET_FLOW_20", "source": "accumulation_distribution_1m"},
        "mechanism": "ad_net_flow_20",
        "hypothesis": "Chaikin 1966/1982 CLV加权量流净额占比，20日均值。体检：disc-0.0559/579天/审计+0.0268，max|corr|=0.35（vs bar_size_order_flow:TICK_IMBALANCE_20），非shadow。假设：量流净额高(A高，成交集中在上涨收盘)=积累行为，rank与未来收益正相关（此处发现期为负，符号按discovery定）。",
        "expected_sign": -1,
    },
    {
        "id": "NA2",
        "operator": "atomic",
        "left": {"name": "AD_NET_FLOW_SLOPE_20", "source": "accumulation_distribution_1m"},
        "right": {"name": "AD_NET_FLOW_SLOPE_20", "source": "accumulation_distribution_1m"},
        "mechanism": "ad_net_flow_slope_20",
        "hypothesis": "量流净额占比的20日趋势斜率。体检：disc-0.0844/审计+0.0146，max|corr|=0.23，非shadow。假设：量流净额正在上升(A高)=积累行为增强，符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "NA3",
        "operator": "atomic",
        "left": {"name": "AD_NET_FLOW_CHG_20", "source": "accumulation_distribution_1m"},
        "right": {"name": "AD_NET_FLOW_CHG_20", "source": "accumulation_distribution_1m"},
        "mechanism": "ad_net_flow_change_20",
        "hypothesis": "量流净额占比的20日变化（regime切换）。体检：disc-0.0396/审计+0.0235，max|corr|=0.25，非shadow。假设：量流净额正在上升(A高)=延续，符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "NA4",
        "operator": "atomic",
        "left": {"name": "OBV_SLOPE_20", "source": "accumulation_distribution_1m"},
        "right": {"name": "OBV_SLOPE_20", "source": "accumulation_distribution_1m"},
        "mechanism": "obv_slope_20",
        "hypothesis": "Granville 1963 OBV日内斜率（按日成交量归一化），20日均值。体检：disc-0.0176/审计-0.0086，max|corr|=0.78（vs bar_size_order_flow:TICK_IMBALANCE_20），**shadow=True**（OBV斜率本质上是签名成交量的累积趋势，与tick不平衡高度重叠符合预期）。",
        "expected_sign": -1,
    },
    {
        "id": "NA5",
        "operator": "atomic",
        "left": {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"},
        "right": {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"},
        "mechanism": "obv_slope_change_20",
        "hypothesis": "OBV日内斜率的20日变化。体检：disc-0.0324/审计**+0.0474**（本族非shadow原子里审计IC绝对值最大），max|corr|=0.44，非shadow。假设：OBV斜率正在上升(A高，买盘压力增强)=延续，符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "NA6",
        "operator": "atomic",
        "left": {"name": "MFI_14_MEAN_20", "source": "accumulation_distribution_1m"},
        "right": {"name": "MFI_14_MEAN_20", "source": "accumulation_distribution_1m"},
        "mechanism": "mfi_14_mean_20",
        "hypothesis": "Quong-Soudack 1989 资金流量指标（14 bar），日均值的20日均值。体检：disc+0.0284/审计+0.0105，max|corr|=0.69，非shadow（接近阈值）。假设：MFI高(A高，资金流入占优)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NA7",
        "operator": "atomic",
        "left": {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"},
        "right": {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"},
        "mechanism": "mfi_extreme_frac_20",
        "hypothesis": "MFI超买超卖(>80或<20)频率，20日均值。体检：disc+0.0843/审计+0.0507，max|corr|=0.86（vs bar_size_order_flow:BIGBAR_VOL_SHARE_20），**shadow=True**（超买超卖频率与大bar成交占比同源，两者都是日内极端成交事件的代理）。",
        "expected_sign": 1,
    },
    {
        "id": "NA8",
        "operator": "atomic",
        "left": {"name": "AD_PRICE_CORR_20", "source": "accumulation_distribution_1m"},
        "right": {"name": "AD_PRICE_CORR_20", "source": "accumulation_distribution_1m"},
        "mechanism": "ad_price_corr_20",
        "hypothesis": "Blume-Easley-O'Hara 1994 量流与同期收益的20日相关性。体检：disc-0.0743/审计-0.0330（本族非shadow原子里发现期IC绝对值最大），max|corr|=0.34，非shadow。假设：量流与价格同步性低(A低，量价背离)=延续；符号按discovery定。",
        "expected_sign": -1,
    },
    # ---- first pairing batch: OBV_SLOPE_CHG_20 as sole left leg this
    # stage (strongest non-shadow atom-health audit IC), <=8 partners,
    # per the pairing-discipline rule ----
    {
        "id": "NB1",
        "operator": "rank_spread",
        "left": {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"},
        "right": _OPEN30,
        "mechanism": "obv_slope_chg_confirmed_by_open30_vol_share",
        "hypothesis": "A=OBV日内斜率20日变化（体检审计+0.0474，本族最强非shadow原子）。B=开盘30分钟成交占比（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：OBV斜率正在上升(A高)且开盘集中放量(B高)=买盘压力增强在开盘时段被确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "NB2",
        "operator": "rank_spread",
        "left": {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"},
        "right": _VOL_SPIKE,
        "mechanism": "obv_slope_chg_confirmed_by_volume_spike_freq",
        "hypothesis": "A=同上。B=成交量脉冲频率（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：OBV斜率上升(A高)且脉冲放量频繁(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NB3",
        "operator": "rank_spread",
        "left": {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"},
        "right": _CATEGORY_VOL,
        "mechanism": "obv_slope_chg_confirmed_by_category_vol",
        "hypothesis": "A=同上。B=同类别板块波动率（category_state，round_053门7全过史）。假设：OBV斜率上升(A高)且所属板块高波动(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NB4",
        "operator": "rank_spread",
        "left": {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"},
        "right": _GAP_FILL60,
        "mechanism": "obv_slope_chg_confirmed_by_gap_absorption",
        "hypothesis": "A=同上。B=60日窗缺口回补比例（gap_repair，round_053门7全过史）。假设：OBV斜率上升(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NB5",
        "operator": "rank_spread",
        "left": {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"},
        "right": _LOG_AMT,
        "mechanism": "obv_slope_chg_confirmed_by_high_activity",
        "hypothesis": "A=同上。B=对数成交额（liquidity_variability，本线历史最强单腿之一）。假设：OBV斜率上升(A高)且整体活跃度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NB6",
        "operator": "rank_spread",
        "left": {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"},
        "right": _BIGBAR_DIR_SKEW,
        "mechanism": "obv_slope_chg_confirmed_by_bigbar_dir_skew",
        "hypothesis": "A=同上。B=大bar方向偏斜（bar_size_order_flow，S4阶段CONTINUOUS_BETA_60最强confirming partner之一，t=3.48）。假设：OBV斜率上升(A高)且大bar方向持续偏向一侧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NB7",
        "operator": "rank_spread",
        "left": {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"},
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "obv_slope_chg_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=同伴OU回归半衰期（peer_relative_value，S4阶段本线最高命中率家族，t=3.75）。假设：OBV斜率上升(A高)且相对同伴回复速度慢(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NB8",
        "operator": "rank_spread",
        "left": {"name": "OBV_SLOPE_CHG_20", "source": "accumulation_distribution_1m"},
        "right": _WORST_DAY20,
        "mechanism": "obv_slope_chg_confirmed_by_worst_day",
        "hypothesis": "A=同上。B=20日最差单日收益（return_tail_shape，S5阶段MB8命中partner，t=2.63）。假设：OBV斜率上升(A高)且下行尾更极端(B更负)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
