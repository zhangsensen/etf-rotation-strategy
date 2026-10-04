#!/usr/bin/env python3
"""Round 526 driver: S4 stage step 8 -- jump_continuous_beta pairing, round 8.

Seven-round scoreboard (round_519-525, 104 candidates, 9 net admissions
after round_525's window-variant self-correction, no three-zero streak).
CONTINUOUS_BETA_60's asymmetry channel (round_522/523/524) and its
serial_dependence/RET_ACF1 channel (round_525, corrected to 1 net) are both
now treated as extracted -- further partners there would mostly rediscover
already-admitted information.

This round pairs CONTINUOUS_BETA_60 with the two remaining catalog families
most directly relevant to a jump/continuous beta decomposition and never
yet touched by any jump_continuous_beta leg: realized_measures_1m
(Barndorff-Nielsen-Shephard 2004 bipower variation, Andersen-Bollerslev-
Diebold 2007 jump-variation share, Amaya-Christoffersen-Jacobs-Vasquez 2015
realized skew/kurtosis -- literally the same jump-detection literature this
family's own atoms cite, but measuring an asset's OWN univariate jump
activity rather than its co-jump beta with the market) and microstructure_1m
(Kyle 1985 lambda, Amihud 2002 illiquidity, VPIN, Roll 1984 spread, order-
flow-imbalance autocorrelation -- price-impact/liquidity constructs that
could plausibly confirm whether a beta's jump component reflects genuine
information-driven impact vs noise).

JUMP_BETA_20 and BETA_GAP_20 and JUMP_BETA_STABILITY_20 (all flat/closed
across 6+ rounds of diverse partners) each get exactly 2 atoms from these
fresh families as a final diagnostic -- own-jump-activity atoms for
JUMP_BETA_20 (the most directly analogous new information), price-impact
atoms for the other two. CONTINUOUS_BETA_20 stays fully closed, no new
candidates.

All (left,right) combos below are new to this family's cumulative history.
No same-family pairs, no window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_526"

_BPV_RV_RATIO = {"name": "BPV_RV_RATIO_20", "source": "realized_measures_1m"}
_JV_RV_SHARE = {"name": "JV_RV_SHARE_20", "source": "realized_measures_1m"}
_LM_JUMP_COUNT = {"name": "LM_JUMP_COUNT_20", "source": "realized_measures_1m"}
_RSKEW20_RM = {"name": "RSKEW_20", "source": "realized_measures_1m"}
_RKURT20 = {"name": "RKURT_20", "source": "realized_measures_1m"}
_RS_MINUS20 = {"name": "RS_MINUS_20", "source": "realized_measures_1m"}
_VOL_USHAPE20 = {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"}

_VPIN_CLOSE = {"name": "VPIN_CLOSE_20", "source": "microstructure_1m"}
_KYLE_LAMBDA = {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"}
_ROLL_SPREAD = {"name": "ROLL_SPREAD_20", "source": "microstructure_1m"}
_AMIHUD_1M = {"name": "AMIHUD_1M_20", "source": "microstructure_1m"}
_OFI_AUTOCORR = {"name": "OFI_AUTOCORR_20", "source": "microstructure_1m"}
_IMPACT_ASYM = {"name": "IMPACT_ASYM_20", "source": "microstructure_1m"}

_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_JB20 = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_BGAP20 = {"name": "BETA_GAP_20", "source": "jump_continuous_beta"}
_JBSTAB20 = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}

base.CANDIDATES = [
    # ---- CONTINUOUS_BETA_60 x realized_measures_1m: same jump-detection
    # literature as this leg's own construction, but univariate own-jump
    # activity instead of cross-asset co-jump beta ----
    {
        "id": "KT1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _BPV_RV_RATIO,
        "mechanism": "continuous_beta60_confirmed_by_bpv_rv_ratio",
        "hypothesis": "A=连续分量beta，60日窗（9次净入选中5次来自该腿：asymmetry×3, ACF1×1净计）。B=双幂变差/已实现方差比（Barndorff-Nielsen-Shephard 2004，本族首次使用；衡量自身收益中连续分量占比，与A的构造方法同源但是单资产自身跳跃占比而非与市场的协跳跃beta）。假设：常态系统性暴露高(A高)且自身收益以连续分量为主(B高，跳跃占比低)=系统性暴露的定价更平滑可预测，延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KT2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _JV_RV_SHARE,
        "mechanism": "continuous_beta60_confirmed_by_jump_variation_share",
        "hypothesis": "A=同上。B=跳跃变差占已实现方差比例（Andersen-Bollerslev-Diebold 2007，本族首次使用；与A互补——A是与市场的协变化中连续分量，B是自身方差中跳跃占比）。假设：常态系统性暴露高(A高)且自身跳跃占比低(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KT3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _LM_JUMP_COUNT,
        "mechanism": "continuous_beta60_confirmed_by_jump_count",
        "hypothesis": "A=同上。B=Lee-Mykland跳跃计数（本族首次使用；自身跳跃发生频率，与A的连续分量beta构造中排除的跳跃bar直接对应）。假设：常态系统性暴露高(A高)且自身跳跃频率低(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KT4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RSKEW20_RM,
        "mechanism": "continuous_beta60_confirmed_by_realized_skew",
        "hypothesis": "A=同上。B=已实现偏度（Amaya-Christoffersen-Jacobs-Vasquez 2015，本族首次使用；由高频收益直接计算的偏度，与round_523已入选的daily RETURN_SKEW_20不同数据频率的独立预注册原子）。假设：常态系统性暴露高(A高)且日内已实现偏度为正(B高)=延续，测试该asymmetry channel在高频尺度是否也成立。",
        "expected_sign": 1,
    },
    {
        "id": "KT5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RKURT20,
        "mechanism": "continuous_beta60_confirmed_by_realized_kurtosis",
        "hypothesis": "A=同上。B=已实现峰度（同上，本族首次使用）。假设：常态系统性暴露高(A高)且日内已实现峰度低(B低，尾部薄)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KT6",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RS_MINUS20,
        "mechanism": "continuous_beta60_confirmed_by_realized_semivariance_minus",
        "hypothesis": "A=同上。B=已实现负半方差占比（Barndorff-Nielsen-Kinnebrock-Shephard风格下行波动分解，本族首次使用）。假设：常态系统性暴露高(A高)且下行半方差占比低(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KT7",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _VOL_USHAPE20,
        "mechanism": "continuous_beta60_confirmed_by_vol_ushape",
        "hypothesis": "A=同上。B=日内成交量U型强度（round_053门7已admitted的独立原子，本族首次使用；与A测试是否有交互增量）。假设：常态系统性暴露高(A高)且U型强度高(B高，开盘收盘量能集中)=延续。",
        "expected_sign": 1,
    },
    # ---- CONTINUOUS_BETA_60 x microstructure_1m: price-impact confirmation ----
    {
        "id": "KU1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _VPIN_CLOSE,
        "mechanism": "continuous_beta60_confirmed_by_vpin",
        "hypothesis": "A=同上。B=收盘时点VPIN（成交量同步概率的知情交易概率代理，本族首次使用）。假设：常态系统性暴露高(A高)且VPIN高(B高，知情交易占比高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KU2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _KYLE_LAMBDA,
        "mechanism": "continuous_beta60_confirmed_by_kyle_lambda",
        "hypothesis": "A=同上。B=Kyle(1985)价格冲击系数（本族首次使用）。假设：常态系统性暴露高(A高)且价格冲击系数高(B高，流动性薄)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KU3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _ROLL_SPREAD,
        "mechanism": "continuous_beta60_confirmed_by_roll_spread",
        "hypothesis": "A=同上。B=Roll(1984)隐含买卖价差（收益序列相关估计，本族首次使用）。假设：常态系统性暴露高(A高)且隐含价差大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KU4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _AMIHUD_1M,
        "mechanism": "continuous_beta60_confirmed_by_amihud_1m",
        "hypothesis": "A=同上。B=Amihud(2002)非流动性比率的1m版本（本族首次使用）。假设：常态系统性暴露高(A高)且非流动性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KU5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _OFI_AUTOCORR,
        "mechanism": "continuous_beta60_confirmed_by_ofi_autocorr",
        "hypothesis": "A=同上。B=订单流不平衡自相关（本族首次使用）。假设：常态系统性暴露高(A高)且订单流不平衡持续性强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KU6",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _IMPACT_ASYM,
        "mechanism": "continuous_beta60_confirmed_by_impact_asymmetry",
        "hypothesis": "A=同上。B=价格冲击不对称性（买单冲击vs卖单冲击的差异，本族首次使用；与A的asymmetry主题呼应但衡量的是微观结构层面的不对称，非收益分布层面）。假设：常态系统性暴露高(A高)且冲击不对称明显(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- flat/closed legs: 2-atom final diagnostic each with genuinely
    # fresh, conceptually-matched families ----
    {
        "id": "KV1",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _JV_RV_SHARE,
        "mechanism": "jump_beta_confirmed_by_jump_variation_share",
        "hypothesis": "A=跳跃分量beta（2/11，round_520后再无新命中）。B=自身跳跃变差占比（realized_measures_1m，本腿首次接触；与A直接相关——A衡量跳跃期与市场的协变化，B衡量自身跳跃活跃度，逻辑上最贴近的confirming partner）。假设：跳跃期系统性暴露高(A高)且自身跳跃活跃(B高)=该资产的跳跃更多是系统性驱动而非孤立噪声，延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KV2",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _LM_JUMP_COUNT,
        "mechanism": "jump_beta_confirmed_by_jump_count",
        "hypothesis": "A=同上。B=自身跳跃计数（realized_measures_1m，本腿首次接触）。假设：延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KV3",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _KYLE_LAMBDA,
        "mechanism": "beta_gap_confirmed_by_kyle_lambda",
        "hypothesis": "A=崩盘beta缺口（0/9，此前partner全部来自微观结构量能/量价对称/宏观对冲/序列相关主题）。B=Kyle价格冲击系数（microstructure_1m，本腿首次接触）。假设：缺口大(A高)且价格冲击系数高(B高)=延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KV4",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _IMPACT_ASYM,
        "mechanism": "beta_gap_confirmed_by_impact_asymmetry",
        "hypothesis": "A=同上。B=价格冲击不对称性（microstructure_1m，本腿首次接触）。假设：延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KV5",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _VPIN_CLOSE,
        "mechanism": "jump_beta_stability_confirmed_by_vpin",
        "hypothesis": "A=跳跃beta估计不确定性（1/18，round_521 KI1后再无新命中）。B=VPIN（microstructure_1m，本腿首次接触）。假设：估计不确定性高(A高)且知情交易概率高(B高)=延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KV6",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _OFI_AUTOCORR,
        "mechanism": "jump_beta_stability_confirmed_by_ofi_autocorr",
        "hypothesis": "A=同上。B=订单流不平衡自相关（microstructure_1m，本腿首次接触）。假设：延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
