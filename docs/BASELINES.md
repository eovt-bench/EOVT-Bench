# Baselines and allowed information

| Item | RGB Tracker PID | Oracle PID |
| --- | --- | --- |
| Image | Robot jaw RGB | Same RGB for common interface |
| Detection | YOLO11x person detector | Target-specific simulator sensor box |
| Initialization | Largest detected person, without target truth | Original-target truth sensor |
| Association | IoU, center motion and RGB appearance | Shared association on target-specific detections |
| Control | Bounding-box PID | Same PID implementation |
| Privileged policy input | No target position, identity, future path or reference event labels | Target box/facing and semantic ID from simulator |
| Tasks | STT, OR, IC | STT, OR, IC |

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

Baseline dominance is the fraction of post-activation steps for which Euclidean
robot-to-original distance is strictly smaller than robot-to-candidate distance.
An equal-distance step contributes false to that comparison. The existing
runtime's recorded empty-trace behavior is retained. Navigation-graph distance
and reachability handling are not claimed.

The existing runner's online facing/dominance summaries and BIA/SameSR/SwapSR
fields are legacy compatibility outputs. They must not be presented as v0.2
OR/IC results. Canonical v0.2 scoring is performed by
`evaluation/score_or_ic.py` from the synchronized evidence described in
`evaluation/PROTOCOL.md`; historical summaries alone are insufficient.
The latest demonstration package supplies complete scorer inputs.
Resource checks and offline reproduction do not constitute a new GPU rollout.
