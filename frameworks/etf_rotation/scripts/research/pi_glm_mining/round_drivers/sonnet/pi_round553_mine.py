#!/usr/bin/env python3
"""Round 553 driver: S9 stage step 1 -- range_based_vol_1m family
(Parkinson 1980; Garman-Klass 1980; Rogers-Satchell 1991; Yang-Zhang 2000;
Alizadeh-Brandt-Diebold 2002), main controller's pre-specified S9 direction
after S8's closure (round_552).

Atom health (round_553_atom_health, vs realized_measures_1m/
intraday_volatility_structure/daily_candle): only YZ_OVERNIGHT_SHARE_20 is
shadow (0.872 vs gap_volatility:<hash>, an unregistered/legacy shelf key,
not one of the three directive reference families -- none of the three
directive references produced a shadow hit). The other 6 atoms clean
(max|corr| 0.16-0.60, all < 0.70).

This round: 7 atomic (all new atoms) + 2 first pairing batches for
YZ_OVERNIGHT_SHARE_20 (shadow, prioritized per this line's established
shadow-atom-rescue heuristic) and GK_RV_RATIO_20 (canonical/most literature-
efficient of the three range estimators, strongest non-shadow disc_ic
magnitude at -0.0275). = 23 candidates, within the 15-30 band.

Remaining 5 atoms (PARKINSON_RV_RATIO_20, RS_RV_RATIO_20,
GK_RV_RATIO_CHG_20, GK_RV_RATIO_Z_60, WICK_SHARE_20) still have their one
legal pairing batch available in later S9 rounds."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_553"

_BPV_RV_RATIO = {"name": "BPV_RV_RATIO_20", "source": "realized_measures_1m"}
_VPIN_CLOSE = {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_PEER_RESID_Z = {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"}
_CAT_MOM20 = {"name": "CATEGORY_MOM_20", "source": "category_state"}
_SHARE_CHG20 = {"name": "SHARE_CHG_20", "source": "fund_flow"}
_GAP_VOL_RATIO = {"name": "GAP_VOL_RATIO_20", "source": "gap_volatility"}
_RANGE_ACF1 = {"name": "RANGE_ACF1_20", "source": "range_memory"}

_JV_RV_SHARE = {"name": "JV_RV_SHARE_20", "source": "realized_measures_1m"}
_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_CAT_DISP20 = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_PREMIUM_Z20 = {"name": "PREMIUM_Z_20", "source": "nav_premium"}
_COJUMP_INDEX = {"name": "COJUMP_INDEX_SHARE_20", "source": "cojump_1m"}
_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}

_PARKINSON = {"name": "PARKINSON_RV_RATIO_20", "source": "range_based_vol_1m"}
_GK_RATIO = {"name": "GK_RV_RATIO_20", "source": "range_based_vol_1m"}
_RS_RATIO = {"name": "RS_RV_RATIO_20", "source": "range_based_vol_1m"}
_YZ_OVERNIGHT = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}
_GK_CHG = {"name": "GK_RV_RATIO_CHG_20", "source": "range_based_vol_1m"}
_GK_Z60 = {"name": "GK_RV_RATIO_Z_60", "source": "range_based_vol_1m"}
_WICK_SHARE = {"name": "WICK_SHARE_20", "source": "range_based_vol_1m"}

base.CANDIDATES = [
    # ---- 7 atomic: new range_based_vol_1m atoms ----
    {
        "id": "TA1",
        "operator": "atomic",
        "left": _PARKINSON,
        "right": _PARKINSON,
        "mechanism": "parkinson_rv_ratio_20",
        "hypothesis": "Parkinson(1980)高低区间方差估计(按1m bar求和)与已实现方差(RV)之比,20日均值。体检:disc-0.0232/579天/审计+0.0583,max|corr|=0.60(vs realized_measures_1m:BPV_RV_RATIO_20),非shadow。假设:比值高(A高)=bar内(高低区间)波动相对bar间(收盘对收盘)波动占主导,可能是趋势内高频反转噪声,rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "TA2",
        "operator": "atomic",
        "left": _GK_RATIO,
        "right": _GK_RATIO,
        "mechanism": "gk_rv_ratio_20",
        "hypothesis": "Garman-Klass(1980)估计(区间+开盘收盘项,按1m bar求和)与RV之比,20日均值,三个比值估计中最literature-efficient的一个。体检:disc-0.0275/审计+0.0632,max|corr|=0.60,非shadow。假设方向同Parkinson。",
        "expected_sign": -1,
    },
    {
        "id": "TA3",
        "operator": "atomic",
        "left": _RS_RATIO,
        "right": _RS_RATIO,
        "mechanism": "rs_rv_ratio_20",
        "hypothesis": "Rogers-Satchell(1991)漂移无关估计(按1m bar求和)与RV之比,20日均值,三者中唯一不假设零漂移。体检:disc+0.0035(接近0)/审计+0.0675,max|corr|=0.52,非shadow。假设:比值高(A高)=漂移调整后bar内活动仍占主导,rank与未来收益正相关(弱,符号按discovery定)。",
        "expected_sign": 1,
    },
    {
        "id": "TA4",
        "operator": "atomic",
        "left": _YZ_OVERNIGHT,
        "right": _YZ_OVERNIGHT,
        "mechanism": "yz_overnight_share_20",
        "hypothesis": "Yang-Zhang(2000)完整分解(隔夜+开盘session+Rogers-Satchell,按日OHLC滚动20日窗口)中隔夜分量占总方差比例。体检:disc+0.0605/审计+0.0621,max|corr|=0.87(vs gap_volatility族一个未在三个指定参照家族里的历史shelf key),标记shadow。假设:隔夜方差占比高(A高)=跳空/隔夜消息驱动为主导机制,rank与未来收益正相关。",
        "expected_sign": 1,
    },
    {
        "id": "TA5",
        "operator": "atomic",
        "left": _GK_CHG,
        "right": _GK_CHG,
        "mechanism": "gk_rv_ratio_chg_20",
        "hypothesis": "GK_RV_RATIO_20的20日变化(比值趋势)。体检:disc-0.0428/审计+0.0719,max|corr|=0.20(vs daily_candle:GAP_MEAN_60),非shadow。假设:比值正在上升(A高)=bar内活动相对bar间活动的重要性正在提升,rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "TA6",
        "operator": "atomic",
        "left": _GK_Z60,
        "right": _GK_Z60,
        "mechanism": "gk_rv_ratio_z_60",
        "hypothesis": "gk_ratio原始日度序列的60日滚动z分数(与SHARE_Z_60同规范)。体检:disc-0.0207/审计+0.0362,max|corr|=0.16,非shadow。假设方向同CHG变体:z值高(A高)=当前比值相对近期异常偏高,rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "TA7",
        "operator": "atomic",
        "left": _WICK_SHARE,
        "right": _WICK_SHARE,
        "mechanism": "wick_share_20",
        "hypothesis": "全天聚合O/H/L/C的上下影线合计占区间比例,20日均值(Alizadeh-Brandt-Diebold 2002区间效率框架应用于bar内反转强度)。体检:disc+0.0137/审计+0.0281,max|corr|=0.25(vs gap_volatility族历史shelf key),非shadow。假设:影线占比高(A高)=日内反转/试探性强,rank与未来收益正相关(弱,符号按discovery定)。",
        "expected_sign": 1,
    },
    # ---- YZ_OVERNIGHT_SHARE_20: first pairing batch (shadow, prioritized) ----
    {
        "id": "TB1",
        "operator": "rank_spread",
        "left": _YZ_OVERNIGHT,
        "right": _BPV_RV_RATIO,
        "mechanism": "yz_overnight_share_confirmed_by_bpv_rv_ratio",
        "hypothesis": "A=隔夜方差占比(体检disc+0.0605,shadow vs 非指定参照)。B=双幂变差/已实现方差比(realized_measures_1m,本族首次配对)。假设:隔夜驱动为主(A高)且自身连续分量占比低(B低)=跳空延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "TB2",
        "operator": "rank_spread",
        "left": _YZ_OVERNIGHT,
        "right": _VPIN_CLOSE,
        "mechanism": "yz_overnight_share_confirmed_by_vpin_close",
        "hypothesis": "A=同上。B=收盘时点VPIN(microstructure_1m,本族首次配对)。假设:隔夜驱动为主(A高)且收盘前知情交易浓度高(B高)=隔夜信息有更强价格压力,延续。",
        "expected_sign": 1,
    },
    {
        "id": "TB3",
        "operator": "rank_spread",
        "left": _YZ_OVERNIGHT,
        "right": _GRANGER_IN,
        "mechanism": "yz_overnight_share_confirmed_by_granger_in_degree",
        "hypothesis": "A=同上。B=格兰杰因果入度(cross_dependence_1m,本族首次配对)。假设:隔夜驱动为主(A高)且被同伴领先影响强(B高)=隔夜消息经同伴扩散,延续。",
        "expected_sign": 1,
    },
    {
        "id": "TB4",
        "operator": "rank_spread",
        "left": _YZ_OVERNIGHT,
        "right": _PEER_RESID_Z,
        "mechanism": "yz_overnight_share_confirmed_by_peer_resid_z",
        "hypothesis": "A=同上。B=相对同伴协整残差z值(peer_relative_value,本族首次配对)。假设:隔夜驱动为主(A高)且相对同伴正向偏离(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "TB5",
        "operator": "rank_spread",
        "left": _YZ_OVERNIGHT,
        "right": _CAT_MOM20,
        "mechanism": "yz_overnight_share_confirmed_by_category_momentum_20",
        "hypothesis": "A=同上。B=板块20日动量(category_state,本族首次配对)。假设:隔夜驱动为主(A高)且所属板块动量强(B高)=隔夜消息与板块共振,延续。",
        "expected_sign": 1,
    },
    {
        "id": "TB6",
        "operator": "rank_spread",
        "left": _YZ_OVERNIGHT,
        "right": _SHARE_CHG20,
        "mechanism": "yz_overnight_share_confirmed_by_share_change_20",
        "hypothesis": "A=同上。B=基金份额20日变化(fund_flow,本族首次配对)。假设:隔夜驱动为主(A高)且份额同步扩张(B高)=资金端确认隔夜信号,延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "TB7",
        "operator": "rank_spread",
        "left": _YZ_OVERNIGHT,
        "right": _GAP_VOL_RATIO,
        "mechanism": "yz_overnight_share_confirmed_by_gap_volatility_ratio",
        "hypothesis": "A=同上。B=跳空波动率比率(gap_volatility族,本族首次配对;概念上与A呼应但衡量口径不同——B是跳空后已实现波动占比,A是YZ框架下隔夜方差占比)。假设:隔夜驱动为主(A高)且跳空后波动占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "TB8",
        "operator": "rank_spread",
        "left": _YZ_OVERNIGHT,
        "right": _RANGE_ACF1,
        "mechanism": "yz_overnight_share_confirmed_by_range_acf1",
        "hypothesis": "A=同上。B=日内振幅一阶自相关(range_memory,S7阶段QH4命中partner,t=2.13,本族首次配对)。假设:隔夜驱动为主(A高)且振幅具持续性(B高)=延续;本族最后一批。",
        "expected_sign": 1,
    },
    # ---- GK_RV_RATIO_20: first pairing batch ----
    {
        "id": "TC1",
        "operator": "rank_spread",
        "left": _GK_RATIO,
        "right": _JV_RV_SHARE,
        "mechanism": "gk_rv_ratio_confirmed_by_jump_variation_share",
        "hypothesis": "A=GK区间估计/RV之比(体检disc-0.0275)。B=跳跃变差占已实现方差比例(realized_measures_1m,本族首次配对)。假设:bar内活动占主导(A高)且自身跳跃占比低(B低)=平滑趋势延续,rank与未来收益负相关(符号按discovery定,方向与A一致)。",
        "expected_sign": -1,
    },
    {
        "id": "TC2",
        "operator": "rank_spread",
        "left": _GK_RATIO,
        "right": _AMIHUD_1M,
        "mechanism": "gk_rv_ratio_confirmed_by_amihud_1m",
        "hypothesis": "A=同上。B=Amihud非流动性比率的1m版本(microstructure_1m,本族首次配对)。假设:bar内活动占主导(A高)且非流动性高(B高)=区间信息更多来自流动性冲击而非信息驱动,延续。",
        "expected_sign": -1,
    },
    {
        "id": "TC3",
        "operator": "rank_spread",
        "left": _GK_RATIO,
        "right": _DEP_DRIFT,
        "mechanism": "gk_rv_ratio_confirmed_by_dep_drift_20",
        "hypothesis": "A=同上。B=依赖漂移指标(cross_dependence_1m,本族首次配对)。假设:bar内活动占主导(A高)且依赖漂移方向一致(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "TC4",
        "operator": "rank_spread",
        "left": _GK_RATIO,
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "gk_rv_ratio_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=相对同伴OU回归半衰期(peer_relative_value,本族首次配对)。假设:bar内活动占主导(A高)且相对同伴均值回归慢(B高,半衰期长)=趋势延续性更强,延续。",
        "expected_sign": -1,
    },
    {
        "id": "TC5",
        "operator": "rank_spread",
        "left": _GK_RATIO,
        "right": _CAT_DISP20,
        "mechanism": "gk_rv_ratio_confirmed_by_category_dispersion_20",
        "hypothesis": "A=同上。B=板块内部20日收益离散度(category_state,本族首次配对)。假设:bar内活动占主导(A高)且板块内部分化大(B高)=个股层面区间信息更具信息量而非板块共振,延续。",
        "expected_sign": -1,
    },
    {
        "id": "TC6",
        "operator": "rank_spread",
        "left": _GK_RATIO,
        "right": _PREMIUM_Z20,
        "mechanism": "gk_rv_ratio_confirmed_by_premium_z_20",
        "hypothesis": "A=同上。B=净值溢价20日z值(nav_premium,本族首次配对)。假设:bar内活动占主导(A高)且溢价异常(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "TC7",
        "operator": "rank_spread",
        "left": _GK_RATIO,
        "right": _COJUMP_INDEX,
        "mechanism": "gk_rv_ratio_confirmed_by_cojump_index_share",
        "hypothesis": "A=同上。B=共跳占指数跳跃比例(cojump_1m,本族首次配对)。假设:bar内活动占主导(A高)且与指数共跳比例低(B低)=区间信息更多是个股特异噪声而非系统性跳跃,延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "TC8",
        "operator": "rank_spread",
        "left": _GK_RATIO,
        "right": _BIGBAR_DIR_SKEW,
        "mechanism": "gk_rv_ratio_confirmed_by_bigbar_dir_skew_20",
        "hypothesis": "A=同上。B=大单方向偏度(bar_size_order_flow,本线通道原子之一,本族首次配对)。假设:bar内活动占主导(A高)且大单方向偏度明显(B按discovery定)=区间波动主要来自大单驱动的方向性冲击而非噪声,延续;本族最后一批。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
