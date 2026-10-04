#!/usr/bin/env python3
"""Round 557 driver: S11 stage step 1 -- complexity_measures_1m family
(Pincus 1991 ApEn; Richman-Moorman 2000 SampEn; Lempel-Ziv 1976/
Kaspar-Schuster 1987 LZ complexity; Eckmann-Kamphorst-Ruelle 1987
recurrence rate; multiscale permutation entropy), main controller's
pre-specified S11 direction deepening the S6 channel after S9's closure
(round_556). The controller's S10 block (accumulation_distribution_1m) is
superseded by this S11 block per the directive's own stated precedence
("本块覆盖上方'当前生效'").

Atom health (round_557_atom_health, vs permutation_entropy_1m/
serial_dependence/path_efficiency): 5 of 8 atoms are shadow, and far more
extreme than this line's usual 0.70-0.80 shadow band -- SAMPEN_RET_20
(0.96), LZ_COMPLEXITY_20 (0.96), RECURRENCE_RATE_20 (0.98),
MSPE_SCALE_DIFF_20 (0.89), APEN_RET_20 (0.86), all vs S6's
PERM_ENTROPY_RET_20 or CEP_DISTANCE_20. This is a materially different
finding than prior stages' shadow flags: SampEn/ApEn/LZ/RR are, at these
correlation levels, near-restatements of the same "randomness vs
structure" axis PERM_ENTROPY_RET_20 already captures, not independent
complexity dimensions -- and since PERM_ENTROPY_RET_20 itself is a prior
gate-7 admission (S6), the OFFICIAL dedup gate (which compares against
shelf16+prior-admitted, not just this broad atom-health reference) will
very likely reject these five outright on redundancy, atomic or paired.
Only the multiscale atoms (MSPE_5M_20 corr 0.44, MSPE_15M_20 corr 0.17)
and the CHG variant (SAMPEN_RET_CHG_20 corr 0.66) are genuinely below the
0.70 line and represent whatever independent signal this channel has
left, consistent with coarse-graining (multiscale entropy) being a
different axis than same-scale entropy re-estimated a different way.

This round: 8 atomic (all new atoms, run for completeness/protocol even
though 5 are expected to fail on redundancy) + 2 first pairing batches
for the two most independent atoms, MSPE_15M_20 and MSPE_5M_20 = 24
candidates, within the 15-30 band."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_557"

_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_LBAR_CLOCK_STD = {"name": "LBAR_CLOCK_STD_20", "source": "largebar_footprint_1m"}
_GRANGER_IN = {"name": "GRANGER_IN_DEGREE_20", "source": "cross_dependence_1m"}
_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_CONTINUOUS_BETA20 = {"name": "CONTINUOUS_BETA_20", "source": "jump_continuous_beta"}
_GAP_VOL_RATIO = {"name": "GAP_VOL_RATIO_20", "source": "gap_volatility"}

_TICK_IMBALANCE = {"name": "TICK_IMBALANCE_20", "source": "bar_size_order_flow"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_PEER_RESID_Z = {"name": "PEER_RESID_Z_20", "source": "peer_relative_value"}
_CAT_DISP20 = {"name": "CATEGORY_DISPERSION_20", "source": "category_state"}
_TRACK_ERR60 = {"name": "TRACKING_ERROR_60", "source": "market_relative_strength"}
_PROFIT_RATIO60 = {"name": "PROFIT_RATIO_60", "source": "cost_distribution"}
_RS_RATIO = {"name": "RS_RV_RATIO_20", "source": "range_based_vol_1m"}

_SAMPEN = {"name": "SAMPEN_RET_20", "source": "complexity_measures_1m"}
_APEN = {"name": "APEN_RET_20", "source": "complexity_measures_1m"}
_LZ = {"name": "LZ_COMPLEXITY_20", "source": "complexity_measures_1m"}
_MSPE5 = {"name": "MSPE_5M_20", "source": "complexity_measures_1m"}
_MSPE15 = {"name": "MSPE_15M_20", "source": "complexity_measures_1m"}
_MSPE_DIFF = {"name": "MSPE_SCALE_DIFF_20", "source": "complexity_measures_1m"}
_RR = {"name": "RECURRENCE_RATE_20", "source": "complexity_measures_1m"}
_SAMPEN_CHG = {"name": "SAMPEN_RET_CHG_20", "source": "complexity_measures_1m"}

base.CANDIDATES = [
    # ---- 8 atomic: new complexity_measures_1m atoms ----
    {
        "id": "CA1",
        "operator": "atomic",
        "left": _SAMPEN,
        "right": _SAMPEN,
        "mechanism": "sampen_ret_20",
        "hypothesis": "Richman-Moorman(2000)样本熵,m=2,r=0.2*std,1m收益,20日均值。体检:disc-0.0971/579天/审计-0.0614,max|corr|=0.96(vs permutation_entropy_1m:PERM_ENTROPY_RET_20,S6已admitted原子),标记shadow(远超常规0.70-0.80区间)。假设:样本熵高(A高,序列更随机)=噪声主导,rank与未来收益负相关;预期因与已admitted原子高度共线而在官方去重门被拒。",
        "expected_sign": -1,
    },
    {
        "id": "CA2",
        "operator": "atomic",
        "left": _APEN,
        "right": _APEN,
        "mechanism": "apen_ret_20",
        "hypothesis": "Pincus(1991)近似熵,同参数,含自匹配,20日均值。体检:disc-0.0988/审计-0.0551,max|corr|=0.86(vs同一S6原子),shadow。假设方向同SampEn。",
        "expected_sign": -1,
    },
    {
        "id": "CA3",
        "operator": "atomic",
        "left": _LZ,
        "right": _LZ,
        "mechanism": "lz_complexity_20",
        "hypothesis": "Lempel-Ziv(1976)/Kaspar-Schuster(1987)归一化复杂度,收益符号序列,20日均值。体检:disc-0.0965/审计-0.0788,max|corr|=0.96(vs同一S6原子),shadow。假设:LZ复杂度高(A高,算法压缩率低=更随机)=噪声主导,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "CA4",
        "operator": "atomic",
        "left": _MSPE5,
        "right": _MSPE5,
        "mechanism": "mspe_5m_20",
        "hypothesis": "5分钟聚合收益的Bandt-Pompe排列熵(多尺度熵框架),20日均值。体检:disc-0.0613/审计-0.0599,max|corr|=0.44,非shadow——本族8个原子里与S6重叠度最低的两个之一。假设:5m尺度仍随机(A高)=噪声主导,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "CA5",
        "operator": "atomic",
        "left": _MSPE15,
        "right": _MSPE15,
        "mechanism": "mspe_15m_20",
        "hypothesis": "15分钟聚合收益的排列熵,20日均值。体检:disc-0.0254/审计-0.0131,max|corr|=0.17,本族最独立原子。假设:15m尺度仍随机(A高)=噪声主导,负相关(弱)。",
        "expected_sign": -1,
    },
    {
        "id": "CA6",
        "operator": "atomic",
        "left": _MSPE_DIFF,
        "right": _MSPE_DIFF,
        "mechanism": "mspe_scale_diff_20",
        "hypothesis": "15m排列熵减去同日1m排列熵(跨尺度有序度变化),20日均值。体检:disc+0.0787/审计+0.0513,max|corr|=0.89(vs permutation_entropy_1m:CEP_DISTANCE_20),shadow。假设:粗粒度化后熵不降反升(A高,反常)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "CA7",
        "operator": "atomic",
        "left": _RR,
        "right": _RR,
        "mechanism": "recurrence_rate_20",
        "hypothesis": "Eckmann-Kamphorst-Ruelle(1987)递归率,m=2,与SampEn同容差,20日均值。体检:disc+0.0945/审计+0.0711,max|corr|=0.98(vs permutation_entropy_1m:CEP_DISTANCE_20),shadow(本族最高相关)。假设:递归率高(A高,轨迹重访多=结构性强)=延续,正相关。",
        "expected_sign": 1,
    },
    {
        "id": "CA8",
        "operator": "atomic",
        "left": _SAMPEN_CHG,
        "right": _SAMPEN_CHG,
        "mechanism": "sampen_ret_chg_20",
        "hypothesis": "SAMPEN_RET_20的20日变化(复杂度趋势)。体检:disc-0.0260/审计+0.0046,max|corr|=0.66(vs permutation_entropy_1m:PERM_ENTROPY_RET_CHG_20),非shadow(接近阈值)。假设:样本熵正在上升(A高,趋于随机)=噪声增加,负相关(弱,符号按discovery定)。",
        "expected_sign": -1,
    },
    # ---- MSPE_15M_20: first pairing batch (most independent atom) ----
    {
        "id": "CB1",
        "operator": "rank_spread",
        "left": _MSPE15,
        "right": _VOL_SPIKE,
        "mechanism": "mspe_15m_confirmed_by_vol_spike_freq_20",
        "hypothesis": "A=15分钟尺度排列熵(体检disc-0.0254,本族最独立)。B=成交量突增频率(intraday_volume_profile_1m,本线通道原子之一,本族首次配对)。假设:15m尺度仍随机(A高)且成交放量突增频繁(B高,噪声由放量驱动)=延续,负相关。",
        "expected_sign": -1,
    },
    {
        "id": "CB2",
        "operator": "rank_spread",
        "left": _MSPE15,
        "right": _BIGBAR_VOL_SHARE,
        "mechanism": "mspe_15m_confirmed_by_bigbar_vol_share_20",
        "hypothesis": "A=同上。B=大单成交量占比(bar_size_order_flow,本族首次配对)。假设:15m尺度仍随机(A高)且大单占比低(B低,非结构性大单驱动)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "CB3",
        "operator": "rank_spread",
        "left": _MSPE15,
        "right": _LBAR_CLOCK_STD,
        "mechanism": "mspe_15m_confirmed_by_lbar_clock_std_20",
        "hypothesis": "A=同上。B=大单出现时刻标准差(largebar_footprint_1m,本族首次配对)。假设:15m尺度仍随机(A高)且大单时刻分散(B高,无规律)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "CB4",
        "operator": "rank_spread",
        "left": _MSPE15,
        "right": _GRANGER_IN,
        "mechanism": "mspe_15m_confirmed_by_granger_in_degree_20",
        "hypothesis": "A=同上。B=格兰杰因果入度(cross_dependence_1m,本族首次配对)。假设:15m尺度仍随机(A高)且被同伴领先影响弱(B低,无外部结构注入)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "CB5",
        "operator": "rank_spread",
        "left": _MSPE15,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "mspe_15m_confirmed_by_idio_liquidity_shock_20",
        "hypothesis": "A=同上。B=特异流动性冲击z值(liquidity_commonality_1m,本族首次配对)。假设:15m尺度仍随机(A高)且特异流动性冲击小(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "CB6",
        "operator": "rank_spread",
        "left": _MSPE15,
        "right": _REL_MOM20,
        "mechanism": "mspe_15m_confirmed_by_relative_market_momentum_20",
        "hypothesis": "A=同上。B=相对基准篮子动量,20日(market_relative_strength,本族首次配对)。假设:15m尺度仍随机(A高)且相对动量弱(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "CB7",
        "operator": "rank_spread",
        "left": _MSPE15,
        "right": _CONTINUOUS_BETA20,
        "mechanism": "mspe_15m_confirmed_by_continuous_beta_20",
        "hypothesis": "A=同上。B=对14只等权篮子的连续beta,20日(jump_continuous_beta,本族首次配对)。假设:15m尺度仍随机(A高)且系统性beta低(B低,特异性噪声)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "CB8",
        "operator": "rank_spread",
        "left": _MSPE15,
        "right": _GAP_VOL_RATIO,
        "mechanism": "mspe_15m_confirmed_by_gap_volatility_ratio_20",
        "hypothesis": "A=同上。B=跳空波动率比率(gap_volatility,本族首次配对)。假设:15m尺度仍随机(A高)且跳空波动占比低(B低)=延续;本族最后一批。",
        "expected_sign": -1,
    },
    # ---- MSPE_5M_20: first pairing batch ----
    {
        "id": "CC1",
        "operator": "rank_spread",
        "left": _MSPE5,
        "right": _TICK_IMBALANCE,
        "mechanism": "mspe_5m_confirmed_by_tick_imbalance_20",
        "hypothesis": "A=5分钟尺度排列熵(体检disc-0.0613)。B=tick方向不平衡(bar_size_order_flow,本族首次配对)。假设:5m尺度仍随机(A高)且tick不平衡弱(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "CC2",
        "operator": "rank_spread",
        "left": _MSPE5,
        "right": _VOL_ENTROPY,
        "mechanism": "mspe_5m_confirmed_by_vol_entropy_20",
        "hypothesis": "A=同上。B=日内成交量分布熵(intraday_volume_profile_1m,本族首次配对)。假设:5m尺度收益随机(A高)且成交时点分布也均匀(B高)=两个维度的随机性共振,延续。",
        "expected_sign": -1,
    },
    {
        "id": "CC3",
        "operator": "rank_spread",
        "left": _MSPE5,
        "right": _AMIHUD_1M,
        "mechanism": "mspe_5m_confirmed_by_amihud_1m_20",
        "hypothesis": "A=同上。B=Amihud非流动性比率1m版本(microstructure_1m,本族首次配对)。假设:5m尺度仍随机(A高)且非流动性低(B低,流动性好=噪声更纯粹)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "CC4",
        "operator": "rank_spread",
        "left": _MSPE5,
        "right": _PEER_RESID_Z,
        "mechanism": "mspe_5m_confirmed_by_peer_resid_z_20",
        "hypothesis": "A=同上。B=相对同伴协整残差z值(peer_relative_value,本族首次配对)。假设:5m尺度仍随机(A高)且相对同伴无明显偏离(B按discovery定)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "CC5",
        "operator": "rank_spread",
        "left": _MSPE5,
        "right": _CAT_DISP20,
        "mechanism": "mspe_5m_confirmed_by_category_dispersion_20",
        "hypothesis": "A=同上。B=板块内部20日收益离散度(category_state,本族首次配对)。假设:5m尺度仍随机(A高)且板块内部分化小(B低,系统性弱)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "CC6",
        "operator": "rank_spread",
        "left": _MSPE5,
        "right": _TRACK_ERR60,
        "mechanism": "mspe_5m_confirmed_by_tracking_error_60",
        "hypothesis": "A=同上。B=相对基准跟踪误差,60日(market_relative_strength,本族首次配对)。假设:5m尺度仍随机(A高)且跟踪误差低(B低)=延续。",
        "expected_sign": -1,
    },
    {
        "id": "CC7",
        "operator": "rank_spread",
        "left": _MSPE5,
        "right": _PROFIT_RATIO60,
        "mechanism": "mspe_5m_confirmed_by_profit_ratio_60",
        "hypothesis": "A=同上。B=60日获利盘比例(cost_distribution,本族首次配对)。假设:5m尺度仍随机(A高)且获利盘比例低(B低)=延续;符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "CC8",
        "operator": "rank_spread",
        "left": _MSPE5,
        "right": _RS_RATIO,
        "mechanism": "mspe_5m_confirmed_by_rs_rv_ratio_20",
        "hypothesis": "A=同上。B=Rogers-Satchell区间估计/RV之比(range_based_vol_1m,S9阶段本族唯一有信号的比值,本族首次配对)。假设:5m尺度仍随机(A高)且bar内活动占比低(B低)=延续;本族最后一批。",
        "expected_sign": -1,
    },
]

if __name__ == "__main__":
    base.main()
