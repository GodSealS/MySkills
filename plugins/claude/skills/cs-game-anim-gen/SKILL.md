---
name: cs-game-anim-gen
description: "Generates 2D game animation from a character image via wan3.0-video: locked-camera motion video, per-frame PNGs with cut alpha, a packed sprite sheet, GIF preview and an engine-ready manifest; loop cycles close by sending the character as first and last frame. / 通过 wan3.0-video 从角色图生成 2D 游戏动画：锁定机位动作视频、抠像逐帧 PNG、精灵图、GIF 预览与引擎可用 manifest；循环动作以首尾同帧闭合。"
---

# Game 2D Animation Generation (wan3.0-video)

Two positional inputs: the character image and the animation context. The bundled
`scripts/gen_anim.py` wraps the DashScope async video protocol plus a local,
zero-cost post-processing pipeline behind one CLI with three stages: `video`
(paid), `frames` and `sheet` (local, re-runnable).

## When to Use

- Sprite/frame animation for engines: idle, walk, run, attack, hurt, cast, die
- Locked-camera motion previews and animatics from existing character art
- GIF previews for design review of a motion idea

Route static concept art to `cs-game-image-gen` and 3D reconstruction to
`cs-img2threejs`. HD2D/pixel-art eight-direction action packs and sprite reskinning
belong to the external `frameronin` service skill — a different provider, billing
model and art direction; use this skill for painterly or arbitrary-style
video-derived animation. Skeletal/Spine rigs are a documented ROADMAP increment
([references/postprocess.md](references/postprocess.md)), not this skill's output.

## Prerequisites

- Python 3.9+ with Pillow, numpy and one decoder (imageio-ffmpeg preferred;
  opencv-python-headless or av accepted). Install with
  `python -m pip install -r "<skill-dir>/requirements.txt"`; `--dry-run` needs only Python.
- Alpha cutout: `--alpha rembg` needs `rembg` (`python -m pip install rembg`) and
  handles painted scenes; `--alpha matte` needs nothing beyond numpy and keys out a
  flat background; `--alpha none` keeps opaque frames.
