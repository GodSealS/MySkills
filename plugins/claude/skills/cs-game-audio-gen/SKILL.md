---
name: cs-game-audio-gen
description: "Generates game music and sound effects locally via ACE-Step, with an optional reference-audio style guide. Instrumental BGM loops, vocal theme songs and trimmed one-shot SFX, batch tracks.json and an engine-ready manifest; audition before batch. / 通过本地 ACE-Step 生成游戏音乐与音效，支持可选参考音频风格引导：纯音乐 BGM 循环、人声主题曲与裁剪后的一次性音效、批量 tracks.json 与引擎可用 manifest；批量前先试听。"
---

# Game Audio Generation (local ACE-Step)

Generate game BGM, theme songs and sound effects through the bundled
`scripts/gen_audio.py`, a standard-library client for a **local ACE-Step REST API
server** that the user installs and starts themselves. One prompt becomes one audio
asset plus a `manifest.json` entry, so engines can address tracks by id. Generation
runs entirely on the user's GPU — no cloud calls, no per-take fees; the cost is local
GPU time. An optional `--reference-audio` file guides the style of the result.

## When to Use

- Background music: menu/village/dungeon/battle/boss loops, ambient beds, victory/stinger cues
- Theme songs with vocals (lyrics-driven) — resolve the vocal choice first (Phase 1)
- Sound effects: weapon hits, UI clicks, magic, explosions, footsteps, ambient textures
- Style-guided variations: "make a battle version that feels like this reference track"

Music and SFX only. Route character voice to `cs-game-voice-gen`, character art to
`cs-game-image-gen`, motion to `cs-game-anim-gen`. Timeline placement, ducking and
beat-sync belong to the engine/editor, not to generation.

## Prerequisites

- Python 3.8+ for the script (standard library only); `--dry-run` needs no server.
- **Local model weights (startup preflight).** Resolve the ACE-Step install dir
  (`--acestep-home` or `ACESTEP_HOME`, e.g. `F:\Tools\ACE-Step`). Before generating, the
  script checks the weights through ACE-Step's own downloader logic and **downloads
  whatever is missing** (main model: turbo DiT + vae + text encoder + LM 1.7B, plus the
  server-default LM 0.6B). Run `--preflight-only` to do this check/download up front.
  First download is multi-GB and slow; it streams progress to stderr. If the install or
  its `.venv` is absent, the script fails with install instructions instead of guessing.
- A running ACE-Step server (ACE-Step 1.5, MIT-licensed code and weights). Start it in
  its own environment, e.g. on this machine:
  `cd F:\Tools\ACE-Step && .venv\Scripts\python.exe -m acestep.api_server --host 127.0.0.1 --port 8001`
  The script probes `/health`; if the server is down it fails with `SERVER_DOWN` and
  these instructions — start the server, wait for health, then generate. The first
  request loads models (may take minutes); later requests are fast.
- Server address: `--server-url` or `ACESTEP_API_URL`, else `http://127.0.0.1:8001`.
  Optional auth: `ACESTEP_API_KEY` only if the server was started with `--api-key`.
  Never echo or persist the key.
- Hardware/model tiers, install steps and mirrors: [local models](references/local-models.md).
  API contract and verified provider facts: [ACE-Step API](references/acestep-api.md).

## Workflow

### Phase 1: Classify the asset and resolve the vocal choice

| Kind | Examples | Defaults |
|------|----------|----------|
| music | BGM loop, ambient bed, theme song, stinger | instrumental, 30 s, mp3 |
| sfx | hit/UI/magic/footstep one-shots, ambient textures | instrumental, 10 s generated → trim, wav |

For music, resolve vocals before any other creative detail: BGM/loop/bed requests are
instrumental by default; a "song"/"主题曲" request that does not specify vocals gets one
binary question first — "要带人声的歌曲，还是纯音乐配乐？" / "A vocal song or instrumental
music?" — and nothing else that turn. Never route an ordinary BGM request to vocal
generation. For explicit vocals, write or collect lyrics with structure tags
(`[Verse]`/`[Chorus]`...) before generating; preserve user-supplied lyrics as-is.

### Phase 2: Backend readiness, reference audio and the audition gate

