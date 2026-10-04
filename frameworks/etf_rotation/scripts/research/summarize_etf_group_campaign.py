#!/usr/bin/env python3
"""Read-only input audit and local handoff for the bounded group campaign."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[4]
ENTRY=Path(__file__).with_name('discover_etf_groups.py')
spec=importlib.util.spec_from_file_location('group_discovery_handoff_entry',ENTRY)
entry=importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id',required=True)
    args=ap.parse_args()
    if not args.run_id.replace('_','').isalnum():
        raise ValueError('invalid run-id')
    base=ROOT/'runtime_outputs/etf_rotation_research'
    out=base/'handoffs'/args.run_id
    out.mkdir(parents=True,exist_ok=False)
    keys=set()
    inventory=[]
    summaries=[]
    audited=0
    for path in sorted((base/'runs').glob('*/PLAN.json')):
        plan=json.loads(path.read_text())
        if 'mechanisms' not in plan.get('config',{}):
            continue
        run=path.parent
        keys |= entry.definition_keys(plan)
        cfg=plan['config']
        if (cfg['horizon'],cfg['top_k'],cfg['entry_lag'],cfg['as_of'])!=(5,2,2,'2026-09-17'):
            raise ValueError('mixed campaign scope')
        for filename,digest in plan['source_hashes'].items():
            if sha(run/'source'/Path(filename).name)!=digest:
                raise ValueError('source snapshot changed')
            audited+=1
        verdict_path=run/'verdict.json'
        record={'run':run.name,'plan_sha256':sha(path),'registered':len(plan['candidate_ids'])}
        if not verdict_path.exists():
            if not (run/'FAILURE.md').exists():
                raise ValueError(f'unexplained incomplete run: {run}')
            record.update(status='FAILED_BEFORE_EVALUATION',evaluated=0)
        else:
            v=json.loads(verdict_path.read_text())
            s=pd.read_csv(run/'summary.csv')
            if len(s)!=v['evaluated'] or not json.loads((run/'future_leak_check.json').read_text())['all_pass']:
                raise ValueError('verdict/count/leak evidence mismatch')
            if set(s.candidate)!=set(plan['evaluated_ids']):
                raise ValueError('result IDs differ from frozen plan')
            metrics=pd.read_csv(run/'daily_metrics.csv',parse_dates=['signal_date','entry_date','exit_date'])
            valid=metrics.ic.notna()
            if not ((metrics.loc[valid,'signal_date']<metrics.loc[valid,'entry_date']) &
                    (metrics.loc[valid,'entry_date']<metrics.loc[valid,'exit_date'])).all():
                raise ValueError('time ordering failed')
            if not np.allclose((metrics.excess8+metrics.allocation_effect).dropna(),
                               metrics.excess14.dropna(),atol=1e-12):
                raise ValueError('benchmark decomposition failed')
            s['run']=run.name
            s['source_type']=cfg.get('source_type','daily')
            pilot=len(plan['evaluated_ids'])<len(plan['candidate_ids'])
            record.update(status='PILOT_REPLAY' if pilot else 'EVALUATED',evaluated=len(s),
                          admitted=int(s.screen_pass.sum()),first_signal=s.first_signal.min(),
                          last_signal=s.last_signal.max(),n_min=int(s.n.min()),n_max=int(s.n.max()))
            if not pilot:
                summaries.append(s)
            if cfg.get('source_type')=='interaction':
                pairs=pd.read_csv(run/'paired_increment.csv')
                if len(pairs)!=2*len(s) or not pairs.groupby('candidate').side.nunique().eq(2).all():
                    raise ValueError('missing paired leg comparisons')
                record['paired_leg_comparisons']=len(pairs)
                record['candidates_passing_both_paired_metrics']=int((~s.failed_screens.str.contains('paired_increment',na=False)).sum())
        inventory.append(record)
    all_rows=pd.concat(summaries,ignore_index=True)
    if all_rows.candidate.duplicated().any():
        raise ValueError('duplicate formulas in nonpilot summary; do not double count')
    if len(keys)>96:
        raise ValueError('budget cap violated')
    all_rows.to_csv(out/'all_candidates.csv',index=False)
    payload={'unique_evaluated_candidates':len(all_rows),'registered_source_versions':len(keys),
             'registration_cap':96,'registrations_remaining':96-len(keys),
             'admitted_candidates':int(all_rows.screen_pass.sum()),'certified_factors':0,
             'source_snapshot_hashes_checked':audited,'runs':inventory,
             'scope':'fixed14/eight_groups/H5/K2/seen_history_only',
             'checks':'source snapshots, IDs, counts, signal-entry-exit order, benchmark identity, paired coverage',
             'not_proven':'source vintages, independent confirmation, live execution or universal absence of ETF alpha'}
    (out/'AUDIT.json').write_text(json.dumps(payload,indent=2)+'\n')
    (out/'source.py').write_text(Path(__file__).read_text())
    lines=['# Bounded ETF group discovery handoff','',
           f"Evaluated formulas: {len(all_rows)}. Admitted: {payload['admitted_candidates']}. Certified: 0.",
           f'Registered source versions: {len(keys)}/96; remaining: {96-len(keys)}.',
           'Failed source-loader versions were reserved before any return evaluation and remain counted.',
           'All results are previously seen history, H5, D+2 to D+7, K=2. Main return benchmark B8; mandatory comparison B14.',
           'Coverage differs by batch; do not treat cross-batch t rankings as paired incremental evidence.', '',
           '| Run | Status | Evaluated | Admitted | Dates | N |',
           '|---|---|---:|---:|---|---|']
    for r in inventory:
        lines.append(f"| {r['run']} | {r['status']} | {r['evaluated']} | {r.get('admitted','—')} | {r.get('first_signal','—')} — {r.get('last_signal','—')} | {r.get('n_min','—')} |")
    lines += ['', 'No new budget, population, holding horizon or screening threshold is authorized by this report.',
              'Budget exhaustion closes this bounded batch, not the general research objective.',
              'Further new definitions require an explicit budget decision; existing evidence may still be audited without new selection.',
              '', 'Reproduce: `uv run --no-sync python frameworks/etf_rotation/scripts/research/summarize_etf_group_campaign.py --run-id <new-id>`.',
              'Evidence: AUDIT.json, all_candidates.csv and the source run REPORT/PLAN/summary/paired_increment files.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(payload,indent=2))


if __name__=='__main__':
    main()
