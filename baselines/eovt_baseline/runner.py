from __future__ import annotations

import argparse
import os
import random
import sys
import traceback
from pathlib import Path

import numpy as np

from .agent import BaselineAgent
from .config import load_config
from .evaluator import evaluate_identity, evaluate_standard
from .paths import BASELINE_ROOT, EOVT_BENCH_ROOT, resolve_readonly, writable_path
from .result_schema import atomic_write_json
from .runtime import (
    configure_process_environment,
    dataset_file,
    install_driver_paths,
    install_readonly_humanoid_info_redirect,
    preconfigure_avatar,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Independent EOVT-Bench oracle/RGB PID baselines")
    parser.add_argument("--variant", choices=("oracle_pid", "rgb_tracker_pid"), required=True)
    parser.add_argument("--task", choices=("stt", "or", "ic"), required=True)
    parser.add_argument("--config", help="Baseline JSON config; default configs/<variant>.json")
    parser.add_argument("--driver-root", default="../evaluation/runtime", help="Read-only bundled environment driver")
    parser.add_argument("--dataset-root", default="../episodes", help="Read-only EOVT-Bench dataset root")
    parser.add_argument("--dataset-path", help="Explicit read-only dataset JSON.GZ (recommended for IC appearance v2)")
    parser.add_argument("--habitat-config", default="configs/habitat/benchmark/nav/track/track_infer_stt.yaml")
    parser.add_argument("--output", help="Output path; must remain inside this baseline directory")
    parser.add_argument("--split-num", type=int, default=1)
    parser.add_argument("--split-id", type=int, default=0)
    parser.add_argument("--max-episodes", type=int)
    parser.add_argument("--gpu", type=int, default=0, help="Habitat and detector CUDA device index")
    parser.add_argument("--egl-device", type=int, help="Optional Habitat-Sim EGL device override")
    parser.add_argument("--resume", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.split_num < 1 or not 0 <= args.split_id < args.split_num:
        raise SystemExit("--split-id must be in [0, split-num)")
    if args.max_episodes is not None and args.max_episodes < 1:
        raise SystemExit("--max-episodes must be positive")

    configure_process_environment()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    driver = install_driver_paths(args.driver_root)
    config_override = args.config
    if config_override is None and args.task == "ic":
        config_override = EOVT_BENCH_ROOT / "configs" / "baselines" / f"{args.variant}_ic.json"
    baseline_config = load_config(args.variant, config_override)
    baseline_config.detector["device"] = "cuda:0"
    output = writable_path(args.output or f"outputs/{args.variant}/{args.task}")
    output.mkdir(parents=True, exist_ok=True)
    status_path = output / "run_status_info.json"
    status = {"status": "RUNNING", "variant": args.variant, "task": args.task, "split_id": args.split_id, "split_num": args.split_num}
    atomic_write_json(status_path, status)

    try:
        # EOVT-Bench's scene dataset manifests contain relative asset paths and
        # therefore require this cwd. A narrowly scoped read redirect handles
        # the upstream task's hard-coded humanoid_infos.json path.
        os.chdir(EOVT_BENCH_ROOT)
        install_readonly_humanoid_info_redirect(driver)
        import habitat
        import eovt_bench  # noqa: F401 - registers the dataset/task
        from habitat.config import read_write

        config_path = resolve_readonly(EOVT_BENCH_ROOT / args.habitat_config)
        habitat_config = habitat.get_config(str(config_path))
        if args.dataset_path:
            data_path = Path(args.dataset_path).expanduser().resolve()
            if not data_path.is_file():
                raise FileNotFoundError(f"dataset not found: {data_path}")
        else:
            data_path = dataset_file(args.dataset_root, args.task)
        robot_urdf = EOVT_BENCH_ROOT / "assets" / "robots" / "hab_spot_arm" / "urdf" / "hab_spot_arm.urdf"
        if not robot_urdf.is_file():
            raise FileNotFoundError(f"robot URDF not found: {robot_urdf}")
        with read_write(habitat_config):
            habitat_config.habitat.dataset.data_path = str(data_path)
            habitat_config.habitat.dataset.scenes_dir = ""
            habitat_config.habitat.dataset.split = "val"
            habitat_config.habitat.environment.max_episode_steps = baseline_config.evaluation.max_steps
            if args.egl_device is not None:
                habitat_config.habitat.simulator.habitat_sim_v0.gpu_device_id = args.egl_device
            else:
                habitat_config.habitat.simulator.habitat_sim_v0.gpu_device_id = 0
            habitat_config.habitat.simulator.agents.agent_1.articulated_agent_urdf = str(robot_urdf)
        preconfigure_avatar(habitat_config, "agent_0", "male_4")
        # Habitat instantiates every configured articulated agent before the
        # episode tells the task how many extras are active. Give inactive
        # slots valid absolute assets as well.
        for agent_index in range(2, 9):
            preconfigure_avatar(habitat_config, f"agent_{agent_index}", "female_2")

        seed = int(habitat_config.habitat.simulator.seed)
        random.seed(seed)
        np.random.seed(seed)
        dataset = habitat.datasets.make_dataset(habitat_config.habitat.dataset.type, config=habitat_config.habitat.dataset)
        try:
            splits = dataset.get_splits(args.split_num, allow_uneven_splits=True)
        except TypeError:
            splits = dataset.get_splits(args.split_num)
        dataset = splits[args.split_id]
        agent = BaselineAgent(baseline_config, device_override="cuda:0")
        if args.task == "ic":
            counts = evaluate_identity(
                habitat, habitat_config, dataset, agent, baseline_config, output,
                resume=args.resume, max_episodes=args.max_episodes,
            )
        else:
            counts = evaluate_standard(
                habitat, habitat_config, dataset, agent, baseline_config, args.task, output,
                resume=args.resume, max_episodes=args.max_episodes,
            )
        status.update({"status": "PASS" if counts["failed"] == 0 else "PARTIAL", **counts})
        atomic_write_json(status_path, status)
        print(status, flush=True)
        return 0 if counts["failed"] == 0 else 2
    except Exception:
        status.update({"status": "FAIL", "error": traceback.format_exc()})
        atomic_write_json(status_path, status)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

