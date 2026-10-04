#!/usr/bin/env python3
"""Repository-root read-only entry for the integrated ETF research package."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frameworks/etf_rotation/src"))

from etf_strategy.canonical_data import load_canonical_daily, reference_factors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--as-of", required=True, help="Completed trading date, YYYY-MM-DD")
    parser.add_argument("--universe", type=Path, default=ROOT / "config/etf_rotation_universe_v1.json")
    parser.add_argument("--roles", nargs="+", help="Omit to inspect all maintained ETFs")
    args = parser.parse_args()
    prices = load_canonical_daily(args.data_root, args.universe, as_of=args.as_of,
                                  roles=tuple(args.roles) if args.roles else None)
    factors = reference_factors(prices)
    print(json.dumps({
        "status": "DATA_AND_FACTOR_SMOKE_PASS",
        "as_of": args.as_of,
        "symbols": len(prices["close"].columns),
        "daily_observations": int(prices["close"].notna().sum().sum()),
        "first_date": str(prices["close"].index.min().date()),
        "factor_nonnull_counts": {k: int(v.notna().sum().sum()) for k, v in factors.items()},
        "factor_available_symbols_as_of": {k: int(v.iloc[-1].notna().sum()) for k, v in factors.items()},
        "price_basis": "adjusted research view; not execution prices",
        "scope": "Engineering smoke only; no returns, ranking or strategy certification",
    }, indent=2))


if __name__ == "__main__":
    main()
