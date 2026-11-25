#!/usr/bin/env python3
"""Generate game character voice lines via Qwen-Audio-TTS or local Piper.

Backends:
  qwen   (default) Token Plan Qwen-Audio-TTS SpeechSynthesizer (sync HTTP)
  piper  local offline Piper CLI (CPU, zero cost, one voice per .onnx model)

Usage:
  python gen_voice.py "<text>" --voice longanlingxin [options]
  python gen_voice.py --lines lines.json [--voice longanlingxin] [options]
  python gen_voice.py "<text>" --backend piper --model <voice.onnx> [options]

Auth (qwen): ANTHROPIC_AUTH_TOKEN (the env name used by the official Token Plan
docs), falling back to QWEN_API_KEY, then TOKEN_PLAN_API_KEY.
Endpoint host (qwen): QWEN_TTS_BASE_URL, else the Token Plan host
https://token-plan.maas.qianwenaiapi.com. The sk-sp- Token Plan key belongs to
that platform; the aliyuncs.com Token Plan host is a DIFFERENT platform and
rejects this key with 401.

Official qwen request contract (platform.qianwenai.com docs, checked 2026-11-18;
see references/provider-notes.md):
  POST {host}/api/v1/services/audio/tts/SpeechSynthesizer
  {"model": "qwen-audio-3.0-tts-plus",
   "input": {"text": ..., "voice": ..., "format": "wav|mp3",
             "sample_rate": N, "instruction": ..., "rate": 0.5-2.0,
             "pitch": 0.5-2.0, "volume": 0-100, "seed": 0-65535}}
  -> 200 sync; output.audio.url (24 h) or output.audio.data (base64),
     output.audio.expires_at, usage.characters. No async task protocol.
  Voices are model-specific (see references/voices.md); cross-model voices
  fail with InvalidParameter.

Batch input (--lines) is a JSON array of line objects:
  [{"id": "hero_greet_01", "character": "hero", "text": "...",
    "voice": "longanlufeng", "instructions": "..."}]
Only id and text are required per line; voice/instructions fall back to the CLI
defaults. Each line becomes one audio file named after its id, plus a merged
manifest.json in --out (existing approved entries are never erased by a failed
retry; they gain a last_error note instead).

Outputs one JSON object on stdout (except --help); progress logs go to stderr.
Success covers decoding and duration; listening review is pending.
Exit codes: 0 success, 2 usage/local error, 3 API/generation error.
"""

import argparse
import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import wave
from datetime import datetime
from pathlib import Path

DEFAULT_HOST = "https://token-plan.maas.qianwenaiapi.com"
GEN_PATH = "/api/v1/services/audio/tts/SpeechSynthesizer"

MODELS = ("qwen-audio-3.0-tts-plus", "qwen-audio-3.0-tts-flash",
          "qwen-audio-3.1-tts-plus", "qwen-audio-3.1-tts-flash")
DEFAULT_MODEL = "qwen-audio-3.0-tts-plus"
FORMATS = ("wav", "mp3")  # provider also offers pcm/opus; the wrapper validates wav/mp3 only
SAMPLE_RATES = (8000, 12000, 16000, 22050, 24000, 44100, 48000)
BACKENDS = ("qwen", "piper")
SOFT_TEXT_LIMIT = 600  # skill guidance: split long text into separate takes.
HTTP_TIMEOUT = 240
API_ERRORS = {"API_ERROR", "DOWNLOAD_FAILED", "NETWORK_ERROR",
              "INVALID_RESPONSE", "INVALID_AUDIO", "PIPER_FAILED"}


class GenerationError(Exception):
    def __init__(self, code, message, **extra):
        super().__init__(message)
        self.code = code
        self.extra = extra


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        fail("INVALID_ARGUMENTS", message)


