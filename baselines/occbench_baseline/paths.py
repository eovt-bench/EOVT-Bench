from __future__ import annotations

from pathlib import Path


BASELINE_ROOT = Path(__file__).resolve().parents[1]
OCCBENCH_ROOT = BASELINE_ROOT.parent
EVT_ROOT = OCCBENCH_ROOT


def resolve_readonly(path: str | Path, *, base: Path = BASELINE_ROOT) -> Path:
    value = Path(path).expanduser()
    return (value if value.is_absolute() else base / value).resolve()


def writable_path(path: str | Path) -> Path:
    """Resolve a path and reject every write outside the baseline directory."""
    resolved = resolve_readonly(path)
    try:
        resolved.relative_to(BASELINE_ROOT)
    except ValueError as exc:
        raise ValueError(f"refusing to write outside {BASELINE_ROOT}: {resolved}") from exc
    return resolved


def ensure_runtime_dirs() -> None:
    for name in ("cache", "outputs", "tmp"):
        writable_path(name).mkdir(parents=True, exist_ok=True)

