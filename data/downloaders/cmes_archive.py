"""ETF-local CMES archive transport; no stock mining imports."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
from io import BytesIO
import json
import os
from pathlib import Path
import signal
import sys
import time
import types
from typing import Any
import zipfile
class CmesQuarantineError(RuntimeError):
    pass

def _load_cmes_stock_modules() -> tuple[Any, Any]:
    package_spec = importlib.util.find_spec("cmesdata")
    if package_spec is None or package_spec.origin is None:
        raise CmesQuarantineError(
            "cmesdata is unavailable; run with `uv run --with cmesdata==1.2.30`"
        )
    package = types.ModuleType("cmesdata")
    package.__path__ = [str(Path(package_spec.origin).parent)]
    package.__package__ = "cmesdata"
    package.__spec__ = package_spec
    sys.modules["cmesdata"] = package
    return (
        importlib.import_module("cmesdata.stock"),
        importlib.import_module("cmesdata.historydata"),
    )

def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()

def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_bytes(payload)
    os.replace(temporary, path)

def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)

def _validate_zip(payload: bytes) -> tuple[int, int]:
    if len(payload) < 22:
        raise RuntimeError(f"short ZIP response: {len(payload)} bytes")
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"corrupt ZIP member: {bad}")
        members = [item for item in archive.infolist() if not item.is_dir()]
        if not members:
            raise RuntimeError("empty ZIP response")
        return len(members), sum(item.file_size for item in members)

def _download(
    historydata: Any,
    task: dict[str, str],
    destination: Path,
    token: str,
    attempts: int,
    retry_delay: float,
    download_timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    _, data_menu, _ = historydata._menu_info(task["symbol"])
    filename = task["name"] if task["name"].lower().endswith(".zip") else task["name"] + ".zip"
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            previous_handler = signal.getsignal(signal.SIGALRM)

            def _deadline_exceeded(_signum: int, _frame: Any) -> None:
                raise TimeoutError(
                    f"CMES download exceeded {download_timeout_seconds:g}s"
                )

            signal.signal(signal.SIGALRM, _deadline_exceeded)
            signal.setitimer(signal.ITIMER_REAL, download_timeout_seconds)
            try:
                payload = historydata._download_file(
                    data_menu,
                    filename,
                    token,
                    folder=task["folder"],
                )
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous_handler)
            members, uncompressed_bytes = _validate_zip(payload)
            _atomic_bytes(destination, payload)
            receipt = {
                "schema_version": "1.0.0",
                "source_symbol": task["symbol"],
                "source_name": task["name"],
                "source_folder": task["folder"],
                "data_menu": data_menu,
                "zip_sha256": _sha256_bytes(payload),
                "compressed_bytes": len(payload),
                "uncompressed_bytes": uncompressed_bytes,
                "member_count": members,
                "raw_vendor_payload": True,
                "target_or_outcome_read": False,
                "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            _atomic_json(destination.with_suffix(destination.suffix + ".receipt.json"), receipt)
            return {"completed": True, **receipt}
        except Exception as error:  # vendor/network boundary
            last_error = error
            if attempt < attempts:
                time.sleep(retry_delay * attempt)
    assert last_error is not None
    return {
        "completed": False,
        "source_symbol": task["symbol"],
        "source_name": task["name"],
        "source_folder": task["folder"],
        "error": str(last_error).replace(token, "[REDACTED]")[:500],
    }
