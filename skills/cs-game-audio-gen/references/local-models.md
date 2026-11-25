# Local backend: ACE-Step 1.5

Official sources (checked 2026-11-19):
- [ACE-Step 1.5 repo](https://github.com/ACE-Step/ACE-Step-1.5) (local install docs: `docs/en/INSTALL.md`, `docs/en/API.md`)
- [Weights](https://huggingface.co/ACE-Step/Ace-Step1.5) / [ModelScope mirror](https://modelscope.cn/models/ACE-Step/Ace-Step1.5)
- [Project page](https://ace-step.github.io/ACE-Step-1.5/en)

## License

ACE-Step 1.5 code and model weights are **MIT-licensed**; the project states generated
output is cleared for commercial use. Recheck the weight card before shipping a
commercial title — provider facts can change. The optional Stable Audio Open route
below has a different, more restrictive license.

## Install and start the server

The script talks to a local REST server; it never imports torch itself.

```powershell
git clone https://github.com/ACE-Step/ACE-Step-1.5.git
cd ACE-Step-1.5
uv sync          # creates .venv (Python 3.11-3.12, CUDA torch)
# start the API server (models auto-download on first run):
.venv\Scripts\python.exe -m acestep.api_server --host 127.0.0.1 --port 8001
```

- The bundled `start_api_server.bat` also works but is interactive (update prompts);
  the direct `python -m acestep.api_server` command is script-friendly.
- First request loads DiT + VAE (+ LM) and can take minutes; the script allows 300 s
  for submission and polls up to `--timeout` (default 900 s). `/health` reports
  `models_initialized` — false means lazy loading is still pending, not an error.
- Download source: `--download-source modelscope` when Hugging Face is slow/blocked;
  `HF_ENDPOINT=https://hf-mirror.com` is the usual mirror override.
- Optional auth: start with `--api-key <key>` and set `ACESTEP_API_KEY` for the script.
- Verified instance on this machine (2026-11-19): `F:\Tools\ACE-Step` with
  `.venv` (Python 3.12, torch 2.7.1+cu128), weights in `checkpoints\`
  (`acestep-v15-turbo`, `acestep-5Hz-lm-0.6B`, `acestep-5Hz-lm-1.7B`, `vae`).

## Startup model preflight (check + auto-download)

`gen_audio.py` checks the weights before generating whenever the install home is known
(`--acestep-home` or `ACESTEP_HOME`); `--preflight-only` runs just this check plus a
server health probe. The check delegates to ACE-Step's own downloader logic (no
reimplemented file heuristics):

- Required: the **main model** components — `acestep-v15-turbo` (DiT), `vae`,
  `Qwen3-Embedding-0.6B` (text encoder), `acestep-5Hz-lm-1.7B` — plus the server-default
  LM `acestep-5Hz-lm-0.6B`. A component counts as present when its directory holds a
  weights artifact (`model.safetensors`, `*.index.json`, `pytorch_model.bin`, ...).
- Missing weights are fetched with the bundled downloader inside the ACE-Step env:
  `python -m acestep.model_downloader` (main model) and
  `python -m acestep.model_downloader --model acestep-5Hz-lm-0.6B --skip-main` (default LM).
  It auto-detects the network and falls back between HuggingFace and ModelScope; set
  `HF_ENDPOINT=https://hf-mirror.com` to force a mirror. Progress streams to stderr;
  `--download-timeout` (default 3600 s) bounds each invocation. Partial downloads are
  kept, so a rerun resumes.
- Checkpoints location follows ACE-Step: `ACESTEP_CHECKPOINTS_DIR` (shared across
  installs) else `<home>/checkpoints`. The preflight reports the resolved path.
- If the home or its `.venv`/`python_embedded` interpreter is missing, the script fails
  with `ACESTEP_NOT_INSTALLED` + install instructions; it does not auto-install ACE-Step.
- Without a home, generation skips the preflight with a warning (the server `/health`
  probe still applies) — useful when the server is managed elsewhere.

## Model zoo and VRAM tiers

DiT (audio decoder) + optional 5Hz LM (planner: lyrics/codes/metadata CoT).

| GPU VRAM | DiT | LM | Notes |
|----------|-----|----|-------|
| ≤6 GB | 2B turbo | none | DiT-only, INT8 + CPU offload |
| 6–8 GB | 2B turbo | 0.6B | `pt` LM backend |
| 8–16 GB | 2B turbo/sft | 0.6B (8–12) / 1.7B (12–16) | **RTX 3080 10 GB sits here** |
| 16–24 GB | 2B sft / XL turbo | 1.7B | XL needs offload below 20 GB |
| ≥24 GB | XL sft | 4B | best quality |

- `acestep-v15-turbo`: 1–20 diffusion steps (default 8), fast; supports
  `text2music`, `repaint`, `cover`. This wrapper only uses `text2music` (+ reference
  audio style guidance), which every DiT supports.
- `acestep-v15-base`/`sft`: up to 200 steps, `guidance_scale` effective; adds
  `extract`/`lego`/`complete` tasks (not wrapped).
- XL (4B) variants: higher quality, ≥12 GB VRAM with offload — not for the 3080.
- `--thinking` enables LM code planning (needs an LM loaded); metadata CoT
  (`use_cot_caption`, server default on) already uses the LM when available.
- Low VRAM: `ACESTEP_OFFLOAD_TO_CPU=true` when starting the server.

## Capability facts that shape the workflow

- Duration is **10–600 s** per generation. Game one-shot SFX are shorter: generate
  10 s and trim locally (`--trim-start/--trim-end`, WAV only).
- ACE-Step is a **music foundation model**. SFX come from texture/instrument
  understanding (impacts, whooshes, magic, ambience work well); precise foley
  (dry UI clicks, specific footsteps) may read musical — audition and iterate, or
  use the Stable Audio Open route below.
- Reference audio = **style transfer** (`audio_cover_strength` ~0.2), not melody
  copy or continuation; duration stays controllable. The server samples 3×10 s
  segments (front/middle/back) from any audible file.
- No seamless-loop guarantee; loop seams are auditioned and fixed downstream.
- Vocals: 50+ languages via lyrics + `vocal_language`; quality is song-grade, not
  dialogue-grade — character voice lines belong to `cs-game-voice-gen`.

## Optional upgrade: Stable Audio Open for dedicated SFX

`stabilityai/stable-audio-open-1.0` (diffusers `StableAudioPipeline`) is trained for
sound effects/field recordings, up to 47 s, 44.1 kHz stereo. **Not bundled in v1**:

- Weights are **gated** on Hugging Face: the user must accept the license on the model
  page and provide an HF token; ~4 GB+ download.
- License: Stability AI Community License (free commercial use under the revenue
  threshold; check the current terms) — unlike ACE-Step's MIT.
- Text-only input: no reference-audio conditioning.
- The verified ACE-Step venv already ships `diffusers` (0.37.1), so no new environment
  is needed if the user accepts the weights. Ask before adding this route; keep
  ACE-Step as the default until then.