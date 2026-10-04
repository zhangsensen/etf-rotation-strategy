import numpy as np
import pandas as pd
import pytest
import yaml

from etf_strategy.core.etf_group_sources import (
    MINUTE_NAMES, minute_daily, share_daily, nav_daily, build_atoms, leakage_checks,
    _minute_market_residual_abs_cluster, _minute_returns_by_day,
)


def bars(day):
    ts=pd.date_range(f'{day} 09:31',f'{day} 11:30',freq='min').append(
        pd.date_range(f'{day} 13:01',f'{day} 15:00',freq='min'))
    price=1+np.arange(240)/10000
    volume=np.arange(240)+100
    return pd.DataFrame({'datetime':ts,'open':price,'high':price+.002,
        'low':price-.001,'close':price+.001,'volume':volume,
        'turnover':volume*(price+.0005)})


def test_complete_minute_days_and_deterministic_late_period():
    cal=pd.bdate_range('2024-01-02',periods=2)
    b=bars('2024-01-02')
    d,a=minute_daily(b,cal)
    assert a['complete_days']==1
    assert d.iloc[1].isna().all()
    assert d.iloc[0].minute_late_return==pytest.approx(b.close.iloc[-1]/b.open.iloc[180]-1)
    assert d.iloc[0].minute_late_volume_share==pytest.approx(b.volume.iloc[180:].sum()/b.volume.sum())
    assert d.iloc[0].minute_downside_ratio==0
    minute_return = b.close.to_numpy() / b.open.to_numpy() - 1.0
    lagged = minute_return[:-1]
    current = minute_return[1:]
    expected_beta = ((lagged - lagged.mean()) * (current - current.mean())).sum() / ((lagged - lagged.mean()) ** 2).sum()
    assert d.iloc[0].minute_return_ar1_beta==pytest.approx(expected_beta)


def test_incomplete_and_invalid_bars_do_not_get_padded():
    cal=pd.bdate_range('2024-01-02',periods=1)
    b=bars('2024-01-02')
    assert minute_daily(b.iloc[:-1],cal)[0].isna().all().all()
    b.loc[0,'high']=.1
    assert minute_daily(b,cal)[0].isna().all().all()


def test_duplicate_bars_fail():
    b=bars('2024-01-02')
    with pytest.raises(ValueError,match='duplicate'):
        minute_daily(pd.concat([b,b.iloc[:1]]),pd.bdate_range('2024-01-02',periods=1))


def test_future_minute_bars_do_not_change_earlier_day():
    cal=pd.bdate_range('2024-01-02',periods=2)
    b=bars('2024-01-02')
    full=pd.concat([b,bars('2024-01-03')],ignore_index=True)
    pd.testing.assert_frame_equal(minute_daily(full,cal)[0].iloc[:1],minute_daily(b,cal[:1])[0])


def test_minute_ar1_zero_variance_is_nan_and_240_bar_completeness_is_strict():
    cal=pd.bdate_range('2024-01-02',periods=1)
    b=bars('2024-01-02')
    b['close']=b['open']
    b['high']=b['open']+.002
    b['low']=b['open']-.001
    out,_=minute_daily(b,cal)
    assert pd.isna(out.iloc[0].minute_return_ar1_beta)
    assert minute_daily(b.iloc[:-1],cal)[0].iloc[0].isna().all()


def test_batch9_minute_daily_hand_formulas_and_c_to_o_signed_return():
    cal=pd.bdate_range('2024-01-02',periods=1)
    b=bars('2024-01-02')
    # Make the current bar's close fall between its own open and the prior
    # close: C/O is positive while C/C_prev is negative.
    b.loc[1,'close']=1.0005
    out,_=minute_daily(b,cal)
    minute_return=b.close.to_numpy()/b.open.to_numpy()-1.0
    minute_range=(b.high.to_numpy()-b.low.to_numpy())/b.close.to_numpy()

    def corr(a,b):
        return np.corrcoef(a,b)[0,1]

    expected_range_persistence=corr(minute_range[:-1],minute_range[1:])
    signed_flow=np.sign(minute_return)*b.turnover.to_numpy()/b.turnover.sum()
    expected_flow_persistence=corr(signed_flow[:-1],signed_flow[1:])
    expected_flow_return_lead=corr(signed_flow[:-1],minute_return[1:])
    centered=minute_range-minute_range.mean()
    expected_range_skew=(centered**3).mean()/(centered**2).mean()**1.5
    assert out.iloc[0].minute_range_persistence==pytest.approx(expected_range_persistence)
    assert out.iloc[0].minute_signed_flow_persistence==pytest.approx(expected_flow_persistence)
    assert out.iloc[0].minute_signed_flow_return_lead==pytest.approx(expected_flow_return_lead)
    assert out.iloc[0].minute_range_skew==pytest.approx(expected_range_skew)
    # The signed-flow state is based on each bar's close/open return.  Using
    # O_k/C_{k-1}-1 would produce a different sign/serial state on this fixture.
    prior_close=b.close.shift(1).to_numpy()
    wrong_return=b.close.to_numpy()/prior_close-1.0
    wrong_flow=np.sign(np.nan_to_num(wrong_return))*b.turnover.to_numpy()/b.turnover.sum()
    assert not np.isclose(
        expected_flow_persistence,
        corr(wrong_flow[1:-1],wrong_flow[2:]),
    )


def test_batch12_phase_return_curvature_hand_boundaries_and_direction():
    cal = pd.bdate_range('2024-01-02', periods=1)
    b = bars('2024-01-02')
    phase_return = np.r_[
        np.full(60, 0.001),
        np.full(120, 0.003),
        np.full(60, -0.001),
    ]
    b['open'] = 100.0
    b['close'] = b['open'] * (1.0 + phase_return)
    b['high'] = np.maximum(b['open'], b['close']) + 1.0
    b['low'] = np.minimum(b['open'], b['close']) - 1.0
    b['turnover'] = b['volume'] * 100.0
    daily, audit = minute_daily(b, cal)
    assert audit['complete_days'] == 1
    # The values at k=60/61 and k=180/181 belong to middle/middle and
    # middle/late respectively; the frozen slices are [0:60], [60:180],
    # and [180:240].
    assert daily.iloc[0].minute_phase_return_curvature == pytest.approx(0.006)

    panel = pd.DataFrame(
        {'minute_phase_return_curvature': np.arange(20, dtype=float)}, index=cal[:1].append(
            pd.bdate_range('2024-01-03', periods=19)
        )
    )
    cfg = {
        'source_type': 'minute', 'windows': [20],
        'mechanisms': {'minute_phase_return_curvature': {'direction': 1}},
    }
    atoms = build_atoms({'minute_phase_return_curvature': panel}, cfg)
    assert atoms['minute_phase_return_curvature_20'].iloc[19, 0] == pytest.approx(9.5)
    assert atoms['minute_phase_return_curvature_20'].iloc[:19].isna().all().all()


def test_batch12_phase_return_curvature_nan_240_bar_and_causal_rolling():
    cal = pd.bdate_range('2024-01-02', periods=40)
    b = bars('2024-01-02')
    incomplete, _ = minute_daily(b.iloc[:-1], cal[:1])
    assert incomplete.iloc[0].isna().all()

    t = np.arange(len(cal), dtype=float)
    panel = pd.DataFrame(
        {'minute_phase_return_curvature': 0.01 + 0.002 * np.sin(t / 3.0)},
        index=cal,
    )
    cfg = {
        'source_type': 'minute', 'windows': [20],
        'mechanisms': {'minute_phase_return_curvature': {'direction': 1}},
    }
    broken = panel.copy()
    broken.iloc[5, 0] = np.nan
    broken_atoms = build_atoms(
        {'minute_phase_return_curvature': broken}, cfg
    )['minute_phase_return_curvature_20']
    assert pd.isna(broken_atoms.iloc[19, 0])
    assert pd.notna(broken_atoms.iloc[25, 0])
    assert all(leakage_checks({'minute_phase_return_curvature': panel}, cfg, cal[25]).values())


