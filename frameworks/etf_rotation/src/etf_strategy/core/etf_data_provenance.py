"""Content hashes for the local ETF market-data files consumed by a run."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

import yaml


def hash_config_dependencies(project_root: Path, config_paths: Iterable[Path]) -> dict[str, str]:
    """Hash secondary config files referenced by family configs."""
    root = project_root.resolve()
    dependencies: set[Path] = set()

    def visit(value: object, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                visit(child_value, str(child_key))
        elif isinstance(value, list):
            for child in value:
                visit(child, key)
        elif key.endswith("_config") and isinstance(value, str):
            path = Path(value)
            path = path if path.is_absolute() else (root / path).resolve()
            if not path.is_file():
                raise FileNotFoundError(f"referenced config missing: {path}")
            dependencies.add(path)

    for config_path in config_paths:
        visit(yaml.safe_load(config_path.read_text()))
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(dependencies)
    }


def hash_research_inputs(
    data_root: Path,
    symbols: Iterable[str],
    intraday_frequencies: Iterable[str],
) -> dict[str, object]:
    root = data_root.resolve()
    paths: list[Path] = []
    for symbol in sorted(set(symbols)):
        paths.extend((root / "1d" / f"{symbol}.parquet", root / "adj_factor" / f"{symbol}.parquet"))
        for frequency in sorted(set(intraday_frequencies)):
            paths.append(root / frequency / f"{symbol}.parquet")
    aggregate = hashlib.sha256()
    for path in sorted(paths):
        if not path.is_file():
            raise FileNotFoundError(f"research input missing: {path}")
        relative = str(path.relative_to(root))
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        aggregate.update(relative.encode())
        aggregate.update(b"\0")
        aggregate.update(digest.digest())
    return {
        "root": str(root),
        "file_count": len(paths),
        "intraday_frequencies": sorted(set(intraday_frequencies)),
        "sha256": aggregate.hexdigest(),
    }
