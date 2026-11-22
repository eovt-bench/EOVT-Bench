# Release status

Benchmark/evaluator version: `0.1.0-pre.20261121` / `eovt-evaluator-20261121`.
Public distribution update: 2026-11-22.

Access is temporarily restricted pending hosting-provider cleanup of obsolete
history caches. The current source snapshot and release tags are sanitized;
this does not establish removal of server-side cached historical objects.

## Included

- Fixed definitions for 60 layouts, 1,800 STT episodes, 630 OR events and
  630 IC events (one Same and three distinct Similar trials per event).
- Original-target assignments, descriptions and fixed Similar candidates.
- RGB Tracker PID and Oracle PID code, configuration and custom environment.
- Shared evaluator, layout-cluster bootstrap and offline sensitivity tools.
- Matched Industrial input episodes and selected qualitative videos.
- Baseline aggregate values and confidence intervals in the README files.
- External-resource acquisition guidance and compatibility checks.

## Public distribution

Baseline raw result JSONs, their result-file manifests and downloadable result
archives are not distributed. Historical baseline attachment links have been
removed. Users can evaluate their own locally generated result files.

Scene, humanoid, robot and detector binaries are acquired separately. The
benchmark scenes were constructed by the benchmark author; a standalone scene
archive is not attached. Follow the resource guide for the humanoid acquisition
link, upstream robot/detector sources and checksum verification.

The default branch and public release tags use a new project-attributed source
snapshot. Published source files omit personal contact information and private
machine paths. Platform caches and copies held outside this repository are
outside the scope of a Git history update.

## Metric version

This update changes distribution and documentation, not measured results.
The README tables retain the 2026-11-21 evaluator semantics. OR log-continuation
VOR is not an independent geometric visibility measurement. IC OTPR is a
distance-based behavioral proxy, not a direct identity classifier or the
proposed Same-trajectory/orientation criterion. See `evaluation/PROTOCOL.md`.

## Validation and limitations

Local offline logic, evaluator, resource-policy and syntax checks are recorded
in `VALIDATION_REPORT.json`. Twelve selected OmTrackVLA rollouts were previously
executed on an existing WSL2 installation; they are not a clean-install test or
a full benchmark rerun.

Public access is not a blanket code/data license. Existing copyright notices
and resource-specific permissions remain applicable. The root `LICENSE`
does not grant a new license for the complete package.
