#!/usr/bin/env python3
"""Research prototype (2026-09-24): assemble HAS_IC group factors into a K=2 / 5-day rotation on the fixed 14 ETF / 8 group frame.

IN-SAMPLE ONLY. All factors were selected on this same 2025+ window; the block-shuffle calibration at the bottom shows a top-15-by-t composite from noise reaches IC ~0.21, so the in-sample composite IC/return here is not evidence. Use only as the assembly recipe for forward (monthly factory) selections.
"""
import sys, json, yaml, csv, numpy as np, pandas as pd
from pathlib import Path
ROOT=Path(str(Path(__file__).resolve().parents[4])); sys.path.insert(0,str(ROOT/'frameworks/etf_rotation/src'))
from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as engine
from etf_strategy.core.etf_rank_utils import stable_rank
from etf_strategy.core.etf_mining_referee import fractional_topk_weights
R=ROOT/'runtime_outputs/etf_rotation_research/runs'
inv=ROOT/'runtime_outputs/etf_rotation_research/ic_inventory_20260923_claude_10rounds/all_factors.csv'
groups=yaml.safe_load((ROOT/'frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml').read_text())['groups']
uni=ROOT/'config/etf_rotation_universe_v1.json'; root=Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))
panels=load_canonical_daily(root,uni,as_of='2026-09-17',roles=('candidate',))
cal=pd.DatetimeIndex(pd.to_datetime(pd.read_parquet(root/'1d/510300.SH.parquet').trade_date)).sort_values()
cal=cal[(cal>=panels['close'].index.min())&(cal<=pd.Timestamp('2026-09-17'))]
panels={k:p.reindex(cal) for k,p in panels.items()}
mlab,timing=engine.labels(panels,2,5); glab=engine.aggregate(mlab,groups)
ev=cal[(cal>=pd.Timestamp('2025-01-01'))]
has=[x for x in csv.DictReader(open(inv)) if x['status']=='HAS_IC']
S={}
for x in has:
    p=R/x['source_run']/f"scores_{x['candidate']}.csv"
    if not p.exists(): print('missing',x['candidate']); continue
    s=pd.read_csv(p,index_col=0,parse_dates=True).reindex(ev)
    ic=stable_rank(s).corrwith(glab.reindex(ev).rank(axis=1),axis=1)
    m=ic.mean(); 
    if m<0: s=-s; print('flipped',x['candidate'],round(m,3))
    S[x['candidate']]=s
print('factors',len(S))
QDII={'513100.SH','513130.SH','513120.SH'}
cost_member={m:(0.005 if m in QDII else 0.002) for g in groups.values() for m in g['members']}
gcost=pd.Series({g:np.mean([cost_member[m] for m in v['members']]) for g,v in groups.items()})
def composite(names, how='rank'):
    ranks=[stable_rank(S[n],pct=True) for n in names]
    return sum(ranks)/len(ranks)
def run(names,label,k=2,freq=5,hyst=False):
    comp=composite(names); L=glab.reindex(ev)
    ic=comp.corrwith(L.rank(axis=1),axis=1)
    x=ic.dropna().values; mu=x.mean(); xc=x-mu; n=len(x); s=xc@xc/n
    for j in range(1,11): s+=2*(1-j/11)*(xc[j:]@xc[:-j]/n)
    t=mu/np.sqrt(s/n)
    # strategy: rebalance every `freq` days on signal days; hold group labels (open D+2 -> open D+7)
    days=ev[::freq]; W=fractional_topk_weights(comp.loc[days],k,min_names=8)/k
    complete=L.loc[days].notna().all(axis=1)&comp.loc[days].notna().all(axis=1)
    W=W.where(complete); ret=(W*L.loc[days]).sum(axis=1).where(complete)
    b8=L.loc[days].mean(axis=1).where(complete); b14=mlab.reindex(days).mean(axis=1).where(complete)
    to=(W.fillna(0).diff().abs()); to.iloc[0]=W.fillna(0).iloc[0].abs()
    cost=(to*gcost).sum(axis=1).where(complete)   # one-way cost per unit weight change, both sides counted via abs diff (buy+sell)
    net=ret-cost
    def ann(r): r=r.dropna(); return (1+r).prod()**(252/(len(r)*freq))-1
    def per(r): r=r.dropna(); return r.mean()*1e4, r.mean()/r.std()*np.sqrt(len(r)) if len(r)>1 else np.nan
    out={'label':label,'n_factors':len(names),'IC':round(mu,4),'IC_t':round(t,2),'n_days':n,
         'gross_ann':round(ann(ret),3),'net_ann':round(ann(net),3),'B8_ann':round(ann(b8),3),'B14_ann':round(ann(b14),3),
         'excess_net_vs_B8_bp_per_rebal':round(per(net-b8)[0],1),'t_excess_net_vs_B8':round(per(net-b8)[1],2),
         'excess_net_vs_B14_bp':round(per(net-b14)[0],1),'turnover_per_rebal':round(to.sum(axis=1).where(complete).mean(),2),
         'cost_ann':round(cost.mean()*252/freq,3)}
    for y in (2025,2026):
        m=(net.index.year==y); out[f'excess_net_vs_B8_{y}_bp']=round((net-b8)[m].mean()*1e4,1); out[f'IC_{y}']=round(ic[ic.index.year==y].mean(),3)
    return out, (W,ret,net,b8,b14)
