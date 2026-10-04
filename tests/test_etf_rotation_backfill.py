import pandas as pd
import pytest

from data.downloaders.etf_rotation_backfill import resample, validate


def minutes():
    t = pd.date_range("2026-09-17 09:31", periods=120, freq="min").append(
        pd.date_range("2026-09-17 13:01", periods=120, freq="min")
    )
    return pd.DataFrame(
        {
            "datetime": t,
            "ts_code": "159995.SZ",
            "open": 1.0,
            "high": 2.0,
            "low": 0.5,
            "close": 1.5,
            "volume": 100.0,
            "turnover": 150.0,
        }
    )


def test_lunch_anchoring_and_activity_conservation():
    x = minutes()
    y = resample(x, 60)
    assert y.datetime.dt.strftime("%H:%M").tolist() == ["10:30", "11:30", "14:00", "15:00"]
    assert y.volume.sum() == x.volume.sum()
    assert y.turnover.sum() == x.turnover.sum()
    assert len(resample(x, 5)) == 48
    assert len(resample(x, 15)) == 16
    assert len(resample(x, 30)) == 8


def test_missing_minute_never_becomes_complete_bar():
    x = minutes().drop(index=0)
    y = resample(x, 5)
    assert len(y) == 47
    assert pd.Timestamp("2026-09-17 09:35") not in set(y.datetime)


def test_duplicate_timestamp_is_rejected():
    x = minutes()
    with pytest.raises(ValueError, match="duplicated"):
        validate(pd.concat([x, x.iloc[:1]]), "datetime")


def test_current_year_archive_refreshes_for_new_completed_session(tmp_path):
    import json
    from data.downloaders.etf_rotation_backfill import archive_is_current

    p = tmp_path / "sample.zip"
    p.write_bytes(b"raw")
    receipt = p.with_suffix(".zip.receipt.json")
    receipt.write_text(json.dumps({"downloaded_at_utc": "2026-09-18T05:00:00+00:00"}))
    assert archive_is_current(p, 2026, "2026-09-17")
    assert not archive_is_current(p, 2026, "2026-09-18")


def test_only_zero_volume_sub_yuan_roundoff_is_corrected():
    from data.downloaders.etf_rotation_backfill import clean_activity_roundoff

    x = minutes().iloc[:3].copy()
    x["volume"] = [0.0, 100.0, 0.0]
    x["turnover"] = [-0.196, -0.196, -2.0]
    out, record = clean_activity_roundoff(x)
    assert out.turnover.tolist() == [0.0, -0.196, -2.0]
    assert len(record) == 1
    assert record.turnover.iloc[0] == -0.196
