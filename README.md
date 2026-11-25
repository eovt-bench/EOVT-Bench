# EOVT-Bench

A Benchmark for Evaluating Occlusion Robustness in Embodied Visual Tracking.

[中文说明](README.zh-CN.md) · [Data fields](docs/DATA_FORMAT.md) ·
[Protocol](evaluation/PROTOCOL.md) · [Baselines](docs/BASELINES.md)
· [External resources](docs/THIRD_PARTY_RESOURCES.md)

Version **0.2.1-pre.20261125**. This research preview contains fixed
scenes/episodes, environment configuration, two diagnostic baselines and a
shared evaluator. Users do not need to rebuild scenes or regenerate episodes.

The repository publishes the benchmark interface, diagnostic baselines,
versioned evaluator and selected OmTrackVLA qualitative demonstrations.
Model weights and learned-model implementations are not included.

| Task | Data | Headline metrics |
| --- | --- | --- |
| STT: Single-Target Tracking | 1,800 episodes | SR / TR / CR |
| OR: Post-Occlusion Target Reacquisition | 630 events from 558 source episodes | RSR / VOR / CRR / MRS |
| IC: Post-Occlusion Identity Consistency | 630 events, each 1 Same + 3 distinct Similar | RFR / DSR |

The 60 layouts comprise 20 each of Route (`road`), Indoor and Industrial.
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
separately from their providers; they are not hosted as Release attachments.
Baseline aggregate values are reported below; raw baseline results are not distributed.
The three learned model implementations and their weights are not included.

## Download

```bash
python scripts/check_resources.py --group metadata
```

Before simulation, follow [external resource acquisition](docs/THIRD_PARTY_RESOURCES.md):
resource links, destinations and checksums are provided. The benchmark author
supplies the constructed scenes; the humanoid download is
[humanoids.zip](https://drive.google.com/file/d/1aE_wyvPqvOuVmF8px2vTO3trr70DKf1l/view?pli=1).
The viewer is accessible; the archive contents have not been compared with the
experiment inventory. Generic assets cannot replace the fixed experiment files.
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
python run_baseline.py --variant rgb_tracker_pid --task or --gpu 0 --resume
python run_baseline.py --variant rgb_tracker_pid --task ic --gpu 0 --resume
bash baselines/scripts/run_all_tasks.sh oracle_pid 0
```

Use `--split-num 30 --split-id 0` for sharding. IC selects the frozen
appearance dataset and `_ic.json` configuration. Results stay inside
`baselines/outputs/`. Only valid final JSONs count for resume; auxiliary
`*_info.json` and broken JSON do not.

The requirements file records observed versions, not a verified clean-install
lockfile. The original packaging audit did not run a GPU rollout. The subsequent selected local rollouts are documented in the qualitative examples; they do not establish a fresh installation or full benchmark rerun. Offline common
scoring uses the Python standard library; optional sensitivity and baseline
unit tests also require NumPy.

## Evaluate

```bash
python evaluation/aggregate_results.py baselines/outputs/rgb_tracker_pid/stt --task stt --bootstrap 2000
python evaluation/aggregate_results.py baselines/outputs/rgb_tracker_pid/or --task or --bootstrap 2000
python evaluation/aggregate_results.py baselines/outputs/rgb_tracker_pid/ic --task ic --bootstrap 2000
```

Intervals use layout-cluster bootstrap. The current OR scorer uses actual
runtime loss events as its denominator. The current IC scorer compares the
complete Similar trajectory and pose against Same and does not use OTPR for
the binary decision. Legacy SameSR/SwapSR/BIA and OTPR fields remain only for
compatibility and audit. See [exact semantics](evaluation/PROTOCOL.md) and the
versioned thresholds in `configs/evaluation/or_ic_initial_v0.1.json`.

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
The root preparation notice grants no blanket open-source/data license.
Access restrictions do not replace the resource-specific permissions and license notices.

## Baseline reference values

These are aggregate values from completed runs. Brackets give 95% layout-cluster bootstrap intervals (2,000 repetitions). Rates are percentages; MRS is in steps. This publication update does not rerun experiments or change the measured values. Per-episode baseline result JSONs, result-file inventories and result archives are not distributed in Git or Releases.

### STT

| Method | Episodes/events | SR | TR | CR |
| --- | --- | --- | --- | --- |
| RGB Tracker PID | 1800 | 49.28 [46.50, 52.06] | 69.31 [66.88, 71.60] | 0.00 [0.00, 0.00] |
| Oracle PID | 1800 | 42.28 [38.94, 45.39] | 65.74 [63.02, 68.30] | 0.00 [0.00, 0.00] |

### OR

| Method | Episodes/events | RSR | VOR | CRR | MRS |
| --- | --- | --- | --- | --- | --- |
| RGB Tracker PID | 630 | 31.43 [27.82, 35.33] | 72.54 [69.23, 75.94] | 43.33 [38.53, 48.28] | 4.50 [3.29, 5.89] |
| Oracle PID | 630 | 11.43 [8.62, 14.24] | 72.54 [69.69, 75.46] | 15.75 [11.85, 19.75] | 11.29 [9.66, 12.94] |

### IC

| Method | Valid Same | DSR eligible events | RFR | DSR |
| --- | --- | --- | --- | --- |
| RGB Tracker PID | 630 | 174 | 72.22 [68.97, 75.39] | 72.80 [65.15, 80.61] |
| Oracle PID | 629 | 130 | 79.17 [75.97, 82.38] | 61.79 [51.99, 71.78] |

**Version and interpretation.** The tables above preserve the previously
reported aggregate reference values and are labeled with their original
evaluator version. They are not silently recomputed under the new OR/IC
protocol. New runs must record the evaluator and protocol version alongside
their results. The protocol is diagnostic: it describes capability failure
modes and is not intended to establish a universal ranking of models.

## Qualitative examples

Twelve fresh OmTrackVLA robot-camera videos (STT/OR/IC: two successes and two failures each) are available with result JSONs and step trajectories. See the [case index and metric caveats](qualitative/omtrack_first_person/README.md).


Publication scope and attribution: [PUBLICATION](docs/PUBLICATION.md).
