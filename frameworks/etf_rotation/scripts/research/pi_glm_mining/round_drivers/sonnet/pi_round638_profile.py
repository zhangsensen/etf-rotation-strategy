#!/usr/bin/env python3
"""Round 638 driver: S39 stage (main controller directive, 2026-09-21) --
H=10/H=20 profile (K=3 fixed) for ALL gate_pass=True candidates on this
line since round_005 (the line's own numbering before the round_500
rename), report-only, no gate/criteria changes, no new preregistration.

Reuses the same pattern as round_633's S34 profile: reconstructs each
candidate's exact signal via PLAN.json's stored left/right/operator,
builds atoms once via the engine's own _build_atoms (cache-backed, no
new 1m derivation expected since every atom here was already computed
by its own originating round), and computes AUDIT-window excess_bp +
5-session block-t at K=3 for H in {5, 10, 20}.

Classification (per directive) uses AUDIT block-t (the "still holds
after discovery" test, consistent with S34's convention of reporting
audit-window K/H variants):
  slow_signal: audit_t(H=5) < 2 AND audit_t(H=20) >= 2
  short_only:  audit_t(H=5) >= 2 AND audit_t(H=20) < 1
  all_horizon: audit_t(H=5) >= 2 AND audit_t(H=10) >= 2 AND audit_t(H=20) >= 2
round_022_replay is excluded (byte-identical replay of round_022's Z2,
not a distinct candidate)."""
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

ROUND_ID = "round_638"
OUT = eng.WORKSPACE_OUTPUTS / ROUND_ID
OUT.mkdir(parents=True, exist_ok=True)


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


def audit_stats(excess: pd.Series) -> tuple[float, float]:
    s = excess.dropna()
    s = s.loc[(s.index >= eng.AUDIT_START) & (s.index <= eng.AUDIT_END)]
    if s.empty:
        return float("nan"), float("nan")
    return float(s.mean() * 1e4), block_t(s)