def test_batch14_minute_config_hand_formulas_and_240_bar_boundary():
    cfg = {
        'source_type': 'minute', 'windows': [20],
        'mechanisms': {
            'minute_turnover_return_corr': {'direction': 1},
            'minute_range_turnover_corr': {'direction': 1},
        },
    }
    cal = pd.bdate_range('2024-01-02', periods=1)
    b = bars('2024-01-02')
    daily, audit = minute_daily(b, cal)
    assert audit['complete_days'] == 1
    minute_return = b.close.to_numpy() / b.open.to_numpy() - 1.0
    amount_share = b.turnover.to_numpy() / b.turnover.sum()
    minute_range = (b.high.to_numpy() - b.low.to_numpy()) / b.close.to_numpy()

    def corr(left, right):
        return np.corrcoef(left, right)[0, 1]

    assert daily.iloc[0].minute_turnover_return_corr == pytest.approx(
        corr(amount_share, minute_return)
    )
    assert daily.iloc[0].minute_range_turnover_corr == pytest.approx(
        corr(minute_range, amount_share)
    )
    panel_index = cal.append(pd.bdate_range('2024-01-03', periods=19))
    panels = {
        name: pd.DataFrame(np.repeat(daily[name].to_numpy()[None, :], 20, axis=0),
                           index=panel_index, columns=['a'])
        for name in ('minute_turnover_return_corr', 'minute_range_turnover_corr')
    }
    out = build_atoms(panels, cfg)
    assert out['minute_turnover_return_corr_20'].iloc[19, 0] == pytest.approx(
        daily.iloc[0].minute_turnover_return_corr
    )
    assert out['minute_range_turnover_corr_20'].iloc[19, 0] == pytest.approx(
        daily.iloc[0].minute_range_turnover_corr
    )
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())

    incomplete, _ = minute_daily(b.iloc[:-1], cal)
    assert incomplete.iloc[0].isna().all()


def test_batch14_minute_config_contract():
    with open('frameworks/etf_rotation/configs/group_ic20_batch14_minute_20260923.yaml') as handle:
        cfg = yaml.safe_load(handle)
    assert cfg['discovery_surface'] == '2025_DIRECTION_DISCOVERY_ONLY'
    assert cfg['as_of'] == '2025-12-31'
    assert cfg['prior_registered'] == 172
    assert cfg['budget_cap'] == 174
    assert cfg['new_definitions'] == 2
    assert cfg['external_registered_definitions'] == 8
    assert list(cfg['mechanisms']) == [
        'minute_turnover_return_corr', 'minute_range_turnover_corr'
    ]
    assert [cfg['mechanisms'][name]['direction'] for name in cfg['mechanisms']] == [1, 1]


def test_batch14_minute_amount_source_zero_variance_and_prefix_future():
    cal = pd.bdate_range('2024-01-02', periods=40)
    t = np.arange(len(cal), dtype=float)
    panels = {
        'minute_turnover_return_corr': pd.DataFrame(
            np.repeat((0.1 + 0.03 * np.sin(t / 3))[:, None], 2, axis=1),
            index=cal, columns=['a', 'b']),
        'minute_range_turnover_corr': pd.DataFrame(
            np.repeat((0.2 + 0.02 * np.cos(t / 4))[:, None], 2, axis=1),
            index=cal, columns=['a', 'b']),
    }
    cfg = {
        'source_type': 'minute', 'windows': [20],
        'mechanisms': {
            'minute_turnover_return_corr': {'direction': 1},
            'minute_range_turnover_corr': {'direction': 1},
        },
    }
    out = build_atoms(panels, cfg)
    for name in panels:
        pd.testing.assert_frame_equal(
            out[f'{name}_20'], panels[name].rolling(20, min_periods=20).mean()
        )
    assert all(leakage_checks(panels, cfg, cal[25]).values())

    zero = panels.copy()
    zero['minute_turnover_return_corr'] = panels['minute_turnover_return_corr'].copy()
    zero['minute_turnover_return_corr'].iloc[10, 0] = np.nan
    zero_out = build_atoms(zero, cfg)
    assert pd.isna(zero_out['minute_turnover_return_corr_20'].iloc[19, 0])
    assert pd.notna(zero_out['minute_turnover_return_corr_20'].iloc[30, 0])

    b = bars('2024-01-02')
    b['close'] = b['open']
    b['high'] = b['open'] + .002
    b['low'] = b['open'] - .001
    daily, _ = minute_daily(b, cal[:1])
    assert pd.isna(daily.iloc[0].minute_turnover_return_corr)


def test_batch14_stage2_minute_aliases_equal_raw_times_frozen_sign():
    cal = pd.bdate_range('2024-01-01', periods=40)
    t = np.arange(len(cal), dtype=float)
    raw_panels = {
        'minute_turnover_return_corr': pd.DataFrame(
            np.repeat((0.1 + 0.03 * np.sin(t / 3))[:, None], 2, axis=1),
            index=cal, columns=['a', 'b']),
        'minute_range_turnover_corr': pd.DataFrame(
            np.repeat((0.2 + 0.02 * np.cos(t / 4))[:, None], 2, axis=1),
            index=cal, columns=['a', 'b']),
    }
    raw_cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        name: {'direction': 1} for name in raw_panels
    }}
    aliases = {
        'd2025_minute_turnover_return_corr': ('minute_turnover_return_corr', 1),
        'd2025_minute_range_turnover_corr': ('minute_range_turnover_corr', 1),
    }
    alias_cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        name: {'direction': sign} for name, (_, sign) in aliases.items()
    }}
    raw_out = build_atoms(raw_panels, raw_cfg)
    alias_out = build_atoms(raw_panels, alias_cfg)
    for alias, (raw, sign) in aliases.items():
        pd.testing.assert_frame_equal(
            alias_out[f'{alias}_20'], raw_out[f'{raw}_20'] * sign
        )
    assert all(leakage_checks(raw_panels, alias_cfg, cal[25]).values())


def test_batch14_stage2_minute_config_contract():
    with open('frameworks/etf_rotation/configs/group_ic20_batch14_stage2_minute_20260923.yaml') as handle:
        cfg = yaml.safe_load(handle)
    assert cfg['discovery_surface'] == '2025_POST_IC_DIRECTION'
    assert cfg['non_independent_confirmation'] is True
    assert cfg['as_of'] == '2026-09-17'
    assert cfg['evaluation_start'] == '2025-01-01'
    assert cfg['prior_registered'] == 188
    assert cfg['budget_cap'] == 190
    assert cfg['new_definitions'] == 2
    assert cfg['external_registered_definitions'] == 8
    assert list(cfg['mechanisms']) == [
        'd2025_minute_turnover_return_corr',
        'd2025_minute_range_turnover_corr',
    ]
    assert [cfg['mechanisms'][name]['direction'] for name in cfg['mechanisms']] == [1, 1]


def test_batch15_minute_daily_amount_conditionals_and_240_bar_hand_formulas():
    cal = pd.bdate_range('2024-01-02', periods=1)
    b = bars('2024-01-02')
    signs = np.where(np.arange(240) % 2 == 0, 1.0, -1.0)
    b['open'] = 100.0
    b['close'] = b['open'] * (1.0 + signs * 0.001)
    b['high'] = np.maximum(b['open'], b['close']) + 1.0
    b['low'] = np.minimum(b['open'], b['close']) - 1.0
    b['turnover'] = b['volume'] * 100.0
    daily, audit = minute_daily(b, cal)
    assert audit['complete_days'] == 1
    m = b.close.to_numpy() / b.open.to_numpy() - 1.0
    r = (b.high.to_numpy() - b.low.to_numpy()) / b.close.to_numpy()
    a = b.turnover.to_numpy()
    share = a / a.sum()
    positive = m > 0
    nonpositive = ~positive
    expected_range_asym = r[positive].mean() - r[nonpositive].mean()
    expected_amount_sign = share[positive].sum() - share[nonpositive].sum()
    amount_abs = share * np.abs(m)
    expected_amount_concentration = (amount_abs ** 2).sum() / amount_abs.sum() ** 2
    assert daily.iloc[0].minute_range_sign_asymmetry == pytest.approx(expected_range_asym)
    assert daily.iloc[0].minute_amount_sign_imbalance == pytest.approx(expected_amount_sign)
    assert daily.iloc[0].minute_amount_abs_return_concentration == pytest.approx(expected_amount_concentration)
    assert daily.iloc[0].minute_early_daily_mean_return == pytest.approx(m[:60].mean())
    assert daily.iloc[0].minute_late_daily_mean_return == pytest.approx(m[180:].mean())

    cal20 = pd.bdate_range('2024-01-02', periods=20)
    early = np.linspace(-0.02, 0.02, 20)
    late = np.linspace(0.03, -0.01, 20)
    panels = {
        'minute_early_daily_mean_return': pd.DataFrame({'a': early}, index=cal20),
        'minute_late_daily_mean_return': pd.DataFrame({'a': late}, index=cal20),
    }
    cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        'minute_phase_signed_return_corr': {'direction': 1},
    }}
    atom = build_atoms(panels, cfg)['minute_phase_signed_return_corr_20']
    assert atom.iloc[-1, 0] == pytest.approx(np.corrcoef(early, late)[0, 1])


