#!/usr/bin/env python3
"""Round 633 driver: S34 stage (main controller directive, 2026-09-21) --
robustness profile, report-only, no gate/criteria/weight/combination
changes. No new preregistration (n_preregistered=0). Profiles the 15
cluster-representative admitted candidates from this line's history,
disambiguated from round-local non-unique IDs via gate_pass=True filter
against each candidate's original PLAN.json.

Reuses the engine's own atom-building and expression-materialization
path (pi_round002_mine._build_atoms + etf_factor_grammar.materialize_
expression) so the exact same cached atom parquet files and rank
definitions are used -- no re-derivation, no re-gating.

Computes, per candidate:
1. K in {2,4} (H=5 fixed) and H in {10,20} (K=3 fixed) audit excess_bp
   + 5-session block-t, generalizing _topk_referee's hardcoded k=3/h=5.
2. Yearly (2021-2025) excess_bp + block-t at K=3/H=5, over the full
   available date range (not just the audit window); two custom
   sub-periods (2024-01-2024-08, 2024-09-2025-04).
3. Top-3 holdings day-over-day turnover proxy: mean size of the
   intersection between today's top-3 and the previous session's
   top-3 (K=3/H=5 mask), over the full available date range.
4. Full pairwise rank-correlation matrix among the 15 candidates'
   RAW (direction-unadjusted) signals, via the engine's own
   _stride_vector (discovery window, stride=5) + _pairwise_pearson --
   identical method to the dedup gate.

No gate/criteria/weight/combination conclusion is drawn here; only
numbers are reported, per the S34 directive."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as eng  # noqa: E402
from etf_strategy.core.etf_factor_grammar import ExpressionSpec, materialize_expression  # noqa: E402
from etf_strategy.core.etf_family_referee import block_means  # noqa: E402

ROUND_ID = "round_633"
OUT = eng.WORKSPACE_OUTPUTS / ROUND_ID
OUT.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    {"id": "S27B5", "round": "round_614", "operator": "rank_spread", "direction": -1.0,
     "left": {"name": "GAP_DD_CONSUMPTION_RATIO_20", "source": "overnight_intraday_mismatch_v1"},
     "right": {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}},
    {"id": "S29P10", "round": "round_625", "operator": "rank_spread", "direction": -1.0,
     "left": {"name": "REL_UNDERWATER_CATEGORY_20", "source": "mechanism_atoms_v2"},
     "right": {"name": "R_LOG_AMOUNT_VOL_20", "source": "repl_volume_core_a"}},
    {"id": "S29Q1", "round": "round_626", "operator": "rank_spread", "direction": -1.0,
     "left": {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"},
     "right": {"name": "MFI_EXTREME_UNDERWATER_SKEW_20", "source": "mechanism_atoms_v2"}},
    {"id": "UE3", "round": "round_575", "operator": "rank_spread", "direction": 1.0,
     "left": {"name": "YZ_OVERNIGHT_SHARE_20", "source": "range_based_vol_1m"},
     "right": {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}},
    {"id": "HB1", "round": "round_592", "operator": "rank_spread", "direction": 1.0,
     "left": {"name": "ON_SIGN_STREAK_20", "source": "overnight_structure_1d"},
     "right": {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}},
    {"id": "PA1", "round": "round_541", "operator": "atomic", "direction": -1.0,
     "left": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"},
     "right": {"name": "PERM_ENTROPY_RET_20", "source": "permutation_entropy_1m"}},
    {"id": "QA8", "round": "round_545", "operator": "atomic", "direction": -1.0,
     "left": {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"},
     "right": {"name": "UNDERWATER_FRAC_CHG_20", "source": "intraday_drawdown_1m"}},
    {"id": "WA1", "round": "round_601", "operator": "rank_spread", "direction": -1.0,
     "left": {"name": "VT_UNDERWATER_FRAC_20", "source": "volume_time_drawdown"},
     "right": {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"}},
    {"id": "XC5", "round": "round_603", "operator": "rank_spread", "direction": 1.0,
     "left": {"name": "VT_BUCKET_COUNT_SHIFT_20", "source": "volume_time_1m"},
     "right": {"name": "BEST_DAY_20", "source": "upside_tail"}},
    {"id": "XB1", "round": "round_603", "operator": "rank_spread", "direction": -1.0,
     "left": {"name": "VT_AUTOCORR_20", "source": "volume_time_1m"},
     "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}},
    {"id": "VA3", "round": "round_506", "operator": "rank_spread", "direction": -1.0,
     "left": {"name": "BEST_DAY_60_XVOL", "source": "upside_tail"},
     "right": {"name": "VOL_SPIKE_FREQ_20", "source": "intraday_volume_profile_1m"}},
    {"id": "NI1", "round": "round_539", "operator": "rank_spread", "direction": 1.0,
     "left": {"name": "MFI_EXTREME_FRAC_20", "source": "accumulation_distribution_1m"},
     "right": {"name": "VOL_USHAPE_20", "source": "realized_measures_1m"}},
    {"id": "KU2", "round": "round_526", "operator": "rank_spread", "direction": -1.0,
     "left": {"name": "CONTINUOUS_BETA_60", "source": "jump_continuous_beta"},
     "right": {"name": "KYLE_LAMBDA_20", "source": "microstructure_1m"}},
    {"id": "MH3", "round": "round_534", "operator": "rank_spread", "direction": -1.0,
     "left": {"name": "NOISE_VAR_20", "source": "microstructure_noise_1m"},
     "right": {"name": "ROLL_SPREAD_20", "source": "microstructure_1m"}},
    {"id": "LB7", "round": "round_597", "operator": "rank_spread", "direction": 1.0,
     "left": {"name": "LUNCH_POST_RUN_20", "source": "lunch_break_1m"},
     "right": {"name": "BEST_DAY_20", "source": "upside_tail"}},
]

SUBPERIODS = [
    ("2024H1_ext", "2024-01-01", "2024-08-31"),
    ("2024H2_2025Q1", "2024-09-01", "2025-04-30"),
]
YEARS = [2021, 2022, 2023, 2024, 2025]


def block_t(series: pd.Series, block: int = 5) -> float:
    if series is None or series.empty:
        return float("nan")
    blocks = block_means(series.to_frame("x"), block)["x"].dropna()
    if len(blocks) <= 3:
        return float("nan")
    denom = blocks.std(ddof=1) / np.sqrt(len(blocks))
    if not np.isfinite(denom) or denom == 0:
        return float("nan")
    return float(blocks.mean() / denom)


def excess_and_topmask(signal, direction, forward_h, eligibility, k):
    sig = (signal * direction).where(eligibility)
    f = forward_h.where(eligibility)
    valid = sig.notna() & f.notna()
    sig, f = sig.where(valid), f.where(valid)
    n = valid.sum(axis=1)
    ok = n >= max(eng.MIN_PAIRS, k + 1)
    top_mask = (sig.rank(axis=1, ascending=False, method="first") <= k) & ok.to_numpy()[:, None]
    top_ret = f.where(top_mask).mean(axis=1).where(ok)
    ew_ret = f.mean(axis=1).where(ok)
    excess = (top_ret - ew_ret)
    return excess, top_mask


def window_stats(excess: pd.Series, start=None, end=None) -> tuple[float, float, int]:
    s = excess.dropna()
    if start is not None:
        s = s.loc[s.index >= pd.Timestamp(start)]
    if end is not None:
        s = s.loc[s.index <= pd.Timestamp(end)]
    if s.empty:
        return float("nan"), float("nan"), 0
    return float(s.mean() * 1e4), block_t(s), int(len(s))


def turnover_proxy(top_mask: pd.DataFrame) -> tuple[float, int]:
    rows = top_mask.index
    sizes = []
    prev_set = None
    for date in rows:
        row = top_mask.loc[date]
        if not row.any():
            prev_set = None
            continue
        cur_set = set(row.index[row.to_numpy()])
        if prev_set is not None:
            sizes.append(len(cur_set & prev_set))
        prev_set = cur_set
    if not sizes:
        return float("nan"), 0
    return float(np.mean(sizes)), len(sizes)


def main() -> None:
    eng.load_builtin_families()
    panels, eligibility_all, symbols, forward = eng._load_context()
    eligibility = eligibility_all[symbols]

    plan_stub = {"candidates": CANDIDATES}
    ranked = eng._build_atoms(panels, eligibility_all, symbols, plan_stub)

    signals: dict[str, pd.DataFrame] = {}
    for cand in CANDIDATES:
        op = cand["operator"]
        spec = ExpressionSpec(op, cand["left"]["name"], None if op == "atomic" else cand["right"]["name"])
        signals[cand["id"]] = materialize_expression(spec, ranked)

    profile_rows = []
    md_sections = []

    for cand in CANDIDATES:
        cid = cand["id"]
        direction = float(cand["direction"])
        signal = signals[cid]
        row: dict[str, object] = {"candidate_id": cid, "source_round": cand["round"],
                                   "operator": cand["operator"], "direction": direction,
                                   "left": cand["left"]["name"], "right": cand["right"]["name"]}

        # --- primary K=3/H=5 excess series (full available range) ---
        excess_k3h5, top_mask_k3h5 = excess_and_topmask(signal, direction, forward[5], eligibility, 3)

        # 1a. K variants (H=5 fixed)
        for k in (2, 4):
            exc, _ = excess_and_topmask(signal, direction, forward[5], eligibility, k)
            bp, t, n = window_stats(exc, eng.AUDIT_START, eng.AUDIT_END)
            row[f"k{k}_h5_audit_excess_bp"] = bp
            row[f"k{k}_h5_audit_block_t"] = t
            row[f"k{k}_h5_audit_n"] = n

        # 1b. H variants (K=3 fixed)
        for h in (10, 20):
            exc, _ = excess_and_topmask(signal, direction, forward[h], eligibility, 3)
            bp, t, n = window_stats(exc, eng.AUDIT_START, eng.AUDIT_END)
            row[f"k3_h{h}_audit_excess_bp"] = bp
            row[f"k3_h{h}_audit_block_t"] = t
            row[f"k3_h{h}_audit_n"] = n

        # reference: primary K=3/H=5 audit stats (for comparison against variants)
        bp0, t0, n0 = window_stats(excess_k3h5, eng.AUDIT_START, eng.AUDIT_END)
        row["k3_h5_audit_excess_bp"] = bp0
        row["k3_h5_audit_block_t"] = t0
        row["k3_h5_audit_n"] = n0

        # 2a. Yearly (K=3/H=5, full available range, not audit-restricted)
        yearly = {}
        for year in YEARS:
            bp, t, n = window_stats(excess_k3h5, f"{year}-01-01", f"{year}-12-31")
            row[f"k3_h5_excess_bp_{year}"] = bp
            row[f"k3_h5_block_t_{year}"] = t
            row[f"k3_h5_n_{year}"] = n
            yearly[year] = (bp, t, n)

        # 2b. Sub-periods (K=3/H=5)
        subperiods = {}
        for label, start, end in SUBPERIODS:
            bp, t, n = window_stats(excess_k3h5, start, end)
            row[f"k3_h5_excess_bp_{label}"] = bp
            row[f"k3_h5_block_t_{label}"] = t
            row[f"k3_h5_n_{label}"] = n
            subperiods[label] = (bp, t, n)

        # 3. Top-3 turnover proxy (K=3/H=5, full available range)
        turnover_mean, turnover_n = turnover_proxy(top_mask_k3h5)
        row["top3_turnover_intersection_mean"] = turnover_mean
        row["top3_turnover_n_transitions"] = turnover_n

        profile_rows.append(row)

        md_sections.append(
            f"### {cid}（来源 {cand['round']}，direction={direction:+.0f}）\n"
            f"表达式：`{cand['operator']}({cand['left']['name']}, {cand['right']['name']})`\n\n"
            f"**K/H 变体（审计期 2024-01～2025-04）：**\n\n"
            f"| 参数 | 审计超额(bp) | block-t | n |\n|---|---|---|---|\n"
            f"| K=2,H=5 | {row['k2_h5_audit_excess_bp']:.2f} | {row['k2_h5_audit_block_t']:.2f} | {row['k2_h5_audit_n']} |\n"
            f"| K=3,H=5(主参数) | {row['k3_h5_audit_excess_bp']:.2f} | {row['k3_h5_audit_block_t']:.2f} | {row['k3_h5_audit_n']} |\n"
            f"| K=4,H=5 | {row['k4_h5_audit_excess_bp']:.2f} | {row['k4_h5_audit_block_t']:.2f} | {row['k4_h5_audit_n']} |\n"
            f"| K=3,H=10 | {row['k3_h10_audit_excess_bp']:.2f} | {row['k3_h10_audit_block_t']:.2f} | {row['k3_h10_audit_n']} |\n"
            f"| K=3,H=20 | {row['k3_h20_audit_excess_bp']:.2f} | {row['k3_h20_audit_block_t']:.2f} | {row['k3_h20_audit_n']} |\n\n"
            f"**逐年（K=3,H=5，全样本区间，非仅审计期）：**\n\n"
            f"| 年 | 超额(bp) | block-t | n |\n|---|---|---|---|\n"
            + "\n".join(
                f"| {year} | {yearly[year][0]:.2f} | {yearly[year][1]:.2f} | {yearly[year][2]} |"
                if np.isfinite(yearly[year][0]) else f"| {year} | nan | nan | {yearly[year][2]} |"
                for year in YEARS
            )
            + "\n\n**子期（K=3,H=5）：**\n\n"
            f"| 子期 | 超额(bp) | block-t | n |\n|---|---|---|---|\n"
            + "\n".join(
                f"| {label} | {subperiods[label][0]:.2f} | {subperiods[label][1]:.2f} | {subperiods[label][2]} |"
                if np.isfinite(subperiods[label][0]) else f"| {label} | nan | nan | {subperiods[label][2]} |"
                for label, _, _ in SUBPERIODS
            )
            + f"\n\n**top-3 持仓日均换手（交集大小均值，全样本区间）：** {turnover_mean:.3f}（转移数 n={turnover_n}）\n"
        )

    # 4. Rank correlation matrix (raw signal, discovery window, stride=5 -- same method as dedup gate)
    stride_vectors = {cid: eng._stride_vector(signals[cid]) for cid in signals}
    ids = [c["id"] for c in CANDIDATES]
    corr_matrix = pd.DataFrame(index=ids, columns=ids, dtype=float)
    for i, a in enumerate(ids):
        for b in ids[i:]:
            value = eng._pairwise_pearson(stride_vectors[a], stride_vectors[b])
            corr_matrix.loc[a, b] = value
            corr_matrix.loc[b, a] = value

    # --- write outputs ---
    metrics = pd.DataFrame(profile_rows)
    metrics.to_csv(OUT / "robustness_profile.csv", index=False)
    corr_matrix.round(4).to_csv(OUT / "rank_correlation_matrix.csv")

    empty_candidate_metrics = pd.DataFrame(
        columns=["candidate_id", "expression", "mechanism", "expected_sign", "direction",
                 "discovery_ic", "seen_audit_ic", "gate_pass", "gate_failures", "evidence_status"]
    )
    empty_candidate_metrics.to_csv(OUT / "candidate_metrics.csv", index=False)

    corr_lines = ["| |" + "|".join(ids) + "|", "|---|" + "---|" * len(ids)]
    for a in ids:
        corr_lines.append("| " + a + " |" + "|".join(f"{corr_matrix.loc[a, b]:.3f}" for b in ids) + "|")

    report = (
        "# round_633 -- S34（顶级簇稳健性剖面，只报不改门）\n\n"
        "## 任务\n"
        "主控指定：对本线主控验证两窗口显著、按簇归一后的 15 条代表候选做只报告不改门的稳健性剖面。"
        "本轮 n_preregistered=0，不做任何门/口径/权重/组合结论，只列数。\n\n"
        "## 对象（15 条，round-local ID 已按 gate_pass=True 去歧义）\n\n"
        "| ID | 来源轮次 | 算子 | direction | 左腿 | 右腿 |\n|---|---|---|---|---|---|\n"
        + "\n".join(
            f"| {c['id']} | {c['round']} | {c['operator']} | {c['direction']:+.0f} | "
            f"{c['left']['name']} | {c['right']['name']} |"
            for c in CANDIDATES
        )
        + "\n\n## 逐候选剖面\n\n"
        + "\n".join(md_sections)
        + "\n## 15×15 rank 相关矩阵（原始信号，未加 direction，discovery 窗口，stride=5，与去重门同方法）\n\n"
        + "\n".join(corr_lines)
        + "\n\n## 锚检查\n"
        "本轮为对已入选进攻型单因子候选的稳健性剖面报告，不做策略/仓位/择时/组合判断，"
        "不改变七道门口径，仅供主控簇归一登记参考。\n"
    )
    (OUT / "ROBUSTNESS_PROFILE.md").write_text(report)

    status = {
        "round_id": ROUND_ID,
        "as_of": eng.AS_OF,
        "stage": "S34_profile",
        "n_preregistered": 0,
        "n_gate_pass": 0,
        "profiled_candidates": ids,
        "profiled_candidate_source_rounds": {c["id"]: c["round"] for c in CANDIDATES},
        "outputs": ["ROBUSTNESS_PROFILE.md", "robustness_profile.csv", "rank_correlation_matrix.csv"],
        "note": "只报不改门；不预注册新候选；不做门/口径/权重/组合结论。",
    }
    (OUT / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2))

    exhausted = {
        "status": "MECHANISM_EXHAUSTED",
        "stage": "S34_profile",
        "rounds": [ROUND_ID],
        "reason": "S34 是主控指定的单轮只报告阶段（'只此一轮'），非挖掘阶段：不预注册新候选，"
                  "只对 15 条已入选簇代表做 K/H 变体、逐年、子期、换手、rank corr 矩阵的补充稳健性剖面。"
                  "任务完成即视为本阶段穷尽，无需继续本阶段。",
        "corrected_admission_count": 0,
        "raw_gate_pass_count": 0,
        "tested_scope": {
            "profiled_candidates": ids,
            "total_candidates_evaluated": 0,
            "metrics_reported_per_candidate": [
                "k2_h5_audit", "k3_h5_audit(primary)", "k4_h5_audit",
                "k3_h10_audit", "k3_h20_audit",
                "yearly_2021_2025(k3h5)", "subperiod_2024H1ext(k3h5)", "subperiod_2024H2_2025Q1(k3h5)",
                "top3_turnover_intersection_mean", "rank_corr_matrix_15x15",
            ],
        },
        "next_required_input": "主控查阅 outputs/round_633/ROBUSTNESS_PROFILE.md 完成簇归一登记，指定 S35 方向。",
        "retrospective": "本轮无 RETROSPECTIVE.md（无门失败可统计，报告型阶段）",
    }
    (OUT / "MECHANISM_EXHAUSTED.json").write_text(json.dumps(exhausted, ensure_ascii=False, indent=2))

    print(f"wrote {len(profile_rows)} candidate profiles to {OUT}")
    print(metrics[["candidate_id", "k3_h5_audit_excess_bp", "k3_h5_audit_block_t",
                    "top3_turnover_intersection_mean"]].to_string(index=False))


if __name__ == "__main__":
    main()
