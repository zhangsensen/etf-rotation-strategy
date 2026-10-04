#!/usr/bin/env python3
"""Monthly walk-forward simulation (2026-09-24) over all saved group-score panels: each month select top-k by trailing |t| (labels matured), sign by t, evaluate next month (K=2 groups, 5-day rebalance, costs). Library composition is still contaminated by full-window knowledge, so results are an optimistic bound, not clean OOS."""
import sys, glob, yaml, numpy as np, pandas as pd
from pathlib import Path
ROOT=Path(str(Path(__file__).resolve().parents[4])); sys.path.insert(0,str(ROOT/'frameworks/etf_rotation/src'))
from etf_strategy.canonical_data import load_canonical_daily
from etf_strategy.core import etf_group_discovery as engine
from etf_strategy.core.etf_rank_utils import stable_rank
R=ROOT/'runtime_outputs/etf_rotation_research/runs'
groups=yaml.safe_load((ROOT/'frameworks/etf_rotation/configs/etf_candidate14_economic_groups_v1.yaml').read_text())['groups']
root=Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1")); uni=ROOT/'config/etf_rotation_universe_v1.json'
panels=load_canonical_daily(root,uni,as_of='2026-09-17',roles=('candidate',))
cal=pd.DatetimeIndex(pd.to_datetime(pd.read_parquet(root/'1d/510300.SH.parquet').trade_date)).sort_values()
cal=cal[(cal>=panels['close'].index.min())&(cal<=pd.Timestamp('2026-09-17'))]; panels={k:p.reindex(cal) for k,p in panels.items()}
mlab,_=engine.labels(panels,2,5); glab=engine.aggregate(mlab,groups)
ev=cal[cal>=pd.Timestamp('2025-01-01')]
P={}
for f in glob.glob(str(R/'*/scores_*.csv')):
    n=Path(f).name[7:-4]
    if n in P: continue
    try: s=pd.read_csv(f,index_col=0,parse_dates=True).reindex(ev)
    except Exception: continue
    if s.shape[1]!=8 or s.notna().all(axis=1).mean()<0.9: continue
    P[n]=stable_rank(s).to_numpy()
names=list(P); A=np.stack([P[n] for n in names]); T=len(ev)
QDII={'513100.SH','513130.SH','513120.SH'}; gcost=np.array([np.mean([0.005 if m in QDII else 0.002 for m in v['members']]) for v in groups.values()])
def rowcorr(a,b):
    a=a-np.nanmean(a,axis=-1,keepdims=True); b=b-np.nanmean(b,axis=-1,keepdims=True)
    return np.nansum(a*b,axis=-1)/np.sqrt(np.nansum(a*a,axis=-1)*np.nansum(b*b,axis=-1))
def topk_w(comp,k=2):
    w=np.zeros_like(comp); 
    for i,row in enumerate(comp):
        if np.isnan(row).any(): w[i]=np.nan; continue
        idx=np.argsort(-row)[:k]; w[i,idx]=1/k
    return w
def wfo(Lr,Lret,k_fac,min_train=120,label_lag=7):
    """Each month M: train on days < first day of M minus label_lag (labels matured), select top-k by |t|, sign by t; evaluate on M."""
    months=pd.PeriodIndex(ev,freq='M'); out=[]
    for m in months.unique():
        test=np.where(months==m)[0]; start=test[0]
        tr_end=start-label_lag
        if tr_end<min_train: continue
        ic=rowcorr(A[:,:tr_end],Lr[None,:tr_end]); mu=np.nanmean(ic,axis=1); sd=np.nanstd(ic,axis=1); n=np.sum(~np.isnan(ic),axis=1); t=mu/(sd/np.sqrt(n))
        t=np.where(n>=60,t,np.nan); sel=np.argsort(-np.abs(np.nan_to_num(t)))[:k_fac]; sign=np.sign(t[sel])
        comp=np.nanmean(A[sel][:,test]*sign[:,None,None],axis=0); oos_ic=rowcorr(comp,Lr[test])
        days=test[::5]; W=topk_w(comp[::5]); ret=np.nansum(W*Lret[days],axis=1); b8=np.nanmean(Lret[days],axis=1)
        to=np.abs(np.diff(np.vstack([np.zeros(8),np.nan_to_num(W)]),axis=0)); cost=(to*gcost).sum(axis=1); net=ret-cost
        out.append(dict(month=str(m),n=len(test),oos_ic=np.nanmean(oos_ic),exc_net_b8=np.nanmean(net-b8),sel=[names[i] for i in sel]))
    return pd.DataFrame(out)
Lr=glab.reindex(ev).rank(axis=1).to_numpy(); Lret=glab.reindex(ev).to_numpy()
for k in (2,5,15):
    d=wfo(Lr,Lret,k); ic=d.oos_ic; e=d.exc_net_b8
    print(f"k={k:2d} months={len(d)} OOS IC mean {ic.mean():.4f} t {ic.mean()/ic.std()*np.sqrt(len(ic)):.2f} | pos months {(ic>0).mean():.2f} | net exc vs B8 {e.mean()*1e4:.1f} bp/rebal t {e.mean()/e.std()*np.sqrt(len(e)):.2f}")
    if k==2: print(d[['month','oos_ic','exc_net_b8','sel']].to_string(index=False))
print("== null: block-shuffled labels (both rank & return labels shuffled identically), k=5 ==")
rng=np.random.default_rng(1); res=[]
for b in range(30):
    idx=np.concatenate([blk for blk in (lambda bl: (rng.shuffle(bl), bl)[1])([np.arange(i,min(i+20,T)) for i in range(0,T,20)])])
    d=wfo(Lr[idx],Lret[idx],5); res.append(d.oos_ic.mean())
res=np.array(res); print(f"null OOS IC mean {res.mean():.4f} sd {res.std():.4f} max {res.max():.4f}")