**Readiness first:** resolve `--acestep-home`/`ACESTEP_HOME`, then run
`python "<skill-dir>/scripts/gen_audio.py" --preflight-only --acestep-home "<dir>"`.
It checks the local weights and downloads any that are missing before you spend GPU
time; it also reports whether the server is up. If it reports the server down, start the
server (Prerequisites) and re-probe. Generation repeats this preflight automatically, so
a missing model is fetched on demand rather than failing mid-task.

`--reference-audio <path>` is optional. When present, the file is uploaded to the local
server and guides the **style** of the result (timbre/arrangement feel), not a melody
copy; `--cover-strength` (0.0–1.0, default 0.2) controls the influence. Resolve first:

- Rights: the reference must be user-owned, licensed, or a previously generated take.
  Do not use copyrighted recordings to imitate a named artist's track; say no and offer
  a text-described style instead.
- Content: an audible file (wav/mp3/flac/ogg...); silence is rejected by the server.
  Any length works — the server samples front/middle/back segments.
- Expectation: style transfer changes the palette, not the composition. If the user
  wants the same melody re-arranged, that is a cover/edit task outside this wrapper.

**Audition gate (mandatory before batch):** for each new style/direction not yet
approved in this project, generate one signature track (`--name <style>-audition`),
play it for the user, and lock the approved prompt direction. Never batch a whole
soundtrack with an unapproved direction.

