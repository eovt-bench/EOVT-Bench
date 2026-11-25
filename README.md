# EOVT-Bench

A Benchmark for Evaluating Occlusion Robustness in Embodied Visual Tracking.

[中文说明](README.zh-CN.md) · [Data fields](docs/DATA_FORMAT.md) ·
[Protocol](evaluation/PROTOCOL.md) · [Baselines](docs/BASELINES.md)
· [External resources](docs/THIRD_PARTY_RESOURCES.md)

Version **0.2.8**. This release contains fixed
episode/event metadata, environment configuration, two diagnostic baselines
and a shared evaluator. The fixed author-constructed scenes are distributed
as a separate checksum-pinned archive; humanoid, robot and detector resources
are acquired from their providers.
Users with the matching assets do not need to rebuild scenes or regenerate episodes.

The repository publishes the benchmark interface, diagnostic baselines,
versioned evaluator and selected OmTrackVLA qualitative demonstrations.
Model weights and learned-model implementations are not included.

| Task | Data | Headline metrics |
| --- | --- | --- |
| STT: Single-Target Tracking | 1,800 episodes | SR / TR / CR |
| OR: Post-Occlusion Target Reacquisition | 630 events from 558 source episodes | RSR / VOR / CRR / MRS |
| IC: Post-Occlusion Identity Consistency | 630 events, each 1 Same + 3 distinct Similar | Same eligibility / effective following ratio |

The 60 layouts comprise 20 each of Road (`road`), Indoor and Industrial.
All scenes were constructed by the benchmark author.
Reference geometry labels are distinct from a policy's runtime visibility.

## Package

```text
episodes/             Fixed episodes, trajectories, events and IC assignments
configs/              Simulator YAML, baseline JSON and observed environment
assets/               Fixed appearance metadata and asset checksums
baselines/            RGB Tracker PID and Oracle PID
evaluation/           Shared scorer and modified environment driver
examples/             Matched real Industrial input episode records
scripts/              Verified resource download
docs/                 Fields, permissions, protocol and release status
```

Code and compact metadata live in Git. Simulation assets must be obtained
separately. Only author-constructed scenes are hosted as a resource Release.
Historical baseline aggregate values are archived; raw baseline results are not distributed.
The three learned model implementations and their weights are not included.

## Download

```bash
python scripts/check_resources.py --group metadata
```

Install the standalone scene archive:

```bash
python scripts/download_resources.py --kind scenes
```

