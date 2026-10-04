"""Historical config paths resolve locally without the former GPU project."""
from pathlib import Path
import sys

import yaml

from etf_strategy.project_paths import LEGACY_ROOTS, local_path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/research"))
import etf_autoresearch_inputs as inputs


def test_historical_paths_resolve_without_old_directories(tmp_path):
    for old in LEGACY_ROOTS:
        for relative in ("data/etf_rotation_v1", "runtime_outputs/etf_rotation_research/PLAN.json",
                         "frameworks/etf_rotation/configs/frozen.yaml"):
            assert local_path(old / relative, tmp_path) == tmp_path / relative
    external = Path("/home/sensen/data_vendor/cmes")
    assert local_path(external, tmp_path) == external


def test_frozen_input_profile_is_portable_and_keeps_original_bytes(tmp_path, monkeypatch):
    profile = "minute"
    config = tmp_path / "frameworks/etf_rotation/configs" / inputs._CONFIGS[profile]
    config.parent.mkdir(parents=True)
    config.write_text(yaml.safe_dump({
        "source_type": profile, "as_of": "2026-03-24",
        "data_root": "/home/sensen/dev/projects/gpu_ml/data/etf_rotation_v1",
    }))
    original = config.read_bytes()
    monkeypatch.setattr(inputs, "CANONICAL_DATA_ROOT", tmp_path / "data/etf_rotation_v1")
    payload, path = inputs._profile_config(profile, tmp_path)
    assert path == config
    assert payload["data_root"] == "/home/sensen/dev/projects/gpu_ml/data/etf_rotation_v1"
    assert config.read_bytes() == original
