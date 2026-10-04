#!/usr/bin/env python3
"""Describe registered group signals on seen discovery history; never certify."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'frameworks/etf_rotation/src'))
from etf_strategy.core.etf_mining_referee import fractional_topk_weights

RUNS=['group_daily_v1_batch_20260922','group_minute_v1_batch_20260922',
      'group_share_v1_loaderfix_20260922']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_panel(p):
    d=pd.read_csv(p,index_col=0,parse_dates=True)
    if d.index.has_duplicates or not d.index.is_monotonic_increasing:
        raise ValueError(f'invalid panel index: {p}')
    return d


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run-id',required=True)
    args=ap.parse_args()
    if not args.run_id.replace('_','').isalnum():
        raise ValueError('invalid run-id')
    base=ROOT/'runtime_outputs/etf_rotation_research'
    out=base/'profiles'/args.run_id
    out.mkdir(parents=True,exist_ok=False)
    files=[]
    scores={}
    labels=None
    known=None
    end=pd.Timestamp('2024-12-31')
    for name in RUNS:
        run=base/'runs'/name
        plan=json.loads((run/'PLAN.json').read_text())
        if (plan['config']['entry_lag'],plan['config']['horizon'],plan['config']['top_k'])!=(2,5,2):
            raise ValueError('incompatible time contract')
        lab=read_panel(run/'group_labels.csv')
        if labels is None:
            labels=lab
        else:
            pd.testing.assert_frame_equal(labels,lab)
        cv=pd.read_csv(run/'coverage.csv',parse_dates=['signal_date','exit_date']).set_index('signal_date')
        mask=cv.known_complete & cv.labels_complete & cv.exit_date.le(end) & cv.index.to_series().ge('2023-07-27')
        known=mask if known is None else known & mask
        files.extend([run/'PLAN.json',run/'coverage.csv',run/'group_labels.csv'])
        for p in sorted(run.glob('scores_*.csv')):
            candidate=p.stem.removeprefix('scores_')
            if candidate in scores:
                raise ValueError('duplicate candidate')
            scores[candidate]=read_panel(p)
            files.append(p)
    hashes={str(p):sha(p) for p in files}
    plan={'purpose':'SEEN_DISCOVERY_DESCRIPTION_ONLY','discovery_exit_end':'2024-12-31',
          'input_runs':RUNS,'input_hashes':hashes,'candidate_count':len(scores),
          'new_candidate_formulas':0,'command':[sys.executable,*sys.argv],
          'description':'Same-date winner/loser feature contrast and descriptive group fixed-effect decomposition. '
                        'Fitted group means are never materialized as tradable features; no p-values or certification.'}
    (out/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
    (out/'source.py').write_text(Path(__file__).read_text())
    dates=known.index[known]
    labels=labels.reindex(dates)
    if not labels.notna().all().all():
        raise ValueError('incomplete labels after coverage alignment')
    winner=fractional_topk_weights(labels,2,min_names=8)
    loser=fractional_topk_weights(-labels,2,min_names=8)
    y=labels.rank(axis=1,pct=True)
    # Cross-sectional ranks center each date; group means are fitted diagnostics only.
    y=y.sub(y.mean(axis=1),axis=0)
    yw=y-y.mean(axis=0)
    rows=[]
    group_rows=[]
    for name,score in scores.items():
        score=score.reindex(dates)
        if not score.notna().all().all():
            raise ValueError('incomplete pre-known feature sample')
        x=score.rank(axis=1,pct=True)
        x=x.sub(x.mean(axis=1),axis=0)
        xw=x-x.mean(axis=0)
        raw_cov=float((x*y).mean().mean())
        within_cov=float((xw*yw).mean().mean())
        between=float((x.mean(axis=0)*y.mean(axis=0)).mean())
        identity_fraction=float((x.mean(axis=0)**2).mean()/x.pow(2).mean().mean())
        contrasts=[]
        for g in labels:
            high=(score[g]*winner[g]).sum()/winner[g].sum()
            low=(score[g]*loser[g]).sum()/loser[g].sum()
            sd=score[g].std()
            effect=(high-low)/sd if sd>0 else np.nan
            contrasts.append(effect)
            group_rows.append({'candidate':name,'group':g,'winner_loser_std_difference':effect,
                               'winner_weight':winner[g].sum(),'loser_weight':loser[g].sum()})
        row={'candidate':name,'n_dates':len(dates),'raw_rank_ic':score.rank(axis=1).corrwith(labels.rank(axis=1),axis=1).mean(),
             'rank_identity_variance_fraction':identity_fraction,'raw_rank_covariance':raw_cov,
             'within_group_rank_covariance':within_cov,'between_group_rank_covariance':between,
             'positive_within_group_contrasts':int(np.sum(np.array(contrasts)>0)),
             'median_within_group_std_contrast':float(np.nanmedian(contrasts))}
        if not np.isclose(raw_cov,within_cov+between,atol=1e-12):
            raise AssertionError('decomposition failed')
        rows.append(row)
    if hashes!={str(p):sha(p) for p in files}:
        raise RuntimeError('input artifacts changed')
    table=pd.DataFrame(rows).sort_values('rank_identity_variance_fraction',ascending=False)
    table.to_csv(out/'profiles.csv',index=False)
    pd.DataFrame(group_rows).to_csv(out/'group_contrasts.csv',index=False)
    pd.DataFrame({'winner_frequency':winner.mean()/2,'loser_frequency':loser.mean()/2,
                  'mean_return_rank':y.mean()+.5625}).to_csv(out/'group_outcome_profile.csv')
    report=['# Registered-signal mechanism profile','',
            'Seen discovery only. No new candidate formula or certification.',
            f'{len(scores)} registered signals; {len(dates)} common dates: {dates.min().date()} to {dates.max().date()}; exits <= 2024-12-31.',
            'Group-fixed-effect means use the discovery sample only as a descriptive regression decomposition, never as signal input.',
            'Positive contrast counts describe associations, not independent tests or proof of conditional predictability.',
            '', '| Signal | Identity variance fraction | Within covariance | Positive group contrasts |',
            '|---|---:|---:|---:|']
    for r in table.to_dict('records'):
        report.append(f"| {r['candidate']} | {r['rank_identity_variance_fraction']:.3f} | {r['within_group_rank_covariance']:.5f} | {r['positive_within_group_contrasts']} / 8 |")
    report+=['','Reproduce: `'+ ' '.join(plan['command'])+'` (new run-id required).']
    (out/'REPORT.md').write_text('\n'.join(report)+'\n')
    print(table[['candidate','rank_identity_variance_fraction','within_group_rank_covariance','positive_within_group_contrasts']].to_string(index=False))
    print(f'Profile dates {len(dates)}: {dates.min()} -> {dates.max()}')


if __name__=='__main__':
    main()
