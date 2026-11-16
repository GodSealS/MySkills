---
name: cs-ui-spec-from-image
description: "Extract a reproduction-ready DESIGN.md from UI screenshots and function notes, including layout, exact copy and resource bindings. Use for 从图片提取UI规范 or the spec stage of screenshot UI复刻; an explicit static-only scope can replace function notes."
---

# UI spec from image

Extract the evidence needed to reproduce the pictured screens. Appearance comes
from images; function comes from notes. Keep observed, estimated and unknown
facts distinct.

Read [the DESIGN.md contract](../../references/cs-design-md-contract.md)
before writing, including its screen/resource handoff and gap rules. Use the
[format spec](references/spec.md) for syntax questions and the
[format philosophy](references/PHILOSOPHY.md) when documenting design intent.

## Inputs

Read each supplied UI image at its original size. If no image is available,
request it before extraction. Read function notes from the conversation or the
named file; labels in an image establish copy, not hidden business behavior.
An explicit static-only request is sufficient scope without per-control notes.

For incomplete notes, extract known visual facts and classify missing behaviors
using the contract. Ask for blocking details while continuing independent work.
Check supplied/project asset and font files, and the target stack when named.

## Extract

1. Record the source/capture context, then separate captures by screen, state
   and viewport. Keep one DESIGN.md per visual system and identify merged images.
2. Run the sampler when Python and Pillow are available. From this skill directory:

   ```text
   python scripts/sample_colors.py "<image>"
   python scripts/sample_colors.py "<image>" --point 24 36
   python scripts/sample_colors.py "<image>" --region 20 30 8 8
   ```

   Default output is quantized palette candidates. Confirm flat-fill colors with
   original pixel/region samples away from antialiased edges. Point/region modes
   use original image coordinates and stored RGBA, without compositing/profile
   conversion. If sampling cannot run, mark visual estimates explicitly.
3. Measure meaningful regions, controls and text. Populate the contract's
   Observed Screens records: hierarchy, bounds/constraints, exact copy and
   wrapping, style/resource bindings and annotated event/results. Check ambiguous
   text at a readable scale and retain unresolved text when it cannot be read.
4. Populate Assets and Fonts from files actually inspected. Identify missing
   originals and actual substitutions instead of implying they were recovered.

Write a token only for a role that is visible. Omit an unmeasured scale and
list it in `omitted` with the reason. An unidentified font stays a generic
role (`geometric sans`, `humanist serif`, `mono`); do not substitute Inter,
Roboto, or another brand font. Mark every estimated value in Extraction Notes.

## Write

Write at the user's DESIGN.md path, otherwise next to the images. Update an
existing file when the task authorizes that update, preserving unrelated manual
content; clarify an ambiguous destination or unapproved replacement.

Follow the contract's order and evidence records. Name components by annotated
function (`icon-button-close`), or visible role when function is unknown. Describe
unpictured annotated results as such, without inventing their appearance. Finish
Extraction Notes with `READY`/`DRAFT`, blockers and fidelity limits.

## Done

The file is done when:

- images and available notes/static scope were read; every requested region,
  control and visible text has a record or a named evidence gap
- each capture retains its source/context and each used asset/font is bound to
  a verified file or an explicit missing/substituted resource
- every color, type, radius, and spacing token is observed or marked estimated
- section order and handoff records match the contract; notes distinguish
  blocking gaps from fidelity limits instead of claiming a draft is ready
- the contract's lint check has zero errors, or its unavailability and the
  manual checks are reported

Report path, readiness and remaining gaps. This skill completes the spec stage;
`cs-ui-generator` owns generation and runtime comparison. If the user requested
the full reproduction, continue to it under the existing authorization.
