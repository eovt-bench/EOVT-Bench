# Release status

Benchmark/evaluator version: `0.2.5-pre.20261125` /
`eovt-evaluator-20261125-v0.2`.
Public distribution update: 2026-11-25.

This source version publishes the benchmark interface, diagnostic baselines, current
versioned OR/IC evaluator and selected OmTrackVLA qualitative demonstrations.

## Included

- Fixed definitions for 60 layouts, 1,800 STT episodes, 630 OR events and
  630 IC events (one Same and three distinct Similar trials per event).
- Original-target assignments, descriptions and fixed Similar candidates.
- RGB Tracker PID and Oracle PID code, configuration and custom environment.
- Shared evaluator, layout-cluster bootstrap and a historical-metric subset tool.
- Versioned OR visibility/recovery and Same-referenced IC behavioral
  scoring modules.
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

The default branch and public release tags use a project-attributed source
snapshot. Published source files omit personal contact information and private
machine paths. Platform caches and copies held outside this repository are
outside the scope of a Git history update.

## Metric version

The release adds `eovt-or-ic-v0.2`. OR uses actual runtime loss events
and synchronized target visibility evidence. IC uses complete Same-referenced
trajectory and pose evidence; OTPR is not used for the binary decision.
Previously reported aggregate tables retain their original
`eovt-evaluator-20261121` label and are not silently recomputed.
See `evaluation/PROTOCOL.md`.

## Validation and limitations

Local checks are recorded in `VALIDATION_REPORT.json`. Current demonstrations
add four timestamped STT captures, select Road/Indoor cases from the completed
630-event OR raw collection, and include sixteen IC closed-loop recordings from
four complete 1+3 events. Each of the four main IC cases uses a different
event and Same control. The selected OR cases contain visually checked,
sustained complete disappearance, followed by recovery or failure to recover.
All task videos and IC Same controls use 0.5x simulation-speed playback:
presentation time is twice elapsed simulation time. Original scorer
timestamps and results remain unchanged; no captured frames are dropped
or interpolated. The video release v0.2.4 is a presentation-only update to v0.2.3.
The 12 selected main videos are fully decoded and checked against logged frame
counts. The current IC port matches all 20 frozen development decisions; this
is code regression, not independent human validation or a clean-install test.
Historical aggregate performance tables have not been silently recomputed.

Source v0.2.5 corrects citation/inventory metadata and adds protocol/layout
guards to execution and reporting, and fixes inconsistent Same-collision
diagnostic text. Numerical OR/IC thresholds, binary decisions and
the v0.2.4 video assets are unchanged. The archived scorer byte manifest
remains tied to its source tag. See [repository audit](REPOSITORY_AUDIT.md).

Public access is not a blanket code/data license. Existing copyright notices
and resource-specific permissions remain applicable. The root `LICENSE`
does not grant a new license for the complete package.
