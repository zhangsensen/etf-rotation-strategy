#!/usr/bin/env python3
"""Round 573 driver: S15 (controller) stage step 3 --
relative_path_vs_basket_1m pairing, round 3 (covers the last 3 remaining
left-leg atoms). Three first-pairing batches for
REL_UNDERWATER_FRAC_CHG_20, REL_MAXDD_CHG_20, REL_RECOVERY_FRAC_20 -- the
final 3 of the 8 relative_path_vs_basket_1m atoms not yet used as a left
leg (round_571 covered UNDERWATER_FRAC_DIFF_20/REL_MAXDD_20, round_572
covered REL_UNDERWATER_FRAC_20/REL_PERM_ENTROPY_20/REL_PATH_EFFICIENCY_20).

After this round, all 8 relative_path_vs_basket_1m atoms will have used
their one legal pairing batch -- no legal candidates remain for this
family regardless of outcome, so this S15 will need formal closure next
round.

All 24 right-leg partners below are new to this family's S15 pairing
history (round_571/572's 40 partners are not repeated). No same-family
pairs, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_573"

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
_GK_Z60 = {"name": "GK_RV_RATIO_Z_60", "source": "range_based_vol_1m"}
_LZ = {"name": "LZ_COMPLEXITY_20", "source": "complexity_measures_1m"}

_UPSIDE_BETA20 = {"name": "UPSIDE_BETA_20", "source": "market_sensitivity"}
_JUMP_BETA_STAB = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}
_LBAR_OVERNIGHT = {"name": "LBAR_OVERNIGHT_20", "source": "largebar_footprint_1m"}
_RSKEW20 = {"name": "RSKEW_20", "source": "realized_measures_1m"}
_STREAK_DAYS = {"name": "STREAK_DAYS", "source": "fund_flow"}
_MSPE5 = {"name": "MSPE_5M_20", "source": "complexity_measures_1m"}
_VPIN_CLOSE = {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"}
_AD_PRICE_CORR = {"name": "AD_PRICE_CORR_20", "source": "accumulation_distribution_1m"}

_REL_UF_CHG = {"name": "REL_UNDERWATER_FRAC_CHG_20", "source": "relative_path_vs_basket_1m"}
_REL_MAXDD_CHG = {"name": "REL_MAXDD_CHG_20", "source": "relative_path_vs_basket_1m"}
_REL_RECOVERY = {"name": "REL_RECOVERY_FRAC_20", "source": "relative_path_vs_basket_1m"}

base.CANDIDATES = [
    # ---- REL_UNDERWATER_FRAC_CHG_20: first pairing batch ----
    {
        "id": "PA1",
        "operator": "rank_spread",
        "left": _REL_UF_CHG,
        "right": _MARKET_BETA20,
        "mechanism": "rel_underwater_frac_chg_confirmed_by_market_beta_20",
        "hypothesis": "A=主动路径水下占比的20日变化(体检disc-0.0332,atomic未过topk_gate)。B=对篮子beta,20日(market_sensitivity,本族首次配对)。假设:主动水下占比正在上升(A高)且系统性beta高(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "PA2",
        "operator": "rank_spread",
        "left": _REL_UF_CHG,
        "right": _JUMP_BETA20,
        "mechanism": "rel_underwater_frac_chg_confirmed_by_jump_beta_20",
        "hypothesis": "A=同上。B=对篮子跳跃beta,20日(jump_continuous_beta,本族首次配对)。假设:主动水下占比上升(A高)且跳跃beta高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PA3",
        "operator": "rank_spread",
        "left": _REL_UF_CHG,
        "right": _LBAR_RUN_MAX,
        "mechanism": "rel_underwater_frac_chg_confirmed_by_lbar_run_max_20",
        "hypothesis": "A=同上。B=大单连续出现的最长run(largebar_footprint_1m,本族首次配对)。假设:主动水下占比上升(A高)且大单连续性弱(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PA4",
        "operator": "rank_spread",
        "left": _REL_UF_CHG,
        "right": _BPV_RV_RATIO,
        "mechanism": "rel_underwater_frac_chg_confirmed_by_bpv_rv_ratio_20",
        "hypothesis": "A=同上。B=双幂变差/已实现方差比(realized_measures_1m,本族首次配对)。假设:主动水下占比上升(A高)且连续分量占比低(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PA5",
        "operator": "rank_spread",
        "left": _REL_UF_CHG,
        "right": _REL_MOM20,
        "mechanism": "rel_underwater_frac_chg_confirmed_by_relative_market_momentum_20",
        "hypothesis": "A=同上。B=相对基准篮子动量,20日(market_relative_strength,本族首次配对)。假设:主动水下占比上升(A高)且相对动量转弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PA6",
        "operator": "rank_spread",
        "left": _REL_UF_CHG,
        "right": _PROFIT_RATIO60,
        "mechanism": "rel_underwater_frac_chg_confirmed_by_profit_ratio_60",
        "hypothesis": "A=同上。B=60日获利盘比例(cost_distribution,本族首次配对)。假设:主动水下占比上升(A高)且获利盘比例下降(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PA7",
        "operator": "rank_spread",
        "left": _REL_UF_CHG,
        "right": _LIQ_COMMON_R2,
        "mechanism": "rel_underwater_frac_chg_confirmed_by_liq_common_r2_20",
        "hypothesis": "A=同上。B=流动性共性R²(liquidity_commonality_1m,本族首次配对)。假设:主动水下占比上升(A高)且流动性共性升高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PA8",
        "operator": "rank_spread",
        "left": _REL_UF_CHG,
        "right": _PARKINSON,
        "mechanism": "rel_underwater_frac_chg_confirmed_by_parkinson_rv_ratio_20",
        "hypothesis": "A=同上。B=Parkinson区间估计/RV之比(range_based_vol_1m,S9阶段本族原子,本族首次配对)。假设:主动水下占比上升(A高)且bar内活动占比升高(B高)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- REL_MAXDD_CHG_20: first pairing batch ----
    {
        "id": "PB1",
        "operator": "rank_spread",
        "left": _REL_MAXDD_CHG,
        "right": _DOWNSIDE_BETA20,
        "mechanism": "rel_maxdd_chg_confirmed_by_downside_beta_20",
        "hypothesis": "A=主动最大回撤的20日变化(体检disc-0.0177,非shadow)。B=下行beta,20日(market_sensitivity,本族首次配对)。假设:主动最大回撤正在扩大(A高)且下行beta高(B高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "PB2",
        "operator": "rank_spread",
        "left": _REL_MAXDD_CHG,
        "right": _BETA_GAP20,
        "mechanism": "rel_maxdd_chg_confirmed_by_beta_gap_20",
        "hypothesis": "A=同上。B=跳跃beta与连续beta之差(jump_continuous_beta,本族首次配对)。假设:主动最大回撤扩大(A高)且beta缺口方向按discovery定(B)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PB3",
        "operator": "rank_spread",
        "left": _REL_MAXDD_CHG,
        "right": _LBAR_PERM15,
        "mechanism": "rel_maxdd_chg_confirmed_by_lbar_perm15_20",
        "hypothesis": "A=同上。B=大单15分钟排列模式指标(largebar_footprint_1m,本族首次配对)。假设:主动最大回撤扩大(A高)且大单15m模式指标方向按discovery定(B)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PB4",
        "operator": "rank_spread",
        "left": _REL_MAXDD_CHG,
        "right": _JV_RV_SHARE,
        "mechanism": "rel_maxdd_chg_confirmed_by_jump_variation_share_20",
        "hypothesis": "A=同上。B=跳跃变差占已实现方差比例(realized_measures_1m,本族首次配对)。假设:主动最大回撤扩大(A高)且跳跃占比升高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PB5",
        "operator": "rank_spread",
        "left": _REL_MAXDD_CHG,
        "right": _REL_MOM120,
        "mechanism": "rel_maxdd_chg_confirmed_by_relative_market_momentum_120",
        "hypothesis": "A=同上。B=相对基准篮子动量,120日(market_relative_strength,本族首次配对)。假设:主动最大回撤扩大(A高)且长期相对动量转弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PB6",
        "operator": "rank_spread",
        "left": _REL_MAXDD_CHG,
        "right": _OVERHAND_THICK,
        "mechanism": "rel_maxdd_chg_confirmed_by_overhand_thickness_60",
        "hypothesis": "A=同上。B=套牢盘厚度,60日(cost_distribution,本族首次配对)。假设:主动最大回撤扩大(A高)且套牢盘增厚(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PB7",
        "operator": "rank_spread",
        "left": _REL_MAXDD_CHG,
        "right": _GK_Z60,
        "mechanism": "rel_maxdd_chg_confirmed_by_gk_rv_ratio_z_60",
        "hypothesis": "A=同上。B=gk_ratio原始日度序列60日z分数(range_based_vol_1m,本族首次配对)。假设:主动最大回撤扩大(A高)且区间比值异常偏高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PB8",
        "operator": "rank_spread",
        "left": _REL_MAXDD_CHG,
        "right": _LZ,
        "mechanism": "rel_maxdd_chg_confirmed_by_lz_complexity_20",
        "hypothesis": "A=同上。B=1m收益符号序列LZ复杂度(complexity_measures_1m,S11阶段本族原子,本族首次配对)。假设:主动最大回撤扩大(A高)且LZ复杂度升高(B高,更随机)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- REL_RECOVERY_FRAC_20: first pairing batch ----
    {
        "id": "PC1",
        "operator": "rank_spread",
        "left": _REL_RECOVERY,
        "right": _UPSIDE_BETA20,
        "mechanism": "rel_recovery_frac_confirmed_by_upside_beta_20",
        "hypothesis": "A=主动路径恢复时间占比(体检disc-0.0073,本族最独立原子之一)。B=上行beta,20日(market_sensitivity,本族首次配对)。假设:主动恢复耗时占比高(A高)且上行beta低(B低)=延续,负相关(弱)。",
        "expected_sign": -1,
    },
    {
        "id": "PC2",
        "operator": "rank_spread",
        "left": _REL_RECOVERY,
        "right": _JUMP_BETA_STAB,
        "mechanism": "rel_recovery_frac_confirmed_by_jump_beta_stability_20",
        "hypothesis": "A=同上。B=跳跃beta稳定性,20日(jump_continuous_beta,本族首次配对)。假设:主动恢复耗时占比高(A高)且跳跃beta不稳定(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PC3",
        "operator": "rank_spread",
        "left": _REL_RECOVERY,
        "right": _LBAR_OVERNIGHT,
        "mechanism": "rel_recovery_frac_confirmed_by_lbar_overnight_20",
        "hypothesis": "A=同上。B=大单隔夜出现比例(largebar_footprint_1m,本族首次配对)。假设:主动恢复耗时占比高(A高)且大单隔夜比例低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PC4",
        "operator": "rank_spread",
        "left": _REL_RECOVERY,
        "right": _RSKEW20,
        "mechanism": "rel_recovery_frac_confirmed_by_rskew_20",
        "hypothesis": "A=同上。B=已实现偏度,20日(realized_measures_1m,本族首次配对)。假设:主动恢复耗时占比高(A高)且偏度转负(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PC5",
        "operator": "rank_spread",
        "left": _REL_RECOVERY,
        "right": _STREAK_DAYS,
        "mechanism": "rel_recovery_frac_confirmed_by_streak_days",
        "hypothesis": "A=同上。B=基金份额同向变化连续天数(fund_flow,本族首次配对)。假设:主动恢复耗时占比高(A高)且份额变化连续性低(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PC6",
        "operator": "rank_spread",
        "left": _REL_RECOVERY,
        "right": _MSPE5,
        "mechanism": "rel_recovery_frac_confirmed_by_mspe_5m_20",
        "hypothesis": "A=同上。B=5分钟尺度排列熵(complexity_measures_1m,S11阶段本族入选原子,本族首次配对)。假设:主动恢复耗时占比高(A高)且5m尺度熵低(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PC7",
        "operator": "rank_spread",
        "left": _REL_RECOVERY,
        "right": _VPIN_CLOSE,
        "mechanism": "rel_recovery_frac_confirmed_by_vpin_close_20",
        "hypothesis": "A=同上。B=收盘时点VPIN(microstructure_1m,本族首次配对)。假设:主动恢复耗时占比高(A高)且收盘前知情交易浓度升高(B高)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "PC8",
        "operator": "rank_spread",
        "left": _REL_RECOVERY,
        "right": _AD_PRICE_CORR,
        "mechanism": "rel_recovery_frac_confirmed_by_ad_price_corr_20",
        "hypothesis": "A=同上。B=A/D净流与当日收益的20日相关(accumulation_distribution_1m,S10阶段本族原子,本族首次配对)。假设:主动恢复耗时占比高(A高)且量价同步性低(B低)=延续;本族最后一批,S15阶段所有8个原子的合法配对将全部用尽。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
