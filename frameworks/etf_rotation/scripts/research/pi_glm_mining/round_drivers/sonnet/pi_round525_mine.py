#!/usr/bin/env python3
"""Round 525 driver: S4 stage step 7 -- jump_continuous_beta pairing, round 7.

Six-round scoreboard (round_519-524, 89 candidates, 8 admitted, no
three-zero streak yet). CONTINUOUS_BETA_60's asymmetry channel (4/27:
atomic, BIGBAR_DIR_SKEW_20, RETURN_SKEW_20, MAX5_MEAN_20) looks saturated:
round_524 exhausted the two families built specifically for co-moment/tail
asymmetry (coskewness_risk, upside_tail) and every remaining strong-t
candidate there died on rank_correlation_redundancy against its own prior
admissions, not on economic weakness. Continuing to mine the SAME
asymmetry theme would now mostly re-discover already-admitted information.

This round switches to a genuinely different information type never once
paired with any jump_continuous_beta atom across 6 rounds: serial_dependence
(return/sign autocorrelation and variance-ratio tests of return
predictability -- an isolated discovery dimension in this line's own
catalog, built from same-ETF close-to-close returns only, no volume/
co-moment/tail content at all). The economic link tested: does a beta's
jump/continuous decomposition co-occur with reversal or momentum in the
same asset's own return sequence (distinct from asymmetry/tail-shape).

Compute is split: CONTINUOUS_BETA_60 (still the productive leg) gets the
full 9-atom serial_dependence sweep; the three flat/closed legs
(JUMP_BETA_20, BETA_GAP_20, JUMP_BETA_STABILITY_20) each get exactly 2
atoms from this fresh family as a final diagnostic against a genuinely new
information type (not the microstructure/volume themes they were already
closed against) -- consistent with "3 partners is one cluster" but this is
a different cluster, not a repeat. CONTINUOUS_BETA_20 stays closed (0/6,
structurally shadow) and gets nothing.

All 15 (left,right) combos below are new. No same-family pairs, no window
variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_525"

_RET_ACF1_5 = {"name": "RET_ACF1_5", "source": "serial_dependence"}
_RET_ACF1_20 = {"name": "RET_ACF1_20", "source": "serial_dependence"}
_RET_ACF1_60 = {"name": "RET_ACF1_60", "source": "serial_dependence"}
_SIGN_ACF1_5 = {"name": "SIGN_ACF1_5", "source": "serial_dependence"}
_SIGN_ACF1_20 = {"name": "SIGN_ACF1_20", "source": "serial_dependence"}
_SIGN_ACF1_60 = {"name": "SIGN_ACF1_60", "source": "serial_dependence"}
_RET_ACF2_20 = {"name": "RET_ACF2_20", "source": "serial_dependence"}
_RET_ACF2_60 = {"name": "RET_ACF2_60", "source": "serial_dependence"}
_VAR_RATIO_5_60 = {"name": "VAR_RATIO_5_60", "source": "serial_dependence"}
_VAR_RATIO_20_120 = {"name": "VAR_RATIO_20_120", "source": "serial_dependence"}

_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}
_JB20 = {"name": "JUMP_BETA_20", "source": "jump_continuous_beta"}
_BGAP20 = {"name": "BETA_GAP_20", "source": "jump_continuous_beta"}
_JBSTAB20 = {"name": "JUMP_BETA_STABILITY_20", "source": "jump_continuous_beta"}

base.CANDIDATES = [
    # ---- CONTINUOUS_BETA_60: full serial_dependence sweep (9 atoms,
    # genuinely new information type after the asymmetry channel saturated) ----
    {
        "id": "KR1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RET_ACF1_5,
        "mechanism": "continuous_beta60_confirmed_by_ret_acf1_5",
        "hypothesis": "A=连续分量beta，60日窗（4次asymmetry主题命中，该主题本轮已换方向）。B=5日收益一阶自相关（serial_dependence，本线独立发现维度，仅用同ETF自身收盘价，从未与本族任何腿配对）。假设：常态系统性暴露高(A高)且短期收益呈现动量(B高，正自相关)=系统性暴露的定价存在惯性延续，用rank_spread方向按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "KR2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RET_ACF1_20,
        "mechanism": "continuous_beta60_confirmed_by_ret_acf1_20",
        "hypothesis": "A=同上。B=20日版本（同上）。假设：同KR1，中期窗口下是否更强。",
        "expected_sign": 1,
    },
    {
        "id": "KR3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RET_ACF1_60,
        "mechanism": "continuous_beta60_confirmed_by_ret_acf1_60",
        "hypothesis": "A=同上。B=60日版本（同上，与A同窗对齐）。假设：同KR1，同窗对齐是否更强。",
        "expected_sign": 1,
    },
    {
        "id": "KR4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _SIGN_ACF1_5,
        "mechanism": "continuous_beta60_confirmed_by_sign_acf1_5",
        "hypothesis": "A=同上。B=5日收益符号一阶自相关（serial_dependence，符号版本，对极端值更稳健，本族首次使用）。假设：常态系统性暴露高(A高)且涨跌方向持续(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KR5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _SIGN_ACF1_20,
        "mechanism": "continuous_beta60_confirmed_by_sign_acf1_20",
        "hypothesis": "A=同上。B=20日版本（同上）。假设：同KR4，中期窗口。",
        "expected_sign": 1,
    },
    {
        "id": "KR6",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _SIGN_ACF1_60,
        "mechanism": "continuous_beta60_confirmed_by_sign_acf1_60",
        "hypothesis": "A=同上。B=60日版本（同上，与A同窗对齐）。假设：同KR4，同窗对齐。",
        "expected_sign": 1,
    },
    {
        "id": "KR7",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RET_ACF2_20,
        "mechanism": "continuous_beta60_confirmed_by_ret_acf2_20",
        "hypothesis": "A=同上。B=20日收益二阶自相关（serial_dependence，捕捉更长周期的收益记忆结构，本族首次使用）。假设：常态系统性暴露高(A高)且存在二阶记忆(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "KR8",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RET_ACF2_60,
        "mechanism": "continuous_beta60_confirmed_by_ret_acf2_60",
        "hypothesis": "A=同上。B=60日版本（同上，与A同窗对齐）。假设：同KR7，同窗对齐。",
        "expected_sign": 1,
    },
    {
        "id": "KR9",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _VAR_RATIO_5_60,
        "mechanism": "continuous_beta60_confirmed_by_variance_ratio_5_60",
        "hypothesis": "A=同上。B=5日聚合收益方差与随机游走假设的比值（serial_dependence方差比检验，本族首次使用；偏离1衡量趋势/均值回复）。假设：常态系统性暴露高(A高)且方差比偏离1(B方向按discovery定，趋势性更强)=延续。",
        "expected_sign": 1,
    },
    # ---- flat/closed legs: 2-atom final diagnostic each against this
    # genuinely fresh family (not a repeat of prior microstructure/volume
    # themed closures) ----
    {
        "id": "KS1",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _RET_ACF1_20,
        "mechanism": "jump_beta_confirmed_by_ret_acf1_20",
        "hypothesis": "A=跳跃分量beta（2/11，round_520后再无新命中，此前partner全部来自微观结构/量能主题）。B=20日收益一阶自相关（serial_dependence，本腿首次接触的信息类型）。假设：跳跃期系统性暴露高(A高)且自身收益呈现动量(B高)=延续；该腿最后一次正交信息面诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KS2",
        "operator": "rank_spread",
        "left": _JB20,
        "right": _VAR_RATIO_20_120,
        "mechanism": "jump_beta_confirmed_by_variance_ratio_20_120",
        "hypothesis": "A=同上。B=20日/120日方差比（serial_dependence，本腿首次接触）。假设：延续；该腿最后一次正交诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KS3",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _SIGN_ACF1_20,
        "mechanism": "beta_gap_confirmed_by_sign_acf1_20",
        "hypothesis": "A=崩盘beta缺口（0/9，此前partner全部来自微观结构/量能/宏观对冲主题）。B=20日符号自相关（serial_dependence，本腿首次接触）。假设：缺口大(A高)且涨跌方向持续(B高)=延续；该腿最后一次正交诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KS4",
        "operator": "rank_spread",
        "left": _BGAP20,
        "right": _VAR_RATIO_5_60,
        "mechanism": "beta_gap_confirmed_by_variance_ratio_5_60",
        "hypothesis": "A=同上。B=5日/60日方差比（serial_dependence，本腿首次接触）。假设：延续；该腿最后一次正交诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KS5",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _RET_ACF2_20,
        "mechanism": "jump_beta_stability_confirmed_by_ret_acf2_20",
        "hypothesis": "A=跳跃beta估计不确定性（1/18，round_521 KI1后再无新命中）。B=20日收益二阶自相关（serial_dependence，本腿首次接触）。假设：估计不确定性高(A高)且存在二阶收益记忆(B方向按discovery定)=延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
    {
        "id": "KS6",
        "operator": "rank_spread",
        "left": _JBSTAB20,
        "right": _RET_ACF1_60,
        "mechanism": "jump_beta_stability_confirmed_by_ret_acf1_60",
        "hypothesis": "A=同上。B=60日收益一阶自相关（serial_dependence，本腿首次接触）。假设：延续；该腿最后一次诊断。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
