# Install and run EOVT-Bench

The supported simulator platform is Linux with NVIDIA/EGL, including the
validated Ubuntu 22.04 WSL2 configuration. No learned-model code or weights
are required for either diagnostic baseline.

## 1. Prepare the fixed resources

From the repository root:

```bash
python scripts/check_resources.py --group metadata
python scripts/download_resources.py --kind scenes
```

Download the separate humanoid ZIP using the author-supplied address in
[resource instructions](THIRD_PARTY_RESOURCES.md), then install:

```bash
python scripts/install_humanoids.py --archive /path/to/humanoids.zip
python scripts/prepare_spot.py --download --source .downloads/spot-official
```

The Spot command obtains the pinned official files, applies the documented
eight arm-visual omissions, and checks the exact experiment hashes. It
preserves the upstream notices. The humanoid command copies only the 500
fixed actor files and preserves repository identity/candidate metadata.

RGB Tracker PID additionally requires the official YOLO11x weight file
described in the resource guide, at `assets/detectors/yolo11x.pt`. Oracle PID
does not require that file.

```bash
python scripts/check_resources.py --group scenes
python scripts/check_resources.py --group humanoids
python scripts/check_resources.py --group robot
# RGB baseline only:
python scripts/check_resources.py --group detector
```

The standalone scene archive contains only author-constructed scenes.
Humanoids, robot and detector weights are acquired directly from their
providers, under the applicable terms.

## 2. Create the simulator environment

```bash
conda env create -f environment.yml
conda activate eovt-bench
python -m pip install -r requirements.txt
python -m pip check
bash baselines/scripts/test.sh
```

The environment contains Habitat-Sim 0.3.3. The launcher uses the bundled
modified Habitat-Lab/custom task; installing stock Habitat-Lab is insufficient.
`configs/environment_observed.json` records the original server snapshot.
`configs/environment_validated.json` records the independent fresh-prefix
installation verification, including the actual package versions and scope.

## 3. Run the current tasks

```bash
python run_baseline.py --variant oracle_pid --task stt --gpu 0 --max-episodes 1
python run_baseline.py --variant oracle_pid --task or --gpu 0 --resume
python run_baseline.py --variant rgb_tracker_pid --task ic --gpu 0 --resume
```

Use `--split-num N --split-id I` for sharding, `--episode-id ID` for a fixed
episode/event, and `--seed` for the recorded trial seed. All three current
tasks are the default; historical OR/IC requires `--legacy-online-metrics`.
On the validated WSL2 Mesa/D3D12 renderer, `--egl-device -1` is required.
Native NVIDIA/EGL normally uses the default device selection.

Outputs remain under `baselines/outputs/<method>/<task>/`. Current OR/IC
results include complete evidence, its SHA-256, the execution fingerprint
and scorer version. Resume validates these before skipping an event.

## 4. Rescore and aggregate

```bash
python evaluation/score_or_ic.py or /path/to/frames.jsonl --output /path/to/scored_or/event.json
python evaluation/score_or_ic.py ic /path/to/ic_event.json --output /path/to/scored_ic/event.json
python evaluation/aggregate_results.py baselines/outputs/oracle_pid/or --task or --bootstrap 2000
python evaluation/aggregate_results.py baselines/outputs/rgb_tracker_pid/ic --task ic --bootstrap 2000
```

Evidence paths are stored in each result. Auxiliary evidence directories are
excluded from aggregation. Same exclusion, observed failure and missing
evidence are distinct cases; see [protocol](../evaluation/PROTOCOL.md).
Single-case smoke checks verify execution, not population performance.
