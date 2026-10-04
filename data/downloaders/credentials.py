"""Provider credentials from environment or an untracked project-local file."""
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def tushare_token() -> str:
    token = os.environ.get("TUSHARE_TOKEN", "").strip()
    if token:
        return token
    path = Path(os.environ.get("ETF_SECRETS_FILE", str(PROJECT_ROOT / ".env")))
    if path.is_file():
        for line in path.read_text().splitlines():
            if line.startswith("TUSHARE_TOKEN="):
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
                if token:
                    return token
    raise RuntimeError("Set TUSHARE_TOKEN or provide it in the local ETF secrets file")
