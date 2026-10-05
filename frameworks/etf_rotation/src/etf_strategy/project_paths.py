"""Resolve historical local paths without changing sealed configuration bytes."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
LEGACY_ROOTS = (
    Path("/home/sensen/dev/projects/-0927"),
    Path("/home/sensen/dev/projects/gpu_ml-coral"),
    Path("/home/sensen/dev/projects/gpu_ml-coral-autoresearch"),
    Path("/home/sensen/dev/projects/gpu_ml"),
)


def local_path(value: str | Path, root: Path = PROJECT_ROOT) -> Path:
    path = Path(value)
    for old in LEGACY_ROOTS:
        if path.is_relative_to(old):
            return (root / path.relative_to(old)).resolve()
    return (path if path.is_absolute() else root / path).resolve()
