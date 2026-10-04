# ETF family breadth v3 — Claude collaboration

This round expands mechanisms before IC mining. Signals use D-close information;
future labels remain D+2 open through D+2+H open (H=5/10/20), but no labels are
read by this breadth acceptance. Current population: 20 maintained ETFs and
14 candidate roles. Historical membership is not claimed point-in-time.

The v1/v2 catalogs remain intact. Use `configs/family_catalog_v3.yaml` with
`configs/economic_axis_taxonomy_v3.yaml`. The paired referee configuration is
`configs/family_adjudication_breadth_v3.yaml`; no new referee run is part of this task.
The expansion is 14 families / 32 atoms, to 45 families / 179 atoms.
All remain grouped in 11 axes: only volume-price distribution is a new axis.

| Family | New information | Explicit boundary |
|---|---|---|
| dependence_structure | Leading correlation-mode variance share and contemporaneous peer connectivity | Trailing eligible complete windows; minimum 5 members; eigenvector sign cancels by squaring |
| tail_dependence | Probability of own lower-tail event conditional on another ETF's event | Self excluded; thresholds estimated on lagged trailing 60 sessions with at least 40 observations, 15% quantile; minimum 3 conditioning events and 4 peers |
| macro_hedge_sensitivity | Bond/gold partial correlation controlling equity market | Benchmarks 510300/510500; references 511010/518880; gold self-sensitivity missing |
| pool_turnover_allocation | Change of turnover share within candidate pool | Secondary-market activity, not fund flow; at least 5 names complete throughout each trailing window; recompute all window denominators using that same D-known cohort |
| volume_at_price_memory | Turnover-weighted historical adjusted price position | HLC typical-price proxy, not actual VWAP or investor inventory |
| drawdown_duration | Underwater fraction and longest underwater run | Trailing 60-day high; 0.5% tolerance; no future recovery event |
| swing_topology | Number of trailing directional reversals | Threshold fixed at 1.5 times return std for each trailing window; no future pivot confirmation |
| volatility_feedback | Prior return sign versus current range-change/conditional range | Latest pair is D-1 return and D range; minimum 5 positive and negative observations for conditional ratio |
| gap_repair | Fraction of opening gap touched during the session | Adjusted daily OHLC only; absolute gap over 0.3%; minimum 5 qualifying days |
| intraday_systematic_share | Within-day peer-return R-squared | 5m; self excluded; 4 eligible peers minimum; 60% nonzero own bars |
| jump_variation | Realized versus bipower variation | 5m complete days; nonnegative jump share; 60% nonzero bars; proxy, not proof of news |
| intraday_profile_deviation | Distance of current turnover/absolute-return profiles from previous profile | 48 bins; lagged 20 complete observations; trading-session gaps are not fabricated |
| intraday_extremes_timing | Signed time between day's low and high | 5m complete days; earliest timestamp wins ties; flat range missing |
| intraday_volume_at_price | Close percentile and width of turnover-weighted typical-price distribution | Within-day prices only; no unadjusted cross-day join |

Window variants are atoms within one family. Family labels are mechanism
hypotheses, not proof of independent alpha. The full old catalog is included in
the redundancy check. Within-family variants can remain highly correlated;
they share the family-level multiplicity budget and must not be described as
independent discoveries.

## Excluded directions from Claude's proposal

- Co-drawdown: too close to existing drawdown and market-downside sensitivity;
  do not enlarge the taxonomy just by making an interaction.
- Intraday Kyle depth: missing signed-trade observations; lagged price-sign
  surrogate is not actual depth and overlaps existing price-impact mechanisms.
- Rank churn: second-order transformation of existing momentum, deferred to
  expression generation rather than counted as a new information family.
- Calendar pressure: low-priority seasonality hypothesis, not needed to assert
  current data coverage; no exchange-calendar inference from future rows.
- Vol-of-vol, alternative range-vol estimators and extra windows: no new family.

Five native ETF data gaps remain unchanged: fund shares/redemptions, NAV/IOPV,
underlying-index tracking, holdings, and primary-market baskets/quotes. These
must never be replaced by turnover proxies and called available.

## Reproduction

Run from repository root:

    PYTHONPATH=frameworks/etf_rotation/src .venv/bin/python -m pytest -q frameworks/etf_rotation/tests
    PYTHONPATH=frameworks/etf_rotation/src .venv/bin/python frameworks/etf_rotation/scripts/validate_family_catalog.py --canonical-data-root /home/sensen/dev/projects/gpu_ml/data/etf_rotation_v1 --universe-config config/etf_rotation_universe_v1.json --catalog frameworks/etf_rotation/configs/family_catalog_v3.yaml --as-of 2026-09-17 --output runtime_outputs/etf_family_catalog_v3_breadth_20260919.json

