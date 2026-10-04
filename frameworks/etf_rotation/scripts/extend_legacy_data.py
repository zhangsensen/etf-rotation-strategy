"""Fetch a bounded local research extension of the sealed ETF universe.

Never writes to the old project or the maintained twenty-ETF production store.
Retains historical adjusted prices verbatim and extends them at the old anchor.
This reproduces legacy research units (including volume in hands), not execution
quotes. No strategy parameters are selected by this program.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from data.downloaders.etf_rotation_backfill import tushare_client


def fetch_one(symbol, output, end, pro):
    counts = {}
    for endpoint in ('fund_daily', 'fund_adj', 'fund_share', 'margin_detail'):
        path = output / 'vendor' / endpoint / f'{symbol}.parquet'
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            frame = pd.read_parquet(path)
        else:
            error = None
            for attempt in range(2):
                try:
                    frame = getattr(pro, endpoint)(ts_code=symbol, start_date='20260201', end_date=end)
                    frame.to_parquet(path, index=False)
                    error = None
                    break
                except Exception as exc:
                    error = type(exc).__name__
                    time.sleep(1)
            if error:
                raise RuntimeError(f'{symbol} {endpoint}: {error}')
        counts[endpoint] = {'rows': len(frame), 'last': str(frame.trade_date.max()) if len(frame) else None}
    return symbol, counts


def dated(frame):
    frame = frame.copy()
    text = frame.trade_date.astype(str).str.replace('-', '', regex=False).str[:8]
    frame['trade_date'] = pd.to_datetime(text, format='%Y%m%d')
    return frame.sort_values('trade_date').reset_index(drop=True)


def append_only(old, new):
    old, new = dated(old), dated(new)
    if old.empty:
        return new
    return pd.concat([old, new[new.trade_date > old.trade_date.max()]], ignore_index=True)


def materialize(legacy, output, symbols, end):
    base = legacy / 'raw/ETF'
    target = output / 'data/ETF'
    for name in ('daily', 'fund_share', 'margin'):
        (target / name).mkdir(parents=True, exist_ok=True)
    audit = []
    margin_old = dated(pd.read_parquet(base / 'margin/margin_pool43_2020_now.parquet'))
    margins = []
    for symbol in symbols:
        code = symbol.split('.')[0]
        old = dated(pd.read_parquet(next((base / 'daily').glob(f'{symbol}_daily_*.parquet'))))
        raw = dated(pd.read_parquet(output / 'vendor/fund_daily' / f'{symbol}.parquet'))
        factors = dated(pd.read_parquet(output / 'vendor/fund_adj' / f'{symbol}.parquet'))
        assert not raw.trade_date.duplicated().any(), symbol
        assert not factors.trade_date.duplicated().any(), symbol
        full = raw.merge(factors[['trade_date', 'adj_factor']], on='trade_date', how='left', validate='one_to_one')
        if full.adj_factor.isna().any() or (full.adj_factor <= 0).any():
            raise ValueError(f'{symbol}: missing adjustment factors')
        anchor = old.iloc[-1]
        match = full[full.trade_date.eq(anchor.trade_date)]
        if len(match) != 1:
            raise ValueError(f'{symbol}: missing overlap anchor')
        at = match.iloc[0]
        # Keep old history and extend split/dividend-adjusted returns in its units.
        scale = float(anchor.adj_close / (at.close * at.adj_factor))
        additional = full[full.trade_date > anchor.trade_date].copy()
        if additional.empty or additional.trade_date.max() != pd.Timestamp(end):
            raise ValueError(f'{symbol}: daily does not reach {end}')
        fresh = pd.DataFrame({'trade_date': additional.trade_date})
        for field in ('open', 'high', 'low', 'close'):
            fresh['adj_' + field] = additional[field] * additional.adj_factor * scale
        fresh['vol'] = additional.vol  # Legacy units are hands; do not silently convert.
        price_columns = ['adj_open', 'adj_high', 'adj_low', 'adj_close']
        if (not np.isfinite(fresh[price_columns + ['vol']].to_numpy()).all()
                or (fresh[price_columns] <= 0).any().any() or (fresh.vol < 0).any()
                or (fresh.adj_high < fresh[price_columns].max(axis=1)).any()
                or (fresh.adj_low > fresh[price_columns].min(axis=1)).any()):
            raise ValueError(f'{symbol}: invalid new OHLCV')
        combined = pd.concat([old, fresh], ignore_index=True)
        for field in ('adj_open', 'adj_high', 'adj_low', 'adj_close', 'vol'):
            assert np.array_equal(combined[field].iloc[:len(old)].values, old[field].values, equal_nan=True)
        # Old loader parses YYYYMMDD exactly.
        combined['trade_date'] = combined.trade_date.dt.strftime('%Y%m%d')
        combined.to_parquet(target / 'daily' / f'{symbol}_daily_research.parquet', index=False)
        shares_old = pd.read_parquet(base / 'fund_share' / f'fund_share_{code}.parquet')
        shares_new = pd.read_parquet(output / 'vendor/fund_share' / f'{symbol}.parquet')
        if shares_new.empty:
            raise ValueError(f'{symbol}: no new fund shares')
        shares = append_only(shares_old, shares_new)
        shares.to_parquet(target / 'fund_share' / f'fund_share_{code}.parquet', index=False)
        old_m = margin_old[margin_old.ts_code.eq(symbol)]
        new_m = pd.read_parquet(output / 'vendor/margin_detail' / f'{symbol}.parquet')
        if new_m.empty:
            merged_m = old_m
        else:
            merged_m = append_only(old_m, new_m)
        if len(merged_m):
            margins.append(merged_m)
        audit.append({'symbol': symbol, 'history_rows_unchanged': len(old), 'new_daily_rows': len(fresh),
                      'daily_last': str(additional.trade_date.max().date()),
                      'fund_share_last': str(shares.trade_date.max().date()),
                      'margin_last': str(merged_m.trade_date.max().date()) if len(merged_m) else None,
                      'old_anchor_date': str(anchor.trade_date.date()), 'old_anchor_price': float(anchor.adj_close),
                      'provider_anchor_price': float(at.close), 'provider_anchor_adj_factor': float(at.adj_factor),
                      'anchor_volume_ratio': float(anchor.vol / at.vol) if at.vol else None,
                      'extension_price_units': 'old_anchor_adjusted_research_price'})
    margin = pd.concat(margins, ignore_index=True)
    margin['trade_date'] = margin.trade_date.dt.strftime('%Y%m%d')
    margin.to_parquet(target / 'margin/margin_pool43_2020_now.parquet', index=False)
    (output / 'coverage.json').write_text(json.dumps(audit, indent=2))
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--end', required=True)
    args = parser.parse_args()
    config = yaml.safe_load((args.legacy_root / 'sealed_strategies/v8.0_20260215/locked/configs/combo_wfo_config.yaml').read_text())
    symbols = [code + ('.SZ' if code.startswith('15') else '.SH') for code in config['data']['symbols']]
    args.output.mkdir(parents=True, exist_ok=True)
    request_path = args.output / 'request.json'
    request = {'legacy_root': str(args.legacy_root.resolve()), 'end': args.end,
               'symbols': symbols, 'vendor_start': '20260201'}
    if request_path.exists() and json.loads(request_path.read_text()) != request:
        raise ValueError('Output directory belongs to a different request; choose a new directory')
    request_path.write_text(json.dumps(request, indent=2))
    pro = tushare_client()
    pro._DataApi__timeout = 20
    statuses = {}
    failures = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(fetch_one, code, args.output, args.end, pro): code for code in symbols}
        for future in as_completed(futures):
            try:
                symbol, status = future.result()
            except Exception as exc:
                failures[futures[future]] = str(exc)
                print("FETCH_FAILED", futures[future], str(exc), flush=True)
                continue
            statuses[symbol] = status
            (args.output / 'download_status.json').write_text(json.dumps(statuses, indent=2))
            print(f'{len(statuses)}/{len(symbols)} {symbol} {status}', flush=True)
    if failures:
        (args.output / "download_failures.json").write_text(json.dumps(failures, indent=2))
        raise RuntimeError("Some downloads failed; rerun uses completed local responses")
    audit = materialize(args.legacy_root, args.output, symbols, args.end)
    print('MATERIALIZED', len(audit), 'symbols', sum(x['new_daily_rows'] for x in audit), 'new daily rows', flush=True)


if __name__ == '__main__':
    main()