- Authentication comes from `ANTHROPIC_AUTH_TOKEN` (the `sk-sp-` Token Plan key, the
  official docs' env name), falling back to `QWEN_API_KEY` then `TOKEN_PLAN_API_KEY`.
  Dry runs need no key.
- Endpoint host: `QWEN_VIDEO_BASE_URL`, else `https://token-plan.maas.qianwenaiapi.com`.
  The `sk-sp-` key belongs to that platform; the aliyuncs.com Token Plan host is a
  DIFFERENT platform and rejects this key with 401. This is the DashScope async task
  protocol; read [provider notes](references/provider-notes.md) before changing hosts
  or quoting costs.

## Workflow

### Phase 1: Classify the action and load the template

| Kind | Examples | Template |
|------|----------|----------|
| loop | idle, walk, run, breathe, float, hover | [references/templates/loop.md](references/templates/loop.md) |
| oneshot | attack, cast, hurt, die, jump, dash | [references/templates/oneshot.md](references/templates/oneshot.md) |

Resolve facing (side / front / three-quarter), cycle length and style from the
request or the project's established art direction; state assumptions when neither
exists. Finish this phase with one kind, one facing and an explicit loop decision.

### Phase 2: Model, resolution and the cost gate

| Model | Use when |
|-------|----------|
| `wan3.0-video` | **Default.** All task types; the model routes by media and prompt |
| `wan3.0-video-prime` | Same capability with faster end-to-end latency |

Billing is per output second and scales with resolution tier; the CLI defaults to
`480P` deliberately because sprite frames are downscaled anyway and the API's own
default (1080P) costs 4x the 480P rate. **Cost gate:** before any paid run state
duration x resolution x rate with its source from [provider notes](references/provider-notes.md).
Token Plan spends Credits — never translate list prices into a fixed Credits or cash
figure. Retries are explicit, never automatic; preserve task ids and downloaded files.

**Draft → final ladder:** iterate at 480P, get the motion approved, then re-run the
approved context at 720P/1080P only if the target actually needs the pixels. Frames
and sheets can be re-extracted from an approved draft at zero cost, so upgrade the
video only when resolution — not motion — is the open question. Name runs with
`--name <character>-<action>` so drafts and finals stay distinguishable.

### Phase 3: Resolve the destination before generation

| Engine | Assets root | Output dir |
|--------|------------|------------|
| Unity | `Assets/` | `Assets/Art/AIGenerated/animation/<character>/<action>/` |
| Godot / Cocos | `assets/` | `assets/art/ai-generated/animation/<character>/<action>/` |
| Unreal | `Content/` | `Content/Art/AIGenerated/Animation/<character>/<action>/` |

If no game project is detectable, ask which project is in play; fall back to
`--out generated-animations/` in the workspace only when the user confirms none.
Result video URLs expire in 24 hours — the downloaded MP4, frames and sheet are the
deliverables. Finish with the resolved directory for `--out`.

### Phase 4: Compose the context

Fill the selected template's slots into the context. The CLI prepends the
locked-camera constraint, the first-frame role declaration ("图1为精确首帧…") and,
with `--loop`, the cycle-closure instruction — do not repeat those in the context.
Pass `--loop` for loop kinds so the character is sent as both first and last frame.

Prompt discipline (each rule prevents a paid failure mode):

- **Parameters never enter the prompt.** Duration, resolution, ratio, fps, format
  and model name are CLI arguments only. Writing "3秒循环" or "720P" into the
  context wastes tokens and can contradict the actual request.
- **Entity checklist before submitting.** List every required character, prop and
  setting with one unambiguous responsibility; state counts and ownership for
  unique props ("剑始终背在背后，葫芦始终在左手"). Describe the anchor by
  appearance, not by name — "白发黑袍、背负长剑的剑客" constrains more than a
  character's proper name.
- **Explicit negations for leakage-prone attributes.** When a prop, colour or
  identity tends to drift, negate the wrong variant ("武器不是刀，袍色不是红").
- **Stage structure for multi-beat actions.** Use
  `阶段N：起始可见状态 → 一个具体动作 → 可观察结束状态` instead of free prose;
  each stage ends in a state the next inherits.
- **Do not pad duration.** If the clip is longer than the action needs, expand the
  existing action with preparation, pauses and reactions — never repetitive
  filler, extra characters or a changed ending.

### Phase 5: Generate the video and check the machine result

```bash
python "<skill-dir>/scripts/gen_anim.py" "<character-image>" "<context>" --stage video --loop --duration 3 --resolution 480P --out "<resolved-output-dir>"
```

- Use `--dry-run` before an unfamiliar parameter combination; it prints the payload
  (base64 elided) and calls nothing.
- One JSON object on stdout, logs on stderr. Exit 2 = local/usage failure,
  exit 3 = transport/provider/task failure. The CLI redacts the API key.
- `status: success` means the MP4 downloaded and decoded as an MP4 container.
  Compare `usage.duration`, `usage.SR`, `usage.fps` and `usage.ratio` against the
  request; a mismatch is an error to resolve before spending on another run.
- **Async by default for long jobs.** `--submit-only` returns the `task_id` plus a
  `task-<id>.json` record and ends immediately; resume later with
  `--task-id <id> --stage all` (poll + download + post-process, no new submission).
  Prefer this over blocking the session for minutes. A timed-out poll may still
  succeed server-side — always resume by task id before resubmitting.
- **Submit one clip at a time** and let the user review it before the next paid
  run, unless parallel clips were explicitly requested. Batch submission hides
  drift: one rejected direction is cheaper to redo than five.
- Each download writes `<video>.mp4.source.json` recording the provider URL
  (valid 24 h). Keep it: it is the only way to reuse the clip for edit/extend.

#### Revising an existing clip

Decide what the existing clip **is** in the next call before spending:

| The clip is… | Route |
|--------------|-------|
| The thing being modified (colour, prop, a region) | `--edit-from <url-or-mp4-with-sidecar> "<只改什么，其余保持不变>"` |
| A motion source to continue or lengthen | `--extend-from <…> "<新动作>" --duration N [--extend-direction forward\|backward]` |
| Not reusable — the intent changed | regenerate from the character image, restart at Phase 1 |

Edit/extend send the clip as `reference_video` (frame slots and reference slots are
mutually exclusive, so no character image and no `--loop`). Edit inherits source
timing (`duration: -1`, `ratio: adaptive`); extend adds the requested seconds and
requires input + output ≤ 30 s. `reference_video` accepts only a public/OSS URL —
a local MP4 works solely through its recorded `.source.json` URL within 24 h;
otherwise the CLI fails with `SOURCE_URL_REQUIRED` rather than guessing.
**No generative edit is lossless**: review the result before replacing deliverables.

### Phase 6: Post-process into frames and sheet (zero cost, re-runnable)

```bash
python "<skill-dir>/scripts/gen_anim.py" --stage all --from-video "<mp4>" --fps 12 --alpha rembg --loop --out "<resolved-output-dir>"
```

- `--stage frames` writes uniform-canvas `frames/frame-NNN.png` plus
  `contact-sheet.png`; `--stage sheet` packs `sprite-sheet.png`, `preview.gif` and
  `manifest.json`. `--stage all` runs both. Re-run freely with different
  `--fps`/`--alpha`/`--pad`; never re-pay for the video to change sampling.
- Sprite fps is quantized to `source_fps / integer step`; the real rate is written
  to `frames/meta.json` and reused by the sheet stage and manifest.
- Choose the cutout by background complexity:

  | `--alpha` | Use when |
  |-----------|----------|
  | `rembg` | **Default.** Painted scenes, complex or textured backgrounds |
  | `matte` | Flat solid background; border-connected color key, no extra dependency. Keeps same-color regions inside the character. Tune with `--matte-color` / `--matte-tolerance` |
  | `none` | Full-screen effects and cutscenes where opaque frames are fine |

  With `--alpha matte`, transparent input is flattened onto the key color and the
  prompt names that color, so the generated background stays removable.
  `MATTE_NO_BORDER` means the key color is wrong for this video — switch to `rembg`,
  change `--matte-color`, or widen `--matte-tolerance`; do not force it.
- Pixel-art targets: `--scale` (nearest-neighbour, 0.125–8) and `--colors`
  (2–255) reduce the sequence to one **shared** palette without dither, which
  prevents the per-frame colour flicker that independent quantization causes. Both
  are recorded in `frames/meta.json` (`pixel_art`) and applied to every frame on the
  same canvas.
- Machine checks: every frame must have non-zero alpha coverage
  (`metrics.coverage_min > 0`); `metrics.loop_seam_mean_abs_diff` reports cycle
  closure for loop runs (lower is better). A zero-coverage frame is an error, not a
  warning — the alpha strategy or the source video is wrong.

### Phase 7: Verify visually and iterate

Open `contact-sheet.png` and `preview.gif` and check against the request: subject
identity versus the source art, camera lock (background stationary), silhouette
continuity between adjacent frames, loop seam (last frame flows into first), and
clean alpha edges with no background halo. Record pass/fail per item and report any
unverified item explicitly. Completion requires these checks, not merely a
successful download. On revision, change the context and reuse the same character
image; keep prior outputs as separate files and re-apply the Phase 2 cost gate.

**Escalation ladder — never a third text-only retry.** If the same issue (identity
drift, prop leakage, camera motion, wrong silhouette) survives **two** context
adjustments, stop editing text:

1. Change the anchor: a cleaner character image, a flat background for `matte`,
   or explicit appearance description plus negations in the context.
2. Switch route: use `--edit-from` for a localized fix on an otherwise good clip,
   or `--extend-from` when only the tail is wrong, instead of regenerating.
3. If neither applies, report the blocker with the evidence rather than spending
   on another identical attempt.

Ambiguous feedback ("感觉不对") is a question, not a regeneration request: ask what
specifically to change first.

## Core Constraints

- Generated animation is a concept/deliverable asset: this skill never edits engine
  project files, import settings or game code.
- Skeletal (Spine/DragonBones) export is out of scope for this version; see the
  ROADMAP in [references/postprocess.md](references/postprocess.md).

## Recommended Next Steps

- Engine import: hand `manifest.json` + `sprite-sheet.png` to the engine specialist
  or `cs-blender-operator` through the host, with the target paths from Phase 3.
- Skeletal rig: start from the ROADMAP in references/postprocess.md (the 2D/3D
  pose-track comparison report comes first).
- Missing or inconsistent character art: generate it with `cs-game-image-gen`.

## Verification

- [ ] Kind, facing and loop decision resolved; template slots filled (Phases 1, 4)
- [ ] Prompt has no parameter words; entity checklist and negations applied (Phase 4)
- [ ] Cost gate stated with source; resolution and duration explicit (Phase 2)
- [ ] Destination resolved before generation (Phase 3)
- [ ] Task ids preserved; a timed-out poll was resumed, not resubmitted (Phase 5)
- [ ] Edit/extend used only with a valid source URL and duration budget (Phase 5)
- [ ] Machine checks passed: usage vs request, coverage, frame count (Phases 5-6)
- [ ] Visual checks recorded from contact sheet and GIF (Phase 7)
- [ ] Escalation ladder respected: no third text-only retry on the same issue (Phase 7)
