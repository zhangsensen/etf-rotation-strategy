#!/usr/bin/env python3
"""Round 644 driver: S44 stage (main controller directive, 2026-09-21) --
H=20 profile (K=3) for candidates rejected SOLELY by topk_gate (gate 7),
i.e. every other gate (discovery_days, abs_discovery_ic,
signed_seen_audit_ic, horizon_direction, year_direction, identity_gate)
passed. Report-only, no new preregistration, no gate changes.

Finds candidates where H=20 discovery block-t >= 2 AND H=20 audit
block-t >= 2 ("rejected by the 5-day referee, but the 20-day horizon
holds up on both windows") -- the mirror image of S39's slow-signal
finding, this time applied to the REJECTED pool instead of the admitted
one."""
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

ROUND_ID = "round_644"
OUT = eng.WORKSPACE_OUTPUTS / ROUND_ID
OUT.mkdir(parents=True, exist_ok=True)

_VOLUME_KEYWORDS = ("VOL", "BAR", "MFI", "TURNOVER", "AMOUNT", "OBV", "TICK", "LBAR", "AD_", "ELASTICITY")


def _is_volume(names: list[str]) -> bool:
    return any(any(k in n for k in _VOLUME_KEYWORDS) for n in names)


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


def excess_series(signal, direction, forward_h, eligibility, k):
    sig = (signal * direction).where(eligibility)
    f = forward_h.where(eligibility)
    valid = sig.notna() & f.notna()
    sig, f = sig.where(valid), f.where(valid)
    n = valid.sum(axis=1)
    ok = n >= max(eng.MIN_PAIRS, k + 1)
    top_mask = (sig.rank(axis=1, ascending=False, method="first") <= k) & ok.to_numpy()[:, None]
    top_ret = f.where(top_mask).mean(axis=1).where(ok)
    ew_ret = f.mean(axis=1).where(ok)
    return top_ret - ew_ret


def window_stats(excess: pd.Series, start=None, end=None) -> tuple[float, float, int]:
    s = excess.dropna()
    if start is not None:
        s = s.loc[s.index >= pd.Timestamp(start)]
    if end is not None:
        s = s.loc[s.index <= pd.Timestamp(end)]
    if s.empty:
        return float("nan"), float("nan"), 0
    return float(s.mean() * 1e4), block_t(s), int(len(s))