The catalog validator reads no outcomes. It verifies materialization and screens
rank aliases/cross-family correlation >=0.98 on the declared candidate pool.
This is a coarse redundancy screen, not independence or IC certification.
New tests cover prefix/future perturbations, price scaling, ineligible-peer
exclusion, incomplete intraday sessions and the as-of boundary.

Claude design and implementation audit outputs stay local under
`alpha_mining/AI/outputs/claude_reviews/`; data and generated outputs are not Git
artifacts. No stock-engine imports are introduced.

## Coverage and interpretation boundaries

Coverage is measured against the same 14 candidate roles, with 120-session
history and positive-volume eligibility, through 2026-09-17. The standalone
no-label surface diagnostic is local:
`runtime_outputs/etf_breadth_v3_surface_coverage_20260919.json`, reproduced by
`PYTHONPATH=frameworks/etf_rotation/src .venv/bin/python /tmp/etf_v3_surface_coverage.py`.
It counts dates with at least 8 finite eligible signals, before intersecting
with forward-return availability. The 32 new atoms have 406–581 such discovery
dates through 2023-12-31 and 312–320 seen-audit dates during
2024-01-01..2025-04-30. These are coverage counts, not IC observations or results.

The main validator also emits per-atom cell coverage, coverage on dates with
at least 8 eligible names, and total dates with at least 8 finite signals.
Older sparse-pool history is retained as missing; it is not backfilled to make
an atom appear rankable. Gold self-sensitivity remains missing. Minimum sample
and common signal/label checks still apply in the unchanged IC referee.

The new empty-peer-history and invalid-OHLC tests protect intraday cross-peer
alignment. Invalid turnover is excluded from turnover-allocation denominators.
Five native-data gaps above still constrain further meaningful expansion.
No claim is made that 45 family names mean 45 independent information sources,
or that this expansion has yielded a certified factor.

The final full-catalog materialization check passed on 2026-09-19 for 45
families / 179 atoms, with zero exact rank aliases and zero cross-family pairs
at absolute rank correlation >=0.98. Among the new atoms, cell coverage on
at-least-8-eligible dates ranges from 83.42% to 100%; this does not imply
independence at lower correlation thresholds. ETF tests: 314 passed / 3 skipped.
The future-leak static scan found no suspicious hits in the three new core
builders; prefix and future-perturbation tests provide the dynamic checks.

## Claude paired-review disposition

Design review: local
`alpha_mining/AI/outputs/claude_reviews/20260919T060238Z_etf_breadth_v3_design.stdout.txt`.
Paired audit: local
`alpha_mining/AI/outputs/claude_reviews/20260919T061001Z_etf_breadth_v3_implementation.stdout.txt`.
Both completed successfully via the `claude-code-review` skill. The paired
review conditionally accepted breadth after concrete repairs:

- Removed `PEER_ABS_CONNECTIVITY_60` and `UNDERWATER_RUN_20` before mining;
  their within-family rank correlations to retained atoms were about 0.966
  and 0.962. Final new count is 32, not the initial 34. Within-family pairs
  >=0.95 are now reported (not automatically rejected) for the full catalog.
- Fixed turnover allocation with a D-known cohort complete over the entire
  window and recomputed every denominator in that window on that same cohort.
  Simply delaying eligibility by w days, as the review's snippet suggested,
  would delay the membership spike without removing it. Constant-turnover
  entry/exit regression tests require exactly zero allocation change.
- Declared gold's maximum 13-candidate population in its config. A new test
  confirms the existing referee intersects and reranks both signal and label
  on the same 13 names; it does not assume 14 IC pairs. Thus no new external
  gold ETF or universe change is required. Gold self-exclusion and nonrandom
  activity/tail missingness remain visible limitations.
- Aligned intraday systematic output to the daily index; a missing daily
  session is handled without a KeyError. Aligned referee columns with the
  validator's reindexing behavior.
- Renamed signed `EXTREME_TIME_SPAN` to `EXTREME_TIME_ORDER` and documented
  the tail threshold's minimum 40 observations within its lagged 60-session
  window. No threshold was changed after viewing outcomes.

There was no new IC/return-label run. The next step is the frozen v3 family
adjudication, with the existing generation ledger and positive/negative IC
both eligible for discovery-direction assessment.
