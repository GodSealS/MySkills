# Material Evidence Branch

Read when material fidelity matters and a source image exists. Select the route
in [surface-routing.md](surface-routing.md) first. Package paths below resolve
from the staged skill root; actual script flags come from the installed help.

Analyze each material's **finish**, then extract reference PBR evidence per crop.
Verify each crop belongs to its assigned part:

   - `forge/stage1_intake/analyze_texture.py <crop> --spec spec.json --material-id <id> --in-place`
     classifies the finish, extracts the gradient palette, and writes doc-grounded
     MeshPhysicalMaterial scalars onto the material. Recipes + Three.js texture/PBR rules:
     `grimoire/build/threejs_texture_reference.md`. Rule of thumb: **solid albedo for flat paint,
     real reference crop for patterned finishes**.
   - `forge/stage1_intake/extract_pbr_evidence.py <crop> --out-dir <dir> --material-id <id> --target-threshold 0.7`.
     Confidence < 0.7 is a stop/refine-input signal, not a pass. It is inference, not inverse rendering.
   - For multiple named regions: `forge/stage1_intake/material_region_analysis.py --manifest regions.json --out-dir material-evidence --out material-analysis.json`,
     resolve each assignment from `docs/materials/material-reference.json`, wire it in with
     `forge/stage2_spec/apply_material_analysis.py`.
   - Emit the controlled material camera/crop contract (`forge/stage4_review/material_views.py`),
     compare visible-footprint crops (`material_comparator.py`), apply only bounded material-scoped
     corrections (`material_feedback.py`), and record the blocking result (`material_gate.py`).
