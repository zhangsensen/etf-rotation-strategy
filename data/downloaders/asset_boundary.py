"""Pure asset-boundary checks; no provider, account, logging or I/O initialization."""
from pathlib import Path


def is_fund_code(code: str) -> bool:
    code = code.upper()
    return (code.endswith(".SH") and code.startswith("5")) or (
        code.endswith(".SZ") and code.startswith(("15", "16", "18"))
    )


def assert_asset_root(data_root: Path, asset_class: str) -> None:
    # Include physical path so a symlink cannot disguise the opposite asset root.
    parts = set()
    for value in (str(data_root), str(data_root.resolve())):
        parts.update(value.replace(chr(92), "/").lower().split("/"))
    equity_roots = {"gold_standard", "qmt_gold", "qmt_gold_standard"}
    fund_roots = {"etf_rotation_v1", "etf_qmt_legacy", "tech_etf_ts", "intraday_etf", "t0_etf"}
    if asset_class == "fund" and parts & equity_roots:
        raise ValueError("Fund data cannot be written to the equity root")
    if asset_class == "equity" and parts & fund_roots:
        raise ValueError("Equity data cannot be written to a fund root")
