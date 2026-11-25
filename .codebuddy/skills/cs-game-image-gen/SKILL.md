---
name: cs-game-image-gen
description: "Generates game concept art via Qianwen platform Token Plan image models (Wan / Qwen-Image). Branches: character (humanoid/creature/mech), scene and architecture, prop and machine, seamless material textures, and game UI panel/HUD/icon mockups; accepts an optional reference image for subject consistency. / 通过千问平台 Token Plan 图像模型（Wan / Qwen-Image）生成游戏概念图。分支：角色（人形/生物/机甲）、场景与建筑、道具与机械、无缝材质贴图、游戏 UI 面板/HUD/图标；支持参考图保持主体一致性。"
argument-hint: "<prompt> [--model model] [--reference image]"
user-invocable: true
allowed-tools: Read, Bash, Write
---

# Game Image Generation (Qianwen Platform Token Plan)

Generate game concept art, characters, scene elements, material textures and UI mockups
through the bundled `scripts/gen_image.py`. The script wraps three image models
(wan2.7-image-pro / wan2.7-image / qwen-image-3.0-pro) behind one CLI and handles sync
responses, defensive async task polling and result downloading.

## When to Use

- Character concept art: humanoid, creature/monster, mech
- Scene art: environment panoramas, architecture
- Scene elements: props, weapons, machines, vehicles
- Material textures: seamless tileable albedo maps (organic / inorganic / special)
- Game UI: panel mockups, HUD designs, icon sets

Deliver raster concepts and color textures here. Route 3D reconstruction to `cs-img2threejs`
and PBR normal/roughness baking to downstream material tools such as Blender.

## Prerequisites

- Python 3.8+ and Pillow for real image decoding. Install with
  `python -m pip install -r "<skill-dir>/requirements.txt"`; `--dry-run` needs only Python.
