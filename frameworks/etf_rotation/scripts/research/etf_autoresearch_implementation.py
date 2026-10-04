"""Frozen numerical templates and label-free execution checks for candidate code."""
from __future__ import annotations
import ast
import inspect


def etf_conditional_ols(x, y, condition, window, min_pairs, require_complete=False):
    """Population slope on selected pairs inside a fixed trailing row window."""
    import numpy as np
    valid = np.isfinite(x) & np.isfinite(y)
    selected = valid & condition.fillna(False)
    n = selected.astype(float).rolling(window, min_periods=window).sum()
    xx, yy = x.where(selected, 0.0), y.where(selected, 0.0)
    sx = xx.rolling(window, min_periods=window).sum()
    sy = yy.rolling(window, min_periods=window).sum()
    sxy = (xx * yy).rolling(window, min_periods=window).sum()
    sxx = (xx * xx).rolling(window, min_periods=window).sum()
    denominator = sxx - sx * sx / n.where(n.gt(0))
    slope = (sxy - sx * sy / n.where(n.gt(0))) / denominator.where(denominator.gt(0))
    usable = n.ge(min_pairs) & denominator.gt(0)
    if require_complete:
        usable = usable & valid.astype(float).rolling(window, min_periods=window).sum().eq(window)
    return slope.where(usable)


def etf_rolling_spearman(x, y, window, min_pairs):
    """Average-tie ranks recomputed among paired observations in each window."""
    import numpy as np
    import pandas as pd
    xs = np.stack([x.shift(k).to_numpy(dtype=float) for k in range(window)])
    ys = np.stack([y.shift(k).to_numpy(dtype=float) for k in range(window)])
    valid = np.isfinite(xs) & np.isfinite(ys)
    xr, yr = np.zeros_like(xs), np.zeros_like(ys)
    for k in range(window):
        xr[k] = 1.0 + ((xs < xs[k]) & valid).sum(axis=0) + .5 * (((xs == xs[k]) & valid).sum(axis=0) - 1)
        yr[k] = 1.0 + ((ys < ys[k]) & valid).sum(axis=0) + .5 * (((ys == ys[k]) & valid).sum(axis=0) - 1)
    xr, yr = np.where(valid, xr, 0.0), np.where(valid, yr, 0.0)
    n = valid.sum(axis=0)
    count = np.where(n > 0, n, np.nan)
    sx, sy = xr.sum(axis=0), yr.sum(axis=0)
    covariance = (xr * yr).sum(axis=0) - sx * sy / count
    vx = (xr * xr).sum(axis=0) - sx * sx / count
    vy = (yr * yr).sum(axis=0) - sy * sy / count
    denominator = np.sqrt(np.maximum(vx * vy, 0.0))
    corr = covariance / np.where(denominator > 0, denominator, np.nan)
    result = pd.DataFrame(np.where(n >= min_pairs, corr, np.nan), index=x.index, columns=x.columns)
    full_window = x.notna().astype(float).rolling(window, min_periods=window).sum().notna()
    return result.where(full_window)


KERNELS = {'conditional_ols': etf_conditional_ols, 'rolling_spearman': etf_rolling_spearman}

KERNEL_SELECTION_GUIDANCE = (
    'Mathematical template selection: conditional_ols is a SINGLE predictor OLS with an intercept, '
    'on observations selected by a boolean condition. A condition selects rows; it does NOT add a '
    'control variable. Joint/multiple regression, partial coefficients controlling for another predictor, '
    'and residualization require custom implementation. Do not replace them with a marginal slope. '
    'rolling_spearman recomputes paired ranks inside each trailing window. The frozen formula takes '
    'precedence over a suggested template. If a template cannot express the formula, use custom code '
    'and explain the mismatch; preserve all windows, masks, lags, predictors and direction. Technical '
    'review must verify the formula even when a template is called.'
)


def kernel_binding(source, kind='custom'):
    """Record template use, not a verdict on whether code implements the formula."""
    used = kind != 'custom' and any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == KERNELS[kind].__name__
        for n in ast.walk(ast.parse(source)))
    return {'requested': kind, 'effective': kind if used else 'custom',
            'template_called': bool(used),
            'reason': 'template call present; formula still needs review' if used else
                      'custom implementation; verify frozen formula, not template membership'}



def kernel_contract(kind):
    if kind == 'custom':
        return {'kind': kind, 'note': KERNEL_SELECTION_GUIDANCE}
    function = KERNELS[kind]
    return {'kind': kind, 'function': function.__name__, 'source': inspect.getsource(function),
            'instruction': KERNEL_SELECTION_GUIDANCE + ' If applicable, call the function without redefining it. '
                           'The controller embeds its exact body in the source seal. Apply frozen lags, '
                           'masks and score scaling outside it.'}


