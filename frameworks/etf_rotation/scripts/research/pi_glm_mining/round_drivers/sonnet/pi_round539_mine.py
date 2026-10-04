#!/usr/bin/env python3
"""Round 539 driver: S10 stage step 4 -- accumulation_distribution_1m
pairing, round 4 (final legal round for this family). Opens the last two
unpaired atoms: OBV_SLOPE_20 (shadow vs bar_size_order_flow:
TICK_IMBALANCE_20, 0.78) and MFI_EXTREME_FRAC_20 (shadow vs
bar_size_order_flow:BIGBAR_VOL_SHARE_20, 0.86). Per the S4/S5 precedent
(JB2, NOISE_VAR_20's MH3), atom-health shadow status does not preclude
testing since the official dedup gate only checks shelf16+prior-admitted.

Partner theme avoids the specific atoms each is shadow against (no
TICK_IMBALANCE_20/BIGBAR_VOL_SHARE_20 partners here) and draws from
liquidity-impact, tail-shape, cross-dependence, and jump/realized-measure
families not yet used as confirming partners for this family's flow/OBV/
MFI atoms.

After this round, all 8 accumulation_distribution_1m atoms will have used
their one legal pairing batch -- no legal candidates remain for this
family regardless of outcome."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_539"

_KYLE_LAMBDA = {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"}
_ROLL_SPREAD_DAILY = {"name": "ROLL_SPREAD_20", "source": "microstructure_1m"}
_WORST_DAY60 = {"name": "WORST_DAY_60", "source": "return_tail_shape"}
_CAT_MOM20 = {"name": "CATEGORY_MOM_20", "source": "category_state"}
_TAILQ10_20 = {"name": "TAIL_Q10_20", "source": "return_tail_shape"}
_SHARE_CHG20 = {"name": "SHARE_CHG_20", "source": "fund_flow"}
_PREMIUM_Z20 = {"name": "PREMIUM_Z_20", "source": "nav_premium"}
_HKS_SLOT = {"name": "HKS_SLOT_PERSIST_20", "source": "intraday_periodicity"}

_VOL_USHAPE20 = {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"}
_JV_RV_SHARE = {"name": "JV_RV_SHARE_20", "source": "realized_measures_1m"}
_BPV_RV_RATIO = {"name": "BPV_RV_RATIO_20", "source": "realized_measures_1m"}
_COJUMP_DIR_AGREE = {"name": "COJUMP_DIR_AGREE_20", "source": "cojump_1m"}
_IDIO_LIQ_SHOCK = {"name": "IDIO_LIQ_SHOCK_Z_20", "source": "liquidity_commonality_1m"}
_OVERNIGHT_DIFF = {"name": "OVERNIGHT_INTRA_DIFF_20", "source": "intraday_periodicity"}
_TAIL30_BETA_FULL = {"name": "TAIL30_BETA_FULL_20", "source": "intraday_periodicity"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}

_OBV_SLOPE = {"name": "OBV_SLOPE_20", "source": "accumulation_distribution_1m"}
_MFI_EXTREME = {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}

base.CANDIDATES = [
    # ---- OBV_SLOPE_20 (shadow vs TICK_IMBALANCE_20; avoid that theme,
    # use liquidity-impact/tail/flow/premium partners instead) ----
    {
        "id": "NH1",
        "operator": "rank_spread",
        "left": _OBV_SLOPE,
        "right": _KYLE_LAMBDA,
        "mechanism": "obv_slope_confirmed_by_kyle_lambda",
        "hypothesis": "A=OBV日内斜率水平（Granville 1963，atom-health shadow=True vs bar_size_order_flow:TICK_IMBALANCE_20，官方去重不预先排除）。B=Kyle价格冲击系数（microstructure_1m，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：OBV斜率高(A高，买盘压力大)且价格冲击系数高(B高，流动性薄)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "NH2",
        "operator": "rank_spread",
        "left": _OBV_SLOPE,
        "right": _ROLL_SPREAD_DAILY,
        "mechanism": "obv_slope_confirmed_by_daily_roll_spread",
        "hypothesis": "A=同上。B=日频Roll隐含价差（microstructure_1m，本族首次配对，与S5阶段MH3类似的跨频率交叉验证）。假设：OBV斜率高(A高)且日频隐含价差大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NH3",
        "operator": "rank_spread",
        "left": _OBV_SLOPE,
        "right": _WORST_DAY60,
        "mechanism": "obv_slope_confirmed_by_worst_day_60",
        "hypothesis": "A=同上。B=60日最差单日收益（return_tail_shape，本族首次配对）。假设：OBV斜率高(A高)且下行尾更极端(B更负)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "NH4",
        "operator": "rank_spread",
        "left": _OBV_SLOPE,
        "right": _CAT_MOM20,
        "mechanism": "obv_slope_confirmed_by_category_momentum_20",
        "hypothesis": "A=同上。B=板块20日动量（category_state，本族首次配对）。假设：OBV斜率高(A高)且板块动量强(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NH5",
        "operator": "rank_spread",
        "left": _OBV_SLOPE,
        "right": _TAILQ10_20,
        "mechanism": "obv_slope_confirmed_by_tail_q10_20",
        "hypothesis": "A=同上。B=20日收益分布10%分位数（return_tail_shape，本族首次配对）。假设：OBV斜率高(A高)且下尾更浅(B高)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "NH6",
        "operator": "rank_spread",
        "left": _OBV_SLOPE,
        "right": _SHARE_CHG20,
        "mechanism": "obv_slope_confirmed_by_share_change_20",
        "hypothesis": "A=同上。B=基金份额20日变化（fund_flow，本族首次配对）。假设：OBV斜率高(A高)且份额扩张(B高，资金净申购)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NH7",
        "operator": "rank_spread",
        "left": _OBV_SLOPE,
        "right": _PREMIUM_Z20,
        "mechanism": "obv_slope_confirmed_by_premium_z_20",
        "hypothesis": "A=同上。B=净值溢价20日z值（nav_premium，本族首次配对）。假设：OBV斜率高(A高)且溢价异常走高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NH8",
        "operator": "rank_spread",
        "left": _OBV_SLOPE,
        "right": _HKS_SLOT,
        "mechanism": "obv_slope_confirmed_by_hks_slot_persistence",
        "hypothesis": "A=同上。B=日内时段模式持续性（intraday_periodicity，S4阶段CONTINUOUS_BETA_60命中partner，本族首次配对）。假设：OBV斜率高(A高)且日内时段模式稳定(B高)=延续。",
        "expected_sign": 1,
    },
    # ---- MFI_EXTREME_FRAC_20 (shadow vs BIGBAR_VOL_SHARE_20; avoid that
    # theme, use jump/realized-measure/dependency partners instead) ----
    {
        "id": "NI1",
        "operator": "rank_spread",
        "left": _MFI_EXTREME,
        "right": _VOL_USHAPE20,
        "mechanism": "mfi_extreme_confirmed_by_vol_ushape",
        "hypothesis": "A=MFI超买超卖频率水平（Quong-Soudack 1989，atom-health shadow=True vs bar_size_order_flow:BIGBAR_VOL_SHARE_20，官方去重不预先排除）。B=日内成交量U型强度（realized_measures_1m，round_053门7已admitted的独立原子，本族首次配对）。假设：MFI极端频率高(A高)且U型强度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NI2",
        "operator": "rank_spread",
        "left": _MFI_EXTREME,
        "right": _JV_RV_SHARE,
        "mechanism": "mfi_extreme_confirmed_by_jump_variation_share",
        "hypothesis": "A=同上。B=跳跃变差占已实现方差比例（realized_measures_1m，本族首次配对）。假设：MFI极端频率高(A高)且自身跳跃占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NI3",
        "operator": "rank_spread",
        "left": _MFI_EXTREME,
        "right": _BPV_RV_RATIO,
        "mechanism": "mfi_extreme_confirmed_by_bpv_rv_ratio",
        "hypothesis": "A=同上。B=双幂变差/已实现方差比（realized_measures_1m，本族首次配对）。假设：MFI极端频率高(A高)且自身收益连续分量占比低(B低)=延续；符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "NI4",
        "operator": "rank_spread",
        "left": _MFI_EXTREME,
        "right": _COJUMP_DIR_AGREE,
        "mechanism": "mfi_extreme_confirmed_by_cojump_dir_agree",
        "hypothesis": "A=同上。B=共跳方向一致性（cojump_1m，本族首次配对）。假设：MFI极端频率高(A高)且共跳方向一致性高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NI5",
        "operator": "rank_spread",
        "left": _MFI_EXTREME,
        "right": _IDIO_LIQ_SHOCK,
        "mechanism": "mfi_extreme_confirmed_by_idio_liquidity_shock",
        "hypothesis": "A=同上。B=特异流动性冲击z值（liquidity_commonality_1m，本族首次配对）。假设：MFI极端频率高(A高)且特异流动性冲击大(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NI6",
        "operator": "rank_spread",
        "left": _MFI_EXTREME,
        "right": _OVERNIGHT_DIFF,
        "mechanism": "mfi_extreme_confirmed_by_overnight_intra_diff",
        "hypothesis": "A=同上。B=隔夜与日内收益差异（intraday_periodicity，本族首次配对）。假设：MFI极端频率高(A高)且隔夜/日内收益分化明显(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NI7",
        "operator": "rank_spread",
        "left": _MFI_EXTREME,
        "right": _TAIL30_BETA_FULL,
        "mechanism": "mfi_extreme_confirmed_by_tail30_beta_full",
        "hypothesis": "A=同上。B=尾盘30分钟beta相对全天beta的比值（intraday_periodicity，本族首次配对）。假设：MFI极端频率高(A高)且尾盘beta占比高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "NI8",
        "operator": "rank_spread",
        "left": _MFI_EXTREME,
        "right": _DEP_DRIFT,
        "mechanism": "mfi_extreme_confirmed_by_dependency_drift",
        "hypothesis": "A=同上。B=依赖结构20日漂移（cross_dependence_1m，本族首次配对）。假设：MFI极端频率高(A高)且依赖结构正在漂移(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
