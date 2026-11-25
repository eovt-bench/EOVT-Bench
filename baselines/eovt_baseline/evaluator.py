from __future__ import annotations

import copy
import random
import time
from pathlib import Path
from typing import Any

import numpy as np

from .agent import BaselineAgent
from .config import BaselineConfig
from .metrics import generic_metrics, identity_metrics, occlusion_metrics
from .paths import EOVT_BENCH_ROOT, writable_path
from .result_schema import atomic_write_json, valid_final_result
from .runtime import layout_id, preconfigure_avatar, scene_category


def _event_metadata(episode: Any) -> dict[str, Any]:
    """Prefer the appearance-v2 task metadata carried in episode.info.

    The source IC dataset may still contain a legacy top-level eovt_event.
    Using it first silently reverts 1 SAME + 3 SIMILAR to the old six-trial
    protocol, so appearance-v2 metadata must take precedence.
    """
    info = getattr(episode, "info", {}) or {}
    info_event = dict(info.get("eovt_task", {}) or {})
    if info_event.get("identity_protocol_version") == "appearance_top3_1same_3similar_v1":
        return info_event
    event = getattr(episode, "eovt_event", None)
    if event:
        return dict(event)
    return info_event


def _episode_output(output_root: Path, episode: Any) -> tuple[Path, Path]:
    category = scene_category(episode)
    episode_id = str(episode.episode_id).replace("/", "_").replace("\\", "_")
    final_path = output_root / category / f"{episode_id}.json"
    info_path = output_root / category / f"{episode_id}_info.json"
    return final_path, info_path


def _task_observations(env: Any, episode: Any) -> dict[str, Any]:
    try:
        return env.task._get_observations(episode)
    except TypeError:
        return env.task._get_observations(episode=episode)


def _joint_action(env: Any, robot_action: np.ndarray) -> dict[str, Any]:
    action_names = ["agent_0_humanoid_navigate_action", "agent_1_base_velocity"]
    actions = getattr(env.task, "actions", {})
    for index in range(2, 9):
        name = f"agent_{index}_oracle_nav_randcoord_action_obstacle"
        if name in actions:
            action_names.append(name)
    return {
        "action": tuple(action_names),
        "action_args": {"agent_1_base_vel": [float(value) for value in robot_action]},
    }


def _visibility(task_observations: dict[str, Any]) -> bool:
    value = task_observations.get("agent_1_main_humanoid_detector_sensor")
    if value is None:
        for key, candidate in task_observations.items():
            if key.startswith("agent_1_") and key.endswith("main_humanoid_detector_sensor"):
                value = candidate
                break
    if value is not None:
        if isinstance(value, dict):
            facing = np.asarray(value.get("facing", False)).reshape(-1)
            return bool(facing.size and float(facing[0]) > 0)
        flat = np.asarray(value).reshape(-1)
        return bool(flat.size and float(flat[0]) > 0)
    return False


