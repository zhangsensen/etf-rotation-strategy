#!/usr/bin/env python3
"""Profile causal daily factor atoms on the broad point-in-time ETF population."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd
import yaml

ETF_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ETF_ROOT / "src"))

from etf_strategy.core.etf_all_daily_data import (  # noqa: E402
    hash_all_etf_cache_contract,
    load_all_etf_daily,
)
from etf_strategy.core.etf_all_daily_discovery import (  # noqa: E402
    AllEtfDiscoverySettings,
    executable_forward_return,
    profile_all_etf_signal,
)
from etf_strategy.core.etf_factor_grammar import cross_sectional_rank  # noqa: E402
from etf_strategy.core.family_registry import load_builtin_families, resolve_family  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _settings(config: dict[str, Any]) -> AllEtfDiscoverySettings:
    execution = config["execution"]
    surfaces = config["surfaces"]
    gates = config["discovery_gates"]
    return AllEtfDiscoverySettings(
        entry_lag=int(execution["entry_lag_sessions"]),
        horizon=int(execution["horizon"]),
        min_names=int(gates["min_names"]),
        direction_start=str(surfaces["direction_start"]),
        direction_end=str(surfaces["direction_end"]),
        discovery_start=str(surfaces["discovery_start"]),
        discovery_end=str(surfaces["discovery_end"]),
        validation_start=str(surfaces["validation_start"]),
        validation_end=str(surfaces["validation_end"]),
        min_direction_days=int(gates["min_direction_days"]),
        min_discovery_days=int(gates["min_discovery_days"]),
        min_validation_days=int(gates["min_validation_days"]),
        min_abs_controlled_ic=float(gates["min_abs_controlled_ic"]),
        min_discovery_hac_t=float(gates["min_discovery_hac_t"]),
        min_validation_hac_t=float(gates["min_validation_hac_t"]),
    )


def _catalog(config: dict[str, Any]) -> dict[str, Path]:
    value = Path(str(config["family_catalog"]))
    path = value if value.is_absolute() else (ETF_ROOT / value).resolve()
    rows = yaml.safe_load(path.read_text())["available_families"]
    return {
        str(row["source"]): (
            Path(str(row["config"]))
            if Path(str(row["config"])).is_absolute()
            else (ETF_ROOT / str(row["config"])).resolve()
        )
        for row in rows
    }


def _ranked_source(
    source: str,
    source_path: Path,
    *,
    panels: dict[str, pd.DataFrame],
    eligibility: pd.DataFrame,
    data_root: Path,
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    source_config = yaml.safe_load(source_path.read_text())
    if str(source_config["factor_source"]) != source:
        raise ValueError(f"catalog/config source mismatch: {source}")
    frequency = str(source_config.get("frequency", ""))
    if frequency not in ("", "1d", "adj_factor"):
        raise ValueError(f"all-ETF daily discovery rejects non-daily source {source}: {frequency}")
    space = resolve_family(source).builder(panels, eligibility, data_root, source_config)
    ranked: dict[str, pd.DataFrame] = {}
    families: dict[str, str] = {}
    for atom in source_config["atoms"]:
        name, family = str(atom["name"]), str(atom["family"])
        if name not in space:
            raise ValueError(f"{source} did not materialize {name}")
        ranked[name] = cross_sectional_rank(
            space[name].reindex_like(eligibility), eligibility
        ).astype("float32")
        families[name] = family
    return ranked, families


def discover(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"output must be new and empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text())
    catalog_value = Path(str(config["family_catalog"]))
    catalog_path = (
        catalog_value if catalog_value.is_absolute() else (ETF_ROOT / catalog_value).resolve()
    )
    settings = _settings(config)
    settings.validate()
    data = config["data"]
    population = config["population"]
    data_root = Path(str(data["cache_root"])).resolve()
    context = load_all_etf_daily(
        data_root,
        start=str(data["start"]),
        as_of=str(data["as_of"]),
        min_history_sessions=int(population["min_history_sessions"]),
        liquidity_window=int(population["liquidity_window"]),
        min_median_amount_thousand=float(population["min_median_amount_thousand"]),
    )
    forward = executable_forward_return(
        context.panels["open"],
        entry_lag=settings.entry_lag,
        horizon=settings.horizon,
    )
    load_builtin_families()
    catalog = _catalog(config)
    sources = [str(value) for value in config["sources"]]
    if len(sources) != len(set(sources)):
        raise ValueError("source list contains duplicates")
    missing_sources = set(sources) - set(catalog)
    if missing_sources:
        raise ValueError(f"catalog is missing sources: {sorted(missing_sources)}")

    control_specs = [(str(row["source"]), str(row["atom"])) for row in config["controls"]]
    controls: dict[str, pd.DataFrame] = {}
    source_cache: dict[str, tuple[dict[str, pd.DataFrame], dict[str, str]]] = {}
    for source, atom in control_specs:
        if source not in source_cache:
            source_cache[source] = _ranked_source(
                source,
                catalog[source],
                panels=context.panels,
                eligibility=context.eligibility,
                data_root=data_root,
            )
        ranked, _ = source_cache[source]
        if atom not in ranked:
            raise ValueError(f"control atom missing: {source}:{atom}")
        controls[atom] = ranked[atom]

    rows: list[dict[str, object]] = []
    config_hashes: dict[str, str] = {}
    control_names = set(controls)
    for source_index, source in enumerate(sources, start=1):
        print(f"[profile] source={source} {source_index}/{len(sources)}", flush=True)
        ranked, families = source_cache.pop(source, (None, None))
        if ranked is None or families is None:
            ranked, families = _ranked_source(
                source,
                catalog[source],
                panels=context.panels,
                eligibility=context.eligibility,
                data_root=data_root,
            )
        config_hashes[str(catalog[source])] = _sha256(catalog[source])
        for name, signal in ranked.items():
            if name in control_names:
                continue
            profile = profile_all_etf_signal(
                signal,
                forward,
                context.eligibility,
                controls,
                name=name,
                settings=settings,
            )
            profile.update(
                {
                    "source": source,
                    "family": families[name],
                    "config": str(catalog[source]),
                }
            )
            rows.append(profile)
        pd.DataFrame(rows).to_csv(output / "atom_profiles.partial.csv", index=False)

    profiles = pd.DataFrame(rows).sort_values(
        ["stable_lead", "controlled_validation_hac_t", "controlled_discovery_hac_t"],
        ascending=[False, False, False],
    )
    profiles.to_csv(output / "atom_profiles.csv", index=False)
    (output / "atom_profiles.partial.csv").unlink(missing_ok=True)
    eligible_counts = context.eligibility.sum(axis=1)
    population_summary = {
        "identity_rows": int(len(context.population_table)),
        "symbol_columns": int(len(context.symbols)),
        "session_count": int(len(context.sessions)),
        "eligible_min": int(eligible_counts.min()),
        "eligible_median": float(eligible_counts.median()),
        "eligible_max": int(eligible_counts.max()),
        "eligible_at_direction_start": int(
            eligible_counts.loc[:pd.Timestamp(settings.direction_start)].iloc[-1]
        ),
        "eligible_at_validation_end": int(eligible_counts.loc[:pd.Timestamp(settings.validation_end)].iloc[-1]),
    }
    _write_json(output / "population_summary.json", population_summary)
    manifest = {
        "schema_version": "all_etf_daily_discovery_run_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": sys.argv,
        "config": str(config_path),
        "config_sha256": _sha256(config_path),
        "family_catalog": str(catalog_path),
        "family_catalog_sha256": _sha256(catalog_path),
        "entry_sha256": _sha256(Path(__file__).resolve()),
        "data_core_sha256": _sha256(
            ETF_ROOT / "src/etf_strategy/core/etf_all_daily_data.py"
        ),
        "discovery_core_sha256": _sha256(
            ETF_ROOT / "src/etf_strategy/core/etf_all_daily_discovery.py"
        ),
        "cache_contract": hash_all_etf_cache_contract(data_root),
        "source_config_hashes": config_hashes,
        "provider_code_hashes": {
            str(Path(str(inspect.getsourcefile(resolve_family(source).builder))).resolve()):
                _sha256(Path(str(inspect.getsourcefile(resolve_family(source).builder))).resolve())
            for source in sources
        },
        "population": population_summary,
        "atoms_profiled": int(len(profiles)),
        "stable_leads": int(profiles["stable_lead"].sum()),
        "label": "open(D+7)/open(D+2)-1",
        "outcomes_are_features": False,
        "forward_surface_downloaded": False,
    }
    _write_json(output / "run_manifest.json", manifest)
    print(
        f"All-ETF discovery complete: atoms={len(profiles)} "
        f"stable={int(profiles['stable_lead'].sum())} output={output}",
        flush=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    discover(parse_args())