def test_batch15_minute_missing_condition_and_prefix_future():
    cal = pd.bdate_range('2024-01-02', periods=40)
    t = np.arange(40, dtype=float)
    panels = {
        'minute_range_sign_asymmetry': pd.DataFrame({'a': 0.1 + 0.01 * np.sin(t)}, index=cal),
        'minute_amount_sign_imbalance': pd.DataFrame({'a': 0.2 + 0.01 * np.cos(t)}, index=cal),
        'minute_amount_abs_return_concentration': pd.DataFrame({'a': 0.3 + 0.01 * np.sin(t / 2)}, index=cal),
        'minute_early_daily_mean_return': pd.DataFrame({'a': 0.01 + 0.001 * np.sin(t / 3)}, index=cal),
        'minute_late_daily_mean_return': pd.DataFrame({'a': 0.02 + 0.001 * np.cos(t / 4)}, index=cal),
    }
    cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        'minute_range_sign_asymmetry': {'direction': 1},
        'minute_amount_sign_imbalance': {'direction': 1},
        'minute_amount_abs_return_concentration': {'direction': 1},
        'minute_phase_signed_return_corr': {'direction': 1},
    }}
    out = build_atoms(panels, cfg)
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(leakage_checks(panels, cfg, cal[25]).values())
    broken = {key: value.copy() for key, value in panels.items()}
    broken['minute_early_daily_mean_return'].iloc[5, 0] = np.nan
    broken_out = build_atoms(broken, cfg)
    assert pd.isna(broken_out['minute_phase_signed_return_corr_20'].iloc[19, 0])
    assert pd.notna(broken_out['minute_phase_signed_return_corr_20'].iloc[30, 0])
    incomplete, _ = minute_daily(bars('2024-01-02').iloc[:-1], cal[:1])
    assert incomplete.iloc[0].isna().all()


def test_batch15_minute_config_contract():
    with open('frameworks/etf_rotation/configs/group_ic20_batch15_minute_20260923.yaml') as handle:
        cfg = yaml.safe_load(handle)
    assert cfg['discovery_surface'] == '2025_DIRECTION_DISCOVERY_ONLY'
    assert cfg['as_of'] == '2025-12-31'
    assert cfg['prior_registered'] == 202
    assert cfg['budget_cap'] == 206
    assert cfg['new_definitions'] == 4
    assert cfg['external_registered_definitions'] == 8
    assert list(cfg['mechanisms']) == [
        'minute_range_sign_asymmetry', 'minute_amount_sign_imbalance',
        'minute_amount_abs_return_concentration', 'minute_phase_signed_return_corr',
    ]


def test_batch15_stage2_minute_aliases_equal_raw_times_each_direction():
    cal = pd.bdate_range('2024-01-01', periods=40)
    t = np.arange(len(cal), dtype=float)
    raw_panels = {
        'minute_range_sign_asymmetry': pd.DataFrame({'a': 0.1 + 0.01 * np.sin(t)}, index=cal),
        'minute_amount_sign_imbalance': pd.DataFrame({'a': 0.2 + 0.01 * np.cos(t)}, index=cal),
        'minute_amount_abs_return_concentration': pd.DataFrame({'a': 0.3 + 0.01 * np.sin(t / 2)}, index=cal),
        'minute_early_daily_mean_return': pd.DataFrame({'a': 0.01 + 0.001 * np.sin(t / 3)}, index=cal),
        'minute_late_daily_mean_return': pd.DataFrame({'a': 0.02 + 0.001 * np.cos(t / 4)}, index=cal),
    }
    aliases = {
        'd2025_minute_range_sign_asymmetry': ('minute_range_sign_asymmetry', 1),
        'd2025_minute_amount_sign_imbalance': ('minute_amount_sign_imbalance', 1),
        'd2025_minute_amount_abs_return_concentration': ('minute_amount_abs_return_concentration', 1),
        'd2025_minute_phase_signed_return_corr': ('minute_phase_signed_return_corr', 1),
    }
    raw_cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        name: {'direction': 1} for name in (
            'minute_range_sign_asymmetry', 'minute_amount_sign_imbalance',
            'minute_amount_abs_return_concentration', 'minute_phase_signed_return_corr'
        )
    }}
    alias_cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        name: {'direction': sign} for name, (_, sign) in aliases.items()
    }}
    raw_out = build_atoms(raw_panels, raw_cfg)
    alias_out = build_atoms(raw_panels, alias_cfg)
    for alias, (raw, sign) in aliases.items():
        pd.testing.assert_frame_equal(alias_out[f'{alias}_20'], raw_out[f'{raw}_20'] * sign)
    assert all(leakage_checks(raw_panels, alias_cfg, cal[25]).values())


def test_batch15_stage2_minute_config_contract():
    with open('frameworks/etf_rotation/configs/group_ic20_batch15_stage2_minute_20260923.yaml') as handle:
        cfg = yaml.safe_load(handle)
    assert cfg['purpose'] == 'seen_history_discovery_only'
    assert cfg['discovery_surface'] == '2025_POST_IC_DIRECTION'
    assert cfg['as_of'] == '2026-09-17'
    assert cfg['evaluation_start'] == '2025-01-01'
    assert cfg['prior_registered'] == 218
    assert cfg['budget_cap'] == 222
    assert cfg['new_definitions'] == 4
    assert cfg['external_registered_definitions'] == 8
    assert all(name.startswith('d2025_') for name in cfg['mechanisms'])


def test_batch10_minute_source_atoms_hand_directions_and_leakage():
    cal = pd.bdate_range('2024-01-01', periods=80)
    t = np.arange(len(cal), dtype=float)
    panels = {
        'minute_signed_flow_return_lead': pd.DataFrame(
            np.repeat((0.1 + 0.03 * np.sin(t / 3))[:, None], 2, axis=1),
            index=cal, columns=['a', 'b']),
        'minute_market_residual_abs_cluster': pd.DataFrame(
            np.repeat((0.2 + 0.02 * np.cos(t / 4))[:, None], 2, axis=1),
            index=cal, columns=['a', 'b']),
    }
    cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        'minute_signed_flow_return_lead': {'direction': 1},
        'minute_market_residual_abs_cluster': {'direction': -1},
    }}
    out = build_atoms(panels, cfg)
    pd.testing.assert_frame_equal(
        out['minute_signed_flow_return_lead_20'],
        panels['minute_signed_flow_return_lead'].rolling(20, min_periods=20).mean(),
    )
    pd.testing.assert_frame_equal(
        out['minute_market_residual_abs_cluster_20'],
        -panels['minute_market_residual_abs_cluster'].rolling(20, min_periods=20).mean(),
    )
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(leakage_checks(panels, cfg, cal[60]).values())
    broken = {key: value.copy() for key, value in panels.items()}
    broken['minute_market_residual_abs_cluster'].iloc[30, 0] = np.nan
    broken_out = build_atoms(broken, cfg)
    assert pd.isna(broken_out['minute_market_residual_abs_cluster_20'].iloc[49, 0])
    assert pd.notna(broken_out['minute_market_residual_abs_cluster_20'].iloc[50, 0])


def test_batch10_minute_residual_helper_requires_all_members_and_240_bars():
    cal = pd.bdate_range('2024-01-02', periods=2)
    full = bars('2024-01-02')
    valid = _minute_returns_by_day(full, cal)
    assert list(valid) == [pd.Timestamp('2024-01-02')]
    assert _minute_returns_by_day(full.iloc[:-1], cal) == {}
    raw_by_symbol = {f's{i}': valid for i in range(14)}
    panel = _minute_market_residual_abs_cluster(raw_by_symbol, list(raw_by_symbol), cal)
    # Identical member paths have zero residual variance, hence no false finite state.
    assert panel.iloc[0].isna().all()
    missing = dict(raw_by_symbol)
    missing['s7'] = {}
    assert _minute_market_residual_abs_cluster(missing, list(raw_by_symbol), cal).iloc[0].isna().all()


def test_batch9_minute_source_atoms_directions_prefix_and_future_perturbation():
    cal=pd.bdate_range('2024-01-01',periods=80)
    t=np.arange(len(cal),dtype=float)
    panels={
        'minute_range_persistence':pd.DataFrame(np.repeat((0.2+0.03*np.sin(t/3))[:,None],2,axis=1),index=cal,columns=['a','b']),
        'minute_signed_flow_persistence':pd.DataFrame(np.repeat((0.1+0.02*np.cos(t/4))[:,None],2,axis=1),index=cal,columns=['a','b']),
        'minute_range_skew':pd.DataFrame(np.repeat((-0.2+0.04*np.sin(t/5))[:,None],2,axis=1),index=cal,columns=['a','b']),
    }
    cfg={'source_type':'minute','windows':[20], 'mechanisms':{
        'minute_range_persistence':{'direction':-1},
        'minute_signed_flow_persistence':{'direction':1},
        'minute_range_skew':{'direction':-1},
    }}
    out=build_atoms(panels,cfg)
    pd.testing.assert_frame_equal(
        out['minute_range_persistence_20'],
        -panels['minute_range_persistence'].rolling(20,min_periods=20).mean(),
    )
    pd.testing.assert_frame_equal(
        out['minute_signed_flow_persistence_20'],
        panels['minute_signed_flow_persistence'].rolling(20,min_periods=20).mean(),
    )
    pd.testing.assert_frame_equal(
        out['minute_range_skew_20'],
        -panels['minute_range_skew'].rolling(20,min_periods=20).mean(),
    )
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(leakage_checks(panels,cfg,cal[60]).values())
    broken={key:value.copy() for key,value in panels.items()}
    broken['minute_range_persistence'].iloc[30,0]=np.nan
    broken_out=build_atoms(broken,cfg)
    assert pd.isna(broken_out['minute_range_persistence_20'].iloc[49,0])
    assert pd.notna(broken_out['minute_range_persistence_20'].iloc[50,0])