def embed_kernel(source, kind='custom'):
    """Embed code, not a mutable import: the existing candidate seal covers it."""
    if kind == 'custom':
        return source
    function = KERNELS[kind]
    template = inspect.getsource(function)
    tree = ast.parse(source)
    expected = ast.dump(ast.parse(template).body[0], include_attributes=False)
    definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function.__name__]
    if len(definitions) > 1 or any(ast.dump(n, include_attributes=False) != expected for n in definitions):
        raise ValueError('math kernel body differs from frozen template')
    # A reference to the function outside a call cannot establish use of the statistic.
    if not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == function.__name__
               for n in ast.walk(tree)):
        return source  # A template mismatch must not force a change of estimand.
    return source if definitions else source + '\n\n' + template


def editable_candidate_source(source, kind='custom'):
    """Hide an exact controller-owned helper from the repair request, not its seal."""
    if kind == 'custom':
        return source
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source  # Keep broken syntax visible to the implementation repair.
    function = KERNELS[kind]
    expected = ast.dump(ast.parse(inspect.getsource(function)).body[0], include_attributes=False)
    definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function.__name__]
    if not definitions:
        return source
    if len(definitions) != 1 or ast.dump(definitions[0], include_attributes=False) != expected:
        raise ValueError('math kernel body differs from frozen template')
    node = definitions[0]
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno - 1] + lines[node.end_lineno:])


def synthetic_check(source, panels):
    """No market data, labels or fitted thresholds; run inside a bounded worker."""
    import numpy as np
    import pandas as pd
    from unittest.mock import patch
    from run_etf_autoresearch_campaign import validate_source
    validate_source(source)
    namespace = {}; exec(compile(source, '<candidate-synthetic>', 'exec'), namespace)
    score = namespace['score']
    dates = pd.bdate_range('2024-01-01', periods=96)
    columns = [f'ETF_{i:02d}' for i in range(14)]
    rng = np.random.default_rng(110928)
    close = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0, .02, (96, 14)), axis=0)), index=dates, columns=columns)
    inputs = {'close': close, 'open': close * (1 + rng.uniform(-.01, .01, close.shape))}
    inputs.update(high=np.maximum(close, inputs['open']) * 1.01, low=np.minimum(close, inputs['open']) * .99,
                  volume=close * 10000, amount=close * close * 10000, shares=close * 100000,
                  premium=pd.DataFrame(rng.normal(0, .02, close.shape), index=dates, columns=columns))
    for panel in panels:
        if panel not in inputs:
            inputs[panel] = pd.DataFrame(rng.normal(0, .02, close.shape), index=dates, columns=columns)
    original_sub = pd.Series.sub
    def checked_sub(left, right, *args, **kwargs):
        result = original_sub(left, right, *args, **kwargs)
        if isinstance(right, pd.DataFrame) and (not result.index.equals(right.index) or not result.columns.equals(right.columns)):
            raise ValueError('shape: Series.sub(DataFrame) expanded axes; use DataFrame.rsub(series, axis=0)')
        return result
    def compute(data):
        before = {k: v.copy(deep=True) for k, v in data.items()}
        with patch.object(pd.Series, 'sub', checked_sub):
            output = score(data)
        if not isinstance(output, pd.DataFrame) or not output.index.equals(data['close'].index) or not output.columns.equals(pd.Index(columns)):
            raise ValueError('shape: synthetic score must preserve ETF index and columns')
        if not all(pd.api.types.is_numeric_dtype(t) for t in output.dtypes):
            raise ValueError('shape: synthetic score must be numeric')
        for key in data:
            pd.testing.assert_frame_equal(data[key], before[key], obj='candidate mutated inputs')
        return output.replace([np.inf, -np.inf], np.nan)
    full = compute({k: v.copy() for k,v in inputs.items()})
    for end in (71, 87):
        prefix = compute({k: v.iloc[:end].copy() for k,v in inputs.items()})
        pd.testing.assert_frame_equal(full.iloc[:end], prefix, check_exact=False, rtol=1e-10, atol=1e-12)
    # Sparse/all-missing synthetic scores are advisory; real coverage rules stay frozen.
    return {'status': 'PASS', 'synthetic_rows': len(dates), 'labels_opened': False,
            'finite_cells': int(full.notna().sum().sum()),
            'scope': 'shape, mutation and two prefix cuts; not proof of mathematical/economic validity'}
