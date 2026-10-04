#!/usr/bin/env python3
"""IC-first presentation of immutable frozen80 v3 evidence; no new evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'runtime_outputs/etf_rotation_research/rejudgments/frozen80_2025_rejudge_20260922_v3'


def classify(frame):
    """Preserve original signed metrics; do not replace IC with returns."""
    out = frame.copy()
    out['coverage_sufficient'] = out['n'].ge(360)
    out['ic_supported'] = out['ranking_supported']
    out['ic_budget_supported'] = out.ic_supported & out.budget_diagnostic_pass
    out['economic_supported'] = out.coverage_sufficient & out.economic_metrics_pass
    out['reverse_watch'] = (out.ic_mean.le(-.01) & out.ic_hac_t.le(-2)
                            & out.ic_block_t.le(-2))
    out['ic_evidence_status'] = 'NOT_SUPPORTED_THIS_SCREEN'
    out.loc[out.reverse_watch, 'ic_evidence_status'] = 'REVERSE_WATCH_NOT_VALIDATED'
    out.loc[out.ic_supported, 'ic_evidence_status'] = 'IC_LEAD_ONLY'
    out.loc[~out.coverage_sufficient, 'ic_evidence_status'] = 'INSUFFICIENT_COVERAGE'
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id', required=True)
    args = ap.parse_args()
    if not args.run_id.replace('_', '').isalnum():
        raise ValueError('invalid run-id')
    files = [SOURCE / n for n in ('comparison.csv', 'PLAN.json', 'verdict.json',
                                  'yearly.csv', 'leave_group.csv', 'paired_increment.csv')]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    hashes = {str(p): sha(p) for p in files}
    frame = pd.read_csv(SOURCE / 'comparison.csv', float_precision='round_trip')
    assert len(frame) == 80 and frame.candidate.is_unique
    result = classify(frame)
    out = ROOT / 'runtime_outputs/etf_rotation_research/ic_reports' / args.run_id
    out.mkdir(parents=True, exist_ok=False)
    plan = {'kind': 'PRESENTATION_ONLY_NO_NEW_FORMULAS_OR_EVALUATION',
            'signal_start': '2025-01-01', 'exit_end': '2026-09-17',
            'time_contract': 'close(D) score; open(D+2) to open(D+7) adjusted gross return',
            'primary_statistic': 'signed H5 eight-group Rank IC',
            'economic_primary': 'B8', 'mandatory_comparator': 'B14',
            'inherited_batch_correction_denominator': 96,
            'global_search_count': 'UNKNOWN', 'input_hashes': hashes,
            'source_hash': sha(Path(__file__)),
            'reverse_rule': 'signed mean<=-.01, HAC t<=-2, block t<=-2; watch only',
            'new_hypotheses': 0}
    (out / 'PLAN.json').write_text(json.dumps(plan, indent=2) + '\n')
    result.to_csv(out / 'all80.csv', index=False)
    result[result.ic_supported].to_csv(out / 'ic_leads.csv', index=False)
    result[result.reverse_watch].to_csv(out / 'reverse_watch.csv', index=False)
    counts = {k: int(result[k].sum()) for k in (
        'coverage_sufficient', 'ic_supported', 'ic_budget_supported',
        'economic_metrics_pass', 'economic_supported', 'reverse_watch')}
    counts.update(evaluated=80, insufficient_coverage=int((~result.coverage_sufficient).sum()),
                  raw_ic_economic_intersection=int((result.ranking_metrics_pass & result.economic_metrics_pass).sum()),
                  covered_ic_economic_intersection=int((result.ic_supported & result.economic_supported).sum()),
                  certified_factors=0)
    (out / 'verdict.json').write_text(json.dumps(counts, indent=2) + '\n')
    lines = ['# IC优先：固定80条排序证据', '',
             '2025起、退出不晚于2026-09-17；固定14只/8组，D+2→D+7，H5。',
             '主问题为排序信息；K2相对B8的经济指标与B14对照另列。未重算或改变公式、方向、门限。',
             '全部为已见历史；基础IC线索不是校正后显著或认证因子。96是继承的批内条件校正，累计搜索未知。',
             '', '```json', json.dumps(counts, indent=2), '```', '',
             '## 基础IC线索（覆盖及原排序门通过）', '',
             '|候选|N|IC|HAC t|块t|B8 t（另列）|批内校正通过|',
             '|---|---:|---:|---:|---:|---:|---|']
    for r in result[result.ic_supported].itertuples():
        lines.append(f'|{r.candidate}|{r.n}|{r.ic_mean:.4f}|{r.ic_hac_t:.2f}|{r.ic_block_t:.2f}|{r.excess8_hac_t:.2f}|{r.budget_diagnostic_pass}|')
    lines += ['', '## 反向观察（不是原方向通过，也不是已验证的新方向）', '',
              '|候选|N|原方向IC|HAC t|块t|', '|---|---:|---:|---:|---:|']
    for r in result[result.reverse_watch].itertuples():
        lines.append(f'|{r.candidate}|{r.n}|{r.ic_mean:.4f}|{r.ic_hac_t:.2f}|{r.ic_block_t:.2f}|')
    lines += ['', '负向统计一直保留在v3全表；本次新增显式观察清单，不翻向、不新增运行。',
              '翻向需要新假设登记；同一历史面换批次不成为独立验证。',
              '经济指标2条均覆盖不足，覆盖合格经济支持0条；原始IC/经济指标交集为own_downside（226日），不是空集。',
              '低IC不能证明头部超额必然是噪声；这里只能说该候选缺乏整体排序支持。',
              '已有货架增量、源数据历史可得版本和独立确认均未认证。', '',
              '复现：`uv run --no-sync python frameworks/etf_rotation/scripts/research/report_group_ic_evidence.py --run-id <new-id>`']
    (out / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    assert {str(p): sha(p) for p in files} == hashes
    print(json.dumps(counts, indent=2))


if __name__ == '__main__':
    main()
