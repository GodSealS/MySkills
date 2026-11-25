# Provider contract, pricing and quotas

Official sources (checked 2026-11-18):
- [Token Plan 语音合成接入](https://platform.qianwenai.com/docs/token-plan/best-practices/speech-synthesis)
- [Qwen-Audio-TTS HTTP API 参考](https://platform.qianwenai.com/docs/api-reference/speech-synthesis/qwen-audio-tts/http-api)
- [Qwen-Audio-TTS 音色列表](https://platform.qianwenai.com/docs/developer-guides/speech/voice-list/qwen-audio-tts)

Recheck the account console before quoting a price or quota; these are provider/account
facts, not permanent skill constants.

## Official request contract

```
POST https://token-plan.maas.qianwenaiapi.com/api/v1/services/audio/tts/SpeechSynthesizer
Authorization: Bearer <sk-sp- Token Plan key>
Content-Type: application/json

{"model": "qwen-audio-3.0-tts-plus",
 "input": {"text": "...", "voice": "longanlingxin",
           "format": "wav", "sample_rate": 24000,
           "instruction": "请用惊恐颤抖的语气说",
           "rate": 1.0, "pitch": 1.0, "volume": 50, "seed": 0}}
```

- Everything lives in `input` — there is no `parameters` object on this API.
- `input.instruction` (singular) controls dialect/emotion/character delivery; the voice
  must support instruction control (see [voices.md](voices.md)).
- Optional `input` fields and ranges: `format` mp3 (provider default) / pcm / wav / opus;
  `sample_rate` 8000/12000/16000/22050 (default)/24000/44100/48000 (opus restricts the
  set); `volume` 0–100 (default 50); `rate` 0.5–2.0 (default 1.0); `pitch` 0.5–2.0
  (default 1.0); `seed` 0–65535 (reproducible takes); `bit_rate` (opus only).
- Provider features NOT wrapped by the CLI (documented, call the API directly if needed):
  SSML (`enable_ssml`), LaTeX input, `hot_fix` pronunciation/replace (useful for lore
  names), `language_hints` (3.1-flash multilingual/dialect voices), streaming
  (`X-DashScope-SSE: enable`), word timestamps, AIGC watermark tags.
- The wrapper requests `wav` by default and validates wav/mp3 only; pcm/opus are not
  wrapped because the local decoder check cannot verify them.

## Official response (sync, no task protocol)

```json
{"request_id": "...",
 "output": {"finish_reason": "stop",
            "audio": {"data": "", "url": "https://.../xxx.wav",
                      "id": "audio_...", "expires_at": 1772697707}},
 "usage": {"characters": 15}}
```

- `output.audio.url` is valid 24 h (`expires_at` epoch); download immediately — the local
  take is the deliverable. `output.audio.data` carries base64 only in streaming mode.
- There is no `task_id`/polling on this endpoint; earlier bundled drafts assumed the
  multimodal-generation task protocol — that was wrong for TTS and has been removed.

## Hosts and keys — platform matters

| Host | Platform | Key |
|------|----------|-----|
| `token-plan.maas.qianwenaiapi.com` | 千问平台 Token Plan (official docs default) | `sk-sp-` Token Plan key |
| `maas.qianwenaiapi.com` | 千问平台 standard API | standard API key (`DASHSCOPE_API_KEY` style) |
| `token-plan.cn-beijing.maas.aliyuncs.com` | 阿里云百炼 Token Plan (different platform) | its own Token Plan key |

The CLI resolves the host from `QWEN_TTS_BASE_URL`, else defaults to
`token-plan.maas.qianwenaiapi.com`. It does NOT derive the host from `QWEN_BASE_URL`
(that variable points at the image gateway, potentially on the other platform).
Key resolution: `ANTHROPIC_AUTH_TOKEN` (the env name used by the official Token Plan
docs, user-designated primary) → `QWEN_API_KEY` → `TOKEN_PLAN_API_KEY`. A 401 `InvalidApiKey` means the key is not
valid on THAT host — check platform matching and key validity before retrying.

**Verification status (2026-11-18, LIVE VERIFIED on the Qianwen host):**
`qwen-audio-3.0-tts-plus` + `longanlingxin` + emotion `instruction` generated a 6.8 s
panic line (24000 Hz mono WAV); `usage` returned `characters` plus token counts. Two
observed facts: (1) the provider WAV is stream-written — its header claims a placeholder
frame count (observed: 44739 s for a 6.8 s take); the CLI clamps duration to the frames
actually present. (2) The default sample rate for this model was 24000, not the documented
22050 — always read the probed value. Earlier that day, the stale 122-char environment key
returned 401 on ALL hosts/paths; the valid key is the machine-scope `ANTHROPIC_AUTH_TOKEN`
(116-char). If 401 reappears, check which key the resolution chain picked before blaming
the endpoint. The local Piper backend is also live-verified (see
[local-models.md](local-models.md)).

## Billing and rate limits

| Model family | Billing |
|--------------|---------|
| `qwen-audio-3.0-tts-plus` / `-flash`, `qwen-audio-3.1-tts-plus` | per input character (`usage.characters`) |
| `qwen-audio-3.1-tts-flash` | per input+output tokens (`usage.*_tokens`) |

Token Plan spends plan quota/Credits — consult the
[console usage stats](https://platform.qianwenai.com/home/analytics/token-plan/individual);
do not translate list prices into a fixed Credits or cash figure. Apply the batch cost
rule in Phase 2 of SKILL.md: line count x total characters x billing mode, with its source.

The CLI sends one request per line, sequentially, and never retries automatically.
Preserve saved takes and the manifest before retrying; regenerate only failed line ids.
Surface HTTP 429 and respect the account's actual rate limit (not documented on the
best-practice page; check the console).

## Output facts

- Voice/model mismatch returns `InvalidParameter` (e.g. `[cosyvoice:]Engine error [411]`)
  — resolve via the matching rules in [voices.md](voices.md), not by guessing ids.
- WAV takes report `duration_seconds`, `sample_rate`, `channels`; MP3 takes report format
  only (duration null) — measure downstream if timing matters.
- The manifest records `source_url` + `source_url_expires_at` for short-term reuse only.
