# Repository release audit — 2026-11-25

Source candidate: `0.2.6-pre.20261125`.
Technical checks have passed. A final reusable code/data release still requires
the owner's license selection; public access alone does not supply that license.

## Canonical interface

- **EOVT-Bench**; **STT**, Single-Target Tracking; **OR**, Post-Occlusion Target
  Reacquisition; **IC**, Post-Occlusion Identity Consistency.
- Road, Indoor and Industrial: 20 layouts each, 1,800 STT episodes.
- OR/IC: 630 events from 558 source episodes, spanning 60 layouts.
- IC: exactly one Same and three distinct Similar trials per event; every
  candidate matches the original person's fixed published top-three list.
- Effective action mode: `closed_loop_model_actions_executed`. Historical
  action/description fields remain only under explicit `legacy_*` provenance.
- OR scores actual runtime loss, verified visibility opportunities and stable
  following. IC qualifies Same before complete-path/pose comparison. OTPR
  does not determine current binary outcomes. Thresholds are unchanged.

## Issues corrected

| Finding | Release correction |
| --- | --- |
| Old names, descriptions and metadata versions could imply obsolete tasks | Canonical names and current descriptions; historical fields explicitly separated, geometry and identities preserved |
| Historical facing/distance summaries could be confused with current OR/IC | Current synchronized collection/scoring is now the default for both baselines; legacy execution/aggregation require explicit flags |
| Baselines could not generate current OR/IC evidence | Record initialization and every true step, poses, simulation time, actions, activation and termination; OR adds real masks and exact full-target projections |
| Auxiliary JSON could enter result statistics or stale evidence could be resumed | Exclude evidence attempts from aggregation; validate execution fingerprint and evidence SHA-256 for resume |
| Arbitrary event IDs could become bootstrap clusters | Preserve explicit layout context and reject bootstrap without actual layout evidence |
| Historical result tables were prominent in current instructions | Move unchanged historical values to a separately labeled archive |
| Fixed scenes had no standalone delivery | Provide a scene-only archive: 60 layouts, 1,860 files, pinned archive/file checksums and installer |
| Humanoid link had not been checked against the experiment | Acquire the actual ZIP and verify all 500 required actor files; provide selective installation preserving repository metadata |
| Official robot download did not exactly reproduce the experiment | Pin official source hashes/revision; reproduce eight arm-visual omissions and text line endings; all 25 converted files match |
| Detector compatibility had not been verified | Download official YOLO11x and verify the exact pinned SHA-256 |
| Environment description was only an observed snapshot | Create an independent conda environment, install declared dependencies, run pip check, all tests and real simulator rollouts |
| Inventory/citation/version metadata and links were inconsistent | Synchronize source metadata and checksum inventory; check public links and release attachment scope |

## Verification evidence

- 49 tests: 13 baseline/data-contract and 36 evaluator/resource/interface cases.
- Independent current CLI rescoring and aggregation of nine baseline smoke
  events, including Same exclusion/eligibility, positive/negative Similar and
  actual-loss/no-loss OR branches. These are interface tests, not performance
  estimates; no raw baseline results are published.
- Empty-directory installation and SHA-256 verification of 2,385 resource files:
  1,860 scene, 500 humanoid and 25 prepared robot files.
- Fresh Python 3.9.19 / Habitat-Sim 0.3.3 / PyTorch 2.4.0+cu118 environment:
  pip check, full test entrypoint, both STT methods, current Oracle OR and a
  complete 1+3 IC event. Current OR/IC were independently rescored again there.
- Official wheel caches were reused; an existing environment's site-packages
  were not. Fixed installed assets were used for these GPU checks; resource
  installation was verified separately. Hardware coverage is the recorded
  Linux/WSL2 configuration, not every possible driver/system.
- Compressed metadata, source syntax/JSON, naming, credentials/private-path
  patterns, reachable Git history, source inventory and release attachment
  scope are checked. Pattern checks do not prove that every upstream function
  has been exercised.

The twelve main 0.5x demonstration videos and their archived evidence remain
unchanged. Their exact scorer-byte manifest is pinned to
`v0.2.4-videos.20261125`, not silently replaced by later source changes.

## Release boundary and owner decision

The final license for benchmark-owned code, scenes and metadata has not been
selected. `LICENSE` currently grants no new license. This is an unresolved
release requirement, not a claim of an already completed final release.
Third-party assets retain their own conditions and are acquired separately.
The standalone scene archive does not include humanoids, robot or detector
weights. No learned-model implementation/weights or baseline result population
is included in Git or resource attachments.

The current numerical settings are declared initial operational rules.
Twenty frozen IC development pairs establish code regression only; independent
human validation and universal threshold robustness are not claimed. Historical
population tables are not new-protocol measurements. These scientific limits
remain explicit without substituting for executable installation verification.

## Repeatable checks

```bash
python scripts/package_inventory.py
python scripts/check_resources.py --group metadata
bash baselines/scripts/test.sh
```

See [installation](INSTALLATION.md), [protocol](../evaluation/PROTOCOL.md) and
`VALIDATION_REPORT.json`. Refresh the tracked source inventory only after staging
intended files, with `python scripts/package_inventory.py --write`.
