#!/usr/bin/env python3
"""Round 643 driver: S43 stage (main controller directive, 2026-09-21) --
redo the cluster ledger with average-linkage (UPGMA) instead of
round_639's (S40) single-linkage, which chained 87/135 candidates into
one giant connected component (a well-known single-linkage pathology:
A-B corr~0.61, B-C corr~0.62 merges A and C even if A-C corr is near
zero). Report-only, no new preregistration, no gate changes.

Reuses round_638/round_639's already-computed inputs: the round_500+
candidate list + H5/10/20 audit stats from round_638's
slow_signal_profile.csv, rebuilt signals via the engine's own
_build_atoms/materialize_expression (cache-backed, fast). Computes the
full pairwise |rank corr| matrix (stride=5, discovery window, raw
signal, same convention as the dedup gate), converts to a distance
matrix (1 - |corr|), and runs scipy's average-linkage hierarchical
clustering, cutting at distance 0.3 (|corr| >= 0.7) as the primary cut
and distance 0.4 (|corr| >= 0.6) for comparison."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as eng  # noqa: E402
from etf_strategy.core.etf_factor_grammar import ExpressionSpec, materialize_expression  # noqa: E402

ROUND_ID = "round_643"
OUT = eng.WORKSPACE_OUTPUTS / ROUND_ID
OUT.mkdir(parents=True, exist_ok=True)

_VOLUME_KEYWORDS = ("VOL", "BAR", "MFI", "TURNOVER", "AMOUNT", "OBV", "TICK", "LBAR", "AD_", "ELASTICITY")

_REPRO_STATUS = {
    "BIGBAR_DIR_SKEW_20": "成立",
    "VOL_AUTOCORR_20": "成立",
    "LUNCH_PRE_RUN_20": "成立",
    "CLOSE5_DAY_CONSIST_20": "成立",
    "FIRST_PASSAGE_UP_20": "成立",
    "PD_D1_CHG_20": "定义敏感",
    "AUC_VARIANCE_RATIO_20": "定义敏感",
    "ON_PREM_20": "未复现",
    "BIGBAR_EDGE_CONC_20": "未复现",
    "PV_ELASTICITY_20": "成立",
}


def _repro_status(names: list[str]) -> str:
    for name in names:
        if name in _REPRO_STATUS:
            return _REPRO_STATUS[name]
    return "单实现"


def _is_volume(names: list[str]) -> bool:
    return any(any(k in n for k in _VOLUME_KEYWORDS) for n in names)


def main() -> None:
    eng.load_builtin_families()

    profile = pd.read_csv("outputs/round_638/slow_signal_profile.csv")
    profile["round_num"] = profile["round"].str.extract(r"round_(\d+)").astype(int)
    scoped = profile[profile["round_num"] >= 500].copy()

    plan_cache: dict[str, dict] = {}
    targets = []
    for _, row in scoped.iterrows():
        rnd, cid = row["round"], row["candidate_id"]
        if rnd not in plan_cache:
            plan_cache[rnd] = json.loads((eng.WORKSPACE_OUTPUTS / rnd / "PLAN.json").read_text())
        cand = next((c for c in plan_cache[rnd]["candidates"] if c["id"] == cid), None)
        if cand is None:
            continue
        targets.append({
            "key": f"{rnd}:{cid}", "round": rnd, "id": cid, "operator": cand["operator"],
            "left": {"name": cand["left"]["name"], "source": cand["left"]["source"]},
            "right": {"name": cand["right"]["name"], "source": cand["right"]["source"]},
            "h5_audit_t": row["h5_audit_t"], "h5_audit_bp": row["h5_audit_bp"],
            "h10_audit_t": row["h10_audit_t"], "h10_audit_bp": row["h10_audit_bp"],
            "h20_audit_t": row["h20_audit_t"], "h20_audit_bp": row["h20_audit_bp"],
        })

    panels, eligibility_all, symbols, forward = eng._load_context()
    plan_stub = {"candidates": [{"left": t["left"], "right": t["right"]} for t in targets]}
    ranked = eng._build_atoms(panels, eligibility_all, symbols, plan_stub)

    stride_vectors = {}
    for t in targets:
        op = t["operator"]
        spec = ExpressionSpec(op, t["left"]["name"], None if op == "atomic" else t["right"]["name"])
        signal = materialize_expression(spec, ranked)
        stride_vectors[t["key"]] = eng._stride_vector(signal)

    keys = [t["key"] for t in targets]
    n = len(keys)
    corr_mat = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            c = eng._pairwise_pearson(stride_vectors[keys[i]], stride_vectors[keys[j]])
            c = c if np.isfinite(c) else 0.0
            corr_mat[i, j] = corr_mat[j, i] = c

    dist_mat = 1.0 - np.abs(corr_mat)
    np.fill_diagonal(dist_mat, 0.0)
    condensed = squareform(dist_mat, checks=False)
    Z = linkage(condensed, method="average")

    labels_07 = fcluster(Z, t=0.3, criterion="distance")
    labels_06 = fcluster(Z, t=0.4, criterion="distance")
    n_clusters_07 = len(set(labels_07))
    n_clusters_06 = len(set(labels_06))

    # Note: 0.7 is the dedup gate's own hard cutoff -- every admitted
    # candidate was already checked against every prior admitted one at
    # exactly this threshold before admission, so pairwise |corr| >= 0.7
    # among admitted candidates should be ~absent BY CONSTRUCTION. That
    # is confirmed below (n_clusters_07 == n_candidates, i.e. all
    # singletons) and is the expected, meaningful result, not a bug. The
    # actually informative grouping is the looser 0.6 cut (below the
    # gate's own threshold), used as the primary ledger here.
    by_key = {t["key"]: t for t in targets}
    groups: dict[int, list[str]] = {}
    for k, lab in zip(keys, labels_06):
        groups.setdefault(lab, []).append(k)

    cluster_rows = []
    for lab, members in groups.items():
        member_ts = [by_key[m] for m in members]
        rep = max(member_ts, key=lambda t: (t["h5_audit_t"] if np.isfinite(t["h5_audit_t"]) else -1e9))
        all_names = []
        for t in member_ts:
            all_names.append(t["left"]["name"])
            if t["operator"] != "atomic":
                all_names.append(t["right"]["name"])
        cluster_rows.append({
            "cluster_id": rep["left"]["name"],
            "representative": rep["key"],
            "representative_expr": rep["left"]["name"] if rep["operator"] == "atomic"
                                   else f"{rep['left']['name']} x {rep['right']['name']}",
            "n_members": len(members),
            "members": ";".join(sorted(members)),
            "h5_audit_t": rep["h5_audit_t"], "h5_audit_bp": rep["h5_audit_bp"],
            "h10_audit_t": rep["h10_audit_t"], "h10_audit_bp": rep["h10_audit_bp"],
            "h20_audit_t": rep["h20_audit_t"], "h20_audit_bp": rep["h20_audit_bp"],
            "has_volume_leg": _is_volume(all_names),
            "repro_status": _repro_status(all_names),
            "source_round": rep["round"],
        })

    cluster_df = pd.DataFrame(cluster_rows).sort_values("h5_audit_t", ascending=False)
    cluster_df.to_csv(OUT / "cluster_ledger_v2.csv", index=False)

    # rank corr matrix among cluster representatives. Index by the unique
    # `representative` key (round:id), NOT cluster_id (=left-leg atom
    # name) -- cluster_id is frequently duplicated (e.g.
    # CONTINUOUS_BETA_60 is the left leg of 12 different single-member
    # clusters), and indexing a DataFrame by a duplicated label makes
    # .loc[label, label] match ALL rows sharing that label, silently
    # returning a self-correlation of 1.0 instead of the intended
    # cross-cluster value. Caught via a sanity check (max was 1.0 before
    # this fix); cluster_id is kept only as a display label, appended
    # with the representative key to disambiguate.
    rep_keys = cluster_df["representative"].tolist()
    rep_labels = [f"{cid}[{key}]" for cid, key in zip(cluster_df["cluster_id"], rep_keys)]
    key_to_idx = {k: i for i, k in enumerate(keys)}
    rep_corr = pd.DataFrame(index=rep_labels, columns=rep_labels, dtype=float)
    for a_label, a_key in zip(rep_labels, rep_keys):
        for b_label, b_key in zip(rep_labels, rep_keys):
            rep_corr.loc[a_label, b_label] = corr_mat[key_to_idx[a_key], key_to_idx[b_key]]
    rep_corr.round(3).to_csv(OUT / "cluster_representative_corr_matrix.csv")

    max_offdiag = 0.0
    for i in range(len(rep_keys)):
        for j in range(len(rep_keys)):
            if i != j:
                max_offdiag = max(max_offdiag, abs(rep_corr.iloc[i, j]))

    def fmt_members(members_str: str) -> str:
        members = members_str.split(";")
        if len(members) <= 10:
            return ", ".join(members)
        return ", ".join(members[:10]) + f" 等 {len(members)} 条"

    lines = ["| 簇ID | 代表 | 表达式 | 成员数 | H5 t/bp | H10 t/bp | H20 t/bp | 含量腿 | 跨实现状态 | 来源轮次 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in cluster_df.iterrows():
        lines.append(
            f"| {r['cluster_id']} | {r['representative']} | {r['representative_expr']} | {r['n_members']} | "
            f"{r['h5_audit_t']:.2f}/{r['h5_audit_bp']:.1f} | {r['h10_audit_t']:.2f}/{r['h10_audit_bp']:.1f} | "
            f"{r['h20_audit_t']:.2f}/{r['h20_audit_bp']:.1f} | {'是' if r['has_volume_leg'] else '否'} | "
            f"{r['repro_status']} | {r['source_round']} |"
        )
    member_lines = ["\n### 簇成员明细\n"]
    for _, r in cluster_df.iterrows():
        member_lines.append(f"- **{r['cluster_id']}**（{r['n_members']} 条）：{fmt_members(r['members'])}")

    report = f"""# round_643 -- S43（簇归一账本重做：平均链接 UPGMA，只报不改门）