def redact(text):
    for var in ("QWEN_API_KEY", "TOKEN_PLAN_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        key = os.environ.get(var, "").strip()
        if key:
            text = text.replace(key, "[REDACTED]")
    return text


def log(msg):
    print(redact(msg), file=sys.stderr, flush=True)


def fail(code, message, **extra):
    raise GenerationError(code, message, **extra)


def resolve_host():
    explicit = os.environ.get("QWEN_TTS_BASE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    return DEFAULT_HOST


def resolve_api_key():
    # ANTHROPIC_AUTH_TOKEN is the official Token Plan docs' env name and the
    # user's designated key source; it wins over legacy QWEN_API_KEY.
    for var in ("ANTHROPIC_AUTH_TOKEN", "QWEN_API_KEY", "TOKEN_PLAN_API_KEY"):
        key = os.environ.get(var, "").strip()
        if key:
            return key
    return ""


def http_request(url, data=None, headers=None, timeout=HTTP_TIMEOUT):
    try:
        req = urllib.request.Request(url, data=data, headers=headers or {},
                                     method="POST" if data is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            with exc:
                return exc.code, exc.read()
    except (urllib.error.URLError, OSError) as exc:
        fail("NETWORK_ERROR", str(exc))
    except ValueError as exc:
        fail("INVALID_URL", str(exc))


def parse_response(body):
    try:
        data = json.loads(body)
    except (ValueError, UnicodeError):
        fail("INVALID_RESPONSE", "Provider response is not valid JSON")
    if not isinstance(data, dict):
        fail("INVALID_RESPONSE", "Provider response must be a JSON object")
    return data


def build_qwen_payload(line, args):
    voice = line.get("voice") or args.voice
    if not voice:
        fail("MISSING_VOICE", "Line '%s' has no voice; pass --voice or a per-line voice" % line["id"])
    input_data = {"text": line["text"], "voice": voice, "format": args.format or "wav"}
    if args.sample_rate:
        input_data["sample_rate"] = args.sample_rate
    instructions = line.get("instructions")
    if instructions is None:
        instructions = args.instructions
    if instructions:
        input_data["instruction"] = instructions
    if args.rate != 1.0:
        input_data["rate"] = args.rate
    if args.pitch != 1.0:
        input_data["pitch"] = args.pitch
    if args.volume != 50:
        input_data["volume"] = args.volume
    if args.seed is not None:
        input_data["seed"] = args.seed
    return {"model": args.model, "input": input_data}


def extract_audio(data):
    """Official non-streaming shape: output.audio.url (or base64 data)."""
    output = data.get("output") or {}
    if not isinstance(output, dict):
        fail("INVALID_RESPONSE", "Provider output must be an object")
    audio = output.get("audio")
    if not isinstance(audio, dict):
        return None
    url = audio.get("url")
    if isinstance(url, str) and re.match(r"^https?://", url, re.IGNORECASE):
        return ("url", url)
    b64 = audio.get("data")
    if isinstance(b64, str) and b64.strip():
        return ("base64", b64.strip())
    return None


def fetch_audio_bytes(kind, value):
    if kind == "url":
        status, data = http_request(value, timeout=300)
        if status != 200:
            fail("DOWNLOAD_FAILED",
                 "Failed to download result audio (HTTP %d) from %s" % (status, value[:200]))
        return data
    if value.startswith("data:"):
        value = value.split(",", 1)[-1]
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        fail("INVALID_AUDIO", "Result audio is not valid base64: %s" % exc)


def probe_audio(data):
    """Sniff the container, decode WAV fully, report duration/sample rate/channels."""
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        try:
            with wave.open(io.BytesIO(data)) as w:
                rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
                # Provider WAVs may be stream-written with a placeholder frame count
                # in the header; clamp to the frames actually present in the payload.
                actual_bytes = len(w.readframes(w.getnframes()))
                frames = actual_bytes // (channels * width) if channels * width else 0
                duration = frames / float(rate) if rate else 0.0
        except (wave.Error, EOFError, OSError) as exc:
            fail("INVALID_AUDIO", "Result does not decode as a complete WAV: %s" % exc)
        if duration <= 0:
            fail("INVALID_AUDIO", "Result WAV contains no audio frames")
        return {"format": "wav", "duration_seconds": round(duration, 3),
                "sample_rate": rate, "channels": channels}
    if data[:3] == b"ID3" or (len(data) > 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return {"format": "mp3", "duration_seconds": None, "sample_rate": None, "channels": None}
    fail("INVALID_AUDIO", "Result is neither WAV nor MP3 (first bytes: %r)" % data[:12])


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9._-]", "_", value).strip("._") or "line"


def save_take(data, probe, out_dir, name):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / (safe_name(name) + "." + probe["format"])
    if path.exists():
        fail("FILE_EXISTS", "Refusing to overwrite existing take: %s" % path)
    path.write_bytes(data)
    return path


def run_qwen_line(line, args, host, api_key, out_dir):
    payload = build_qwen_payload(line, args)
    # Protect existing takes BEFORE spending on a request; the container format is
    # only known after download, so guard both possible extensions.
    for ext in (".wav", ".mp3"):
        existing = out_dir / (safe_name(line["id"]) + ext)
        if existing.exists():
            fail("FILE_EXISTS", "Refusing to overwrite existing take: %s" % existing)
    endpoint = host + GEN_PATH
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    status, resp_body = http_request(endpoint, data=body, headers=headers)
    text = resp_body.decode("utf-8", errors="replace")
    if status != 200:
        hint = ""
        if status in (401, 403):
            hint = (" Check that the key matches the endpoint platform: sk-sp- Token Plan"
                    " keys belong to token-plan.maas.qianwenaiapi.com (QWEN_TTS_BASE_URL).")
        fail("API_ERROR", "TTS request failed (HTTP %d):%s %s" % (status, hint, text[:800]),
             http_status=status)
    data = parse_response(resp_body)
    audio = extract_audio(data)
    if audio is None:
        fail("API_ERROR", "No audio in API response: %s" % json.dumps(data, ensure_ascii=False)[:800])
    raw = fetch_audio_bytes(*audio)
    probe = probe_audio(raw)
    if args.format and probe["format"] != args.format:
        log("warning: requested format %s but provider returned %s" % (args.format, probe["format"]))
    path = save_take(raw, probe, out_dir, line["id"])
    entry = {"id": line["id"], "character": line.get("character"), "text": line["text"],
             "voice": payload["input"]["voice"], "status": "success", "path": str(path.resolve()),
             **probe}
    if payload["input"].get("instruction"):
        entry["instructions"] = payload["input"]["instruction"]
    if isinstance(data.get("usage"), dict):
        entry["usage"] = data["usage"]
    output_audio = (data.get("output") or {}).get("audio") or {}
    if audio[0] == "url":
        entry["source_url"] = audio[1]
        if output_audio.get("expires_at") is not None:
            entry["source_url_expires_at"] = output_audio["expires_at"]
    return entry


def run_piper_line(line, args, out_dir):
    piper_bin = args.piper_bin or shutil.which("piper")
    if not piper_bin:
        fail("PIPER_NOT_FOUND",
             "Piper CLI not found. Install with: python -m pip install piper-tts "
             "(see references/local-models.md)")
    if not args.model:
        fail("INVALID_MODEL", "Piper requires --model <voice.onnx or voice name>")
    if args.model.endswith(".onnx") and not Path(args.model).is_file():
        fail("MODEL_NOT_FOUND", "Piper voice model not found: %s" % args.model)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / (safe_name(line["id"]) + ".wav")
    if target.exists():
        fail("FILE_EXISTS", "Refusing to overwrite existing take: %s" % target)
    cmd = [piper_bin, "--model", args.model, "--output_file", str(target)]
    if args.speaker is not None:
        cmd += ["--speaker", str(args.speaker)]
    if args.length_scale != 1.0:
        cmd += ["--length-scale", str(args.length_scale)]
    if args.sentence_silence != 0.3:
        cmd += ["--sentence-silence", str(args.sentence_silence)]
    try:
        proc = subprocess.run(cmd, input=line["text"].encode("utf-8"),
                              capture_output=True, timeout=args.local_timeout)
    except subprocess.TimeoutExpired:
        target.unlink(missing_ok=True)
        fail("PIPER_FAILED", "Piper timed out after %d s" % args.local_timeout)
    except OSError as exc:
        fail("PIPER_FAILED", "Could not run Piper: %s" % exc)
    if proc.returncode != 0:
        target.unlink(missing_ok=True)
        fail("PIPER_FAILED", "Piper failed (exit %d): %s" % (
            proc.returncode, proc.stderr.decode("utf-8", errors="replace")[:500]))
    if not target.is_file():
        fail("PIPER_FAILED", "Piper output file missing: %s" % target)
    probe = probe_audio(target.read_bytes())
    return {"id": line["id"], "character": line.get("character"), "text": line["text"],
            "voice": Path(args.model).stem, "status": "success", "path": str(target.resolve()),
            **probe}


def load_lines(args):
    if args.lines:
        if args.text:
            fail("INVALID_ARGUMENTS", "Use either a text argument or --lines, not both")
        try:
            raw = json.loads(Path(args.lines).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            fail("INVALID_LINES", "Cannot read --lines file: %s" % exc)
        if not isinstance(raw, list) or not raw:
            fail("INVALID_LINES", "--lines must be a non-empty JSON array of line objects")
        lines = []
        for i, item in enumerate(raw, start=1):
            if not isinstance(item, dict) or not str(item.get("text") or "").strip():
                fail("INVALID_LINES", "Line %d must be an object with non-empty text" % i)
            line = dict(item)
            line["id"] = str(line.get("id") or "line-%03d" % i)
            line["text"] = str(line["text"]).strip()
            lines.append(line)
    else:
        if not args.text or not args.text.strip():
            fail("EMPTY_TEXT", "Text must not be empty")
        default_id = "take-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        lines = [{"id": args.name or default_id, "character": args.character,
                  "text": args.text.strip()}]
    ids = [line["id"] for line in lines]
    if len(set(ids)) != len(ids):
        fail("INVALID_LINES", "Duplicate line ids in batch")
    if args.backend == "piper" and any(line.get("instructions") for line in lines):
        fail("INVALID_PARAMETERS", "Piper does not support delivery instructions")
    for line in lines:
        if len(line["text"]) > SOFT_TEXT_LIMIT:
            log("warning: line '%s' is %d chars (> %d); consider splitting at natural pauses"
                % (line["id"], len(line["text"]), SOFT_TEXT_LIMIT))
    return lines


def write_manifest(out_dir, backend, model, entries):
    manifest_path = out_dir / "manifest.json"
    merged = {}
    if manifest_path.is_file():
        try:
            old = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in old.get("lines") or []:
                if isinstance(entry, dict) and entry.get("id"):
                    merged[entry["id"]] = entry
        except (OSError, ValueError):
            log("warning: existing manifest.json unreadable; rewriting it")
    for entry in entries:
        prev = merged.get(entry["id"])
        if entry.get("status") != "success" and prev and prev.get("status") == "success":
            # A failed retry must not erase the record of an existing approved take.
            kept = dict(prev)
            kept["last_error"] = {"error": entry.get("error"), "message": entry.get("message")}
            merged[entry["id"]] = kept
        else:
            merged[entry["id"]] = entry
    manifest = {"updated_at": datetime.now().isoformat(timespec="seconds"),
                "backend": backend, "model": model,
                "lines": [merged[k] for k in sorted(merged)]}
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = manifest_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(manifest_path)
    return manifest_path


def generate():
    parser = JsonArgumentParser(description="Generate game voice lines (Qwen-Audio-TTS or local Piper).")
    parser.add_argument("text", nargs="?", help="Line text (single-line mode)")
    parser.add_argument("--lines", help="Batch JSON file: array of {id,text,voice?,character?,instructions?}")
    parser.add_argument("--backend", choices=BACKENDS, default="qwen", help="TTS backend (default qwen)")
    parser.add_argument("--model", help="qwen model id, or Piper voice .onnx path/name")
    parser.add_argument("--voice", help="qwen voice id (e.g. longanlingxin); required for qwen, must match the model")
    parser.add_argument("--instructions", help="Delivery direction (emotion, dialect, character) -> input.instruction")
    parser.add_argument("--character", help="Character name recorded in the manifest (single-line mode)")
    parser.add_argument("--name", help="Take id/filename stem (single-line mode; default take-<timestamp>)")
    parser.add_argument("--format", choices=FORMATS, help="Audio format (qwen only; default wav)")
    parser.add_argument("--sample-rate", type=int, help="Sample rate in Hz (qwen only; one of %s)" % (SAMPLE_RATES,))
    parser.add_argument("--rate", type=float, default=1.0, help="Speech rate 0.5-2.0 (qwen only)")
    parser.add_argument("--pitch", type=float, default=1.0, help="Pitch 0.5-2.0 (qwen only)")
    parser.add_argument("--volume", type=int, default=50, help="Volume 0-100 (qwen only)")
    parser.add_argument("--seed", type=int, help="Random seed 0-65535 for reproducible takes (qwen only)")
    parser.add_argument("--out", default="generated-voice", help="Output directory (default ./generated-voice)")
    parser.add_argument("--piper-bin", help="Path to the piper executable (default: search PATH)")
    parser.add_argument("--speaker", type=int, help="Piper multi-speaker model speaker id")
    parser.add_argument("--length-scale", type=float, default=1.0, help="Piper speed: >1 slower, <1 faster")
    parser.add_argument("--sentence-silence", type=float, default=0.3, help="Piper pause between sentences (seconds)")
    parser.add_argument("--local-timeout", type=int, default=300, help="Piper per-line timeout seconds")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads/commands and exit without generating")
    args = parser.parse_args()

    if args.model is None:
        args.model = DEFAULT_MODEL if args.backend == "qwen" else None
    if args.backend == "qwen":
        if args.model not in MODELS:
            fail("INVALID_MODEL", "Unknown model '%s'. Allowed: %s" % (args.model, ", ".join(MODELS)))
        if not 0.5 <= args.rate <= 2.0:
            fail("INVALID_PARAMETERS", "--rate must be within [0.5, 2.0]")
        if not 0.5 <= args.pitch <= 2.0:
            fail("INVALID_PARAMETERS", "--pitch must be within [0.5, 2.0]")
        if not 0 <= args.volume <= 100:
            fail("INVALID_PARAMETERS", "--volume must be within [0, 100]")
        if args.seed is not None and not 0 <= args.seed <= 65535:
            fail("INVALID_PARAMETERS", "--seed must be within [0, 65535]")
        if args.sample_rate is not None and args.sample_rate not in SAMPLE_RATES:
            fail("INVALID_PARAMETERS", "--sample-rate must be one of %s" % (SAMPLE_RATES,))
    else:
        if args.format or args.sample_rate:
            fail("INVALID_PARAMETERS", "--format/--sample-rate are qwen-only; Piper always writes WAV")
        if args.instructions:
            fail("INVALID_PARAMETERS", "Piper does not support delivery instructions")
        if args.rate != 1.0 or args.pitch != 1.0 or args.volume != 50 or args.seed is not None:
            fail("INVALID_PARAMETERS", "--rate/--pitch/--volume/--seed are qwen-only")
        if args.length_scale <= 0 or args.sentence_silence < 0:
            fail("INVALID_PARAMETERS", "--length-scale must be > 0 and --sentence-silence >= 0")
    if args.local_timeout <= 0:
        fail("INVALID_POLL_TIME", "Local timeout must be positive")

    lines = load_lines(args)
    out_dir = Path(args.out)
    host = resolve_host()

    if args.dry_run:
        if args.backend == "qwen":
            return {"status": "dry-run", "backend": "qwen", "endpoint": host + GEN_PATH,
                    "payloads": [build_qwen_payload(line, args) for line in lines]}
        cmds = []
        for line in lines:
            cmds.append({"id": line["id"], "stdin": line["text"],
                         "command": [args.piper_bin or "piper", "--model", args.model or "<voice.onnx>",
                                     "--output_file", str(out_dir / (safe_name(line["id"]) + ".wav"))]})
        return {"status": "dry-run", "backend": "piper", "commands": cmds}

    api_key = ""
    if args.backend == "qwen":
        api_key = resolve_api_key()
        if not api_key:
            fail("MISSING_API_KEY", "Set ANTHROPIC_AUTH_TOKEN (or QWEN_API_KEY / TOKEN_PLAN_API_KEY)")
        log("backend=qwen model=%s voice=%s lines=%d endpoint=%s" % (
            args.model, args.voice or "(per-line)", len(lines), host + GEN_PATH))
    else:
        log("backend=piper model=%s lines=%d" % (args.model, len(lines)))

    entries = []
    for i, line in enumerate(lines, start=1):
        log("[%d/%d] %s" % (i, len(lines), line["id"]))
        try:
            if args.backend == "qwen":
                entry = run_qwen_line(line, args, host, api_key, out_dir)
            else:
                entry = run_piper_line(line, args, out_dir)
            log("saved %s (%.2fs)" % (entry["path"], entry["duration_seconds"] or 0))
        except GenerationError as exc:
            entry = {"id": line["id"], "character": line.get("character"), "text": line["text"],
                     "status": "error", "error": exc.code, "message": str(exc), **exc.extra}
            log("line '%s' failed: %s %s" % (line["id"], exc.code, exc))
            if len(lines) == 1:
                raise
        entries.append(entry)

    manifest_path = write_manifest(out_dir, args.backend, args.model, entries)
    ok = [e for e in entries if e["status"] == "success"]
    failed = [e for e in entries if e["status"] != "success"]
    status = "success" if not failed else ("partial" if ok else "error")
    result = {"status": status, "backend": args.backend, "model": args.model,
              "requested": len(lines), "count": len(ok), "out": str(out_dir.resolve()),
              "manifest": str(manifest_path.resolve()), "lines": entries,
              "audio_review": "pending"}
    if failed:
        result["failed"] = len(failed)
        codes = {e["error"] for e in failed}
        raise GenerationError("BATCH_PARTIAL" if ok else sorted(codes)[0],
                              "%d of %d lines failed" % (len(failed), len(lines)),
                              result=result)
    return result


def main():
    exit_code = 0
    try:
        payload = generate()
    except GenerationError as exc:
        payload = exc.extra.pop("result", None) or {
            "status": "error", "error": exc.code, "message": str(exc), **exc.extra}
        if exc.code == "BATCH_PARTIAL":
            payload.setdefault("error", "BATCH_PARTIAL")
            payload.setdefault("message", str(exc))
        api_failure = exc.code in API_ERRORS or any(
            e.get("error") in API_ERRORS for e in payload.get("lines", []))
        exit_code = 3 if api_failure else 2
    except OSError as exc:
        payload = {"status": "error", "error": "IO_ERROR", "message": str(exc)}
        exit_code = 2
    print(redact(json.dumps(payload, ensure_ascii=False, indent=2)))
    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
