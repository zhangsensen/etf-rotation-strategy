"""Research extension must not rewrite the certified historical prefix."""
import pandas as pd

from extend_legacy_data import append_only, materialize
from build_statement import period_stats


def test_append_keeps_old_observations_despite_vendor_revisions():
    old = pd.DataFrame({'trade_date': ['20260210', '20260211'], 'value': [10., 11.]})
    new = pd.DataFrame({'trade_date': ['20260211', '20260212'], 'value': [999., 12.]})
    result = append_only(old, new)
    assert result.value.tolist() == [10., 11., 12.]


def test_extension_adjusts_future_split_without_rewriting_old_prices(tmp_path):
    legacy, output = tmp_path / 'old', tmp_path / 'new'
    base = legacy / 'raw/ETF'
    for folder in ['daily', 'fund_share', 'margin']:
        (base / folder).mkdir(parents=True)
    dates = ['20260210', '20260211', '20260212']
    old = pd.DataFrame({'trade_date': dates[:2], 'adj_open': [9., 10.],
                        'adj_high': [9., 10.], 'adj_low': [9., 10.],
                        'adj_close': [9., 10.], 'vol': [100., 200.]})
    old.to_parquet(base / 'daily/510300.SH_daily_test.parquet')
    share = pd.DataFrame({'trade_date': dates[:2], 'ts_code': '510300.SH', 'fd_share': [100., 101.]})
    share.to_parquet(base / 'fund_share/fund_share_510300.parquet')
    margin = pd.DataFrame({'trade_date': dates[:2], 'ts_code': '510300.SH', 'rzye': [100., 101.]})
    margin.to_parquet(base / 'margin/margin_pool43_2020_now.parquet')
    vendor = output / 'vendor'
    for folder in ['fund_daily', 'fund_adj', 'fund_share', 'margin_detail']:
        (vendor / folder).mkdir(parents=True)
    daily = pd.DataFrame({'trade_date': dates, 'open': [9., 10., 5.5],
                          'high': [9., 10., 5.5], 'low': [9., 10., 5.5],
                          'close': [9., 10., 5.5], 'vol': [100., 200., 300.]})
    daily.to_parquet(vendor / 'fund_daily/510300.SH.parquet')
    pd.DataFrame({'trade_date': dates, 'adj_factor': [1., 1., 2.]}).to_parquet(vendor / 'fund_adj/510300.SH.parquet')
    share.to_parquet(vendor / 'fund_share/510300.SH.parquet')
    margin.to_parquet(vendor / 'margin_detail/510300.SH.parquet')
    materialize(legacy, output, ['510300.SH'], '20260212')
    result = pd.read_parquet(output / 'data/ETF/daily/510300.SH_daily_research.parquet')
    assert result.adj_close.tolist() == [9., 10., 11.]
    assert result.vol.tolist() == [100., 200., 300.]
    pd.testing.assert_frame_equal(pd.read_parquet(base / 'daily/510300.SH_daily_test.parquet'), old)


def test_continuation_returns_use_existing_capital_and_peak():
    equity = pd.Series([100., 200., 180., 220.], index=pd.date_range('2026-02-09', periods=4))
    result = period_stats(equity, '2026-02-10', '2026-02-12')
    assert abs(result['return'] - .1) < 1e-12
    assert abs(result['max_drawdown'] - .1) < 1e-12