def run_episode(
    env: Any,
    agent: BaselineAgent,
    config: BaselineConfig,
    *,
    identity_condition: str | None = None,
    candidate_index: int = 2,
    event_step: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    episode = env.current_episode
    episode_info = dict(getattr(episode, "info", {}) or {})
    agent.reset()
    records: list[dict[str, Any]] = []
    visibility_trace: list[bool] = []
    too_far_count = 0
    activated = False
    previous_visible = False
    robot = env.sim.agents_mgr[1].articulated_agent
    target = env.sim.agents_mgr[0].articulated_agent
    is_similar = identity_condition in {"similar", "swap", "similar_swap"}
    candidate = env.sim.agents_mgr[candidate_index].articulated_agent if is_similar else None
    if candidate is not None:
        candidate.base_pos = target.base_pos + np.asarray([100.0, 0.0, 100.0], dtype=np.float32)

    start_time = time.time()
    for step in range(config.evaluation.max_steps):
        raw = env.sim.get_sensor_observations()
        task_obs = _task_observations(env, episode)
        visible = _visibility(task_obs)
        visibility_trace.append(visible)

        if candidate is not None and not activated:
            transition = previous_visible and not visible
            if transition or (event_step is not None and step >= event_step):
                try:
                    import magnum as mn

                    candidate.base_pos = target.base_pos + mn.Vector3(1.0, 0.0, 0.0)
                    candidate.base_rot = target.base_rot
                except (ImportError, TypeError):
                    candidate.base_pos = target.base_pos + np.asarray([1.0, 0.0, 0.0], dtype=np.float32)
                activated = True

        robot_action, debug = agent.act(raw, task_obs, episode_info)
        env.step(_joint_action(env, robot_action))
        metrics = dict(env.get_metrics())
        distance = float(np.linalg.norm(np.asarray(robot.base_pos) - np.asarray(target.base_pos)))
        record: dict[str, Any] = {
            "step": step + 1,
            "distance_to_target": distance,
            "human_following": float(metrics.get("human_following", 0.0)),
            "human_collision": float(metrics.get("human_collision", 0.0)),
            "target_visible": visible,
            **debug,
        }
        if candidate is not None and activated:
            candidate_distance = float(np.linalg.norm(np.asarray(robot.base_pos) - np.asarray(candidate.base_pos)))
            record["distance_to_candidate"] = candidate_distance
            record["target_preferred"] = float(distance < candidate_distance)
        records.append(record)
        previous_visible = visible

        if metrics.get("human_following", 0.0):
            too_far_count = 0
        elif distance > config.evaluation.too_far_distance:
            too_far_count += 1
        else:
            too_far_count = 0
        if metrics.get("human_collision", 0.0) or too_far_count > config.evaluation.too_far_patience:
            break
        if env.episode_over:
            break

    final_info = dict(env.get_metrics())
    generic = generic_metrics(records, final_info, config.evaluation.max_steps)
    result: dict[str, Any] = {
        **generic,
        "total_steps": len(records),
        "following_steps": int(sum(float(r["human_following"]) for r in records)),
        "elapsed_seconds": round(time.time() - start_time, 3),
    }
    details = {"records": records, "visibility_trace": visibility_trace, "final_metrics": final_info}
    if is_similar:
        dominance = [float(record["target_preferred"]) for record in records if "target_preferred" in record]
        result["target_retained"] = float(bool(dominance) and sum(dominance) / len(dominance) >= 0.5)
        result["target_dominance_rate"] = sum(dominance) / len(dominance) if dominance else 0.0
        result["distractor_activated"] = activated
    return result, details


def _base_result(episode: Any, task: str, method: str) -> dict[str, Any]:
    event = _event_metadata(episode)
    info = getattr(episode, "info", {}) or {}
    return {
        "schema_version": "eovt-bench-baseline-v1",
        "episode_id": str(episode.episode_id),
        "source_episode_id": event.get("source_episode_id", info.get("source_episode_id", episode.episode_id)),
        "task": task,
        "method": method,
        "layout": event.get("layout_id") or layout_id(episode),
        "scene_category": event.get("scene_category", scene_category(episode)),
    }


def evaluate_standard(
    habitat: Any,
    habitat_config: Any,
    dataset: Any,
    agent: BaselineAgent,
    baseline_config: BaselineConfig,
    task: str,
    output_root: Path,
    *,
    resume: bool,
    max_episodes: int | None,
) -> dict[str, int]:
    completed = skipped = failed = 0
    limit = len(dataset.episodes) if max_episodes is None else min(len(dataset.episodes), max_episodes)
    dataset.episodes = dataset.episodes[:limit]
    with habitat.TrackEnv(config=habitat_config, dataset=dataset) as env:
        if hasattr(env.task, "_first_init"):
            env.task._first_init = False
        for _ in range(limit):
            env.reset()
            episode = env.current_episode
            final_path, info_path = _episode_output(output_root, episode)
            if resume and valid_final_result(final_path):
                skipped += 1
                continue
            try:
                result, details = run_episode(env, agent, baseline_config)
                result = {**_base_result(episode, task, baseline_config.variant), **result}
                if task == "or":
                    result.update(occlusion_metrics(details["visibility_trace"]))
                atomic_write_json(info_path, {**_base_result(episode, task, baseline_config.variant), **details})
                atomic_write_json(final_path, result)
                completed += 1
                print(f"[{task}] {completed + skipped}/{limit} {episode.episode_id} SR={result['success']:.3f} TR={result['following_rate']:.3f} CR={result['collision']:.3f}", flush=True)
            except Exception as exc:
                failed += 1
                atomic_write_json(info_path, {**_base_result(episode, task, baseline_config.variant), "status": "FAIL", "error": repr(exc)})
                print(f"[{task}] FAIL {episode.episode_id}: {exc!r}", flush=True)
    return {"completed": completed, "skipped": skipped, "failed": failed}


def _one_episode_dataset(dataset: Any, episode: Any) -> Any:
    trial_dataset = copy.deepcopy(dataset)
    trial_dataset.episodes = [copy.deepcopy(episode)]
    return trial_dataset


def _identity_trial_config(base_config: Any, episode: Any, trial: dict[str, Any]) -> tuple[Any, Any]:
    config = copy.deepcopy(base_config)
    trial_episode = copy.deepcopy(episode)
    info = trial_episode.info
    target_name = str(trial.get("target_actor_name", info.get("main_humanoid_name", "male_4")))
    preconfigure_avatar(config, "agent_0", target_name)
    if trial.get("condition") in {"similar", "swap", "similar_swap"}:
        candidate = str(trial["actor_name_after_occlusion"])
        preconfigure_avatar(config, "agent_2", candidate)
        info["human_num"] = max(1, int(info.get("human_num", 0)))
        info["extra_humanoid_names"] = [candidate]
    else:
        info["human_num"] = 0
        info["extra_humanoid_names"] = []
    return config, trial_episode


def evaluate_identity(
    habitat: Any,
    habitat_config: Any,
    dataset: Any,
    agent: BaselineAgent,
    baseline_config: BaselineConfig,
    output_root: Path,
    *,
    resume: bool,
    max_episodes: int | None,
) -> dict[str, int]:
    completed = skipped = failed = 0
    episodes = list(dataset.episodes)
    if max_episodes is not None:
        episodes = episodes[:max_episodes]
    for index, episode in enumerate(episodes, 1):
        final_path, info_path = _episode_output(output_root, episode)
        if resume and valid_final_result(final_path):
            try:
                import json
                existing = json.loads(final_path.read_text(encoding="utf-8"))
                complete_v2 = (
                    existing.get("identity_protocol") == "appearance_top3_1same_3similar_v1"
                    and len(existing.get("identity_trial_results", [])) == 4
                    and all(key in existing for key in (
                        "same_success_rate", "similar_success_rate", "balanced_identity_accuracy"
                    ))
                )
            except (OSError, ValueError, TypeError):
                complete_v2 = False
            if complete_v2:
                skipped += 1
                continue
        event = _event_metadata(episode)
        trials = list(event.get("identity_trials", []))
        if not trials:
            failed += 1
            atomic_write_json(info_path, {**_base_result(episode, "ic", baseline_config.variant), "status": "FAIL", "error": "identity_trials missing"})
            continue
        protocol = str(event.get("identity_protocol_version", ""))
        if protocol == "appearance_top3_1same_3similar_v1":
            same_trials = [t for t in trials if t.get("condition") == "same"]
            similar_trials = [t for t in trials if t.get("condition") in {"similar", "swap", "similar_swap"}]
            candidates = [t.get("actor_name_after_occlusion") for t in similar_trials]
            if len(trials) != 4 or len(same_trials) != 1 or len(similar_trials) != 3 or len(set(candidates)) != 3:
                failed += 1
                atomic_write_json(info_path, {
                    **_base_result(episode, "ic", baseline_config.variant),
                    "status": "FAIL",
                    "error": "appearance IC requires exactly 1 same + 3 distinct similar trials",
                })
                continue
        trial_results = []
        trial_details = []
        try:
            pre_clear = float(event.get("pre_clear_length_m", 0.0))
            estimated_event_step = max(5, int(round(pre_clear / 0.2)))
            for trial in trials:
                trial_config, trial_episode = _identity_trial_config(habitat_config, episode, trial)
                trial_dataset = _one_episode_dataset(dataset, trial_episode)
                with habitat.TrackEnv(config=trial_config, dataset=trial_dataset) as env:
                    if hasattr(env.task, "_first_init"):
                        env.task._first_init = False
                    env.reset()
                    result, details = run_episode(
                        env,
                        agent,
                        baseline_config,
                        identity_condition=str(trial.get("condition")),
                        event_step=estimated_event_step,
                    )
                result.update({"round_id": trial.get("round_id"), "condition": trial.get("condition"), "candidate": trial.get("actor_name_after_occlusion")})
                if trial.get("condition") == "same":
                    result["target_retained"] = result["success"]
                trial_results.append(result)
                trial_details.append({
                    "trial": trial,
                    "result": result,
                    "details_summary": {
                        "record_count": len(details.get("records", [])),
                        "sensor_visible_steps": sum(bool(value) for value in details.get("visibility_trace", [])),
                        "detected_steps": sum(bool(row.get("visible")) for row in details.get("records", [])),
                        "following_steps": sum(float(row.get("human_following", 0.0)) for row in details.get("records", [])),
                        "distance_initial": details.get("records", [{}])[0].get("distance_to_target") if details.get("records") else None,
                        "distance_final": details.get("records", [{}])[-1].get("distance_to_target") if details.get("records") else None,
                        "distance_min": min((row.get("distance_to_target") for row in details.get("records", []) if row.get("distance_to_target") is not None), default=None),
                        "distance_max": max((row.get("distance_to_target") for row in details.get("records", []) if row.get("distance_to_target") is not None), default=None),
                        "first_actions": [row.get("action") for row in details.get("records", [])[:5]],
                    },
                })
            special = identity_metrics(trial_results)
            result = {
                **_base_result(episode, "ic", baseline_config.variant),
                "success": special["balanced_identity_accuracy"],
                "following_rate": float(np.mean([row["following_rate"] for row in trial_results])),
                "collision": float(np.mean([row["collision"] for row in trial_results])),
                **special,
                "same_success": special["same_success_rate"],
                "similar_success": special["similar_success_rate"],
                # Legacy aliases remain in generated output for audit compatibility.
                "swap_success": special["swap_success_rate"],
                "similar_bia": special["balanced_identity_accuracy"],
                "identity_protocol": protocol or "closed_loop_target_vs_distractor_v2",
                "identity_trials": trials,
                "identity_trial_results": trial_results,
            }
            atomic_write_json(info_path, {**_base_result(episode, "ic", baseline_config.variant), "trials": trial_details})
            atomic_write_json(final_path, result)
            completed += 1
            print(f"[ic] {index}/{len(episodes)} {episode.episode_id} SameSR={special['same_success_rate']:.3f} SimilarSR={special['similar_success_rate']:.3f} BIA={special['balanced_identity_accuracy']:.3f}", flush=True)
        except Exception as exc:
            failed += 1
            atomic_write_json(info_path, {**_base_result(episode, "ic", baseline_config.variant), "status": "FAIL", "error": repr(exc), "partial_trials": trial_details})
            print(f"[ic] FAIL {episode.episode_id}: {exc!r}", flush=True)
    return {"completed": completed, "skipped": skipped, "failed": failed}
