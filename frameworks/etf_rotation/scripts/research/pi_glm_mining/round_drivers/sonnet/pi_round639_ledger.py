#!/usr/bin/env python3
"""Round 639 driver: S40 stage (main controller directive, 2026-09-21) --
cluster ledger for ALL of this line's OWN gate_pass=True candidates
(round_500 onward), report-only, no gate/criteria changes, no new
preregistration.

Data-integrity note found while scoping this round: round_638's S39
profile (outputs/round_638/slow_signal_profile.csv) mistakenly included
29 candidates from rounds 005-076 -- those rounds carry
PLAN.json["miner"] == "pi/zai/glm-5.3-flash" and round_022's stored
config path points into the PI workspace
(.../etf_pi_glm_mining_20260919/workspace/...). Per this workspace's own
CLAUDE.md and the main controller's opening line ("历史 79 轮（pi/GLM
线）产物在 outputs/，去重与 previously_admitted 直接读它们"), rounds
005-076 are PI-line history copied into this workspace SOLELY for
dedup/previously-admitted reference -- they are not this Sonnet line's
own mined candidates. S39's directive text said "round_500 起" but this
round_638 filtered on gate_pass=True across ALL outputs/round_* without
excluding the pi-authored 005-076 range. This round (S40) scopes
correctly to round_500+ only (135 of the 164 profiled in round_638) and
reuses round_638's already-computed h5/h10/h20 audit stats for the
round_500+ subset rather than recomputing.

Clustering: single-linkage (connected components) on pairwise rank
correlation (engine's own _stride_vector: discovery window, stride=5)
of each candidate's RAW signal (no direction applied, matching the
dedup gate's own convention), threshold |corr| >= 0.6."""
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

ROUND_ID = "round_639"
OUT = eng.WORKSPACE_OUTPUTS / ROUND_ID
OUT.mkdir(parents=True, exist_ok=True)

CORR_THRESHOLD = 0.6

_VOLUME_KEYWORDS = ("VOL", "BAR", "MFI", "TURNOVER", "AMOUNT", "OBV", "TICK", "LBAR", "AD_")

_REPRO_STATUS = {
    # atom-name substrings -> (status, note)
    "BIGBAR_DIR_SKEW_20": ("成立", "S26R2 用 pi 精确定义复现 Z2/R2_Z2，符号量级一致"),
    "VOL_AUTOCORR_20": ("成立", "S26R2 复现（Z2/CO36 相关）"),
    "LUNCH_PRE_RUN_20": ("成立", "S14 复现 CK04 成立"),
    "CLOSE5_DAY_CONSIST_20": ("成立", "S14 复现 CK04 成立"),
    "FIRST_PASSAGE_UP_20": ("成立", "S38 复现 DB09，与本线 round_577 VB1 逐 bp 一致（+31.9bp）"),
    "PD_D1_CHG_20": ("定义敏感", "S14 复现 DA57 同号但幅度差 14bp，判实现敏感"),
    "AUC_VARIANCE_RATIO_20": ("定义敏感", "S14 复现 DA57 同号但幅度差 14bp，判实现敏感"),
    "ON_PREM_20": ("未复现", "S14 复现 CZ01 未能复现"),
    "BIGBAR_EDGE_CONC_20": ("未复现", "S14 复现 CZ01 未能复现"),
    "PV_ELASTICITY_20": ("成立", "S14 复现 CA1 成立（与下行风险重叠）"),
}


def _repro_status(names: list[str]) -> str:
    for name in names:
        for key, (status, _note) in _REPRO_STATUS.items():
            if key in name:
                return status
    return "单实现"


def _is_volume(names: list[str]) -> bool:
    return any(any(k in n for k in _VOLUME_KEYWORDS) for n in names)


