# Character, Hair and Animation Branch

Load for `character`/`hybrid` subjects, hair, or a character rig. Package paths in
backticks resolve from the staged skill root. These rules add to the common gates.

## Intake and construction

Use the registered `character` profile for static character work. If the rig must
move, select the installed `animated-character` profile; an unavailable provider
is a blocker, not permission to omit animation gates. Complete plugin intake first.
Extract landmarks with `forge/stage1_intake/extract_landmarks.py`, fill
`preSpecAssessment.anatomy`, and read `grimoire/character/reconstruction.md`.
For maximum likeness also read `grimoire/character/likeness_maximization.md`;
its projection work follows [surface routing and actual bake evidence](surface-routing.md).

Build in this order, reading the contract at each stage:

1. Parts: `grimoire/character/structure_decomposition.md`.
2. Head: `grimoire/character/head_construction.md`.
3. Hair when present: `grimoire/character/stylized_hair_threejs.md` and
   `grimoire/character/threejs_hair_parameter_contract.json`. Lock topology only
   after silhouette review; material tuning cannot repair wrong lock topology.

Feature review targets include anatomy proportion, face landmarks, pose silhouette
and outfit/palette. A requested reference-free humanoid uses
`forge/stage2_spec/humanoid_proportions.py --style-heads 8 --in-place` with the spec
argument; it records `anatomy.source: canon-table` and refuses a spec naming an image.
This optional task is not evidence of matching a supplied concept image.

## Left and right

A left/right pair is a **reflection**, never a rotation: negate the lateral axis and nothing else,
`(x, y, z) → (-x, y, z)`. With `forward: +Z`, Y up and a right-handed frame, the character's own
left is **+X**. The convention lives as code in `forge/_shared/chirality.py`
(`CHARACTER_LEFT_SIGN`), with two different gates for the two defects that shipped from getting it
wrong: `validate_chirality` catches a rotation-mistaken-for-reflection at spec time, and
`medial_lateral_bias` vs a reference catches a pair that is wrong the same way on both sides.
Reflecting also inverts triangle winding — flip it back on the mirrored side or `flatShading`
lights the limb as though lit from behind. Full write-up with the measured defects:
`grimoire/scripts.md` ("Left and right").

## Hair

Hair has its own subsystem because it has failure modes no other gate can see. Full contract,
measurements and non-goals: `docs/HAIR_PIPELINE.md`. The hard rules:

- Roots bind to the scalp as `(u, v)`, never absolute positions (hard validation error).
- `standProud` is enforced by the generator, not advisory.
- `scalp_exposure.py` is a HARD gate on geometry before any render; a coverage shortfall never on
  its own authorises widening the masses.
- Default representation tier is `shell`, not locks; strand impression comes from faceting and
  material (`hair.human.code-only`); this hair representation does not generate alpha cards.
- `plane-card` is rejected by this procedural hair contract. General surface projection
  does not add an alpha-card hair generator; a different hair representation requires owner approval.
- Hair is rigidly parented, never smooth-skinned (the geodesic field runs through the skull).

## Character gates

- **Scalp exposure (HARD, hair subjects, before any render)**:
  `forge/stage4_review/scalp_exposure.py` finds bald patches geometrically, on points, so it needs no
  browser and no capture. Exposure above `--hard-max` is always a failure. It counts only hair
  OUTSIDE the skull — a nearest-neighbour test passes the failing build, because those vertices were
  still nearby, merely sunk below the surface. Silhouette IoU cannot see a bald crown (it is
  interior) and interior difference cannot separate it from a colour shift.
- **Hair gate (soft, hair subjects)**: `forge/stage4_review/hair_gate.py` compares banded coverage,
  hairline offset and highlight-band position. Its verdict is subordinate to `scalp_exposure`. **A
  coverage shortfall never authorises widening the masses on its own** — doing so took closure from
  42.2% to 40.9%, worse on all six views, with crown exposure up 14.9 points on the worst view,
  because the widened masses slid off the skull. Full record: `docs/HAIR_PIPELINE.md`.
- **Procedural rig contract**: for humanoid/character builds, validate the authored
  `joints`/`parents`/`names`/`matrix_local`/packed skin payload with
  `forge/stage5_rig/validate_rig_payload.py` before binding `THREE.Skeleton`. The gate proves
  structural payload integrity only; pose stress, dynamic bounds, readable screenshots, and
  visual likeness remain separate gates. Payload ownership and non-goals:
  `grimoire/readiness/procedural_rigging_contract.md`.

- **Character track**: when `primaryDomain` is `character`/`hybrid` (or `--character`), the spec
  author auto-builds a stylized humanoid template (head/neck/torso/arms + hair, glasses,
  headphones, face features), flattened to world space under a hidden root, with per-part
  character materials and character build passes (`proportion-lock`, `feature-placement`).
  strict-quality requires a filled `anatomy` block (head-units, proportions, face landmarks) and
  character feature targets. Suitability routing for humans: `grimoire/intake/validation_rubric.md`
  (stylized vs maximum-likeness). Stylized bust, not a face-copy; refine positions per reference.

## Moving rigs and runtime

Read `grimoire/readiness/animation_contract.md` when a rig must move. Follow the
profile's Stage R order: repair mesh, freeze it, bind additively, verify parity and
sample actual motion. Missing gate input is unevaluated, not a pass.

Use `grimoire/readiness/standard_character_pipeline.md` for character work. Beta owns the
strict sculpt/build/review gates; alpha owns deterministic camera manifests, browser screenshot
evidence and UniRig-shaped rig validation. CharacterGen, Tripo, VRM and other neural/asset
systems are opt-in adapters with source, checkpoint, license, coordinate conversion and output
hashes. They never silently replace the procedural TypeScript factory. Image-to-mesh systems emit a
static mesh with no skeleton, so their output is never animation-ready however good it looks.
Executable entry points: `forge/stage4_review/render_bridge.py` and
`scripts/capture_threejs_playwright.py` (`init → browser capture → validate → diagnose`; capture
must operate on the real showcase/browser route and leave readable PNGs in the workspace).