def test_share_asof_never_before_available_and_stale_masked():
    cal=pd.bdate_range('2024-01-02',periods=12)
    raw=pd.DataFrame({'trade_date':['2024-01-02','2024-01-17'],
                      'usable_from_date':['2024-01-03','2024-01-18'],'fund_shares':[100.,200.]})
    s,a=share_daily(raw,cal,7)
    assert pd.isna(s.iloc[0])
    assert s.loc['2024-01-03']==100
    assert pd.isna(s.loc['2024-01-11'])
    assert a['availability_status']=='NEXT_SESSION_ASSUMPTION_NOT_PUBLICATION_PROOF'


def test_share_same_day_availability_rejected():
    raw=pd.DataFrame({'trade_date':['2024-01-02'],'usable_from_date':['2024-01-02'],'fund_shares':[100.]})
    with pytest.raises(ValueError,match='follow'):
        share_daily(raw,pd.bdate_range('2024-01-02',periods=2))


def test_weekend_share_collision_uses_latest_source_only_when_available():
    raw=pd.DataFrame({'trade_date':['2024-03-29','2024-03-31'],
                      'usable_from_date':['2024-04-01','2024-04-01'],
                      'fund_shares':[100.,110.]})
    s,a=share_daily(raw,pd.bdate_range('2024-03-29',periods=3))
    assert pd.isna(s.iloc[0])
    assert s.loc['2024-04-01']==110
    assert a['same_availability_date_collisions']==1
    with pytest.raises(ValueError,match='source dates'):
        share_daily(pd.concat([raw,raw.iloc[:1]]),s.index)


@pytest.mark.parametrize('kind',['minute','share'])
def test_source_atoms_causal_on_calendar(kind):
    cal=pd.bdate_range('2024-01-01',periods=150)
    rng=np.random.default_rng(321)
    names=MINUTE_NAMES if kind=='minute' else ['shares']
    panels={n:pd.DataFrame(rng.uniform(1,2,(150,14)),index=cal) for n in names}
    ms=MINUTE_NAMES if kind=='minute' else ['share_redemption','share_persistence','share_acceleration','share_volatility']
    cfg={'source_type':kind,'windows':[5,20], 'mechanisms':{n:{'direction':-1} for n in ms}}
    assert len(build_atoms(panels,cfg))==len(ms)*2
    assert all(leakage_checks(panels,cfg,cal[100]).values())


def test_approved_batch8_source_atoms_hand_calculation_and_directions():
    cal=pd.bdate_range('2024-01-01',periods=80)
    t=np.arange(len(cal),dtype=float)
    close=pd.DataFrame({
        'a':100*np.cumprod(1+0.002+0.001*np.sin(t/4)),
        'b':80*np.cumprod(1-0.001+0.002*np.cos(t/5)),
    },index=cal)
    minute_ar1=pd.DataFrame({'a':0.05+0.01*np.sin(t/3),'b':-0.02+0.01*np.cos(t/4)},index=cal)
    signed=pd.DataFrame({'a':0.1*np.sin(t/3),'b':-0.1*np.cos(t/4)},index=cal)
    minute_panels={n:pd.DataFrame(0.2+0.01*np.repeat(np.sin(t[:,None]/(i+2)),2,axis=1),index=cal,columns=['a','b'])
                   for i,n in enumerate(MINUTE_NAMES)}
    minute_panels['minute_return_ar1_beta']=minute_ar1
    minute_panels['minute_signed_volume']=signed
    minute_panels['close']=close
    minute_cfg={'source_type':'minute','windows':[20], 'mechanisms':{
        'minute_return_ar1_beta':{'direction':1},
        'minute_orderflow_return_lead':{'direction':1},
    }}
    minute_out=build_atoms(minute_panels,minute_cfg)
    pd.testing.assert_frame_equal(
        minute_out['minute_return_ar1_beta_20'],
        minute_ar1.rolling(20,min_periods=20).mean(),
    )
    returns=close.pct_change(fill_method=None)
    expected_orderflow=signed.shift(1).rolling(20,min_periods=20).corr(returns)
    pd.testing.assert_frame_equal(minute_out['minute_orderflow_return_lead_20'],expected_orderflow)

    shares=pd.DataFrame({'a':1000+2*t+3*np.sin(t/5),'b':800+1.5*t+2*np.cos(t/6)},index=cal)
    share_panels={'shares':shares,'close':close}
    share_cfg={'source_type':'share','windows':[20], 'mechanisms':{
        'share_flow_return_lead':{'direction':1},
    }}
    share_out=build_atoms(share_panels,share_cfg)['share_flow_return_lead_20']
    expected_share=np.log(shares).diff().shift(1).rolling(20,min_periods=20).corr(returns)
    pd.testing.assert_frame_equal(share_out,expected_share)
    assert share_out.iloc[:21].isna().all().all()
    assert share_out.iloc[30:].notna().all().all()

    assert all(leakage_checks(minute_panels,minute_cfg,cal[60]).values())
    assert all(leakage_checks(share_panels,share_cfg,cal[60]).values())


def test_batch8_source_missing_propagation_and_required_close_panel():
    cal=pd.bdate_range('2024-01-01',periods=60)
    x=pd.DataFrame(np.linspace(1,2,len(cal)*2).reshape(len(cal),2),index=cal,columns=['a','b'])
    minute_panels={n:x+1 for n in MINUTE_NAMES}
    minute_panels['close']=x+10
    cfg={'source_type':'minute','windows':[20], 'mechanisms':{
        'minute_orderflow_return_lead':{'direction':1},
    }}
    with pytest.raises(KeyError,match='close panel'):
        build_atoms({n:x+1 for n in MINUTE_NAMES},cfg)
    minute_panels['minute_signed_volume'].iloc[30,0]=np.nan
    out=build_atoms(minute_panels,cfg)['minute_orderflow_return_lead_20']
    assert pd.isna(out.iloc[49,0])
    assert pd.isna(out.iloc[50,0])
    assert pd.notna(out.iloc[51,0])

    shares=x+100
    share_cfg={'source_type':'share','windows':[20], 'mechanisms':{
        'share_flow_return_lead':{'direction':1},
    }}
    with pytest.raises(KeyError,match='close panel'):
        build_atoms({'shares':shares},share_cfg)
    shares.iloc[30,0]=np.nan
    share_out=build_atoms({'shares':shares,'close':x+10},share_cfg)['share_flow_return_lead_20']
    assert pd.isna(share_out.iloc[50,0])


def test_reverse_minute_late_return_is_explicit_negative_direction_alias():
    cal=pd.bdate_range('2024-01-01',periods=40)
    x=pd.DataFrame(np.arange(40*14,dtype=float).reshape(40,14),index=cal)
    panels={n:x+1 for n in MINUTE_NAMES}
    original=build_atoms(panels,{'source_type':'minute','windows':[5],
        'mechanisms':{'minute_late_return':{'direction':1}}})['minute_late_return_5']
    reverse=build_atoms(panels,{'source_type':'minute','windows':[5],
        'mechanisms':{'reverse_minute_late_return':{'direction':-1}}})['reverse_minute_late_return_5']
    pd.testing.assert_frame_equal(reverse,-original)
    assert all(leakage_checks(panels,{'source_type':'minute','windows':[5],
        'mechanisms':{'reverse_minute_late_return':{'direction':-1}}},cal[30]).values())