allf=list(S); top3=['market_residual_abs_cluster_20','market_coskewness_20','beta_asymmetry_60']
claude3=['beta_asymmetry_60','peer_corr_network_change_60','weekday_relative_return_pattern_60']
rows=[]
for names,label in [(allf,'ALL_HAS_IC'),(top3,'TOP3_by_t'),(claude3,'CLAUDE3'),(['market_residual_abs_cluster_20'],'MRAC_only')]:
    o,_=run(names,label); rows.append(o)
df=pd.DataFrame(rows).set_index('label'); pd.set_option('display.width',250); print(df.T.to_string())
# factor-composite dispersion: pairwise IC-series corr among all
ICs=pd.DataFrame({n:stable_rank(S[n]).corrwith(glab.reindex(ev).rank(axis=1),axis=1) for n in allf})
ev_=np.linalg.eigvalsh(ICs.corr().fillna(0).values)[::-1]; print('effective N of',len(allf),'factors:',round(ev_.sum()**2/(ev_**2).sum(),2))

print("\n== common-day comparison (days where all 15 factors valid) ==")
common=pd.concat([S[n].notna().all(axis=1) for n in allf],axis=1).all(axis=1)
ev2=ev[common.reindex(ev).fillna(False).values]
def run2(names,label,k=2,freq=5):
    comp=composite(names).reindex(ev2); L=glab.reindex(ev2)
    days=ev2[::freq]; W=fractional_topk_weights(comp.loc[days],k,min_names=8)/k
    ok=L.loc[days].notna().all(axis=1)&comp.loc[days].notna().all(axis=1); W=W.where(ok)
    ret=(W*L.loc[days]).sum(axis=1).where(ok); b8=L.loc[days].mean(axis=1).where(ok); b14=mlab.reindex(days).mean(axis=1).where(ok)
    to=W.fillna(0).diff().abs(); to.iloc[0]=W.fillna(0).iloc[0].abs(); net=ret-(to*gcost).sum(axis=1).where(ok)
    d=(net-b8).dropna(); return dict(label=label, n_rebal=len(d), gross_ann=round((1+ret.dropna()).prod()**(252/(len(ret.dropna())*freq))-1,3), net_ann=round((1+net.dropna()).prod()**(252/(len(net.dropna())*freq))-1,3), B8_ann=round((1+b8.dropna()).prod()**(252/(len(b8.dropna())*freq))-1,3), B14_ann=round((1+b14.dropna()).prod()**(252/(len(b14.dropna())*freq))-1,3), exc_net_B8_bp=round(d.mean()*1e4,1), t=round(d.mean()/d.std()*np.sqrt(len(d)),2), maxDD_net=round(((1+net.fillna(0)).cumprod()/(1+net.fillna(0)).cumprod().cummax()-1).min(),3))
print(pd.DataFrame([run2(allf,'ALL15'),run2(top3,'TOP3'),run2(claude3,'CLAUDE3')]).set_index('label').T.to_string())

print("\n== selection-bias calibration: top-15-by-|t| composite from ALL saved score panels, real vs block-shuffled labels ==")
import glob
panels_s={}
for f in glob.glob(str(R/'*/scores_*.csv')):
    name=Path(f).name[7:-4]
    if name in panels_s: continue
    try: s=pd.read_csv(f,index_col=0,parse_dates=True).reindex(ev2)
    except Exception: continue
    if s.shape[1]!=8 or s.notna().all(axis=1).mean()<0.9: continue
    panels_s[name]=stable_rank(s).to_numpy()
names=list(panels_s); A=np.stack([panels_s[n] for n in names])  # F x T x 8
print('score panels usable:',len(names))
Lr=glab.reindex(ev2).rank(axis=1).to_numpy()
def rowcorr(a,b):
    a=a-np.nanmean(a,axis=-1,keepdims=True); b=b-np.nanmean(b,axis=-1,keepdims=True)
    return np.nansum(a*b,axis=-1)/np.sqrt(np.nansum(a*a,axis=-1)*np.nansum(b*b,axis=-1))
def topk_composite_ic(Lr,k=15):
    ic=rowcorr(A,Lr[None])            # F x T
    mu=np.nanmean(ic,axis=1); sd=np.nanstd(ic,axis=1); n=np.sum(~np.isnan(ic),axis=1); t=mu/(sd/np.sqrt(n))
    sel=np.argsort(-np.abs(t))[:k]; sign=np.sign(t[sel])
    comp=np.nanmean(A[sel]*sign[:,None,None],axis=0)   # composite of signed ranks
    cic=rowcorr(comp,Lr); return np.nanmean(cic), np.nanmean(np.abs(t[sel]))
real=topk_composite_ic(Lr); print('REAL: top15 composite IC',round(real[0],4),'mean|t| of selected',round(real[1],2))
rng=np.random.default_rng(0); T=Lr.shape[0]; B=40; res=[]
for b in range(B):
    blocks=[Lr[i:i+20] for i in range(0,T,20)]; rng.shuffle(blocks); Ls=np.concatenate(blocks)[:T]
    res.append(topk_composite_ic(Ls)[0])
res=np.array(res); print(f'NULL (block-shuffled labels, B={B}): composite IC mean {res.mean():.4f}, sd {res.std():.4f}, max {res.max():.4f}')