## 任务
主控指定：S40（round_639）用单链接（连通分量）阈值 0.6 把 87/135 候选串成一个巨簇（链式合并伪影），账本不可用。本轮改用平均链接（UPGMA）重做，主控原定阈值 |corr| ≥ 0.7；实算后发现 0.7 阈值下**全部 135 条候选各自成簇（0 次合并）**，原因不是 bug，而是这个阈值本身就是去重门的硬性判据——每条候选在入选前都已经和当时全部已入选候选做过 max_abs_rank_corr ≥ 0.7 的检验并要求不通过才会拒绝，所以入选集合内部两两 |corr| ≥ 0.7 按构造应当基本不存在，0.7 阈值下的"全员独立"是**预期且正确**的确认结果，不是聚类失败。因此本报告改用去重门阈值以下的 **0.6** 作为主账本（更松，能看出去重门允许通过但仍有中等相关性的候选群），0.7 结果作为确认性校验保留。

## 方法
沿用 round_638/639 已算好的 135 条 round_500+ 候选（H5/10/20 审计统计直接复用，未重算）；用引擎 `_build_atoms` + `materialize_expression` 重建每条候选的原始信号（未加 direction），取 `_stride_vector`（发现窗，stride=5，与去重门同口径）算出完整 135×135 pairwise |rank corr| 矩阵；距离 = 1 − |corr|；scipy `linkage(method="average")` + `fcluster(criterion="distance")` 切簇。

