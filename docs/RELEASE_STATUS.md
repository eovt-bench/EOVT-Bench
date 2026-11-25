# Release status

Benchmark/evaluator version: `0.2.2-pre.20261125` /
`eovt-evaluator-20261125-v0.2`.
Public distribution update: 2026-11-25.

This release publishes the benchmark interface, diagnostic baselines, initial
versioned OR/IC evaluator and selected OmTrackVLA qualitative demonstrations.

## Included

- Fixed definitions for 60 layouts, 1,800 STT episodes, 630 OR events and
  630 IC events (one Same and three distinct Similar trials per event).
- Original-target assignments, descriptions and fixed Similar candidates.
- RGB Tracker PID and Oracle PID code, configuration and custom environment.
- Shared evaluator, layout-cluster bootstrap and offline sensitivity tools.
- Versioned initial OR visibility/recovery and Same-referenced IC behavioral
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
reuse unchanged STT captures, rescore the completed 630-event OR raw collection,
and add eight new IC closed-loop recordings from two complete 1+3 events.
The 12 selected main videos are fully decoded and checked against logged frame
counts. The current IC port matches all 20 frozen development decisions; this
is code regression, not independent human validation or a clean-install test.
Historical aggregate performance tables have not been silently recomputed.

Public access is not a blanket code/data license. Existing copyright notices
and resource-specific permissions remain applicable. The root `LICENSE`
does not grant a new license for the complete package.
