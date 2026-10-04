#!/usr/bin/env python3
"""Frozen eight-candidate group-structure discovery batch; seen history only."""
from __future__ import annotations

import argparse, hashlib, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / 'frameworks/etf_rotation'
sys.path.insert(0, str(ETF/'src'))
from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as engine
from etf_strategy.core.etf_mining_referee import newey_west_t_calendar


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating, float)): return float(x) if np.isfinite(x) else None
    if isinstance(x, np.bool_): return bool(x)
    return x


def write_json(path, value):
    path.write_text(json.dumps(clean(value), ensure_ascii=False, indent=2)+'\n')


def atoms(panels, groups, windows):
    ret = panels['close'].pct_change(fill_method=None)
    result = {}
    for w in windows:
        roll = ret.rolling(w, min_periods=w)
        # A group is scored only when every fixed member is available.  A
        # singleton has its own observable value; it is never dropped.
        for g, spec in groups.items():
            x = ret[spec['members']]
            signs = np.sign(x)
            breadth = signs.gt(0).mean(axis=1)
            agreement = signs.apply(lambda row: ((row.to_numpy()[:,None] * row.to_numpy()[None,:]) > 0).sum() / (len(row)**2), axis=1)
            absx = x.abs()
            shares = absx.div(absx.sum(axis=1).replace(0, np.nan), axis=0)
            hhi = (shares**2).sum(axis=1)
            # 0 is the neutral singleton convention, not a missing value.
            balance = -hhi if len(spec['members']) > 1 else pd.Series(0.0, index=x.index)
            # Winner counts over the window; ties split equally.
            maxx = x.eq(x.max(axis=1), axis=0).astype(float)
            entropy = maxx.rolling(w, min_periods=w).mean()
            ent = -(entropy * np.log(entropy.where(entropy > 0))).sum(axis=1)
            ent = ent / np.log(len(spec['members'])) if len(spec['members']) > 1 else pd.Series(0.0, index=x.index)
            for name, value in (('breadth', breadth.rolling(w, min_periods=w).mean()),
                                ('sign_agreement', agreement.rolling(w, min_periods=w).mean()),
                                ('contribution_balance', balance.rolling(w, min_periods=w).mean()),
                                ('leader_entropy', ent)):
                result.setdefault(f'{name}_{w}', {})[g] = value
    return {name: pd.DataFrame(values).reindex(panels['close'].index) for name, values in result.items()}


def leakage_check(panels, groups, windows, cutoff):
    full = atoms(panels, groups, windows)
    prefix_panels = {k: v.loc[:cutoff] for k, v in panels.items()}
    prefix = atoms(prefix_panels, groups, windows)
    mutated = {k: v.copy() for k, v in panels.items()}
    for v in mutated.values(): v.loc[v.index > pd.Timestamp(cutoff)] *= 1.71
    changed = atoms(mutated, groups, windows)
    for name in full:
        pd.testing.assert_frame_equal(full[name].loc[:cutoff], prefix[name], check_exact=False, rtol=1e-9, atol=1e-12)
        pd.testing.assert_frame_equal(full[name].loc[:cutoff], changed[name].loc[:cutoff], check_exact=False, rtol=1e-9, atol=1e-12)
    return {name: True for name in full}


