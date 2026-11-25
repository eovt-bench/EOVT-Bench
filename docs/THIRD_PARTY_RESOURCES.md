# Benchmark scenes and external resources

[中文说明](THIRD_PARTY_RESOURCES.zh-CN.md)

Resource policy version: `external-resources-20261121`. Official pages checked
on 2026-11-21. The repository provides benchmark code, configuration, episodes,
fixed identity metadata and checksums. It does not redistribute the mixed
simulation asset archive. Users obtain external files from their providers,
under the terms applicable to their use.

## Resource inventory

| Resource | Destination relative to repository | Acquisition |
| --- | --- | --- |
| Exact EOVT scenes (60 layouts) | `scenes/layout_instances/` | All scenes were constructed by the benchmark author, who supplies the fixed layout pack. No third-party scene download is needed; a standalone scene download is not yet attached to this Release. |
| Custom humanoids and motions | `assets/humanoids/humanoid_data/` | Obtain [humanoids.zip](https://drive.google.com/file/d/1aE_wyvPqvOuVmF8px2vTO3trr70DKf1l/view?pli=1) from the address supplied by the benchmark author; see verification below. |
| Spot robot | `assets/robots/hab_spot_arm/` | Use Habitat's official resource route below, retain notices and check exact compatibility. |
| YOLO11x weights (RGB baseline only) | `assets/detectors/yolo11x.pt` | Download separately from the official Ultralytics release under the applicable terms. |
| Fixed IDs, descriptions, Similar candidates | `assets/humanoids/*.json` | Included in Git. No avatar meshes or motion/model parameters are included. |
| Baseline aggregate values | README | Numeric tables and confidence intervals only; no raw baseline result download. |

`assets/manifest.json` pins the **actual experiment files**. Resource presence
or a matching hash establishes compatibility, not permission to redistribute.
The machine-readable policy is `assets/resource_policy.json`.

## Author-constructed scenes

On 2026-11-21 the benchmark author confirmed that all Road, Indoor and
Industrial scenes were constructed by the author. The 60 layouts are benchmark
data supplied by the author, rather than an unidentified third-party scene
collection. Keep their directory names and matching episode references.
This clarification changes neither layouts nor episodes. A standalone scene
archive is not yet attached to this preparation Release; existing experiment
copies are preserved locally.

## Humanoid download and installation

The benchmark author supplied this acquisition address on 2026-11-21:

[Download humanoids.zip from Google Drive](https://drive.google.com/file/d/1aE_wyvPqvOuVmF8px2vTO3trr70DKf1l/view?pli=1)

The viewer returned HTTP 200 and identifies the file as `humanoids.zip`.
This update did not download the archive or compare its contents with the
frozen experiment files. This is an author-supplied acquisition address,
not a claim that Google Drive is the original model licensor.

1. Download and extract the archive to a temporary directory; retain its notices.
2. Locate the actor-data tree. Examples of expected paths are
   `male_4/male_4.urdf` and `male_4/male_4_motion_data_smplx.pkl`.
   Do not assume the ZIP root already matches the installation destination.
3. Place actor directories under `assets/humanoids/humanoid_data/`, preserving
   URDFs, referenced meshes/textures and motions. Keep the repository's fixed
   `assets/humanoids/humanoid_infos.json`, `humanoid_descriptions.json` and
   `appearance_top3.json`; do not replace them with archive metadata.
4. Run `python scripts/check_resources.py --group humanoids`. Investigate any
   missing/mismatched files before running IC. A generic model download is not
   a substitute for the fixed experiment resource set.

For resources subject to SMPL-X terms, the [project website](https://smpl-x.is.tue.mpg.de/),
[model license](https://smpl-x.is.tue.mpg.de/modellicense.html) and
[Body license](https://smpl-x.is.tue.mpg.de/bodylicense.html) remain supplementary
references. They are not substitutes for the supplied humanoid archive.
Providing the acquisition link does not grant a new redistribution license.

## Spot

Habitat-Sim's [version 0.3.3 resource downloader](https://github.com/facebookresearch/habitat-sim/blob/v0.3.3/src_python/habitat_sim/utils/datasets_download.py)
defines `hab_spot_arm`, sourced from the official
[ai-habitat resource repository](https://huggingface.co/datasets/ai-habitat/hab_spot_arm).
In the compatible installed Habitat-Sim environment, the upstream command is:

```bash
python -m habitat_sim.utils.datasets_download \
  --uids hab_spot_arm --data-path /path/to/separate/habitat-data
```

This is an upstream acquisition command, not an installation verified by this
update. Read the upstream conditions and `licenses/Spot-assets-LICENSE.txt`;
then place the matching resource tree at `assets/robots/hab_spot_arm/`.
The existing notice records permission obtained by upstream authors; it is
not a newly issued unrestricted license from EOVT-Bench.
If the downloaded files differ from the manifest, stop and investigate;
do not edit the manifest merely to suppress the mismatch.

## Detector

Review [Ultralytics licensing](https://www.ultralytics.com/license) and the
[YOLO11 documentation](https://docs.ultralytics.com/models/yolo11/), then
obtain [`yolo11x.pt` from the official v8.3.0 asset release](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11x.pt).
The observed experiment file has:

```text
destination: assets/detectors/yolo11x.pt
bytes: 114636239
sha256: 7bc158aa95c0ebfdd87f70f01653c1131b93e92522dbe15c228bcd742e773a24
```

The official release lists a file of the same size; this update did not
redownload it to establish byte identity. Verify the checksum after obtaining
it. Oracle PID does not need the detector; RGB Tracker PID does.

## Validate, then run

```bash
python scripts/check_resources.py --group metadata
python scripts/check_resources.py --group robot
python scripts/check_resources.py --group humanoids
python scripts/check_resources.py --group scenes
python scripts/check_resources.py --group detector
python evaluation/validate_package.py
```

The checker only reads files. `--json` prints exact missing or mismatched paths;
`--presence-only` checks sizes without hashing and is not full validation.
Oracle runs need scenes, humanoids and robot resources; RGB runs additionally
need the detector. Use the author-constructed scene pack and supplied humanoid
download, then check compatibility rather than substituting different assets.

For existing users who already lawfully possess the frozen, complete local
archive, the installer retains an offline compatibility path:

```bash
python scripts/download_resources.py --kind assets --archive /path/to/existing/assets.tar.gz
```

This command checks the original archive and each file; it does not download
anything, grant a license or authorize sharing that archive.
The old multipart download route has been withdrawn.

## Publication boundary

Retain applicable notices for external components. The benchmark scenes are
author-constructed data, as confirmed by their author; their final data license
remains the benchmark owner's choice. Humanoids, robot resources and detector
weights are acquired separately rather than rehosted in the mixed archive.
