"""Fixed-pool OHLCV atoms proposed for ETF IC rounds 41--45.

All outputs are member-by-date scores with the pre-label direction applied.
The module deliberately requires the fixed 14-member pool for peer formulas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from .etf_rank_utils import stable_rank


WINDOW = 20
DIRECTIONS = {
    "l41_peer_amount_to_return_beta": 1,
    "l41_peer_amount_return_correlation": 1,
    "l41_peer_amount_shock_response_asymmetry": 1,
    "l41_peer_flow_reversal_beta": -1,
    "l42_peer_liquidity_adjusted_return": 1,
    "l42_peer_flow_impact_spread": 1,
    "l42_amount_neutral_peer_response": 1,
    "l42_peer_flow_impact_instability": -1,
    "l43_peer_amount_inflow_breadth": 1,
    "l43_peer_amount_inflow_disagreement": -1,
    "l43_peer_flow_breadth_change": 1,
    "l43_peer_flow_dispersion_change": -1,
    "l44_peer_flow_rank_persistence": 1,
    "l44_peer_return_flow_confirmation": 1,
    "l44_peer_flow_lead_confirmation": 1,
    "l44_peer_flow_rank_reversal": -1,
    "l45_peer_flow_lagged_correlation": 1,
    "l45_peer_flow_directional_consensus": 1,
    "l45_peer_flow_shock_catchup": 1,
    "l45_peer_flow_shock_divergence": -1,
}


def _complete(mask: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    return mask.astype(float).rolling(window, min_periods=window).sum().eq(window)


def _mean(frame: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    return frame.rolling(window, min_periods=window).mean().where(
        _complete(frame.notna(), window)
    )


def _rolling_cov(x: pd.DataFrame, y: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    valid = x.notna() & y.notna()
    xm = x.rolling(window, min_periods=window).mean()
    ym = y.rolling(window, min_periods=window).mean()
    cov = (x * y).rolling(window, min_periods=window).mean() - xm * ym
    return cov.where(_complete(valid, window))


def _beta(y: pd.DataFrame, x: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    cov = _rolling_cov(x, y, window)
    var = x.rolling(window, min_periods=window).var(ddof=0).where(
        _complete(x.notna(), window)
    )
    return cov.div(var.where(var.gt(0.0)))


def _corr(x: pd.DataFrame, y: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    cov = _rolling_cov(x, y, window)
    sx = x.rolling(window, min_periods=window).std(ddof=0)
    sy = y.rolling(window, min_periods=window).std(ddof=0)
    return cov.div((sx * sy).where((sx * sy).gt(0.0)))


def _peer_mean(frame: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-out mean over the other 13 members; fail closed on missing peers."""
    values = frame.to_numpy(dtype=float)
    out = np.full(values.shape, np.nan, dtype=float)
    for j in range(values.shape[1]):
        others = np.delete(values, j, axis=1)
        valid = np.isfinite(others).all(axis=1)
        out[valid, j] = others[valid].mean(axis=1)
    return pd.DataFrame(out, index=frame.index, columns=frame.columns)


def _peer_std(frame: pd.DataFrame) -> pd.DataFrame:
    values = frame.to_numpy(dtype=float)
    out = np.full(values.shape, np.nan, dtype=float)
    for j in range(values.shape[1]):
        others = np.delete(values, j, axis=1)
        valid = np.isfinite(others).all(axis=1)
        out[valid, j] = others[valid].std(axis=1, ddof=0)
    return pd.DataFrame(out, index=frame.index, columns=frame.columns)


def _conditional_mean(
    value: pd.DataFrame, condition: pd.DataFrame, min_count: int = 4,
    window: int = WINDOW,
    pair_valid: pd.DataFrame | None = None,
) -> pd.DataFrame:
    valid = value.notna() & condition
    if pair_valid is not None:
        valid &= pair_valid
        complete_pairs = _complete(pair_valid, window)
    else:
        complete_pairs = _complete(value.notna(), window)
    numerator = value.where(valid).rolling(window, min_periods=1).sum()
    count = valid.astype(int).rolling(window, min_periods=1).sum()
    return numerator.div(count.where(count.ge(min_count))).where(complete_pairs)


