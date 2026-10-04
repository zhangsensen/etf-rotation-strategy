"""ETF data integration boundaries; synthetic local inputs only."""
import subprocess
import pytest
from scripts.update_etf_rotation import run_one

def test_timeout_preserves_old_data_and_next_symbol_runs(tmp_path):
    old = tmp_path / "1d" / "513120.SH.parquet"
    old.parent.mkdir()
    old.write_bytes(b"old data")
    calls = []

    def timeout(cmd, **kwargs):
        calls.append(cmd)
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    for symbol in ["513120.SH", "159995.SZ"]:
        result = run_one(symbol, "2026-09-17", tmp_path, timeout=1, runner=timeout)
        assert not result["ok"]
    assert len(calls) == 2
    assert old.read_bytes() == b"old data"

def test_bad_etf_universe_rejected_before_vendor_access(tmp_path, monkeypatch):
    import json
    from data.downloaders import etf_rotation_backfill as module

    config = tmp_path / "pool.json"
    config.write_text(json.dumps({"etfs": [{"ts_code": "000001.SZ"}]}))
    monkeypatch.setattr(
        "sys.argv",
        [
            "backfill",
            "--config",
            str(config),
            "--output",
            str(tmp_path / "funds"),
            "--as-of",
            "2026-09-17",
        ],
    )
    with pytest.raises(ValueError, match="non-fund"):
        module.main()
    assert not (tmp_path / "funds").exists()

def test_full_update_replaces_retired_universe_and_stale_statistics(tmp_path, monkeypatch):
    import json
    import pandas as pd
    from scripts import update_etf_rotation as module

    (tmp_path / "config").mkdir()
    config = {"etfs": [{"ts_code": "513100.SH"}], "classification_revision": "new"}
    (tmp_path / "config/etf_rotation_universe_v1.json").write_text(json.dumps(config))
    output = tmp_path / "etf_rotation_v1"
    output.mkdir()
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "config": {"etfs": [{"ts_code": "513310.SH"}]},
                "rows_by_period": {"1d": 999},
                "cross_source_issue_count": 999,
            }
        )
    )
    for period in module.PERIODS:
        (output / period).mkdir()
        pd.DataFrame({"value": [1, 2]}).to_parquet(output / period / "513100.SH.parquet")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(
        module,
        "run_one",
        lambda *args: {
            "ok": True,
            "audit": {
                "minute_missing_daily_dates": [],
                "minute_days_not_240": 0,
            },
        },
    )
    monkeypatch.setattr("sys.argv", ["update", "--as-of", "2026-09-17", "--output", str(output)])
    assert module.main() == 0
    result = json.loads((output / "manifest.json").read_text())
    assert result["config"] == config
    assert set(result["symbols"]) == {"513100.SH"}
    assert result["rows_by_period"] == {p: 2 for p in module.PERIODS}
    assert "cross_source_issue_count" not in result