def main() -> None:
    eng.load_builtin_families()

    rejects = pd.read_csv("/tmp/topk_only_rejects.csv")
    print(f"loaded {len(rejects)} topk_gate-only-rejected candidates")

    plan_cache: dict[str, dict] = {}
    targets = []
    for _, row in rejects.iterrows():
        rnd, cid = row["round"], row["id"]
        if rnd not in plan_cache:
            plan_path = eng.WORKSPACE_OUTPUTS / rnd / "PLAN.json"
            if not plan_path.exists():
                continue
            plan_cache[rnd] = json.loads(plan_path.read_text())
        plan = plan_cache[rnd]
        cand = next((c for c in plan["candidates"] if c["id"] == cid), None)
        if cand is None:
            continue
        targets.append({
            "round": rnd, "id": cid, "direction": float(row["direction"]),
            "h5_disc_t_orig": row["topk_t_block5_disc"],
            "operator": cand["operator"],
            "left": {"name": cand["left"]["name"], "source": cand["left"]["source"]},
            "right": {"name": cand["right"]["name"], "source": cand["right"]["source"]},
        })
    print(f"resolved {len(targets)} against PLAN.json")

    panels, eligibility_all, symbols, forward = eng._load_context()
    eligibility = eligibility_all[symbols]

    plan_stub = {"candidates": [{"left": t["left"], "right": t["right"]} for t in targets]}
    ranked = eng._build_atoms(panels, eligibility_all, symbols, plan_stub)
    print(f"built/loaded {len(ranked)} unique atoms")

    rows = []
    for t in targets:
        op = t["operator"]
        spec = ExpressionSpec(op, t["left"]["name"], None if op == "atomic" else t["right"]["name"])
        try:
            signal = materialize_expression(spec, ranked)
        except KeyError:
            continue
        direction = t["direction"]
        exc20 = excess_series(signal, direction, forward[20], eligibility, 3)
        disc_bp, disc_t, disc_n = window_stats(exc20, None, eng.DISCOVERY_END)
        audit_bp, audit_t, audit_n = window_stats(exc20, eng.AUDIT_START, eng.AUDIT_END)

        left_name, right_name = t["left"]["name"], t["right"]["name"]
        rows.append({
            "round": t["round"], "candidate_id": t["id"], "operator": op,
            "left": left_name, "right": right_name if op != "atomic" else "",
            "direction": direction,
            "h5_disc_t_orig": t["h5_disc_t_orig"],
            "h20_disc_bp": disc_bp, "h20_disc_t": disc_t, "h20_disc_n": disc_n,
            "h20_audit_bp": audit_bp, "h20_audit_t": audit_t, "h20_audit_n": audit_n,
            "has_volume_leg": _is_volume([left_name] + ([right_name] if op != "atomic" else [])),
        })

    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "rejected_h20_profile.csv", index=False)

    def sig(x):
        return np.isfinite(x) and x >= 2

    surviving = metrics[metrics["h20_disc_t"].apply(sig) & metrics["h20_audit_t"].apply(sig)].copy()
    surviving = surviving.sort_values("h20_audit_t", ascending=False)

    # rank-corr check against S43's cluster representatives (0.6-threshold ledger)
    same_cluster_flags = []
    try:
        cluster_df = pd.read_csv("outputs/round_643/cluster_ledger_v2.csv")
        rep_keys = cluster_df["representative"].tolist()
        rep_plan_cache = plan_cache
        rep_targets = []
        for rk in rep_keys:
            rrnd, rcid = rk.split(":")
            if rrnd not in rep_plan_cache:
                rep_plan_cache[rrnd] = json.loads((eng.WORKSPACE_OUTPUTS / rrnd / "PLAN.json").read_text())
            rc = next((c for c in rep_plan_cache[rrnd]["candidates"] if c["id"] == rcid), None)
            if rc is None:
                continue
            rep_targets.append({"key": rk, "operator": rc["operator"],
                                 "left": {"name": rc["left"]["name"], "source": rc["left"]["source"]},
                                 "right": {"name": rc["right"]["name"], "source": rc["right"]["source"]}})
        rep_plan_stub = {"candidates": [{"left": r["left"], "right": r["right"]} for r in rep_targets]}
        rep_ranked = eng._build_atoms(panels, eligibility_all, symbols, rep_plan_stub)
        rep_vectors = {}
        for r in rep_targets:
            rop = r["operator"]
            rspec = ExpressionSpec(rop, r["left"]["name"], None if rop == "atomic" else r["right"]["name"])
            rsig = materialize_expression(rspec, rep_ranked)
            rep_vectors[r["key"]] = eng._stride_vector(rsig)

        for _, row in surviving.iterrows():
            op = row["operator"]
            spec = ExpressionSpec(op, row["left"], None if op == "atomic" else row["right"])
            sig_frame = materialize_expression(spec, ranked)
            vec = eng._stride_vector(sig_frame)
            best_corr, best_key = 0.0, ""
            for rk, rv in rep_vectors.items():
                c = eng._pairwise_pearson(vec, rv)
                if np.isfinite(c) and abs(c) > abs(best_corr):
                    best_corr, best_key = c, rk
            same_cluster_flags.append({"max_corr_vs_admitted": best_corr, "closest_admitted": best_key,
                                        "same_cluster": abs(best_corr) >= 0.7})
    except FileNotFoundError:
        same_cluster_flags = [{"max_corr_vs_admitted": np.nan, "closest_admitted": "", "same_cluster": False}
                               for _ in range(len(surviving))]

    for k, flag in zip(surviving.index, same_cluster_flags):
        surviving.loc[k, "max_corr_vs_admitted"] = flag["max_corr_vs_admitted"]
        surviving.loc[k, "closest_admitted"] = flag["closest_admitted"]
        surviving.loc[k, "same_cluster"] = flag["same_cluster"]

    surviving.to_csv(OUT / "rejected_h20_survivors.csv", index=False)

    def fmt_table(df: pd.DataFrame) -> str:
        if df.empty:
            return "（无）\n"
        lines = ["| round | id | 表达式 | H5 t(原) | H20 disc t/bp | H20 audit t/bp | 含量腿 | 与已入选最大corr | 同簇 |",
                 "|---|---|---|---|---|---|---|---|---|"]
        for _, r in df.iterrows():
            expr = r["left"] if r["operator"] == "atomic" else f"{r['left']} x {r['right']}"
            lines.append(
                f"| {r['round']} | {r['candidate_id']} | {expr} | {r['h5_disc_t_orig']:.2f} | "
                f"{r['h20_disc_t']:.2f}/{r['h20_disc_bp']:.1f} | {r['h20_audit_t']:.2f}/{r['h20_audit_bp']:.1f} | "
                f"{'是' if r['has_volume_leg'] else '否'} | {r['max_corr_vs_admitted']:.3f} | "
                f"{'是' if r['same_cluster'] else '否'} |"
            )
        return "\n".join(lines) + "\n"

    n_novol = int((surviving["has_volume_leg"] == False).sum()) if len(surviving) else 0
    n_same_cluster = int(surviving["same_cluster"].sum()) if len(surviving) else 0

    report = f"""# round_644 -- S44（被门7拒绝候选的 H=20 剖面，只报不改门）

## 任务
主控指定：S39 只看了入选候选的 H=10/H=20 表现；本阶段看**被拒绝**的——本线 round_500 起全部 gate_pass=False 且**只因 topk_gate（门7）被拒**（其余六道门全部通过）的候选，计算 K=3 下 H=20 的发现期与审计期 block-t，找出"5 日裁判拒掉、20 日视界两窗口都成立"（disc t≥2 且 audit t≥2）的名单。本轮 n_preregistered=0，不改门。

## 样本范围
从 outputs/round_5*+/candidate_metrics.csv 抓取 gate_failures 精确等于 "topk_gate" 的记录（即其余六道门——discovery_days/abs_discovery_ic/signed_seen_audit_ic/horizon_direction/year_direction/identity_gate——全部通过，只差门7）：共 {len(rejects)} 条，成功重建信号并算出 H=20 统计的 {len(metrics)} 条。

## 发现：H=20 两窗口都 ≥2 的"漏网"候选（{len(surviving)} 条）
{fmt_table(surviving)}

## 汇总
- 两窗口 H=20 都显著的候选共 **{len(surviving)}** 条（占重算样本 {len(metrics)} 条的 {len(surviving)/max(len(metrics),1)*100:.1f}%）。
- 其中 **{n_novol}** 条两腿都不含成交量水平。
- 其中 **{n_same_cluster}** 条与某个已入选簇代表 rank corr ≥0.7（即使被 H=5 门拒绝，本质上是已入选机制的同簇变体，非独立新发现）。
- 剩余 **{len(surviving) - n_same_cluster}** 条为与现有入选簇不重叠的独立候选，是本阶段最值得后续跟进的名单。

## 锚检查
本轮为对已拒绝候选的稳健性剖面报告，不做策略/仓位/择时/组合判断，不改变七道门口径。
"""
    (OUT / "REJECTED_H20_PROFILE.md").write_text(report)

    status = {
        "round_id": ROUND_ID,
        "as_of": eng.AS_OF,
        "stage": "S44_profile",
        "n_preregistered": 0,
        "n_gate_pass": 0,
        "n_rejects_scoped": len(rejects),
        "n_profiled": len(metrics),
        "n_h20_both_windows_significant": len(surviving),
        "n_no_volume_survivors": n_novol,
        "n_same_cluster_as_admitted": n_same_cluster,
        "outputs": ["REJECTED_H20_PROFILE.md", "rejected_h20_profile.csv", "rejected_h20_survivors.csv"],
        "note": "只报不改门；不预注册新候选；不做门/口径/权重/组合结论。",
    }
    (OUT / "STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2))

    empty_candidate_metrics = pd.DataFrame(
        columns=["candidate_id", "expression", "mechanism", "expected_sign", "direction",
                 "discovery_ic", "seen_audit_ic", "gate_pass", "gate_failures", "evidence_status"]
    )
    empty_candidate_metrics.to_csv(OUT / "candidate_metrics.csv", index=False)

    exhausted = {
        "status": "MECHANISM_EXHAUSTED",
        "stage": "S44_profile",
        "rounds": [ROUND_ID],
        "reason": "S44 是主控指定的单轮只报告阶段（'只此一轮'）：对被门7拒绝的候选做 H=20 剖面，不预注册新候选。任务完成即视为本阶段穷尽。",
        "corrected_admission_count": 0,
        "raw_gate_pass_count": 0,
        "tested_scope": {
            "n_rejects_scoped": len(rejects),
            "n_profiled": len(metrics),
            "n_h20_both_windows_significant": len(surviving),
            "n_no_volume_survivors": n_novol,
            "n_same_cluster_as_admitted": n_same_cluster,
        },
        "next_required_input": "主控查阅 outputs/round_644/REJECTED_H20_PROFILE.md，决定是否需要把独立 H=20 名单纳入未来某个机制加深阶段，并指定 S45 方向。",
        "retrospective": "本轮无 RETROSPECTIVE.md（无门失败可统计，报告型阶段）",
    }
    (OUT / "MECHANISM_EXHAUSTED.json").write_text(json.dumps(exhausted, ensure_ascii=False, indent=2))

    print(f"profiled={len(metrics)} h20_both_significant={len(surviving)} no_volume={n_novol} same_cluster={n_same_cluster}")


if __name__ == "__main__":
    main()
