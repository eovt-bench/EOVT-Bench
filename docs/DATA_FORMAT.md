# Data and output fields

## Canonical task files

| Task | File | Records |
| --- | --- | --- |
| STT | `episodes/STT/val/val.json.gz` | 1,800 |
| OR | `episodes/OR/val/val.json.gz` | 630 |
| IC | `episodes/IC/val/val.json.gz` | 630 |

Each decompresses to `{"episodes": [...]}`. These native Habitat records are
the executable interface. The index is `episodes/index/all_episodes.json.gz`.
Additional manifests are under `episodes/metadata/`.

| Field | Meaning |
| --- | --- |
| `episode_id` | Unique episode/event identifier |
| `scene_id` | Relative stage/scene path under repository root |
| `scene_dataset_config` | Relative scene-dataset configuration |
| `start_position`, `start_rotation` | Native episode start; do not substitute for robot state |
| `goals` | Ordered target navigation goals with positions |
| `info.robot_position`, `info.robot_rotation` | Robot initial state consumed by custom task |
| `info.main_humanoid_name` | Original target asset ID |
| `info.instruction` | Language description/instruction |
| `info.eovt_generation` | Reference-generation metadata and navigation resources |
| `info.eovt_task` | OR/IC event and trial definition |

The bundled custom environment defines coordinate/rotation use and action
interpretation. Source fields are preserved rather than converted into a new
coordinate convention.

## OR event

`info.eovt_task` contains `event_id`, `source_episode_id`, `layout_id`,
`scene_category`, `source_event_index`, `event_arc_length_m`,
`pre_clear_length_m`, `post_clear_length_m`, and `selection_criteria`.
Current descriptive fields use the canonical full task name and
`task_version = eovt-or-ic-v0.2`. `reference_annotation_version` and
`legacy_task_*` preserve the original annotation provenance. This does not
recompute reference events or change their paths, actors or selection values.

The frozen selection is pre-clear length **>2.5 m**, occlusion length
**>=0.5 m**, with no additional post-event reappearance requirement.
These reference lengths are not runtime visibility observations.
Current runtime OR thresholds are in
`configs/evaluation/or_visibility_v0.2.json`; the reference selection
parameters are documented in `evaluation/PROTOCOL.md`.
`configs/evaluation/or_ic_initial_v0.1.json` is retained for historical
compatibility. Runtime OR evidence must
contain synchronized `step`, `simulation_time_s` (or accepted alias
`world_time_s`), `target_pixels`,
`image_height`, `image_width`, `target_distance_m`, `collision` and
`env_episode_over` fields.

## IC trials

`identity_protocol_version = appearance_top3_1same_3similar_v1`.
Each event has one `same` and three `similar` trials, with three distinct
candidate actors excluding the original target.
The original target, descriptions, selection seed and candidates are frozen
in the metadata; methods do not resample them independently.
Published candidate assignments are not restricted to the same gender.

The original target remains present and an additional actor is activated.
The canonical condition name is `similar`. Readers may accept the legacy
strings `similar_swap` and `swap` for backward compatibility; neither means
removal of the original target.
`legacy_expected_label` preserves the former label as provenance; it is not
a requested model output or the current behavioral evaluation target.
The effective action mode is `closed_loop_model_actions_executed`.
`legacy_action_mode`, if present, does not override the effective runtime mode.

## Historical online result schema

Final JSONs include `schema_version`, `episode_id`, `source_episode_id`,
`task`, `method`, `layout`, `scene_category`, `success`, `following_rate`,
and `collision`.
OR adds `rsr`, `vor`, `crr`, `recovery_steps`, `lost_index`, `reacquired_index`.
IC adds `identity_trials` and four `identity_trial_results`.
Similar trials store `target_dominance_rate` or `target_dominance`.
Those fields belong to the legacy OTPR-compatible schema. For the current IC
protocol, trial evidence must additionally provide complete records with
`robot_position`, `robot_heading_*`, `original_position` and
`distractor_position`. `simulation_time_s`, recorded person IDs, activation flags and termination
evidence are mandatory. Current scored trials carry
`identity_evaluator_version = eovt-ic-behavior-v0.2` and a binary
`behavior_label` of `follow_original_target` or `failure`.

Current event-level IC summaries expose `same_success`, `similar_count`,
`similar_follow_original_count` and `effective_follow_ratio`. Missing
trajectory evidence is an input error; it is not converted into a model
failure.

Current OR records additionally contain `target_visibility_ratio` from a
verified complete-target projection and actual simulation timestamps.
The current OR score version is `eovt-or-visibility-v0.2`. No-loss records
have null recovery scores; censored outcomes remain null and are reported
separately. Historical facing summaries cannot be converted to these scores
without the missing evidence.

## Current scorer context and examples

The scorer preserves supplied `layout`, `layout_id`, `scene_category` and
`source_episode_id` context. For OR, provide it in the wrapper object or the
first frame; for IC, provide it on the event object. Use an explicit
`layout`/`layout_id` for custom event names. The aggregator requires real
layout evidence when bootstrap is enabled.
Current IC event summaries use `identity_evaluator_version` and
`similar_results`; they do not require legacy BIA or generic `success`.
Current OR summaries use `protocol_version`, `actual_loss`, `opportunity`,
`recovered`, `censored` and nullable recovery scores.
The historical schema above is not a universal required schema for current
scored events.

`finish=false` or `status=Lost` alone does not mean a damaged result:
completed failures are outcomes. Missing records, malformed JSON and wrong
trial structures are data issues. Current IC excludes a colliding Same
control and counts a colliding eligible Similar trial as failure. Historical
uncertain labels are not current IC outputs.
`*_info.json`, status files and videos are not independent samples.
Current baseline results also contain `evidence`, `evidence_sha256` and
`execution_fingerprint`. Evidence is stored under an event's `*_evidence/`
directory, with one unique attempt per execution. OR provides `frames.jsonl`
and synchronized masks; IC provides `ic_event.json`, complete trial trajectories
and termination records. These auxiliary directories are not result samples.

`examples/selection.json` links one Industrial event to its source episode.
The three files in `examples/episodes/` are matched real inputs. Baseline
historical aggregate results are archived in `docs/HISTORICAL_REFERENCE_RESULTS.md`; per-episode baseline result
examples are not distributed. The result fields above document outputs
that users generate from their own runs.
