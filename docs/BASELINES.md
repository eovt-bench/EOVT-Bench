# Baselines and allowed information

| Item | RGB Tracker PID | Oracle PID |
| --- | --- | --- |
| Image | Robot jaw RGB | Same RGB for common interface |
| Detection | YOLO11x person detector | Target-specific simulator sensor box |
| Initialization | Largest detected person, without target truth | Original-target truth sensor |
| Association | IoU, center motion and RGB appearance | Shared association on target-specific detections |
| Control | Bounding-box PID | Same PID implementation |
| Privileged policy input | No target position, identity, future path or reference event labels | Target box/facing and semantic ID from simulator |
| Online task support | STT, current OR and current IC | STT, current OR and current IC |

The RGB detector ignores target-truth task observations. Evaluator access to
simulator state for termination, progression and logging is distinct from
the policy's inputs. Oracle PID is a diagnostic reference, not a guaranteed
performance upper bound.

Exact parameters are in `configs/baselines/`. IC uses `_ic.json`.
Search yaw differs between configurations; do not replace those files with
an unspecified common search policy. Detector weights have frozen checksums.

## Runtime

`evaluation/runtime/` contains the modified Habitat-Lab/custom tracking driver.
All paths resolve relative to the repository. The runner keeps the original
300-step limit, distance/loss termination, control and event activation rules.
PID commands and simulator velocity multipliers are different quantities;
the full simulator configuration is under `configs/habitat/`.

IC activates a candidate at the first visible-to-invisible transition or
the existing estimated-event-step fallback. It preserves the historical
one-meter offset placement and subsequent environment motion. The original
target stays present; robot actions continue.

Historical baseline dominance is the fraction of post-activation steps for which Euclidean
robot-to-original distance is strictly smaller than robot-to-candidate distance.
An equal-distance step contributes false to that comparison. The existing
runtime's recorded empty-trace behavior is retained. Navigation-graph distance
and reachability handling are not claimed.

The historical runner's facing/dominance summaries and BIA/SameSR/SwapSR
fields are legacy compatibility outputs. They must not be presented as v0.2
OR/IC results. Canonical v0.2 scoring is performed by
`evaluation/score_or_ic.py` from the synchronized evidence described in
`evaluation/PROTOCOL.md`; historical summaries alone are insufficient.
The latest demonstration package also supplies complete scorer inputs.

## Current OR/IC collection

The default runner records initialization and every actual simulator step,
including simulation timestamps, complete robot/actor transforms, action
commands, target-instance pixel counts, activation and termination. IC records
one Same plus all three Similar trials before scoring. A failed Same excludes
the event without inventing Similar outcomes. Actor motion is suppressed while
the additional person is hidden; robot policy actions continue throughout.

OR retains true visible masks and renders a target-only full projection from
the exact captured camera and articulated pose after the policy environment
closes. The 3x canvas preserves the central camera intrinsics. Mask alignment,
zero projection and clipping checks preserve invalid ratios as missing evidence.
Projection does not advance or teleport the policy environment.

Each current result records its evidence path/SHA-256, execution fingerprint
and scorer version. Each evidence attempt has a separate directory; aggregation
ignores these auxiliary files. Resume requires all evidence checks to pass.
`--episode-id` selects fixed cases; `--seed` sets Python/NumPy trial seeds.
The resolved simulator configuration and source checksums are retained in
`run_manifest_info.json`. Same/Similar use the same seed; environment motion can
still differ and the current scorer explicitly handles differing target paths.

```bash
python run_baseline.py --variant oracle_pid --task or --gpu 0 --resume
python run_baseline.py --variant rgb_tracker_pid --task ic --gpu 0 --resume
```

Real local simulator smoke checks cover both methods' current OR and full
1+3 IC execution. They verify the interface, not population performance.
Historical reproduction requires `--legacy-online-metrics`, writes to
`or_legacy` / `ic_legacy`, and must be aggregated with `--allow-legacy`.
Historical results do not carry the current v0.2 scorer version.