Before simulation, follow [external resource acquisition](docs/THIRD_PARTY_RESOURCES.md):
resource links, destinations and checksums are provided. The benchmark author
supplies the constructed scenes; the humanoid download is
[humanoids.zip](https://drive.google.com/file/d/1aE_wyvPqvOuVmF8px2vTO3trr70DKf1l/view?pli=1).
The downloaded archive was checked on 2026-11-25: all 500 required actor
files match the pinned inventory. Install with
`python scripts/install_humanoids.py --archive /path/to/humanoids.zip`. Generic assets cannot replace the fixed experiment files.
Run `python scripts/check_resources.py` and
`python evaluation/validate_package.py` after installing matching files.
The former mixed asset download has been withdrawn. Existing lawfully held
local archives retain an offline installation path. See [downloads](docs/DOWNLOADS.md).

## Environment and running

Simulation uses Linux/WSL2 with NVIDIA/EGL. Observed versions include Python
3.9.19, Habitat-Sim 0.3.3 and PyTorch 2.4.0+cu118. The launcher imports the
bundled modified Habitat-Lab/custom task; stock Habitat-Lab is insufficient.

```bash
conda env create -f environment.yml
conda activate eovt-bench
python -m pip install -r requirements.txt
bash baselines/scripts/test.sh

python run_baseline.py --variant oracle_pid --task stt --gpu 0 --max-episodes 1
python run_baseline.py --variant rgb_tracker_pid --task stt --gpu 0 --resume
```

All three tasks use the current protocol by default. OR/IC execution writes
synchronized evidence and scores it with the public v0.2 evaluator:

```bash
python run_baseline.py --variant rgb_tracker_pid --task or --gpu 0 --resume
python run_baseline.py --variant rgb_tracker_pid --task ic --gpu 0 --resume
bash baselines/scripts/run_all_tasks.sh oracle_pid 0
```

Use `--split-num 30 --split-id 0` for sharding. IC selects the frozen
appearance dataset and `_ic.json` configuration. Results stay inside
`baselines/outputs/`. Only valid final JSONs count for resume; auxiliary
`*_info.json` and broken JSON do not.

A newly created Linux/WSL2 conda environment was verified on 2026-11-25:
Habitat-Sim 0.3.3, the declared Python dependencies, `pip check`, 49 tests,
both STT baselines and current Oracle OR/IC simulator execution. Official
cached wheels were reused, not an existing environment's site-packages.
This is installation/interface validation, not a population rerun or a
universal driver guarantee. See [installation](docs/INSTALLATION.md) and
`configs/environment_validated.json`. Current OR/IC scoring requires NumPy;
aggregation uses the Python standard library.

## Evaluate

```bash
python evaluation/score_or_ic.py or frames.jsonl --output scored_or/event.json
python evaluation/score_or_ic.py ic ic_event.json --output scored_ic/event.json
python evaluation/aggregate_results.py scored_or --task or --bootstrap 2000
python evaluation/aggregate_results.py scored_ic --task ic --bootstrap 2000
python evaluation/aggregate_results.py baselines/outputs/rgb_tracker_pid/stt --task stt --bootstrap 2000
```

Current OR/IC outputs include an evidence path, evidence checksum, execution
fingerprint and evaluator version. Resume checks all four. Evidence attempts
are preserved separately and excluded from population aggregation. Use
`--episode-id EVENT_ID` to reproduce fixed cases; it can be repeated.
Historical scoring requires explicit `--legacy-online-metrics` and writes
`or_legacy` / `ic_legacy`; aggregation requires `--allow-legacy`.
Historical summaries alone cannot be converted to v0.2 without full evidence.

Intervals use layout-cluster bootstrap. The current OR scorer uses actual
runtime loss events as its denominator. The current IC scorer compares the
complete Similar trajectory and pose against Same and does not use OTPR for
the binary decision. Legacy SameSR/SwapSR/BIA and OTPR fields remain only for
compatibility and audit. See [exact semantics](evaluation/PROTOCOL.md) and the
versioned thresholds in `configs/evaluation/or_visibility_v0.2.json`.
Supply `layout` or `layout_id` for custom event IDs; bootstrap rejects missing
layout evidence rather than treating arbitrary events as independent layouts.

## Baseline input permissions

| Method | Perception | Control | Privileged policy input |
| --- | --- | --- | --- |
| RGB Tracker PID | YOLO person detection and appearance/motion association | Bounding-box PID | None; initializes from largest detection |
| Oracle PID | Target-specific simulator box/facing | Same PID implementation, frozen configuration | Original-target truth sensor |

Oracle PID is diagnostic, not a guaranteed upper bound.

## Version, citation and licensing

Read [release status](docs/RELEASE_STATUS.md), `VALIDATION_REPORT.json`,
`LICENSE`, and `THIRD_PARTY_NOTICES.md` for what is actually verified.
`CITATION.cff` provides a software citation without inventing paper authors,
acceptance, or a DOI.
Benchmark-owned code and executable configuration are licensed under
[MIT](LICENSE). Benchmark-owned scenes, episodes, event metadata and
documentation are licensed under [CC BY 4.0](LICENSE-DATA).
Both permit commercial use. See [license scope and attribution](docs/LICENSING.md).
Third-party code, humanoids, robot assets and detector weights retain their
original terms; these licenses do not replace resource-specific permissions.

## Historical reference results

Prior aggregate values retain their original scoring version on the
[historical reference page](docs/HISTORICAL_REFERENCE_RESULTS.md).
Current OR/IC population results have not been rerun; a smoke test is not a new benchmark score.

## Qualitative examples

Twelve current OmTrackVLA robot-camera demonstrations (OR/IC scored under v0.2) (STT/OR/IC: two successes and two failures each) are available with result JSONs and step trajectories. See the [case index and metric caveats](qualitative/omtrack_first_person/README.md).


Publication scope and attribution: [PUBLICATION](docs/PUBLICATION.md).
The [repository audit](docs/REPOSITORY_AUDIT.md) lists corrected inconsistencies
and the remaining execution and release limitations.
