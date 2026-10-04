"""ETF peer dependence, with D-known eligibility and self exclusion."""
from __future__ import annotations

import numpy as np
import pandas as pd


def build_dependence_space(panels, eligibility, peer_symbols):
    close = panels['close']
    peers = list(peer_symbols)
    if len(peers) < 5 or len(set(peers)) != len(peers) or not set(peers) <= set(close):
        raise ValueError('At least five distinct configured peers required')
    returns = close.pct_change(fill_method=None).where(eligibility)
    # Thresholds are lagged, so a shock cannot redefine its own tail boundary.
    threshold = returns.rolling(60, min_periods=40).quantile(.15).shift(1)
    tails = returns.lt(threshold).where(returns.notna() & threshold.notna())
    result = {}
    for window in (20, 60):
        network = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
        joint_tail = network.copy()
        for symbol in peers:
            others = [p for p in peers if p != symbol]
            correlations = pd.concat([
                returns[symbol].rolling(window, min_periods=window).corr(returns[p])
                for p in others
            ], axis=1)
            network[symbol] = correlations.abs().mean(axis=1).where(correlations.count(axis=1) >= 4)
            conditional = []
            for peer in others:
                valid = tails[symbol].notna() & tails[peer].notna()
                events = tails[peer].where(valid).rolling(window, min_periods=window).sum()
                joint = (tails[symbol].astype(float) * tails[peer].astype(float)).where(valid)
                conditional.append(joint.rolling(window, min_periods=window).sum() / events.where(events >= 3))
            frame = pd.concat(conditional, axis=1)
            joint_tail[symbol] = frame.mean(axis=1).where(frame.count(axis=1) >= 4)
        if window == 20:  # 60-session connectivity duplicates the PC1 loading.
            result[f'PEER_ABS_CONNECTIVITY_{window}'] = network
        result[f'PEER_TAIL_CONDITIONAL_{window}'] = joint_tail
    return result


def build_systemic_loading(panels, eligibility, peer_symbols):
    close = panels['close']
    r = close[list(peer_symbols)].pct_change(fill_method=None).where(eligibility[list(peer_symbols)])
    loading = pd.DataFrame(np.nan,index=close.index,columns=close.columns)
    for t in range(59,len(r)):
        window = r.iloc[t-59:t+1]
        selected = window.columns[window.notna().all() & window.std().gt(1e-12)]
        if len(selected)<5:
            continue
        corr = window[selected].corr().to_numpy()
        eigenvalues, vectors = np.linalg.eigh(corr)
        loading.loc[r.index[t],selected] = eigenvalues[-1]*vectors[:,-1]**2
    return {'SYSTEMIC_VARIANCE_SHARE_60':loading.clip(0,1)}
