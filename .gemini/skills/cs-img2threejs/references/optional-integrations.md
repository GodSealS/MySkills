# Optional Plugins and Runtime Adapters

Load the applicable section only when a plugin serves the task or an optional
adapter is requested/needed. Package paths resolve from the staged skill root.

## Domain plugins

A domain plugin makes a run exact where this pipeline would otherwise infer. It contributes its own
checklist steps and gates, and publishes a `spec-augmentation.json` that this pipeline pulls at
`spec-authoring`. With no plugin serving the item, nothing here changes: author the skeleton and
infer the shape from the reference, as for any other object.

- The steps a plugin contributes appear in the checklist with their own ids and resolved paths. Read
  what each step names -- a plugin ships its own contract, and it governs its own domain.
- A plugin may **raise** this pipeline's quality floors and can never lower one; the merge clamps.
- A plugin that does not serve an item publishes no augmentation. That is not an error and not a
  blocked run: it is the generic path, and the reconstruction proceeds by inference.
- This pipeline names no domain. If a rule is domain-specific, it lives in that domain's plugin.

### The img2 harness

Plugins are installed and managed by the `img2` harness
([img2threejs/img2](https://github.com/img2threejs/img2)), a separate dependency-free CLI (Node
launcher, Python core). This skill
never installs anything itself: when `state.py init` names a profile as unavailable, name the
`img2 add` command that installs it and stop — never vendor domain logic instead.

```bash
img2 add img2threejs/plugin-<id> --ref <tag>      # install a plugin at a tag (e.g. plugin-cs2)
img2 doctor                                       # what each host resolves: base-skill path + version, plugin gates
img2 capabilities --from-kind image --to-kind glb # which installed plugin serves an edge
```

Setup and the full CLI reference live in the README quick-start and the harness repo's docs.

## Domain review gates

- **A domain review contract** (ships with the serving plugin): its review tool consumes the manifest and
  versioned scene fixture, then blocks wrong family identity, missing projection coverage,
  painted-region mismatch, critical identity-detail failure, finish/material response failure,
  and degenerate orbit form. It records exactness tier, hidden-region confidence, per-region
  confidence, approximation notes, camera, environment hash, exposure, tone mapping, resolution,
  background, and renderer version. Which items a domain plugin templates is that plugin's business,
  stated in its own contract. An item it does not serve gets no augmentation, and the run proceeds on
  the generic path by inference rather than being blocked -- declining is not a failure.

## Fidelity adapters

Use only for an observed weak point: local SAM2 for thin/complex masks, MediaPipe
for character face/pose, Depth Anything V2 for weak front/back cues. Each
`forge/stage1_intake/run_vision_adapter.py` result needs provenance; monocular
depth is relative. Read `docs/integrations/reference_fidelity_tooling.md` before
using the adapter. Write proven scene changes back to spec/TypeScript and recapture.

## Python and Three.js render bridge

When Python is requested for rendering, use it as a deterministic job/evidence
layer around the browser Three.js runtime: camera manifests, hashes, readiness,
screenshots, masks, diagnostics and comparison packaging. The target browser
remains the renderer. Read `grimoire/build/python_threejs_render_bridge.md`.
An optional adapter does not replace the procedural factory without an approved
change to the task; external asset provenance and limitations remain explicit.
