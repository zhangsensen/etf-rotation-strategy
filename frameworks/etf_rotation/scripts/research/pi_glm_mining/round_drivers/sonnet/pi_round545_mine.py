#!/usr/bin/env python3
"""Round 545 driver: S7 stage step 1 -- intraday_drawdown_1m family
(Magdon-Ismail-Atiya 2004 max drawdown; Chekhlov-Uryasev-Zabarankin 2005
CDaR; Grossman-Zhou 1993 underwater-time), main controller's pre-specified
S7 direction after S6's closure.

Atom health (round_545_atom_health, vs drawdown_duration/intraday_extremes_
timing/intraday_return_path/downside_risk, all registered in this
catalog): INTRADAY_MAXDD_20, INTRADAY_MAXRUNUP_20, INTRADAY_CDAR_20 all
shadow (0.79-0.80 vs downside_risk) -- expected, these three all measure
the same underlying intraday extremity via slightly different
constructions. The other 5 atoms non-shadow. UNDERWATER_FRAC_20 has the
strongest non-shadow audit IC (-0.081) and is chosen as this round's sole
left leg for the first pairing batch, per the pairing-discipline rule."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_545"

_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}

base.CANDIDATES = [
    # ---- 8 atomic: new intraday_drawdown_1m atoms ----
    {
        "id": "QA1",
        "operator": "atomic",
        "left": {"name": "INTRADAY_MAXDD_20", "source": "intraday_drawdown_1m"},
        "right": {"name": "INTRADAY_MAXDD_20", "source": "intraday_drawdown_1m"},
        "mechanism": "intraday_maxdd_20",
        "hypothesis": "Magdon-Ismail-Atiya 2004 最大回撤，应用于1m日内价格路径，20日均值。体检：disc-0.1001/579天/审计-0.0739，max|corr|=0.80（vs downside_risk同哈希原子），**shadow=True**（日内最大回撤与日频下行风险度量本质相关，重叠符合预期）。",
        "expected_sign": -1,
    },
    {
        "id": "QA2",
        "operator": "atomic",
        "left": {"name": "INTRADAY_MAXRUNUP_20", "source": "intraday_drawdown_1m"},
        "right": {"name": "INTRADAY_MAXRUNUP_20", "source": "intraday_drawdown_1m"},
        "mechanism": "intraday_maxrunup_20",
        "hypothesis": "对称的日内最大反弹（谷到峰），20日均值。体检：disc-0.1031/审计-0.0652，max|corr|=0.79（vs downside_risk同哈希原子），**shadow=True**。",
        "expected_sign": -1,
    },
    {
        "id": "QA3",
        "operator": "atomic",
        "left": {"name": "DD_RUNUP_ASYM_20", "source": "intraday_drawdown_1m"},
        "right": {"name": "DD_RUNUP_ASYM_20", "source": "intraday_drawdown_1m"},
        "mechanism": "dd_runup_asymmetry_20",
        "hypothesis": "最大回撤减最大反弹（日内路径不对称性），20日均值。体检：disc+0.0029/审计+0.0018，max|corr|=0.31（vs drawdown_duration:UNDERWATER_FRACTION_20），非shadow。假设：回撤显著大于反弹(A高)=日内下行压力主导，rank与未来收益负相关（此处发现期为正，符号按discovery定）。",
        "expected_sign": 1,
    },
    {
        "id": "QA4",
        "operator": "atomic",
        "left": {"name": "UNDERWATER_FRAC_20", "source": "intraday_drawdown_1m"},
        "right": {"name": "UNDERWATER_FRAC_20", "source": "intraday_drawdown_1m"},
        "mechanism": "underwater_fraction_20",
        "hypothesis": "Grossman-Zhou 1993 水下时间框架，日内低于运行峰值的bar占比，20日均值。体检：disc-0.1018/审计-0.0809（本族非shadow原子里审计IC绝对值最大），max|corr|=0.56，非shadow。假设：水下时间占比高(A高)=日内多数时间承压，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "QA5",
        "operator": "atomic",
        "left": {"name": "INTRADAY_CDAR_20", "source": "intraday_drawdown_1m"},
        "right": {"name": "INTRADAY_CDAR_20", "source": "intraday_drawdown_1m"},
        "mechanism": "intraday_cdar_20",
        "hypothesis": "Chekhlov-Uryasev-Zabarankin 2005 条件回撤风险(CDaR)，最差20%bar的回撤均值，20日均值。体检：disc-0.1015/审计-0.0747，max|corr|=0.80（vs downside_risk同哈希原子），**shadow=True**。",
        "expected_sign": -1,
    },
    {
        "id": "QA6",
        "operator": "atomic",
        "left": {"name": "DD_TROUGH_TIMING_20", "source": "intraday_drawdown_1m"},
        "right": {"name": "DD_TROUGH_TIMING_20", "source": "intraday_drawdown_1m"},
        "mechanism": "dd_trough_timing_20",
        "hypothesis": "最大回撤谷底出现在全日的相对位置（0=开盘,1=收盘），20日均值。体检：disc-0.0503/审计-0.0244，max|corr|=0.26，非shadow。假设：回撤谷底靠后(A高，尾盘探底)=当日收盘承压延续到次日，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "QA7",
        "operator": "atomic",
        "left": {"name": "INTRADAY_MAXDD_CHG_20", "source": "intraday_drawdown_1m"},
        "right": {"name": "INTRADAY_MAXDD_CHG_20", "source": "intraday_drawdown_1m"},
        "mechanism": "intraday_maxdd_change_20",
        "hypothesis": "日内最大回撤的20日变化（regime切换）。体检：disc-0.0296/审计+0.0600，max|corr|=0.21，非shadow。假设：日内最大回撤正在扩大(A高)=延续，符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "QA8",
        "operator": "atomic",
        "left": {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"},
        "right": {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"},
        "mechanism": "underwater_fraction_change_20",
        "hypothesis": "水下时间占比的20日变化。体检：disc-0.0747/审计-0.0760（本族非shadow原子里发现期与审计期IC都较大），max|corr|=0.20，非shadow。假设：水下时间占比正在上升(A高)=承压时间延长，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    # ---- first pairing batch: UNDERWATER_FRAC_20 as sole left leg this
    # stage (strongest non-shadow atom-health audit IC), <=8 partners,
    # per the pairing-discipline rule ----
    {
        "id": "QB1",
        "operator": "rank_spread",
        "left": {"name": "UNDERWATER_FRAC_20", "source": "intraday_drawdown_1m"},
        "right": _OPEN30,
        "mechanism": "underwater_frac_confirmed_by_open30_vol_share",
        "hypothesis": "A=水下时间占比（体检审计-0.0809，本族最强非shadow原子）。B=开盘30分钟成交占比（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：水下时间占比高(A高)且开盘集中放量(B高)=承压状态在开盘时段被确认，延续。",
        "expected_sign": 1,
    },
    {
        "id": "QB2",
        "operator": "rank_spread",
        "left": {"name": "UNDERWATER_FRAC_20", "source": "intraday_drawdown_1m"},
        "right": _VOL_SPIKE,
        "mechanism": "underwater_frac_confirmed_by_volume_spike_freq",
        "hypothesis": "A=同上。B=成交量脉冲频率（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：水下时间占比高(A高)且脉冲放量频繁(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QB3",
        "operator": "rank_spread",
        "left": {"name": "UNDERWATER_FRAC_20", "source": "intraday_drawdown_1m"},
        "right": _CATEGORY_VOL,
        "mechanism": "underwater_frac_confirmed_by_category_vol",
        "hypothesis": "A=同上。B=同类别板块波动率（category_state，round_053门7全过史）。假设：水下时间占比高(A高)且所属板块高波动(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QB4",
        "operator": "rank_spread",
        "left": {"name": "UNDERWATER_FRAC_20", "source": "intraday_drawdown_1m"},
        "right": _GAP_FILL60,
        "mechanism": "underwater_frac_confirmed_by_gap_absorption",
        "hypothesis": "A=同上。B=60日窗缺口回补比例（gap_repair，round_053门7全过史）。假设：水下时间占比高(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QB5",
        "operator": "rank_spread",
        "left": {"name": "UNDERWATER_FRAC_20", "source": "intraday_drawdown_1m"},
        "right": _LOG_AMT,
        "mechanism": "underwater_frac_confirmed_by_high_activity",
        "hypothesis": "A=同上。B=对数成交额（liquidity_variability，本线历史最强单腿之一）。假设：水下时间占比高(A高)且整体活跃度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QB6",
        "operator": "rank_spread",
        "left": {"name": "UNDERWATER_FRAC_20", "source": "intraday_drawdown_1m"},
        "right": _BIGBAR_DIR_SKEW,
        "mechanism": "underwater_frac_confirmed_by_bigbar_dir_skew",
        "hypothesis": "A=同上。B=大bar方向偏斜（bar_size_order_flow，S4阶段CONTINUOUS_BETA_60最强confirming partner之一，t=3.48）。假设：水下时间占比高(A高)且大bar方向持续偏向一侧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QB7",
        "operator": "rank_spread",
        "left": {"name": "UNDERWATER_FRAC_20", "source": "intraday_drawdown_1m"},
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "underwater_frac_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=同伴OU回归半衰期（peer_relative_value，S4阶段本线最高命中率家族，t=3.75）。假设：水下时间占比高(A高)且相对同伴回复速度慢(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "QB8",
        "operator": "rank_spread",
        "left": {"name": "UNDERWATER_FRAC_20", "source": "intraday_drawdown_1m"},
        "right": _DEP_DRIFT,
        "mechanism": "underwater_frac_confirmed_by_dependency_drift",
        "hypothesis": "A=同上。B=依赖结构20日漂移（cross_dependence_1m，S10阶段MFI_EXTREME_FRAC_20最强命中partner，t=4.88）。假设：水下时间占比高(A高)且依赖结构正在漂移(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
