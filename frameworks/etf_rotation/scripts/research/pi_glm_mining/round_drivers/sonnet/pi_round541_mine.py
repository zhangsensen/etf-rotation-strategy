#!/usr/bin/env python3
"""Round 541 driver: S6 stage step 1 -- permutation_entropy_1m family
(Bandt-Pompe 2002 ordinal-pattern entropy; Rosso et al. 2007 statistical
complexity; Zunino-Zanin-Tabak-Perez-Rosso 2010 complexity-entropy
causality plane), main controller's pre-specified S6 direction after
S10's closure.

Atom health (round_541_atom_health): no shadow atoms (max shelf corr
0.11-0.40 across all 8) -- this family is genuinely novel relative to the
existing shelf/channel atoms, unlike every prior stage's family which had
at least one shadow-flagged atom. PERM_ENTROPY_RET_20 has the strongest
non-trivial audit IC (-0.078, the core Bandt-Pompe measure) and is chosen
as this round's sole left leg for the first pairing batch, per the
pairing-discipline rule (one batch of <=8, right legs all cross-family)."""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as base  # noqa: E402

base.ROUND_ID = "round_541"

_OPEN30 = {"name": "OPEN30_VOL_SHARE_20", "source": "intraday_volume_profile_1m"}
_VOL_SPIKE = {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}
_CATEGORY_VOL = {"name": "CATEGORY_VOL_20", "source": "category_state"}
_GAP_FILL60 = {"name": "GAP_FILL_FRACTION_60", "source": "gap_repair"}
_LOG_AMT = {"name": "LOG_AMOUNT_VOL_20", "source": "liquidity_variability"}
_BIGBAR_DIR_SKEW = {"name": "BIGBAR_DIR_SKEW_20", "source": "bar_size_order_flow"}
_PEER_OU_HALFLIFE = {"name": "PEER_OU_HALFLIFE_20", "source": "peer_relative_value"}
_DEP_DRIFT = {"name": "DEP_DRIFT_20", "source": "cross_dependence_1m"}

