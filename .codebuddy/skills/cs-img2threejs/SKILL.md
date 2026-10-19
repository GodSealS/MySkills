---
name: cs-img2threejs
description: "Reconstruct 3D assets from concept images. Use when asked for img2threejs or image-to-3D work, including cs-cocos-specialist asset tasks; export generated models for Blender mesh and UV cleanup. / 根据概念图创建程序化 3D 模型，支持主动调用及 Cocos 专员使用，导出后交给 Blender 操作员修复网格和 UV。"
license: Apache-2.0
metadata:
  upstream-version: "2.0.0"
---

# Concept Image to 3D Asset

Use the bundled img2threejs pipeline to reconstruct a concept image as a procedural
Three.js model. Preserve the reference's identity and the assigned asset contract.
Single-view hidden geometry is inferred; record uncertainty instead of claiming an exact scan.

## Entry and Ownership

- A user may invoke `cs-img2threejs` directly or ask to use `img2threejs`.
- `cs-cocos-specialist` may load this public skill for an asset task covered by its
  frontend lead's `READY` plan. The lead retains design and acceptance authority;
  skill use grants no persona-dispatch authority or permission to change asset budgets.
- For a model-generation task, complete reconstruction and export, then have the **host**
  dispatch `cs-blender-operator` for mesh/UV cleanup using the handoff below. The host
  returns the repaired asset to the caller; the Cocos worker resumes integration and
  reports to its lead. Analysis/spec-only requests stop at their requested artifact.
- If Blender, export tooling or a required input is unavailable, deliver the completed
  stage with a named blocker. A generated factory alone is not a repaired game asset.

## Installed Paths and Prerequisites

Resolve this directory from the installed `SKILL.md`, not the author's checkout.
Use Python 3.10+ (`python` or `python3`, according to the host). Core `forge/` tools
use the standard library. A real Three.js preview/export needs the target project's
Node/Three.js setup and available browser/image tools. Optional neural adapters,
domain plugins, model weights and the companion showcase are separate dependencies;
the bundled integration instructions do not prove they are installed.

Read [platform execution](references/platforms.md) once when choosing paths or tools.
Work in a per-asset directory inside the assigned project. Stage a copy of this
skill at `.img2threejs/toolkit/` there once, as described in the platform reference:
the upstream spec-search helper writes a cache relative to its own package root.
Invoke scripts by absolute staged paths; all state, specs, source, screenshots and
exports belong in that asset workspace. Expand relative commands printed by Forge accordingly. Do not run
the upstream base installer over this pack or write task state into a shared skill.

## Reconstruction

1. Read the image and task/plan. Establish use, units, axes, pivot, scale, allowed
   hierarchy/names, triangle/material/texture budgets, rig/animation requirements,
   output paths/formats, per-surface material routes and verification appropriate to the target engine. Reuse
   approved decisions. For Cocos, return missing design choices to the frontend lead.
2. Read [the reconstruction workflow](references/upstream-workflow.md) for the common steps.
   Load only the branches selected by its routing table. The bundled procedural generator,
   quality contracts, strict validation and evidence gates remain authoritative for
   reconstruction. These are asset-quality checks, not a new code unit-test policy.
3. Initialize a new run once; for an existing run, resume through `forge/next.py` first.
   Example from the asset workspace (replace `<skill-root>` with the staged toolkit path):

   ```text
   python "<skill-root>/forge/state.py" init --state .img2threejs/state.json --reference concept.png --profile generic --spec object-sculpt-spec.json
   python "<skill-root>/forge/next.py" --state .img2threejs/state.json object-sculpt-spec.json
   ```

4. Follow the next-step output through intake, assessment/spec, staged generation and
   review. Every completed step needs evidence. Preserve strict gates, correction
   limits and explicit stop decisions; missing plugins or visual evidence are not
   passing results. Use the installed runtime's actual APIs and matching docs.
5. Retain the procedural source, spec, local state, reference view, multi-angle captures
   and reviews. After `part-coverage` and `action-ready`, follow the handoff's terminal
   state procedure; finish any profile-specific rig steps before final export.

## Export, Blender Cleanup and Delivery

Read [the asset handoff contract](references/blender-handoff.md) before exporting.
It defines the actual GLB handoff, required evidence and cleanup/return responsibilities.
The base pipeline has no built-in GLB emission provider: use the project's Three.js
`GLTFExporter` as described there, or a verified installed export provider. A missing
`--target glb` provider is a blocker, not permission to fabricate an export result.

The host gives the actual exported model and contract to `cs-blender-operator`, which
loads its private mesh-editing and texture skills. It removes unintended isolated
vertices, repairs accidental open/broken surfaces and incorrect UVs, while preserving
intentional openings, seams, shared materials and approved shape. Topology or UV work
that changes the agreed design goes back to the assigning owner before it is applied.

Deliver source/spec/state, pre-cleanup export, repaired `.blend` and consumer format,
textures, repair report and visual evidence. Record hashes for both export revisions;
regenerating the factory invalidates the downstream repair evidence. Cocos integration
and final acceptance remain with the worker and frontend lead under their existing plan.
Distinguish `GENERATED`, `EXPORTED`, `CLEANED` and `INTEGRATED` evidence; report only the
stages actually performed, with blockers for outstanding requested work.

Source revision, license, unchanged resource hashes and adapted-file records: [PROVENANCE.json](PROVENANCE.json).
