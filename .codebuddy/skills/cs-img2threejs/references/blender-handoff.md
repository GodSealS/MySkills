# Generated Asset to Blender to Consumer

This is a downstream asset stage. The procedural spec/factory remains the source
of reconstruction decisions; Blender edits produce a separate, versioned asset.
The upstream rule requiring reconstruction fixes in source still applies during
generation. It does not forbid this explicitly requested post-export cleanup.

## Export a Real Model

1. Finish the source generation and image-review gates, then follow the terminal
   state procedure below. Export the model's root,
   not preview grids, reference cards, helpers, lights or presentation cameras.
   Preserve its approved node names, local transforms, pivot, units and materials.
2. Use the project's installed Three.js version and its matching `GLTFExporter`.
   The base `forge/stage3_build/emit_target.py --target glb` works only with an
   installed provider declaring that target; it is not a bundled GLB converter.
   A project exporter is the direct path when no provider is installed.
3. Run in the actual project browser where the factory and textures are loaded.
   The following is an integration pattern, not a tool name or a ready-made scene:

   ```javascript
   import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';

   // modelRoot and clips come from the completed factory and approved asset task.
   modelRoot.updateMatrixWorld(true);
   const bytes = await new GLTFExporter().parseAsync(modelRoot, {
     binary: true,
     onlyVisible: false,
     animations: clips,
   });
   if (!(bytes instanceof ArrayBuffer)) throw new Error('Expected binary GLB');
   // Save through the project's/browser's supported download or file mechanism.
   // Wait for completion and verify the actual saved file, not just this buffer.
   ```

   Inspect the model subtree first: `onlyVisible: false` includes hidden objects.
   Use `clips: []` for a static asset. JS interaction handlers, procedural animation
   callbacks and custom shaders do not automatically become glTF behavior. Bake or
   convert unsupported features only within the contract; report export warnings
   and missing textures/animations. Preserve unmodified source assets.
4. Save to an agreed path such as `exports/model.generated.glb`; record its SHA-256,
   factory/spec revision and texture dependencies. Run
   `python "<skill-root>/forge/stage1_intake/probe_glb.py" <actual-file> --out glb-probe.json`
   using the staged toolkit root.
   This proves only what the prober reports. Reimport in Blender for bounds,
   hierarchy, material/UV and requested animation checks; a container check is
   not visual equivalence or a guarantee of engine compatibility.

