"""Complete-day intraday mechanism hypotheses. No cross-day raw price joins."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from .etf_intraday_factor_space import _read_complete_days


def day_mechanisms(day):
    p = day['close'].to_numpy(float)
    high, low = day['high'].to_numpy(float), day['low'].to_numpy(float)
    amount = day['turnover'].to_numpy(float)
    r = np.diff(np.log(np.r_[float(day['open'].iloc[0]), p]))
    n = len(r)
    rv = np.square(r).sum()
    bv = np.pi/2 * np.sum(np.abs(r[1:])*np.abs(r[:-1])) * n/(n-1)
    active = np.mean(r != 0) >= .6
    valid_weights = np.isfinite(amount).all() and (amount >= 0).all() and amount.sum() > 0
    weights = amount/amount.sum() if valid_weights else np.full(n, np.nan)
    typical = (high+low+p)/3
    order = np.argsort(typical)
    cdf = np.cumsum(weights[order])
    def quantile(q):
        return typical[order][min(np.searchsorted(cdf, q), n-1)]
    variation_share = max(0, (rv-bv)/rv) if active and rv > 0 else np.nan
    values = {
        'JUMP_VARIATION_SHARE': variation_share,
        'EXTREME_TIME_ORDER': (np.argmax(high)-np.argmin(low))/(n-1) if high.max() > low.min() else np.nan,
        'CLOSE_TRADED_PRICE_PERCENTILE': weights[typical < p[-1]].sum() if valid_weights else np.nan,
        'TRADED_PRICE_WIDTH': (quantile(.85)-quantile(.15))/np.dot(weights, typical) if valid_weights else np.nan,
    }
    return values, r, weights


def build_intraday_breadth_v3(data_root, symbols, as_of, peer_symbols, daily_eligibility):
    records = {}; paths = {}; profiles = {}; volprofiles = {}
    for symbol in symbols:
        frame, _ = _read_complete_days(Path(data_root), symbol, '5m', as_of)
        frame['date'] = pd.to_datetime(frame['datetime']).dt.normalize()
        rows = {}; returns = {}; weights = {}; vweights = {}
        for date, day in frame.groupby('date', sort=True):
            if not (day['high'].ge(day[['open', 'close']].max(axis=1)).all()
                    and day['low'].le(day[['open', 'close']].min(axis=1)).all()):
                continue
            values, r, w = day_mechanisms(day)
            rows[date] = values; returns[date] = r; weights[date] = w
            vweights[date] = np.abs(r)/np.abs(r).sum() if np.abs(r).sum() > 0 else np.full(len(r), np.nan)
        records[symbol] = pd.DataFrame.from_dict(rows, orient='index')
        paths[symbol] = pd.DataFrame.from_dict(returns, orient='index').reindex(columns=range(48))
        profiles[symbol] = pd.DataFrame.from_dict(weights, orient='index').reindex(columns=range(48))
        volprofiles[symbol] = pd.DataFrame.from_dict(vweights, orient='index').reindex(columns=range(48))
    names = ['JUMP_VARIATION_SHARE','EXTREME_TIME_ORDER','CLOSE_TRADED_PRICE_PERCENTILE','TRADED_PRICE_WIDTH']
    out = {k:pd.DataFrame({s:records[s][k] if k in records[s] else pd.Series(dtype=float) for s in symbols}) for k in names}
    for key, collection in [('TURNOVER_PROFILE_DISTANCE',profiles), ('VOL_PROFILE_DISTANCE',volprofiles)]:
        out[key] = pd.DataFrame({s: (v-v.shift(1).rolling(20, min_periods=20).mean()).abs().sum(axis=1, min_count=48)/2 for s,v in collection.items()})
    systematic = pd.DataFrame(np.nan,index=daily_eligibility.index,columns=symbols)
    for symbol in peer_symbols:
        own = paths[symbol]
        others = [p for p in peer_symbols if p != symbol]
        # Every bar uses only eligible complete-day peers; minimum four peers.
        aligned = []
        for peer in others:
            frame = paths[peer].reindex(own.index)
            frame = frame.where(daily_eligibility[peer].reindex(own.index).fillna(False),axis=0)
            aligned.append(frame.to_numpy())
        if not len(own):
            continue
        a = np.stack(aligned)
        counts = np.isfinite(a).sum(axis=0)
        mean = np.divide(np.nansum(a,axis=0),counts,out=np.full_like(a[0],np.nan),where=counts>=4)
        x = own.to_numpy(); xc = x-x.mean(axis=1,keepdims=True); mc = mean-mean.mean(axis=1,keepdims=True)
        denom = np.sqrt(np.square(xc).sum(axis=1)*np.square(mc).sum(axis=1))
        corr = np.divide((xc*mc).sum(axis=1),denom,out=np.full(len(x),np.nan),where=denom>1e-15)
        corr[np.mean(x!=0,axis=1)<.6] = np.nan
        systematic[symbol] = pd.Series(corr**2, index=own.index).reindex(systematic.index)
    out['INTRADAY_PEER_R2'] = systematic
    return {k:v.sort_index().replace([np.inf,-np.inf],np.nan) for k,v in out.items()}
