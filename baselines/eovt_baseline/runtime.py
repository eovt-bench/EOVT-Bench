from __future__ import annotations

import os
import sys
import builtins
from pathlib import Path
from typing import Any

from .paths import BASELINE_ROOT, EOVT_BENCH_ROOT, ensure_runtime_dirs, resolve_readonly


TASK_DIRS = {
    "stt": "STT",
    "or": "OR",
    "ic": "IC",
}


def configure_process_environment() -> None:
    ensure_runtime_dirs()
    # This must be set in-process as well: setting the environment variable
    # after interpreter startup alone does not stop imports from writing pyc.
    sys.dont_write_bytecode = True
    cache = BASELINE_ROOT / "cache"
    tmp = BASELINE_ROOT / "tmp"
    values = {
        "XDG_CACHE_HOME": cache,
        "HF_HOME": cache / "huggingface",
        "TRANSFORMERS_CACHE": cache / "huggingface" / "transformers",
        "TORCH_HOME": cache / "torch",
        "YOLO_CONFIG_DIR": cache / "ultralytics",
        "TMPDIR": tmp,
        "TEMP": tmp,
        "TMP": tmp,
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    for key, value in values.items():
        os.environ[key] = str(value)
        Path(value).mkdir(parents=True, exist_ok=True)


def install_driver_paths(driver_root: str | Path) -> Path:
    driver = resolve_readonly(driver_root)
    candidates = [driver, driver / "habitat-lab"]
    for path in reversed(candidates):
        if not path.exists():
            raise FileNotFoundError(f"required read-only driver path is missing: {path}")
        sys.path.insert(0, str(path))
    return driver


def install_readonly_humanoid_info_redirect(driver_root: str | Path) -> None:
    """Redirect the driver's one hard-coded relative metadata read.

    The upstream task calls ``open('humanoid_infos.json')``. EOVT-Bench scenes,
    however, require the process cwd to be EOVT-Bench so their relative asset
    manifests resolve. Redirect only that exact read without copying or
    modifying either external tree.
    """
    driver = resolve_readonly(driver_root)
    metadata = EOVT_BENCH_ROOT / "assets" / "humanoids" / "humanoid_infos.json"
    if not metadata.is_file():
        raise FileNotFoundError(f"humanoid metadata not found: {metadata}")
    original_open = builtins.open

    def redirected_open(file, *args, **kwargs):
        try:
            raw = os.fspath(file)
        except TypeError:
            raw = file
        if raw == "humanoid_infos.json":
            file = metadata
        return original_open(file, *args, **kwargs)

    builtins.open = redirected_open


def dataset_file(dataset_root: str | Path, task: str) -> Path:
    root = resolve_readonly(dataset_root)
    path = root / TASK_DIRS[task] / "val" / "val.json.gz"
    if not path.is_file():
        raise FileNotFoundError(f"dataset not found: {path}")
    return path


def scene_category(episode: Any) -> str:
    info = getattr(episode, "info", {}) or {}
    event = getattr(episode, "eovt_event", None) or (info.get("eovt_task", {}) if isinstance(info, dict) else {})
    category = event.get("scene_category") or info.get("scene_category")
    if category:
        return str(category).lower()
    episode_id = str(getattr(episode, "episode_id", "unknown"))
    tokens = {token.lower() for token in episode_id.split("_")}
    for candidate in ("road", "indoor", "industrial"):
        if candidate in tokens:
            return candidate
    return "unknown"


def layout_id(episode: Any) -> str | None:
    event = getattr(episode, "eovt_event", None)
    info = getattr(episode, "info", {}) or {}
    event = event or (info.get("eovt_task", {}) if isinstance(info, dict) else {})
    if event.get("layout_id"):
        return str(event["layout_id"])
    episode_id = str(getattr(episode, "episode_id", ""))
    parts = episode_id.rsplit("_", 1)
    return parts[0] if len(parts) == 2 and parts[1].isdigit() else None


def preconfigure_avatar(config: Any, agent_name: str, avatar_name: str) -> None:
    """Modify only the in-memory Hydra config; external YAML is never written."""
    avatar_root = EOVT_BENCH_ROOT / "assets" / "humanoids" / "humanoid_data" / avatar_name
    urdf = avatar_root / f"{avatar_name}.urdf"
    motion = avatar_root / f"{avatar_name}_motion_data_smplx.pkl"
    if not urdf.is_file() or not motion.is_file():
        raise FileNotFoundError(f"avatar assets missing under {avatar_root}")
    from habitat.config import read_write

    with read_write(config):
        agent = config.habitat.simulator.agents[agent_name]
        agent.articulated_agent_urdf = str(urdf)
        agent.motion_data_path = str(motion)

