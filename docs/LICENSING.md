# Licensing and attribution

The benchmark owner authorized this license split on 2026-11-25. It applies
to the benchmark-owned material listed below, including the fixed scene
archive identified by its SHA-256. It does not replace third-party terms.

| Material | License | Scope |
| --- | --- | --- |
| Benchmark-owned source code and executable configuration | [MIT](../LICENSE) | Baselines, evaluators, task/environment modifications owned by the benchmark author, utility scripts, tests, workflow and environment/control configuration |
| Benchmark-owned scenes and task data | [CC BY 4.0](../LICENSE-DATA) | The fixed scene geometry, textures and navigation data; episodes, target paths, event annotations, appearance descriptions, Similar assignments, inventories and input/output examples |
| Benchmark-owned documentation and annotations | [CC BY 4.0](../LICENSE-DATA) | README files, protocol descriptions, tables and original case annotations |
| Third-party code, assets and weights | Original applicable terms | Existing notices and exclusions in [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md) take precedence for those components |

This is a per-component split, not a choice between MIT and CC BY 4.0 for
every file. Code embedded in a scene or example package remains MIT when
owned by the benchmark author; non-code scene data remains CC BY 4.0.
Existing copyright headers and more specific third-party notices must be
preserved, including Habitat-Lab's MIT notice.

Both owner-selected licenses permit commercial use. MIT requires retention
of its copyright and permission notice. CC BY 4.0 requires appropriate
attribution, a license reference and an indication of changes. Refer to the
full license texts for their terms.

## Data attribution

Use the following attribution when redistributing benchmark-owned data:

> EOVT-Bench contributors (2026), EOVT-Bench. Source:
> https://github.com/eovt-bench/EOVT-Bench.
> Licensed under Creative Commons Attribution 4.0 International
> (https://creativecommons.org/licenses/by/4.0/).
> Indicate any changes made to the material.

`CITATION.cff` supplies a project citation. This attribution does not invent
paper authors, acceptance status or a DOI.

## Fixed scene archive

The CC BY 4.0 grant covers the benchmark-owned data in
`eovt-scenes-fixed-20261125.tar.gz`, SHA-256:

```text
843b51368a8632e330419c3d667d1807133680cf39d8ac02f214d2ce26a29ef2
```

The archive's 60 layouts and 1,860 files are unchanged. License and
attribution sidecars are supplied alongside the archive on the scene
Release; they do not alter its bytes or the fixed experiment checksums.
If redistributing the archive, retain the applicable license texts and this
attribution. Original helper scripts in the archive are covered by MIT.

## External resources and demonstrations

Humanoid meshes, model parameters, textures and motions, Spot robot assets,
Ultralytics code and detector weights retain their applicable original
terms. Download links and compatibility hashes are not new permissions.
The benchmark does not relicense these resources or grant rights in
third-party material depicted in rendered demonstrations. See the
[resource guide](THIRD_PARTY_RESOURCES.md) for acquisition instructions.

Scientific validation limits are separate from licensing: declaring an
open license does not claim universal thresholds, independently validated
identity labels or new population performance results.
