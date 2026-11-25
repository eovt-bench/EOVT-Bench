# Public evaluation protocol

Current public protocol: `eovt-or-ic-initial-v0.1`.
The threshold file is
[`configs/evaluation/or_ic_initial_v0.1.json`](../configs/evaluation/or_ic_initial_v0.1.json).
The values are the initial frozen settings for reproducible evaluation. They
are versioned protocol choices, not claims that a universal optimum exists.

## STT

SR, TR and CR retain the existing definitions. The evaluator averages valid
episode-level `success`, `following_rate` and `collision` values. It does not
pool time steps across episodes.

## OR: actual loss, observation opportunity and recovery

The 630 reference events are selected with the same fixed geometry:

- path sampling interval: 0.25 m;
- observer lag: 2.0 m;
- 9 visibility rays, at least 5 blocked;
- pre-occlusion clear path: `> 2.5 m`;
- occlusion length: `>= 0.5 m`;
- no additional post-clear path requirement in this initial release.

These are reference-event filters. They do not imply that every policy
experiences a runtime loss.

The public OR scorer reads synchronized target-instance pixels and
robot-target distance from rollout evidence. It requires five initial visible
steps, confirms a loss after three consecutive invisible steps, confirms a
reappearance opportunity after two consecutive visible steps, and requires
five consecutive effective-following steps for recovery. The recovery window
is 50 environment steps. A target is visible when its mask has at least
`max(16, ceil(0.001 * image_area))` pixels. Effective following also requires
distance `<= 3.0 m`, a target pixel fraction between the configured lower and
upper limits, and no collision.

The denominator is the number of **actual runtime loss events**, not the
number of reference events:

```text
RSR = recovered events / actual loss events
VOR = confirmed reappearance opportunities / actual loss events
CRR = recovered events / confirmed reappearance opportunities
MRS = mean (recovery confirmation step - loss onset step)
```

Events without an actual loss are reported separately and are excluded from
the recovery denominator. Incomplete observation windows are marked censored;
they are not silently converted into failures.

The standalone implementation is in [`evaluation/or_visibility.py`](or_visibility.py).
For a JSONL/JSON command-line entry point:

```bash
python evaluation/score_or_ic.py or frames.json --output or_result.json
```

## IC: Same-referenced behavioral identity consistency

Each event contains one Same control and three distinct Similar trials. The
public binary decision does **not** use OTPR, Euclidean dominance, or
navigation-graph dominance.

For each Similar trial, the scorer compares the complete post-activation robot
trajectory and pose against the corresponding Same trajectory. The initial
settings are:

- DTW robot-position RMS error `<= 0.75 m`;
- discrete Fréchet distance `<= 1.5 m`;
- endpoint error `<= 1.0 m`;
- robot path-length difference `<= max(0.5 m, 0.35 * Same path length)`;
- body-heading difference within `45 degrees` for at least 80% of the
  comparable time on each side;
- original-target pose support uses distance `0.5--3.0 m` and a
  robot-to-original-target angle `<=45 degrees`;
- a clear distractor preference requires a distractor angle advantage of at
  least `15 degrees` and person-bearing separation of at least `25 degrees`;
- terminal support uses a 1.0-second window, at least 0.5 seconds of
  continuous support, and a 60% support fraction;
- actual simulation timestamps are used; a gap over 0.2 seconds invalidates
  the corresponding evidence.

If the original target path changes substantially, the Same robot path is not
used as a hard gate; the scorer falls back to the direct original-target pose
support rule. A Similar trial receives one of two public labels:

- `follow_original_target`;
- `failure`.

Failure does not automatically mean that the robot selected the distractor.
It means that the declared original-target behavioral criterion was not met.
Malformed or missing trajectory evidence is an input error rather than a model
failure.

The standalone implementation is in
[`evaluation/ic_behavior.py`](ic_behavior.py). It expects complete trial
records containing robot pose, original-target position and, for Similar
trials, distractor position. The old `target_dominance`/OTPR fields remain
available only for compatibility and audit; they are not part of the current
IC binary decision.

For event-level reporting, publish:

```text
same_success
similar_count
similar_follow_original_count
effective_follow_ratio
```

`effective_follow_ratio` is the number of Similar trials labeled
`follow_original_target` divided by the valid Similar trials in that event.
Results must retain the protocol version and evidence source.
For a single event JSON:

```bash
python evaluation/score_or_ic.py ic ic_event.json --output ic_result.json
```

## Baselines and videos

RGB Tracker PID and Oracle PID are public diagnostic baselines. Their
interface, configuration and allowed information are documented in
[`docs/BASELINES.md`](../docs/BASELINES.md).

The OmTrackVLA first-person videos are qualitative demonstrations only. They
show two successful and two failed cases for each task. They do not publish
OmTrackVLA weights or internal implementation. Existing video evidence
generated under the previous evaluator is labeled with its original scoring
version; it must not be silently relabeled as a v0.1 OR/IC score without the
required trajectory evidence.

## Uncertainty

Layout-cluster bootstrap remains the default uncertainty procedure:
2,000 replacement draws, seed `20261121`, and empirical 95% percentile
intervals. IC aggregates Similar outcomes within an event before layout-level
resampling. The evaluator reports eligibility, censored observations and
invalid-input counts separately.
