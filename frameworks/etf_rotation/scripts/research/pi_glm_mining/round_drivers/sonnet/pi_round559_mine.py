#!/usr/bin/env python3
"""Round 559 driver: S11 stage step 3 -- complexity_measures_1m pairing,
round 3 (covers the last 3 remaining left-leg atoms). Three first-pairing
batches for APEN_RET_20, MSPE_SCALE_DIFF_20, SAMPEN_RET_CHG_20 -- the
final 3 of the 8 complexity_measures_1m atoms not yet used as a left leg
(round_557 covered MSPE_5M_20/MSPE_15M_20 [atomic+pairing], round_558
covered SAMPEN_RET_20/LZ_COMPLEXITY_20/RECURRENCE_RATE_20).

After this round, all 8 complexity_measures_1m atoms will have used their
one legal pairing batch -- no legal candidates remain for this family
regardless of outcome, so S11 will need formal closure next round.

All 24 right-leg partners below are new to this family's S11 pairing
history (round_557/558's 40 partners are not repeated). No same-family
pairs, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_559"

_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_JUMP_BETA20 = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_LBAR_RUN_MAX = {"name": "LBAR_RUN_MAX_20", "source": "largebar_footprint_1m"}
_BPV_RV_RATIO = {"name": "BPV_RV_RATIO_20", "source": "realized_measures_1m"}
_REL_MOM60 = {"name": "REL_MARKET_MOM_60", "source": "market_relative_strength"}
_PRICE_AVGCOST = {"name": "PRICE_VS_AVGCOST_20", "source": "cost_distribution"}
_LIQ_COMMON_R2 = {"name": "LIQ_COMMON_R2_20", "source": "liquidity_commonality_1m"}
_PARKINSON = {"name": "PARKINSON_RV_RATIO_20", "source": "range_based_vol_1m"}

_DOWNSIDE_BETA20 = {"name": "DOWNSIDE_BETA_20", "source": "market_sensitivity"}
_BETA_GAP20 = {"name": "BETA_GAP_20", "source": "jump_continuous_beta"}
_LBAR_PERM15 = {"name": "LBAR_PERM15_20", "source": "largebar_footprint_1m"}
_JV_RV_SHARE = {"name": "JV_RV_SHARE_20", "source": "realized_measures_1m"}
_REL_MOM120 = {"name": "REL_MARKET_MOM_120", "source": "market_relative_strength"}
_SHARE_Z60 = {"name": "SHARE_Z_60", "source": "fund_flow"}
_GK_RATIO = {"name": "GK_RV_RATIO_20", "source": "range_based_vol_1m"}
_YZ_OVERNIGHT = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}

_BENCH_RESID_VOL20 = {"name": "BENCHMARK_RESIDUAL_VOL_20", "source": "market_sensitivity"}
_JUMP_BETA_STAB = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}
_LBAR_OVERNIGHT = {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"}
_RSKEW20 = {"name": "RSKEW_20", "source": "realized_measures_1m"}
_STREAK_DAYS = {"name": "STREAK_DAYS", "source": "fund_flow"}
_WICK_SHARE = {"name": "WICK_SHARE_20", "source": "range_based_vol_1m"}
_GK_CHG = {"name": "GK_RV_RATIO_CHG_20", "source": "range_based_vol_1m"}
_LM_JUMP_COUNT = {"name": "LM_JUMP_COUNT_20", "source": "realized_measures_1m"}

_APEN = {"name": "APEN_RET_20", "source": "complexity_measures_1m"}
_MSPE_DIFF = {"name": "MSPE_SCALE_DIFF_20", "source": "complexity_measures_1m"}
_SAMPEN_CHG = {"name": "SAMPEN_RET_CHG_20", "source": "complexity_measures_1m"}

base.CANDIDATES = [
    # ---- APEN_RET_20: first pairing batch ----
    {
        "id": "EA1",
        "operator": "rank_spread",
        "left": _APEN,
        "right": _MARKET_BETA20,
        "mechanism": "apen_ret_confirmed_by_market_beta_20",
        "hypothesis": "A=近似熵(体检disc-0.0988,atomic因vs PERM_ENTROPY_RET_20冗余被拒[0.86],但0.86是本族8原子里相关最低的shadow,更有机会被partner去相关)。B=对篮子beta,20日(market_sensitivity,本族首次配对)。假设:近似熵高(A高,更随机)且系统性beta低(B低,特异性噪声)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "EA2",
        "operator": "rank_spread",
        "left": _APEN,
        "right": _JUMP_BETA20,
        "mechanism": "apen_ret_confirmed_by_jump_beta_20",
        "hypothesis": "A=同上。B=对篮子跳跃beta,20日(jump_continuous_beta,本族首次配对)。假设:近似熵高(A高)且跳跃beta低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "EA3",
        "operator": "rank_spread",
        "left": _APEN,
        "right": _LBAR_RUN_MAX,
        "mechanism": "apen_ret_confirmed_by_lbar_run_max_20",
        "hypothesis": "A=同上。B=大单连续出现的最长run(largebar_footprint_1m,本族首次配对)。假设:近似熵高(A高)且大单连续性弱(B低,无规律)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "EA4",
        "operator": "rank_spread",
        "left": _APEN,
        "right": _BPV_RV_RATIO,
        "mechanism": "apen_ret_confirmed_by_bpv_rv_ratio_20",
        "hypothesis": "A=同上。B=双幂变差/已实现方差比(realized_measures_1m,本族首次配对)。假设:近似熵高(A高)且连续分量占比低(B低,跳跃驱动)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "EA5",
        "operator": "rank_spread",
        "left": _APEN,
        "right": _REL_MOM60,
        "mechanism": "apen_ret_confirmed_by_relative_market_momentum_60",
        "hypothesis": "A=同上。B=相对基准篮子动量,60日(market_relative_strength,本族首次配对)。假设:近似熵高(A高)且相对动量弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "EA6",
        "operator": "rank_spread",
        "left": _APEN,
        "right": _PRICE_AVGCOST,
        "mechanism": "apen_ret_confirmed_by_price_vs_avgcost_20",
        "hypothesis": "A=同上。B=现价相对平均成本偏离(cost_distribution,本族首次配对)。假设:近似熵高(A高)且现价低于成本(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "EA7",
        "operator": "rank_spread",
        "left": _APEN,
        "right": _LIQ_COMMON_R2,
        "mechanism": "apen_ret_confirmed_by_liq_common_r2_20",
        "hypothesis": "A=同上。B=流动性共性R²(liquidity_commonality_1m,本族首次配对)。假设:近似熵高(A高)且流动性共性低(B低,特异性强)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "EA8",
        "operator": "rank_spread",
        "left": _APEN,
        "right": _PARKINSON,
        "mechanism": "apen_ret_confirmed_by_parkinson_rv_ratio_20",
        "hypothesis": "A=同上。B=Parkinson区间估计/RV之比(range_based_vol_1m,S9阶段本族原子,本族首次配对)。假设:近似熵高(A高)且bar内活动占比低(B低)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- MSPE_SCALE_DIFF_20: first pairing batch ----
    {
        "id": "EB1",
        "operator": "rank_spread",
        "left": _MSPE_DIFF,
        "right": _DOWNSIDE_BETA20,
        "mechanism": "mspe_scale_diff_confirmed_by_downside_beta_20",
        "hypothesis": "A=15m排列熵减1m排列熵(体检disc+0.0787,atomic因vs CEP_DISTANCE_20冗余被拒[0.89])。B=下行beta,20日(market_sensitivity,本族首次配对)。假设:粗粒度化后熵反升(A高,反常结构)且下行beta高(B高)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "EB2",
        "operator": "rank_spread",
        "left": _MSPE_DIFF,
        "right": _BETA_GAP20,
        "mechanism": "mspe_scale_diff_confirmed_by_beta_gap_20",
        "hypothesis": "A=同上。B=跳跃beta与连续beta之差(jump_continuous_beta,本族首次配对)。假设:跨尺度熵反常上升(A高)且beta缺口方向按discovery定(B)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "EB3",
        "operator": "rank_spread",
        "left": _MSPE_DIFF,
        "right": _LBAR_PERM15,
        "mechanism": "mspe_scale_diff_confirmed_by_lbar_perm15_20",
        "hypothesis": "A=同上。B=大单15分钟排列模式指标(largebar_footprint_1m,本族首次配对,概念上与A的多尺度框架呼应)。假设:跨尺度熵反常上升(A高)且大单15m模式指标方向按discovery定(B)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "EB4",
        "operator": "rank_spread",
        "left": _MSPE_DIFF,
        "right": _JV_RV_SHARE,
        "mechanism": "mspe_scale_diff_confirmed_by_jump_variation_share_20",
        "hypothesis": "A=同上。B=跳跃变差占已实现方差比例(realized_measures_1m,本族首次配对)。假设:跨尺度熵反常上升(A高)且跳跃占比高(B高,粗粒度化吸收跳跃信息)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "EB5",
        "operator": "rank_spread",
        "left": _MSPE_DIFF,
        "right": _REL_MOM120,
        "mechanism": "mspe_scale_diff_confirmed_by_relative_market_momentum_120",
        "hypothesis": "A=同上。B=相对基准篮子动量,120日(market_relative_strength,本族首次配对)。假设:跨尺度熵反常上升(A高)且长期相对动量强(B高)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "EB6",
        "operator": "rank_spread",
        "left": _MSPE_DIFF,
        "right": _SHARE_Z60,
        "mechanism": "mspe_scale_diff_confirmed_by_share_z_60",
        "hypothesis": "A=同上。B=基金份额60日z值(fund_flow,本族首次配对)。假设:跨尺度熵反常上升(A高)且份额异常扩张(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "EB7",
        "operator": "rank_spread",
        "left": _MSPE_DIFF,
        "right": _GK_RATIO,
        "mechanism": "mspe_scale_diff_confirmed_by_gk_rv_ratio_20",
        "hypothesis": "A=同上。B=Garman-Klass区间估计/RV之比(range_based_vol_1m,S9阶段本族原子,本族首次配对)。假设:跨尺度熵反常上升(A高)且bar内活动占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "EB8",
        "operator": "rank_spread",
        "left": _MSPE_DIFF,
        "right": _YZ_OVERNIGHT,
        "mechanism": "mspe_scale_diff_confirmed_by_yz_overnight_share_20",
        "hypothesis": "A=同上。B=Yang-Zhang隔夜方差占比(range_based_vol_1m,S9阶段唯一净入选原子,本族首次配对)。假设:跨尺度熵反常上升(A高)且隔夜驱动为主(B高)=延续;本族最后一批。",
        "expected_sign": 1,
    },
    # ---- SAMPEN_RET_CHG_20: first pairing batch ----
    {
        "id": "EC1",
        "operator": "rank_spread",
        "left": _SAMPEN_CHG,
        "right": _BENCH_RESID_VOL20,
        "mechanism": "sampen_ret_chg_confirmed_by_benchmark_residual_vol_20",
        "hypothesis": "A=SAMPEN_RET_20的20日变化(体检disc-0.0260,非shadow[0.66])。B=对基准回归残差波动率,20日(market_sensitivity,本族首次配对)。假设:样本熵正在上升(A高,趋于随机)且特异波动率高(B高)=延续,负相关(弱,符号按discovery定)。",
        "expected_sign": -1,
    },
    {
        "id": "EC2",
        "operator": "rank_spread",
        "left": _SAMPEN_CHG,
        "right": _JUMP_BETA_STAB,
        "mechanism": "sampen_ret_chg_confirmed_by_jump_beta_stability_20",
        "hypothesis": "A=同上。B=跳跃beta稳定性,20日(jump_continuous_beta,本族首次配对)。假设:样本熵上升(A高)且跳跃beta不稳定(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "EC3",
        "operator": "rank_spread",
        "left": _SAMPEN_CHG,
        "right": _LBAR_OVERNIGHT,
        "mechanism": "sampen_ret_chg_confirmed_by_lbar_overnight_20",
        "hypothesis": "A=同上。B=大单隔夜出现比例(largebar_footprint_1m,本族首次配对)。假设:样本熵上升(A高)且大单隔夜比例低(B低,日内大单减少=更随机)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "EC4",
        "operator": "rank_spread",
        "left": _SAMPEN_CHG,
        "right": _RSKEW20,
        "mechanism": "sampen_ret_chg_confirmed_by_rskew_20",
        "hypothesis": "A=同上。B=已实现偏度,20日(realized_measures_1m,本族首次配对)。假设:样本熵上升(A高)且偏度转负(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "EC5",
        "operator": "rank_spread",
        "left": _SAMPEN_CHG,
        "right": _STREAK_DAYS,
        "mechanism": "sampen_ret_chg_confirmed_by_streak_days",
        "hypothesis": "A=同上。B=基金份额同向变化连续天数(fund_flow,本族首次配对)。假设:样本熵上升(A高)且份额变化连续性低(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "EC6",
        "operator": "rank_spread",
        "left": _SAMPEN_CHG,
        "right": _WICK_SHARE,
        "mechanism": "sampen_ret_chg_confirmed_by_wick_share_20",
        "hypothesis": "A=同上。B=全天影线占比(range_based_vol_1m,本族首次配对)。假设:样本熵上升(A高)且影线占比低(B低,试探性弱)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "EC7",
        "operator": "rank_spread",
        "left": _SAMPEN_CHG,
        "right": _GK_CHG,
        "mechanism": "sampen_ret_chg_confirmed_by_gk_rv_ratio_chg_20",
        "hypothesis": "A=同上。B=GK区间估计/RV之比的20日变化(range_based_vol_1m,本族首次配对)。假设:样本熵上升(A高)且区间比值同步上升(B高,两种复杂度measure的趋势一致)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "EC8",
        "operator": "rank_spread",
        "left": _SAMPEN_CHG,
        "right": _LM_JUMP_COUNT,
        "mechanism": "sampen_ret_chg_confirmed_by_lm_jump_count_20",
        "hypothesis": "A=同上。B=Lee-Mykland跳跃计数,20日(realized_measures_1m,本族首次配对)。假设:样本熵上升(A高)且跳跃频率低(B低,平滑噪声而非跳跃驱动)=延续;本族最后一批,S11阶段所有8个原子的合法配对将全部用尽。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
