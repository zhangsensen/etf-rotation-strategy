"""Load and validate the ETF-local information-family catalog."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

import yaml

from .etf_factor_grammar import parse_atoms
from .family_registry import resolve_family


def load_family_catalog(catalog_path: Path, project_root: Path) -> list[Path]:
    """Return configured family files after enforcing one source per family."""
    raw = yaml.safe_load(catalog_path.read_text())
    rows = raw.get("available_families", [])
    if not rows:
        raise ValueError("ETF family catalog has no available_families")
    sources = [str(row["source"]) for row in rows]
    if len(sources) != len(set(sources)):
        raise ValueError("ETF family catalog sources must be unique")
    retired = {str(source) for source in raw.get("retired_sources", [])}
    retired |= {
        str(row["family"])
        for row in raw.get("closed_redundant_families", [])
    }
    overlap = sorted(set(sources) & retired)
    if overlap:
        raise ValueError(f"retired ETF sources cannot be available: {overlap}")

    paths: list[Path] = []
    information_families: list[str] = []
    for row in rows:
        path = Path(str(row["config"]))
        path = path if path.is_absolute() else (project_root / path).resolve()
        config = yaml.safe_load(path.read_text())
        source = str(config["factor_source"])
        if source != str(row["source"]):
            raise ValueError(f"catalog/config source mismatch: {row['source']} != {source}")
        provider = resolve_family(source)
        information_families.append(provider.information_family)
        atoms = parse_atoms(config["atoms"])
        wrong = sorted({atom.family for atom in atoms} - {provider.information_family})
        if wrong:
            raise ValueError(f"{source} atoms cross information-family boundary: {wrong}")
        operators = list(config["grammar"]["operators"])
        if operators != ["atomic"]:
            raise ValueError(f"breadth catalog must start atomic-only: {source}")
        paths.append(path)
    if len(information_families) != len(set(information_families)):
        raise ValueError("ETF catalog providers must map one-to-one to information families")
    return paths


def blocked_family_reasons(catalog_path: Path) -> Mapping[str, str]:
    raw = yaml.safe_load(catalog_path.read_text())
    return {
        str(row["family"]): str(row["missing_data"])
        for row in raw.get("blocked_families", [])
    }
