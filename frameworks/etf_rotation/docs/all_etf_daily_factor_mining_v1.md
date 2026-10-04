# All-ETF daily factor mining v1

> Historical, separate-population specification (archived in place 2026-09-22).
> This is not the active fixed-14 ETF research plan. See
> [current methodology](../ETF_ROTATION_METHODOLOGY.md) and
> [document status](document_status.md). Retained for provenance, not execution authorization.

## Terminal deliverable

- Input: point-in-time exchange-fund lifecycle plus TuShare daily OHLCV,
  adjustment factors, frozen candidate formulas and frozen directions.
- Output: `admitted_factors.json`, `candidate_metrics.csv`, leak audits and a
  sealed run manifest.
- Pass: a candidate passes every frozen forward IC, fixed-budget Bonferroni,
  top-decile excess, baseline-residual and sequential non-redundancy gate.
- Fail: zero admitted factors is a valid result. A candidate that fails one
  gate is not renamed, retuned or replaced using the same forward surface.

## Time and population contract

- Population: exchange-qualified ETF codes whose identity snapshot name
  contains `ETF`, with listing/delisting lifecycle applied on each date.
- Eligibility known at D close: at least 120 observed sessions, positive daily
  OHLCV and trailing-20 median amount of at least CNY 10m.
- Signal: D close; entry: D+2 open; exit: D+7 open.
- Label: `adjusted_open(D+7) / adjusted_open(D+2) - 1`.
- Benchmark: equal-weight return of the same D-known eligible cross-section.
- Discovery-only surfaces end 2025-04-30. The forward surface starts
  2025-05-01 and must not exist locally when `PLAN.json` is sealed.

## Isolation protocol

1. Download only through 2025-04-30.
2. Profile causal daily atoms. Labels may score candidates but never enter an
   atom, filter, imputation rule, eligibility rule or timestamp.
3. Freeze candidate formulas, directions, campaign budget and all thresholds.
4. Run prefix truncation and future perturbation before writing the PLAN.
5. Seal source/config/artifact hashes and every pre-forward data partition.
6. Download the forward period without refreshing the frozen identity snapshot.
7. Recheck all hashes and rerun the leak audit before producing verdicts.

Missing future labels never change the selected names. For the top-decile
check, a day needs at least 95% label coverage; remaining missing returns are
zero in both the selected sleeve and benchmark. IC uses only common finite
pairs and requires at least 100 names.

## Commands

```bash
uv run --no-sync python frameworks/etf_rotation/scripts/research/download_all_etf_daily.py \
  --data-root /home/sensen/dev/projects/gpu_ml/data/etf_all_daily_v1 \
  --start 20200101 --end 20250430

PYTHONPATH=frameworks/etf_rotation/src uv run --no-sync python \
  frameworks/etf_rotation/scripts/research/discover_all_etf_daily.py \
  --config frameworks/etf_rotation/configs/all_etf_daily_discovery_v1.yaml \
  --output runtime_outputs/<discovery-run>

PYTHONPATH=frameworks/etf_rotation/src uv run --no-sync python \
  frameworks/etf_rotation/scripts/research/evaluate_all_etf_daily.py plan \
  --config frameworks/etf_rotation/configs/all_etf_daily_discovery_v1.yaml \
  --candidates frameworks/etf_rotation/configs/<frozen-candidates>.yaml \
  --discovery-output runtime_outputs/<discovery-run> \
  --output runtime_outputs/<sealed-plan>

uv run --no-sync python frameworks/etf_rotation/scripts/research/download_all_etf_daily.py \
  --data-root /home/sensen/dev/projects/gpu_ml/data/etf_all_daily_v1 \
  --start 20250501 --end 20260917

PYTHONPATH=frameworks/etf_rotation/src uv run --no-sync python \
  frameworks/etf_rotation/scripts/research/evaluate_all_etf_daily.py evaluate \
  --plan runtime_outputs/<sealed-plan>/PLAN.json \
  --output runtime_outputs/<forward-verdict>
```

Data, caches, profiles, plans, metrics and reports remain local and are never
committed or uploaded.
