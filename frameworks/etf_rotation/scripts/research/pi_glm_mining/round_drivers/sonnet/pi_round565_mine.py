#!/usr/bin/env python3
"""Round 565 driver: S13 stage step 1 -- frequency_domain_beta_1m family
(Engle 1974 band-spectrum regression; Bandi-Perron 2008; Dew-Becker-Giglio
2016; Chaudhuri-Lo 2016), main controller's pre-specified S13 direction
after S12's closure (round_564).

Atom health (round_565_atom_health, vs market_sensitivity/
jump_continuous_beta/cross_dependence_1m/intraday_systematic_share): 3 of
8 atoms are shadow -- BETA_HF_20 (0.76), BETA_MF_20 (0.83), BETA_LF_20
(0.79), all vs market_sensitivity:MARKET_BETA_60 (expected: all three
band-betas are "beta to market" variants and correlate with plain beta).
The derived/differential constructs are genuinely novel: BETA_FREQ_SLOPE_20
(0.54), COHERENCE_LF_HF_DIFF_20 (0.56), BETA_HF_CHG_20 (0.67),
BETA_LF_CHG_20 (0.41), BETA_FREQ_SLOPE_CHG_20 (0.13, most independent) --
these test whether the beta-market RELATIONSHIP varies by frequency, not
just its level, which is a different economic question than plain beta.

This round: 8 atomic (all new atoms) + 2 first pairing batches for the
two most independent atoms, BETA_FREQ_SLOPE_CHG_20 and BETA_LF_CHG_20 =
24 candidates, within the 15-30 band."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_565"

_HKS_SLOT = {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"}
_TRACK_ERR20 = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_RS_RATIO = {"name": "RS_RV_RATIO_20", "source": "range_based_vol_1m"}
_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_UF_Z60 = {"name": "UNDERWATER_FRAC_Z_60", "source": "intraday_pain_recovery_1m"}

_OVERNIGHT_DIFF = {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"}
_REL_MOM60 = {"name": "REL_MARKET_MOM_60", "source": "market_relative_strength"}
_CAT_DISP20 = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_GAP_SESSION_CORR = {"name": "GAP_SESSION_CORR_20", "source": "gap_response"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_PERM_ENTROPY_RET = {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}
_YZ_OVERNIGHT = {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"}

_BETA_HF = {"name": "BETA_HF_20", "source": "frequency_domain_beta_1m"}
_BETA_MF = {"name": "BETA_MF_20", "source": "frequency_domain_beta_1m"}
_BETA_LF = {"name": "BETA_LF_20", "source": "frequency_domain_beta_1m"}
_FREQ_SLOPE = {"name": "BETA_FREQ_SLOPE_20", "source": "frequency_domain_beta_1m"}
_COH_DIFF = {"name": "COHERENCE_LF_HF_DIFF_20", "source": "frequency_domain_beta_1m"}
_BETA_HF_CHG = {"name": "BETA_HF_CHG_20", "source": "frequency_domain_beta_1m"}
_BETA_LF_CHG = {"name": "BETA_LF_CHG_20", "source": "frequency_domain_beta_1m"}
_FREQ_SLOPE_CHG = {"name": "BETA_FREQ_SLOPE_CHG_20", "source": "frequency_domain_beta_1m"}

base.CANDIDATES = [
    # ---- 8 atomic: new frequency_domain_beta_1m atoms ----
    {
        "id": "IA1",
        "operator": "atomic",
        "left": _BETA_HF,
        "right": _BETA_HF,
        "mechanism": "beta_hf_20",
        "hypothesis": "Engle(1974)频带回归beta,高频带(周期<15分钟,k>16),对510300/510500市场代理,20日均值。体检:disc-0.1045/579天/审计-0.0516,max|corr|=0.76(vs market_sensitivity:MARKET_BETA_60),shadow(预期内,高频beta本质仍是beta)。假设:高频beta高(A高)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "IA2",
        "operator": "atomic",
        "left": _BETA_MF,
        "right": _BETA_MF,
        "mechanism": "beta_mf_20",
        "hypothesis": "同上,中频带(15-60分钟,4<=k<=16)。体检:disc-0.0920/审计-0.0549,max|corr|=0.83(vs同一原子),shadow。假设方向同高频beta。",
        "expected_sign": -1,
    },
    {
        "id": "IA3",
        "operator": "atomic",
        "left": _BETA_LF,
        "right": _BETA_LF,
        "mechanism": "beta_lf_20",
        "hypothesis": "同上,低频带(周期>60分钟,k<4,仅3个频率bin,估计噪声较大)。体检:disc-0.0708/审计-0.0368,max|corr|=0.79(vs同一原子),shadow。假设方向同高频beta。",
        "expected_sign": -1,
    },
    {
        "id": "IA4",
        "operator": "atomic",
        "left": _FREQ_SLOPE,
        "right": _FREQ_SLOPE,
        "mechanism": "beta_freq_slope_20",
        "hypothesis": "Bandi-Perron(2008)长短期beta缺口:低频beta减高频beta,20日均值。体检:disc+0.0257/审计-0.0333,max|corr|=0.54(vs cross_dependence_1m:GRANGER_OUT_DEGREE_20),非shadow。假设:长期beta相对高频beta更高(A高,长期系统性风险主导)=延续,正相关(弱)。",
        "expected_sign": 1,
    },
    {
        "id": "IA5",
        "operator": "atomic",
        "left": _COH_DIFF,
        "right": _COH_DIFF,
        "mechanism": "coherence_lf_hf_diff_20",
        "hypothesis": "Dew-Becker-Giglio(2016)频域相干性:低频相干性减高频相干性(Cauchy-Schwarz有界[0,1]),20日均值。体检:disc+0.0102(接近0)/审计+0.0355,max|corr|=0.56,非shadow。假设:低频共动更强(A高,长期基本面共振)=延续(弱,符号按discovery定)。",
        "expected_sign": 1,
    },
    {
        "id": "IA6",
        "operator": "atomic",
        "left": _BETA_HF_CHG,
        "right": _BETA_HF_CHG,
        "mechanism": "beta_hf_chg_20",
        "hypothesis": "BETA_HF_20的20日变化。体检:disc-0.0018(接近0)/审计-0.0251,max|corr|=0.67(vs cross_dependence_1m:DEP_DRIFT_20),非shadow(接近阈值)。假设:高频beta正在上升(A高)=延续(弱,符号按discovery定)。",
        "expected_sign": -1,
    },
    {
        "id": "IA7",
        "operator": "atomic",
        "left": _BETA_LF_CHG,
        "right": _BETA_LF_CHG,
        "mechanism": "beta_lf_chg_20",
        "hypothesis": "BETA_LF_20的20日变化。体检:disc+0.0451/审计-0.0395,max|corr|=0.41,非shadow(本族较独立原子之一)。假设:低频beta正在上升(A高,长期系统性暴露增加)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "IA8",
        "operator": "atomic",
        "left": _FREQ_SLOPE_CHG,
        "right": _FREQ_SLOPE_CHG,
        "mechanism": "beta_freq_slope_chg_20",
        "hypothesis": "BETA_FREQ_SLOPE_20的20日变化(频率斜率的趋势)。体检:disc+0.0347/审计-0.0079,max|corr|=0.13,本族最独立原子。假设:频率斜率正在上升(A高,长短期beta缺口扩大)=延续,正相关(弱)。",
        "expected_sign": 1,
    },
    # ---- BETA_FREQ_SLOPE_CHG_20: first pairing batch (most independent atom) ----
    {
        "id": "IB1",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE_CHG,
        "right": _HKS_SLOT,
        "mechanism": "freq_slope_chg_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=频率斜率的20日变化(体检disc+0.0347,本族最独立原子)。B=日内时段模式持续性(intraday_periodicity,S4阶段命中partner,本族首次配对)。假设:频率斜率扩大(A高)且日内时段模式稳定(B高)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "IB2",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE_CHG,
        "right": _TRACK_ERR20,
        "mechanism": "freq_slope_chg_confirmed_by_tracking_error_20",
        "hypothesis": "A=同上。B=相对基准跟踪误差,20日(market_relative_strength,本族首次配对)。假设:频率斜率扩大(A高)且跟踪误差高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "IB3",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE_CHG,
        "right": _CATEGORY_VOL,
        "mechanism": "freq_slope_chg_confirmed_by_category_vol_20",
        "hypothesis": "A=同上。B=板块20日波动率(category_state,本族首次配对)。假设:频率斜率扩大(A高)且板块波动低(B低)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "IB4",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE_CHG,
        "right": _VOL_SPIKE,
        "mechanism": "freq_slope_chg_confirmed_by_vol_spike_freq_20",
        "hypothesis": "A=同上。B=成交量突增频率(intraday_volume_profile_1m,本族首次配对)。假设:频率斜率扩大(A高)且成交放量突增频繁(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "IB5",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE_CHG,
        "right": _GAP_FILL60,
        "mechanism": "freq_slope_chg_confirmed_by_gap_fill_fraction_60",
        "hypothesis": "A=同上。B=跳空回补比例,60日(gap_repair,本族首次配对)。假设:频率斜率扩大(A高)且跳空回补比例低(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "IB6",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE_CHG,
        "right": _RS_RATIO,
        "mechanism": "freq_slope_chg_confirmed_by_rs_rv_ratio_20",
        "hypothesis": "A=同上。B=Rogers-Satchell区间估计/RV之比(range_based_vol_1m,S9阶段本族唯一有信号比值,本族首次配对)。假设:频率斜率扩大(A高)且bar内活动占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "IB7",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE_CHG,
        "right": _SAMPEN,
        "mechanism": "freq_slope_chg_confirmed_by_sampen_ret_20",
        "hypothesis": "A=同上。B=1m收益样本熵(complexity_measures_1m,S11阶段本族原子,本族首次配对)。假设:频率斜率扩大(A高)且样本熵高(B高,高频噪声更随机)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "IB8",
        "operator": "rank_spread",
        "left": _FREQ_SLOPE_CHG,
        "right": _UF_Z60,
        "mechanism": "freq_slope_chg_confirmed_by_underwater_frac_z_60",
        "hypothesis": "A=同上。B=水下时间占比60日z分数(intraday_pain_recovery_1m,S12阶段本族唯一净入选原子,本族首次配对)。假设:频率斜率扩大(A高)且水下占比异常偏高(B高)=延续;本族最后一批。",
        "expected_sign": 1,
    },
    # ---- BETA_LF_CHG_20: first pairing batch ----
    {
        "id": "IC1",
        "operator": "rank_spread",
        "left": _BETA_LF_CHG,
        "right": _OVERNIGHT_DIFF,
        "mechanism": "beta_lf_chg_confirmed_by_overnight_intra_diff_20",
        "hypothesis": "A=低频beta的20日变化(体检disc+0.0451,本族较独立原子)。B=隔夜与日内收益差异(intraday_periodicity,本族首次配对)。假设:低频beta上升(A高)且隔夜/日内分化明显(B按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "IC2",
        "operator": "rank_spread",
        "left": _BETA_LF_CHG,
        "right": _REL_MOM60,
        "mechanism": "beta_lf_chg_confirmed_by_relative_market_momentum_60",
        "hypothesis": "A=同上。B=相对基准篮子动量,60日(market_relative_strength,本族首次配对)。假设:低频beta上升(A高)且相对动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "IC3",
        "operator": "rank_spread",
        "left": _BETA_LF_CHG,
        "right": _CAT_DISP20,
        "mechanism": "beta_lf_chg_confirmed_by_category_dispersion_20",
        "hypothesis": "A=同上。B=板块内部20日收益离散度(category_state,本族首次配对)。假设:低频beta上升(A高)且板块内部分化小(B低,系统性增强)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "IC4",
        "operator": "rank_spread",
        "left": _BETA_LF_CHG,
        "right": _AMIHUD_1M,
        "mechanism": "beta_lf_chg_confirmed_by_amihud_1m_20",
        "hypothesis": "A=同上。B=Amihud非流动性比率1m版本(microstructure_1m,本族首次配对)。假设:低频beta上升(A高)且非流动性低(B低)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "IC5",
        "operator": "rank_spread",
        "left": _BETA_LF_CHG,
        "right": _GAP_SESSION_CORR,
        "mechanism": "beta_lf_chg_confirmed_by_gap_session_correlation_20",
        "hypothesis": "A=同上。B=跳空与随后session表现的相关性(gap_response,S4阶段最强命中partner,t=3.89,本族首次配对)。假设:低频beta上升(A高)且跳空延续性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "IC6",
        "operator": "rank_spread",
        "left": _BETA_LF_CHG,
        "right": _CHIP_RANGE,
        "mechanism": "beta_lf_chg_confirmed_by_chip_range_90_60",
        "hypothesis": "A=同上。B=90分位筹码分布宽度(cost_distribution,本族首次配对)。假设:低频beta上升(A高)且筹码分布宽(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "IC7",
        "operator": "rank_spread",
        "left": _BETA_LF_CHG,
        "right": _PERM_ENTROPY_RET,
        "mechanism": "beta_lf_chg_confirmed_by_perm_entropy_ret_20",
        "hypothesis": "A=同上。B=1m收益排列熵(permutation_entropy_1m,S6阶段全线首个不含成交量两窗口显著原子,本族首次配对)。假设:低频beta上升(A高)且排列熵低(B低,结构性更强)=延续;符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "IC8",
        "operator": "rank_spread",
        "left": _BETA_LF_CHG,
        "right": _YZ_OVERNIGHT,
        "mechanism": "beta_lf_chg_confirmed_by_yz_overnight_share_20",
        "hypothesis": "A=同上。B=Yang-Zhang隔夜方差占比(range_based_vol_1m,S9阶段唯一净入选原子,本族首次配对)。假设:低频beta上升(A高)且隔夜驱动为主(B高)=延续;本族最后一批。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
