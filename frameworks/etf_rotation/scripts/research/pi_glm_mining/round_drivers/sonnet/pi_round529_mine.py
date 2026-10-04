#!/usr/bin/env python3
"""Round 529 driver: S4 stage step 11 -- jump_continuous_beta pairing, round 11.

Ten-round scoreboard (round_519-528, 163 candidates, 19 net admissions, no
three-zero streak; round_527/528 both landed 4/N, the stage's best rounds).
CONTINUOUS_BETA_60 has now been paired against nearly every catalog family.
This round does two things:

1. Opens the two remaining never-touched families: market_relative_strength
   (relative momentum vs the benchmark pool, tracking error -- a direct
   systematic-risk-adjacent construct never tried against any
   jump_continuous_beta leg) -- 5 atoms.

2. Closes out every atom within ALREADY-partially-used families that
   happened to be paired with a DIFFERENT jump_continuous_beta leg in an
   earlier round but never with CONTINUOUS_BETA_60 specifically: category_
   state's CATEGORY_MOM_5/20/60 (never used by this family at all -- the
   dispersion/breadth/drawdown/vol atoms from this family were used in
   round_521-523, but the plain momentum atoms were skipped), largebar_
   footprint_1m's LBAR_AMTSPLIT_20 (used with JUMP_BETA_STABILITY_20 in
   round_523, never with CONTINUOUS_BETA_60), intraday_volume_profile_1m's
   VOL_ENTROPY_20 (used with JUMP_BETA_STABILITY_20 in round_525),
   return_tail_shape's WORST_DAY_60 (never used at all by this family --
   WORST_DAY_20 was used in round_522), cost_distribution's OVERHAND_
   THICKNESS_60/CHIP_RANGE_90_60 (used with JUMP_BETA_STABILITY_20/BETA_
   GAP_20 in round_522, never with CONTINUOUS_BETA_60), liquidity_
   commonality_1m's RESILIENCY_20/IDIO_LIQ_SHOCK_Z_20 (used with JUMP_
   BETA_STABILITY_20 in round_522; LIQ_COMMON_BETA_20/R2_20 from the same
   family were used with CONTINUOUS_BETA_60 in round_527), cojump_1m's
   IDIO_JUMP_SHARE_20/COJUMP_DIR_AGREE_20 (used with JUMP_BETA_STABILITY_20
   in round_522; COJUMP_INDEX_SHARE_20 from the same family was used with
   CONTINUOUS_BETA_60 in round_527), gap_repair's GAP_FILL_FRACTION_60
   (used with JUMP_BETA_20/JUMP_BETA_STABILITY_20 in round_519; GAP_FILL_
   FRACTION_20 was used with CONTINUOUS_BETA_60 in round_522).

After this round, CONTINUOUS_BETA_60 will have been tested against every
atom in the local catalog except macro_hedge_sensitivity's GOLD/BOND_
PARTIAL_CORR (known data-availability gap from round_522, not retried
here). All (left,right) combos below are new. No same-family pairs, no
window variants."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_529"

_REL_MOM20 = {"name": "REL_MARKET_MOM_20", "source": "market_relative_strength"}
_REL_MOM60 = {"name": "REL_MARKET_MOM_60", "source": "market_relative_strength"}
_REL_MOM120 = {"name": "REL_MARKET_MOM_120", "source": "market_relative_strength"}
_TRACK_ERR20 = {"name": "TRACKING_ERROR_20", "source": "market_relative_strength"}
_TRACK_ERR60 = {"name": "TRACKING_ERROR_60", "source": "market_relative_strength"}

_CAT_MOM5 = {"name": "CATEGORY_MOM_5", "source": "category_state"}
_CAT_MOM20 = {"name": "CATEGORY_MOM_20", "source": "category_state"}
_CAT_MOM60 = {"name": "CATEGORY_MOM_60", "source": "category_state"}

_LBAR_AMTSPLIT = {"name": "LBAR_AMTSPLIT_20", "source": "largebar_footprint_1m"}
_VOL_ENTROPY = {"name": "VOL_ENTROPY_20", "source": "intraday_volume_profile_1m"}
_WORST_DAY60 = {"name": "WORST_DAY_60", "source": "return_tail_shape"}
_OVERHANG60 = {"name": "OVERHAND_THICKNESS_60", "source": "cost_distribution"}
_CHIP_RANGE = {"name": "CHIP_RANGE_90_60", "source": "cost_distribution"}
_RESILIENCY = {"name": "RESILIENCY_20", "source": "liquidity_commonality_1m"}
_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_IDIO_JUMP_SHARE = {"name": "IDIO_JUMP_SHARE_20", "source": "cojump_1m"}
_COJUMP_DIR_AGREE = {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}

_CBETA60 = {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"}

base.CANDIDATES = [
    # ---- market_relative_strength: never touched by this family ----
    {
        "id": "LF1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _REL_MOM20,
        "mechanism": "continuous_beta60_confirmed_by_relative_market_momentum_20",
        "hypothesis": "A=连续分量beta，60日窗（10轮19次净入选的核心腿）。B=相对基准篮子动量，20日（market_relative_strength，本族首次使用）。假设：常态系统性暴露高(A高)且相对基准动量强(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "LF2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _REL_MOM60,
        "mechanism": "continuous_beta60_confirmed_by_relative_market_momentum_60",
        "hypothesis": "A=同上。B=60日版本（同上，与A同窗对齐）。假设：同LF1，同窗对齐。",
        "expected_sign": 1,
    },
    {
        "id": "LF3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _REL_MOM120,
        "mechanism": "continuous_beta60_confirmed_by_relative_market_momentum_120",
        "hypothesis": "A=同上。B=120日版本（同上，更长窗）。假设：同LF1，更长期是否更稳健。",
        "expected_sign": 1,
    },
    {
        "id": "LF4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _TRACK_ERR20,
        "mechanism": "continuous_beta60_confirmed_by_tracking_error_20",
        "hypothesis": "A=同上。B=相对基准跟踪误差，20日（market_relative_strength，本族首次使用）。假设：常态系统性暴露高(A高)且跟踪误差低(B低，紧跟基准)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "LF5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _TRACK_ERR60,
        "mechanism": "continuous_beta60_confirmed_by_tracking_error_60",
        "hypothesis": "A=同上。B=60日版本（同上）。假设：同LF4。",
        "expected_sign": 1,
    },
    # ---- category_state's never-used momentum atoms ----
    {
        "id": "LG1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CAT_MOM5,
        "mechanism": "continuous_beta60_confirmed_by_category_momentum_5",
        "hypothesis": "A=同上。B=板块5日动量（category_state，本族首次使用该原子；此前只用过该家族的离散度/广度/回撤/波动率原子）。假设：常态系统性暴露高(A高)且板块短期动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LG2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CAT_MOM20,
        "mechanism": "continuous_beta60_confirmed_by_category_momentum_20",
        "hypothesis": "A=同上。B=板块20日动量（同上）。假设：同LG1。",
        "expected_sign": 1,
    },
    {
        "id": "LG3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CAT_MOM60,
        "mechanism": "continuous_beta60_confirmed_by_category_momentum_60",
        "hypothesis": "A=同上。B=板块60日动量（同上，与A同窗对齐）。假设：同LG1，同窗对齐。",
        "expected_sign": 1,
    },
    # ---- last never-paired-with-CBETA60 atoms from already-partially-used
    # families (each was previously paired with a different leg only) ----
    {
        "id": "LH1",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _LBAR_AMTSPLIT,
        "mechanism": "continuous_beta60_confirmed_by_bigbar_amount_split",
        "hypothesis": "A=同上。B=大bar成交额分割结构（largebar_footprint_1m，此前只与JUMP_BETA_STABILITY_20配过[round_523 KO1,未过]，对本腿首次配对）。假设：常态系统性暴露高(A高)且大bar成交额分割异常(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LH2",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _VOL_ENTROPY,
        "mechanism": "continuous_beta60_confirmed_by_volume_entropy",
        "hypothesis": "A=同上。B=日内成交量分布熵（intraday_volume_profile_1m，此前只与JUMP_BETA_STABILITY_20配过[round_525 KO2,未过]，对本腿首次配对）。假设：常态系统性暴露高(A高)且成交量分布熵低(B低，集中而非分散)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LH3",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _WORST_DAY60,
        "mechanism": "continuous_beta60_confirmed_by_worst_day_60",
        "hypothesis": "A=同上。B=60日最差单日收益（return_tail_shape，同族的WORST_DAY_20曾与CONTINUOUS_BETA_60配过[round_522 KE5,未过]，本条是60日版本，与A同窗对齐，首次配对）。假设：常态系统性暴露高(A高)且60日最差单日较浅(B高，下尾较浅)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LH4",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _OVERHANG60,
        "mechanism": "continuous_beta60_confirmed_by_overhang_thickness",
        "hypothesis": "A=同上。B=套牢盘厚度（cost_distribution，此前只与JUMP_BETA_STABILITY_20配过[round_522 KJ7,未过]，对本腿首次配对）。假设：常态系统性暴露高(A高)且套牢盘薄(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LH5",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _CHIP_RANGE,
        "mechanism": "continuous_beta60_confirmed_by_chip_range",
        "hypothesis": "A=同上。B=90分位筹码分布宽度（cost_distribution，此前只与BETA_GAP_20配过[round_522 KM2,未过]，对本腿首次配对）。假设：常态系统性暴露高(A高)且筹码分布窄(B低，持仓集中)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LH6",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _RESILIENCY,
        "mechanism": "continuous_beta60_confirmed_by_liquidity_resiliency",
        "hypothesis": "A=同上。B=流动性恢复力（liquidity_commonality_1m，此前只与JUMP_BETA_STABILITY_20配过[round_522 KJ5,未过]；同族的LIQ_COMMON_BETA_20/R2_20已与本腿配过[round_527，未过]，此原子对本腿首次配对）。假设：常态系统性暴露高(A高)且流动性恢复力强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LH7",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "continuous_beta60_confirmed_by_idio_liquidity_shock",
        "hypothesis": "A=同上。B=特异流动性冲击z值（liquidity_commonality_1m，此前只与JUMP_BETA_STABILITY_20配过[round_522 KJ4,未过]，对本腿首次配对）。假设：常态系统性暴露高(A高)且特异流动性冲击小(B低)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LH8",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _IDIO_JUMP_SHARE,
        "mechanism": "continuous_beta60_confirmed_by_idio_jump_share",
        "hypothesis": "A=同上。B=特异跳跃占比（cojump_1m，此前只与JUMP_BETA_STABILITY_20配过[round_522 KJ2,未过]；同族的COJUMP_INDEX_SHARE_20已与本腿配过[round_527，未过]，此原子对本腿首次配对）。假设：常态系统性暴露高(A高)且特异跳跃占比低(B低，跳跃以共振为主)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LH9",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _COJUMP_DIR_AGREE,
        "mechanism": "continuous_beta60_confirmed_by_cojump_dir_agree",
        "hypothesis": "A=同上。B=共跳方向一致性（cojump_1m，此前只与JUMP_BETA_STABILITY_20配过[round_522 KJ3,未过]，对本腿首次配对）。假设：常态系统性暴露高(A高)且共跳方向一致性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "LH10",
        "operator": "rank_spread",
        "left": _CBETA60,
        "right": _GAP_FILL60,
        "mechanism": "continuous_beta60_confirmed_by_gap_fill_fraction_60",
        "hypothesis": "A=同上。B=60日窗缺口回补比例（gap_repair，此前只与JUMP_BETA_20/JUMP_BETA_STABILITY_20配过[round_519，均未过]；同族的GAP_FILL_FRACTION_20已与本腿配过[round_522 KG5,未过]，此原子首次对本腿配对）。假设：常态系统性暴露高(A高)且长窗缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