def main() -> None:
    eng.load_builtin_families()
    admitted = pd.read_csv("/tmp/all_admitted_dir.csv")

    targets = []
    plan_cache: dict[str, dict] = {}
    for _, row in admitted.iterrows():
        rnd, cid, direction = row["round"], row["id"], float(row["direction"])
        if rnd not in plan_cache:
            plan_path = eng.WORKSPACE_OUTPUTS / rnd / "PLAN.json"
            plan_cache[rnd] = json.loads(plan_path.read_text())
        plan = plan_cache[rnd]
        cand = next((c for c in plan["candidates"] if c["id"] == cid), None)
        if cand is None:
            print(f"WARN: {rnd}:{cid} not found in PLAN.json, skipping")
            continue
        targets.append({
            "round": rnd, "id": cid, "direction": direction,
            "operator": cand["operator"],
            "left": {"name": cand["left"]["name"], "source": cand["left"]["source"]},
            "right": {"name": cand["right"]["name"], "source": cand["right"]["source"]},
        })

    print(f"loaded {len(targets)} target candidates from {len(plan_cache)} rounds")

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
        except KeyError as exc:
            print(f"WARN: {t['round']}:{t['id']} missing atom {exc}, skipping")
            continue
        direction = t["direction"]

        row = {"round": t["round"], "candidate_id": t["id"], "operator": op,
               "left": t["left"]["name"], "right": t["right"]["name"], "direction": direction}
        for h in (5, 10, 20):
            exc = excess_series(signal, direction, forward[h], eligibility, 3)
            bp, tt = audit_stats(exc)
            row[f"h{h}_audit_bp"] = bp
            row[f"h{h}_audit_t"] = tt
        rows.append(row)

    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "slow_signal_profile.csv", index=False)

    def sig(x):
        return np.isfinite(x) and x >= 2

    def weak(x):
        return np.isfinite(x) and x < 1

    slow = metrics[metrics["h5_audit_t"].apply(lambda x: np.isfinite(x) and x < 2) &
                   metrics["h20_audit_t"].apply(sig)]
    short_only = metrics[metrics["h5_audit_t"].apply(sig) &
                         metrics["h20_audit_t"].apply(weak)]
    all_horizon = metrics[metrics["h5_audit_t"].apply(sig) &
                          metrics["h10_audit_t"].apply(sig) &
                          metrics["h20_audit_t"].apply(sig)]

    def fmt_table(df: pd.DataFrame) -> str:
        if df.empty:
            return "（无）\n"
        lines = ["| round | id | 表达式 | H5 t / bp | H10 t / bp | H20 t / bp |",
                 "|---|---|---|---|---|---|"]
        for _, r in df.iterrows():
            expr = r["left"] if r["operator"] == "atomic" else f"{r['left']} x {r['right']}"
            lines.append(
                f"| {r['round']} | {r['candidate_id']} | {expr} | "
                f"{r['h5_audit_t']:.2f} / {r['h5_audit_bp']:.1f} | "
                f"{r['h10_audit_t']:.2f} / {r['h10_audit_bp']:.1f} | "
                f"{r['h20_audit_t']:.2f} / {r['h20_audit_bp']:.1f} |"
            )
        return "\n".join(lines) + "\n"

    report = f"""# round_638 -- S39（全部入选候选的 H=10/H=20 剖面，只报不改门）

## 任务
主控指定：对本线全部 gate_pass=True 的候选（round_005 起，含改名前的早期编号）计算 K=3 下 H=10、H=20 的审计超额与 block-t，列出三类名单。本轮 n_preregistered=0，不做任何门/口径/权重/组合结论，只列数。

## 样本范围
从 outputs/round_*/candidate_metrics.csv 抓取全部 gate_pass=True 记录，去掉 round_022_replay（round_022 的逐 bp 重放，非独立候选），共 {len(admitted)} 条；成功重建信号并算出 K=3/H=5/10/20 审计统计的 {len(metrics)} 条。

## 分类标准（均用审计期 block-t，block=5）
- **慢信号名单**：H=5 t<2 且 H=20 t≥2（被 5 日裁判漏掉的信号）
- **只有短期名单**：H=5 t≥2 且 H=20 t<1（信号在更长视界上迅速衰减）
- **全视界名单**：H=5、H=10、H=20 的 t 都 ≥2

## 慢信号名单（{len(slow)} 条）
{fmt_table(slow)}

## 只有短期名单（{len(short_only)} 条）
{fmt_table(short_only)}

## 全视界名单（{len(all_horizon)} 条）
{fmt_table(all_horizon)}

## 锚检查
本轮为对已入选候选的稳健性剖面报告，不做策略/仓位/择时/组合判断，不改变七道门口径。
"""
    (OUT / "SLOW_SIGNAL_PROFILE.md").write_text(report)

    status = {
        "round_id": ROUND_ID,
        "as_of": eng.AS_OF,
        "stage": "S39_profile",
        "n_preregistered": 0,
        "n_gate_pass": 0,
        "n_candidates_profiled": len(metrics),
        "n_slow_signal": len(slow),
        "n_short_only": len(short_only),
        "n_all_horizon": len(all_horizon),
        "outputs": ["SLOW_SIGNAL_PROFILE.md", "slow_signal_profile.csv"],
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
        "stage": "S39_profile",
        "rounds": [ROUND_ID],
        "reason": "S39 是主控指定的单轮只报告阶段（'只此一轮'）：对全部历史入选候选做 H=10/H=20 剖面，不预注册新候选。任务完成即视为本阶段穷尽。",
        "corrected_admission_count": 0,
        "raw_gate_pass_count": 0,
        "tested_scope": {
            "n_admitted_history": len(admitted),
            "n_profiled": len(metrics),
            "n_slow_signal": len(slow),
            "n_short_only": len(short_only),
            "n_all_horizon": len(all_horizon),
        },
        "next_required_input": "主控查阅 outputs/round_638/SLOW_SIGNAL_PROFILE.md，指定 S40 方向。",
        "retrospective": "本轮无 RETROSPECTIVE.md（无门失败可统计，报告型阶段）",
    }
    (OUT / "MECHANISM_EXHAUSTED.json").write_text(json.dumps(exhausted, ensure_ascii=False, indent=2))

    print(f"profiled={len(metrics)} slow={len(slow)} short_only={len(short_only)} all_horizon={len(all_horizon)}")


if __name__ == "__main__":
    main()
