# GLB Reference Branch

Load only when a GLB is supplied as a reconstruction baseline. Exporting a newly
generated concept-image model uses `blender-handoff.md` instead. Package paths
below resolve from the staged skill root.

When the user supplies a GLB as an intermediate reference, the browser-rendered GLB is the
structural and visual baseline for an independently authored procedural factory. The raw GLB is
never pixel evidence and its topology/materials are never copied into the factory. Before any
factory edit — full contract in `grimoire/build/python_threejs_render_bridge.md`, machine-readable
schema in `docs/specs/render-profile.v2.schema.json` (+ example; fail-closed validation):

1. `forge/stage1_intake/probe_glb.py` first. A merged one-node/one-mesh asset is `insufficient`
   for semantic labels; request a multipart GLB or a browser semantic-ID pass before claiming
   exact regions.
2. Author ONE shared `render-profile.v2` (`forge/stage4_review/validate_render_profile.py`) used by
   both the GLB and procedural routes. Region IDs are subject-specific, never inherited from the
   example profile; declare the required set in `extensions.requiredSemanticRegions` so omission is
   a hard validation error.
3. Capture six passes per admitted view (`beauty`, `alpha-silhouette`, `semantic-id`, `depth`,
   `normal`, `roughness-material-id`); score with `forge/stage4_review/compare_region_passes.py`.
   Missing semantic-ID data blocks per-region confidence rather than falling back to whole-image
   scores.
4. Use region-specific continuous geometry — never replace a face/head volume, cloth shell, or tail
   with floating primitives when the region's silhouette requires a continuous surface.
5. Run ONE correction group per loop, in order: `camera → silhouette → face → clothing → accessory
   → materials → lighting`; recapture the full pass set after each group and record the changed
   group, hashes and score. Never combine groups when diagnosing improvement.