def _state_beta(y: pd.DataFrame, x: pd.DataFrame, state: pd.DataFrame) -> pd.DataFrame:
    valid = x.notna() & y.notna() & state
    n = valid.astype(int).rolling(WINDOW, min_periods=1).sum()
    xm = x.where(valid).rolling(WINDOW, min_periods=1).mean()
    ym = y.where(valid).rolling(WINDOW, min_periods=1).mean()
    cov = (x * y).where(valid).rolling(WINDOW, min_periods=1).mean() - xm * ym
    var = x.where(valid).rolling(WINDOW, min_periods=1).var(ddof=0)
    return cov.div(var.where((var.gt(0.0)) & (n.ge(4)))).where(
        _complete(x.notna() & y.notna(), WINDOW)
    )


def _partial_beta(y: pd.DataFrame, x: pd.DataFrame, z: pd.DataFrame) -> pd.DataFrame:
    """Slope of x in a rolling OLS with intercept and control z; singular fits are NaN."""
    valid = x.notna() & y.notna() & z.notna()
    n = valid.astype(float).rolling(WINDOW, min_periods=WINDOW).sum()

    def moment(v: pd.DataFrame) -> pd.DataFrame:
        return v.where(valid).rolling(WINDOW, min_periods=WINDOW).mean()

    mx, my, mz = moment(x), moment(y), moment(z)
    vx = moment(x * x) - mx * mx
    vz = moment(z * z) - mz * mz
    cxz = moment(x * z) - mx * mz
    cxy = moment(x * y) - mx * my
    czy = moment(z * y) - mz * my
    det = vx * vz - cxz * cxz
    slope = (cxy * vz - czy * cxz).div(det.where(det.gt(0.0)))
    tolerance = 1e-12 * vx.abs() * vz.abs()
    nonsingular = vx.gt(0.0) & vz.gt(0.0) & det.gt(tolerance)
    return slope.where(n.eq(WINDOW) & nonsingular)


def _instability(y: pd.DataFrame, x: pd.DataFrame) -> pd.DataFrame:
    valid = x.notna() & y.notna()
    result = pd.DataFrame(np.nan, index=x.index, columns=x.columns, dtype=float)
    for end in range(39, len(x)):
        lo = end - 39
        if not valid.iloc[lo:end + 1].all(axis=None):
            continue
        betas = []
        for start in (lo, lo + 10, lo + 20, lo + 30):
            xx = x.iloc[start:start + 10]
            yy = y.iloc[start:start + 10]
            vx = xx.var(axis=0, ddof=0)
            cov = ((xx - xx.mean()) * (yy - yy.mean())).mean()
            betas.append(cov.div(vx.where(vx.gt(0.0))))
        block = pd.concat(betas, axis=1)
        result.iloc[end] = block.std(axis=1, ddof=0).where(block.notna().all(axis=1))
    return result


def _validate(panels: dict[str, pd.DataFrame], cfg: dict) -> tuple[list[str], dict[str, pd.DataFrame]]:
    if tuple(cfg.get("windows", ())) != (WINDOW,):
        raise ValueError("Luna rounds 41-45 are frozen to window 20")
    definitions = cfg.get("mechanisms", {})
    if not definitions or set(definitions) - set(DIRECTIONS):
        raise ValueError("mechanisms must be a nonempty subset of approved Luna candidates")
    bad = [name for name in definitions if definitions[name].get("direction") != DIRECTIONS[name]]
    if bad:
        raise ValueError(f"direction mismatch for candidates: {bad}")
    required = {"close", "amount"}
    missing = required - set(panels)
    if missing:
        raise KeyError(f"missing daily panels: {sorted(missing)}")
    close, amount = panels["close"].astype(float), panels["amount"].astype(float)
    if close.shape[1] != 14:
        raise ValueError("peer atoms require the fixed 14-member population")
    if not close.index.equals(amount.index) or not close.columns.equals(amount.columns):
        raise ValueError("close/amount panels must have identical axes")
    return list(definitions), {"close": close, "amount": amount}


