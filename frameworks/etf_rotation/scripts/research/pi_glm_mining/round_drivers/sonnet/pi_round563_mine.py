#!/usr/bin/env python3
"""Round 563 driver: S12 stage step 3 -- intraday_pain_recovery_1m
pairing, round 3 (covers the last 3 remaining left-leg atoms). Three
first-pairing batches for ULCER_INDEX_CHG_20, PAIN_INDEX_CHG_20,
RECOVERY_TIME_FRAC_CHG_20 -- the final 3 of the 8
intraday_pain_recovery_1m atoms not yet used as a left leg (round_561
covered DD_RECOVERY_SPEED_RATIO_20/UNDERWATER_FRAC_Z_60, round_562
covered ULCER_INDEX_20/PAIN_INDEX_20/RECOVERY_TIME_FRAC_20).

After this round, all 8 intraday_pain_recovery_1m atoms will have used
their one legal pairing batch -- no legal candidates remain for this
family regardless of outcome, so S12 will need formal closure next
round.

All 24 right-leg partners below are new to this family's S12 pairing
history (round_561/562's 40 partners are not repeated). No same-family
pairs, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_563"

_MARKET_BETA20 = {"name": "MARKET_BETA_20", "source": "market_sensitivity"}
_CONTINUOUS_BETA20 = {"name": "CONTINUOUS_BETA_20", "source": "jump_continuous_beta"}
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
_WICK_SHARE = {"name": "WICK_SHARE_20", "source": "range_based_vol_1m"}
_APEN = {"name": "APEN_RET_20", "source": "complexity_measures_1m"}

_BENCH_RESID_VOL20 = {"name": "BENCHMARK_RESIDUAL_VOL_20", "source": "market_sensitivity"}
_JUMP_BETA_STAB = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}
_LBAR_OVERNIGHT = {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"}
_RSKEW20 = {"name": "RSKEW_20", "source": "realized_measures_1m"}
_STREAK_DAYS = {"name": "STREAK_DAYS", "source": "fund_flow"}
_GK_CHG = {"name": "GK_RV_RATIO_CHG_20", "source": "range_based_vol_1m"}
_LZ = {"name": "LZ_COMPLEXITY_20", "source": "complexity_measures_1m"}
_VPIN_CLOSE = {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"}

_ULCER_CHG = {"name": "ULCER_INDEX_CHG_20", "source": "intraday_pain_recovery_1m"}
_PAIN_CHG = {"name": "PAIN_INDEX_CHG_20", "source": "intraday_pain_recovery_1m"}
_RECOVERY_FRAC_CHG = {"name": "RECOVERY_TIME_FRAC_CHG_20", "source": "intraday_pain_recovery_1m"}

base.CANDIDATES = [
    # ---- ULCER_INDEX_CHG_20: first pairing batch ----
    {
        "id": "HA1",
        "operator": "rank_spread",
        "left": _ULCER_CHG,
        "right": _MARKET_BETA20,
        "mechanism": "ulcer_index_chg_confirmed_by_market_beta_20",
        "hypothesis": "A=溃疡指数的20日变化(体检disc-0.0284,atomic因vs intraday_drawdown_1m:INTRADAY_MAXDD_CHG_20冗余被拒)。B=对篮子beta,20日(market_sensitivity,本族首次配对)。假设:溃疡指数正在上升(A高)且系统性beta高(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "HA2",
        "operator": "rank_spread",
        "left": _ULCER_CHG,
        "right": _CONTINUOUS_BETA20,
        "mechanism": "ulcer_index_chg_confirmed_by_continuous_beta_20",
        "hypothesis": "A=同上。B=对篮子连续beta,20日(jump_continuous_beta,本族首次配对)。假设:溃疡指数上升(A高)且连续beta高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "HA3",
        "operator": "rank_spread",
        "left": _ULCER_CHG,
        "right": _LBAR_RUN_MAX,
        "mechanism": "ulcer_index_chg_confirmed_by_lbar_run_max_20",
        "hypothesis": "A=同上。B=大单连续出现的最长run(largebar_footprint_1m,本族首次配对)。假设:溃疡指数上升(A高)且大单连续性增强(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "HA4",
        "operator": "rank_spread",
        "left": _ULCER_CHG,
        "right": _BPV_RV_RATIO,
        "mechanism": "ulcer_index_chg_confirmed_by_bpv_rv_ratio_20",
        "hypothesis": "A=同上。B=双幂变差/已实现方差比(realized_measures_1m,本族首次配对)。假设:溃疡指数上升(A高)且连续分量占比低(B低,跳跃驱动恶化)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "HA5",
        "operator": "rank_spread",
        "left": _ULCER_CHG,
        "right": _REL_MOM20,
        "mechanism": "ulcer_index_chg_confirmed_by_relative_market_momentum_20",
        "hypothesis": "A=同上。B=相对基准篮子动量,20日(market_relative_strength,本族首次配对)。假设:溃疡指数上升(A高)且相对动量转弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "HA6",
        "operator": "rank_spread",
        "left": _ULCER_CHG,
        "right": _PROFIT_RATIO60,
        "mechanism": "ulcer_index_chg_confirmed_by_profit_ratio_60",
        "hypothesis": "A=同上。B=60日获利盘比例(cost_distribution,本族首次配对)。假设:溃疡指数上升(A高)且获利盘比例下降(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "HA7",
        "operator": "rank_spread",
        "left": _ULCER_CHG,
        "right": _LIQ_COMMON_R2,
        "mechanism": "ulcer_index_chg_confirmed_by_liq_common_r2_20",
        "hypothesis": "A=同上。B=流动性共性R²(liquidity_commonality_1m,本族首次配对)。假设:溃疡指数上升(A高)且流动性共性升高(B高,系统性流动性恶化)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "HA8",
        "operator": "rank_spread",
        "left": _ULCER_CHG,
        "right": _PARKINSON,
        "mechanism": "ulcer_index_chg_confirmed_by_parkinson_rv_ratio_20",
        "hypothesis": "A=同上。B=Parkinson区间估计/RV之比(range_based_vol_1m,S9阶段本族原子,本族首次配对)。假设:溃疡指数上升(A高)且bar内活动占比升高(B高)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- PAIN_INDEX_CHG_20: first pairing batch ----
    {
        "id": "HB1",
        "operator": "rank_spread",
        "left": _PAIN_CHG,
        "right": _DOWNSIDE_BETA20,
        "mechanism": "pain_index_chg_confirmed_by_downside_beta_20",
        "hypothesis": "A=痛苦指数的20日变化(体检disc-0.0252,atomic因vs S7同族CHG原子冗余被拒)。B=下行beta,20日(market_sensitivity,本族首次配对)。假设:痛苦指数上升(A高)且下行beta高(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "HB2",
        "operator": "rank_spread",
        "left": _PAIN_CHG,
        "right": _BETA_GAP20,
        "mechanism": "pain_index_chg_confirmed_by_beta_gap_20",
        "hypothesis": "A=同上。B=跳跃beta与连续beta之差(jump_continuous_beta,本族首次配对)。假设:痛苦指数上升(A高)且beta缺口方向按discovery定(B)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "HB3",
        "operator": "rank_spread",
        "left": _PAIN_CHG,
        "right": _LBAR_PERM15,
        "mechanism": "pain_index_chg_confirmed_by_lbar_perm15_20",
        "hypothesis": "A=同上。B=大单15分钟排列模式指标(largebar_footprint_1m,本族首次配对)。假设:痛苦指数上升(A高)且大单15m模式指标方向按discovery定(B)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "HB4",
        "operator": "rank_spread",
        "left": _PAIN_CHG,
        "right": _JV_RV_SHARE,
        "mechanism": "pain_index_chg_confirmed_by_jump_variation_share_20",
        "hypothesis": "A=同上。B=跳跃变差占已实现方差比例(realized_measures_1m,本族首次配对)。假设:痛苦指数上升(A高)且跳跃占比升高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "HB5",
        "operator": "rank_spread",
        "left": _PAIN_CHG,
        "right": _REL_MOM120,
        "mechanism": "pain_index_chg_confirmed_by_relative_market_momentum_120",
        "hypothesis": "A=同上。B=相对基准篮子动量,120日(market_relative_strength,本族首次配对)。假设:痛苦指数上升(A高)且长期相对动量转弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "HB6",
        "operator": "rank_spread",
        "left": _PAIN_CHG,
        "right": _OVERHAND_THICK,
        "mechanism": "pain_index_chg_confirmed_by_overhand_thickness_60",
        "hypothesis": "A=同上。B=套牢盘厚度,60日(cost_distribution,本族首次配对)。假设:痛苦指数上升(A高)且套牢盘增厚(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "HB7",
        "operator": "rank_spread",
        "left": _PAIN_CHG,
        "right": _WICK_SHARE,
        "mechanism": "pain_index_chg_confirmed_by_wick_share_20",
        "hypothesis": "A=同上。B=全天影线占比(range_based_vol_1m,本族首次配对)。假设:痛苦指数上升(A高)且影线占比升高(B高,试探性加剧)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "HB8",
        "operator": "rank_spread",
        "left": _PAIN_CHG,
        "right": _APEN,
        "mechanism": "pain_index_chg_confirmed_by_apen_ret_20",
        "hypothesis": "A=同上。B=1m收益近似熵(complexity_measures_1m,S11阶段本族原子,本族首次配对)。假设:痛苦指数上升(A高)且近似熵升高(B高,更随机)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- RECOVERY_TIME_FRAC_CHG_20: first pairing batch ----
    {
        "id": "HC1",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC_CHG,
        "right": _BENCH_RESID_VOL20,
        "mechanism": "recovery_time_frac_chg_confirmed_by_benchmark_residual_vol_20",
        "hypothesis": "A=恢复时间占比的20日变化(体检disc+0.0186,非shadow[0.40])。B=对基准回归残差波动率,20日(market_sensitivity,本族首次配对)。假设:恢复耗时占比正在上升(A高,收复能力恶化)且特异波动率升高(B高)=延续,正相关(弱)。",
        "expected_sign": 1,
    },
    {
        "id": "HC2",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC_CHG,
        "right": _JUMP_BETA_STAB,
        "mechanism": "recovery_time_frac_chg_confirmed_by_jump_beta_stability_20",
        "hypothesis": "A=同上。B=跳跃beta稳定性,20日(jump_continuous_beta,本族首次配对)。假设:恢复耗时占比上升(A高)且跳跃beta不稳定(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "HC3",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC_CHG,
        "right": _LBAR_OVERNIGHT,
        "mechanism": "recovery_time_frac_chg_confirmed_by_lbar_overnight_20",
        "hypothesis": "A=同上。B=大单隔夜出现比例(largebar_footprint_1m,本族首次配对)。假设:恢复耗时占比上升(A高)且大单隔夜比例下降(B低,日内大单减少)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "HC4",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC_CHG,
        "right": _RSKEW20,
        "mechanism": "recovery_time_frac_chg_confirmed_by_rskew_20",
        "hypothesis": "A=同上。B=已实现偏度,20日(realized_measures_1m,本族首次配对)。假设:恢复耗时占比上升(A高)且偏度转负(B低)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "HC5",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC_CHG,
        "right": _STREAK_DAYS,
        "mechanism": "recovery_time_frac_chg_confirmed_by_streak_days",
        "hypothesis": "A=同上。B=基金份额同向变化连续天数(fund_flow,本族首次配对)。假设:恢复耗时占比上升(A高)且份额变化连续性下降(B低)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "HC6",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC_CHG,
        "right": _GK_CHG,
        "mechanism": "recovery_time_frac_chg_confirmed_by_gk_rv_ratio_chg_20",
        "hypothesis": "A=同上。B=GK区间估计/RV之比的20日变化(range_based_vol_1m,本族首次配对)。假设:恢复耗时占比上升(A高)且区间比值同步上升(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "HC7",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC_CHG,
        "right": _LZ,
        "mechanism": "recovery_time_frac_chg_confirmed_by_lz_complexity_20",
        "hypothesis": "A=同上。B=1m收益符号序列LZ复杂度(complexity_measures_1m,S11阶段本族原子,本族首次配对)。假设:恢复耗时占比上升(A高)且LZ复杂度升高(B高,更随机)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "HC8",
        "operator": "rank_spread",
        "left": _RECOVERY_FRAC_CHG,
        "right": _VPIN_CLOSE,
        "mechanism": "recovery_time_frac_chg_confirmed_by_vpin_close_20",
        "hypothesis": "A=同上。B=收盘时点VPIN(microstructure_1m,本族首次配对)。假设:恢复耗时占比上升(A高)且收盘前知情交易浓度升高(B高)=延续;本族最后一批,S12阶段所有8个原子的合法配对将全部用尽。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
