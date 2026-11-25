---
name: cs-game-voice-gen
description: "Generates game character voice lines via qwen-audio-3.0-tts-plus (Token Plan) or local Piper: per-line WAV takes with delivery instructions, batch lines.json dubbing and an engine-ready manifest; audition and lock each character voice before batch generation. / 通过 qwen-audio-3.0-tts-plus（Token Plan）或本地 Piper 生成游戏角色配音：逐句 WAV 与演绎指令、批量 lines.json 配音、引擎可用 manifest；批量生成前先试音锁定每个角色的音色。"
argument-hint: "<text> [--voice name] [--lines lines.json] [--backend qwen|piper]"
user-invocable: true
allowed-tools: Read, Bash, Write
---

# Game Voice Generation (qwen-audio-3.0-tts-plus / Piper)

Generate character dialogue, combat barks, narration and UI voice through the bundled
`scripts/gen_voice.py`. One line of text becomes one audio take plus a `manifest.json`
entry, so engines and subtitle systems can address lines by id. Cloud generation uses
the official Qwen-Audio-TTS SpeechSynthesizer API (sync, emotion via `instruction`);
the local Piper backend is offline and zero-cost.

## When to Use

- Character dialogue lines and quest/conversation voiceover
- Combat and reaction barks: attack, hurt, die, skill shout, victory
- Narration: intro, story beats, tutorial, announcer/UI system voice
- Auditioning and locking a character's voice before batch dubbing

Speech only. Route BGM and sound effects to `cs-game-audio-gen`, and video
narration placement/sync to the video editing workflow. Character art goes to
`cs-game-image-gen`, motion to `cs-game-anim-gen`.

## Prerequisites