def test_batch16_minute_phase_states_hand_formulas_scale_and_240_bar():
    cal = pd.bdate_range('2024-01-02', periods=1)
    b = bars('2024-01-02')
    phase_return = np.r_[
        np.full(60, 0.001), np.full(120, -0.002), np.full(60, 0.003)
    ]
    b['open'] = 100.0
    b['close'] = b['open'] * (1.0 + phase_return)
    b['high'] = np.maximum(b['open'], b['close']) + 1.0
    b['low'] = np.minimum(b['open'], b['close']) - 1.0
    phase_amount = np.r_[np.full(60, 1.0), np.full(120, 2.0), np.full(60, 4.0)]
    b['volume'] = 100.0 * phase_amount
    b['turnover'] = b['volume'].to_numpy() * 100.0
    daily, audit = minute_daily(b, cal)
    assert audit['complete_days'] == 1
    minute_range = (b.high.to_numpy() - b.low.to_numpy()) / b.close.to_numpy()
    early_range = minute_range[:60].mean()
    late_range = minute_range[180:].mean()
    expected_range_migration = (late_range - early_range) / (late_range + early_range)
    assert daily.iloc[0].minute_phase_range_migration == pytest.approx(expected_range_migration)
    amount_share = b.turnover.to_numpy() / b.turnover.sum()
    expected_amount_migration = amount_share[180:].sum() - amount_share[:60].sum()
    assert daily.iloc[0].minute_phase_amount_migration == pytest.approx(expected_amount_migration)
    assert daily.iloc[0].minute_phase_return_path_persistence == pytest.approx(-1.0)
    assert daily.iloc[0].minute_phase_return_reversal == pytest.approx(0.0)
    assert daily.iloc[0].minute_gap_repair_phase != daily.iloc[0].minute_gap_repair_phase
    assert minute_daily(b.iloc[:-1], cal)[0].iloc[0].isna().all()

    panel_index = pd.bdate_range('2024-01-02', periods=40)
    panels = {
        name: pd.DataFrame(
            np.linspace(0.01, 0.2, len(panel_index) * 2).reshape(len(panel_index), 2),
            index=panel_index, columns=['a', 'b']
        )
        for name in MINUTE_NAMES
    }
    cfg = yaml.safe_load(open(
        'frameworks/etf_rotation/configs/group_ic20_batch16_minute_20260923.yaml'
    ))
    out = build_atoms(panels, cfg)
    assert list(out) == [f'{name}_20' for name in cfg['mechanisms']]
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(frame.iloc[19:].notna().all().all() for frame in out.values())
    scaled_b = b.copy()
    for field in ('open', 'high', 'low', 'close'):
        scaled_b[field] *= 7.0
    scaled_b['turnover'] *= 7.0
    scaled_daily, _ = minute_daily(scaled_b, cal)
    scale_invariant = (
        'minute_phase_range_migration', 'minute_phase_amount_migration',
        'minute_phase_abs_return_migration', 'minute_phase_return_path_persistence',
        'minute_phase_return_reversal', 'minute_phase_amount_curvature',
        'minute_phase_amount_abs_return_migration',
        'minute_phase_return_range_absorption', 'minute_gap_repair_phase',
    )
    for name in scale_invariant:
        if pd.isna(daily.iloc[0][name]):
            assert pd.isna(scaled_daily.iloc[0][name])
        else:
            assert scaled_daily.iloc[0][name] == pytest.approx(daily.iloc[0][name])
    assert all(leakage_checks(panels, cfg, panel_index[30]).values())


def test_batch16_minute_config_contract():
    cfg = yaml.safe_load(open(
        'frameworks/etf_rotation/configs/group_ic20_batch16_minute_20260923.yaml'
    ))
    expected = [
        'minute_phase_range_migration', 'minute_phase_amount_migration',
        'minute_phase_abs_return_migration', 'minute_phase_return_path_persistence',
        'minute_phase_return_reversal', 'minute_phase_range_curvature',
        'minute_phase_amount_curvature', 'minute_phase_amount_abs_return_migration',
        'minute_phase_return_range_absorption', 'minute_phase_directional_range_shift',
        'minute_phase_directional_amount_shift', 'minute_gap_repair_phase',
    ]
    assert list(cfg['mechanisms']) == expected
    assert cfg['purpose'] == 'seen_history_discovery_only'
    assert cfg['discovery_surface'] == '2025_DIRECTION_DISCOVERY_ONLY'
    assert cfg['as_of'] == '2025-12-31'
    assert cfg['prior_registered'] == 226
    assert cfg['budget_cap'] == 238
    assert cfg['new_definitions'] == 12
    assert cfg['external_registered_definitions'] == 8
    assert [cfg['mechanisms'][name]['direction'] for name in expected] == [1] * 12


def test_batch16_stage2_minute_aliases_equal_raw_times_frozen_direction():
    cal = pd.bdate_range('2024-01-02', periods=40)
    x = np.linspace(0.01, 0.2, len(cal) * 2).reshape(len(cal), 2)
    panels = {
        name: pd.DataFrame(x, index=cal, columns=['a', 'b'])
        for name in MINUTE_NAMES
    }
    aliases = {
        'd2025_minute_phase_range_migration': ('minute_phase_range_migration', -1),
        'd2025_minute_phase_amount_migration': ('minute_phase_amount_migration', -1),
        'd2025_minute_phase_abs_return_migration': ('minute_phase_abs_return_migration', -1),
        'd2025_minute_phase_return_path_persistence': ('minute_phase_return_path_persistence', 1),
        'd2025_minute_phase_return_reversal': ('minute_phase_return_reversal', 1),
        'd2025_minute_phase_range_curvature': ('minute_phase_range_curvature', -1),
        'd2025_minute_phase_amount_curvature': ('minute_phase_amount_curvature', -1),
        'd2025_minute_phase_amount_abs_return_migration': ('minute_phase_amount_abs_return_migration', -1),
        'd2025_minute_phase_return_range_absorption': ('minute_phase_return_range_absorption', 1),
        'd2025_minute_phase_directional_range_shift': ('minute_phase_directional_range_shift', -1),
        'd2025_minute_phase_directional_amount_shift': ('minute_phase_directional_amount_shift', -1),
        'd2025_minute_gap_repair_phase': ('minute_gap_repair_phase', 1),
    }
    raw_cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        raw: {'direction': 1} for raw, _ in aliases.values()
    }}
    alias_cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        alias: {'direction': sign} for alias, (_, sign) in aliases.items()
    }}
    raw_out = build_atoms(panels, raw_cfg)
    alias_out = build_atoms(panels, alias_cfg)
    for alias, (raw, sign) in aliases.items():
        pd.testing.assert_frame_equal(
            alias_out[f'{alias}_20'], raw_out[f'{raw}_20'] * sign
        )
    assert all(leakage_checks(panels, alias_cfg, cal[30]).values())


def test_batch16_stage2_minute_config_contracts():
    expected = {
        'group_ic20_batch16_stage2_minute_a_20260923.yaml': (242, 248, 6),
        'group_ic20_batch16_stage2_minute_b_20260923.yaml': (248, 254, 6),
    }
    for filename, (prior, cap, count) in expected.items():
        cfg = yaml.safe_load(open('frameworks/etf_rotation/configs/' + filename))
        assert cfg['purpose'] == 'seen_history_discovery_only'
        assert cfg['discovery_surface'] == '2025_POST_IC_DIRECTION'
        assert cfg['as_of'] == '2026-09-17'
        assert cfg['evaluation_start'] == '2025-01-01'
        assert cfg['prior_registered'] == prior
        assert cfg['budget_cap'] == cap
        assert cfg['new_definitions'] == count
        assert cfg['external_registered_definitions'] == 8
        assert len(cfg['mechanisms']) == count


def test_batch17_minute_amount_impact_hand_formula_scale_and_prefix():
    cal = pd.bdate_range('2024-01-02', periods=1)
    b = bars('2024-01-02')
    b['open'] = 100.0
    b['close'] = b['open'] * (1.0 + np.where(np.arange(240) % 3 == 0, 0.002, -0.001))
    b['high'] = np.maximum(b['open'], b['close']) + 1.0
    b['low'] = np.minimum(b['open'], b['close']) - 1.0
    b['volume'] = np.linspace(100.0, 500.0, 240)
    b['turnover'] = b['volume'] * 100.0
    daily, audit = minute_daily(b, cal)
    assert audit['complete_days'] == 1
    m = b.close.to_numpy() / b.open.to_numpy() - 1.0
    amount_share = b.turnover.to_numpy() / b.turnover.sum()
    expected_price_impact = np.sum(amount_share * np.abs(m))
    expected_signed_impact = np.sum(amount_share * m)
    assert daily.iloc[0].minute_amount_price_impact == pytest.approx(expected_price_impact)
    assert daily.iloc[0].minute_amount_signed_impact == pytest.approx(expected_signed_impact)
    assert daily.iloc[0].minute_amount_impact_time_position >= 0
    assert daily.iloc[0].minute_amount_impact_time_position <= 1
    assert minute_daily(b.iloc[:-1], cal)[0].iloc[0].isna().all()

    panel_index = pd.bdate_range('2024-01-02', periods=40)
    panels = {
        name: pd.DataFrame(
            np.linspace(0.01, 0.2, len(panel_index) * 2).reshape(len(panel_index), 2),
            index=panel_index, columns=['a', 'b']
        )
        for name in MINUTE_NAMES
    }
    cfg = yaml.safe_load(open(
        'frameworks/etf_rotation/configs/group_ic20_batch17_minute_20260923.yaml'
    ))
    out = build_atoms(panels, cfg)
    assert list(out) == [f'{name}_20' for name in cfg['mechanisms']]
    assert all(frame.iloc[:19].isna().all().all() for frame in out.values())
    assert all(frame.iloc[19:].notna().all().all() for frame in out.values())
    assert all(leakage_checks(panels, cfg, panel_index[30]).values())


