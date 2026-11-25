# Post-processing pipeline and engine delivery

How the local stages turn the MP4 into engine-ready 2D animation, and what is
deliberately not in this version.

## Frame sampling

The source video is 30 fps. Sprite frame rate is quantized to
`source_fps / integer step`; the CLI picks the step whose resulting rate is closest
to `--fps` and records the real rate in `frames/meta.json` (`effective_fps`).
The sheet stage and `manifest.json` always use that real rate, so GIF timing and
engine import never disagree with the frames. For loop runs the final source frame
(which repeats frame 0) is excluded from sampling.

## Alpha cutout

The model output has no alpha channel and the input image's alpha is flattened
before upload, so cutout is the only path to transparent sprites. Three strategies:

- `rembg` (default): the u2net session is created once and reused for every frame.
  Works on painted or textured backgrounds; costs a ~170 MB model download.
- `matte`: a **border-connected color key** that needs nothing beyond numpy. Only
  background color reachable from the frame border is removed, so the same color
  inside the character (eyes, highlights, cloth folds) survives — a plain global
  color match would punch holes in the subject. Tolerance is a squared RGB distance
  (`--matte-tolerance`, 0–120). With this mode the CLI flattens transparent input
  onto the key color and names that color in the prompt, so the generated background
  stays removable; `MATTE_NO_BORDER` means the key color is wrong for this video.
- `none`: opaque frames for full-screen effects and cutscenes.

The prompt envelope asks for a flat solid background in both cutout modes, which
keeps `matte` viable and rembg stable. Edges still deserve a visual check in
Phase 7; `matte` produces hard edges by construction.

## Pixel-art targets

`--scale` applies nearest-neighbour resizing (never bilinear — it blurs the hard
edges pixel art depends on) and `--colors` reduces the sequence to **one shared
palette**, built from a montage of evenly spaced frames and applied to every frame
without dither. Independent per-frame quantization picks different palettes per
frame and produces visible colour flicker in motion; the shared palette removes
that. Both settings are recorded in `frames/meta.json` under `pixel_art`. Scaling
happens after the union canvas is assembled, so every frame keeps an identical size.

## Canvas alignment

All frames share one union bounding box (subject box over every sampled frame plus
`--pad`), so the character keeps its absolute position inside a fixed canvas. This
preserves intended motion (steps, lunges, recoil) while giving every frame an
identical size — the property engines require for a sprite sheet. Global camera
drift in locked-camera output measured <= 3 px in the 2026-11-16 probe, which is
below one pixel of typical sprite downscale and needs no correction.

## Deliverables

| File | Content |
|------|---------|
| `frames/frame-NNN.png` | Uniform-canvas RGBA frames |
| `frames/meta.json` | Source fps, step, effective fps, canvas, offset, metrics |
| `contact-sheet.png` | 3-column sample grid for visual verification |
| `sprite-sheet.png` | Row-major grid, transparent padding |
| `preview.gif` | Looping preview at the effective fps |
| `manifest.json` | `schema: cs-game-anim-gen/manifest@1` with fps, frame_count, loop, cell, grid, file paths and metrics |

Import convention: read `manifest.json` first; `cell` + `grid` define the slice
rectangles, `fps` the playback rate, `loop` whether the clip wraps. This skill does
not create engine asset files (Animator controllers, SpriteFrames, AnimationClips);
the host dispatches the engine specialist or `cs-blender-operator` for that step.

## ROADMAP: delivery increments (v1.5)

Two increments borrowed from the `frameronin` skill's proven conventions; both are
local/CLI work, no new provider:

1. **Direction packs via mirror completion.** Generate five source directions
   (front, back, left, front-left, back-left) per action and obtain right,
   front-right and back-right by mirroring the left-side frames — eight directions
   from five paid runs (~37% saving) with guaranteed left/right symmetry. Requires
   one shared canvas contract across all directions of an action, a `mirrors` map in
   `manifest.json`, and mirrored frames written beside their source. Direction
   frames must be selected by inspecting numbered previews, never by uniform
   sampling or by guessing from an index.
2. **Machine-enforced budget gate.** A plan file recording each job's estimated
   `duration x resolution tier` cost plus the batch total, with an explicit
   `--confirm-charge` before submission, and a resume path that queries existing
   task ids instead of resubmitting. This turns the Phase 2 cost gate from an
   instruction into code, so an unbounded "try again" can never silently spend.

## ROADMAP: skeletal export (not in this version)

Target: locked-camera video -> pose tracks -> Spine JSON. Agreed sequencing:

1. **v2 entry — pose-track comparison report.** Extract 2D joint tracks
   (DWPose or an anime-tuned variant) and 3D tracks (SMPL-family, e.g. HybrIK /
   4D-Humans) from the same video, output a per-joint deviation report, and let the
   data choose the primary source. Rationale: 3D estimators are trained on real
   humans and degrade on robe-covered or stylized characters, while a locked camera
   makes 2D joints directly observable; the 3D->2D round trip is only worth its cost
   where occlusion ordering needs depth.
2. **v2 — Spine JSON with a single weighted mesh.** Bind the whole character image
   as one weighted mesh to the bone hierarchy (setup pose from the neutral frame),
   emit rotate/translate timelines from smoothed joint tracks (temporal smoothing
   plus keyframe reduction to the target fps), and validate by forward-kinematics
   self-rendering against the source video frames — no Spine license required.
   Target the Spine 4.x JSON dialect (`value` on rotate keyframes) and document the
   3.8 `angle` difference.
3. **v3 — part-cut rigs and dual formats.** Pose-guided part segmentation with
   inpainting for occluded regions, true multi-attachment skins, and DragonBones
   JSON alongside Spine.

Each increment ships with its own verification; none of them change the v1
frame/sheet contract above.
