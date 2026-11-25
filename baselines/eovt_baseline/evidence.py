"""Synchronized simulator evidence, independent of any learned-model adapter."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .paths import EOVT_BENCH_ROOT, writable_path
from .result_schema import atomic_write_json

CAMERA = "agent_1_articulated_agent_jaw_panoptic"


def actor_state(actor: Any) -> dict:
    import magnum as mn

    transform = actor.base_transformation
    return {
        "position": np.asarray(actor.base_pos, dtype=float).tolist(),
        "forward": list(map(float, transform.transform_vector(mn.Vector3(1, 0, 0)))),
        "rotation_matrix_rows": np.asarray(transform, dtype=float)[:3, :3].tolist(),
        "transform": np.asarray(actor.sim_obj.transformation, dtype=float).tolist(),
        "joints": np.asarray(actor.sim_obj.joint_positions, dtype=float).tolist(),
    }


class EvidenceRecorder:
    """One record for initialization and every real environment step."""

    def __init__(self, directory: Path, *, episode, config, condition: str):
        self.directory = writable_path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.episode, self.condition = episode, condition
        self.rows: list[dict] = []
        self._stream = (self.directory / "capture.jsonl").open("w", encoding="utf-8")
        self._mask_dir = self.directory / "masks"
        self._mask_dir.mkdir(exist_ok=True)
        self._config = config
        self.metadata = None

    def capture(self, env, *, candidate=None, active=False, activation_time=None,
                applied_action=None, policy_debug=None) -> dict:
        sim = env.sim
        raw = sim.get_sensor_observations()
        target = sim.agents_mgr[0].articulated_agent
        robot = sim.agents_mgr[1].articulated_agent
        semantic_id = int(self.episode.info["main_human_semantic_id"])
        mask = np.asarray(raw[CAMERA]).squeeze() == semantic_id
        if mask.ndim != 2:
            raise ValueError("Target-instance camera must be a 2D image")
        spec = sim._sensors[CAMERA]._sensor_object.specification()
        sensor = sim._sensors[CAMERA]._sensor_object
        if self.metadata is None:
            urdf = Path(self._config.habitat.simulator.agents.agent_0.articulated_agent_urdf)
            self.metadata = {
                "semantic_id": semantic_id, "target_id": self.episode.info["main_humanoid_name"],
                "urdf": str(urdf.relative_to(EOVT_BENCH_ROOT)),
                "resolution": list(map(int, spec.resolution)),
                "hfov": float(spec.hfov), "near": float(spec.near), "far": float(spec.far),
                "gpu_device_id": int(self._config.habitat.simulator.habitat_sim_v0.gpu_device_id),
                "camera": CAMERA,
            }
            atomic_write_json(self.directory / "camera_info.json", self.metadata)
        metrics = dict(env.get_metrics())
        target_pose, robot_pose = actor_state(target), actor_state(robot)
        distance = math.dist(target_pose["position"], robot_pose["position"])
        count = int(mask.sum())
        row = {
            "episode_id": str(self.episode.episode_id), "condition": self.condition,
            "step": len(self.rows), "simulation_time_s": float(sim.get_world_time()),
            "robot": robot_pose, "target": target_pose,
            "original_id": self.episode.info["main_humanoid_name"],
            "candidate": actor_state(candidate) if active else None,
            "candidate_active": bool(active), "activation_time_s": activation_time,
            "target_pixels": count, "image_height": mask.shape[0], "image_width": mask.shape[1],
            "target_distance_m": distance,
            "human_following": bool(distance <= 3 and 3000 / (384 * 384) < count / mask.size < 0.3),
            "native_human_following": bool(metrics.get("human_following", False)),
            "collision": bool(metrics.get("human_collision", False)),
            "env_episode_over": bool(env.episode_over),
            "camera_transform": np.asarray(sensor.node.absolute_transformation(), dtype=float).tolist(),
            "action_applied": applied_action, "policy_debug": policy_debug,
        }
        if self.rows and row["simulation_time_s"] <= self.rows[-1]["simulation_time_s"]:
            raise ValueError("Simulator timestamps did not advance")
        if self.condition == "or":
            np.savez_compressed(self._mask_dir / f"{row['step']:06d}.npz", visible=mask)
        self.rows.append(row)
        self._stream.write(json.dumps(row, allow_nan=False) + "\n")
        self._stream.flush()
        return row

    def close(self):
        self._stream.close()

    def complete(self, trial_result: dict) -> None:
        if not self.rows:
            raise ValueError("Empty evidence")
        self.rows[-1]["termination_reason"] = trial_result["end_reason"]
        atomic_write_json(self.directory / "trial_info.json", {
            **trial_result, "recorded_frames": len(self.rows),
            "simulation_time_start_s": self.rows[0]["simulation_time_s"],
            "simulation_time_end_s": self.rows[-1]["simulation_time_s"],
        })
        # Publish the complete rows after termination evidence is attached.
        with (self.directory / "trajectory.jsonl").open("w", encoding="utf-8") as stream:
            for row in self.rows:
                stream.write(json.dumps(row, allow_nan=False) + "\n")


class CompleteTargetProjection:
    """Frozen-pose clone, same intrinsics in the center of a 3x canvas."""

    def __init__(self, metadata: dict):
        import habitat_sim as hs
        import magnum as mn

        self.semantic_id = metadata["semantic_id"]
        self.height, self.width = metadata["resolution"]
        camera = hs.CameraSensorSpec()
        camera.uuid = "target_only"
        camera.sensor_type = hs.SensorType.SEMANTIC
        camera.resolution = [self.height * 3, self.width * 3]
        camera.hfov = math.degrees(2 * math.atan(3 * math.tan(math.radians(metadata["hfov"]) / 2)))
        camera.near, camera.far = metadata["near"], metadata["far"]
        camera.position = mn.Vector3(0, 0, 0)
        config = hs.SimulatorConfiguration()
        config.scene_id, config.enable_physics = "NONE", True
        config.gpu_device_id = metadata["gpu_device_id"]
        agent = hs.agent.AgentConfiguration()
        agent.sensor_specifications = [camera]
        self.sim = hs.Simulator(hs.Configuration(config, [agent]))
        urdf = EOVT_BENCH_ROOT / metadata["urdf"]
        self.clone = self.sim.get_articulated_object_manager().add_articulated_object_from_urdf(
            str(urdf), fixed_base=False, maintain_link_order=True,
        )
        self.clone.motion_type = hs.physics.MotionType.KINEMATIC
        for motor_id in list(self.clone.existing_joint_motor_ids):
            self.clone.remove_joint_motor(motor_id)

    def render(self, visible: np.ndarray, row: dict):
        import magnum as mn

        self.clone.transformation = mn.Matrix4(np.asarray(row["target"]["transform"]))
        self.clone.joint_positions = np.asarray(row["target"]["joints"])
        camera = self.sim._sensors["target_only"]._sensor_object
        camera.node.transformation = mn.Matrix4(np.asarray(row["camera_transform"]))
        full = np.asarray(self.sim.get_sensor_observations()["target_only"]).squeeze() == self.semantic_id
        h, w = self.height, self.width
        center = full[h:2 * h, w:2 * w]
        count, visible_count = int(full.sum()), int(visible.sum())
        outside = int(np.count_nonzero(visible & ~center))
        verified = outside <= max(5, int(visible_count * 0.01))
        truncated = bool(full[0].any() or full[-1].any() or full[:, 0].any() or full[:, -1].any())
        raw_ratio = visible_count / count if count else None
        reason = (
            "full_projection_denominator_zero" if count == 0 else
            "expanded_projection_clipped" if truncated else
            "clone_alignment_failed" if not verified else
            "visible_count_exceeds_projection" if raw_ratio > 1.01 else None
        )
        return {
            "full_target_pixels": count, "full_in_view_pixels": int(center.sum()),
            "target_visibility_ratio": min(1.0, raw_ratio) if reason is None else None,
            "projection_verified": verified, "clone_disagreement_pixels": outside,
            "extended_canvas_truncated": truncated, "visibility_invalid_reason": reason,
        }, full

    def close(self):
        self.sim.close()


def finish_or_projection(recorder: EvidenceRecorder) -> list[dict]:
    """Projection never advances or teleports the policy's environment."""
    renderer = CompleteTargetProjection(recorder.metadata)
    try:
        for row in recorder.rows:
            path = recorder._mask_dir / f"{row['step']:06d}.npz"
            with np.load(path) as archive:
                visible = archive["visible"]
            details, full = renderer.render(visible, row)
            row.update(details)
            np.savez_compressed(path, visible=visible, full=full)
            if row["step"] % 50 == 0:
                print(f"[or projection] {row['step'] + 1}/{len(recorder.rows)}", flush=True)
    finally:
        renderer.close()
    with (recorder.directory / "frames.jsonl").open("w", encoding="utf-8") as stream:
        for row in recorder.rows:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
    return recorder.rows
