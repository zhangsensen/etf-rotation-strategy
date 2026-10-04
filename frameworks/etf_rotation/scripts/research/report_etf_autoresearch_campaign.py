#!/usr/bin/env python3
"""Reconcile a saved campaign and export every signed IC without rerunning it."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

from etf_autoresearch_status import campaign_progress


def report(campaign_dir, output):
    campaign_dir, output = Path(campaign_dir).resolve(), Path(output).resolve()
    summary_path = campaign_dir / 'summary.json'
    summary = json.loads(summary_path.read_text())
    progress = campaign_progress(summary, campaign_dir)
    output.mkdir(parents=True, exist_ok=False)
    progress.update(campaign_id=summary.get('campaign_id', campaign_dir.name),
                    source_summary=str(summary_path),
                    source_sha256=hashlib.sha256(summary_path.read_bytes()).hexdigest(),
                    command=[sys.executable, *sys.argv], historical_outputs_modified=False)
    (output / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n')
    root = campaign_dir.parent.parent
    fields = ['run_id', 'candidate', 'status', 'result_evidence_status', 'direction', 'ic', 'hac_t', 'n',
              'first_signal', 'last_signal', 'formula', 'reason_code', 'error', 'result_path']
    table = []
    for row in summary.get('rounds', []):
        path = root / row['run_id'] / 'result.json'
        result = json.loads(path.read_text()) if path.exists() else {}
        item = {key: (row.get(key) if key == 'status' else result.get(key, row.get(key)))
                for key in fields if key != 'result_evidence_status'}
        item['result_evidence_status'] = result.get('status')
        plan = row.get('family_plan') or {}
        item.update(direction=result.get('direction', plan.get('direction')),
                    formula=plan.get('formula'), result_path=str(path) if path.exists() else None)
        table.append(item)
    with (output / 'candidates.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(table)
    lines = [f"# {progress['campaign_id']}", '',
             f"Effective status: {progress['effective_status']}; recorded status: {progress['recorded_status']}.",
             f"Verified completed rounds: {progress['verified_completed_rounds']}/{progress['requested_rounds']}; "
             f"rounds with candidates: {progress['rounds_with_candidates']}; candidate records: {len(table)}.",
             f"Planning error rounds: {progress['planning_error_rounds']}.", '',
             'Fixed 14 ETFs / 8 groups; close(D) signal; open(D+2) to open(D+7) H5 cross-sectional signed Rank IC.',
             'Seen-history discovery. Direction is frozen; missing evidence stays missing. Family/iteration counts are not independent factors.', '',
             '| Candidate | Status | Direction | IC | HAC t | n | Signal window |',
             '|---|---|---:|---:|---:|---:|---|']
    def number(value):
        return f'{value:+.6f}' if isinstance(value, (int, float)) and math.isfinite(value) else ''
    for row in table:
        lines.append(f"| {row['candidate'] or row['run_id']} | {row['status']} | {row['direction'] or ''} | "
                     f"{number(row['ic'])} | {number(row['hac_t'])} | {row['n'] if row['n'] is not None else ''} | "
                     f"{row['first_signal'] or ''} .. {row['last_signal'] or ''} |")
    lines += ['', f'Source: {summary_path}', 'Formula and failure detail: candidates.csv',
              'Reconciliation and command: progress.json', '']
    (output / 'REPORT.md').write_text('\n'.join(lines))
    return progress


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', type=Path, required=True, help='directory containing summary.json')
    parser.add_argument('--output', type=Path, required=True, help='new local-only report directory')
    args = parser.parse_args()
    print(json.dumps(report(args.campaign, args.output), ensure_ascii=False))
