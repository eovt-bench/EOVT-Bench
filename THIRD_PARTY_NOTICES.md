# Third-party components and external resource policy

Benchmark-owned code uses MIT (`LICENSE`); benchmark-owned scenes, task data
and documentation use CC BY 4.0 (`LICENSE-DATA`). The owner authorized this
split on 2026-11-25. See `docs/LICENSING.md` for exact scope.
Neither license is a blanket grant for third-party resources.

## Components retained with notices

- Modified Habitat-Lab/custom task files retain copyright headers. The
  upstream v0.3.1 MIT notice is preserved in
  `licenses/Habitat-Lab-v0.3.1-LICENSE` and
  `evaluation/runtime/habitat-lab/LICENSE`. It does not license unrelated
  assets or establish ownership of custom modifications.
- The Habitat-Lab/Hydra documentation illustration in `docs/images/` is an
  unmodified upstream v0.3.1 file. Its source and checksum are recorded in
  `docs/images/README.md`; the existing Habitat-Lab MIT notice applies.
  It is not included in the benchmark-owned CC BY 4.0 grant.
- The installed Ultralytics package notice is preserved under
  `evaluation/third_party_licenses/ultralytics/`. Users must comply with the
  terms for their code/weight usage; retaining a notice alone does not
  establish compliance.
- `licenses/Spot-assets-LICENSE.txt` preserves the existing robot attribution
  and upstream redistribution statement. This package does not extend it
  into a new unrestricted permission.

## Resources acquired separately

The mixed scene/humanoid/robot/detector asset archive and its multipart
attachments have been withdrawn from the benchmark Release.
Binary resources are excluded from Git. A separate author-constructed scene
archive is available; it contains no actors, robot or detector files. Existing local copies are
not deleted. See `docs/THIRD_PARTY_RESOURCES.md` for official acquisition
routes, destinations, permission steps and compatibility checks.

- Humanoid meshes, model parameters, textures and motions require provenance
  at the actual file/provider level. SMPL-X model and Body terms differ; a
  filename containing `smplx` establishes neither origin nor permission.
- The benchmark author confirmed on 2026-11-21 that all Road, Indoor and
  Industrial scenes were constructed by the author. The scenes are recorded
  as author-constructed benchmark data, rather than an unidentified third-party
  scene collection. The owner licenses the benchmark-owned scene data under
  CC BY 4.0; original benchmark-owned helper scripts use MIT.
- Humanoid acquisition is through the author-supplied
  [humanoids.zip](https://drive.google.com/file/d/1aE_wyvPqvOuVmF8px2vTO3trr70DKf1l/view?pli=1).
  All 500 required actor files in the acquired archive matched the pinned
  inventory on 2026-11-25; the archive is not rehosted here.
  A download link is not a new resource license grant.
- Spot assets and YOLO11x weights are obtained separately under upstream terms.
  Their expected experiment files remain pinned by checksum.
- Fixed IDs, language descriptions and Similar assignments remain repository
  metadata; the asset inventory is not a license grant.

Externalizing files does not automatically clear embedded or converted
third-party content. This policy does not change repository visibility.
