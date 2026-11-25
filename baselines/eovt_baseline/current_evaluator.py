"""Current OR/IC execution with complete, independently rescorable evidence."""
from __future__ import annotations

import copy
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

from .evaluator import (
    _episode_output, _event_metadata, _identity_trial_config, _joint_action,
    _one_episode_dataset, _task_observations, _visibility,
)
from .evidence import EvidenceRecorder, finish_or_projection
from .metrics import generic_metrics
from .paths import EOVT_BENCH_ROOT
from .result_schema import atomic_write_json, validate_result
from .runtime import layout_id, preconfigure_avatar, scene_category

sys.path.insert(0, str(EOVT_BENCH_ROOT / "evaluation"))
from ic_current import score_event as score_ic
from or_current import score_event as score_or


def context(episode, task, method, fingerprint):
    event = _event_metadata(episode)
    return {
        "schema_version": "eovt-bench-current-v0.2", "task": task, "method": method,
        "episode_id": str(episode.episode_id),
        "source_episode_id": event.get("source_episode_id", str(episode.episode_id)),
        "layout_id": event.get("layout_id") or layout_id(episode),
        "scene_category": event.get("scene_category") or scene_category(episode),
        "execution_fingerprint": fingerprint, "current_or_ic_evidence_collected": True,
        "legacy_online_summary": False,
    }


def resumable(path, task, fingerprint, output_root):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False
        version = (data.get("protocol_version") == "eovt-or-visibility-v0.2" if task == "or"
                   else data.get("identity_evaluator_version") == "eovt-ic-behavior-v0.2")
        evidence = (output_root / data["evidence"]).resolve()
        intact = evidence.is_relative_to(output_root.resolve()) and evidence.is_file()
        return (
            version and data.get("execution_fingerprint") == fingerprint
            and not validate_result(data, task) and intact
            and hashlib.sha256(evidence.read_bytes()).hexdigest() == data["evidence_sha256"]
        )
    except (OSError, ValueError, TypeError, KeyError):
        return False


def _seed(value):
    random.seed(value)
    np.random.seed(value)


def run_trial(env, agent, config, recorder, *, candidate=None, estimated_event_step=None):
    """Observe/activate/capture, then execute one joint action; no hidden steps."""
    episode = env.current_episode
    agent.reset()
    active, activation_time, previous_visible, too_far = False, None, False, 0
    applied_action = policy_debug = None
    terminal = None
    if candidate is not None:
        target = env.sim.agents_mgr[0].articulated_agent
        candidate.base_pos = np.asarray(target.base_pos) + np.asarray([100., 0., 100.])
    for step in range(config.evaluation.max_steps + 1):
        task_obs = _task_observations(env, episode)
        visible = _visibility(task_obs)
        if candidate is not None and not active and terminal is None and not env.episode_over:
            transition = previous_visible and not visible
            fallback = estimated_event_step is not None and step >= estimated_event_step
            if transition or fallback:
                target = env.sim.agents_mgr[0].articulated_agent
                candidate.base_pos = np.asarray(target.base_pos) + np.asarray([1., 0., 0.])
                candidate.base_rot = target.base_rot
                active, activation_time = True, float(env.sim.get_world_time())
                task_obs = _task_observations(env, episode)
        row = recorder.capture(
            env, candidate=candidate, active=active, activation_time=activation_time,
            applied_action=applied_action, policy_debug=policy_debug,
        )
        if step:
            if row["collision"]:
                terminal = "Collision"
            elif not row["native_human_following"] and row["target_distance_m"] > config.evaluation.too_far_distance:
                too_far += 1
            else:
                too_far = 0
            if terminal is None and too_far > config.evaluation.too_far_patience:
                terminal = "Lost"
        if terminal or env.episode_over or step == config.evaluation.max_steps:
            break
        raw = env.sim.get_sensor_observations()
        command, policy_debug = agent.act(raw, task_obs, episode.info)
        action = _joint_action(env, command)
        if candidate is not None and not active:
            action["action"] = tuple(
                name for name in action["action"]
                if name != "agent_2_oracle_nav_randcoord_action_obstacle"
            )
        env.step(action)
        applied_action = list(map(float, command))
        previous_visible = visible
        if step % 50 == 0:
            print(f"[{recorder.condition}] {episode.episode_id} step={step + 1}", flush=True)
    final_metrics = dict(env.get_metrics())
    generic_rows = [
        {"human_following": float(r["native_human_following"])} for r in recorder.rows[1:]
    ]
    result = generic_metrics(generic_rows, final_metrics, config.evaluation.max_steps)
    result.update(
        status=terminal or "Normal", finish=bool(env.episode_over and terminal is None),
        end_reason=terminal or ("episode_over" if env.episode_over else "max_steps"),
        total_steps=len(recorder.rows) - 1,
        activated_step=next((r["step"] for r in recorder.rows if r["candidate_active"]), None),
        activation_time_s=activation_time,
    )
    return result


