# Release status

Source candidate: `0.2.6-pre.20261125`; evaluator: `eovt-or-ic-v0.2`.
Checked on 2026-11-25. Technical execution/resource verification is complete
for the recorded configuration. The benchmark-owned code/data license remains
an owner decision; this is not yet a fully licensed final release.

## Included and executable

- 60 fixed author-constructed layouts, 1,800 STT episodes, 630 OR and IC events.
- Fixed identity descriptions and one Same plus three distinct Similar trials.
- RGB Tracker PID, Oracle PID, their configurations and the custom environment.
- Current synchronized OR/IC collection and scoring as the default; historical
  reproduction only by explicit opt-in.
- Complete-path/pose IC, actual-loss/visibility OR and layout-cluster bootstrap.
- A scene-only resource archive and verified acquisition/installation instructions
  for externally provided humanoids, robot and detector.
- Original input examples and twelve selected OmTrackVLA first-person task videos.

See [installation](INSTALLATION.md), [audit](REPOSITORY_AUDIT.md),
`configs/environment_validated.json` and `VALIDATION_REPORT.json`.
Fresh-environment checks include actual GPU rollouts, not only CLI help.

## Preserved historical material

Prior numerical baseline aggregates are separately labeled in
[historical reference results](HISTORICAL_REFERENCE_RESULTS.md), unchanged under
their original evaluator. They are not current OR/IC measurements. The selected
0.5x video assets and their evidence remain tied to their immutable source tag
`v0.2.4-videos.20261125`; later source changes do not rewrite archived hashes.

## Publication scope

No learned-model implementation/weights or raw baseline result population is
published. Humanoid, robot and detector binaries are not rehosted. Only the
author-constructed scene resource archive is hosted separately from Git.
The humanoid ZIP's 500 required actor files and the official detector weights
were downloaded and verified; the official robot is converted explicitly to
the fixed experiment form with all 25 output hashes verified.

Project-attributed source omits private paths and credentials. Existing
third-party notices remain applicable. Platform copies/caches outside this
repository are outside the scope of a repository update.

## Remaining decision and research scope

The owner must select licenses for benchmark-owned code, scenes and metadata.
Public access does not supply these permissions; the current root notice grants
no new blanket license. Third-party terms cannot be replaced by that decision.

Current thresholds are initial declared settings, not universally optimized
constants. Full current-protocol baseline population results, independent human
IC validation and broad parameter robustness are not claimed. The benchmark is
intended for capability diagnosis under a specified protocol, not universal
model ranking. These limits are separate from the completed installation,
interface and selected real-run verification.
