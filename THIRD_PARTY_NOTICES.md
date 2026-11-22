# Third-party components and external resource policy

The repository is a research preview. The root `LICENSE`
does not grant a blanket code/data license.

## Components retained with notices

- Modified Habitat-Lab/custom task files retain copyright headers. The
  upstream v0.3.1 MIT notice is preserved in
  `licenses/Habitat-Lab-v0.3.1-LICENSE` and
  `evaluation/runtime/habitat-lab/LICENSE`. It does not license unrelated
  assets or establish ownership of custom modifications.
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
Simulation binary resources are excluded from Git; existing local copies are
not deleted. See `docs/THIRD_PARTY_RESOURCES.md` for official acquisition
routes, destinations, permission steps and compatibility checks.

- Humanoid meshes, model parameters, textures and motions require provenance
  at the actual file/provider level. SMPL-X model and Body terms differ; a
  filename containing `smplx` establishes neither origin nor permission.
- The benchmark author confirmed on 2026-11-21 that all Road/Route, Indoor and
  Industrial scenes were constructed by the author. The scenes are recorded
  as author-constructed benchmark data, rather than an unidentified third-party
  scene collection. The final scene-data license remains the owner's choice.
- Humanoid acquisition is through the author-supplied
  [humanoids.zip](https://drive.google.com/file/d/1aE_wyvPqvOuVmF8px2vTO3trr70DKf1l/view?pli=1).
  The viewer is accessible; archive file identity has not yet been verified.
  A download link is not a new resource license grant.
- Spot assets and YOLO11x weights are obtained separately under upstream terms.
  Their expected experiment files remain pinned by checksum.
- Fixed IDs, language descriptions and Similar assignments remain repository
  metadata; the asset inventory is not a license grant.

The owner still needs to select the license for benchmark-owned code/data.
Externalizing files does not automatically clear embedded or converted
third-party content. This policy does not change repository visibility.
