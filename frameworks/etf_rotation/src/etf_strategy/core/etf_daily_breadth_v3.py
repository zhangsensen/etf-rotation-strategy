"""D-close ETF mechanism hypotheses; no labels and no forward imputation."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _div(x, y):
    return x / y.replace(0, np.nan)


def _longest(a):
    best = run = 0
    for x in a:
        run = run + 1 if x else 0
        best = max(best, run)
    return best / len(a)


def _swing(a):
    # Input is a trailing log-price window. Threshold frozen for this window.
    threshold = 1.5 * np.std(np.diff(a), ddof=1)
    if not np.isfinite(threshold) or threshold <= 1e-12:
        return np.nan
    high = low = a[0]
    direction = count = 0
    for value in a[1:]:
        high, low = max(high, value), min(low, value)
        if direction >= 0 and high - value >= threshold:
            count += 1
            direction, low = -1, value
        elif direction <= 0 and value - low >= threshold:
            count += 1
            direction, high = 1, value
    return count / len(a)


def build_daily_breadth_v3(panels):
    c, o, h, l = (panels[k] for k in ('close', 'open', 'high', 'low'))
    r = c.pct_change(fill_method=None)
    span = (h-l)/c
    amount = panels['amount'].where(panels['amount'] > 0)
    typical = (h+l+c)/3  # adjusted price proxy, NOT amount/volume VWAP
    out = {}
    gap = o/c.shift(1)-1
    fill = ((o-l)/(o-c.shift(1))).where(gap > 0, (h-o)/(c.shift(1)-o)).clip(0, 1)
    event = gap.abs().gt(.003).where(gap.notna())
    prior = r.shift(1)
    for w in (20, 60):
        vol_change = np.log(span.where(span > 0)).diff()
        out[f'LEVERAGE_CORR_{w}'] = prior.rolling(w).corr(vol_change).where(vol_change.rolling(w).std() > 1e-12)
        neg, pos = prior.lt(0).where(prior.notna()), prior.gt(0).where(prior.notna())
        nneg, npos = neg.rolling(w).sum(), pos.rolling(w).sum()
        dn = span.where(prior < 0, 0).where(prior.notna()).rolling(w).sum()/nneg.where(nneg >= 5)
        up = span.where(prior > 0, 0).where(prior.notna()).rolling(w).sum()/npos.where(npos >= 5)
        out[f'VOL_RESPONSE_ASYMMETRY_{w}'] = _div(dn, up)
        underwater = c.lt(c.rolling(60).max() * .995).where(c.rolling(60).count().eq(60))
        if w == 60:  # 20-session run is redundant with underwater fraction.
            out[f'UNDERWATER_RUN_{w}'] = underwater.rolling(w).apply(_longest, raw=True)
        out[f'UNDERWATER_FRACTION_{w}'] = underwater.rolling(w).mean()
        out[f'SWING_COUNT_{w}'] = np.log(c).rolling(w).apply(_swing, raw=True)
        events = event.rolling(w).sum()
        out[f'GAP_FILL_FRACTION_{w}'] = fill.where(event.eq(1), 0).where(gap.notna()).rolling(w).sum()/events.where(events >= 5)
        # Per-symbol traded-price memory uses adjusted typical prices with turnover weights.
        overhead = pd.DataFrame(np.nan, index=c.index, columns=c.columns)
        median_distance = overhead.copy()
        for symbol in c:
            prices, weights, closes = typical[symbol].to_numpy(), amount[symbol].to_numpy(), c[symbol].to_numpy()
            for t in range(w-1, len(c)):
                p, a = prices[t-w+1:t+1], weights[t-w+1:t+1]
                if not (np.isfinite(p).all() and np.isfinite(a).all() and np.isfinite(closes[t])):
                    continue
                order = np.argsort(p)
                median = p[order][np.searchsorted(np.cumsum(a[order]), a.sum()/2)]
                overhead.loc[c.index[t], symbol] = a[p > closes[t]].sum()/a.sum()
                median_distance.loc[c.index[t], symbol] = closes[t]/median-1
        out[f'OVERHEAD_TURNOVER_{w}'] = overhead
        out[f'TRADED_MEDIAN_DISTANCE_{w}'] = median_distance
    return {k:v.replace([np.inf, -np.inf], np.nan) for k,v in out.items()}


def build_macro_sensitivity(panels, eligibility, config):
    r = panels['close'].pct_change(fill_method=None).where(eligibility)
    market = r[list(config['benchmark_symbols'])].mean(axis=1, skipna=False)
    out = {}
    for hedge in config['hedge_symbols']:
        for w in (20, 60):
            # Partial correlation after conditioning on the equity reference.
            am = r.rolling(w).corr(market)
            ah = r.rolling(w).corr(r[hedge])
            hm = r[hedge].rolling(w).corr(market)
            numerator = ah.sub(am.mul(hm, axis=0))
            denominator = np.sqrt((1-am.pow(2)).mul(1-hm.pow(2), axis=0))
            v = numerator/denominator.where(denominator > 1e-10)
            v[hedge] = np.nan  # self-sensitivity is undefined as a factor
            out[f'{config["hedge_symbols"][hedge]}_PARTIAL_CORR_{w}'] = v.clip(-1, 1)
    return out


def build_turnover_allocation(panels, eligibility, config):
    amount = panels['amount'].where(eligibility & panels['amount'].gt(0))
    peers = list(config['peer_symbols'])
    out = {}
    for w in (20, 60):
        change = pd.DataFrame(np.nan, index=amount.index, columns=peers)
        for t in range(w - 1, len(amount)):
            window = amount[peers].iloc[t-w+1:t+1]
            # Recompute ALL historical denominators on D's trailing complete
            # cohort. Rolling a changing denominator only delays entry spikes.
            cohort = window.columns[np.isfinite(window).all()]
            if len(cohort) < 5:
                continue
            history = window[cohort]
            shares = history.div(history.sum(axis=1), axis=0)
            change.loc[amount.index[t], cohort] = shares.iloc[-1] - shares.mean()
        out[f'POOL_TURNOVER_SHARE_CHANGE_{w}'] = change
    return out
