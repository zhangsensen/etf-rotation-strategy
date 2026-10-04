"""Historical read boundary for the saved-lead value audit."""
import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/research/audit_saved_etf_ic_history.py"
spec = importlib.util.spec_from_file_location("audit_saved_etf_ic_history", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_cold_cutoff_rejects_any_later_date_before_loading_inputs(tmp_path):
    with pytest.raises(ValueError, match="cold cutoff"):
        audit.run("2026-03-25", tmp_path / "later")
    assert not (tmp_path / "later").exists()
