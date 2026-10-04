#!/usr/bin/env python3
"""Recompute leave-group ranks for frozen interactions; no new candidate search."""
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd
import yaml

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'frameworks/etf_rotation/src'))
from etf_strategy.core import etf_group_interactions as interaction
from etf_strategy.core.etf_mining_referee import newey_west_t_calendar


def main():
    run=ROOT/'runtime_outputs/etf_rotation_research/runs/group_interaction_v1_batch_20260922'
    plan=json.loads((run/'PLAN.json').read_text())
    cfg=plan['config']
    out=run/'loso_recomputed_v1'
    out.mkdir(exist_ok=False)
    groups=yaml.safe_load((run/'source/etf_candidate14_economic_groups_v1.yaml').read_text())['groups']
    labels=pd.read_csv(run/'group_labels.csv',index_col=0,parse_dates=True)
    metrics=pd.read_csv(run/'daily_metrics.csv',parse_dates=['signal_date'])
    raw,audits=interaction.load_parent_source(ROOT,groups,labels.index,cfg)
    rows=[]
    for name in plan['evaluated_ids']:
        complete=metrics.loc[metrics.candidate.eq(name)].set_index('signal_date').ic.notna()
        for omitted in groups:
            score=interaction.leave_group_score(raw,name.removesuffix('_1'),omitted)
            ic=score.rank(axis=1).corrwith(labels.drop(columns=omitted).rank(axis=1),axis=1)
            ic=ic.where(complete.reindex(ic.index,fill_value=False))
            rows.append({'candidate':name,'omitted_group':omitted,'n':int(ic.notna().sum()),
                         'ic_mean':float(ic.mean()),'ic_hac_t':newey_west_t_calendar(ic,labels.index,cfg['hac_lag'])})
    result=pd.DataFrame(rows)
    result.to_csv(out/'leave_group.csv',index=False)
    original=pd.read_csv(run/'summary.csv')
    minimum=result.groupby('candidate').ic_mean.min()
    passes=original.set_index('candidate').screen_pass
    # All already fail at least one other gate, so this correction cannot admit them.
    if not original.failed_screens.str.replace('leave_group','',regex=False).str.strip(',').ne('').all():
        raise ValueError('a candidate needs a fresh complete verdict, not just this annotation')
    payload={'scope':'FROZEN_CANDIDATE_DIAGNOSTIC_CORRECTION_NOT_NEW_SEARCH',
             'comparisons':len(result),'all_primary_failures_unchanged':True,
             'admitted_after_correction':int(passes.sum()),
             'recomputed_loso_minima':minimum.to_dict(),
             'source_sha256':hashlib.sha256(Path(interaction.__file__).read_bytes()).hexdigest(),
             'original_leave_group_csv':'evaluation-only deletion of already composed eight-group scores',
             'corrected_leave_group_csv':'remove group before recomputing both cross-sectional rank operators'}
    (out/'AUDIT.json').write_text(json.dumps(payload,indent=2)+'\n')
    (out/'source.py').write_text(Path(__file__).read_text())
    (out/'interaction_source.py').write_text(Path(interaction.__file__).read_text())
    print(json.dumps(payload,indent=2))


if __name__=='__main__':
    main()
