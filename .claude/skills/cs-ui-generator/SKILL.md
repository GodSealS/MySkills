---
name: cs-ui-generator
description: "Generate and verify UI from DESIGN.md: reproduce observed screens or design a new screen in that system. Use for 根据规范生成UI or UI复刻 after screenshot extraction; includes resource bindings and render/compare/repair."
---

# UI from DESIGN.md

Generate the requested UI and verify it in the actual target. Tokens are values;
prose determines their use. Reproduction also preserves source geometry, copy,
resources and requested behavior.

Read [the DESIGN.md contract](../../references/cs-design-md-contract.md)
before generating, including gap repair and reproduction verification. Use the
[format spec](references/spec.md) for syntax questions. Apply the user's values,
not the format examples.

## Inputs

A DESIGN.md is required. Read it completely and resolve its source images and
resources relative to the file. For a screenshot-only request, use
`cs-ui-spec-from-image` first, then continue when the spec supports the slice.

Choose and report the mode from intent, not merely the presence of a brief:

- `reproduce`: requests to copy, restore, match, 复刻 or 还原 an observed screen.
  A brief adding click behavior or naming the screen stays in this mode. Read
  the reference images as well as Observed Screens; retain their layout/copy.
- `new-screen`: an explicitly new layout or screen in the visual system. Use
  the brief; Observed Screens illustrate usage rather than prescribe its layout.
- No explicit mode and observed screens exist: default to `reproduce`. Without
  an identifiable screen or new-screen brief, ask what to build.

Explicit requested visual changes override those parts of the reference; record
them as intended deviations. Classify other gaps under the shared contract,
continue independent work, and repair blocking spec entries before dependent work.

## Target

Use the target the user names. Otherwise, if the task is to edit an existing
UI file, edit that file in its current stack. Otherwise write one
HTML file per screen in `ui/` next to DESIGN.md, with local assets when needed.
Reuse the current app and resource pipeline. Modify existing source within the
authorized scope rather than starting a second app.

For Cocos work, read [cs-frontend-ui](../cs-frontend-ui/SKILL.md) for lead/worker routing and verify the
Creator runtime: map design units, hierarchy, anchors, widgets, clipping and
resource types to actual scene/prefab components. Other native targets use their
existing project conventions and runtime; HTML output does not prove that target.

## Generate

Map reusable styles to the spec's tokens/prose and screen-specific dimensions
and content to its observation records. In HTML, declare token values as CSS
variables (`--colors-primary`) and use them at call sites. Use constraints and
the project's layout system to satisfy measured geometry across supplied sizes.

Apply the Overview reference and each section's restrictions. A token that
prose limits to one role stays in that role. Resolve missing roles through the
contract's gap classification and repair loop. Correct implementation under existing
values; change spec values only when source evidence or an explicit requirement
supports it. An unknown font may use a named generic fallback for a draft, but
retain that fidelity limit and verify actual font loading and line breaks.

Bind real images/icons/fonts through Assets and Fonts. Keep text and controls
interactive rather than using the screenshot as a full-page background.
Implement annotated events/results in the existing state/navigation system.
Label local demo behavior and unavailable external integration honestly; use
static controls only when that is the requested scope.

Do not restyle the screen toward a generic kit. If the spec has no gradient,
shadow, blur, or rounded corner, the UI does not add one.

## Render, compare, repair

Follow the contract's reproduction verification steps and write
`UI-VERIFICATION.md`. For web output use an available browser tool or
[cs-browser-test](../cs-browser-test/SKILL.md); the active implementation owner runs the checks. Capture the
actual engine/device target for non-DOM content. Use existing available tools;
if they cannot run, report `PARTIAL`/`BLOCKED` with the precise missing check.

With Python and Pillow, from this skill directory:

```text
python scripts/compare_ui.py "<reference.png>" "<rendered.png>" --out-dir "<iteration-evidence>"
```

The helper writes `comparison.json`, `side-by-side.png`, `overlay.png`, `diff.png`.
Exit 0 means its pixel screen passed, 1 a pixel/size mismatch, 2 invalid input or
missing dependency. Dimensions must match; it never resizes the images. Review
the artifacts, not just the exit code. See `--help` for working tolerances and
repeatable `--mask X Y W H` exclusions; document every mask's reason in the report.
Use separate reference/render captures and a new evidence directory per iteration;
the helper rejects input overwrite, self-comparison and existing evidence files.
Use an equivalent overlay/manual comparison when Pillow is unavailable and
report which checks/metrics were not performed.

Repair differences and repeat affected checks within the contract's stopping
rule. Changing thresholds, masks or source measurements merely to obtain a pass
does not resolve the difference.

## Done

The UI is done when:

- the chosen mode and screen match user intent and all used source/spec entries
  are accounted for
- reusable styles trace to tokens/prose, screen geometry/content to observations
  or the new-screen brief, and actual substitutions are named in the report
- each Don't in the spec is absent, and each component used matches its
  component entry and prose
- spec lint was checked or its unavailability reported; errors were resolved via
  the spec-authoring step rather than hidden during generation
- real target captures and visual/behavior checks exist for requested states and
  viewports, or the result explicitly remains `PARTIAL`/`BLOCKED`

State output and verification-report paths, mode, overall result and unresolved
differences. A generated file alone is not a verified reproduction.
