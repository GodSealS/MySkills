# Surface Representation and Projection Bake

Read when selecting a surface representation, at `projection-route`, or before
implementing a reference-matched finish. This is the pack's authority for choosing
vertex colour versus projected textures; historical upstream plans are background.

## Select per surface before implementation

Record the component/material ID, route, source evidence, texture/triangle budget,
UV requirements, unseen-region strategy and acceptance checks in the asset contract.
For Cocos this belongs in the frontend lead's plan; the worker executes that choice.
Reuse an approved route. A conflicting plugin requirement or an undecided route goes
to the assigning owner before implementation, including when the budget cannot fit it.

| Surface and approved goal | Route | Required evidence |
|---|---|---|
| Uniform paint, no spatial pattern | Solid material albedo | Material assignment and reference-view render |
| Discrete flat-colour regions whose boundaries are defined analytically in object space, within the geometry budget | Vertex colour via `_shared/vertex_paint.py` | Geometry/palette and `vertex_region_gate.py` report, plus rendered boundary comparison |
| Reference-specific photographic detail, decals or complex painted patterns whose identity depends on the source pixels | Projected texture, when texture use is allowed | Actual baked image, UV/material wiring, source hashes and rendered comparison |

A stripe or marking is not inherently a vertex-colour surface. The approved goal
and representation select its route. If both routes fit and the plan leaves the
choice open, have the owner settle it. Neither route silently replaces the other
after a failed gate. For mixed assets record each region separately.

`vertex_region_gate.py` measures vertex colours; it does not validate a projected
texture. For projected regions use image/UV evidence and any applicable plugin's
projection-coverage/painted-region gate. All routes still pass geometry, material,
multi-angle and identity-feature review. Procedural geometry can use baked images.

## Projection: route evidence is not a baked texture

1. During intake, match and record the camera with `solve_camera_pose.py`, inspect
   the source crop, and de-light it with `delight_albedo.py`. Read the scripts' help
   for the installed flags. Keep source/crop/camera paths and hashes.
2. Generate the descriptor, using actual files and the planned component ID:

   ```text
   python "<skill-root>/forge/stage3_build/bake_projected_texture.py" --reference-image concept.png --delit-image albedo-delit.png --camera camera.json --mesh-id body --out projection-descriptor.json
   ```

   This command writes **JSON only**: it does no image sampling or UV rasterization.
   `projection-route` may be marked done with the approved route, input evidence
   and descriptor; it records a decision before a fitted mesh exists. A non-projected
   task skips that step with a reason referencing its approved surface routes.
3. At the material build pass, fit the mesh and provide valid UVs. Implement or use
   the actual project's Three.js projection and UV-bake routine described by the
   descriptor's `bakeSteps`. Record the source implementation/command and runtime
   version. The bundled factory does not automatically consume this descriptor.
   If the runtime cannot perform the bake, stop that pass with a named blocker.
4. Run the bake and save a real PNG or other agreed image, including the declared
   unseen-region treatment and coverage metadata. Wire it into the material's
   albedo map, with independent roughness/normal/AO inputs. A preview-only custom
   shader must be baked/converted to the agreed exportable material before handoff.
5. Reopen the saved image and render the textured mesh from the reference camera
   and meaningful orbit views. Check alignment, UV seams, uncovered texels, lighting
   contamination and required detail. Save the image path/hash/dimensions, mesh/UV
   revision, material mapping and comparison captures in `projection-bake-report.json`.

The material pass passes only with an actual saved image, correct material wiring
and passing visual evidence. A descriptor or successful descriptor command proves
none of these. Missing pixels or failed alignment block generation acceptance and
export. Regenerating geometry/UVs or replacing the source invalidates this bake's
affected evidence; repeat the bake and checks. Downstream Blender UV cleanup must
preserve the approved appearance or return a verified replacement texture.