def test_batch17_minute_config_contract():
    cfg = yaml.safe_load(open(
        'frameworks/etf_rotation/configs/group_ic20_batch17_minute_20260923.yaml'
    ))
    assert cfg['purpose'] == 'seen_history_discovery_only'
    assert cfg['discovery_surface'] == '2025_DIRECTION_DISCOVERY_ONLY'
    assert cfg['as_of'] == '2025-12-31'
    assert cfg['prior_registered'] == 260
    assert cfg['budget_cap'] == 270
    assert cfg['new_definitions'] == 10
    assert cfg['external_registered_definitions'] == 8
    assert len(cfg['mechanisms']) == 10
    assert all(item['direction'] == 1 for item in cfg['mechanisms'].values())


def test_batch17_stage2_minute_aliases_equal_raw_times_direction():
    cal = pd.bdate_range('2024-01-02', periods=40)
    x = np.linspace(0.01, 0.2, len(cal) * 2).reshape(len(cal), 2)
    panels = {name: pd.DataFrame(x, index=cal, columns=['a', 'b']) for name in MINUTE_NAMES}
    aliases = {
        'd2025_minute_amount_price_impact': ('minute_amount_price_impact', 1),
        'd2025_minute_amount_signed_impact': ('minute_amount_signed_impact', 1),
        'd2025_minute_amount_directional_consistency': ('minute_amount_directional_consistency', 1),
        'd2025_minute_amount_impact_late_share': ('minute_amount_impact_late_share', -1),
        'd2025_minute_amount_impact_phase_shift': ('minute_amount_impact_phase_shift', -1),
        'd2025_minute_amount_impact_sign_transition': ('minute_amount_impact_sign_transition', 1),
        'd2025_minute_amount_reversal_impact_share': ('minute_amount_reversal_impact_share', -1),
        'd2025_minute_amount_range_pressure': ('minute_amount_range_pressure', 1),
        'd2025_minute_amount_return_range_absorption': ('minute_amount_return_range_absorption', 1),
        'd2025_minute_amount_impact_time_position': ('minute_amount_impact_time_position', -1),
    }
    raw_cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        raw: {'direction': 1} for raw, _ in aliases.values()
    }}
    alias_cfg = {'source_type': 'minute', 'windows': [20], 'mechanisms': {
        alias: {'direction': sign} for alias, (_, sign) in aliases.items()
    }}
    raw = build_atoms(panels, raw_cfg)
    alias = build_atoms(panels, alias_cfg)
    for a, (r, s) in aliases.items():
        pd.testing.assert_frame_equal(alias[f'{a}_20'], raw[f'{r}_20'] * s)
    assert all(leakage_checks(panels, alias_cfg, cal[30]).values())


def test_self_state_uses_prior_only_normalization():
    cal=pd.bdate_range('2024-01-01',periods=80)
    x=pd.DataFrame({'a':np.arange(80,dtype=float)},index=cal)
    cfg={'source_type':'self_state','windows':[60],'mechanisms':{'own_test':{'direction':1}}}
    out=build_atoms({'own_test':x},cfg)['own_test_60']
    assert out.iloc[:60].isna().all().all()
    expected=(60-np.arange(60).mean())/np.arange(60).std(ddof=1)
    assert out.iloc[60,0]==pytest.approx(expected)
    changed=x.copy()
    changed.iloc[60,0]=600
    now=build_atoms({'own_test':changed},cfg)['own_test_60']
    assert now.iloc[60,0]==pytest.approx((600-np.arange(60).mean())/np.arange(60).std(ddof=1))
    assert all(leakage_checks({'own_test':x},cfg,cal[65]).values())


def test_nav_matches_valuation_day_price_not_current_price():
    cal=pd.bdate_range('2024-01-02',periods=4)
    raw=pd.DataFrame({'nav_date':[cal[0]],'ann_date':[cal[1]],'usable_from_date':[cal[2]],'unit_nav':[1.]})
    price=pd.DataFrame({'trade_date':cal,'close':[1.01,1.1,1.2,1.3],'price_basis':'unadjusted'})
    s,_=nav_daily(raw,price,cal)
    assert s.iloc[:2].isna().all()
    assert s.iloc[2]==pytest.approx(.01)
    assert s.iloc[3]==pytest.approx(.01)
    raw.loc[0,'ann_date']=pd.NaT
    with pytest.raises(ValueError,match='timing missing'):
        nav_daily(raw,price,cal)


def test_nav_rejects_publication_before_valuation():
    cal=pd.bdate_range('2024-01-02',periods=4)
    raw=pd.DataFrame({'nav_date':[cal[1]],'ann_date':[cal[0]],'usable_from_date':[cal[2]],'unit_nav':[1.]})
    price=pd.DataFrame({'trade_date':cal,'close':1.,'price_basis':'unadjusted'})
    with pytest.raises(ValueError,match='ordering'):
        nav_daily(raw,price,cal)


def test_late_old_nav_cannot_replace_newer_known_valuation():
    cal=pd.bdate_range('2024-01-02',periods=5)
    raw=pd.DataFrame({'nav_date':[cal[0],cal[1]],
        'ann_date':[cal[3],cal[1]],'usable_from_date':[cal[4],cal[2]],'unit_nav':[.5,1.]})
    price=pd.DataFrame({'trade_date':cal,'close':1.1,'price_basis':'unadjusted'})
    s,a=nav_daily(raw,price,cal)
    assert s.iloc[-1]==pytest.approx(.1)
    assert a['late_older_valuations_ignored']==1


def test_future_nav_prices_cannot_change_earlier_scores():
    cal=pd.bdate_range('2024-01-02',periods=5)
    raw=pd.DataFrame({'nav_date':cal[:4],'ann_date':cal[:4],
                      'usable_from_date':cal[1:],'unit_nav':1.})
    price=pd.DataFrame({'trade_date':cal,'close':1.1,'price_basis':'unadjusted'})
    a,_=nav_daily(raw,price,cal)
    price.loc[price.trade_date>cal[2],'close']=9.
    raw.loc[raw.usable_from_date>cal[2],'unit_nav']=5.
    b,_=nav_daily(raw,price,cal)
    pd.testing.assert_series_equal(a.loc[:cal[2]],b.loc[:cal[2]])


# --- Batch23: share-amount cross family --------------------------------

_SHARE_AMOUNT_NAMES=['share_amount_flow_divergence_corr','share_amount_tail_mismatch_rate',
    'share_flow_amount_signed_alignment','share_lag_amount_abs_corr',
    'share_amount_ratio_dispersion','share_flow_amount_conditional_asymmetry']


def _share_amount_panels(seed=7,periods=90,cols=('a','b')):
    cal=pd.bdate_range('2024-01-01',periods=periods)
    rng=np.random.default_rng(seed)
    shares=pd.DataFrame(1000+np.cumsum(rng.normal(0,5,(periods,len(cols))),axis=0),index=cal,columns=cols)
    amount=pd.DataFrame(np.exp(rng.normal(15,0.3,(periods,len(cols)))),index=cal,columns=cols)
    close=pd.DataFrame(100+np.cumsum(rng.normal(0,1,(periods,len(cols))),axis=0),index=cal,columns=cols)
    return cal,shares,amount,close


def test_share_amount_requires_amount_panel():
    _,shares,_,close=_share_amount_panels()
    cfg={'source_type':'share','windows':[20],
         'mechanisms':{'share_amount_flow_divergence_corr':{'direction':1}}}
    with pytest.raises(KeyError,match='requires amount panel'):
        build_atoms({'shares':shares,'close':close},cfg)


