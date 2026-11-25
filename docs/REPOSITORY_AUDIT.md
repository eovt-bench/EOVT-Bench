# Repository audit — 2026-11-25

Source version: `0.2.5-pre.20261125`. This is an audited research preview,
not a claim of a complete clean-machine benchmark installation.

## Current names and numerical rules

- Benchmark: **EOVT-Bench**.
- Tasks: **STT**, Single-Target Tracking; **OR**, Post-Occlusion Target
  Reacquisition; **IC**, Post-Occlusion Identity Consistency.
- Scene categories: **Road**, **Indoor**, **Industrial**.
- The fixed IC metadata contains 630 events from 558 source episodes,
  spanning 60 layouts. Every event has 1 Same and 3 distinct Similar trials.
  All three candidates match the original person's published top-three list.
- Effective OR/IC metadata uses `closed_loop_model_actions_executed`.
  `legacy_action_mode` is provenance, not an active instruction.
- Current OR uses actual loss, synchronized masks/projections and simulation
  time. Current IC qualifies Same geometrically and judges full trajectories
  and headings. OTPR is audit-only.

Numerical decision thresholds and behavior were not changed by this audit.
A Same collision already excluded the control; its inconsistent diagnostic
text is corrected. A passing offline regression is not independent human validation.

## Corrections in this source version

| Finding | Correction |
| --- | --- |
| Citation and package inventory lagged behind the source | Synchronize source/citation versions; rebuild the complete file inventory and SHA256SUMS |
| Introductory text implied that scene binaries were included | State explicitly that binaries are acquired separately and the standalone scene archive is not attached |
| Road was called Route in some descriptions | Use Road consistently in benchmark-owned documentation |
| Compressed event descriptions still referred to old identity decisions | Update canonical task names, descriptions and protocol fields; preserve annotation provenance under `legacy_*` / `reference_annotation_version` without changing geometry or actor assignments |
| Bundled upstream developer pages contained broken links or generic asset instructions | Fix local links and distinguish upstream examples from benchmark installation |
| Historical baseline online OR/IC metrics could run without an explicit choice | Reject default OR/IC startup; require `--legacy-online-metrics`, label outputs, and use `or_legacy` / `ic_legacy` directories |
| Aggregation could silently interpret historical fields as the default protocol | Reject historical OR/IC inputs unless `--allow-legacy` is supplied; expose input versions |
| Custom event IDs could be used as bootstrap clusters when layout evidence was absent | Preserve supplied layout context and reject bootstrap without layout evidence |
| The subset sensitivity tool implemented only historical metrics | Require explicit historical opt-in and reject current scorer results |
| A recorded Same collision could retain a success string despite failed qualification | Make the diagnostic label, failed check and explanation agree with the existing exclusion |
| Validation and old release descriptions retained private-access wording | Record current public access while preserving historical evidence and labels |

Historical reference tables remain labeled with their original evaluator.
They are not measurements under the new OR/IC rules. Versioned compatibility
modules and old releases remain available as historical material.

## Scope of verification

Checks cover tracked public files, compressed episode metadata, task and
candidate consistency, source inventory/checksums, automated tests, public
release descriptions and attachment inventories, and selected numerical
demonstration evidence. Local installed assets are distinct from tracked
public files. Known private-path and credential patterns are screened;
such screening is not proof that arbitrary sensitive content is impossible.

The current 0.5x video release is `v0.2.4-videos.20261125`.
Its immutable numerical evidence and scorer byte manifest refer to that
source tag. The audit improves entry points; it does not replace archive
hashes or claim that every archived file is byte-identical to the latest
branch. Earlier video releases are explicitly superseded.

## Remaining work

| Item | Actual status |
| --- | --- |
| Baseline online v0.2 OR/IC collection | Incomplete. Historical summaries do not provide the full synchronized evidence required by current scoring |
| Baseline population results under v0.2 | Not rerun; README OR/IC tables are historical |
| Standalone fixed scene archive | Not attached; Git contains definitions and metadata, not scene geometry |
| Humanoid acquisition archive | Link documented; internal archive compatibility has not been verified |
| Clean-machine simulator installation | Not verified. Recorded dependency versions are not a verified lockfile |
| Current-protocol threshold/window/sampling sensitivity | Not fully validated; the historical subset tool does not establish current robustness |
| Independent human validation of current IC labels | Not completed; frozen development-case agreement is regression evidence only |
| Complete-package code/data license | Not granted by the root preparation notice; existing third-party terms still apply |

These limitations must remain visible in release and paper claims. Public
access alone does not resolve them. No learned-model implementation or
weights, raw baseline result population, or mixed simulation-asset archive is
added by this audit.

## Repeatable checks

```bash
python scripts/package_inventory.py
python scripts/check_resources.py --group metadata
python -m unittest discover -s evaluation/tests -v
```

For tests importing the baseline package, set `PYTHONPATH=baselines:evaluation`
on Linux. With matching local simulation assets installed, the broader
`bash baselines/scripts/test.sh` also checks episode-resource references.
Maintainers can stage intended public source files and run
`python scripts/package_inventory.py --write` to refresh the inventory.
This command hashes tracked source only; it does not include ignored assets.
