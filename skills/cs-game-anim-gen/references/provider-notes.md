# Provider contract, pricing and quotas (wan3.0-video)

Read when configuring the gateway, estimating a run or diagnosing rate limits.
Official source: [Token Plan 视频生成接入](https://platform.qianwenai.com/docs/token-plan/best-practices/video-generation),
checked 2026-11-18. Live probe: 2026-11-16 against the aliyuncs Token Plan host
(contract shape identical to the official docs); migrated to the Qianwen platform
host 2026-11-18. Recheck the linked sources and the account console before quoting
a price or quota; these are provider/account facts, not permanent skill constants.

## Endpoints (Token Plan, `sk-sp-` key)

| Purpose | Method + URL |
|---------|--------------|
| Submit task | `POST https://token-plan.maas.qianwenaiapi.com/api/v1/services/aigc/video-generation/video-synthesis` |
| Query task | `GET https://token-plan.maas.qianwenaiapi.com/api/v1/tasks/{task_id}` |

Required headers: `Authorization: Bearer <key>`, `Content-Type: application/json`,
and `X-DashScope-Async: enable` on submission (without it the API rejects the call
with "current user api does not support synchronous calls").

**Platform matters:** the `sk-sp-` key belongs to the Qianwen platform host above.
`token-plan.cn-beijing.maas.aliyuncs.com` is the Aliyun Bailian Token Plan — a
DIFFERENT platform whose keys are not interchangeable (401 `InvalidApiKey` across
hosts). Host override: `QWEN_VIDEO_BASE_URL` only; the CLI no longer derives the
host from `QWEN_BASE_URL`. Key resolution: `ANTHROPIC_AUTH_TOKEN` (official docs' env
name, user-designated primary) → `QWEN_API_KEY` → `TOKEN_PLAN_API_KEY`.

Both generation skills now use the native `api/v1` protocol family on this host:
image posts synchronous `multimodal-generation/generation`, video posts async
`video-generation/video-synthesis` with the task loop below.

## Request body (verified live)

```json
{
  "model": "wan3.0-video",
  "input": {
    "prompt": "<locked-camera envelope + context>",
    "media": [{"type": "first_frame", "url": "<url|oss://|data:image/png;base64,...>"}]
  },
  "parameters": {
    "resolution": "480P", "ratio": "adaptive", "duration": 3,
    "audio": false, "prompt_extend": true, "watermark": false
  }
}
```

- `model`: `wan3.0-video` (standard) or `wan3.0-video-prime` (faster, same capability).
- `input.prompt` and `input.media`: at least one required; prompt max 20,000 chars.
- `media[].type`: `first_frame` (max 1), `last_frame` (max 1), `reference_image`
  (max 10), `reference_video` (max 5, total <= 15 s), `reference_audio` (max 5,
  total <= 15 s), `file` (max 1), `link` (max 1). `first_frame`/`last_frame` are
  mutually exclusive with every `reference_*` type; `file` and `link` are mutually
  exclusive. Sending the same image as `first_frame` + `last_frame` forces the
  motion to close into a seamless cycle — the basis of this skill's loop mode.
- Image input limits: JPEG/JPG/PNG/BMP/WEBP, **transparent channel not supported**
  (the CLI flattens alpha onto `--flatten-color`), 240-8000 px per side, aspect
  <= 8:1, <= 20 MB. Base64 data URIs are accepted by the Token Plan host (probe
  payload 0.9 MB succeeded).
- `parameters.resolution`: `480P` / `720P` / `1080P`, API default **1080P** — the
  CLI always sends an explicit tier and defaults to 480P.
- `parameters.ratio`: `adaptive` (default), `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`.
- `parameters.duration`: integer seconds, [2, 30] without video input (probe
  confirmed 2 s); `-1` = model-chosen. With video input, input + output <= 30 s.
- `parameters.audio`: default **true**; the CLI defaults it off because game
  sprites rarely need an audio track. Toggling does not change price.
- `parameters.prompt_extend`: default true (LLM rewrite; adds latency).
- `parameters.watermark`: default false. `parameters.seed`: -1 or [0, 2147483647].

## Response and task lifecycle (verified live)

- Submission returns `output.task_id` + `output.task_status` (`PENDING`).
- Polling returns `output.task_status` in
  `PENDING | RUNNING | SUCCEEDED | FAILED | CANCELED | UNKNOWN`; on success
  `output.video_url` (MP4/H.264) plus `usage{video_count, duration,
  input_video_duration, output_video_duration, fps, SR, ratio}`.
- Probe observation (2026-11-16, aliyuncs host): 2 s / 480P / 1:1 job took 52 s
  end-to-end with 10 s polling; output was 640x640 @ 30 fps (60 frames), i.e. the 480P
  tier maps to 640 px per side for a 1:1 ratio. Treat tier->pixel mapping as observed,
  not promised.
- Probe observation (2026-11-18, Qianwen host): 3 s / 480P / 1:1 loop job with base64
  `first_frame` + `last_frame` (768x768 source) SUCCEEDED after 6 polls at 10 s;
  usage `SR=480, fps=30, duration=3.0`. The async protocol and base64 frame slots are
  live-verified on this host.
- `task_id` and `video_url` are valid for 24 hours; download promptly. Query RPS
  limit is 20; poll no faster than ~10 s.

## Billing and rate limits

| Access mode | How to report cost and pacing |
|-------------|------------------------------|
| Token Plan (the default host) | Spends Credits per output second; consult account usage. Do not translate list prices into a fixed Credits or cash charge. |
| Standard Model Studio API | Per the model page: Beijing list price 480P 0.3, 720P 0.6, 1080P 1.2 CNY per output second (wan3.0-video; promotional discounts appear in the console and change). Input/output video seconds both count when video is supplied. |

Model page states RPM 300 for wan3.0-video. Apply the Phase 2 cost gate in SKILL.md:
state duration x resolution x rate with its source before any paid run, and surface
HTTP 429 instead of retrying silently. A timed-out poll may still succeed server-side;
keep the task id and query it again before resubmitting.

## Edit and extend (`reference_video`)

The same endpoint supports revising an existing clip; the CLI exposes it as
`--edit-from` / `--extend-from`:

- Media: one `reference_video` entry. Frame slots (`first_frame`/`last_frame`) and
  reference slots are **mutually exclusive**, so edit/extend send no character image.
- `reference_video` accepts a **public HTTP(S) URL or an `oss://` temporary URL only**
  — not base64. Limits: mp4/mov, 1–15 s per clip, ≤15 s total, ≥16 fps, 240–4096 px
  per side, aspect ≤8:1, ≤100 MB per clip. The CLI therefore resolves a local MP4
  through the `<file>.mp4.source.json` sidecar written at download time (it records
  the provider URL, valid 24 h) and fails with `SOURCE_URL_REQUIRED` otherwise.
- Edit convention used by the CLI: `ratio: "adaptive"`, `duration: -1` (inherit /
  model-chosen timing). Extend convention: `ratio: "adaptive"`, `duration` = the
  requested extension seconds, with input + output ≤ 30 s enforced locally when the
  source duration can be probed.
- Prompt intent decides edit vs extend upstream: use explicit "只修改…其余保持不变"
  wording for edit and "向前/向后延长…" for extend. The CLI prepends those contracts.

## Async task records

`--submit-only` writes `task-<id>.json` (schema `cs-game-anim-gen/task@1`) with the
task id, model, mode, parameters and a ready-to-run resume command; `--task-id`
polls and downloads without resubmitting. Each download writes
`<file>.mp4.source.json` (schema `cs-game-anim-gen/video-source@1`) holding the
signed result URL. The signed URL is deliberately kept out of stdout JSON.

## Known gaps

- The Token Plan video documentation only shows a text-to-video example; image-input
  acceptance (`first_frame`/`last_frame` base64) is established by live probes on both
  hosts (2026-11-16 aliyuncs, 2026-11-18 Qianwen), not by that page. Re-probe after any
  gateway change.
- `wan3.0-video-prime` was not exercised by the probe; treat it as documented-only.
- **Edit/extend are contract-covered offline but not live-verified.** The
  `duration: -1` edit convention, Token Plan acceptance of `reference_video`, and
  whether an edit truly inherits source timing need one cheap live probe before
  being treated as established. Until then, report them as documented behavior.
- Local duration probing depends on an available decoder metadata path; when it
  cannot probe, the 1–15 s and 30 s budgets are enforced only by the provider.