base.CANDIDATES = [
    # ---- 8 atomic: new permutation_entropy_1m atoms ----
    {
        "id": "PA1",
        "operator": "atomic",
        "left": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
        "right": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
        "mechanism": "perm_entropy_ret_20",
        "hypothesis": "Bandt-Pompe 2002 排列熵（嵌入维3），1m收益序型复杂度，20日均值。体检：disc-0.0922/579天/审计-0.0777，max|corr|=0.35，非shadow（本族无shadow原子，全新信息面）。假设：排列熵高(A高，序列更接近随机)=价格发现效率高，可预测性弱，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "PA2",
        "operator": "atomic",
        "left": {"name": "STAT_COMPLEXITY_20", "source": "permutation_entropy_1m"},
        "right": {"name": "STAT_COMPLEXITY_20", "source": "permutation_entropy_1m"},
        "mechanism": "stat_complexity_20",
        "hypothesis": "Rosso et al. 2007 统计复杂度C_JS，20日均值。体检：disc+0.0944/审计+0.0676，max|corr|=0.40，非shadow。假设：统计复杂度高(A高，处于噪声与确定性之间的结构化状态)=存在可利用的中等复杂度结构，延续。",
        "expected_sign": 1,
    },
    {
        "id": "PA3",
        "operator": "atomic",
        "left": {"name": "CEP_DISTANCE_20", "source": "permutation_entropy_1m"},
        "right": {"name": "CEP_DISTANCE_20", "source": "permutation_entropy_1m"},
        "mechanism": "cep_distance_20",
        "hypothesis": "Zunino-Zanin-Tabak-Perez-Rosso 2010 复杂度-熵平面到白噪声点(1,0)的欧氏距离，20日均值。体检：disc+0.0932/审计+0.0746，max|corr|=0.40，非shadow。假设：距离白噪声点越远(A高)=市场无效率程度越高，延续。",
        "expected_sign": 1,
    },
    {
        "id": "PA4",
        "operator": "atomic",
        "left": {"name": "PERM_ENTROPY_VOL_20", "source": "permutation_entropy_1m"},
        "right": {"name": "PERM_ENTROPY_VOL_20", "source": "permutation_entropy_1m"},
        "mechanism": "perm_entropy_vol_20",
        "hypothesis": "1m成交量序列的排列熵（到达规律性），20日均值。体检：disc-0.0425/审计-0.0321，max|corr|=0.26，非shadow。假设：成交量到达序型熵高(A高，到达模式随机)=延续，符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PA5",
        "operator": "atomic",
        "left": {"name": "ENTROPY_RET_VOL_DIFF_20", "source": "permutation_entropy_1m"},
        "right": {"name": "ENTROPY_RET_VOL_DIFF_20", "source": "permutation_entropy_1m"},
        "mechanism": "entropy_ret_vol_diff_20",
        "hypothesis": "收益排列熵与成交量排列熵之差，20日均值。体检：disc-0.1012/审计-0.0728（本族非shadow原子里发现期IC绝对值最大），max|corr|=0.35，非shadow。假设：收益比成交量更随机(A高，收益熵超过成交量熵)=成交量携带的结构信息比价格更多，rank与未来收益负相关。",
        "expected_sign": -1,
    },
    {
        "id": "PA6",
        "operator": "atomic",
        "left": {"name": "PERM_ENTROPY_RET_CHG_20", "source": "permutation_entropy_1m"},
        "right": {"name": "PERM_ENTROPY_RET_CHG_20", "source": "permutation_entropy_1m"},
        "mechanism": "perm_entropy_ret_change_20",
        "hypothesis": "收益排列熵的20日变化（效率regime切换）。体检：disc-0.0206/审计+0.0102，max|corr|=0.22，非shadow。假设：排列熵正在上升(A高，效率正在提高)=延续，符号按discovery定。",
        "expected_sign": -1,
    },
    {
        "id": "PA7",
        "operator": "atomic",
        "left": {"name": "STAT_COMPLEXITY_CHG_20", "source": "permutation_entropy_1m"},
        "right": {"name": "STAT_COMPLEXITY_CHG_20", "source": "permutation_entropy_1m"},
        "mechanism": "stat_complexity_change_20",
        "hypothesis": "统计复杂度的20日变化。体检：disc+0.0203/审计-0.0161，max|corr|=0.11，非shadow。假设：统计复杂度正在上升(A高)=结构化程度增强，符号按discovery定。",
        "expected_sign": 1,
    },
    {
        "id": "PA8",
        "operator": "atomic",
        "left": {"name": "PERM_ENTROPY_VOL_CHG_20", "source": "permutation_entropy_1m"},
        "right": {"name": "PERM_ENTROPY_VOL_CHG_20", "source": "permutation_entropy_1m"},
        "mechanism": "perm_entropy_vol_change_20",
        "hypothesis": "成交量排列熵的20日变化。体检：disc-0.0205/审计-0.0244，max|corr|=0.18，非shadow。假设：成交量到达模式正在随机化(A高)=延续，符号按discovery定。",
        "expected_sign": -1,
    },
    # ---- first pairing batch: PERM_ENTROPY_RET_20 as sole left leg this
    # stage (strongest core Bandt-Pompe atom-health audit IC), <=8
    # partners, per the pairing-discipline rule ----
    {
        "id": "PB1",
        "operator": "rank_spread",
        "left": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
        "right": _OPEN30,
        "mechanism": "perm_entropy_ret_confirmed_by_open30_vol_share",
        "hypothesis": "A=1m收益排列熵（体检审计-0.0777，本族核心原子）。B=开盘30分钟成交占比（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：排列熵高(A高，接近随机)且开盘集中放量(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB2",
        "operator": "rank_spread",
        "left": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
        "right": _VOL_SPIKE,
        "mechanism": "perm_entropy_ret_confirmed_by_volume_spike_freq",
        "hypothesis": "A=同上。B=成交量脉冲频率（intraday_volume_profile_1m，本线历史最强confirming partner之一）。假设：排列熵高(A高)且脉冲放量频繁(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB3",
        "operator": "rank_spread",
        "left": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
        "right": _CATEGORY_VOL,
        "mechanism": "perm_entropy_ret_confirmed_by_category_vol",
        "hypothesis": "A=同上。B=同类别板块波动率（category_state，round_053门7全过史）。假设：排列熵高(A高)且所属板块高波动(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB4",
        "operator": "rank_spread",
        "left": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
        "right": _GAP_FILL60,
        "mechanism": "perm_entropy_ret_confirmed_by_gap_absorption",
        "hypothesis": "A=同上。B=60日窗缺口回补比例（gap_repair，round_053门7全过史）。假设：排列熵高(A高)且缺口易回补(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB5",
        "operator": "rank_spread",
        "left": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
        "right": _LOG_AMT,
        "mechanism": "perm_entropy_ret_confirmed_by_high_activity",
        "hypothesis": "A=同上。B=对数成交额（liquidity_variability，本线历史最强单腿之一）。假设：排列熵高(A高)且整体活跃度高(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB6",
        "operator": "rank_spread",
        "left": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
        "right": _BIGBAR_DIR_SKEW,
        "mechanism": "perm_entropy_ret_confirmed_by_bigbar_dir_skew",
        "hypothesis": "A=同上。B=大bar方向偏斜（bar_size_order_flow，S4阶段CONTINUOUS_BETA_60最强confirming partner之一，t=3.48）。假设：排列熵高(A高)且大bar方向持续偏向一侧(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB7",
        "operator": "rank_spread",
        "left": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
        "right": _PEER_OU_HALFLIFE,
        "mechanism": "perm_entropy_ret_confirmed_by_peer_ou_halflife",
        "hypothesis": "A=同上。B=同伴OU回归半衰期（peer_relative_value，S4阶段本线最高命中率家族，t=3.75）。假设：排列熵高(A高)且相对同伴回复速度慢(B高)=延续。",
        "expected_sign": 1,
    },
    {
        "id": "PB8",
        "operator": "rank_spread",
        "left": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
        "right": _DEP_DRIFT,
        "mechanism": "perm_entropy_ret_confirmed_by_dependency_drift",
        "hypothesis": "A=同上。B=依赖结构20日漂移（cross_dependence_1m，S10阶段MFI_EXTREME_FRAC_20最强命中partner，t=4.88）。假设：排列熵高(A高)且依赖结构正在漂移(B方向按discovery定)=延续。",
        "expected_sign": 1,
    },
]

if __name__ == "__main__":
    base.main()