- Authentication comes from `ANTHROPIC_AUTH_TOKEN` (the `sk-sp-` Token Plan key, the
  official docs' env name), falling back to `QWEN_API_KEY` then `TOKEN_PLAN_API_KEY`;
  if missing, explain how to set it without echoing or persisting the value. Dry runs
  need no key.
- Default endpoint host is `https://token-plan.maas.qianwenaiapi.com` (Qianwen platform
  Token Plan); override with `QWEN_IMAGE_BASE_URL` (or legacy `QWEN_BASE_URL`, whose
  `/compatible-mode/v1` suffix is stripped). The `sk-sp-` key belongs to that platform;
  the aliyuncs.com Token Plan host is a DIFFERENT platform and rejects this key with 401.
  Read [provider notes](references/provider-notes.md) when configuring a gateway or estimating
  costs/rate limits; the bundled contract is the native `multimodal-generation` API,
  distinct from the OpenAI-compatible Images API.

## Workflow

### Phase 1: Classify and load the template

Map the request to one category and load **only that** template file:

| Category | Subtypes | Template |
|----------|----------|----------|
| character | humanoid / creature / mech | [references/templates/character.md](references/templates/character.md) |
| scene | environment / architecture | [references/templates/scene.md](references/templates/scene.md) |
| element | prop / machine | [references/templates/element.md](references/templates/element.md) |
| texture | organic / inorganic / special | [references/templates/texture.md](references/templates/texture.md) |
| ui | panel / hud / icon | [references/templates/ui.md](references/templates/ui.md) |

Resolve style from the user's request or the project's established art direction. If neither
exists, state a provisional style suited to the game; request clarification only when the
choice materially changes the requested result. Then load [style presets](references/style-presets.md)
when a preset fits; preserve custom styles directly. Style and subtype are independent.
Complete this phase with one category/subtype and an explicit style source or assumption.

### Phase 2: Select the model

| Model | Use when |
|-------|----------|
| `wan2.7-image-pro` | **Default.** Final concept art, reference-based subject consistency, image sets |
| `wan2.7-image` | Iteration drafts and exploration rounds |
| `qwen-image-3.0-pro` | Text-heavy UI mockups and complex layouts |

Honor an explicit user model choice. Choose the total image count and dimensions/aspect ratio
before calling the CLI; `--n` is limited to 1–4 per call. Use exact pixel dimensions when they
are acceptance criteria; `1K`/`2K` are provider presets, not fixed width/height promises.

**Batch cost rule:** before any planned batch of two or more images (including split calls
and planned retries), state the total count, resolution, billing mode and cost estimate with
its source. Read [provider notes](references/provider-notes.md); if Token Plan Credits or
account quotas are unknown, say the estimate is unavailable instead of inventing a price.
Respect the account's actual rate limit and surface HTTP 429; retries are explicit, not automatic.

### Phase 3: Resolve the destination before generation

Reuse an explicit output path; otherwise detect the target project's assets root and choose:

| Engine | Assets root | Output dir |
|--------|------------|------------|
| Unity | `Assets/` | `Assets/Art/AIGenerated/<category>/` |
| Godot / Cocos | `assets/` | `assets/art/ai-generated/<category>/` |
| Unreal | `Content/` | `Content/Art/AIGenerated/<category>/` |

`<category>` is one of `character`, `scene`, `element`, `texture`, `ui`. If no game project
is detectable, ask which project is in play; fall back to `--out generated-images/` in the
workspace only when the user confirms none. Result URLs expire — always keep the downloaded
local files as the deliverable. Finish with the resolved directory for `--out`.

### Phase 4: Compose the prompt

Fill the selected template's required slots. Combine its skeleton, the resolved style and
the user's description; adapt generic defaults/negatives that conflict with the user's facts
or style. Preserve canonical names, colors and lore. Pass the negative prompt via `--negative`.
For image sets, specify each view or icon separately and the features that must stay consistent.

### Phase 5: Generate and check the machine result

```bash
python "<skill-dir>/scripts/gen_image.py" "<prompt>" --model wan2.7-image-pro --size "1024*1024" --n 1 --out "<resolved-output-dir>"
```

- Add `--reference "<local-path-or-URL>"`, `--negative "<negative>"` or `--sequential` as needed.
  Legacy `[model] "<prompt>" [reference_image]` also works; named options avoid ambiguity.
- `--n 2..4 --sequential` is for wan image sets; verify consistency visually in Phase 6.
- Use `--dry-run` before a batch or an unfamiliar parameter combination. It previews the
  gateway payload with local image data omitted, and performs no API call.
- The CLI emits one JSON object (except `--help`), with logs on stderr. Preserve error codes
  and provider messages, redacting credentials. Exit 2 means local/usage failure; exit 3 means
  transport, provider or output-validation failure. Saved files are listed even on partial failure.
- `status: success` means the requested count of PNG/JPEG/WebP files decoded, were saved without
  overwriting existing files, and matched an explicit pixel size when supplied. Each file has
  `{path,url,width,height,format}`; preset dimensions are reported for review. `visual_review`
  remains `pending` until Phase 6. A mismatch is an error; retain usable files and resolve it
  before claiming completion or spending on another request.

### Phase 6: Verify and iterate

Open and inspect every delivered image against the request, then show local image previews.
Record pass/fail for count, dimensions/aspect ratio, required subject details and consistency
across views. For UI, also check actual copy, clipping and icon legibility; for textures,
follow the template's 2x2 tiling check. Report any unverified item explicitly.

Completion requires these checks to pass, not merely a successful download. On revisions,
change the previous prompt and use the prior image as reference when preserving its subject.
Keep new revisions as separate files and follow the Phase 2 batch cost rule for planned retries.

## Core Constraints

- Generated art is a concept deliverable: it does not modify game code or import settings

## Recommended Next Steps

- Concept image → 3D asset: hand the saved file to `cs-img2threejs`
- UI mockup → real UI: extract a spec with `cs-ui-spec-from-image`, build with `cs-ui-generator`
- Texture/mesh integration in an engine project: host dispatches `cs-blender-operator` or the
  engine specialist with the generated files and their target paths

## Verification

- [ ] Category, style source and requested model/count/dimensions resolved (Phases 1–2)
- [ ] Batch cost rule applied when triggered (Phase 2)
- [ ] Destination resolved before generation; prompt matches required slots (Phases 3–4)
- [ ] Machine output validated; errors and partial files accounted for (Phase 5)
- [ ] Visual checks recorded and local previews shown (Phase 6)