**Batch cost rule:** local generation is free of charge but spends GPU time. Before any
batch of two or more tracks, state the track count, total requested duration and that
generation is local (approximate time from the server's `/v1/stats` average if useful).
Retries are explicit, never automatic.

### Phase 3: Resolve the destination before generation

| Engine | Assets root | Music dir | SFX dir |
|--------|------------|-----------|---------|
| Unity | `Assets/` | `Assets/Audio/Music/` | `Assets/Audio/SFX/` |
| Godot / Cocos | `assets/` | `assets/audio/music/` | `assets/audio/sfx/` |
| Unreal | `Content/` | `Content/Audio/Music/` | `Content/Audio/SFX/` |

If no game project is detectable, ask which project is in play; fall back to
`--out generated-audio/` in the workspace only when the user confirms none. The
downloaded files and `manifest.json` are the deliverables (server temp files are
cleaned up). Finish with the resolved directory for `--out`.

### Phase 4: Prepare the tracks

Write prompts with the shapes in [prompts](references/prompts.md): music = genre +
instrumentation + energy/mood + tempo + game role + loop constraint; SFX = source +
action + material/space + perspective + "no music, no melody". Use `--bpm`/`--key` for
music when the project has a tempo/key plan; duration is 10–600 s (provider limit).
SFX shorter than 10 s: generate 10 s and cut the one-shot with `--trim-start/--trim-end`
(WAV only). Write a `tracks.json` array for batches:

```json
[
  {"id": "menu_theme_01", "kind": "music", "prompt": "calm fantasy village menu theme, ...",
   "duration": 30, "bpm": 90, "key": "C Major"},
  {"id": "sword_clash_01", "kind": "sfx", "prompt": "single sharp sword clash metal hit, ...",
   "duration": 10, "trim_start": 0, "trim_end": 2},
  {"id": "battle_theme_01", "kind": "music", "prompt": "intense battle variation, ...",
   "duration": 30, "bpm": 140, "reference_audio": "refs/menu_theme_01.mp3", "cover_strength": 0.2}
]
```

- `id` and `prompt` are required; everything else falls back to CLI defaults. Ids become
  filenames and manifest keys — stable and engine-friendly.
- One track = one take; variants are separate tracks with distinct ids, never silent
  parallel spends. Lyrics go in `lyrics` (music only), never into the prompt.
- Looping is a downstream concern: the model does not guarantee seamless loop points.
  Plan to audition the seam and trim/crossfade in the engine or an audio editor.

### Phase 5: Generate and check the machine result

```bash
python "<skill-dir>/scripts/gen_audio.py" --preflight-only --acestep-home "<ACE-Step dir>"
python "<skill-dir>/scripts/gen_audio.py" "<prompt>" --kind music --duration 30 --bpm 90 --name menu_theme_01 --out "<resolved-dir>"
python "<skill-dir>/scripts/gen_audio.py" "<prompt>" --kind sfx --trim-start 0 --trim-end 2 --name sword_clash_01 --out "<resolved-dir>"
python "<skill-dir>/scripts/gen_audio.py" "<prompt>" --reference-audio "<ref.wav>" --cover-strength 0.2 --name battle_theme_01 --out "<resolved-dir>"
python "<skill-dir>/scripts/gen_audio.py" --tracks "<tracks.json>" --out "<resolved-dir>"
```

- With `--acestep-home`/`ACESTEP_HOME` set, every generation run first checks the local
  weights and downloads any that are missing (result carries a `preflight` report).
  Without it, the preflight is skipped with a warning and the server alone is probed.
- Use `--dry-run` before a batch or an unfamiliar parameter combination; it prints the
  request payloads and calls nothing (no preflight, no server).
- The CLI emits one JSON object (except `--help`), logs on stderr, redacts the key.
  Exit 2 = local/usage failure; exit 3 = server/generation failure. Batch runs continue
  past a failed track and report `status: partial` with per-track errors.
- `status: success` means every requested take decoded (WAV fully, MP3 sniffed) and was
  saved without overwriting. WAV deliverables are normalized to 16-bit PCM (the provider
  writes float WAV). `FILE_EXISTS` protects approved takes — use a new id or directory
  for a replacement; delete a rejected take explicitly before reusing its id.
  `manifest.json` merges by id and keeps previously approved entries.
- `audio_review` stays `pending` until Phase 6. A decoding success is not an approval.

### Phase 6: Listen, verify and iterate

The agent cannot hear audio — play the takes for the user (e.g. PowerShell
`(New-Object Media.SoundPlayer "<path>").PlaySync()`) and record their verdict per track:

- Music: mood/energy fits the scene; instrumentation matches the direction; tempo and
  key fit the project plan; loop seam acceptable or flagged for downstream editing;
  vocals (if any) pronounce names/terms correctly.
- SFX: the transient reads as the intended action; no musical bed leaking into a
  one-shot; trim window captures the hit without dead air; loudness consistent across
  the same family of effects.
- Reference-guided tracks: the palette resembles the reference without copying it.

Regenerate only rejected tracks, changing the prompt/strength/seed — never re-spend on
approved tracks. Re-apply the Phase 2 cost gate for planned retries. If the same defect
survives two prompt adjustments, change direction (different instrumentation wording,
strength, or seed) instead of a third identical retry. Ambiguous feedback ("感觉不对")
is a question: ask what to change first.

## Core Constraints

- Generated audio is a deliverable asset: this skill never edits engine project files,
  import settings or game code.
- Local-only generation through the user's ACE-Step server; no cloud fallback.
- New original assets only: no remixing, cleaning up, separating or replacing existing
  recordings; reference audio guides style, it is not a source to reproduce.
- No exact beat/loop-point/timestamp guarantees — placement, trimming, looping, fades
  and ducking happen downstream in the engine or an audio editor.
- Do not imitate a named living artist; reference audio requires rights (Phase 2).

## Recommended Next Steps

- Engine import: hand `manifest.json` + files to the engine specialist through the host,
  with the target paths from Phase 3; track ids double as audio-event keys.
- Character voice lines: `cs-game-voice-gen`. Missing art or animation:
  `cs-game-image-gen`, `cs-game-anim-gen`.
- Higher-quality SFX or longer beds: the optional Stable Audio Open route in
  [local models](references/local-models.md) (gated weights, manual setup).

## Verification

- [ ] Asset kind classified; vocal choice resolved before creative details (Phase 1)
- [ ] Model preflight run: weights present or downloaded; server up (Phase 2)
- [ ] Reference audio rights/semantics resolved; audition approved before batch (Phase 2)
- [ ] Batch cost rule applied when triggered (Phase 2)
- [ ] Destination resolved before generation; tracks prepared with stable ids (Phases 3–4)
- [ ] Machine output validated; partial failures and protected takes accounted for (Phase 5)
- [ ] Listening verdict recorded per track; only rejected tracks regenerated (Phase 6)