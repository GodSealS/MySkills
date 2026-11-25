# ACE-Step local API contract and verified facts

Source: `docs/en/API.md` of the ACE-Step 1.5 install (checked 2026-11-19 against
`F:\Tools\ACE-Step`), plus live verification on this machine (RTX 3080 10 GB,
`acestep-v15-turbo` + `acestep-5Hz-lm-0.6B`). Server default: `http://127.0.0.1:8001`.

## Workflow

1. `GET /health` → `data.status == "ok"`; `models_initialized`/`llm_initialized`
   may be false (lazy load on first request — not an error).
2. `POST /release_task` → `data.task_id`. JSON body, or multipart/form-data when
   uploading reference audio. **The first call can block for minutes while models
   load** — the wrapper uses a 300 s submit timeout, separate from polling.
3. `POST /query_result` `{"task_id_list": ["<id>"]}` → `data[].status`:
   `0` queued/running, `1` succeeded, `2` failed. `result` is a **JSON string**;
   parse it to a list of outputs with `file`, `metas`, `seed_value`, `dit_model`,
   `lm_model`.
4. `GET /v1/audio?path=<urlencoded>` → audio bytes. `file` in the result is a
   relative URL (`/v1/audio?path=...`); join it with the server base.

All responses are wrapped: `{"data": ..., "code": 200, "error": null, ...}`.
Auth (only if the server was started with `--api-key`): `Authorization: Bearer <key>`
or `ai_token` in the body. The wrapper reads `ACESTEP_API_KEY`.

## release_task fields used by the wrapper

| Field | Value | Notes |
|-------|-------|-------|
| `prompt` | text | music/SFX description (alias `caption`) |
| `lyrics` | text | empty / `[Inst]` / `[Instrumental]` = instrumental; structure tags for vocals |
| `task_type` | `text2music` | reference audio works with text2music; `cover` needs `src_audio` and locks duration to it — not used |
| `audio_duration` | 10–600 | seconds; provider hard limit |
| `bpm` | 30–300 | optional |
| `key_scale` | e.g. `C Major`, `Am` | optional |
| `time_signature` | `2`/`3`/`4`/`6` | optional |
| `audio_format` | `wav`/`mp3` | provider also offers flac/opus/aac/wav32; wrapper validates wav/mp3 only |
| `batch_size` | `1` | one take per track; variants are separate requests |
| `inference_steps` | 8 | turbo 1–20; base 1–200 |
| `seed` + `use_random_seed=false` | int | reproducible takes; default random |
| `thinking` | bool | LM code planning; LM auto-skipped for cover/repaint/extract |
| `vocal_language` | `en`/`zh`/... | optional hint |
| `audio_cover_strength` | 0.0–1.0 | only with reference audio; ~0.2 = style transfer |

Reference audio upload (multipart): file part named `reference_audio` (or `ref_audio`);
uploaded files override any `reference_audio_path` field. JSON-only callers can pass
`reference_audio_path` as an absolute path **on the server host**. The server decodes
any audible audio (wav/mp3/flac/ogg...), normalizes to stereo 48 kHz and samples 3×10 s
segments; silent/unreadable files fail the task with "Invalid reference audio".

## Verified provider facts (2026-11-19, live on this machine)

- **WAV output is IEEE float (fmt tag 3)** for both `wav` and `wav32` — Python's
  `wave` module cannot read it ("unknown format: 3"). The wrapper converts float32 →
  16-bit PCM before probing/trimming/saving, so deliverables are engine-friendly PCM.
- MP3 output: ~30 s ≈ 480 KB; duration is not probed by the wrapper (MP3 sniff only),
  but `metas.duration` in the result reports the requested duration.
- `metas` echoes bpm/duration/keyscale/timesignature; the LM (0.6B) fills metadata even
  with `thinking=false` (server-side CoT defaults on).
- Instrumental BGM (30 s, bpm/key pinned), SFX (10 s → 2 s trim, 48 kHz stereo WAV) and
  reference-guided style transfer (uploaded MP3 reference, strength 0.2) all generated
  successfully; server log confirms "Processing reference audio..." with the decoded
  reference shape.
- A client-side submit timeout does **not** cancel the server task; it keeps running.
  Query before resubmitting to avoid duplicate GPU spend.

## Error handling

| HTTP | Meaning | Wrapper behavior |
|------|---------|------------------|
| 400 | invalid params | `API_ERROR` with server detail |
| 401 | server requires a key | `API_ERROR` + set `ACESTEP_API_KEY` hint |
| 429 | queue full | `API_ERROR` + wait hint |
| 500/503 | server error/overload | `API_ERROR`; retry explicitly |
| conn refused | server down | `SERVER_DOWN` + start instructions (exit 3) |
| task status 2 | generation failed | `GENERATION_FAILED` with result detail |
| poll budget spent | still running | `POLL_TIMEOUT`; task may finish server-side |

Exit codes: 0 success; 2 usage/local (`INVALID_*`, `FILE_EXISTS`, `EMPTY_PROMPT`,
`REFERENCE_NOT_FOUND`, ...); 3 server/generation (`SERVER_DOWN`, `NETWORK_ERROR`,
`API_ERROR`, `GENERATION_FAILED`, `POLL_TIMEOUT`, `DOWNLOAD_FAILED`, `INVALID_RESPONSE`,
`INVALID_AUDIO`).