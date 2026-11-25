# Evaluation protocol v0.2

Protocol: `eovt-or-ic-v0.2`. Versioned thresholds are initial operational
choices, not universal or independently optimized constants. The v0.1 code
and threshold file remain explicitly historical; they are not the default CLI.

## STT

SR, TR and CR use the existing episode-level `success`, `following_rate`
and `collision` values. Average episodes; do not pool their time steps.

## OR: actual loss, an observation opportunity, then stable following

The reference event index still uses 0.25 m sampling, a 2.0 m observer lag,
9 rays with at least 5 blocked, a pre-clear length >2.5 m and an occlusion
length >=0.5 m. These filters provide common task indices. They do not assert
that the executing policy necessarily loses the target.

Use synchronized target-instance masks and genuine simulation timestamps.
After five initial visible records, three consecutive invisible records
establish actual loss. Visibility means at least
`max(16, ceil(0.001*image_area))` target-instance pixels. No actual loss:
report separately, exclude from the OR denominator.

After loss, an opportunity requires target image fraction 0.003–0.40,
visible target pixels / complete target projection pixels >=0.25, and
robot-target distance >=0.8 m, continuously for 0.2 simulation seconds.
Complete target projection is rendered with the same pose and camera in an
unoccluded target-only rendering. An invalid projection is missing evidence,
not a zero-visibility observation.
Tiny rasterization differences can make visible pixels slightly exceed the
full projection; the recorder clips the ratio to 1 after rejecting ratios
above 1.01. Original pixel counts and clone-disagreement counts remain logged.

Recovery requires effective STT following after opportunity confirmation,
continuously for 0.4 simulation seconds: distance <=3.0 m, target pixels
>3000 and <30% of a 384x384 image, and no recorded collision. Equivalent
pixel fractions are used at another resolution. The recovery window remains
50 environment steps from loss onset. Elapsed-time confirmation uses actual
timestamps; the window is explicitly in steps and is not converted to a
constant duration.

At most one loss/opportunity/recovery sequence is scored per indexed rollout:
the first confirmed runtime loss after initial visibility. Reference index
membership alone is not evidence that the loss was geometrically associated
with that reference interval.

```text
RSR = recovered / actual runtime loss events
VOR = observation opportunities / actual runtime loss events
CRR = recovered / observation opportunities
MRS = mean(recovery confirmation step - loss onset step), recovered only
```

An administrative cut is censored. Known task termination or collision is
an observed endpoint. Unknown projection evidence is retained explicitly;
if an outcome remains unobserved, return null and bounds, not a fabricated
failure or a reduced denominator. A confirmed recovery is already known even
if the full window was not subsequently recorded.

Implementation: `evaluation/or_visibility.py`; settings:
`configs/evaluation/or_visibility_v0.2.json`.

## IC: qualify Same before judging Similar

Each event contains 1 Same control and 3 trials with distinct recorded
appearance-neighbor IDs. The original target remains present; the additional
person is a distractor. Robot actions continue in closed loop. Historical
metadata may contain `hold_pose_after_event`; actual execution and recorded
robot poses take precedence and must be reported.

Same geometric qualification requires normal completion, no recorded
collision or <0.5 m contact proxy, final original-target distance 1–3 m,
final horizontal heading error <=45 degrees, at least 80% joint support in
the final 0.48 simulation seconds, and both complete paths >=0.08 m.
Geometric qualification is a separate field, not a reconstruction of missing
original evaluator success or semantic visibility.

For an eligible event, compare trajectories from actual Similar activation
to each trial's own final record, interpolating only the Same start boundary.
Do not crop to a common prefix or common end time, or fit a spatial transform.
Resample spatially at <=0.05 m. Use endpoint-anchored weighted DTW (squared
XZ distance, diagonal weight 2, horizontal/vertical weight 1, denominator
m+n), discrete Frechet distance, endpoint error and path-length difference.
Heading correspondence follows that spatial DTW, not favorable orientation
matching; all raw poses remain available for time-weighted heading coverage.

Thresholds: DTW RMS <=0.75 m, Frechet <=1.5 m, endpoint <=1.0 m, path-length
difference <=max(0.5 m, 35% of Same), heading difference <=45 degrees for >=80%
of each side's duration. These tests form one success route. They are not
individually compulsory for every positive trial.

When target motion itself differs substantially, do not use the Same robot
path as a hard gate. Instead test direct original-target support: distance
0.5–3.0 m, horizontal body heading error <=45 degrees, without clear distractor
preference. The latter needs distractor distance 0.5–3.0 m, heading <=45
degrees, angle advantage >=15 degrees and actual person-bearing separation
>=25 degrees.

Terminal support uses the last 1.0 second: >=60% duration, >=0.5 s continuous
support, >=0.5 s observed duration, and the last frame must support the label.
The pose fallback additionally requires >=60% whole-trial original support.
Real timestamps are mandatory; gaps >0.2 s are input errors. Lost, collision
and the existing close-contact proxy are failures. Sustained terminal
distractor preference overrides a matching robot path.

Public labels are `follow_original_target` and `failure`. Failure is not
automatically an identity switch. OTPR is optional audit information only;
no OTPR threshold contributes to the binary decision. These are behavioral
criteria, not direct access to the model's internal identity decision.

Settings: `ic_same_geometry_v0.2.json`, `ic_behavior_v0.2.json` and
`ic_spatial_v0.2.json` under `configs/evaluation/`. The public implementation
was checked for code-regression agreement with 20 frozen development pairs;
that check is not independent human validation.

## Run and aggregate

```bash
python evaluation/score_or_ic.py or frames.json --output or_result.json
python evaluation/score_or_ic.py ic ic_event.json --output ic_result.json
```

The OR input is JSONL, a JSON list, or a JSON object containing `records`
(accepted alias: `frames`). IC input
contains `same` and exactly three `similar` trial objects with person IDs.
Complete examples accompany the current qualitative Release.
The current video archive's scorer byte manifest is tied to source tag
`v0.2.4-videos.20261125`; use that tag for exact archival byte reproduction.
Subsequent source audits may improve wrappers without changing the frozen
numerical decision rules or replacing that archived manifest.

Report Same eligibility, eligible Similar count, original-target-following
count and `effective_follow_ratio`. Keep exclusions separate from failures.
Use layout-cluster bootstrap (2,000 draws, seed 20261121, percentile 95% CI).
Aggregate IC trials within event before resampling layouts.
Custom event IDs require explicit `layout` or `layout_id` context. With
bootstrap enabled, missing layout evidence is an error.

The default aggregation entry rejects historical OR/IC results. Explicit
`--allow-legacy` enables historical analysis and reports input versions;
mixed current/historical evaluator versions remain an error.
`event_filter_sensitivity.py` is a historical-metric subset tool requiring
the same explicit opt-in. It is not a current v0.2 sensitivity evaluator.

Historical baseline aggregate tables retain their original scoring version.
Qualitative examples are selected illustrations, not population estimates.
No model weights or model implementation are distributed.