def build_atoms(panels: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    """Build selected signed member scores from daily close and canonical amount."""
    names, p = _validate(panels, cfg)
    close, amount = p["close"], p["amount"]
    valid_amount = amount.where(np.isfinite(amount) & amount.gt(0.0))
    log_amount = np.log(valid_amount)
    # Canonical amount innovation is a trading-activity measure, not flow direction.
    activity = log_amount - log_amount.shift(1).rolling(WINDOW, min_periods=WINDOW).mean()
    activity = activity.where(_complete(log_amount.shift(1).notna(), WINDOW) & log_amount.notna())
    clean_close = close.where(np.isfinite(close) & close.gt(0.0))
    ret = clean_close.pct_change(fill_method=None)
    # Every peer statistic uses the complete fixed 14-member date row.
    all14 = activity.notna().all(axis=1) & ret.notna().all(axis=1)
    activity = activity.where(all14, axis=0)
    ret = ret.where(all14, axis=0)
    peer_activity = _peer_mean(activity)
    peer_activity_sd = _peer_std(activity)
    peer_return = _peer_mean(ret)
    signed: dict[str, pd.DataFrame] = {}

    for name in names:
        if name == "l41_peer_amount_to_return_beta":
            signed[name] = _beta(ret, peer_activity.shift(1))
        elif name == "l41_peer_amount_return_correlation":
            signed[name] = _corr(ret, peer_activity.shift(1))
        elif name == "l41_peer_amount_shock_response_asymmetry":
            x = peer_activity.shift(1)
            pair_valid = x.notna() & ret.notna()
            signed[name] = (
                _conditional_mean(ret, x.gt(0.0), pair_valid=pair_valid)
                - _conditional_mean(ret, x.lt(0.0), pair_valid=pair_valid)
            )
        elif name == "l41_peer_flow_reversal_beta":
            x = peer_activity.shift(1)
            # Threshold at t uses the 20 peer-activity observations ending t-2;
            # it is known by the lagged shock date t-1 and excludes that shock.
            threshold = peer_activity.abs().shift(1).rolling(
                WINDOW, min_periods=WINDOW
            ).median().shift(1)
            extreme = threshold.notna() & x.abs().ge(threshold)
            signed[name] = _state_beta(ret, x, extreme).where(
                _complete(threshold.notna())
            )
        elif name == "l42_peer_liquidity_adjusted_return":
            q = ret.div(1.0 + activity.abs())
            signed[name] = _beta(q, peer_activity)
        elif name == "l42_peer_flow_impact_spread":
            signed[name] = _beta(ret, peer_activity) - _beta(ret, peer_activity.abs())
        elif name == "l42_amount_neutral_peer_response":
            signed[name] = _partial_beta(ret, peer_activity, activity)
        elif name == "l42_peer_flow_impact_instability":
            signed[name] = _instability(ret, peer_activity)
        elif name == "l43_peer_amount_inflow_breadth":
            peer_positive = _peer_mean(activity.gt(0.0).astype(float).where(activity.notna()))
            signed[name] = _mean(peer_positive)
        elif name == "l43_peer_amount_inflow_disagreement":
            signed[name] = _mean(peer_activity_sd)
        elif name == "l43_peer_flow_breadth_change":
            peer_positive = _peer_mean(activity.gt(0.0).astype(float).where(activity.notna()))
            signed[name] = _mean(peer_positive.diff())
        elif name == "l43_peer_flow_dispersion_change":
            signed[name] = _mean(peer_activity_sd.diff())
        elif name == "l44_peer_flow_rank_persistence":
            ranks = stable_rank(activity, pct=True)
            # This is Pearson correlation of consecutive cross-sectional rank
            # series, with average ties and the shared stable-score rounding.
            signed[name] = _corr(ranks, ranks.shift(1))
        elif name == "l44_peer_return_flow_confirmation":
            signed[name] = _corr(activity, peer_return)
        elif name == "l44_peer_flow_lead_confirmation":
            signed[name] = _corr(activity, peer_return.shift(1))
        elif name == "l44_peer_flow_rank_reversal":
            ranks = stable_rank(activity, pct=True)
            prior_change = ranks.shift(1) - ranks.shift(2)
            next_change = ranks - ranks.shift(1)
            # Raw score is post-rise rank change; direction -1 rewards reversal.
            pair_valid = prior_change.notna() & next_change.notna()
            signed[name] = _conditional_mean(
                next_change, prior_change.gt(0.0), pair_valid=pair_valid
            )
        elif name == "l45_peer_flow_lagged_correlation":
            signed[name] = _corr(activity, peer_activity.shift(1))
        elif name == "l45_peer_flow_directional_consensus":
            peer_sign = _peer_mean(np.sign(activity).where(activity.notna()))
            signed[name] = _mean(peer_sign.abs())
        elif name == "l45_peer_flow_shock_catchup":
            signed[name] = _mean(activity - peer_activity.shift(1))
        elif name == "l45_peer_flow_shock_divergence":
            signed[name] = _mean((activity - peer_activity).pow(2))
        else:  # guarded by _validate
            raise ValueError(f"unhandled candidate: {name}")

    return {
        f"{name}_{WINDOW}": frame.mul(DIRECTIONS[name]).replace([np.inf, -np.inf], np.nan)
        for name, frame in signed.items()
    }
