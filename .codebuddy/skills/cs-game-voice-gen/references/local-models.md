# Local TTS models

Load when the user wants offline/zero-cost generation, or when the cloud key/quota fails.

## Piper (supported by `--backend piper`)

CPU-only, offline, deterministic; one voice per `.onnx` model. Quality is below cloud
TTS — use it for drafts, placeholders, privacy-constrained projects or fallback, and say
so when delivering final-quality expectations.

Setup (live-verified 2026-11-18 with piper-tts 1.4.2):

```powershell
python -m pip install piper-tts
# Download a voice — each voice ships .onnx + .onnx.json. Browse:
# https://huggingface.co/rhasspy/piper-voices (mirror: https://hf-mirror.com/rhasspy/piper-voices)
# Verified Chinese voice: zh_CN-huayan-medium (~60 MB, 22050 Hz mono), path pattern:
#   <repo>/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx[.json]
```

- piper-tts 1.4.x accepts both `--output_file` and `--output-file` style flags; the bundled
  CLI uses the underscore style, which also matches older 1.2.x installs.
- The `piper` executable may not be on PATH (e.g. it lives in `anaconda3\Scripts`); pass
  `--piper-bin "<full path to piper.exe>"` when `where.exe piper` finds nothing.

Usage:

```bash
python "<skill-dir>/scripts/gen_voice.py" "你好，旅行者。" --backend piper --model "<path>/zh_CN-huayan-medium.onnx" --name npc_greet_01 --out "<dir>"
```

- `--model` accepts a `.onnx` path (must exist) or a Piper voice name resolvable by the
  installed CLI. Keep `.onnx.json` beside the `.onnx`.
- Knobs: `--length-scale` (>1 slower, <1 faster), `--sentence-silence` (pause seconds),
  `--speaker` (multi-speaker models only). No delivery instructions — Piper cannot act;
  pick a voice whose natural timbre fits the character.
- Language is fixed by the voice model; `--language`, `--format`, `--sample-rate` and
  `--instructions` are rejected for this backend.
- Output is always WAV; the manifest records the model stem as the voice.

## VoxCPM2 (advanced manual route, not bundled)

High-quality offline Chinese TTS (48 kHz, dialects), natural-language voice design and
reference-audio cloning. Requires manual install: PyTorch >= 2.5 + CUDA 12, VRAM >= 8 GB,
`git clone https://github.com/OpenBMB/VoxCPM` + its requirements; model auto-downloads
(~4 GB) on first use. The bundled CLI does not wrap it — run it in its own environment
and import the resulting WAVs into the project voice directory manually.

**Consent gate for cloning:** clone only the user's own voice or a voice with the
speaker's explicit permission, confirmed before generation; never clone a third party's
voice merely because a recording exists in the project, and never use a cloned voice for
impersonation. Record the consent alongside the reference audio.

## Routing summary

| Need | Route |
|------|-------|
| Final expressive Chinese/English takes | qwen `qwen-audio-3.0-tts-plus` |
| Offline draft / placeholder / privacy | Piper |
| Offline final-quality Chinese, dialects, voice design | VoxCPM2 (manual) |
| Cloned voice | out of scope for the bundled CLI; VoxCPM2 manual route + consent gate |
