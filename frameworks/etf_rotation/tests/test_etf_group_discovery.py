"""Synthetic fixtures only; no market datasets committed."""
import numpy as np
import pandas as pd
import pytest

from etf_strategy.core.etf_group_discovery import (
    aggregate, build_atoms, evaluate, labels, leakage_checks, validate_groups,
)


def fixture():
    dates = pd.bdate_range('2020-01-01', periods=180)
    columns = [f'e{i}' for i in range(14)]
    rng = np.random.default_rng(917)
    close = pd.DataFrame(np.exp(rng.normal(0, .02, (180, 14)).cumsum(axis=0)), index=dates, columns=columns)
    panels = {'close':close, 'open':close*.99, 'high':close*1.02, 'low':close*.98,
              'amount':pd.DataFrame(rng.uniform(1e5, 1e6, (180,14)), index=dates, columns=columns),
              'volume':close*10000}
    groups = {'g0':{'members':columns[:6]}, 'g1':{'members':columns[6:8]}}
    groups.update({f'g{i-6}':{'members':[columns[i]]} for i in range(8,14)})
    return panels, groups


def test_exact_population():
    panels, groups = fixture()
    validate_groups(groups, list(panels['close']))
    groups['g2']['members'].append('e0')
    with pytest.raises(ValueError, match='mismatch'):
        validate_groups(groups, list(panels['close']))


def test_no_partial_member_average():
    panels, groups = fixture()
    close = panels['close'].copy()
    close.iloc[0,0] = np.nan
    assert np.isnan(aggregate(close, groups).iloc[0,0])


def test_labels_use_calendar_positions_and_mature_at_exit():
    panels, _ = fixture()
    panels['open'].iloc[3,0] = np.nan
    r, timing = labels(panels)
    assert r.iloc[0,1] == pytest.approx(panels['open'].iloc[7,1]/panels['open'].iloc[2,1]-1)
    assert pd.isna(r.iloc[1,0])  # Missing entry is not compressed out of the calendar.
    assert timing.iloc[0].entry_date == panels['open'].index[2]
    assert timing.iloc[0].exit_date == panels['open'].index[7]
    assert r.tail(7).isna().all().all()


def test_future_missing_label_drops_whole_date_without_reselection():
    panels, groups = fixture()
    returns, timing = labels(panels)
    score = aggregate(panels['close'], groups)
    known = pd.Series(True, index=score.index)
    a, wa = evaluate(score, returns, groups, known, timing)
    damaged = returns.copy()
    damaged.iloc[0,0] = np.nan
    b, wb = evaluate(score, damaged, groups, known, timing)
    pd.testing.assert_frame_equal(wa, wb)
    assert pd.notna(a.iloc[0].ic)
    assert b.iloc[0][['ic','selected','b8','b14','excess8','excess14']].isna().all()


def test_ties_and_benchmark_decomposition():
    panels, groups = fixture()
    returns, timing = labels(panels)
    score = aggregate(panels['close'], groups)*0+1
    frame, weights = evaluate(score, returns, groups, pd.Series(True, index=score.index), timing)
    np.testing.assert_allclose(weights, 1/8)
    np.testing.assert_allclose(frame.excess8.dropna(), 0, atol=1e-15)
    np.testing.assert_allclose((frame.excess8+frame.allocation_effect).dropna(), frame.excess14.dropna())


def test_all_feature_prefixes_and_future_perturbations():
    panels, _ = fixture()
    names = ['momentum','efficiency','reversal','gap','volatility','downside',
             'range_expansion','amount_expansion','price_volume_corr','illiquidity',
             'close_location','intraday_return']
    cfg = {'windows':[5,20], 'mechanisms':{n:{'direction':1} for n in names}}
    assert len(build_atoms(panels, cfg)) == 24
    assert all(leakage_checks(panels, cfg, panels['close'].index[100]).values())


def test_reverse_illiquidity_is_explicit_alias_with_frozen_positive_direction():
    panels, _ = fixture()
    base = build_atoms(panels, {'windows':[5],
        'mechanisms':{'illiquidity':{'direction':1}}})['illiquidity_5']
    reverse = build_atoms(panels, {'windows':[5],
        'mechanisms':{'reverse_illiquidity':{'direction':1}}})['reverse_illiquidity_5']
    pd.testing.assert_frame_equal(base, reverse)
    assert all(leakage_checks(panels, {'windows':[5],
        'mechanisms':{'reverse_illiquidity':{'direction':1}}},
        panels['close'].index[100]).values())


def test_signal_missing_on_d_prevents_all_selection():
    panels, groups = fixture()
    returns, timing = labels(panels)
    score = aggregate(panels['close'], groups)
    known = pd.Series(True, index=score.index)
    known.iloc[5] = False
    frame, weights = evaluate(score, returns, groups, known, timing)
    assert weights.iloc[5].sum() == 0
    assert pd.isna(frame.iloc[5].selected)