class UnionFind:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def main() -> None:
    eng.load_builtin_families()

    profile = pd.read_csv("outputs/round_638/slow_signal_profile.csv")
    profile["round_num"] = profile["round"].str.extract(r"round_(\d+)").astype(int)
    scoped = profile[profile["round_num"] >= 500].copy()
    excluded_pi = profile[profile["round_num"] < 500]
    print(f"round_500+ candidates: {len(scoped)} (excluding {len(excluded_pi)} pi-line rounds 005-076 "
          f"mistakenly included in round_638's S39 scope)")

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
            "round": rnd, "id": cid, "operator": cand["operator"],
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
        key = f"{t['round']}:{t['id']}"
        stride_vectors[key] = eng._stride_vector(signal)

    keys = list(stride_vectors.keys())
    uf = UnionFind(keys)
    n = len(keys)
    for i in range(n):
        for j in range(i + 1, n):
            corr = eng._pairwise_pearson(stride_vectors[keys[i]], stride_vectors[keys[j]])
            if np.isfinite(corr) and abs(corr) >= CORR_THRESHOLD:
                uf.union(keys[i], keys[j])

    by_key = {f"{t['round']}:{t['id']}": t for t in targets}
    groups: dict[str, list[str]] = {}
    for k in keys:
        root = uf.find(k)
        groups.setdefault(root, []).append(k)

    cluster_rows = []
    for members in groups.values():
        member_ts = [by_key[m] for m in members]
        rep = max(member_ts, key=lambda t: (t["h5_audit_t"] if np.isfinite(t["h5_audit_t"]) else -1e9))
        left_name = rep["left"]["name"]
        all_names = []
        for t in member_ts:
            all_names.append(t["left"]["name"])
            if t["operator"] != "atomic":
                all_names.append(t["right"]["name"])
        cluster_rows.append({
            "cluster_id": left_name,
            "representative": f"{rep['round']}:{rep['id']}",
            "representative_expr": rep["left"]["name"] if rep["operator"] == "atomic"
                                   else f"{rep['left']['name']} x {rep['right']['name']}",
            "n_members": len(members),
            "members": ";".join(sorted(members)),
            "h5_audit_t": rep["h5_audit_t"], "h5_audit_bp": rep["h5_audit_bp"],
            "h10_audit_t": rep["h10_audit_t"], "h10_audit_bp": rep["h10_audit_bp"],
            "h20_audit_t": rep["h20_audit_t"], "h20_audit_bp": rep["h20_audit_bp"],
            "has_volume_leg": _is_volume(all_names),
            "repro_status": _repro_status(all_names),
            "source_stage_hint": rep["round"],
        })

    cluster_df = pd.DataFrame(cluster_rows).sort_values("h5_audit_t", ascending=False)
    cluster_df.to_csv(OUT / "cluster_ledger.csv", index=False)

    lines = ["| 簇ID | 代表 | 表达式 | 成员数 | H5 t/bp | H10 t/bp | H20 t/bp | 含量腿 | 跨实现状态 |",
             "|---|---|---|---|---|---|---|---|---|"]
    for _, r in cluster_df.iterrows():
        lines.append(
            f"| {r['cluster_id']} | {r['representative']} | {r['representative_expr']} | {r['n_members']} | "
            f"{r['h5_audit_t']:.2f}/{r['h5_audit_bp']:.1f} | {r['h10_audit_t']:.2f}/{r['h10_audit_bp']:.1f} | "
            f"{r['h20_audit_t']:.2f}/{r['h20_audit_bp']:.1f} | {'是' if r['has_volume_leg'] else '否'} | "
            f"{r['repro_status']} |"
        )

    report = f"""# round_639 -- S40（本线簇归一账本，只报不改门）

## 任务
主控指定：把本线全部 gate_pass=True 候选（round_500 起）按 rank corr（stride 5，发现窗）单链接聚类（阈值 0.6），产出簇账本。本轮 n_preregistered=0，不做权重/组合结论，不改门。

## 范围修正（数据完整性发现）
上一轮 round_638（S39）在抓取"全部 gate_pass=True 候选"时误把 round_005–076（PLAN.json 记录 `miner: pi/zai/glm-5.3-flash`，round_022 的 config 路径指向 pi 工作区）共 **{len(excluded_pi)} 条 pi/GLM 线候选**当成本线自己的入选。这批早期编号轮次是主控指令开篇明确说明的"历史 79 轮（pi/GLM 线）产物在 outputs/，去重与 previously_admitted 直接读它们"——即 pi 线成果被复制进本工作区仅作去重参照，不是本线自己挖的。S39 指令原文本就写的是"round_500 起"，round_638 的过滤条件疏漏了这条限制。本轮（S40）按 round_500+ 正确限定范围：**{len(scoped)} 条**（round_638 剖面里已算好 H5/10/20 审计数字，直接复用，未重新计算）。

## 聚类方法
单链接（连通分量）：两条候选只要 rank corr（stride=5，发现窗，原始信号未加 direction，与去重门同方法）绝对值 ≥ 0.6 就连边，取连通分量为簇。簇 ID = 簇内审计 t（H=5）最高成员的左腿名；代表 = 同一候选。

## 簇账本（{len(cluster_df)} 簇，来自 {len(scoped)} 条候选）

{chr(10).join(lines)}

## 锚检查
本轮为已入选候选的聚类账本报告，不做权重/组合/策略判断，不改变七道门口径。
"""
    (OUT / "CLUSTER_LEDGER.md").write_text(report)

    status = {
        "round_id": ROUND_ID,
        "as_of": eng.AS_OF,
        "stage": "S40_ledger",
        "n_preregistered": 0,
        "n_gate_pass": 0,
        "n_candidates_scoped": len(scoped),
        "n_candidates_excluded_pi_line": len(excluded_pi),
        "n_clusters": len(cluster_df),
        "outputs": ["CLUSTER_LEDGER.md", "cluster_ledger.csv"],
        "note": "只报不改门；不预注册新候选；修正 round_638 误把 pi/GLM 线历史(round_005-076)计入本线范围的问题。",
    }
    (OUT / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2))

    empty_candidate_metrics = pd.DataFrame(
        columns=["candidate_id", "expression", "mechanism", "expected_sign", "direction",
                 "discovery_ic", "seen_audit_ic", "gate_pass", "gate_failures", "evidence_status"]
    )
    empty_candidate_metrics.to_csv(OUT / "candidate_metrics.csv", index=False)

    exhausted = {
        "status": "MECHANISM_EXHAUSTED",
        "stage": "S40_ledger",
        "rounds": [ROUND_ID],
        "reason": "S40 是主控指定的单轮只报告阶段（'只此一轮'）：对本线全部入选候选做簇归一账本，不预注册新候选。任务完成即视为本阶段穷尽。",
        "corrected_admission_count": 0,
        "raw_gate_pass_count": 0,
        "tested_scope": {
            "n_candidates_scoped": len(scoped),
            "n_candidates_excluded_pi_line_history": len(excluded_pi),
            "n_clusters": len(cluster_df),
        },
        "data_integrity_finding": (
            f"round_638 (S39) scope incorrectly included {len(excluded_pi)} PI/GLM-line candidates "
            "from rounds 005-076 (miner=pi/zai/glm-5.3-flash) that were copied into this workspace "
            "solely as dedup reference, not mined by this Sonnet line. Not corrected retroactively in "
            "round_638 itself (out of scope for this round); flagged here for the main controller's "
            "awareness. S40's own scope is correctly limited to round_500+."
        ),
        "next_required_input": "主控查阅 outputs/round_639/CLUSTER_LEDGER.md，决定是否需要回补修正 round_638 的范围，并指定 S41 方向。",
        "retrospective": "本轮无 RETROSPECTIVE.md（无门失败可统计，报告型阶段）",
    }
    (OUT / "MECHANISM_EXHAUSTED.json").write_text(json.dumps(exhausted, ensure_ascii=False, indent=2))

    print(f"scoped={len(scoped)} excluded_pi={len(excluded_pi)} clusters={len(cluster_df)}")


if __name__ == "__main__":
    main()
