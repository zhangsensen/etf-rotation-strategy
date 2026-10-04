#!/usr/bin/env python3
"""Round 567 driver: S13 stage step 3 -- frequency_domain_beta_1m
pairing, round 3 (covers the last 3 remaining left-leg atoms). Three
first-pairing batches for BETA_FREQ_SLOPE_20, COHERENCE_LF_HF_DIFF_20,
BETA_HF_CHG_20 -- the final 3 of the 8 frequency_domain_beta_1m atoms
not yet used as a left leg (round_565 covered
BETA_FREQ_SLOPE_CHG_20/BETA_LF_CHG_20, round_566 covered
BETA_HF_20/BETA_MF_20/BETA_LF_20). Both prior rounds admitted 0/48
combined -- this family has so far produced a purely
discovery-only-noise signature (several high-t candidates, none
surviving audit consistency, no tradable signal found).

After this round, all 8 frequency_domain_beta_1m atoms will have used
their one legal pairing batch -- no legal candidates remain for this
family regardless of outcome, so S13 will need formal closure next
round (which, if this round also yields 0, would be this line's first
zero-net-admission stage).

All 24 right-leg partners below are new to this family's S13 pairing
history (round_565/566's 40 partners are not repeated). No same-family
pairs, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_567"

_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_JUMP_BETA20 = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_LBAR_RUN_MAX = {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"}
_BPV_RV_RATIO = {"name": "BPV_RV_RATIO_20", "source": "realized_measures_1m"}
_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_PROFIT_RATIO60 = {"name": "PROFIT_RATIO_60", "source": "cost_distribution"}
_LIQ_COMMON_R2 = {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"}
_PARKINSON = {"name": "PARKINSON_RV_RATIO_20", "source": "range_based_vol_1m"}

_DOWNSIDE_BETA20 = {"name": "DOWNSIDE_BETA_20", "source": "market_sensitivity"}
_BETA_GAP20 = {"name": "BETA_GAP_20", "source": "jump_continuous_beta"}
_LBAR_PERM15 = {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"}
_JV_RV_SHARE = {"name": "JV_RV_SHARE_20", "source": "realized_measures_1m"}
_REL_MOM120 = {"name": "REL_MARKET_MOM_120", "source": "market_relative_strength"}
_OVERHAND_THICK = {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"}
_GK_CHG = {"name": "GK_RV_RATIO_CHG_20", "source": "range_based_vol_1m"}
_LZ = {"name": "LZ_COMPLEXITY_20", "source": "complexity_measures_1m"}

_UPSIDE_BETA20 = {"name": "UPSIDE_BETA_20", "source": "market_sensitivity"}
_JUMP_BETA_STAB = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}
_LBAR_OVERNIGHT = {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"}
_RSKEW20 = {"name": "RSKEW_20", "source": "realized_measures_1m"}
_STREAK_DAYS = {"name": "STREAK_DAYS", "source": "fund_flow"}
_GK_Z60 = {"name": "GK_RV_RATIO_Z_60", "source": "range_based_vol_1m"}
_MSPE5 = {"name": "MSPE_5M_20", "source": "complexity_measures_1m"}
_VPIN_CLOSE = {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"}

_FREQ_SLOPE = {"name": "BETA_FREQ_SLOPE_20", "source": "frequency_domain_beta_1m"}
_COH_DIFF = {"name": "COHERENCE_LF_HF_DIFF_20", "source": "frequency_domain_beta_1m"}
_BETA_HF_CHG = {"name": "BETA_HF_CHG_20", "source": "frequency_domain_beta_1m"}

base.CANDIDATES = [
    # ---- BETA_FREQ_SLOPE_20: first pairing batch ----
    {
        "id": "KA1",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE,
        "right": _MARKET_BETA20,
        "mechanism": "freq_slope_confirmed_by_market_beta_20",
        "hypothesis": "A=频率斜率(低频beta减高频beta,体检disc+0.0257,非shadow)。B=对篮子beta,20日(market_sensitivity,本族首次配对)。假设:长期beta相对高频beta更高(A高)且系统性beta本身也高(B高)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "KA2",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE,
        "right": _JUMP_BETA20,
        "mechanism": "freq_slope_confirmed_by_jump_beta_20",
        "hypothesis": "A=同上。B=对篮子跳跃beta,20日(jump_continuous_beta,本族首次配对)。假设:频率斜率高(A高)且跳跃beta低(B低,长期共振非跳跃驱动)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KA3",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE,
        "right": _LBAR_RUN_MAX,
        "mechanism": "freq_slope_confirmed_by_lbar_run_max_20",
        "hypothesis": "A=同上。B=大单连续出现的最长run(largebar_footprint_1m,本族首次配对)。假设:频率斜率高(A高)且大单连续性弱(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KA4",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE,
        "right": _BPV_RV_RATIO,
        "mechanism": "freq_slope_confirmed_by_bpv_rv_ratio_20",
        "hypothesis": "A=同上。B=双幂变差/已实现方差比(realized_measures_1m,本族首次配对)。假设:频率斜率高(A高)且连续分量占比高(B高,长期平滑共振)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KA5",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE,
        "right": _REL_MOM20,
        "mechanism": "freq_slope_confirmed_by_relative_market_momentum_20",
        "hypothesis": "A=同上。B=相对基准篮子动量,20日(market_relative_strength,本族首次配对)。假设:频率斜率高(A高)且相对动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KA6",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE,
        "right": _PROFIT_RATIO60,
        "mechanism": "freq_slope_confirmed_by_profit_ratio_60",
        "hypothesis": "A=同上。B=60日获利盘比例(cost_distribution,本族首次配对)。假设:频率斜率高(A高)且获利盘比例高(B高)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KA7",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE,
        "right": _LIQ_COMMON_R2,
        "mechanism": "freq_slope_confirmed_by_liq_common_r2_20",
        "hypothesis": "A=同上。B=流动性共性R²(liquidity_commonality_1m,本族首次配对)。假设:频率斜率高(A高)且流动性共性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KA8",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE,
        "right": _PARKINSON,
        "mechanism": "freq_slope_confirmed_by_parkinson_rv_ratio_20",
        "hypothesis": "A=同上。B=Parkinson区间估计/RV之比(range_based_vol_1m,S9阶段本族原子,本族首次配对)。假设:频率斜率高(A高)且bar内活动占比低(B低)=延续;本族最后一批。",
        "expected_sign": 1,
    },
    # ---- COHERENCE_LF_HF_DIFF_20: first pairing batch ----
    {
        "id": "KB1",
        "operator": "rank_spread",
        "left": _COH_DIFF,
        "right": _DOWNSIDE_BETA20,
        "mechanism": "coherence_diff_confirmed_by_downside_beta_20",
        "hypothesis": "A=低频相干性减高频相干性(体检disc+0.0102,非shadow)。B=下行beta,20日(market_sensitivity,本族首次配对)。假设:低频共动更强(A高)且下行beta高(B高)=延续,正相关(弱)。",
        "expected_sign": 1,
    },
    {
        "id": "KB2",
        "operator": "rank_spread",
        "left": _COH_DIFF,
        "right": _BETA_GAP20,
        "mechanism": "coherence_diff_confirmed_by_beta_gap_20",
        "hypothesis": "A=同上。B=跳跃beta与连续beta之差(jump_continuous_beta,本族首次配对)。假设:低频共动更强(A高)且beta缺口方向按discovery定(B)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KB3",
        "operator": "rank_spread",
        "left": _COH_DIFF,
        "right": _LBAR_PERM15,
        "mechanism": "coherence_diff_confirmed_by_lbar_perm15_20",
        "hypothesis": "A=同上。B=大单15分钟排列模式指标(largebar_footprint_1m,本族首次配对)。假设:低频共动更强(A高)且大单15m模式指标方向按discovery定(B)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KB4",
        "operator": "rank_spread",
        "left": _COH_DIFF,
        "right": _JV_RV_SHARE,
        "mechanism": "coherence_diff_confirmed_by_jump_variation_share_20",
        "hypothesis": "A=同上。B=跳跃变差占已实现方差比例(realized_measures_1m,本族首次配对)。假设:低频共动更强(A高)且跳跃占比低(B低)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KB5",
        "operator": "rank_spread",
        "left": _COH_DIFF,
        "right": _REL_MOM120,
        "mechanism": "coherence_diff_confirmed_by_relative_market_momentum_120",
        "hypothesis": "A=同上。B=相对基准篮子动量,120日(market_relative_strength,本族首次配对)。假设:低频共动更强(A高)且长期相对动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KB6",
        "operator": "rank_spread",
        "left": _COH_DIFF,
        "right": _OVERHAND_THICK,
        "mechanism": "coherence_diff_confirmed_by_overhand_thickness_60",
        "hypothesis": "A=同上。B=套牢盘厚度,60日(cost_distribution,本族首次配对)。假设:低频共动更强(A高)且套牢盘薄(B低)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KB7",
        "operator": "rank_spread",
        "left": _COH_DIFF,
        "right": _GK_CHG,
        "mechanism": "coherence_diff_confirmed_by_gk_rv_ratio_chg_20",
        "hypothesis": "A=同上。B=GK区间估计/RV之比的20日变化(range_based_vol_1m,本族首次配对)。假设:低频共动更强(A高)且区间比值下降(B低)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KB8",
        "operator": "rank_spread",
        "left": _COH_DIFF,
        "right": _LZ,
        "mechanism": "coherence_diff_confirmed_by_lz_complexity_20",
        "hypothesis": "A=同上。B=1m收益符号序列LZ复杂度(complexity_measures_1m,S11阶段本族原子,本族首次配对)。假设:低频共动更强(A高)且LZ复杂度低(B低,结构性更强)=延续;符号按discovery定;本族最后一批。",
        "expected_sign": 1,
    },
    # ---- BETA_HF_CHG_20: first pairing batch ----
    {
        "id": "KC1",
        "operator": "rank_spread",
        "left": _BETA_HF_CHG,
        "right": _UPSIDE_BETA20,
        "mechanism": "beta_hf_chg_confirmed_by_upside_beta_20",
        "hypothesis": "A=高频beta的20日变化(体检disc-0.0018,接近0,非shadow)。B=上行beta,20日(market_sensitivity,本族首次配对)。假设:高频beta正在上升(A高)且上行beta高(B高)=延续,负相关(弱)。",
        "expected_sign": -1,
    },
    {
        "id": "KC2",
        "operator": "rank_spread",
        "left": _BETA_HF_CHG,
        "right": _JUMP_BETA_STAB,
        "mechanism": "beta_hf_chg_confirmed_by_jump_beta_stability_20",
        "hypothesis": "A=同上。B=跳跃beta稳定性,20日(jump_continuous_beta,本族首次配对)。假设:高频beta上升(A高)且跳跃beta不稳定(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "KC3",
        "operator": "rank_spread",
        "left": _BETA_HF_CHG,
        "right": _LBAR_OVERNIGHT,
        "mechanism": "beta_hf_chg_confirmed_by_lbar_overnight_20",
        "hypothesis": "A=同上。B=大单隔夜出现比例(largebar_footprint_1m,本族首次配对)。假设:高频beta上升(A高)且大单隔夜比例低(B低,日内高频共振为主)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "KC4",
        "operator": "rank_spread",
        "left": _BETA_HF_CHG,
        "right": _RSKEW20,
        "mechanism": "beta_hf_chg_confirmed_by_rskew_20",
        "hypothesis": "A=同上。B=已实现偏度,20日(realized_measures_1m,本族首次配对)。假设:高频beta上升(A高)且偏度转负(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "KC5",
        "operator": "rank_spread",
        "left": _BETA_HF_CHG,
        "right": _STREAK_DAYS,
        "mechanism": "beta_hf_chg_confirmed_by_streak_days",
        "hypothesis": "A=同上。B=基金份额同向变化连续天数(fund_flow,本族首次配对)。假设:高频beta上升(A高)且份额变化连续性低(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "KC6",
        "operator": "rank_spread",
        "left": _BETA_HF_CHG,
        "right": _GK_Z60,
        "mechanism": "beta_hf_chg_confirmed_by_gk_rv_ratio_z_60",
        "hypothesis": "A=同上。B=gk_ratio原始日度序列60日z分数(range_based_vol_1m,本族首次配对)。假设:高频beta上升(A高)且区间比值异常偏高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "KC7",
        "operator": "rank_spread",
        "left": _BETA_HF_CHG,
        "right": _MSPE5,
        "mechanism": "beta_hf_chg_confirmed_by_mspe_5m_20",
        "hypothesis": "A=同上。B=5分钟尺度排列熵(complexity_measures_1m,S11阶段本族入选原子,本族首次配对)。假设:高频beta上升(A高)且5m尺度熵低(B低,结构性增强)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "KC8",
        "operator": "rank_spread",
        "left": _BETA_HF_CHG,
        "right": _VPIN_CLOSE,
        "mechanism": "beta_hf_chg_confirmed_by_vpin_close_20",
        "hypothesis": "A=同上。B=收盘时点VPIN(microstructure_1m,本族首次配对)。假设:高频beta上升(A高)且收盘前知情交易浓度升高(B高)=延续;本族最后一批,S13阶段所有8个原子的合法配对将全部用尽。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
