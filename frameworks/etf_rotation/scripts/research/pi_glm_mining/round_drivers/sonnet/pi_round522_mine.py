#!/usr/bin/env python3
"""Round 522 driver: S4 stage step 4 -- jump_continuous_beta pairing, round 4.

Three-round scoreboard (round_519-521, 45 candidates, 4 admitted):
JUMP_BETA_20 2/11 partners (now flat after 6 straight misses in round_521 --
treated as near-exhausted, gets only 1 final orthogonal-family diagnostic
partner this round, no more volume/microstructure-theme partners).
BETA_GAP_20 0/8 (flat across every theme tried so far -- 1 final
orthogonal-family diagnostic partner, then close).
CONTINUOUS_BETA_20 0/6 including 3 clean rank_correlation_redundancy fails
-- structurally shadow, closed, no new candidates this round.
CONTINUOUS_BETA_60 0/10 pairs (atomic admitted) but two round_521 misses
(KG2 t=2.69, KG3 t=3.09) died only on the bp floor, not on direction or
redundancy -- one more amplitude/concentration-themed pass.
JUMP_BETA_STABILITY_20 1/8 (round_521's KI1 broke its 0/6 streak via
LBAR_OVERNIGHT_20) -- the channel the data currently favors, gets the
largest new-partner allocation this round, drawn from jump/liquidity-shock
themed families never yet paired with this atom (cojump_1m,
liquidity_commonality_1m) plus cost-distribution/large-bar atoms unused so
far anywhere in this family's history.

All partners below are new to this family's cumulative pairing history
(round_519+520+521's ~23 partners are all excluded). No same-family pairs,
no window variants of an existing (left,right) combo."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_522"

_LBAR_SILENT = {"name": "LBAR_SILENT_20", "source": "largebar_footprint_1m"}
_IDIO_JUMP_SHARE = {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"}
_COJUMP_DIR_AGREE = {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"}
_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_RET_CONC_60 = {"name": "RETURN_CONCENTRATION_60", "source": "return_concentration"}
_OVERHANG = {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"}
_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_BIGBAR_EDGE_CONC = {"name": "BIGBAR_EDGE_CONC_20", "source": "bar_size_order_flow"}
_CAT_VOL60 = {"name": "CATEGORY_VOL_60", "source": "category_state"}
_RET_CONC_20 = {"name": "RETURN_CONCENTRATION_20", "source": "return_concentration"}
_GOLD_CORR20 = {"name": "GOLD_PARTIAL_CORR_20", "source": "macro_hedge_sensitivity"}
_BOND_CORR20 = {"name": "BOND_PARTIAL_CORR_20", "source": "macro_hedge_sensitivity"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}

_JB20 = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_BGAP20 = {"name": "BETA_GAP_20", "source": "jump_continuous_beta"}
_JBSTAB20 = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}
_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}

base.CANDIDATES = [
    # ---- JUMP_BETA_STABILITY_20: follow the channel (KI1 admitted last
    # round, t=2.47, +17.3bp); jump-share/liquidity-shock themes fit the
    # "estimation uncertainty of the jump beta" mechanism directly ----
    {
        "id": "KJ1",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _LBAR_SILENT,
        "mechanism": "jump_beta_stability_confirmed_by_bigbar_silent",
        "hypothesis": "A=跳跃beta估计不确定性（round_521 KI1已证该腿非退化：×LBAR_OVERNIGHT_20 t=2.47 +17.3bp）。B=大bar沉寂期长度（largebar_footprint_1m，本族首次使用）。假设：估计不确定性高(A高)且近期大bar沉寂(B高，冲击稀疏)=不确定性缺乏近期事件校准，估计更不可靠，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KJ2",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _IDIO_JUMP_SHARE,
        "mechanism": "jump_beta_stability_confirmed_by_idio_jump_share",
        "hypothesis": "A=同上。B=特异跳跃占比（cojump_1m，本族首次使用；衡量跳跃是否为个体特异而非市场共振）。假设：估计不确定性高(A高)且跳跃以特异性为主(B高，非共振)=跳跃beta估计噪声主要来自个体特质冲击而非可靠的系统性关系，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KJ3",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _COJUMP_DIR_AGREE,
        "mechanism": "jump_beta_stability_confirmed_by_cojump_dir_agree",
        "hypothesis": "A=同上。B=共跳方向一致性（cojump_1m，本族首次使用）。假设：估计不确定性高(A高)且共跳方向不一致(B低，与A高同向定义为rank_spread(A,B)高)=跳跃beta估计缺乏方向一致性支撑，延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KJ4",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "jump_beta_stability_confirmed_by_idio_liquidity_shock",
        "hypothesis": "A=同上。B=特异流动性冲击z值（liquidity_commonality_1m，本族首次使用）。假设：估计不确定性高(A高)且遭遇特异流动性冲击(B高)=跳跃beta的估计噪声与流动性冲击同源，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KJ5",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _RESILIENCY,
        "mechanism": "jump_beta_stability_confirmed_by_resiliency",
        "hypothesis": "A=同上。B=流动性恢复力（liquidity_commonality_1m，本族首次使用）。假设：估计不确定性高(A高)且流动性恢复力弱(B低)=冲击后价格发现慢，估计噪声持续更久，用rank_spread(A,B)方向按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KJ6",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _RET_CONC_60,
        "mechanism": "jump_beta_stability_confirmed_by_return_concentration",
        "hypothesis": "A=同上。B=60日收益集中度（return_concentration，本族首次使用；收益是否由少数日主导）。假设：估计不确定性高(A高)且收益由少数极端日主导(B高)=跳跃beta的信息含量集中在稀疏事件上，估计天然不稳定，延续。",
        "expected_sign": 1,
    },
    {
        "id": "KJ7",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _OVERHANG,
        "mechanism": "jump_beta_stability_confirmed_by_overhang_thickness",
        "hypothesis": "A=同上。B=套牢盘厚度（cost_distribution，本族首次使用）。假设：估计不确定性高(A高)且套牢盘厚(B高)=解套抛压使跳跃反应缺乏稳定的系统性结构，延续；诊断性测试。",
        "expected_sign": 1,
    },
    # ---- CONTINUOUS_BETA_60: one more amplitude/concentration pass
    # (round_521 KG2 t=2.69, KG3 t=3.09 both died only on bp floor) ----
    {
        "id": "KK1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _BIGBAR_DIR_SKEW,
        "mechanism": "continuous_beta60_confirmed_by_bigbar_dir_skew",
        "hypothesis": "A=连续分量beta，60日窗（JB2已atomic入选）。B=大bar方向偏斜（bar_size_order_flow，本族首次使用）。假设：常态系统性暴露高(A高)且大bar方向持续偏向一侧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KK2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _BIGBAR_EDGE_CONC,
        "mechanism": "continuous_beta60_confirmed_by_bigbar_edge_concentration",
        "hypothesis": "A=同上。B=大bar集中于日内边缘时段的程度（bar_size_order_flow，本族首次使用）。假设：常态系统性暴露高(A高)且大bar集中在开盘/收盘边缘(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KK3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CAT_VOL60,
        "mechanism": "continuous_beta60_confirmed_by_category_vol_60",
        "hypothesis": "A=同上。B=60日板块波动率（category_state，与已用20日版本互补窗口的独立预注册原子，本族首次使用60日版本）。假设：常态系统性暴露高(A高)且板块长期高波动(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KK4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RET_CONC_20,
        "mechanism": "continuous_beta60_confirmed_by_return_concentration_20",
        "hypothesis": "A=同上。B=20日收益集中度（return_concentration，本族首次使用）。假设：常态系统性暴露高(A高)且近期收益集中在少数日(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- JUMP_BETA_20: near-exhausted (2/11, 0/6 last round), one final
    # orthogonal-family diagnostic before closing this leg ----
    {
        "id": "KL1",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _GOLD_CORR20,
        "mechanism": "jump_beta_confirmed_by_gold_partial_correlation",
        "hypothesis": "A=跳跃分量beta（2/11 partner命中，round_521连续6次未过，接近饱和）。B=与黄金的偏相关（macro_hedge_sensitivity，本族首次使用，与前11个partner的微观结构/量能主题完全正交）。假设：跳跃期系统性暴露高(A高)且与避险资产相关性低(B低，风险偏好资产特征)=延续；本条为该腿关闭前最后一次正交信息面诊断。",
        "expected_sign": 1,
    },
    # ---- BETA_GAP_20: flat 0/8, one final orthogonal-family diagnostic
    # before closing this leg ----
    {
        "id": "KM1",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _BOND_CORR20,
        "mechanism": "beta_gap_confirmed_by_bond_partial_correlation",
        "hypothesis": "A=崩盘beta缺口（0/8，前8个partner全部来自微观结构/量能主题）。B=与国债的偏相关（macro_hedge_sensitivity，本族首次使用，完全正交信息面）。假设：缺口大(A高)且与债券负相关更强(B低，风险资产特征更纯)=延续；本条为该腿关闭前最后一次正交诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KM2",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _CHIP_RANGE,
        "mechanism": "beta_gap_confirmed_by_chip_range",
        "hypothesis": "A=同上。B=90分位筹码分布宽度（cost_distribution，本族首次使用）。假设：缺口大(A高)且筹码分布宽(B高，持仓成本分散)=延续；本条为该腿关闭前最后一次正交诊断，测试完毕后若仍为0命中则该腿判定穷尽。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