def test_share_amount_hand_formulas():
    cal,shares,amount,close=_share_amount_panels()
    panels={'shares':shares,'amount':amount,'close':close}
    cfg={'source_type':'share','windows':[20],
         'mechanisms':{n:{'direction':1} for n in _SHARE_AMOUNT_NAMES}}
    out=build_atoms(panels,cfg)
    assert set(out)=={f'{n}_20' for n in _SHARE_AMOUNT_NAMES}

    flow=np.log(shares).diff()
    innovation=np.log(amount).diff()
    complete=flow.notna()&innovation.notna()
    complete_count=complete.astype(float).rolling(20,min_periods=20).sum()

    expected_corr=flow.rolling(20,min_periods=20).corr(innovation).where(complete_count.eq(20))
    pd.testing.assert_frame_equal(out['share_amount_flow_divergence_corr_20'],expected_corr)

    flow_tail=flow.abs()>flow.abs().rolling(20,min_periods=20).mean()
    innovation_tail=innovation.abs()>innovation.abs().rolling(20,min_periods=20).mean()
    mismatch=(flow_tail^innovation_tail).astype(float)
    expected_mismatch=mismatch.where(complete).rolling(20,min_periods=20).mean().where(complete_count.eq(20))
    pd.testing.assert_frame_equal(out['share_amount_tail_mismatch_rate_20'],expected_mismatch)

    expected_alignment=(np.sign(flow)*np.sign(innovation)).where(complete).rolling(
        20,min_periods=20).mean().where(complete_count.eq(20))
    pd.testing.assert_frame_equal(out['share_flow_amount_signed_alignment_20'],expected_alignment)

    lagged_flow=flow.shift(1)
    lag_complete=lagged_flow.notna()&innovation.notna()
    lag_complete_count=lag_complete.astype(float).rolling(20,min_periods=20).sum()
    expected_lag_corr=lagged_flow.rolling(20,min_periods=20).corr(innovation.abs()).where(
        lag_complete_count.eq(20))
    pd.testing.assert_frame_equal(out['share_lag_amount_abs_corr_20'],expected_lag_corr)

    flow_pct=flow.abs().rolling(20,min_periods=20).rank(pct=True)
    innovation_pct=innovation.abs().rolling(20,min_periods=20).rank(pct=True)
    rank_gap=(flow_pct-innovation_pct).where(complete)
    expected_dispersion=rank_gap.rolling(20,min_periods=20).std().where(complete_count.eq(20))
    pd.testing.assert_frame_equal(out['share_amount_ratio_dispersion_20'],expected_dispersion)

    positive=innovation.gt(0).where(innovation.notna())
    positive_bool=positive.astype('boolean').fillna(False)
    valid=flow.notna()&positive.notna()
    pos_mask=positive_bool&valid
    neg_mask=(~positive_bool)&valid
    pos_count=pos_mask.astype(float).rolling(20,min_periods=1).sum()
    neg_count=neg_mask.astype(float).rolling(20,min_periods=1).sum()
    pos_mean=flow.abs().where(pos_mask).rolling(20,min_periods=1).sum().div(pos_count.where(pos_count.gt(0)))
    neg_mean=flow.abs().where(neg_mask).rolling(20,min_periods=1).sum().div(neg_count.where(neg_count.gt(0)))
    expected_asymmetry=(pos_mean-neg_mean).where(complete_count.eq(20)&pos_count.gt(0)&neg_count.gt(0))
    pd.testing.assert_frame_equal(
        out['share_flow_amount_conditional_asymmetry_20'],expected_asymmetry)


def test_share_amount_direction_applies_and_missing_amount_masks_only_after_gap():
    cal,shares,amount,close=_share_amount_panels()
    panels={'shares':shares,'amount':amount,'close':close}
    positive_cfg={'source_type':'share','windows':[20],
        'mechanisms':{'share_flow_amount_signed_alignment':{'direction':1}}}
    negative_cfg={'source_type':'share','windows':[20],
        'mechanisms':{'share_flow_amount_signed_alignment':{'direction':-1}}}
    pos=build_atoms(panels,positive_cfg)['share_flow_amount_signed_alignment_20']
    neg=build_atoms(panels,negative_cfg)['share_flow_amount_signed_alignment_20']
    pd.testing.assert_frame_equal(neg,-pos)

    amount_gap=amount.copy()
    amount_gap.iloc[40,0]=np.nan
    out=build_atoms({'shares':shares,'amount':amount_gap,'close':close},positive_cfg)[
        'share_flow_amount_signed_alignment_20']
    assert pd.isna(out.iloc[40,0])
    assert pd.isna(out.iloc[60,0])
    assert pd.notna(out.iloc[61,0])


def test_share_amount_ratio_dispersion_bounded_when_amount_is_near_static():
    # Regression for the pre-run structural diagnostic on 513100.SH: amount
    # innovation collapsing towards zero must not blow up the ratio.
    cal,shares,amount,close=_share_amount_panels(periods=90)
    degenerate_amount=amount.copy()
    degenerate_amount['a']=100.0  # constant turnover -> log-diff innovation == 0
    cfg={'source_type':'share','windows':[20],
         'mechanisms':{'share_amount_ratio_dispersion':{'direction':1}}}
    out=build_atoms({'shares':shares,'amount':degenerate_amount,'close':close},cfg)[
        'share_amount_ratio_dispersion_20']
    finite=out['a'].dropna()
    assert len(finite)>0
    assert np.isfinite(finite).all()
    assert (finite.abs()<=1.0).all()


def test_share_amount_leakage_checks_pass_for_all_definitions():
    cal,shares,amount,close=_share_amount_panels(periods=110)
    panels={'shares':shares,'amount':amount,'close':close}
    cfg={'source_type':'share','windows':[20],
         'mechanisms':{n:{'direction':1} for n in _SHARE_AMOUNT_NAMES}}
    assert all(leakage_checks(panels,cfg,cal[80]).values())


# --- Round2 (Batch24): minute intraday volume-shape family ------------

def test_round2_bucket_boundaries_match_timestamps_not_positions():
    # bar 0 = 09:31. 11:01-11:30 is minute-of-day 661-690 -> array index
    # 90:120 (NOT 100:120). 13:01-13:30 is 781-810 -> array index 120:150.
    # So midday = index 90:150 (60 bars), not 100:150 (50 bars).
    b=bars('2024-01-02')
    times=(b.datetime.dt.hour*60+b.datetime.dt.minute).to_numpy()
    opening=(times>=571)&(times<=600)
    closing=(times>=871)&(times<=900)
    midday=((times>=661)&(times<=690))|((times>=781)&(times<=810))
    assert opening.sum()==30
    assert closing.sum()==30
    assert midday.sum()==60
    assert opening.sum()+closing.sum()+midday.sum()<240
    assert np.flatnonzero(opening).tolist()==list(range(0,30))
    assert np.flatnonzero(closing).tolist()==list(range(210,240))
    assert np.flatnonzero(midday).tolist()==list(range(90,150))


def test_round2_minute_volume_shape_hand_formulas_and_fixed_bar_buckets():
    cal=pd.bdate_range('2024-01-02',periods=1)
    b=bars('2024-01-02')
    # Deterministic, non-monotonic volume so opening/midday/closing/rest
    # buckets are all distinguishable by construction.
    volume=np.zeros(240)
    volume[:30]=10.0       # opening 30min: 09:31-10:00 (bar index 0:30)
    volume[30:90]=1.0      # 10:01-11:00, excluded from every bucket below
    volume[90:150]=5.0     # midday: 11:01-11:30 + 13:01-13:30 (index 90:150)
    volume[150:210]=1.0    # 13:31-14:30, excluded
    volume[210:240]=20.0   # closing 30min: 14:31-15:00 (index 210:240)
    b['volume']=volume
    b['turnover']=volume*(b['close'])
    out,_=minute_daily(b,cal)
    row=out.iloc[0]

    total=volume.sum()
    expected_u_shape=(volume[:30].sum()+volume[210:240].sum())/total
    expected_midday=volume[90:150].sum()/total
    expected_opening_share=volume[:30].sum()/total
    expected_absorption=volume[:5].sum()/volume[:30].sum()
    expected_closing_abs_return=abs(b['close'].iloc[239]/b['open'].iloc[210]-1.0)

    assert row.minute_volume_u_shape_ratio==pytest.approx(expected_u_shape)
    assert row.minute_volume_midday_share==pytest.approx(expected_midday)
    assert row.minute_volume_opening_share==pytest.approx(expected_opening_share)
    assert row.minute_volume_opening_absorption_speed==pytest.approx(expected_absorption)
    assert row.minute_volume_closing_session_abs_return==pytest.approx(expected_closing_abs_return)
    # Sanity: buckets sum to <= total and are mutually exclusive by construction.
    assert expected_u_shape+expected_midday<1.0


