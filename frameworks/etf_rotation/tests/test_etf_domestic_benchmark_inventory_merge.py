"""Synthetic preservation and semantic-ID checks for a two-row local merge."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest
import yaml

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts/research/merge_domestic_benchmark_inventory_20260925.py"
spec = importlib.util.spec_from_file_location("merge_domestic_benchmark_inventory_20260925", SCRIPT)
merge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge)


def test_two_frozen_rows_append_without_modifying_prior_semantics():
    cfg = yaml.safe_load((BASE / "configs/group_ic_cn_benchmark_aux_20260925.yaml").read_text())
    names = merge.rules.candidate_ids(cfg)
    old = pd.DataFrame([{"definition_id": "old", "candidate": "prior",
                         "full_ic_mean": .12, "historical_metrics_pass": True}])
    current = pd.DataFrame([{"candidate": name, "n": 287, "ic_mean": -.02,
                             "ic_hac_t": -.5, "ic_block_t": -.4, "ic_blocks": 57,
                             "ic_p_normal_one_sided": .7, "min_leave_group_ic": -.03,
                             "historical_2026_min_leave_group_ic": -.1,
                             "historical_ic_supported": False,
                             "historical_2026_metrics_pass": False,
                             "factor_evidence_supported": False,
                             "ic_budget_supported": False} for name in names])
    annual = pd.DataFrame([{"candidate": name, "year": year, "n": 236 if year == 2025 else 44,
                            "ic_mean": -.03, "ic_hac_t": -.6, "ic_block_t": -.4,
                            "ic_blocks": 47 if year == 2025 else 8,
                            "ic_p_normal_one_sided": .8}
                           for name in names for year in (2025, 2026)])
    result = merge.append_rows(old, current, annual, cfg, Path("run"))
    assert len(result) == 3
    assert result.iloc[0].to_dict() == old.iloc[0].to_dict()
    assert result.definition_id.is_unique
    assert set(result.candidate.tail(2)) == set(names)
    assert result.full_ic_mean.tail(2).eq(-.02).all()
    with pytest.raises(ValueError, match="already in prior"):
        merge.append_rows(result, current, annual, cfg, Path("run"))
