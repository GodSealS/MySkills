#!/usr/bin/env python3
"""Generate game music and sound effects with a local ACE-Step 1.5 server.

Backend:
  ace-step (the only backend) — a local ACE-Step REST API server that you start
  yourself (see references/local-models.md). No cloud calls, no per-take fees;
  the cost is local GPU time. The script itself is Python 3.8+ standard library
  only and never imports torch.

Usage:
  python gen_audio.py "<prompt>" [--kind music|sfx] [options]
  python gen_audio.py --tracks tracks.json [options]
  python gen_audio.py --preflight-only --acestep-home <ACE-Step dir>

Server: --server-url or ACESTEP_API_URL, else http://127.0.0.1:8001.
Optional auth: ACESTEP_API_KEY (only if the server was started with --api-key).

Model preflight (startup check): when the ACE-Step install home is known
(--acestep-home or ACESTEP_HOME), every run first checks the local model weights
through ACE-Step's own downloader logic and downloads whatever is missing
(main model: acestep-v15-turbo + vae + Qwen3-Embedding-0.6B + acestep-5Hz-lm-1.7B;
plus the server-default acestep-5Hz-lm-0.6B). Downloads use `python -m
acestep.model_downloader` inside the ACE-Step environment (HuggingFace <->
ModelScope auto-fallback) and may take a long time on first run. --preflight-only
runs this check/download plus a server health probe without generating.

ACE-Step request contract (F:\\Tools\\ACE-Step docs/en/API.md, checked 2026-11-19;
see references/acestep-api.md):
  POST {server}/release_task   JSON, or multipart when uploading reference audio
    prompt/caption, lyrics ("[Instrumental]" or empty = instrumental),
    task_type=text2music, audio_duration 10-600 s, bpm 30-300, key_scale,
    time_signature, inference_steps, seed/use_random_seed, batch_size=1,
    audio_format wav|mp3, thinking, vocal_language,
    reference_audio_path / uploaded reference_audio file + audio_cover_strength
    (0.0-1.0; ~0.2 = style transfer, the reference guides style, not melody).
  POST {server}/query_result   {"task_id_list": [...]} -> status 0/1/2
  GET  {server}/v1/audio?path=...   download the generated file
  GET  {server}/health         readiness probe

Batch input (--tracks) is a JSON array of track objects:
  [{"id": "menu_theme_01", "prompt": "...", "kind": "music",
    "lyrics": "[Instrumental]", "duration": 30, "reference_audio": "ref.wav"}]
Only id and prompt are required per track; everything else falls back to the
CLI defaults. Each track becomes one audio file named after its id, plus a
merged manifest.json in --out (existing approved entries are never erased by a
failed retry; they gain a last_error note instead).

Outputs one JSON object on stdout (except --help); progress logs go to stderr.
Success covers decoding and duration; listening review is pending.
Exit codes: 0 success, 2 usage/local error, 3 server/generation error.
"""

import argparse
import array
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import wave
from datetime import datetime
from pathlib import Path

DEFAULT_SERVER = "http://127.0.0.1:8001"
KINDS = ("music", "sfx")
FORMATS = ("wav", "mp3")  # ACE-Step also offers flac/opus/aac; the wrapper validates wav/mp3 only
DURATION_RANGE = (10, 600)  # ACE-Step hard limits; SFX shorter than 10 s are trimmed locally
BPM_RANGE = (30, 300)
DEFAULT_DURATION = {"music": 30, "sfx": 10}
DEFAULT_FORMAT = {"music": "mp3", "sfx": "wav"}
DEFAULT_COVER_STRENGTH = 0.2  # provider docs: lower values (~0.2) for style transfer
INSTRUMENTAL_LYRICS = "[Instrumental]"
HTTP_TIMEOUT = 30
SUBMIT_TIMEOUT = 300  # first release_task may block while the server loads models
POLL_INTERVAL = 3
DEFAULT_POLL_TIMEOUT = 900  # first request may include model loading
DEFAULT_DOWNLOAD_TIMEOUT = 3600  # per downloader invocation; weights are multi-GB
MODEL_CHECK_TIMEOUT = 180  # venv python startup + weight-file scan
DEFAULT_LM_MODEL = "acestep-5Hz-lm-0.6B"  # server-default LM (API.md ACESTEP_LM_MODEL_PATH)
API_ERRORS = {"API_ERROR", "SERVER_DOWN", "NETWORK_ERROR", "INVALID_RESPONSE",
              "DOWNLOAD_FAILED", "INVALID_AUDIO", "GENERATION_FAILED", "POLL_TIMEOUT",
              "MODEL_DOWNLOAD_FAILED", "MODEL_DOWNLOAD_TIMEOUT"}


