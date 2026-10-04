#!/usr/bin/env python3
"""Round 555 driver: S9 stage step 3 -- range_based_vol_1m pairing,
round 3 (covers the last 2 remaining left-leg atoms). Two first-pairing
batches for GK_RV_RATIO_CHG_20 and GK_RV_RATIO_Z_60 -- the final 2 of the
7 range_based_vol_1m atoms not yet used as a left leg (round_553 covered
YZ_OVERNIGHT_SHARE_20/GK_RV_RATIO_20, round_554 covered
PARKINSON_RV_RATIO_20/RS_RV_RATIO_20/WICK_SHARE_20).

After this round, all 7 range_based_vol_1m atoms will have used their one
legal pairing batch -- no legal candidates remain for this family
regardless of outcome, so S9 will need formal closure next round.

All 16 right-leg partners below are new to this family's S9 pairing
history (round_553/554's 40 partners are not repeated). No same-family
pairs, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_555"

_VOL_USHAPE20 = {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"}
_LM_JUMP_COUNT = {"name": "LM_JUMP_COUNT_20", "source": "realized_measures_1m"}
_DOWNSIDE_BETA60 = {"name": "DOWNSIDE_BETA_60", "source": "market_sensitivity"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_LBAR_RET_CONTRIB = {"name": "LBAR_RET_CONTRIB_20", "source": "largebar_footprint_1m"}
_JUMP_BETA20 = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_PRICE_AVGCOST = {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"}
_LIQ_COMMON_BETA = {"name": "LIQ_COMMON_BETA_20", "source": "liquidity_commonality_1m"}

_RSKEW20 = {"name": "RSKEW_20", "source": "realized_measures_1m"}
_RS_MINUS20 = {"name": "RS_MINUS_20", "source": "realized_measures_1m"}
_UPSIDE_BETA60 = {"name": "UPSIDE_BETA_60", "source": "market_sensitivity"}
_CLOSE30_VOL_SHARE = {"name": "CLOSE30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_LBAR_TREND = {"name": "LBAR_TREND_20_60", "source": "largebar_footprint_1m"}
_BETA_GAP20 = {"name": "BETA_GAP_20", "source": "jump_continuous_beta"}
_OVERHAND_THICK = {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"}
_LIQ_COMMON_R2 = {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"}

_GK_CHG = {"name": "GK_RV_RATIO_CHG_20", "source": "range_based_vol_1m"}
_GK_Z60 = {"name": "GK_RV_RATIO_Z_60", "source": "range_based_vol_1m"}

base.CANDIDATES = [
    # ---- GK_RV_RATIO_CHG_20: first pairing batch ----
    {
        "id": "GA1",
        "operator": "rank_spread",
        "left": _GK_CHG,
        "right": _VOL_USHAPE20,
        "mechanism": "gk_rv_ratio_chg_confirmed_by_vol_ushape_20",
        "hypothesis": "A=GK区间估计/RV之比的20日变化(体检disc-0.0428)。B=日内成交量U型强度(realized_measures_1m,round_053门7已admitted原子,本族首次配对)。假设:比值正在上升(A高)且U型强度高(B高)=区间信息重要性提升与开收盘活跃度提升同步,rank与未来收益负相关(符号按discovery定)。",
        "expected_sign": -1,
    },
    {
        "id": "GA2",
        "operator": "rank_spread",
        "left": _GK_CHG,
        "right": _LM_JUMP_COUNT,
        "mechanism": "gk_rv_ratio_chg_confirmed_by_lm_jump_count_20",
        "hypothesis": "A=同上。B=Lee-Mykland跳跃计数,20日(realized_measures_1m,本族首次配对)。假设:比值上升(A高)且跳跃频率低(B低,平滑bar内活动而非跳跃驱动)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GA3",
        "operator": "rank_spread",
        "left": _GK_CHG,
        "right": _DOWNSIDE_BETA60,
        "mechanism": "gk_rv_ratio_chg_confirmed_by_downside_beta_60",
        "hypothesis": "A=同上。B=下行beta,60日(market_sensitivity,本族首次配对)。假设:比值上升(A高)且下行beta低(B低,防御性)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "GA4",
        "operator": "rank_spread",
        "left": _GK_CHG,
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "gk_rv_ratio_chg_confirmed_by_bigbar_vol_share_20",
        "hypothesis": "A=同上。B=大单成交量占比(bar_size_order_flow,本线通道原子之一,本族首次配对)。假设:比值上升(A高)且大单占比低(B低,非大单驱动)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GA5",
        "operator": "rank_spread",
        "left": _GK_CHG,
        "right": _LBAR_RET_CONTRIB,
        "mechanism": "gk_rv_ratio_chg_confirmed_by_lbar_ret_contrib_20",
        "hypothesis": "A=同上。B=大单bar对当日收益的贡献占比(largebar_footprint_1m,本族首次配对)。假设:比值上升(A高)且大单贡献低(B低)=区间信息由普通bar累积而非个别大单,延续。",
        "expected_sign": -1,
    },
    {
        "id": "GA6",
        "operator": "rank_spread",
        "left": _GK_CHG,
        "right": _JUMP_BETA20,
        "mechanism": "gk_rv_ratio_chg_confirmed_by_jump_beta_20",
        "hypothesis": "A=同上。B=对14只等权篮子的跳跃beta,20日(jump_continuous_beta,本族首次配对)。假设:比值上升(A高)且跳跃beta低(B低)=区间信息与系统性跳跃无关,延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "GA7",
        "operator": "rank_spread",
        "left": _GK_CHG,
        "right": _PRICE_AVGCOST,
        "mechanism": "gk_rv_ratio_chg_confirmed_by_price_vs_avgcost_20",
        "hypothesis": "A=同上。B=现价相对平均成本偏离(cost_distribution,本族首次配对)。假设:比值上升(A高)且现价低于平均成本(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "GA8",
        "operator": "rank_spread",
        "left": _GK_CHG,
        "right": _LIQ_COMMON_BETA,
        "mechanism": "gk_rv_ratio_chg_confirmed_by_liq_common_beta_20",
        "hypothesis": "A=同上。B=流动性共性beta(liquidity_commonality_1m,本族首次配对)。假设:比值上升(A高)且流动性共性低(B低,特异性强)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- GK_RV_RATIO_Z_60: first pairing batch ----
    {
        "id": "GB1",
        "operator": "rank_spread",
        "left": _GK_Z60,
        "right": _RSKEW20,
        "mechanism": "gk_rv_ratio_z60_confirmed_by_rskew_20",
        "hypothesis": "A=gk_ratio原始日度序列的60日滚动z分数(体检disc-0.0207)。B=已实现偏度,20日(realized_measures_1m,本族首次配对)。假设:z值高(A高,比值异常偏高)且已实现偏度为负(B低)=延续,rank与未来收益负相关(符号按discovery定)。",
        "expected_sign": -1,
    },
    {
        "id": "GB2",
        "operator": "rank_spread",
        "left": _GK_Z60,
        "right": _RS_MINUS20,
        "mechanism": "gk_rv_ratio_z60_confirmed_by_rs_minus_20",
        "hypothesis": "A=同上。B=正负已实现方差之差(realized_measures_1m,本族首次配对)。假设:z值高(A高)且负方差占比更高(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GB3",
        "operator": "rank_spread",
        "left": _GK_Z60,
        "right": _UPSIDE_BETA60,
        "mechanism": "gk_rv_ratio_z60_confirmed_by_upside_beta_60",
        "hypothesis": "A=同上。B=上行beta,60日(market_sensitivity,本族首次配对)。假设:z值高(A高)且上行beta低(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "GB4",
        "operator": "rank_spread",
        "left": _GK_Z60,
        "right": _CLOSE30_VOL_SHARE,
        "mechanism": "gk_rv_ratio_z60_confirmed_by_close30_vol_share_20",
        "hypothesis": "A=同上。B=收盘30分钟成交量占比(intraday_volume_profile_1m,本族首次配对)。假设:z值高(A高)且尾盘放量集中(B高,尾盘冲击驱动异常)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GB5",
        "operator": "rank_spread",
        "left": _GK_Z60,
        "right": _LBAR_TREND,
        "mechanism": "gk_rv_ratio_z60_confirmed_by_lbar_trend_20_60",
        "hypothesis": "A=同上。B=大单20日相对60日的趋势比(largebar_footprint_1m,本族首次配对)。假设:z值高(A高)且大单趋势走弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "GB6",
        "operator": "rank_spread",
        "left": _GK_Z60,
        "right": _BETA_GAP20,
        "mechanism": "gk_rv_ratio_z60_confirmed_by_beta_gap_20",
        "hypothesis": "A=同上。B=跳跃beta与连续beta之差(jump_continuous_beta,本族首次配对)。假设:z值高(A高)且beta缺口方向按discovery定(B)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GB7",
        "operator": "rank_spread",
        "left": _GK_Z60,
        "right": _OVERHAND_THICK,
        "mechanism": "gk_rv_ratio_z60_confirmed_by_overhand_thickness_60",
        "hypothesis": "A=同上。B=套牢盘厚度,60日(cost_distribution,本族首次配对)。假设:z值高(A高)且套牢盘厚(B高,压制反弹)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "GB8",
        "operator": "rank_spread",
        "left": _GK_Z60,
        "right": _LIQ_COMMON_R2,
        "mechanism": "gk_rv_ratio_z60_confirmed_by_liq_common_r2_20",
        "hypothesis": "A=同上。B=流动性共性R²(liquidity_commonality_1m,本族首次配对)。假设:z值高(A高)且流动性共性低(B低,特异性强)=延续;本族最后一批,S9阶段所有7个原子的合法配对将全部用尽。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
