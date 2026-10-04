#!/usr/bin/env python3
"""Round 653 (S51, main controller directive, 2026-09-21): implementation
agreement matrix (report-only, no new candidates). For every atom that
this line has TWO genuinely independent implementations of (a
pi-paraphrased/pi-precise pair, or an S26R/S26R2-style rewrite pair, or
a pre-existing-family-vs-reproduction-family pair), compute discovery-
window and audit-window rank correlation (stride 5, matching the
engine's own dedup convention) plus each side's own single-atom
topk_gate discovery-t/audit-bp (pulled from historical candidate_metrics
.csv where available). Several items on the S51 directive's list turned
out, on inspection, to have only ONE implementation in this codebase
(the other "version" was a direct reuse, per the standing 禁造轮子
convention established in S45/S46) -- these are reported explicitly as
"not independently reimplemented" rather than silently skipped."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(SCRIPT.parent))

import pi_round002_mine as eng  # noqa: E402
from etf_strategy.core.family_registry import load_builtin_families, resolve_family  # noqa: E402

OUT = eng.WORKSPACE_OUTPUTS / "round_653"
OUT.mkdir(parents=True, exist_ok=True)

# (label, (name_a, source_a), (name_b, source_b))
PAIRS = [
    ("VOL_SPIKE_FREQ_20 (R_ paraphrased vs R2_ precise)",
     ("R_VOL_SPIKE_FREQ_20", "repl_volume_core_a"), ("R2_VOL_SPIKE_FREQ_20", "repl_volume_core_v2a")),
    ("BIGBAR_VOL_SHARE_20 (R_ vs R2_)",
     ("R_BIGBAR_VOL_SHARE_20", "repl_volume_core_b"), ("R2_BIGBAR_VOL_SHARE_20", "repl_volume_core_v2b")),
    ("BIGBAR_DIR_SKEW_20 (R_ vs R2_)",
     ("R_BIGBAR_DIR_SKEW_20", "repl_volume_core_a"), ("R2_BIGBAR_DIR_SKEW_20", "repl_volume_core_v2a")),
    ("VOL_AUTOCORR_20 (R_ vs R2_, identical formula both times)",
     ("R_VOL_AUTOCORR_20", "repl_volume_core_b"), ("R2_VOL_AUTOCORR_20", "repl_volume_core_v2b")),
    ("LOG_AMOUNT_VOL_20 (S26R rewrite vs pre-existing liquidity_variability)",
     ("R_LOG_AMOUNT_VOL_20", "repl_volume_core_a"), ("LOG_AMOUNT_VOL_20", "liquidity_variability")),
    ("ULCER_20 daily (S26R rewrite vs pre-existing downside_risk)",
     ("R_ULCER_20", "repl_volume_core_b"), ("ULCER_20", "downside_risk")),
    ("GAP_FILL_FRACTION_60 (S26R rewrite vs pre-existing gap_repair)",
     ("R_GAP_FILL_FRACTION_60", "repl_volume_core_b"), ("GAP_FILL_FRACTION_60", "gap_repair")),
    ("BIGBAR_EDGE_CONC (S14 paraphrased first/last-30min vs S45 precise modal-slot)",
     ("EDGE_BIGBAR_VOLSHARE_20", "pi_edge_bigbar_volshare_1m"), ("R2_BIGBAR_EDGE_CONC_20", "repl_overnight_core_v2b")),
    ("ON_PREM (S45 rewrite vs pre-existing daily_candle GAP_MEAN, textually identical formula)",
     ("R2_ON_PREM_20", "repl_overnight_core_v2a"), ("GAP_MEAN_20", "daily_candle")),
    ("OPEN30_VOL_SHARE_20 (S45 rewrite vs pre-existing intraday_volume_profile_1m)",
     ("R2_OPEN30_VOL_SHARE_20", "repl_overnight_core_v2b"), ("OPEN30_VOL_SHARE_20", "intraday_volume_profile_1m")),
    ("PRICE_POSITION (S45 rewrite vs S28 rewrite, both same formula)",
     ("R2_PRICE_POSITION_20", "repl_overnight_core_v2b"), ("S28_PRICE_POSITION_20", "pi_repl_s28")),
    ("VT_BUCKET_COUNT_SHIFT (S24 own-formula level-diff vs S46 pi-precise ratio)",
     ("VT_BUCKET_COUNT_SHIFT_20", "volume_time_1m"), ("R2_VT_BUCKET_COUNT_SHIFT_20", "repl_vt_bucket_precise_v1")),
    ("overnight variance share (S9 Yang-Zhang decomposition vs S21 simple RV ratio, different windows 20 vs 60)",
     ("YZ_OVERNIGHT_SHARE_20", "range_based_vol_1m"), ("ON_RV_SHARE_60", "overnight_structure_1d")),
]

NOT_REIMPLEMENTED = [
    ("LUNCH_GAP_20", "S46 explicitly reused lunch_break_1m:LUNCH_GAP_20 as-is (textually matches pi's precise definition); no second implementation exists to compare."),
    ("AUC_VARIANCE_RATIO_20", "S46 explicitly reused pi_auc_variance_ratio_1m:AUC_VARIANCE_RATIO_20 as-is; no second implementation exists."),
    ("LUNCH_PRE_RUN_20", "Only one implementation (S14 pi_lunch_prerun_1m); S18/S50 reused it directly, never rebuilt."),
    ("CLOSE5_DAY_CONSIST_20", "Only one implementation (etf_mined_families, S14 confirmed it textually matches pi's definition); never rebuilt."),
    ("PV_ELASTICITY_20", "Only one implementation (S14 pi_pv_elasticity_1m); reused directly in S28/S30/S50, never rebuilt."),
    ("CONTINUOUS_BETA_60", "Only one implementation (S4 jump_continuous_beta_1m); no pi-side independent rewrite exists on this line."),
    ("KYLE_LAMBDA_20", "Only one implementation, used once (S4's KU2 right leg); no second version."),
    ("MAX5_MEAN_20", "Only one implementation (S2 upside_tail); no second version."),
    ("GAP_DD_CONSUMPTION_RATIO_20", "Only one implementation (S27 overnight_intraday_mismatch_v1); S30/S36/S48 reuse or reference it, never rebuild."),
    ("REL_UNDERWATER_CATEGORY_20", "Only one implementation (S32 category_relative_geometry); no second version."),
    ("MFI_EXTREME_UNDERWATER_SKEW_20", "Only one implementation (S29 mechanism_atoms_v2); no second version."),
    ("ON_SIGN_STREAK_20", "Only one implementation (S21 overnight_structure_1d); no second version."),
]

DISCOVERY_END = eng.DISCOVERY_END
AUDIT_START, AUDIT_END = eng.AUDIT_START, eng.AUDIT_END


def _audit_stride_vector(signal: pd.DataFrame) -> pd.Series:
    """Same stride/stack rule as eng._stride_vector, WITHOUT its hardcoded
    .loc[:DISCOVERY_END] clamp -- that clamp is correct for the shelf
    dedup-gate use case (discovery window only) but silently empties any
    frame already restricted to the audit window, which is why the first
    attempt at this script produced audit_corr=nan for all 13 pairs."""
    return signal.iloc[:: eng.RANK_CORR_STRIDE].stack(future_stack=True)


def main() -> None:
    load_builtin_families()
    panels, eligibility_all, symbols, forward = eng._load_context()
    dates = panels["close"].index
    discovery_mask = dates <= DISCOVERY_END
    audit_mask = (dates >= AUDIT_START) & (dates <= AUDIT_END)

    space_cache: dict[str, dict] = {}

    def get_ranked(name: str, source: str) -> pd.DataFrame:
        if source not in space_cache:
            mining = yaml.safe_load(eng._config_path(source).read_text())
            space_cache[source] = resolve_family(source).builder(panels, eligibility_all, eng.CANONICAL_ROOT, mining)
        return eng.cross_sectional_rank(space_cache[source][name][symbols], eligibility_all[symbols])

    rows = []
    for label, (name_a, src_a), (name_b, src_b) in PAIRS:
        try:
            ranked_a = get_ranked(name_a, src_a)
            ranked_b = get_ranked(name_b, src_b)
        except Exception as exc:  # noqa: BLE001
            rows.append({"pair": label, "error": str(exc)})
            print(f"ERROR {label}: {exc}")
            continue

        vec_a_disc = eng._stride_vector(ranked_a.loc[discovery_mask])
        vec_b_disc = eng._stride_vector(ranked_b.loc[discovery_mask])
        vec_a_audit = _audit_stride_vector(ranked_a.loc[audit_mask])
        vec_b_audit = _audit_stride_vector(ranked_b.loc[audit_mask])

        # discovery-window corr uses the engine's own dedup-gate convention
        # (min_periods=500, the actual threshold the plan-stage redundancy
        # check applies). Audit-window corr is NOT part of that gate; the
        # shorter, stride-5-thinned audit sample rarely clears 500 pairs, so
        # it is computed here with a lower min_periods purely as a
        # supplementary diagnostic (not gate-standard; noted in the report).
        corr_disc = eng._pairwise_pearson(vec_a_disc, vec_b_disc)
        audit_frame = pd.DataFrame({"a": vec_a_audit, "b": vec_b_audit})
        n_audit_pairs = int(audit_frame.dropna().shape[0])
        audit_val = audit_frame.corr(min_periods=50)
        corr_audit = float(audit_val.loc["a", "b"]) if np.isfinite(audit_val.loc["a", "b"]) else float("nan")

        rows.append({
            "pair": label,
            "atom_a": f"{src_a}:{name_a}",
            "atom_b": f"{src_b}:{name_b}",
            "corr_discovery": corr_disc,
            "corr_audit": corr_audit,
            "n_audit_pairs": n_audit_pairs,
        })
        print(f"{label}: disc_corr={corr_disc:.3f} audit_corr={corr_audit:.3f} n_audit_pairs={n_audit_pairs}")

    table = pd.DataFrame(rows)
    table.to_csv(OUT / "implementation_agreement.csv", index=False)

    lines = ["# S51 独立实现一致性矩阵（round_653，只报不改门）\n"]
    lines.append("范围：本线全部同一构造存在两套独立实现的原子对（另一批 S51 指令名单里的原子经核查只有单一实现，见文末）。相关系数 = 引擎自己的 rank corr（stride=5），发现窗/审计窗分开算。\n")
    lines.append("## 一、可比对（存在两套独立实现）\n")
    lines.append("发现窗 corr = 引擎自身去重门口径（min_periods=500，含义=预注册去重时会用的相关性）。审计窗 corr 不是门槛的一部分，仅作补充诊断，min_periods=50（样本量见 n_audit_pairs 列）；分类以发现窗 corr 为准，审计窗仅供参考。\n")
    lines.append("| 原子对 | 发现窗 corr | 审计窗 corr | 审计窗有效对数 | 分类 |")
    lines.append("|---|---|---|---|---|")
    for r in rows:
        if "error" in r:
            lines.append(f"| {r['pair']} | ERROR | {r['error']} | — | — |")
            continue
        cd, ca, npairs = r["corr_discovery"], r["corr_audit"], r["n_audit_pairs"]
        cls = "写法无关(>0.95)" if (np.isfinite(cd) and cd > 0.95) else ("写法敏感(<0.85)" if (np.isfinite(cd) and cd < 0.85) else "中等一致")
        ca_str = f"{ca:.3f}" if np.isfinite(ca) else "nan(样本不足50对)"
        lines.append(f"| {r['pair']} | {cd:.3f} | {ca_str} | {npairs} | {cls} |")

    lines.append("\n## 二、不可比对（S51 名单里列出但实际只有单一实现，未重复造轮子）\n")
    lines.append("| 原子 | 说明 |")
    lines.append("|---|---|")
    for name, note in NOT_REIMPLEMENTED:
        lines.append(f"| {name} | {note} |")

    (OUT / "IMPLEMENTATION_AGREEMENT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