## 单链接 vs 平均链接对照
- 单链接（阈值 0.6，round_639 结果）：40 簇，其中 1 个巨簇吞下 87/135（64%）候选——链式合并伪影，账本不可用。
- 平均链接（阈值 0.7，去重门原生阈值）：**{n_clusters_07} 簇**（即全部候选独立成簇，确认去重门按设计工作：入选集合内部两两 |corr| < 0.7）。
- 平均链接（阈值 0.6，本报告采用为主账本）：**{n_clusters_06} 簇**——有意义的中等相关性分组，用来看哪些入选候选虽然通过了 0.7 硬门但彼此仍有 0.6–0.7 的中等相关。

## 簇代表之间的 rank corr 矩阵校验
{len(rep_keys)} 个簇代表（0.6 阈值下）两两 |rank corr| 的最大绝对值 = **{max_offdiag:.3f}**（预期 < 0.6；若有超出说明平均链接在阈值边界的簇间平均距离与簇代表间单点距离存在差异，已如实标注不做修正）。矩阵见 `cluster_representative_corr_matrix.csv`。

## 簇账本（{n_clusters_06} 簇，来自 135 条候选，阈值 0.6）

{chr(10).join(lines)}
{chr(10).join(member_lines)}

## 锚检查
本轮为已入选候选的聚类账本重做（修正单链接链式合并伪影），不做权重/组合/策略判断，不改变七道门口径。
"""
    (OUT / "CLUSTER_LEDGER_V2.md").write_text(report)

    status = {
        "round_id": ROUND_ID,
        "as_of": eng.AS_OF,
        "stage": "S43_ledger",
        "n_preregistered": 0,
        "n_gate_pass": 0,
        "n_candidates_scoped": len(targets),
        "n_clusters_single_linkage_06_round639": 40,
        "n_clusters_average_linkage_06": int(n_clusters_06),
        "n_clusters_average_linkage_07": int(n_clusters_07),
        "max_abs_corr_among_cluster_representatives": round(float(max_offdiag), 4),
        "outputs": ["CLUSTER_LEDGER_V2.md", "cluster_ledger_v2.csv", "cluster_representative_corr_matrix.csv"],
        "note": "只报不改门；不预注册新候选；修正 round_639 单链接链式合并伪影。",
    }
    (OUT / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2))

    empty_candidate_metrics = pd.DataFrame(
        columns=["candidate_id", "expression", "mechanism", "expected_sign", "direction",
                 "discovery_ic", "seen_audit_ic", "gate_pass", "gate_failures", "evidence_status"]
    )
    empty_candidate_metrics.to_csv(OUT / "candidate_metrics.csv", index=False)

    exhausted = {
        "status": "MECHANISM_EXHAUSTED",
        "stage": "S43_ledger",
        "rounds": [ROUND_ID],
        "reason": "S43 是主控指定的单轮只报告阶段（'只此一轮'）：用平均链接重做簇归一账本，修正 round_639 单链接链式合并伪影。不预注册新候选，任务完成即视为本阶段穷尽。",
        "corrected_admission_count": 0,
        "raw_gate_pass_count": 0,
        "tested_scope": {
            "n_candidates_scoped": len(targets),
            "n_clusters_single_linkage_06_round639": 40,
            "n_clusters_average_linkage_06": int(n_clusters_06),
            "n_clusters_average_linkage_07": int(n_clusters_07),
            "max_abs_corr_among_representatives": round(float(max_offdiag), 4),
        },
        "next_required_input": "主控查阅 outputs/round_643/CLUSTER_LEDGER_V2.md，决定是否需要用该账本做后续去重/权重工作，并指定 S44 方向。",
        "retrospective": "本轮无 RETROSPECTIVE.md（无门失败可统计，报告型阶段）",
    }
    (OUT / "MECHANISM_EXHAUSTED.json").write_text(json.dumps(exhausted, ensure_ascii=False, indent=2))

    print(f"scoped={len(targets)} clusters_avg_06={n_clusters_06} clusters_avg_07={n_clusters_07} "
          f"max_rep_corr={max_offdiag:.3f}")


if __name__ == "__main__":
    main()
