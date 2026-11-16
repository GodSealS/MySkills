# DESIGN.md contract

Shared authoring and reproduction contract for the two UI skills. The bundled
`references/spec.md` defines DESIGN.md syntax; this contract defines their
handoff and verification requirements. The philosophy explains design intent,
not an exception to measured values or reproduction acceptance. Preserve legal
extensions in an existing file.

## File shape

Two layers, one file:

1. Tokens — YAML front matter and/or fenced `yaml` blocks. Normative values.
2. Prose — `##` sections. How to apply the values, and what the design is.

A top-level token key (`colors`, `typography`, `rounded`, `spacing`,
`components`, `name`, `version`, `description`, `omitted`) appears at most
once in the whole file. A `##` heading appears at most once.

```yaml
version: alpha
name: <product or system name>
description: <one sentence; optional>
omitted:
  - section: spacing
    reason: <why this section has no measured scale>
colors:
  <role>: "<css color>"
typography:
  <role>:
    fontFamily: <string>
    fontSize: <px|em|rem>
    fontWeight: <number>
    lineHeight: <number or dimension>
    letterSpacing: <dimension>
rounded:
  <level>: <dimension>
spacing:
  <level>: <dimension or number>
components:
  <component-or-variant>:
    backgroundColor: "{colors.role}"
    textColor: "{colors.role}"
    typography: "{typography.role}"
    rounded: "{rounded.level}"
    padding: <dimension>
    height: <dimension>
    width: <dimension>
    size: <dimension>
```

Color is any CSS color. Hex `#RRGGBB` is the default. Dimension units are
`px`, `em`, `rem`. A reference is `{path.to.token}` and must point at a
value, except `components.*.typography`, which may point at a typography
object. Component variants are separate keys (`button-primary`,
`button-primary-hover`), not nested states.

## Section order

Present sections stay in this order. Omit a section that has no evidence;
list it under `omitted` with a reason. Do not invent a placeholder section
to fill the list.

1. Overview (alias: Brand & Style)
2. Colors
3. Typography
4. Layout (alias: Layout & Spacing)
5. Elevation & Depth (alias: Elevation)
6. Shapes
7. Components
8. Do's and Don'ts

These skills append their reproduction evidence after that list:

- `## Observed Screens` — source screens, geometry, content and behavior.
- `## Assets and Fonts` — resource inventory and element bindings.
- `## Extraction Notes` — evidence, estimates, unresolved gaps and readiness.

These are prose sections, not new top-level token groups. Additional extension
sections remain legal under the format spec.

## Observed Screens handoff

Use a stable screen ID and a `###` subsection per screen/state/viewport capture.
Different captures of the same screen reference that screen ID; retain their
individual measurements instead of averaging them into a single layout.

Record the following as tables or equivalent explicit fields. An unknown value
stays `unknown` with its effect on reproduction; an estimate says `estimated`.

| Record | Required information |
|---|---|
| Source | Capture ID, image path relative to DESIGN.md where possible, original pixel width/height; source hash when available. Keep the reference image reachable. |
| Capture context | Screen ID, state, viewport in CSS/design units, device scale/DPR, image scaling/crop origin, scroll position and safe area, each known or unknown. Source pixel size alone does not establish viewport or DPR. |
| Element | Stable ID, parent ID, component/variant, source-image bounds `[x,y,w,h]`, alignment/anchoring, gap/padding, overlap/layering, clipping/scroll behavior, and measurement evidence. |
| Content | Exact visible copy per element, casing, intentional line breaks, wrapping/truncation, selected values and representative data. Record unreadable text as unresolved rather than inventing it. |
| Bindings | Style token/prose references and asset/font IDs for each relevant element. Keep screen data and geometry out of reusable color/type tokens. |
| Behavior | Element ID, event, precondition, action, resulting state/navigation and observable check, all traced to notes. Distinguish local demo behavior, external integration and unknown behavior. |
| Adaptation | For each supplied viewport, fixed/fluid dimensions, constraints, wrapping, safe-area and overflow rules. A single screenshot proves one viewport; label any extrapolated behavior. |

Bounds use original source pixels with a top-left origin; width/height are extents.
Record any conversion to CSS/design coordinates explicitly. Measure controls,
visible text and meaningful regions; parent/component relationships can describe
repeated decorative details. Snapshot bounds are evidence, not a requirement to
implement every element with absolute positioning.

Notes can describe an interaction whose resulting state is not pictured. Preserve
that behavior as `annotated, not pictured`; its visual treatment stays unknown
until another reference or an explicit design decision supplies it. For a
static-only request, mark behavior `out of scope` rather than inventing actions.

## Assets and Fonts handoff

For each used photo, icon, illustration, background and font, record a stable
resource ID, type, source/local path, bound element IDs, intrinsic size or font
family/weight/style, display size, crop/fit/tint and availability:

- `available` — matched to a supplied or existing project file; verify that file.
- `reference-only` — visible in the screenshot but no independent source found.
- `substituted` — name the actual replacement and the affected elements.
- `missing` — state what is needed and which acceptance check it prevents.

Inspect supplied/project resources before selecting a replacement. A screenshot
does not recover an original vector, an occluded asset or a font file. Crop only
an isolated, unobscured raster region when it is suitable for reuse; record source
and crop bounds. Keep the UI as real controls/text, not a whole-screen image.
Use an asset operator through the host for asset work beyond simple resource
reuse. Existing authorization applies; generating UI does not itself authorize
fetching unrelated assets or installing fonts system-wide.