def test_round2_halt_to_1030_day_marks_volume_shape_scalars_missing():
    cal=pd.bdate_range('2024-01-02',periods=2)
    normal_day=bars('2024-01-02')
    halted_day=bars('2024-01-03')
    halted_volume=(np.arange(240)+100).astype(float)
    halted_volume[:60]=0.0  # 09:31-10:30 all zero: opening-auction halt
    halted_day['volume']=halted_volume
    halted_day['turnover']=halted_volume*halted_day['close']
    both=pd.concat([normal_day,halted_day],ignore_index=True)
    out,_=minute_daily(both,cal)

    assert pd.notna(out.iloc[0].minute_volume_u_shape_ratio)
    for col in ('minute_volume_u_shape_ratio','minute_volume_gini',
                'minute_volume_opening_absorption_speed','minute_volume_opening_share',
                'minute_volume_closing_session_abs_return','minute_volume_midday_share'):
        assert pd.isna(out.iloc[1][col]),col
    # A halt day is still a genuine, valid 240-bar session for every other
    # already-registered minute mechanism; it must not be NaN'd here.
    assert pd.notna(out.iloc[1].minute_late_return)
    assert pd.notna(out.iloc[1].minute_volume_entropy)


def test_round2_min_periods_15_tolerates_up_to_5_halt_days_midday_and_lead():
    cal=pd.bdate_range('2024-01-01',periods=40)
    t=np.arange(len(cal),dtype=float)
    rng=np.random.default_rng(5)
    u_shape=pd.DataFrame(0.4+0.05*np.cos(t[:,None]/6+np.arange(14)),index=cal)
    midday=pd.DataFrame(0.2+0.02*np.sin(t[:,None]/4+np.arange(14)),index=cal)
    opening_share=pd.DataFrame(0.3+0.05*np.sin(t[:,None]/5+np.arange(14)),index=cal)
    closing_abs_return=pd.DataFrame(np.abs(rng.normal(0,0.01,(len(cal),14))),index=cal)
    # Knock out 5 of the last 20 rows for column 0 only, leaving exactly 15.
    halt_rows=cal[21:26]
    for frame in (u_shape,midday,opening_share,closing_abs_return):
        frame.loc[halt_rows,0]=np.nan
    minute_panels={n:pd.DataFrame(0.1+0.01*np.repeat(np.sin(t[:,None]/(i+2)),14,axis=1),index=cal)
                   for i,n in enumerate(MINUTE_NAMES)}
    minute_panels['minute_volume_u_shape_ratio']=u_shape
    minute_panels['minute_volume_midday_share']=midday
    minute_panels['minute_volume_opening_share']=opening_share
    minute_panels['minute_volume_closing_session_abs_return']=closing_abs_return

    midday_cfg={'source_type':'minute','windows':[20],
        'mechanisms':{'minute_volume_midday_share':{'direction':1}}}
    midday_out=build_atoms(minute_panels,midday_cfg)['minute_volume_midday_share_20']
    assert pd.notna(midday_out.iloc[39,0])

    lead_cfg={'source_type':'minute','windows':[20],
        'mechanisms':{'minute_volume_return_concentration_lead':{'direction':1}}}
    lead_out=build_atoms(minute_panels,lead_cfg)['minute_volume_return_concentration_lead_20']
    assert pd.notna(lead_out.iloc[39,0])

    # A window that is only 5 for a non-registered size must not crash on
    # min_periods > window; the relaxed threshold applies only at w=20.
    midday_cfg5={'source_type':'minute','windows':[5],
        'mechanisms':{'minute_volume_midday_share':{'direction':1}}}
    build_atoms(minute_panels,midday_cfg5)


def test_round2_shape_persistence_tolerates_nonadjacent_halt_days():
    # Self-lag doubles each halt day's blast radius: shape.shift(1) shifts
    # the NaN one row later, so one halt day removes 2 rows from the pair
    # count, not 1. Two non-adjacent halt days leave 20-4=16 >= 15 pairs.
    cal=pd.bdate_range('2024-01-01',periods=40)
    t=np.arange(len(cal),dtype=float)
    u_shape=pd.DataFrame(0.4+0.05*np.cos(t[:,None]/6+np.arange(14)),index=cal)
    halt_rows=[cal[22],cal[30]]
    u_shape.loc[halt_rows,0]=np.nan
    minute_panels={n:pd.DataFrame(0.1+0.01*np.repeat(np.sin(t[:,None]/(i+2)),14,axis=1),index=cal)
                   for i,n in enumerate(MINUTE_NAMES)}
    minute_panels['minute_volume_u_shape_ratio']=u_shape
    persistence_cfg={'source_type':'minute','windows':[20],
        'mechanisms':{'minute_volume_shape_persistence':{'direction':1}}}
    persistence_out=build_atoms(minute_panels,persistence_cfg)['minute_volume_shape_persistence_20']
    assert pd.notna(persistence_out.iloc[39,0])


def test_round2_minute_volume_gini_known_cases():
    cal=pd.bdate_range('2024-01-02',periods=2)
    equal_day=bars('2024-01-02')
    equal_day['volume']=100.0
    equal_day['turnover']=equal_day['volume']*equal_day['close']
    skewed_day=bars('2024-01-03')
    skewed_volume=np.full(240,1.0)
    skewed_volume[0]=10000.0  # one bar dominates the whole session
    skewed_day['volume']=skewed_volume
    skewed_day['turnover']=skewed_day['volume']*skewed_day['close']
    both=pd.concat([equal_day,skewed_day],ignore_index=True)
    out,_=minute_daily(both,cal)
    assert out.iloc[0].minute_volume_gini==pytest.approx(0.0,abs=1e-9)
    assert out.iloc[1].minute_volume_gini>0.9


def test_round2_special_dispatch_requires_helper_panels():
    cal=pd.bdate_range('2024-01-01',periods=40)
    x=pd.DataFrame(np.arange(40*14,dtype=float).reshape(40,14),index=cal)
    lead_cfg={'source_type':'minute','windows':[20],
        'mechanisms':{'minute_volume_return_concentration_lead':{'direction':1}}}
    incomplete_names=[n for n in MINUTE_NAMES if n not in (
        'minute_volume_opening_share','minute_volume_closing_session_abs_return')]
    with pytest.raises(KeyError,match='opening-share/closing-abs-return'):
        build_atoms({n:x+1 for n in incomplete_names},lead_cfg)
    persistence_cfg={'source_type':'minute','windows':[20],
        'mechanisms':{'minute_volume_shape_persistence':{'direction':1}}}
    with pytest.raises(KeyError):
        build_atoms({n:x+1 for n in MINUTE_NAMES if n!='minute_volume_u_shape_ratio'},persistence_cfg)


def test_round2_special_dispatch_hand_formulas_and_leakage():
    cal=pd.bdate_range('2024-01-01',periods=90)
    t=np.arange(len(cal),dtype=float)
    rng=np.random.default_rng(11)
    opening_share=pd.DataFrame(0.3+0.05*np.sin(t[:,None]/5+np.arange(14)),index=cal)
    closing_abs_return=pd.DataFrame(np.abs(rng.normal(0,0.01,(len(cal),14))),index=cal)
    u_shape=pd.DataFrame(0.4+0.05*np.cos(t[:,None]/6+np.arange(14)),index=cal)
    minute_panels={n:pd.DataFrame(0.1+0.01*np.repeat(np.sin(t[:,None]/(i+2)),14,axis=1),index=cal)
                   for i,n in enumerate(MINUTE_NAMES)}
    minute_panels['minute_volume_opening_share']=opening_share
    minute_panels['minute_volume_closing_session_abs_return']=closing_abs_return
    minute_panels['minute_volume_u_shape_ratio']=u_shape

    # min_periods=15 (not 20): the halt-day tolerance rule. With fully dense
    # synthetic data this only changes how early the window opens, not any
    # value once 20 observations are available.
    lead_cfg={'source_type':'minute','windows':[20],
        'mechanisms':{'minute_volume_return_concentration_lead':{'direction':1}}}
    lead_out=build_atoms(minute_panels,lead_cfg)['minute_volume_return_concentration_lead_20']
    expected_lead=opening_share.rolling(20,min_periods=15).corr(closing_abs_return)
    pd.testing.assert_frame_equal(lead_out,expected_lead)
    assert lead_out.iloc[13].isna().all()
    assert lead_out.iloc[14].notna().all()

    persistence_cfg={'source_type':'minute','windows':[20],
        'mechanisms':{'minute_volume_shape_persistence':{'direction':1}}}
    persistence_out=build_atoms(minute_panels,persistence_cfg)['minute_volume_shape_persistence_20']
    expected_persistence=u_shape.rolling(20,min_periods=15).corr(u_shape.shift(1))
    pd.testing.assert_frame_equal(persistence_out,expected_persistence)

    assert all(leakage_checks(minute_panels,lead_cfg,cal[60]).values())
    assert all(leakage_checks(minute_panels,persistence_cfg,cal[60]).values())