class GenerationError(Exception):
    def __init__(self, code, message, **extra):
        super().__init__(message)
        self.code = code
        self.extra = extra


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        fail("INVALID_ARGUMENTS", message)


def redact(text):
    key = os.environ.get("ACESTEP_API_KEY", "").strip()
    if key:
        text = text.replace(key, "[REDACTED]")
    return text


def log(msg):
    print(redact(msg), file=sys.stderr, flush=True)


def fail(code, message, **extra):
    raise GenerationError(code, message, **extra)


def resolve_server():
    explicit = os.environ.get("ACESTEP_API_URL", "").strip()
    return (explicit or DEFAULT_SERVER).rstrip("/")


def resolve_api_key():
    return os.environ.get("ACESTEP_API_KEY", "").strip()


def resolve_acestep_home():
    return os.environ.get("ACESTEP_HOME", "").strip()


def find_venv_python(home):
    """Locate the ACE-Step environment interpreter (venv or portable package)."""
    candidates = [home / ".venv" / "Scripts" / "python.exe",
                  home / ".venv" / "bin" / "python",
                  home / "python_embedded" / "python.exe"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    fail("ACESTEP_NOT_INSTALLED",
         "No ACE-Step Python environment under %s (looked for .venv and python_embedded). "
         "Install it first: git clone https://github.com/ACE-Step/ACE-Step-1.5.git && "
         "cd ACE-Step-1.5 && uv sync (see references/local-models.md)" % home)


MODEL_CHECK_SNIPPET = (
    "import json; "
    "from acestep.model_downloader import check_main_model_exists, check_model_exists, get_checkpoints_dir; "
    "print(json.dumps({'checkpoints_dir': str(get_checkpoints_dir()), "
    "'main_ready': check_main_model_exists(), "
    "'lm_default_ready': check_model_exists('%s')}))" % DEFAULT_LM_MODEL
)


def read_model_status(home, venv_python):
    """Ask ACE-Step's own downloader logic whether the weights are present."""
    try:
        proc = subprocess.run([str(venv_python), "-c", MODEL_CHECK_SNIPPET],
                              cwd=str(home), capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=MODEL_CHECK_TIMEOUT)
    except subprocess.TimeoutExpired:
        fail("ACESTEP_CHECK_FAILED", "Model check timed out after %d s" % MODEL_CHECK_TIMEOUT)
    except OSError as exc:
        fail("ACESTEP_CHECK_FAILED", "Cannot run the ACE-Step environment: %s" % exc)
    if proc.returncode != 0:
        fail("ACESTEP_CHECK_FAILED",
             "Model check failed (exit %d): %s" % (proc.returncode, (proc.stderr or "")[-800:]))
    try:
        status = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        fail("ACESTEP_CHECK_FAILED", "Model check returned no JSON: %s" % proc.stdout[-400:])
    if not isinstance(status, dict) or "main_ready" not in status:
        fail("ACESTEP_CHECK_FAILED", "Unexpected model check output: %s" % str(status)[:400:])
    return status


def run_model_downloader(home, venv_python, extra_args, timeout, label):
    """Stream `python -m acestep.model_downloader` output to stderr; fail on error."""
    cmd = [str(venv_python), "-m", "acestep.model_downloader"] + extra_args
    log("downloading %s (this can take a long time; progress below)" % label)
    try:
        proc = subprocess.Popen(cmd, cwd=str(home), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace")
    except OSError as exc:
        fail("MODEL_DOWNLOAD_FAILED", "Cannot start the model downloader: %s" % exc)
    deadline = time.monotonic() + timeout
    with proc:
        for line in proc.stdout:
            log(line.rstrip())
            if time.monotonic() > deadline:
                proc.kill()
                fail("MODEL_DOWNLOAD_TIMEOUT",
                     "Downloading %s exceeded %d s; rerun to resume (partial files are kept)"
                     % (label, timeout))
        code = proc.wait()
    if code != 0:
        fail("MODEL_DOWNLOAD_FAILED",
             "Model downloader failed for %s (exit %d); check network/mirror settings "
             "(HF_ENDPOINT, ModelScope fallback) and rerun" % (label, code))


def ensure_local_models(home, download_timeout):
    """Startup preflight: check weights, download whatever is missing, re-check."""
    home = Path(home).expanduser()
    if not home.is_dir():
        fail("ACESTEP_NOT_INSTALLED",
             "ACE-Step home does not exist: %s. Install it first: "
             "git clone https://github.com/ACE-Step/ACE-Step-1.5.git && cd ACE-Step-1.5 && "
             "uv sync (see references/local-models.md)" % home)
    venv_python = find_venv_python(home)
    status = read_model_status(home, venv_python)
    downloaded = []
    if not status.get("main_ready"):
        run_model_downloader(home, venv_python, [], download_timeout,
                             "main model (turbo DiT + vae + text encoder + LM 1.7B)")
        downloaded.append("main")
    if not status.get("lm_default_ready"):
        run_model_downloader(home, venv_python,
                             ["--model", DEFAULT_LM_MODEL, "--skip-main"], download_timeout,
                             "default LM %s" % DEFAULT_LM_MODEL)
        downloaded.append(DEFAULT_LM_MODEL)
    if downloaded:
        status = read_model_status(home, venv_python)
        if not status.get("main_ready") or not status.get("lm_default_ready"):
            fail("MODEL_DOWNLOAD_FAILED",
                 "Weights still missing after download: %s" % json.dumps(status))
        log("model download complete: %s" % ", ".join(downloaded))
    else:
        log("model preflight ok: weights present at %s" % status.get("checkpoints_dir"))
    return {"acestep_home": str(home.resolve()), "venv_python": str(venv_python),
            "checkpoints_dir": status.get("checkpoints_dir"),
            "main_ready": bool(status.get("main_ready")),
            "lm_default_ready": bool(status.get("lm_default_ready")),
            "downloaded": downloaded}


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


def auth_headers(api_key, content_type="application/json"):
    headers = {}
    if content_type:
        headers["Content-Type"] = content_type
    if api_key:
        headers["Authorization"] = "Bearer " + api_key
    return headers


def parse_response(body):
    try:
        data = json.loads(body)
    except (ValueError, UnicodeError):
        fail("INVALID_RESPONSE", "Server response is not valid JSON")
    if not isinstance(data, dict):
        fail("INVALID_RESPONSE", "Server response must be a JSON object")
    return data


def check_server(server, api_key):
    try:
        status, body = http_request(server + "/health", headers=auth_headers(api_key, None),
                                    timeout=10)
    except GenerationError as exc:
        fail("SERVER_DOWN",
             "ACE-Step server not reachable at %s (%s). Start it first, e.g.: "
             "cd <ACE-Step dir> && .venv\\Scripts\\python.exe -m acestep.api_server "
             "--host 127.0.0.1 --port 8001 (see references/local-models.md); "
             "override the address with --server-url or ACESTEP_API_URL."
             % (server, exc))
    if status != 200:
        fail("SERVER_DOWN", "ACE-Step health check failed (HTTP %d): %s"
             % (status, body.decode("utf-8", errors="replace")[:300]))
    data = parse_response(body).get("data") or {}
    if data.get("status") != "ok":
        fail("SERVER_DOWN", "ACE-Step health report is not ok: %s" % json.dumps(data)[:300])
    if not data.get("models_initialized"):
        log("server up; models load lazily on the first request (may take a while)")
    return data


def multipart_encode(fields, file_field, file_path):
    """stdlib multipart/form-data body: text fields + one audio file upload."""
    boundary = "----genaudio" + uuid.uuid4().hex
    lines = []
    for name, value in fields.items():
        lines.append(("--" + boundary).encode())
        lines.append(('Content-Disposition: form-data; name="%s"' % name).encode())
        lines.append(b"")
        lines.append(str(value).encode("utf-8"))
    filename = Path(file_path).name
    lines.append(("--" + boundary).encode())
    lines.append(('Content-Disposition: form-data; name="%s"; filename="%s"'
                  % (file_field, filename)).encode("utf-8"))
    lines.append(b"Content-Type: application/octet-stream")
    lines.append(b"")
    lines.append(Path(file_path).read_bytes())
    lines.append(("--" + boundary + "--").encode())
    lines.append(b"")
    return b"\r\n".join(lines), "multipart/form-data; boundary=" + boundary


def build_task_fields(track, args):
    """Merge per-track overrides over CLI defaults into ACE-Step request fields."""
    kind = track.get("kind") or args.kind
    prompt = str(track.get("prompt") or "").strip()
    duration = track.get("duration", args.duration)
    if duration is None:
        duration = DEFAULT_DURATION[kind]
    fmt = track.get("format") or args.format or DEFAULT_FORMAT[kind]
    lyrics = track.get("lyrics")
    if lyrics is None:
        lyrics = args.lyrics
    if kind == "sfx":
        if lyrics and str(lyrics).strip() not in ("", INSTRUMENTAL_LYRICS, "[Inst]"):
            fail("INVALID_PARAMETERS", "Track '%s': SFX must be instrumental; drop lyrics"
                 % track["id"])
        lyrics = INSTRUMENTAL_LYRICS
    elif lyrics is None or not str(lyrics).strip():
        lyrics = INSTRUMENTAL_LYRICS
    fields = {
        "prompt": prompt,
        "lyrics": str(lyrics),
        "task_type": "text2music",
        "audio_duration": float(duration),
        "audio_format": fmt,
        "batch_size": 1,
        "inference_steps": track.get("steps", args.steps),
    }
    bpm = track.get("bpm", args.bpm)
    if bpm is not None:
        fields["bpm"] = int(bpm)
    key = track.get("key", args.key)
    if key:
        fields["key_scale"] = str(key)
    time_signature = track.get("time_signature", args.time_signature)
    if time_signature:
        fields["time_signature"] = str(time_signature)
    language = track.get("language", args.language)
    if language:
        fields["vocal_language"] = str(language)
    thinking = track.get("thinking", args.thinking)
    fields["thinking"] = bool(thinking)
    seed = track.get("seed", args.seed)
    if seed is not None:
        fields["use_random_seed"] = False
        fields["seed"] = int(seed)
    reference = track.get("reference_audio") or args.reference_audio
    if reference:
        strength = track.get("cover_strength", args.cover_strength)
        fields["audio_cover_strength"] = float(strength)
    return kind, fmt, fields, reference


def validate_track(track, args):
    kind = track.get("kind") or args.kind
    if kind not in KINDS:
        fail("INVALID_PARAMETERS", "Track '%s': kind must be one of %s" % (track["id"], KINDS))
    if not str(track.get("prompt") or "").strip():
        fail("EMPTY_PROMPT", "Track '%s' has an empty prompt" % track["id"])
    duration = track.get("duration", args.duration)
    if duration is None:
        duration = DEFAULT_DURATION[kind]
    if not DURATION_RANGE[0] <= float(duration) <= DURATION_RANGE[1]:
        fail("INVALID_PARAMETERS", "Track '%s': duration must be within %s seconds "
             "(ACE-Step limit); trim shorter SFX locally with --trim-start/--trim-end"
             % (track["id"], DURATION_RANGE))
    bpm = track.get("bpm", args.bpm)
    if bpm is not None and not BPM_RANGE[0] <= int(bpm) <= BPM_RANGE[1]:
        fail("INVALID_PARAMETERS", "Track '%s': bpm must be within %s" % (track["id"], BPM_RANGE))
    fmt = track.get("format") or args.format or DEFAULT_FORMAT[kind]
    if fmt not in FORMATS:
        fail("INVALID_PARAMETERS", "Track '%s': format must be one of %s" % (track["id"], FORMATS))
    steps = track.get("steps", args.steps)
    if not 1 <= int(steps) <= 200:
        fail("INVALID_PARAMETERS", "Track '%s': steps must be within [1, 200] "
             "(turbo models: 1-20, recommended 8)" % track["id"])
    seed = track.get("seed", args.seed)
    if seed is not None and int(seed) < 0:
        fail("INVALID_PARAMETERS", "Track '%s': seed must be >= 0" % track["id"])
    reference = track.get("reference_audio") or args.reference_audio
    strength = track.get("cover_strength", args.cover_strength)
    if not 0.0 <= float(strength) <= 1.0:
        fail("INVALID_PARAMETERS", "Track '%s': cover strength must be within [0.0, 1.0]"
             % track["id"])
    if reference:
        ref_path = Path(reference)
        if not ref_path.is_file() or ref_path.stat().st_size == 0:
            fail("REFERENCE_NOT_FOUND", "Track '%s': reference audio not found or empty: %s"
                 % (track["id"], reference))
    elif track.get("cover_strength") is not None or args.cover_strength != DEFAULT_COVER_STRENGTH:
        fail("INVALID_PARAMETERS", "Track '%s': cover strength requires reference audio"
             % track["id"])
    trim_start = track.get("trim_start", args.trim_start)
    trim_end = track.get("trim_end", args.trim_end)
    if (trim_start is None) != (trim_end is None):
        fail("INVALID_PARAMETERS", "Track '%s': pass both --trim-start and --trim-end"
             % track["id"])
    if trim_start is not None:
        if float(trim_start) < 0 or float(trim_end) <= float(trim_start):
            fail("INVALID_PARAMETERS", "Track '%s': trim needs 0 <= start < end" % track["id"])
        if fmt != "wav":
            fail("INVALID_PARAMETERS", "Track '%s': trimming requires WAV output "
                 "(--format wav); MP3 cannot be trimmed by this wrapper" % track["id"])
    return kind, fmt, duration, reference, (trim_start, trim_end)


def submit_task(server, fields, reference, api_key):
    if reference:
        # Upload the reference file; the server ignores *_path fields when a
        # file part is present (docs/en/API.md, Method B).
        body, content_type = multipart_encode(fields, "reference_audio", reference)
    else:
        body = json.dumps(fields, ensure_ascii=False).encode("utf-8")
        content_type = "application/json"
    status, resp_body = http_request(server + "/release_task", data=body,
                                     headers=auth_headers(api_key, content_type),
                                     timeout=SUBMIT_TIMEOUT)
    text = resp_body.decode("utf-8", errors="replace")
    if status != 200:
        hint = ""
        if status == 401:
            hint = " The server requires an API key: set ACESTEP_API_KEY."
        elif status == 429:
            hint = " Server queue is full; wait for running jobs to finish."
        fail("API_ERROR", "release_task failed (HTTP %d):%s %s" % (status, hint, text[:800]),
             http_status=status)
    data = parse_response(resp_body)
    if data.get("code") != 200:
        fail("API_ERROR", "release_task rejected: %s" % str(data.get("error"))[:800])
    task_id = (data.get("data") or {}).get("task_id")
    if not task_id:
        fail("INVALID_RESPONSE", "No task_id in release_task response: %s" % text[:800])
    return task_id


def poll_task(server, task_id, api_key, timeout):
    deadline = time.monotonic() + timeout
    payload = json.dumps({"task_id_list": [task_id]}).encode("utf-8")
    while True:
        status, resp_body = http_request(server + "/query_result", data=payload,
                                         headers=auth_headers(api_key))
        if status != 200:
            fail("API_ERROR", "query_result failed (HTTP %d): %s"
                 % (status, resp_body.decode("utf-8", errors="replace")[:500]),
                 http_status=status)
        data = parse_response(resp_body)
        items = data.get("data") or []
        item = next((i for i in items if i.get("task_id") == task_id), None)
        if item is not None:
            state = item.get("status")
            if str(state) == "1":
                return item
            if str(state) == "2":
                fail("GENERATION_FAILED", "ACE-Step task failed: %s"
                     % str(item.get("result") or item.get("error") or item)[:800],
                     task_id=task_id)
        if time.monotonic() >= deadline:
            fail("POLL_TIMEOUT", "Task %s not finished within %d s; it may still complete "
                 "server-side — query it again before resubmitting" % (task_id, timeout),
                 task_id=task_id)
        time.sleep(POLL_INTERVAL)


def extract_file_url(item, server):
    result = item.get("result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except ValueError:
            fail("INVALID_RESPONSE", "Task result is not valid JSON: %s" % result[:500])
    if isinstance(result, dict):
        result = [result]
    if not isinstance(result, list) or not result:
        fail("INVALID_RESPONSE", "Task result has no outputs: %s" % str(item)[:500])
    first = result[0] or {}
    if str(first.get("status")) == "2":
        fail("GENERATION_FAILED", "ACE-Step output failed: %s" % str(first)[:800])
    file_url = first.get("file")
    if not isinstance(file_url, str) or not file_url:
        fail("INVALID_RESPONSE", "No file URL in task output: %s" % str(first)[:500])
    return urllib.parse.urljoin(server + "/", file_url), first


def fetch_audio_bytes(url):
    status, data = http_request(url, timeout=300)
    if status != 200:
        fail("DOWNLOAD_FAILED", "Failed to download result audio (HTTP %d) from %s"
             % (status, url[:200]))
    return data


def _wav_chunks(data):
    """Yield (chunk_id, payload) pairs from a RIFF/WAVE byte string."""
    pos = 12
    while pos + 8 <= len(data):
        chunk_id = data[pos:pos + 4]
        size = int.from_bytes(data[pos + 4:pos + 8], "little")
        payload = data[pos + 8:pos + 8 + min(size, len(data) - pos - 8)]
        yield chunk_id, payload
        pos += 8 + size + (size & 1)


def normalize_wav(data):
    """ACE-Step writes IEEE-float WAV (fmt tag 3, both 'wav' and 'wav32'); the
    stdlib wave module only reads PCM. Convert float32 WAV to 16-bit PCM so
    probing/trimming/saving work; PCM WAV and MP3 pass through unchanged.
    The saved deliverable is therefore engine-friendly 16-bit PCM WAV."""
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return data
    fmt = next((p for cid, p in _wav_chunks(data) if cid == b"fmt "), None)
    if not fmt or len(fmt) < 16:
        return data
    audio_format = int.from_bytes(fmt[0:2], "little")
    if audio_format != 3:
        return data
    channels = int.from_bytes(fmt[2:4], "little")
    rate = int.from_bytes(fmt[4:8], "little")
    width = int.from_bytes(fmt[14:16], "little") // 8
    if width != 4 or channels <= 0 or rate <= 0:
        fail("INVALID_AUDIO", "Unsupported float WAV layout (width=%d, channels=%d, rate=%d)"
             % (width, channels, rate))
    payload = next((p for cid, p in _wav_chunks(data) if cid == b"data"), None)
    if not payload:
        fail("INVALID_AUDIO", "Float WAV has no data chunk")
    floats = array.array("f")
    floats.frombytes(payload[:len(payload) - len(payload) % 4])
    if sys.byteorder != "little":
        floats.byteswap()
    pcm = array.array("h", (max(-32768, min(32767, int(round(s * 32767.0)))) for s in floats))
    if sys.byteorder != "little":
        pcm.byteswap()
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return out.getvalue()


def probe_audio(data):
    """Sniff the container, decode WAV fully, report duration/sample rate/channels."""
    data = normalize_wav(data)
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        try:
            with wave.open(io.BytesIO(data)) as w:
                rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
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


def trim_wav(data, start, end):
    """Cut [start, end) seconds out of a WAV byte string; returns new WAV bytes."""
    data = normalize_wav(data)
    try:
        with wave.open(io.BytesIO(data)) as w:
            rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
            frames = w.readframes(w.getnframes())
    except (wave.Error, EOFError, OSError) as exc:
        fail("INVALID_AUDIO", "Cannot trim: result does not decode as WAV: %s" % exc)
    total = len(frames) // (channels * width) if channels * width else 0
    duration = total / float(rate) if rate else 0.0
    if end > duration + 0.05:
        fail("INVALID_TRIM", "Trim end %.2f s exceeds audio duration %.2f s" % (end, duration))
    first = min(int(start * rate), total)
    last = min(int(end * rate), total)
    if last <= first:
        fail("INVALID_TRIM", "Trim range contains no audio frames")
    cut = frames[first * channels * width:last * channels * width]
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(cut)
    return out.getvalue()


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9._-]", "_", value).strip("._") or "track"


def save_take(data, probe, out_dir, name):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / (safe_name(name) + "." + probe["format"])
    if path.exists():
        fail("FILE_EXISTS", "Refusing to overwrite existing take: %s" % path)
    path.write_bytes(data)
    return path


def run_track(track, args, server, api_key, out_dir):
    kind, fmt, fields, reference = build_task_fields(track, args)
    _, _, duration, _, trim = validate_track(track, args)
    # Protect existing takes BEFORE spending GPU time; guard both possible extensions.
    for ext in (".wav", ".mp3"):
        existing = out_dir / (safe_name(track["id"]) + ext)
        if existing.exists():
            fail("FILE_EXISTS", "Refusing to overwrite existing take: %s" % existing)
    log("submit %s (kind=%s, %.0fs, %s%s)" % (
        track["id"], kind, duration, fmt,
        ", reference=%s" % Path(reference).name if reference else ""))
    task_id = submit_task(server, fields, reference, api_key)
    log("task %s queued; polling (timeout %ds)" % (task_id, args.timeout))
    item = poll_task(server, task_id, api_key, args.timeout)
    url, output = extract_file_url(item, server)
    raw = normalize_wav(fetch_audio_bytes(url))
    if trim[0] is not None:
        raw = trim_wav(raw, float(trim[0]), float(trim[1]))
    probe = probe_audio(raw)
    if probe["format"] != fmt:
        log("warning: requested format %s but server returned %s" % (fmt, probe["format"]))
    path = save_take(raw, probe, out_dir, track["id"])
    entry = {"id": track["id"], "kind": kind, "prompt": fields["prompt"],
             "status": "success", "path": str(path.resolve()), **probe}
    if fields["lyrics"] not in ("", INSTRUMENTAL_LYRICS, "[Inst]"):
        entry["lyrics"] = fields["lyrics"]
    for field, key in (("bpm", "bpm"), ("key_scale", "key"), ("time_signature", "time_signature")):
        if field in fields:
            entry[key] = fields[field]
    if reference:
        entry["reference_audio"] = str(Path(reference).resolve())
        entry["cover_strength"] = fields["audio_cover_strength"]
    if trim[0] is not None:
        entry["trim"] = {"start": float(trim[0]), "end": float(trim[1])}
    if output.get("seed_value"):
        entry["seed_value"] = output["seed_value"]
    if output.get("dit_model"):
        entry["dit_model"] = output["dit_model"]
    if output.get("lm_model"):
        entry["lm_model"] = output["lm_model"]
    metas = output.get("metas")
    if isinstance(metas, dict):
        entry["metas"] = metas
    entry["task_id"] = task_id
    return entry


def load_tracks(args):
    if args.tracks:
        if args.prompt:
            fail("INVALID_ARGUMENTS", "Use either a prompt argument or --tracks, not both")
        try:
            raw = json.loads(Path(args.tracks).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            fail("INVALID_TRACKS", "Cannot read --tracks file: %s" % exc)
        if not isinstance(raw, list) or not raw:
            fail("INVALID_TRACKS", "--tracks must be a non-empty JSON array of track objects")
        tracks = []
        for i, item in enumerate(raw, start=1):
            if not isinstance(item, dict) or not str(item.get("prompt") or "").strip():
                fail("INVALID_TRACKS", "Track %d must be an object with a non-empty prompt" % i)
            track = dict(item)
            track["id"] = str(track.get("id") or "track-%03d" % i)
            track["prompt"] = str(track["prompt"]).strip()
            tracks.append(track)
    else:
        if not args.prompt or not args.prompt.strip():
            fail("EMPTY_PROMPT", "Prompt must not be empty")
        default_id = "track-" + datetime.now().strftime("%Y%m%d-%H%M%S")
        tracks = [{"id": args.name or default_id, "prompt": args.prompt.strip()}]
    ids = [track["id"] for track in tracks]
    if len(set(ids)) != len(ids):
        fail("INVALID_TRACKS", "Duplicate track ids in batch")
    if args.lyrics_file:
        if args.lyrics:
            fail("INVALID_ARGUMENTS", "Use either --lyrics or --lyrics-file, not both")
        try:
            args.lyrics = Path(args.lyrics_file).read_text(encoding="utf-8")
        except OSError as exc:
            fail("INVALID_LYRICS", "Cannot read --lyrics-file: %s" % exc)
    return tracks


def write_manifest(out_dir, server, entries):
    manifest_path = out_dir / "manifest.json"
    merged = {}
    if manifest_path.is_file():
        try:
            old = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in old.get("tracks") or []:
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
                "backend": "ace-step", "server": server,
                "tracks": [merged[k] for k in sorted(merged)]}
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = manifest_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(manifest_path)
    return manifest_path


def generate():
    parser = JsonArgumentParser(
        description="Generate game music and sound effects with a local ACE-Step server.")
    parser.add_argument("prompt", nargs="?", help="Music/SFX description (single-track mode)")
    parser.add_argument("--tracks", help="Batch JSON file: array of {id,prompt,kind?,lyrics?,duration?,...}")
    parser.add_argument("--kind", choices=KINDS, default="music",
                        help="Asset kind: music (BGM/theme) or sfx (one-shot/ambient); default music")
    parser.add_argument("--reference-audio", help="Optional reference audio file guiding the style "
                        "(uploaded to the server; style transfer, not melody copy)")
    parser.add_argument("--cover-strength", type=float, default=DEFAULT_COVER_STRENGTH,
                        help="Reference influence 0.0-1.0 (default %.1f = style transfer)"
                             % DEFAULT_COVER_STRENGTH)
    parser.add_argument("--lyrics", help="Vocal lyrics with structure tags ([Verse]/[Chorus]...); "
                        "empty or [Instrumental] = instrumental (music only)")
    parser.add_argument("--lyrics-file", help="Read lyrics from a text file (music only)")
    parser.add_argument("--duration", type=float, help="Seconds, 10-600 (default music 30, sfx 10)")
    parser.add_argument("--bpm", type=int, help="Tempo 30-300")
    parser.add_argument("--key", help="Key/scale, e.g. 'C Major' or 'Am'")
    parser.add_argument("--time-signature", choices=("2", "3", "4", "6"), help="2/4, 3/4, 4/4 or 6/8")
    parser.add_argument("--language", help="Vocal language hint (en, zh, ja, ...)")
    parser.add_argument("--thinking", action="store_true",
                        help="Use the 5Hz LM planner for codes/metadata (higher quality, needs LM)")
    parser.add_argument("--steps", type=int, default=8, help="Diffusion steps (turbo 1-20, default 8)")
    parser.add_argument("--seed", type=int, help="Fixed seed for reproducible takes (default random)")
    parser.add_argument("--format", choices=FORMATS, help="Output format (default music mp3, sfx wav)")
    parser.add_argument("--trim-start", type=float, help="WAV only: cut start seconds (SFX one-shots)")
    parser.add_argument("--trim-end", type=float, help="WAV only: cut end seconds")
    parser.add_argument("--name", help="Track id/filename stem (single-track mode)")
    parser.add_argument("--out", default="generated-audio", help="Output directory (default ./generated-audio)")
    parser.add_argument("--server-url", help="ACE-Step server (default ACESTEP_API_URL or %s)" % DEFAULT_SERVER)
    parser.add_argument("--timeout", type=int, default=DEFAULT_POLL_TIMEOUT,
                        help="Per-track polling budget seconds (default %d; first run loads models)"
                             % DEFAULT_POLL_TIMEOUT)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print request payloads and exit without calling the server")
    parser.add_argument("--acestep-home", help="ACE-Step install dir (default ACESTEP_HOME); "
                        "enables the startup model check/auto-download")
    parser.add_argument("--preflight-only", action="store_true",
                        help="Check/download local models and probe server health, then exit "
                             "without generating (requires --acestep-home or ACESTEP_HOME)")
    parser.add_argument("--download-timeout", type=int, default=DEFAULT_DOWNLOAD_TIMEOUT,
                        help="Per-downloader-invocation budget seconds (default %d)"
                             % DEFAULT_DOWNLOAD_TIMEOUT)
    args = parser.parse_args()

    if args.timeout <= 0:
        fail("INVALID_PARAMETERS", "--timeout must be positive")
    if args.download_timeout <= 0:
        fail("INVALID_PARAMETERS", "--download-timeout must be positive")
    home = args.acestep_home or resolve_acestep_home()
    if args.preflight_only:
        if not home:
            fail("MISSING_ACESTEP_HOME",
                 "--preflight-only needs the ACE-Step install dir: pass --acestep-home "
                 "or set ACESTEP_HOME")
        report = ensure_local_models(home, args.download_timeout)
        server = (args.server_url or resolve_server()).rstrip("/")
        server_report = {"url": server, "up": False}
        try:
            health = check_server(server, resolve_api_key())
            server_report.update(up=True,
                                 models_initialized=bool(health.get("models_initialized")))
        except GenerationError as exc:
            server_report["hint"] = str(exc)
        return {"status": "success", "backend": "ace-step",
                "preflight": report, "server": server_report}
    tracks = load_tracks(args)
    for track in tracks:
        validate_track(track, args)
    out_dir = Path(args.out)
    server = (args.server_url or resolve_server()).rstrip("/")

    if args.dry_run:
        tasks = []
        for track in tracks:
            kind, fmt, fields, reference = build_task_fields(track, args)
            tasks.append({"id": track["id"], "kind": kind, "endpoint": server + "/release_task",
                          "fields": fields,
                          "reference_audio_upload": str(Path(reference).resolve()) if reference else None})
        return {"status": "dry-run", "backend": "ace-step", "server": server, "tasks": tasks}

    preflight = None
    if home:
        preflight = ensure_local_models(home, args.download_timeout)
    else:
        log("warning: model preflight skipped; set --acestep-home or ACESTEP_HOME to "
            "check/auto-download local weights before generating")
    api_key = resolve_api_key()
    check_server(server, api_key)
    log("backend=ace-step server=%s tracks=%d" % (server, len(tracks)))

    entries = []
    for i, track in enumerate(tracks, start=1):
        log("[%d/%d] %s" % (i, len(tracks), track["id"]))
        try:
            entry = run_track(track, args, server, api_key, out_dir)
            log("saved %s (%.2fs)" % (entry["path"], entry["duration_seconds"] or 0))
        except GenerationError as exc:
            entry = {"id": track["id"], "kind": track.get("kind") or args.kind,
                     "prompt": track["prompt"], "status": "error",
                     "error": exc.code, "message": str(exc), **exc.extra}
            log("track '%s' failed: %s %s" % (track["id"], exc.code, exc))
            if len(tracks) == 1:
                raise
        entries.append(entry)

    manifest_path = write_manifest(out_dir, server, entries)
    ok = [e for e in entries if e["status"] == "success"]
    failed = [e for e in entries if e["status"] != "success"]
    status = "success" if not failed else ("partial" if ok else "error")
    result = {"status": status, "backend": "ace-step", "server": server,
              "requested": len(tracks), "count": len(ok), "out": str(out_dir.resolve()),
              "manifest": str(manifest_path.resolve()), "tracks": entries,
              "audio_review": "pending"}
    if preflight is not None:
        result["preflight"] = preflight
    if failed:
        result["failed"] = len(failed)
        codes = {e["error"] for e in failed}
        raise GenerationError("BATCH_PARTIAL" if ok else sorted(codes)[0],
                              "%d of %d tracks failed" % (len(failed), len(tracks)),
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
            e.get("error") in API_ERRORS for e in payload.get("tracks", []))
        exit_code = 3 if api_failure else 2
    except OSError as exc:
        payload = {"status": "error", "error": "IO_ERROR", "message": str(exc)}
        exit_code = 2
    print(redact(json.dumps(payload, ensure_ascii=False, indent=2)))
    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()