Known font names still require a usable font source or verified installed font.
Record the actual rendered family and loading failure/fallback; changes to glyph
width and wrapping remain visual differences. Bundle local resources or use
project paths so an exported HTML page can load its declared dependencies.

## Gaps, readiness and repair

Classify each unresolved item by affected element/check and evidence:

- `blocking` — the requested slice cannot be built meaningfully or safely, such
  as an unreadable required label or a required behavior with no defined result.
- `fidelity-limiting` — a draft can run, but exact appearance/behavior remains
  unverified, such as an unidentified font, missing illustration or inferred DPR.
- `out-of-scope` — deliberately excluded by the user's request.

Unknown behavior blocks its implementation, not independent visual extraction.
Ask focused questions for blockers while continuing independent work. Mark a
spec `READY` when requested-scope blockers are resolved, `DRAFT` otherwise;
list fidelity limits separately. `READY` means usable input, not verified fidelity.

Record each estimated token/measurement with capture/element, method and
confidence (`measured`, `estimated`, `unknown`). Conflicts retain both sources
and the rule used to resolve them. Appearance follows the image; business meaning
follows notes. An explicit requested visual change is a new requirement, not an
observation of the reference.

When generation or comparison exposes a gap, return the affected IDs and evidence
to the spec-authoring step, update only those entries under the current task's
authorization, then regenerate/recheck the affected screens. Preserve unrelated
manual content. For an externally authored DESIGN.md, request or record the
necessary clarification directly; extraction is not required without an image.

## Reproduction verification

The generator writes `UI-VERIFICATION.md` beside its output. Record mode, target
stack, output files, capture IDs/states/viewports, actual runtime and device scale,
font/resource loading, reference/rendered image paths, applied tolerances, visual
checks, behavior checks and unresolved differences. Link the actual evidence.

For each reference capture:

1. Run the actual target and reproduce its content, viewport, scale, scroll and
   state. Wait for fonts/assets to load and settle animations. Use browser checks
   for web UI and the engine/device runtime for canvas/native UI.
2. Capture at the reference size. Repair capture-context mismatches before
   comparison; keep the reference intact and avoid stretching/cropping evidence
   merely to make the metrics pass.
3. Set tolerances before comparing, using the user's criteria or documented
   working tolerances. Inspect key element bounds, text/line breaks, fonts,
   colors, assets/cropping, borders and layering as well as whole-screen pixels.
4. Inspect the side-by-side, overlay and difference images. Mask only genuinely
   dynamic regions with a documented reason, location and size; keep those
   regions visible in the original captures. Review small critical controls even
   when their area falls below a whole-screen pixel threshold.
5. Repair implementation differences; repair source measurements only with new
   evidence. Repeat affected captures. Reuse unchanged valid checks and preserve
   each iteration's evidence. If progress needs missing input/tooling or stalls
   over two repair passes, deliver the current artifacts with the remaining gap.

Helper defaults (`pixel-tolerance=8`, `max-changed-ratio=0.01`) are screening
defaults, not a similarity percentage or a universal acceptance threshold.
Use zero tolerance/zero changed ratio if exact pixels are required. A pixel
`PASS` alone establishes neither layout correctness nor working interactions.

Use one overall result in the verification report:

- `VERIFIED` — the real target ran; every requested reference/state/viewport met
  recorded visual checks and every in-scope interaction passed; no unresolved
  fidelity limit affects the requested acceptance.
- `PARTIAL` — useful output exists, but runtime, references, assets or requested
  checks are incomplete, or a visual/behavior check still fails.
- `BLOCKED` — a named missing prerequisite prevents the requested slice.

A new screen without a matching reference can be runtime-checked for brief and
design-system adherence; label reference fidelity `not applicable` and do not
claim reproduction. Static inspection or unavailable browser/engine tooling
cannot produce a `VERIFIED` reproduction result.

## Prose

Prose explains intent and application. Declared tokens and observed measurements
remain the values to reproduce; narrative style is not permission to change them.

- Name a specific reference (object, material, product type), not a list of
  adjectives. "Modern, clean, premium" is not a design.
- State where a value is used and where it is not. Cite tokens as
  `{colors.primary}` in the sentence that restricts them.
- Do's and Don'ts name concrete absences the reference does not already
  make obvious. Pair each Don't with the treatment to use instead when the
  replacement is not already stated above.

## What not to write

- Token names follow visible roles. Do not copy sample palettes out of the
  format spec's examples.
- Do not emit a full Material palette (`on-primary-container`,
  `primary-fixed`, …) unless each role is visibly distinct.
- Do not put sample copy, user names, or one screen's data into color or
  type tokens.
- Unknown component properties are legal; prefer the listed properties so
  lint stays quiet. Extra visual facts (blur, border, shadow) belong in
  Elevation prose, not in an unlisted component field, unless the prose
  cannot apply them without the value.

## Lint

From the file's directory, when npm is available:

```text
npx "@google/design.md" lint DESIGN.md
```

`errors > 0` blocks delivery. Warnings are reported, not silently rewritten.
If the CLI cannot run, say so and check this contract by hand.
