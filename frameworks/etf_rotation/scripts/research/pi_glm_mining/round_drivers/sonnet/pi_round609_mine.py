#!/usr/bin/env python3
"""Round 609 driver: S26 stage (only round) -- cross-line reproduction of
pi lane's core 1m volume-channel atoms and two significant pairings,
main controller's pre-specified S26 direction after S25's closure
(round_608).

RESULT: all 9 candidates below (5 atomic + 4 pairs) were individually
plan-tested (one at a time, since `plan` halts on the first hash
collision) and EVERY ONE triggered the engine's canonical-hash
collision safety net -- confirming each is byte-identical to an
already-admitted historical candidate in this shared codebase:
  S26A1 VOL_SPIKE_FREQ_20 (atomic) -- collision
  S26A2 BIGBAR_VOL_SHARE_20 (atomic) -- collision
  S26A3 BIGBAR_DIR_SKEW_20 (atomic) -- collision
  S26A4 VOL_AUTOCORR_20 (atomic) -- collision
  S26A5 LOG_AMOUNT_VOL_20 (atomic) -- collision
  S26Z2 = BIGBAR_DIR_SKEW_20 x VOL_AUTOCORR_20 -- collision vs round_022
    Z2 (t=3.56, +49.2bp, matches pi's +49.2bp exactly)
  S26CO36 = VT_AUTOCORR_20 x VOL_SPIKE_FREQ_20 -- collision vs round_603
    XB1 (S24, this line's own independent literature-based
    implementation, t=3.63, +45.4bp vs pi's +47.7bp/t3.14)
  S26BB1 = VOL_SPIKE_FREQ_20 x ULCER_20 -- collision vs round_027 BB1
    (t=2.72, +36.3bp, matches pi's +36.3bp exactly)
  S26AI4 = GAP_FILL_FRACTION_60 x VOL_SPIKE_FREQ_20 -- collision vs
    round_060 AI4 (t=3.55, +42.7bp, matches pi's +42.7bp exactly)

Pre-flight check (via grep of frameworks/etf_rotation/configs/*.yaml,
done before attempting any plan lock): all 5 directive atoms and the
2 additional atoms needed for the pairs (ULCER_20, GAP_FILL_FRACTION_60)
ALREADY EXIST in this shared codebase's family configs
(intraday_volume_profile_1m, bar_size_order_flow, liquidity_variability,
drawdown, gap_repair) -- these are shelf atoms from the pi/GLM line's
original 79-round history (predates this Sonnet line's round_500
start), not something unique to pi's own workspace that this line had
never touched. Per the 'no reinventing the wheel' rule, none were
rebuilt; the hash-collision confirmations above ARE the reproduction
verification (a hash match proves byte-identical construction, not a
coincidental resemblance). This driver is left in CANDIDATES form for
documentation; running `plan` against all 9 at once will halt at the
first collision (as `cmd_plan` asserts one at a time) -- each was
therefore removed and re-planned individually during round_609 to
confirm all 9, not just the first."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_609"

_VOL_SPIKE_FREQ = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_BIGBAR_VOL_SHARE = {"name": "BIGBAR_VOL_SHARE_20", "source": "bar_size_order_flow"}
_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_VOL_AUTOCORR = {"name": "VOL_AUTOCORR_20", "source": "intraday_volume_profile_1m"}
_LOG_AMOUNT_VOL = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_ULCER_20 = {"name": "ULCER_20", "source": "ohlcv"}
_GAP_FILL_60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_VT_AUTOCORR = {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"}

base.CANDIDATES = [
    # ---- 5 atomic reproductions (all confirmed hash-collision vs shared history) ----
    {"id": "S26A1", "operator": "atomic", "left": _VOL_SPIKE_FREQ, "right": _VOL_SPIKE_FREQ,
     "mechanism": "s26_reproduce_vol_spike_freq_20",
     "hypothesis": "复现 pi 单原子 VOL_SPIKE_FREQ_20（1m 成交量超过当日均量+3σ 的 bar 占比 20 日均值）。原子已存在于本地 intraday_volume_profile_1m 族（本线 S24 起多次复用）。pi 单原子审计 +50.7bp。",
     "expected_sign": 1},
    {"id": "S26A2", "operator": "atomic", "left": _BIGBAR_VOL_SHARE, "right": _BIGBAR_VOL_SHARE,
     "mechanism": "s26_reproduce_bigbar_vol_share_20",
     "hypothesis": "复现 pi 单原子 BIGBAR_VOL_SHARE_20（成交量最大 10% bar 的成交量占全日比例 20 日均值）。原子已存在于本地 bar_size_order_flow 族。pi 主控验证 +41.6bp/t2.26。",
     "expected_sign": 1},
    {"id": "S26A3", "operator": "atomic", "left": _BIGBAR_DIR_SKEW, "right": _BIGBAR_DIR_SKEW,
     "mechanism": "s26_reproduce_bigbar_dir_skew_20",
     "hypothesis": "复现 pi 单原子 BIGBAR_DIR_SKEW_20（大 bar 中收益为正的比例−0.5，20 日均值）。原子已存在于本地 bar_size_order_flow 族。",
     "expected_sign": 1},
    {"id": "S26A4", "operator": "atomic", "left": _VOL_AUTOCORR, "right": _VOL_AUTOCORR,
     "mechanism": "s26_reproduce_vol_autocorr_20",
     "hypothesis": "复现 pi 单原子 VOL_AUTOCORR_20（1m 成交量序列 1 阶自相关，日内估计，20 日均值）。原子已存在于本地 intraday_volume_profile_1m 族。",
     "expected_sign": 1},
    {"id": "S26A5", "operator": "atomic", "left": _LOG_AMOUNT_VOL, "right": _LOG_AMOUNT_VOL,
     "mechanism": "s26_reproduce_log_amount_vol_20",
     "hypothesis": "复现 pi 单原子 LOG_AMOUNT_VOL_20（log 日成交额的 20 日标准差）。原子已存在于本地 liquidity_variability 族。",
     "expected_sign": 1},
    # ---- 4 pair reproductions (原表达式，全部命中哈希碰撞) ----
    {"id": "S26Z2", "operator": "rank_spread", "left": _BIGBAR_DIR_SKEW, "right": _VOL_AUTOCORR,
     "mechanism": "s26_reproduce_z2",
     "hypothesis": "复现 pi Z2 = rank(BIGBAR_DIR_SKEW_20) - rank(VOL_AUTOCORR_20)。pi +49.2bp/t3.02。此组合已在本线共享历史 round_022 以完全相同表达式入选（t=3.56/+49.2bp），命中哈希碰撞——即为复现验证本身。",
     "expected_sign": 1},
    {"id": "S26CO36", "operator": "rank_spread", "left": _VT_AUTOCORR, "right": _VOL_SPIKE_FREQ,
     "mechanism": "s26_reproduce_co36",
     "hypothesis": "复现 pi CO36 = rank(VT_AUTOCORR_20) - rank(VOL_SPIKE_FREQ_20)。pi +47.7bp/t3.14。本线已在 S24 round_603（XB1）独立实现并入选（t=3.63/+45.4bp，与 pi 数字接近），命中哈希碰撞。",
     "expected_sign": 1},
    {"id": "S26BB1", "operator": "rank_spread", "left": _VOL_SPIKE_FREQ, "right": _ULCER_20,
     "mechanism": "s26_reproduce_bb1",
     "hypothesis": "复现 pi BB1 = rank(VOL_SPIKE_FREQ_20) - rank(ULCER_20)。pi +36.3bp/t2.46。此组合已在本线共享历史 round_027 以完全相同表达式入选（t=2.72/+36.3bp），命中哈希碰撞。",
     "expected_sign": 1},
    {"id": "S26AI4", "operator": "rank_spread", "left": _GAP_FILL_60, "right": _VOL_SPIKE_FREQ,
     "mechanism": "s26_reproduce_ai4",
     "hypothesis": "复现 pi AI4 = rank(GAP_FILL_FRACTION_60) - rank(VOL_SPIKE_FREQ_20)。pi +42.7bp/t2.58。此组合已在本线共享历史 round_060 以完全相同表达式入选（t=3.55/+42.7bp），命中哈希碰撞。",
     "expected_sign": 1},
]

if __name__ == "__main__":
    base.main()
