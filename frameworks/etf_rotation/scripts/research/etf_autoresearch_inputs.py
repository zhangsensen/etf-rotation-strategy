"""Approved, read-only daily input profiles for ETF autoresearch candidates.

Candidate code receives prepared panels only. This module owns the pinned
historical source reads and their conservative alignment to China sessions.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import json
from pathlib import Path
import sys

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[4]
ETF = ROOT / "frameworks/etf_rotation"
if str(ETF / "src") not in sys.path:
    sys.path.insert(0, str(ETF / "src"))
from etf_strategy.project_paths import local_path
from etf_strategy.core import etf_group_sources

BASE_FIELDS = ("open", "high", "low", "close", "volume", "amount")
PINNED_CUTOFF = pd.Timestamp("2026-03-24")
CANONICAL_DATA_ROOT = Path(str(Path(__file__).resolve().parents[4] / "data/etf_rotation_v1"))

# Profile -> reviewed campaign config. The config's path and digest fields are
# rechecked on every load; adding a source requires an explicit reviewed pin.
_CONFIGS = {
    "us_sector": "group_ic_campaign20_r01_sox_specific_20260926.yaml",
    "us_vix": "group_ic_campaign20_r02_vix_risk_20260926.yaml",
    "us_style": "group_ic_campaign20_r03_us_style_20260926.yaml",
    "ext_gold": "group_ic_campaign20_r04_ext_gold_20260926.yaml",
    "ext_copper": "group_ic_campaign20_r05_ext_copper_20260926.yaml",
    "ext_crude": "group_ic_campaign20_r06_ext_crude_20260926.yaml",
    "ext_cnh": "group_ic_campaign20_r07_ext_cnh_20260926.yaml",
    "ext_hktech": "group_ic_campaign20_r08_ext_hktech_20260926.yaml",
    "ext_realrate": "group_ic_campaign20_r09_ext_realrate_20260926.yaml",
    "ext_coal": "group_ic_campaign20_r10_ext_coal_20260926.yaml",
    "minute": "group_discovery_minute_v1.yaml",
    "share": "group_discovery_share_v1.yaml",
    "nav": "group_discovery_nav_v1.yaml",
}
_COLD_PROFILES = frozenset(set(_CONFIGS) - {"minute", "share", "nav"})
_DATA_FOLDER = {"minute": "1m", "share": "fund_share", "nav": "nav"}
_PROFILE_PANELS = {
    "minute": tuple(etf_group_sources.MINUTE_NAMES),
    "share": ("shares",),
    "nav": ("premium",),
}
_SHOCK_PANEL = {
    "us_sector": "us_sector_shock", "us_vix": "us_vix_shock",
    "us_style": "us_style_shock", "ext_gold": "ext_gold_shock",
    "ext_copper": "ext_copper_shock", "ext_crude": "ext_crude_shock",
    "ext_cnh": "ext_cnh_shock", "ext_hktech": "ext_hktech_shock",
    "ext_realrate": "ext_realrate_shock", "ext_coal": "ext_coal_shock",
}
_AVAILABILITY = {
    "daily": "canonical adjusted daily OHLCV through the pinned cold cutoff",
    "minute": "same-session close(D) from 240 valid unadjusted bars; incomplete sessions remain missing",
    "share": "recorded usable_from_date with next-session assumption; values expire after 7 calendar days",
    "nav": "recorded announcement and usable dates; reported NAV basis expires after 7 calendar days; source vintage is not certified",
}
_EXPECTED_FILES = {
    "sox_file": "runtime_outputs/etf_rotation_research/NASDAQSOX_cold_20260324.csv",
    "ndx_file": "runtime_outputs/etf_rotation_research/us_index_source_preflight_20260925/NASDAQ100.csv",
    "vix_file": "runtime_outputs/etf_rotation_research/VIXCLS_cold_20260324.csv",
    "value_file": "runtime_outputs/etf_rotation_research/NASDAQNQUSLV_cold_20260324.csv",
    "growth_file": "runtime_outputs/etf_rotation_research/NASDAQNQUSLG_cold_20260324.csv",
    "gold_file": "runtime_outputs/etf_rotation_research/long_history_proxies/macro/XAUUSD.parquet",
    "copper_file": "runtime_outputs/etf_rotation_research/long_history_proxies/macro/CU.parquet",
    "crude_file": "runtime_outputs/etf_rotation_research/long_history_proxies/macro/SC.parquet",
    "cnh_file": "runtime_outputs/etf_rotation_research/long_history_proxies/macro/USDCNH.parquet",
    "hktech_file": "runtime_outputs/etf_rotation_research/long_history_proxies/HKTECH.parquet",
    "realrate_file": "runtime_outputs/etf_rotation_research/long_history_proxies/macro/us_trycr.parquet",
    "coal_file": "runtime_outputs/etf_rotation_research/long_history_proxies/macro/JM.parquet",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frame_sha(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(repr((tuple(map(str, frame.columns)), str(frame.index.dtype),
                        tuple(map(str, frame.dtypes)))).encode("utf-8"))
    digest.update(pd.util.hash_pandas_object(frame, index=True).to_numpy().tobytes())
    return digest.hexdigest()


def _profile_config(profile: str, root: Path) -> tuple[dict, Path]:
    config_name = _CONFIGS[profile]
    path = root / "frameworks/etf_rotation/configs" / config_name
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"pinned input profile config is missing or symlinked: {path}")
    cfg = yaml.safe_load(path.read_text())
    if cfg.get("source_type") != profile:
        raise ValueError(f"pinned config source_type mismatch: {profile}")
    if profile in _COLD_PROFILES and cfg.get("as_of") != "2026-03-24":
        raise ValueError(f"pinned config cutoff mismatch: {profile}")
    if profile in {"share", "nav"} and cfg.get("max_stale_calendar_days") != 7:
        raise ValueError(f"source profile stale limit differs from existing contract: {profile}")
    if profile in _DATA_FOLDER and local_path(cfg.get("data_root", ""), root) != CANONICAL_DATA_ROOT.resolve():
        raise ValueError(f"source profile data root differs from fixed canonical ETF store: {profile}")
    return cfg, path


def _candidate_symbols(root: Path) -> list[str]:
    path = root / "config/etf_rotation_universe_v1.json"
    rows = json.loads(path.read_text())["etfs"]
    symbols = [row["ts_code"] for row in rows if row["role"] == "candidate"]
    if len(symbols) != 14 or len(set(symbols)) != 14:
        raise ValueError("source profiles require the fixed candidate ETF population")
    return symbols


def _source_file_paths(profile: str, cfg: dict, root: Path, symbols: list[str]) -> list[Path]:
    data_root = local_path(cfg["data_root"])
    folder = _DATA_FOLDER[profile]
    paths = [data_root / folder / f"{symbol}.parquet" for symbol in symbols]
    if profile == "nav":
        paths.extend(data_root / "1d" / f"{symbol}.parquet" for symbol in symbols)
    return paths


def _panel_names(profile: str) -> list[str]:
    if profile in _SHOCK_PANEL:
        return [*BASE_FIELDS, _SHOCK_PANEL[profile]]
    return [*BASE_FIELDS, *_PROFILE_PANELS.get(profile, ())]


def _availability_convention(profile: str) -> str:
    return _AVAILABILITY.get(profile,
        "foreign/source observations strictly before China session; existing core aligner age rules apply")


def _review_contract(profile: str, root: Path) -> dict:
    """Expose panel semantics and timing to candidate reviewers without data."""
    source_root = ROOT / "frameworks/etf_rotation/src/etf_strategy/core"

    def ref(filename: str, symbols: list[str]) -> dict:
        path = source_root / filename
        return {"path": str(path.relative_to(ROOT)), "sha256": _sha(path), "symbols": symbols}

    def excerpt(filename: str, functions: list[str]) -> str:
        path = source_root / filename
        source = path.read_text()
        tree = ast.parse(source)
        wanted = set(functions)
        spans = [(node.lineno, node.end_lineno) for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name in wanted]
        if len(spans) != len(wanted):
            raise ValueError(f"review contract function missing from {filename}: {wanted}")
        lines = source.splitlines()
        return "\n".join("\n".join(lines[start - 1:end]) for start, end in spans)

    contract = {
        "version": 1,
        "availability": _availability_convention(profile),
        "panels": {},
        "source_implementation": [],
        "limitations": [],
    }
    if profile == "daily":
        contract["panels"] = {name: {
            "formula": "Caller-supplied canonical adjusted daily OHLCV field; no transform in this adapter.",
            "availability": "Inherited from upstream panel builder; this adapter only enforces shared dates/columns and cutoff.",
        } for name in BASE_FIELDS}
        adapter = ROOT / "frameworks/etf_rotation/scripts/research/etf_autoresearch_inputs.py"
        contract["source_implementation"] = [{"path": str(adapter.relative_to(ROOT)),
                                              "sha256": _sha(adapter), "symbols": ["load_inputs"]}]
        contract["limitations"].append("Adapter does not independently verify upstream daily adjustment or publication timing.")
        return contract

    if profile == "minute":
        contract["source_implementation"] = [ref("etf_group_sources.py", ["minute_daily"])]
        contract["source_excerpt"] = excerpt("etf_group_sources.py", ["minute_daily"])
        contract["panels"] = {name: {
            "formula": "Daily scalar computed from unadjusted 1-minute OHLC, volume and turnover over the fixed 240 right-edge bars (09:31-11:30, 13:01-15:00); exact feature formulas are in the referenced implementation.",
            "availability": "Same-session close(D), after the final 15:00 bar; available no earlier than the next decision session.",
        } for name in _PROFILE_PANELS[profile]}
        contract["limitations"].append("Any session with missing, duplicate, invalid, nonpositive-price, or non-240 bars yields missing features; no padding/carry. Raw basis is checked as unadjusted.")
        return contract

    if profile == "share":
        contract["source_implementation"] = [ref("etf_group_sources.py", ["share_daily"])]
        contract["source_excerpt"] = excerpt("etf_group_sources.py", ["share_daily"])
        contract["panels"] = {"shares": {
            "formula": "Latest fund_shares observation selected by backward as-of on usable_from_date; same-date collisions keep latest trade_date.",
            "availability": "Recorded usable_from_date, which must follow trade_date; loader treats this as next-session usability, not verified publication time. Values older than 7 calendar days are missing.",
        }}
        contract["limitations"].append("The source records an assumed availability date; publication-time proof is absent.")
        return contract

    if profile == "nav":
        contract["source_implementation"] = [ref("etf_group_sources.py", ["nav_daily"])]
        contract["source_excerpt"] = excerpt("etf_group_sources.py", ["nav_daily"])
        contract["panels"] = {"premium": {
            "formula": "Matched unadjusted ETF close on nav_date divided by reported unit_nav minus 1; backward as-of on usable_from_date, retaining latest valuation date and ignoring late older valuations.",
            "availability": "Only after ann_date and recorded usable_from_date; usable_from_date must follow ann_date. Premium expires when nav_date is more than 7 calendar days old.",
        }}
        contract["limitations"].append("Reported NAV basis can be asynchronous to ETF/underlying valuation clocks, especially QDII; source vintage is not certified. NAV dates without an exact ETF price match are dropped.")
        return contract

    modules = {
        "us_sector": ("etf_group_us_sector.py", "sox-minus-Nasdaq100: difference of common-date daily percentage changes; align latest US shock strictly before China date, max age 5 calendar days."),
        "us_vix": ("etf_group_us_vix.py", "VIX log change; align latest valid US shock strictly before China date, max age 5 calendar days."),
        "us_style": ("etf_group_us_style.py", "US value-index percentage change minus growth-index percentage change on common dates; strict-prior China alignment, max age 5 calendar days."),
        "ext_gold": ("etf_group_ext_gold.py", "Log change of FXCM XAUUSD bid/ask mid; strict-prior China alignment, max age 5 calendar days."),
        "ext_copper": ("etf_group_ext_copper.py", "SHFE copper settlement log change, differenced on its source calendar then exact-date reindexed to China sessions; missing dates remain missing."),
        "ext_crude": ("etf_group_ext_crude.py", "INE crude settlement log change, differenced on its source calendar then exact-date reindexed to China sessions; missing dates remain missing."),
        "ext_cnh": ("etf_group_ext_cnh.py", "Log change of FXCM offshore USDCNH bid/ask mid; strict-prior China alignment, max age 5 calendar days."),
        "ext_hktech": ("etf_group_ext_hktech.py", "Hang Seng Tech close log change; strict-prior HK session because HK closes after A shares, max age 5 calendar days."),
        "ext_realrate": ("etf_group_ext_realrate.py", "Arithmetic first difference of US 10-year real yield in percent (level may be negative); strict-prior alignment, max age 5 calendar days."),
        "ext_coal": ("etf_group_ext_coal.py", "DCE coking-coal settlement log change, differenced on its source calendar then exact-date reindexed to China sessions; missing dates remain missing."),
    }
    filename, formula = modules[profile]
    function_names = {
        "us_sector": ["read_fred", "align_specific_shock"],
        "us_vix": ["read_vix", "align_vix_shock"],
        "us_style": ["read_style", "align_style_shock"],
        "ext_gold": ["read_gold", "align_gold_shock"],
        "ext_copper": ["read_copper", "align_copper_shock"],
        "ext_crude": ["read_crude", "align_crude_shock"],
        "ext_cnh": ["read_cnh", "align_cnh_shock"],
        "ext_hktech": ["read_hktech", "align_hktech_shock"],
        "ext_realrate": ["read_realrate", "align_realrate_shock"],
        "ext_coal": ["read_coal", "align_coal_shock"],
    }[profile]
    contract["source_implementation"] = [ref(filename, function_names)]
    contract["source_excerpt"] = excerpt(filename, function_names)
    shock = _SHOCK_PANEL[profile]
    contract["panels"] = {shock: {
        "formula": formula,
        "availability": "Per-source alignment above; exact-date domestic futures settlement profiles use close(D), while foreign sources exclude same-date observations.",
    }}
    contract["limitations"].append("This panel is a common source shock broadcast across the fixed candidate ETF columns; missing or stale source dates remain missing.")
    return contract


def _load_source_profile(profile: str, panels: dict[str, pd.DataFrame], cfg: dict,
                         root: Path) -> tuple[dict[str, pd.DataFrame], dict[str, str], dict]:
    """Filtered raw reads followed by the existing canonical source transforms."""
    engine = importlib.import_module("etf_strategy.core.etf_group_sources")
    close = panels["close"]
    calendar = close.index
    symbols = list(close.columns)
    data_root = local_path(cfg["data_root"])
    cutoff = close.index.max()
    raw_hashes: dict[str, str] = {}
    diagnostics: dict[str, dict] = {}
    outputs: dict[str, pd.DataFrame] = {}
    prefix_cuts = (pd.Timestamp("2024-12-31"), pd.Timestamp("2025-12-31"))

    for symbol in symbols:
        raw_path = data_root / _DATA_FOLDER[profile] / f"{symbol}.parquet"
        if raw_path.is_symlink() or not raw_path.is_file():
            raise FileNotFoundError(f"{profile} raw source is missing or symlinked: {raw_path}")
        raw_hashes[str(raw_path)] = _sha(raw_path)
        if profile == "minute":
            raw = pd.read_parquet(raw_path, filters=[("datetime", "<", cutoff + pd.Timedelta(days=1))])
            if not raw.ts_code.eq(symbol).all() or not raw.price_basis.eq("unadjusted").all():
                raise ValueError(f"minute identity or price basis mismatch: {symbol}")
            timestamps = pd.to_datetime(raw.datetime)
            if (timestamps.dt.normalize() > cutoff).any():
                raise ValueError(f"minute filter admitted rows after cutoff: {symbol}")
            full, audit = engine.minute_daily(raw, calendar)
            time_col = timestamps.dt.normalize()
        elif profile == "share":
            raw = pd.read_parquet(raw_path, filters=[("usable_from_date", "<=", cutoff)])
            if not raw.ts_code.eq(symbol).all():
                raise ValueError(f"share identity mismatch: {symbol}")
            time_col = pd.to_datetime(raw.usable_from_date)
            if (time_col > cutoff).any():
                raise ValueError(f"share filter admitted rows after cutoff: {symbol}")
            full, audit = engine.share_daily(raw, calendar, cfg["max_stale_calendar_days"])
        else:
            raw = pd.read_parquet(raw_path, filters=[("usable_from_date", "<=", cutoff)])
            price_path = data_root / "1d" / f"{symbol}.parquet"
            if price_path.is_symlink() or not price_path.is_file():
                raise FileNotFoundError(f"NAV matching price source is missing or symlinked: {price_path}")
            raw_hashes[str(price_path)] = _sha(price_path)
            prices = pd.read_parquet(price_path, filters=[("trade_date", "<=", cutoff)])
            if not raw.ts_code.eq(symbol).all() or not prices.ts_code.eq(symbol).all():
                raise ValueError(f"NAV identity mismatch: {symbol}")
            time_col = pd.to_datetime(raw.usable_from_date)
            if (time_col > cutoff).any():
                raise ValueError(f"NAV filter admitted rows after cutoff: {symbol}")
            price_dates = pd.to_datetime(prices.trade_date)
            if (price_dates > cutoff).any():
                raise ValueError(f"NAV price filter admitted rows after cutoff: {symbol}")
            full, audit = engine.nav_daily(raw, prices, calendar, cfg["max_stale_calendar_days"])

        symbol_audit = {"transform": audit, "prefix_reconstruction": {}}
        for prefix_cut in prefix_cuts:
            prefix_calendar = calendar[calendar <= prefix_cut]
            if profile == "minute":
                prefix_raw = raw.loc[time_col <= prefix_cut]
                prefix, _ = engine.minute_daily(prefix_raw, prefix_calendar)
            elif profile == "share":
                prefix_raw = raw.loc[time_col <= prefix_cut]
                prefix, _ = engine.share_daily(prefix_raw, prefix_calendar, cfg["max_stale_calendar_days"])
            else:
                prefix_raw = raw.loc[time_col <= prefix_cut]
                prefix_prices = prices.loc[pd.to_datetime(prices.trade_date) <= prefix_cut]
                prefix, _ = engine.nav_daily(prefix_raw, prefix_prices, prefix_calendar,
                                             cfg["max_stale_calendar_days"])
            if profile == "minute":
                pd.testing.assert_frame_equal(full.loc[:prefix_cut], prefix,
                                              check_exact=False, rtol=1e-9, atol=1e-12)
            else:
                pd.testing.assert_series_equal(full.loc[:prefix_cut], prefix,
                                               check_exact=False, rtol=1e-9, atol=1e-12)
            symbol_audit["prefix_reconstruction"][str(prefix_cut.date())] = True
        outputs[symbol] = full
        diagnostics[symbol] = symbol_audit

    if profile == "minute":
        result = {name: pd.DataFrame({symbol: outputs[symbol][name] for symbol in symbols}, index=calendar)
                  for name in engine.MINUTE_NAMES}
    elif profile == "share":
        result = {"shares": pd.DataFrame(outputs, index=calendar)}
    else:
        result = {"premium": pd.DataFrame(outputs, index=calendar)}
    return result, raw_hashes, {"by_symbol": diagnostics,
                                "loader_sha256": _sha(Path(engine.__file__))}


def _source_spec(profile: str, cfg: dict, root: Path):
    """Return loader, aligner, source definitions, shock key and source paths."""
    core = "etf_strategy.core."
    if profile == "us_sector":
        engine = importlib.import_module(core + "etf_group_us_sector")
        return (engine, "us_sector_shock", [
            ("sox_file", "sox_sha256", "NASDAQSOX", "read_fred"),
            ("ndx_file", "ndx_sha256", "NASDAQ100", "read_fred")], "align_specific_shock")
    specs = {
        "us_vix": ("etf_group_us_vix", "us_vix_shock", [("vix_file", "vix_sha256", None, "read_vix")], "align_vix_shock"),
        "us_style": ("etf_group_us_style", "us_style_shock", [("value_file", "value_sha256", "NASDAQNQUSLV", "read_style"), ("growth_file", "growth_sha256", "NASDAQNQUSLG", "read_style")], "align_style_shock"),
        "ext_gold": ("etf_group_ext_gold", "ext_gold_shock", [("gold_file", "gold_sha256", None, "read_gold")], "align_gold_shock"),
        "ext_copper": ("etf_group_ext_copper", "ext_copper_shock", [("copper_file", "copper_sha256", None, "read_copper")], "align_copper_shock"),
        "ext_crude": ("etf_group_ext_crude", "ext_crude_shock", [("crude_file", "crude_sha256", None, "read_crude")], "align_crude_shock"),
        "ext_cnh": ("etf_group_ext_cnh", "ext_cnh_shock", [("cnh_file", "cnh_sha256", None, "read_cnh")], "align_cnh_shock"),
        "ext_hktech": ("etf_group_ext_hktech", "ext_hktech_shock", [("hktech_file", "hktech_sha256", None, "read_hktech")], "align_hktech_shock"),
        "ext_realrate": ("etf_group_ext_realrate", "ext_realrate_shock", [("realrate_file", "realrate_sha256", None, "read_realrate")], "align_realrate_shock"),
        "ext_coal": ("etf_group_ext_coal", "ext_coal_shock", [("coal_file", "coal_sha256", None, "read_coal")], "align_coal_shock"),
    }
    module, shock_name, source_defs, align_name = specs[profile]
    engine = importlib.import_module(core + module)
    return engine, shock_name, source_defs, align_name


def _approval_evidence(profile: str, cfg: dict, config_path: Path, root: Path) -> bool:
    """Verify the source was approved and formally run under this exact config."""
    run_id = config_path.stem
    approval = root / "runtime_outputs/etf_rotation_research/approvals" / f"{run_id}.json"
    plan_path = root / "runtime_outputs/etf_rotation_research/runs" / run_id / "PLAN.json"
    if any(not path.is_file() or path.is_symlink() for path in (approval, plan_path)):
        return False
    try:
        approval_data = json.loads(approval.read_text())
        plan = json.loads(plan_path.read_text())
        config_hash = _sha(config_path)
        config_key = str(config_path.resolve())
        if (approval_data.get("config_sha256") != config_hash
                or plan.get("source_type") != profile
                or local_path(plan.get("batch_approval", ""), root) != approval.resolve()
                or {str(local_path(key, root)): value for key, value in plan.get("source_hashes", {}).items()}.get(config_key) != config_hash):
            return False
        input_hashes = {str(local_path(key, root)): value for key, value in plan.get("input_hashes", {}).items()}
        for file_key, digest_key, _, _ in _source_spec(profile, cfg, root)[2]:
            source = (root / cfg[file_key]).resolve()
            if input_hashes.get(str(source)) != cfg[digest_key]:
                return False
        return True
    except (OSError, ValueError, TypeError, KeyError):
        return False


def describe_profiles(root: Path = ROOT) -> dict:
    """Describe available profile pins without opening any market data."""
    root = Path(root)
    result = {"daily": {"available": True, "approved": True,
                         "status": "APPROVED_BASE_PROFILE", "config": None,
                         "source_types": [], "panel_names": _panel_names("daily"),
                         "availability_convention": _availability_convention("daily"),
                         "review_contract": _review_contract("daily", root)}}
    for profile, name in _CONFIGS.items():
        config = root / "frameworks/etf_rotation/configs" / name
        available = config.is_file() and not config.is_symlink()
        source_files = []
        if available:
            cfg, config_path = _profile_config(profile, root)
            if profile in _DATA_FOLDER:
                symbols = _candidate_symbols(root)
                source_paths = _source_file_paths(profile, cfg, root, symbols)
            else:
                source_paths = [(root / cfg[k]) for k, _, _, _ in _source_spec(profile, cfg, root)[2]]
            source_files = [str(path.resolve()) for path in source_paths]
            available = all(path.is_file() and not path.is_symlink() for path in source_paths)
        else:
            cfg = {}
            config_path = config
        approved = bool(available and (profile in _DATA_FOLDER or
                                       _approval_evidence(profile, cfg, config_path, root)))
        result[profile] = {
            "available": available,
            "approved": approved,
            "status": ("APPROVED_EXISTING_CANONICAL_SOURCE_SCOPE" if profile in _DATA_FOLDER and approved
                       else cfg.get("status") if available else "PINNED_CONFIG_OR_SOURCE_MISSING"),
            "approval_evidence": ("existing fixed ETF source scope and present raw files" if profile in _DATA_FOLDER and approved
                                  else "matching formal PLAN and approval artifact" if approved
                                  else "no matching formal PLAN and approval artifact"),
            "config": str(config),
            "source_files": source_files,
            "panel_names": _panel_names(profile),
            "availability_convention": _availability_convention(profile),
            "review_contract": _review_contract(profile, root),
        }
    return result


def load_inputs(profile: str, panels: dict, cutoff: pd.Timestamp,
                root: Path = ROOT) -> tuple[dict[str, pd.DataFrame], dict]:
    """Return the six base panels, selected profile panels, and provenance manifest.

    ``cutoff`` must equal the reviewed 2026-03-24 cutoff. External market
    panels use the existing strict-prior aligners; minute, share, and NAV
    panels use the existing canonical transformations with raw-date filters.
    Candidate code cannot read raw files through this API.
    """
    if profile != "daily" and profile not in _CONFIGS:
        raise ValueError(f"unsupported input profile: {profile}")
    cutoff = pd.Timestamp(cutoff)
    if cutoff.tzinfo is not None or cutoff != PINNED_CUTOFF:
        raise ValueError("input profile cutoff must be the pinned 2026-03-24 date")
    missing = set(BASE_FIELDS) - set(panels)
    if missing:
        raise ValueError(f"missing base daily panels: {sorted(missing)}")
    base = {name: panels[name].copy() for name in BASE_FIELDS}
    close = base["close"]
    if not isinstance(close, pd.DataFrame) or close.columns.has_duplicates or close.index.has_duplicates:
        raise ValueError("close panel must have unique dates and columns")
    if close.index.tz is not None or (len(close.index) and close.index.max() > cutoff):
        raise ValueError("base close panel exceeds the pinned cold cutoff")
    for field, panel in base.items():
        if (not isinstance(panel, pd.DataFrame) or panel.index.has_duplicates or
                panel.columns.has_duplicates or not panel.index.equals(close.index) or
                not panel.columns.equals(close.columns)):
            raise ValueError(f"base {field} panel does not match close dates and columns")
    manifest = {
        "profile": profile,
        "cutoff": cutoff.date().isoformat(),
        "availability_convention": _availability_convention(profile),
        "adapter_sha256": _sha(Path(__file__)),
        "source_sha256": {},
        "loader_sha256": {},
    }
    if profile == "daily":
        manifest["config_sha256"] = None
        manifest["prepared_panel_sha256"] = {name: _frame_sha(frame) for name, frame in base.items()}
        return base, manifest

    root = Path(root).resolve()
    cfg, config_path = _profile_config(profile, root)
    manifest["config_sha256"] = _sha(config_path)
    if profile in _DATA_FOLDER:
        feature_panels, hashes, provenance = _load_source_profile(profile, base, cfg, root)
        base.update(feature_panels)
        manifest["source_sha256"] = hashes
        manifest["loader_sha256"]["etf_group_sources"] = provenance.pop("loader_sha256")
        manifest["loader_diagnostics"] = provenance
        manifest["prepared_panel_sha256"] = {name: _frame_sha(frame) for name, frame in base.items()}
        return base, manifest
    engine, shock_name, source_defs, align_name = _source_spec(profile, cfg, root)
    sources = []
    source_paths = []
    for file_key, digest_key, series_name, reader_name in source_defs:
        rel = cfg[file_key]
        if rel != _EXPECTED_FILES[file_key]:
            raise ValueError(f"source path differs from reviewed pin: {file_key}")
        untrusted_path = root / rel
        expected_path = untrusted_path.resolve()
        if (untrusted_path.is_symlink() or not expected_path.is_relative_to(root)
                or not expected_path.is_file()):
            raise FileNotFoundError(f"pinned source is missing, symlinked, or outside root: {expected_path}")
        digest = cfg[digest_key]
        if _sha(expected_path) != digest:
            raise ValueError(f"pinned source hash mismatch: {expected_path}")
        reader = getattr(engine, reader_name)
        if reader_name == "read_fred":
            source = reader(expected_path, series_name, digest, cutoff)
        elif reader_name == "read_style":
            source = reader(expected_path, series_name, digest, cutoff)
        else:
            source = reader(expected_path, digest, cutoff)
        sources.append(source)
        source_paths.append(expected_path)
        manifest["source_sha256"][str(expected_path)] = digest
        manifest["loader_sha256"][reader_name] = _sha(Path(engine.__file__))
    aligner = getattr(engine, align_name)
    shock = aligner(*sources, close.index) if len(sources) == 2 else aligner(sources[0], close.index)
    manifest["loader_sha256"][align_name] = _sha(Path(engine.__file__))
    if isinstance(shock, pd.Series):
        shock = pd.DataFrame({column: shock.reindex(close.index) for column in close.columns}, index=close.index)
    elif isinstance(shock, pd.DataFrame):
        shock = shock.reindex(index=close.index)
        if shock.shape[1] == 1:
            shock = pd.DataFrame({column: shock.iloc[:, 0] for column in close.columns}, index=close.index)
        elif set(shock.columns) != set(close.columns):
            raise ValueError("aligned shock columns do not match fixed close population")
        else:
            shock = shock.reindex(columns=close.columns)
    else:
        raise TypeError("core aligner must return a Series or DataFrame")
    base[shock_name] = shock
    manifest["prepared_panel_sha256"] = {name: _frame_sha(frame) for name, frame in base.items()}
    return base, manifest


def summarize_feature_panels(panels: dict, cutoff=PINNED_CUTOFF) -> dict:
    """Feature-only availability diagnostics, never forward returns or IC."""
    import numpy as np
    if pd.Timestamp(cutoff) != PINNED_CUTOFF:
        raise ValueError('diagnostic cutoff must equal frozen cold cutoff')
    result = {}
    for name, frame in panels.items():
        if len(frame.index) and frame.index.max() > cutoff:
            raise ValueError('diagnostic feature panel exceeds cold cutoff')
        observed = frame.loc[frame.index >= pd.Timestamp('2025-01-01')]
        valid = np.isfinite(observed)
        clean = observed.where(valid)
        paired = valid & valid.shift(1, fill_value=False)
        changed = clean.ne(clean.shift(1)) & paired
        dates = observed.index[valid.any(axis=1)]
        result[name] = {
            'rows': len(observed), 'columns': len(observed.columns),
            'finite_cells': int(valid.sum().sum()), 'total_cells': int(observed.size),
            'complete_population_days': int(valid.all(axis=1).sum()),
            'nonconstant_cross_section_days': int((clean.nunique(axis=1) > 1).sum()),
            'consecutive_valid_pairs': int(paired.sum().sum()),
            'changed_pairs': int(changed.sum().sum()),
            'first_valid_date': str(dates.min().date()) if len(dates) else None,
            'last_valid_date': str(dates.max().date()) if len(dates) else None,
            'valid_days_by_etf': {str(k): int(v) for k, v in valid.sum().items()},
        }
    return {'window_start': '2025-01-01', 'cold_cutoff': str(PINNED_CUTOFF.date()),
            'label_accessed': False, 'panels': result,
            'interpretation': 'Feature availability only, not IC sample counts or a screening threshold. '
                              'Broadcast shocks may have no cross-sectional variation until combined with ETF exposures.'}


def describe_feature_diagnostics(profile: str, root: Path = ROOT) -> dict:
    """Load approved cold feature surfaces only; no evaluator/labels imported."""
    from etf_strategy.canonical_data import load_canonical_daily
    base = load_canonical_daily(CANONICAL_DATA_ROOT, Path(root) / 'config/etf_rotation_universe_v1.json',
                                as_of=str(PINNED_CUTOFF.date()), roles=('candidate',))
    prepared, manifest = load_inputs(profile, base, PINNED_CUTOFF, root)
    result = summarize_feature_panels(prepared)
    result['input_profile'] = profile
    result['input_manifest'] = manifest
    return result