- Python 3.8+; the qwen backend needs only the standard library. `--dry-run` needs no key.
- Authentication comes from `ANTHROPIC_AUTH_TOKEN` (the `sk-sp-` Token Plan key, the
  official docs' env name), falling back to `QWEN_API_KEY` then `TOKEN_PLAN_API_KEY`.
  Never echo or persist the value.
- Endpoint host: `QWEN_TTS_BASE_URL`, else `https://token-plan.maas.qianwenaiapi.com`.
  The `sk-sp-` key belongs to that platform; the aliyuncs.com Token Plan host is a
  DIFFERENT platform and rejects this key with 401. This is the Qwen-Audio-TTS
  `SpeechSynthesizer` protocol, NOT the chat-completions contract used by
  `cs-game-image-gen`; read [provider notes](references/provider-notes.md) before
  changing hosts or quoting costs.
- Local backend: `python -m pip install piper-tts` plus a voice `.onnx` model; see
  [local models](references/local-models.md). Piper needs no key and no network.

## Workflow

### Phase 1: Classify and build the voice profile

| Kind | Examples | Delivery baseline |
|------|----------|-------------------|
| dialogue | conversation, quest text | character-consistent tone, conversational pace |
| bark | attack/hurt/die/skill shout | short, high-energy, one emotion per take |
| narration | intro, story, tutorial | steady, clear, neutral character bias |
| ui | announcer, system prompts | crisp, consistent across all prompts |

For each speaking character resolve language, gender/age/timbre and a baseline delivery.
Reuse the project's established voice direction; when none exists, propose a voice from
the archetype suggestions in [voices](references/voices.md) and state the assumption.
Finish with one profile per character: voice + baseline instructions.

### Phase 2: Backend, model and the audition gate

| Backend/model | Use when |
|---------------|----------|
| `qwen` + `qwen-audio-3.0-tts-plus` | **Default.** Final takes; instruction-capable system voices (longanlingxin/longanlufeng) |
| `qwen` + `qwen-audio-3.0-tts-flash` | Character voices (child, naughty boy, dialect, haughty female) and cheaper drafts |
| `qwen` + `qwen-audio-3.1-tts-plus` / `-flash` | Newer flagship dramatic voices (`_v3.1`); token-billed; 3.1-flash adds multilingual |
| `piper` + local `.onnx` | Offline/privacy constraints, zero-cost drafts, fallback when the key or quota fails |

Honor an explicit user model choice. Voices are **model-specific ids** — pick from
[voices](references/voices.md) for the selected model; cross-model voices fail with
`InvalidParameter`. Delivery knobs: `--instructions` (emotion/dialect → `input.instruction`),
`--rate`/`--pitch`/`--volume`/`--seed` for bark tuning and reproducible takes.

**Audition gate (mandatory before batch):** for each character voice not yet approved in
this project, generate one signature line (`--name <character>-audition`), let the user
listen, and lock the approved voice + baseline instructions. Never batch-dub a character
with an unapproved voice; one rejected audition is cheaper than fifty rejected lines.

**Batch cost rule:** before any planned batch of two or more paid lines (including split
calls and planned retries), state the line count, total character count and billing mode.
Token Plan spends Credits — read [provider notes](references/provider-notes.md); if the
Credits rate or quota is unknown, say the estimate is unavailable instead of inventing a
price. Retries are explicit, never automatic.

### Phase 3: Resolve the destination before generation

| Engine | Assets root | Output dir |
|--------|------------|------------|
| Unity | `Assets/` | `Assets/Audio/Voice/<character>/` |
| Godot / Cocos | `assets/` | `assets/audio/voice/<character>/` |
| Unreal | `Content/` | `Content/Audio/Voice/<character>/` |

If no game project is detectable, ask which project is in play; fall back to
`--out generated-voice/` in the workspace only when the user confirms none. Provider
audio URLs expire (~24 h) — the downloaded takes and `manifest.json` are the deliverables.
Finish with the resolved directory for `--out`.

### Phase 4: Prepare the lines

One line = one take = one file: engines trigger, subtitle and localize per take. Split
long text at natural pauses or sentence groups; keep each line under ~600 characters.
Write a `lines.json` array for batches:

```json
[
  {"id": "hero_greet_01", "character": "hero", "text": "你终于来了。", "voice": "longanlufeng",
   "instructions": "低沉克制，略带疲惫，语速偏慢"},
  {"id": "hero_bark_attack_01", "character": "hero", "text": "受死吧！", "voice": "longanlufeng",
   "instructions": "爆发性怒吼，短促有力"}
]
```

- `id` and `text` are required; `voice`/`instructions`/`language` fall back to CLI defaults.
  Ids become filenames and manifest keys — make them stable and engine-friendly.
- Delivery direction goes in `instructions` (emotion, pace, tone), never into `text`.
  Parameters (voice name, format, model) never enter the spoken text.
- Keep the character's baseline delivery consistent across lines; vary only the
  per-line emotion the scene requires. Preserve canonical names, terms and lore.
- Duration is an output, not a control: do not promise exact seconds. If a fixed timing
  window is an acceptance criterion, plan local trim/pad downstream instead.

### Phase 5: Generate and check the machine result

```bash
python "<skill-dir>/scripts/gen_voice.py" "<text>" --voice longanlufeng --instructions "<direction>" --character hero --name hero_greet_01 --out "<resolved-output-dir>"
python "<skill-dir>/scripts/gen_voice.py" --lines "<lines.json>" --voice longanlufeng --out "<resolved-output-dir>"
python "<skill-dir>/scripts/gen_voice.py" "<text>" --backend piper --model "<voice.onnx>" --out "<resolved-output-dir>"
```

- Use `--dry-run` before a batch or an unfamiliar parameter combination; it prints the
  payloads/commands and calls nothing.
- The CLI emits one JSON object (except `--help`), logs on stderr, redacts the key.
  Exit 2 = local/usage failure; exit 3 = transport/provider failure. Batch runs continue
  past a failed line and report `status: partial` with per-line errors.
- `status: success` means every requested take decoded as WAV/MP3 with non-zero duration
  (WAV) and was saved without overwriting. `FILE_EXISTS` protects approved takes — use a
  new id or directory for a replacement; delete a rejected take explicitly before reusing
  its id. `manifest.json` merges by id and keeps previously approved entries.
- `audio_review` stays `pending` until Phase 6. A decoding success is not an approval.

### Phase 6: Listen, verify and iterate

The agent cannot hear audio — play the takes for the user (e.g. PowerShell
`(New-Object Media.SoundPlayer "<path>").PlaySync()`) and record their verdict per line:

- Intelligibility and correct pronunciation of names/terms; no clipped or garbled words
- Emotion and pace match the direction; timbre stays consistent across the character's lines
- No clicks, distortion or trailing silence that breaks bark timing
- Duration fits the intended subtitle/UI window when one was specified

Regenerate only rejected lines, changing the instructions or voice — never re-spend on
approved lines. Re-apply the Phase 2 cost gate for planned retries. If the same defect
survives two instruction adjustments, switch voice or backend instead of a third
identical retry. Ambiguous feedback ("感觉不对") is a question: ask what to change first.

## Core Constraints

- Generated voice is a deliverable asset: this skill never edits engine project files,
  import settings or game code.
- Preset voices only in this version; voice cloning is out of scope. Never imitate a real
  person's voice; any future cloning route requires the speaker's explicit consent first.
- Speech only — no BGM or sound-effect generation.

## Recommended Next Steps

- Engine import: hand `manifest.json` + takes to the engine specialist through the host,
  with the target paths from Phase 3; line ids double as subtitle/localization keys.
- Missing character art or animation: `cs-game-image-gen`, `cs-game-anim-gen`.
- Missing BGM or sound effects: `cs-game-audio-gen`.
- Higher-quality offline Chinese or voice design: the VoxCPM2 route in
  [local models](references/local-models.md) (manual install, consent gate for cloning).

## Verification

- [ ] Voice profile per character resolved; audition approved before batch (Phases 1–2)
- [ ] Batch cost rule applied when triggered (Phase 2)
- [ ] Destination resolved before generation; lines split with stable ids (Phases 3–4)
- [ ] Machine output validated; partial failures and protected takes accounted for (Phase 5)
- [ ] Listening verdict recorded per line; only rejected lines regenerated (Phase 6)