Official exporter reference: [GLTFExporter](https://threejs.org/docs/pages/GLTFExporter.html).
Check the installed version's API when options or supported features differ.

## Terminal State and Export Evidence

Choose `project-exporter` or `installed-provider` in the asset contract. Keep this
choice in `export-report.json` with the source/spec revision, actual exporter/version,
output path/hash, texture dependencies, probe result, warnings and verification.
Commands below run from the asset workspace with the staged `<skill-root>`.

After `part-coverage` and `action-ready` have evidence, inspect `state.py status
--json`. At `emission-target`:

- **Project exporter:** the Forge emission provider is not used. Record that fact
  in `export-report.json` (`status: pending` until a real file is verified), then
  explicitly skip this provider-only step. This does not declare the GLB exported.

  ```text
  python "<skill-root>/forge/state.py" mark emission-target --state .img2threejs/state.json --status skipped --reason "Project GLTFExporter selected; Forge provider not used; actual export tracked in export-report.json" --evidence export-report.json
  ```

- **Installed provider:** run `emit_target.py --spec object-sculpt-spec.json
  --workspace . --target <kind> --plugin <id>` using its staged absolute path and
  the verified provider. Success must record `emission-target=done`, artifact
  evidence and `targetSelection`. A run without `--target` is a no-op and leaves
  the step pending; it is not this route. A failed/missing provider remains blocked.

At `plugin-gates`, run the gate sweep for **either route**, since a domain plugin
may have participated without providing export:

```text
python "<skill-root>/forge/stage3_build/run_gates.py" --workspace .
```

Persist its JSON stdout as `plugin-gates.json` with the host's UTF-8 file tool and
record the exit code. Only exit 0 with every involved blocking gate passing permits:

```text
python "<skill-root>/forge/state.py" mark plugin-gates --state .img2threejs/state.json --evidence plugin-gates.json
python "<skill-root>/forge/state.py" status --state .img2threejs/state.json --json
```

An empty `{}` is valid evidence that no plugin gates were involved. Missing tools,
errors or blocking failures leave the step pending; the choice of project exporter
does not exempt domain gates. Never mark the sweep before inspecting its result.

Continue any remaining profile steps through `next.py`; animated profiles run
Stage R after these final rows. A provider export made before Stage R is provisional.
After all source/rig steps, require `status=complete` and an empty `pending` list,
then create the final project export or rerun the provider against the finished
source. If that finalization changed the source, rerun applicable plugin gates,
save fresh reports and repeat export checks. Failure blocks handoff even if an
older checklist says complete. Do not edit state JSON to manufacture completion.

`EXPORTED` requires the actual final file and matching hashes, a passing probe,
current source/rig and gate evidence, and `export-report.json` with `status: verified`.
Checklist completion alone is not export evidence. Pass only that final revision
to Blender, preserving any provisional files separately.

## Host Dispatch Payload

The caller supplies this payload to the host for `cs-blender-operator`. The host
passes the installed operator path and original user request needed by its MCP tools.
The Cocos worker does not gain an `Agent`/`Task` tool by loading this skill.

- Task/project ID, assigning owner, plan path/revision for Cocos tasks, accepted
  concept image and generation evidence. Include target Cocos version/platform.
- Actual input GLB and dependency paths/hashes; state whether Blender can access
  those paths, and transfer through an available host mechanism if it cannot.
- Allowed objects, output paths and target format, units/axes/scale/pivot,
  hierarchy/names, material slots, UV channels, texture and triangle budgets,
  rig/shape-key/animation constraints and intentional open surfaces or mirrored UVs.
- Cleanup requested: unintended isolated vertices/loose geometry, accidental
  holes/broken faces and incorrect UVs. Include known defects or screenshots;
  inspect for additional defects within this same scope.
- Required data/visual checks and return recipient. For Cocos, design conflicts
  return through the host to `cs-frontend-lead`; routine cleanup remains execution.

For a standalone user task, reuse its requirements and let the host resolve material
ambiguity. A standalone asset edit does not acquire the Cocos plan ceremony.

## Cleanup and Return

The Blender operator loads private Mesh Editing and Textures; add Materials only
if assignments or shader wiring need repair. Follow those skills for actual edits.

- Inspect loose vertices, boundary/non-manifold edges, degenerate faces and normals.
  Remove unintended isolated geometry. Repair only accidental holes, broken surfaces
  or disconnected faces; preserve designed openings, thin surfaces and separate parts.
- Check UV availability, finite coordinates, collapsed islands, distortion, seams,
  padding and texture alignment. Overlap or coordinates outside 0–1 can be intentional
  (mirroring, tiling, UDIM); diagnose against the material/asset contract before repair.
  Geometry changes can invalidate UVs, weights and shape keys: recheck them afterward.
- Save a separate `model.cleaned.blend`, required textures and the requested consumer
  export (`model.cleaned.glb`, or another format required by the target Cocos version).
  Preserve the generated GLB. Reopen/reimport outputs, inspect multiple angles and UV
  appearance, and sample required animation. Never substitute a screenshot for a model.
- Return input/output hashes, changed objects, before/after defect measurements,
  repairs, intentionally retained boundaries/UV overlaps, actual preview evidence,
  export/reimport results and unresolved defects. `CLEANED` requires the requested
  repair checks to pass; otherwise return partial output with a named blocker.

The host relays this result to the original caller. For Cocos, the specialist imports
the repaired consumer asset with stable project references and runs the lead's planned
Creator checks; the frontend lead accepts it. A changed source spec, regenerated GLB
or replacement texture invalidates affected downstream cleanup/integration evidence.
Record the new revision and repeat affected stages before using a prior clean result.