def main():
    raise SystemExit(
        'RETIRED_AFTER_REVIEW: six designs are structurally invalid; breadth is redundant. '
        'Do not rerun this batch. Inspect group_next8_20260922_v4/MASTER_VERDICT.json '
        'and use the read-only breadth diagnostic. Frozen source snapshots are retained.'
    )
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-id', required=True)
    args = ap.parse_args()
    if not args.run_id.replace('_','').replace('-','').isalnum(): raise ValueError('invalid run id')
    cfg_path = ETF/'configs/group_next8_20260922.yaml'
    cfg = yaml.safe_load(cfg_path.read_text())
    universe_path = ROOT/cfg['universe']; groups_path = ROOT/cfg['groups']
    root = Path(cfg['data_root']).resolve()
    universe = json.loads(universe_path.read_text())
    symbols = [x['ts_code'] for x in universe['etfs'] if x['role']=='candidate']
    groups = yaml.safe_load(groups_path.read_text())['groups']
    engine.validate_groups(groups, symbols)
    calendar_path = root/'1d'/f"{cfg['calendar_symbol']}.parquet"
    files = ([root/'1d'/f'{s}.parquet' for s in symbols]
             + [root/'adj_factor'/f'{s}.parquet' for s in symbols]
             + [calendar_path])
    out = ROOT/'runtime_outputs/etf_rotation_research'/args.run_id
    out.mkdir(parents=True, exist_ok=False)
    sources = [Path(__file__), Path(engine.__file__), Path(ETF/'src/etf_strategy/canonical_data.py'), cfg_path, groups_path, universe_path]
    (out/'source').mkdir()
    for f in sources: shutil.copyfile(f, out/'source'/f.name)
    candidate_ids = [f'{m}_{w}' for w in cfg['windows'] for m in cfg['mechanisms']]
    inputs = {str(f): sha(f) for f in files}
    source_hashes = {str(f): sha(f) for f in sources}
    plan = {'created_utc': datetime.now(timezone.utc).isoformat(), 'config': cfg,
            'candidate_ids': candidate_ids, 'evaluated_ids': candidate_ids,
            'input_hashes': inputs, 'source_hashes': source_hashes,
            'surface_status':'PREVIOUSLY_SEEN_NOT_OOS', 'population':'fixed14_economic_groups_v1',
            'time_contract': {'signal':'close(D)', 'entry':'open(D+2)', 'exit':'open(D+7)', 'horizon':5},
            'primary_statistic':'signed eight-group cross-sectional rank IC', 'primary_benchmark':'B8',
            'mandatory_comparator':'B14', 'cumulative_budget_diagnostic':104,
            'prior_search_debt':'96 registered plus approximately 60 or more unregistered attempts; cumulative certification denominator unknown',
            'command':[sys.executable, *sys.argv]}
    write_json(out/'PLAN.json', plan)
    panels = load_canonical_daily(root, universe_path, as_of=cfg['as_of'], roles=('candidate',))
    cd = pd.read_parquet(calendar_path); calendar = pd.DatetimeIndex(pd.to_datetime(cd.trade_date)).sort_values()
    calendar = calendar[(calendar >= panels['close'].index.min()) & (calendar <= pd.Timestamp(cfg['as_of']))]
    panels = {k: v.reindex(calendar) for k,v in panels.items()}
    checks = {c: leakage_check(panels, groups, cfg['windows'], c) for c in ('2024-12-31','2025-12-31')}
    write_json(out/'future_leak_check.json', {'all_pass':True,'checks':checks,'scope':'causal feature construction; source vintage not certified'})
    known = panels['close'].notna().rolling(cfg['warmup']).sum().eq(cfg['warmup']).all(axis=1) & panels['volume'].gt(0).all(axis=1)
    labels, timing = engine.labels(panels, cfg['entry_lag'], cfg['horizon'])
    timing['known_complete'] = known; timing['labels_complete'] = labels.notna().all(axis=1); timing.to_csv(out/'coverage.csv', index=False)
    labels_by_group = engine.aggregate(labels, groups); labels_by_group.to_csv(out/'group_labels.csv', index_label='signal_date')
    atom_scores = atoms(panels, groups, cfg['windows'])
    eval_cal = calendar[calendar >= pd.Timestamp(cfg['evaluation_start'])]
    records=[]; summaries=[]; yearly=[]; loso=[]
    for name in candidate_ids:
        score=atom_scores[name]; frame, weights=engine.evaluate(score, labels, groups, known, timing, cfg['top_k']); frame=frame.loc[eval_cal]
        frame.insert(0,'candidate',name); records.append(frame); score.loc[eval_cal].to_csv(out/f'scores_{name}.csv',index_label='signal_date'); weights.loc[eval_cal].to_csv(out/f'weights_{name}.csv',index_label='signal_date')
        row={'candidate':name,**engine.summarize(frame,eval_cal,cfg['hac_lag'])}
        valid=frame.ic.notna(); row['first_signal']=str(frame.index[valid].min().date()) if valid.any() else None; row['last_signal']=str(frame.index[valid].max().date()) if valid.any() else None
        ys=[]
        for year in (2025,2026):
            part=frame.loc[frame.index.year==year].copy(); part.loc[part.exit_date.dt.year.ne(year),['ic','excess8','excess14','allocation_effect']]=np.nan
            y={'candidate':name,'year':year,**engine.summarize(part,part.index,cfg['hac_lag'])}; yearly.append(y)
            if y['n']>=cfg['screens']['min_year_days']: ys.append(y)
        row['positive_years']=sum(y['ic_mean']>0 for y in ys); row['all_eligible_years_positive']=bool(ys) and all(y['ic_mean']>0 for y in ys)
        means=[]
        for g in groups:
            ss=score.drop(columns=g).where(known,axis=0); yy=labels_by_group.drop(columns=g); ic=ss.rank(axis=1).corrwith(yy.rank(axis=1),axis=1).where(frame.ic.reindex(calendar).notna()); means.append(float(ic.mean())); loso.append({'candidate':name,'omitted_group':g,'ic_mean':float(ic.mean()),'ic_hac_t':newey_west_t_calendar(ic,calendar,cfg['hac_lag'])})
        row['min_leave_group_ic']=min(means)
        s=cfg['screens']; gates={'coverage':row['n']>=s['min_days'],'ic':row['ic_mean']>=s['min_ic'],'hac':row['ic_hac_t']>=s['min_ic_hac_t'],'block':row['ic_block_t']>=s['min_ic_block_t'],'budget_diagnostic':row['ic_p_normal_one_sided']<=s['alpha']/s['budget_diagnostic_denominator'],'economic':row['excess8_mean']>0 and row['excess8_hac_t']>=s['min_excess8_hac_t'],'years':row['all_eligible_years_positive'] and row['positive_years']>=s['min_positive_years'],'leave_group':row['min_leave_group_ic']>0}; row['screen_pass']=all(gates.values()); row['failed_screens']=','.join(k for k,v in gates.items() if not v); row['evidence_status']='LEAD_ONLY' if row['screen_pass'] else 'NOT_SUPPORTED_THIS_SCREEN'; summaries.append(row)
    pd.DataFrame(summaries).sort_values(['ic_hac_t','candidate'],ascending=[False,True]).to_csv(out/'summary.csv',index=False); pd.concat(records).to_csv(out/'daily_metrics.csv',index=False); pd.DataFrame(yearly).to_csv(out/'yearly.csv',index=False); pd.DataFrame(loso).to_csv(out/'leave_group.csv',index=False)
    verdict={'status':'DISCOVERY_ONLY','evaluated':8,'registered':8,'prior_registered':96,'budget_diagnostic_denominator':104,'shortlisted':[],'certified_factors':0,'source_vintage_audit':'NOT_CERTIFIED','external_shelf_check':'NOT_RUN','no_live_permission':True,'input_hashes_unchanged':{str(f):sha(f) for f in files}==inputs}
    write_json(out/'verdict.json',verdict)
    lines=['# Group next8 discovery report','','Seen history only; not independent OOS or trading permission.',f"Window: 2025-01-01 to {cfg['as_of']}; D+2 -> D+7; K=2; fixed14/8 groups.",'Primary statistic: signed eight-group rank IC; B8 primary economic benchmark; B14 mandatory comparator.','Four pre-registered mechanisms x two windows = 8 definitions; no interactions or post-result direction changes.','Budget diagnostic denominator is 104 (96 prior registered + 8); approximately 60 or more prior unregistered attempts remain unaccounted, so cumulative certification correction is not computable.','','| Candidate | N | IC | HAC t | B8 excess bp | B8 HAC t | Failed screens |','|---|---:|---:|---:|---:|---:|---|']
    for r in sorted(summaries,key=lambda x:(-x['ic_hac_t'],x['candidate'])): lines.append(f"| {r['candidate']} | {r['n']} | {r['ic_mean']:.4f} | {r['ic_hac_t']:.2f} | {r['excess8_mean']*1e4:.1f} | {r['excess8_hac_t']:.2f} | {r['failed_screens']} |")
    lines += ['', 'Certified factors: 0.', 'Evidence: PLAN.json, future_leak_check.json, coverage.csv, scores_*.csv, summary.csv, yearly.csv, leave_group.csv, source/.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(verdict,ensure_ascii=False))

if __name__ == '__main__': main()