def evaluate_current(habitat, habitat_config, dataset, agent, baseline_config, task, output_root,
                     *, resume, max_episodes, fingerprint, seed=20261121):
    completed = skipped = failed = 0
    episodes = list(dataset.episodes)
    if max_episodes is not None:
        episodes = episodes[:max_episodes]
    for index, episode in enumerate(episodes):
        final_path, info_path = _episode_output(output_root, episode)
        if resume and resumable(final_path, task, fingerprint, output_root):
            skipped += 1
            continue
        folder = final_path.parent / (final_path.stem + "_evidence") / f"attempt_{time.time_ns()}"
        meta = context(episode, task, baseline_config.variant, fingerprint)
        try:
            if task == "or":
                _seed(seed)
                trial_config = copy.deepcopy(habitat_config)
                preconfigure_avatar(trial_config, "agent_0", episode.info["main_humanoid_name"])
                trial_dataset = _one_episode_dataset(dataset, episode)
                recorder = EvidenceRecorder(folder, episode=episode, config=trial_config, condition="or")
                try:
                    with habitat.TrackEnv(config=trial_config, dataset=trial_dataset) as env:
                        if hasattr(env.task, "_first_init"):
                            env.task._first_init = False
                        env.reset()
                        trial_result = run_trial(env, agent, baseline_config, recorder)
                finally:
                    recorder.close()
                recorder.complete(trial_result)
                rows = finish_or_projection(recorder)
                result = {**meta, **score_or(rows), "episode_metrics": trial_result}
                evidence_input = folder / "frames.jsonl"
            else:
                event = _event_metadata(episode)
                definitions = event.get("identity_trials", [])
                same_defs = [t for t in definitions if t["condition"] == "same"]
                similar_defs = [t for t in definitions if t["condition"] == "similar"]
                candidates = [t["actor_name_after_occlusion"] for t in similar_defs]
                original = episode.info["main_humanoid_name"]
                if len(same_defs) != 1 or len(similar_defs) != 3 or len(set(candidates)) != 3 or original in candidates:
                    raise ValueError("Current IC requires one Same and three distinct Similar people")
                trials = []
                for trial_index, definition in enumerate(same_defs + similar_defs):
                    _seed(seed)
                    trial_config, trial_episode = _identity_trial_config(habitat_config, episode, definition)
                    trial_dataset = _one_episode_dataset(dataset, trial_episode)
                    name = "same" if trial_index == 0 else f"similar_{trial_index}"
                    recorder = EvidenceRecorder(folder / name, episode=trial_episode,
                                                config=trial_config, condition=name)
                    try:
                        with habitat.TrackEnv(config=trial_config, dataset=trial_dataset) as env:
                            if hasattr(env.task, "_first_init"):
                                env.task._first_init = False
                            env.reset()
                            candidate = env.sim.agents_mgr[2].articulated_agent if trial_index else None
                            trial_result = run_trial(
                                env, agent, baseline_config, recorder, candidate=candidate,
                                estimated_event_step=max(5, round(event["pre_clear_length_m"] / 0.2)),
                            )
                    finally:
                        recorder.close()
                    recorder.complete(trial_result)
                    trials.append({
                        **trial_result, "records": recorder.rows, "condition": definition["condition"],
                        "actor_name": definition["actor_name_after_occlusion"],
                        "candidate_id": definition["actor_name_after_occlusion"] if trial_index else None,
                    })
                payload = {**meta, "same": trials[0], "similar": trials[1:]}
                evidence_input = folder / "ic_event.json"
                atomic_write_json(evidence_input, payload)
                result = {**meta, **score_ic(payload)}
            result["evidence"] = str(evidence_input.relative_to(output_root))
            result["evidence_sha256"] = hashlib.sha256(evidence_input.read_bytes()).hexdigest()
            atomic_write_json(info_path, {**meta, "event_metadata": _event_metadata(episode)})
            atomic_write_json(final_path, result)
            completed += 1
            outcome = (f"loss={result['actual_loss']} opportunity={result['opportunity']} recovered={result['recovered']}"
                       if task == "or" else
                       f"Same={result['same_success']} Similar={result['similar_count']} original={result['similar_follow_original_count']}")
            print(f"[{task}] {index + 1}/{len(episodes)} {episode.episode_id} {outcome}", flush=True)
        except Exception as error:
            failed += 1
            atomic_write_json(info_path, {**meta, "status": "FAIL", "error": repr(error)})
            print(f"[{task}] FAIL {episode.episode_id}: {error!r}", flush=True)
    return {"completed": completed, "skipped": skipped, "failed": failed}
