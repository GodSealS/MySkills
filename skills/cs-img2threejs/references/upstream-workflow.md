# Reconstruction Workflow

This is the pack's common execution order, adapted from img2threejs. `SKILL.md`
owns invocation, installed paths and Blender delivery. Backtick package paths
resolve from the task-local staged skill root; outputs stay in the asset workspace.
Read applicable references when their stage is reached, not every branch up front.

## Branch selection

| Trigger | Required reference and loading point |
|---|---|
| Surface representation decision, `projection-route`, or reference-matched finish | [Surface routing](surface-routing.md), before spec/material implementation |
| Material fidelity with source crops | [Material evidence](material-workflow.md), at material analysis/wiring |
| Character/hybrid subject, hair or character rig | [Character workflow](character-workflow.md), at intake; load its part/head/hair references only when applicable |
| GLB supplied as reconstruction baseline | [GLB reference track](glb-reference-track.md), before factory edits |
| Participating domain plugin or optional neural/render adapter | Relevant section of [optional integrations](optional-integrations.md), before use |
| Final emission/provider steps or Blender delivery | [Export and state handoff](blender-handoff.md), after part coverage/action readiness |

A domain's registered steps and gates supplement the common order. Read the
contract each contributed step names before running it. Missing required plugins
or runtime tools are named blockers. An unserved generic object needs no plugin.

## Local state and stopping

Initialize once as shown in `SKILL.md`; resume and each correction start with
`forge/next.py --state .img2threejs/state.json [object-sculpt-spec.json]`.
The local state is the ordered checklist authority; the spec, renders and reports
are evidence. Exit 3 or `status=stopped` is a hard stop with a reported reason.

After completing the current step, persist evidence and mark it:

```text
python "<skill-root>/forge/state.py" mark <step-id> --state .img2threejs/state.json --evidence <path>
```

A non-applicable step requires `--status skipped --reason "<specific reason>"`.
A script's exit 0 alone is not a completion criterion. `projection-route` records
routing/descriptor evidence; actual baked pixels are verified in the material pass.
For `emission-target` and `plugin-gates`, follow the explicit handoff procedure.
The correction budget derives from review history: 3 per pass and 6 total by default.

## Intake and spec

1. Read the image and existing asset contract with agent vision, using
   `grimoire/intake/image_analysis.md`: classify, decompose macro/meso/micro,
   identify material/identity features, part relationships and hidden regions.
   `forge/stage1_intake/probe_image.py` adds metadata, not visual understanding.
2. Apply `grimoire/intake/validation_rubric.md` and admit references with
   `check_reference_admission.py`; complete any registered domain intake steps.
   Missing/unreadable images or inadequate views require input or an accepted
   approximation. Report inferred hidden geometry explicitly.
3. Read `grimoire/intake/quality_contract.md`. Create one assessment with
   `new_pre_spec_assessment.py` using the name, image, complexity and output flags
   from the checklist. It performs local BM25 search and records `localSpecSearch`.
   Refine that assessment instead of overwriting it with a second starter. Read
   `grimoire/intake/local_spec_search.md` for domain-specific or incomplete queries.
4. Fill `objectClass.primaryDomain`, quality contract and detail inventory. For
   detailed subjects use `build_detail_inventory.py` and
   `grimoire/intake/detail_inventory.md`; map each detail to a component's
   `localFeatures` or a material's `localOverrides`, not prose only. Resolve the
   surface routes and any applicable character/plugin branch before spec authoring.
5. Run `new_sculpt_spec.py` with the assessment and resolved domain/augmentation
   flags from the checklist. Replace starter review targets with real identity
   features (at most 5 critical and 3 important per pass). Use
   `grimoire/glossary/3d_vocabulary.md` and classify `topologyClass` with
   `grimoire/intake/surface_topology.md` before choosing primitives.
6. Complete material evidence/wiring when applicable. Run
   `forge/stage2_spec/validate_sculpt_spec.py object-sculpt-spec.json` and then
   `--strict-quality`. A shallow starter is blocked even if its JSON is valid.

## Build, capture and review

1. Inspect `orchestrate_passes.py status`; generate only the unlocked pass with
   `generate_threejs_factory.py`. Strict-quality and previous pass reviews must
   pass. Preserve a BLOCKED report and refine the spec when generation is refused.
   Use `--force` only for a new pass/refine-spec as directed by state. Refine-code
   edits the current factory; carry valid hand refinement back before regenerating.
2. Keep the factory TypeScript/plain Three.js (or the project's existing wrapper),
   reconstruction data separate from renderer objects, and procedural seeds fixed.
   Read `grimoire/build/geometry_patterns.md` for the actual geometry task. The
   surface contract governs images; procedural geometry does not forbid textures.
   For triangle reduction use the declared performance budget/tessellation tier.
   Runtime `geometryDescriptor.decimate` retains positions/recomputed normals
   and is refused on authored/unwrapped UVs; apply it before skin binding.
3. Render in the actual project browser. For every pass read the common
   `grimoire/review/gates_reference.md` and use `grimoire/review/self_correction.md`
   for review decisions. Load their conditional contracts only when applicable.
   Capture a fixed reference view and meaningful orbit views. Run
   `turntable_gate.py`, `self_intersection.py` and `attachment_anchor.py`; inspect
   missing azimuths, sampled vertices and unmeasured attachments. Failures block
   continue. Mesh extraction must come from the real preview; the companion
   `runtime/scripts/export_mesh_geometry.mjs` is separately installed, so use it
   only when available or implement equivalent extraction in the target project.
4. Run deterministic gates before AI vision. Record Tier 1 via
   `diagnose_render.py --spec object-sculpt-spec.json --pass-id <pass> --in-place`
   with the capture/reference inputs from its help; use
   `diagnose_render_multi_angle.py` for non-planar forms. Check the pass with
   `orchestrate_passes.py check`. Missing evidence is not a pass.
5. Create a side-by-side sheet with `make_comparison_sheet.py`, inspect with agent
   vision, and record overall, layer and critical-feature scores through
   `append_review.py`. Attach any required plugin review report and scene fixture.
   A failed critical feature blocks continue even if the global score passes.
6. Choose one action: continue, refine-spec, refine-code, request-input or stop.
   Use the root-cause guide; report changed parameters and remaining defects.
   Sync with `orchestrate_passes.py sync ... --in-place`, mark evidence, then run
   `next.py` before another pass/correction. For tiny features read
   `grimoire/review/divine_eye_microscope.md`: measure the visible footprint, not
   an isolated render; concave-feature darkness is not evidence of material colour.
7. After all build passes, run `check_part_coverage.py --spec <spec> --manifest
   parts.json` and verify the action-ready hierarchy. Mark both rows with evidence,
   then follow the handoff's emission/gate/remaining-rig order before final export.

## Completion evidence

Analysis/spec-only tasks end with their requested artifact and unverified work
identified. Implementation requires source/spec/state, actual project typecheck
and build results, reference/orbit renders and passing applicable reviews. The
upstream development suite/showcase is not bundled; missing runtime checks remain
unverified. Use `grimoire/scripts.md` and each installed script's `--help` for flags.
Final asset delivery additionally requires the export/Blender handoff contract.
