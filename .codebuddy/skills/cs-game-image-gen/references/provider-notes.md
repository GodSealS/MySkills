# Provider contract, pricing and quotas

Official sources (checked 2026-11-18):
- [Token Plan 图像生成接入](https://platform.qianwenai.com/docs/token-plan/best-practices/image-generation)
- [Qwen 同步图像生成 API 参考](https://platform.qianwenai.com/docs/api-reference/image-generation/qwen-text-to-image)

Recheck the account console before quoting a price or quota; these are provider/account
facts, not permanent skill constants.

## Official request contract

```
POST https://token-plan.maas.qianwenaiapi.com/api/v1/services/aigc/multimodal-generation/generation
Authorization: Bearer <sk-sp- Token Plan key>
Content-Type: application/json

{"model": "wan2.7-image-pro",
 "input": {"messages": [{"role": "user",
   "content": [{"image": "<url|data-uri>"}, {"text": "<prompt>"}]}]},
 "parameters": {"size": "1024*1024", "n": 1, "negative_prompt": "...",
                "prompt_extend": true}}
```

- Native `input.messages` envelope — NOT the old aliyuncs compatible-mode
  `chat/completions` + `modalities` gateway contract (removed in the 2026-11-18 migration).
- T2I: `content` is exactly one `{"text": ...}` object. I2I (reference image): 1–3
  `{"image": url|base64}` objects before the text object (DashScope image-edit contract
  family; multi-image order defines 图1/图2…, output ratio follows the last image).
- Token Plan model list: `qwen-image-3.0-pro` (platform default), `qwen-image-2.0-pro` /
  `qwen-image-2.0` (team plan), `wan2.7-image`, `wan2.7-image-pro`. This skill keeps
  `wan2.7-image-pro` as its concept-art default.
- `parameters` (qwen sync API): `size` (宽*高; qwen 3.0/2.1 total pixels 512*512–2048*2048,
  ratio 1:8–8:1; omit for model-recommended), `n` (provider 1–6; wrapper limits 1–4),
  `negative_prompt` (≤500 chars; not supported by qwen-image-2.1 series), `prompt_extend`
  (default true), `prompt_extend_mode` (direct/agent, 3.0/2.1 only), `watermark` (default
  false), `enable_thinking` (default true, only with prompt_extend), `seed`
  (0–2147483647). `1K`/`2K` presets are legacy gateway shorthand — prefer exact pixels.
- `enable_sequential` (wan multi-image consistency sets) is a LEGACY aliyuncs-gateway
  feature, NOT documented on this platform. The CLI still sends it when `--sequential`
  is requested; if the provider rejects it, drop the flag and use reference images for
  consistency instead.

## Official response (sync)

- Images at `output.choices[i].message.content[j].image` — PNG URLs, valid 24 h; download
  promptly. `usage`: qwen-image-3.0 series returns `output_image_count` / `output_width` /
  `output_height` / `input_image_count` + 1k/2k metering tiers (`qima_*`); other series
  return `image_count` / `width` / `height`.
- The endpoint is synchronous. The CLI keeps defensive `/api/v1/tasks/<id>` polling for
  gateways that answer with a `task_id` (the platform also documents separate async
  3.0/2.1 endpoints; not wrapped).

## Hosts and keys — platform matters

| Host | Platform | Key |
|------|----------|-----|
| `token-plan.maas.qianwenaiapi.com` | 千问平台 Token Plan (official docs default) | `sk-sp-` Token Plan key |
| `maas.qianwenaiapi.com` | 千问平台 standard API | standard API key |
| `token-plan.cn-beijing.maas.aliyuncs.com` | 阿里云百炼 Token Plan (different platform) | its own Token Plan key |

Host resolution: `QWEN_IMAGE_BASE_URL`, else legacy `QWEN_BASE_URL` with any
`/compatible-mode/v1` suffix stripped, else the default above. Key resolution:
`ANTHROPIC_AUTH_TOKEN` (official docs' env name, user-designated primary) →
`QWEN_API_KEY` → `TOKEN_PLAN_API_KEY`. A 401 `InvalidApiKey`
means the key is not valid on THAT host — check platform matching before retrying.

**Verification status (2026-11-18, LIVE VERIFIED on the Qianwen host):**
- T2I: `wan2.7-image-pro`, 768*768, n=1 → PNG downloaded, exact dimensions.
- I2I: `qwen-image-3.0-pro` with a local reference image sent as base64 data URI in
  `content[0].image` + edit text → PNG downloaded, exact dimensions.
- Observed model constraint: `wan2.7-image-pro` rejects 512*512 with `InvalidParameter`
  "Total pixels (262144) must be between 589824 and 16777216" — wan2.7 accepts
  768*768 (589,824 px) through 4096*4096 (16,777,216 px). The qwen-image series documents
  512*512–2048*2048. Pick sizes per model.
- `enable_sequential` was NOT exercised by these probes; treat it as unverified here.
The wrapper's 1–4 image limit is not a statement of each model's full capacity.

## Billing and rate limits

| Access mode | How to report cost and pacing |
|-------------|------------------------------|
| Token Plan (the default host) | Uses Credits per output image; consult account usage and quota. Do not translate ordinary API list prices into a fixed Credits or cash charge. |
| Standard Model Studio API | Use the model, region and resolution rates from the current pricing page; qwen-image-3.0 meters 1k/2k tiers by output pixel area (≤2,250,000 px = 1k). |

Apply the batch cost rule in Phase 2 of SKILL.md. The CLI sends one generation request and
does not automatically retry a timed-out or rate-limited submission: a timeout may occur
after provider acceptance. Preserve returned task IDs and downloaded files before retrying.
Surface HTTP 429 and respect the account's actual rate limit.
