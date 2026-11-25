#!/usr/bin/env python3
"""Generate 2D game animation assets from a character image via wan3.0-video.

Stages:
  video   submit + poll + download the locked-camera MP4 (paid)
  frames  decode the MP4, sample at target fps, cut alpha, align, write PNGs
  sheet   pack frames into a sprite sheet + GIF preview + manifest.json
  all     video -> frames -> sheet

Usage:
  python gen_anim.py <character_image> "<context>" [options]
  python gen_anim.py --stage frames --from-video <mp4> [options]

Auth: ANTHROPIC_AUTH_TOKEN (sk-sp- Token Plan key, the official docs' env name),
falling back to QWEN_API_KEY, then TOKEN_PLAN_API_KEY.
Endpoint host: QWEN_VIDEO_BASE_URL, else the Token Plan host
https://token-plan.maas.qianwenaiapi.com. The sk-sp- key belongs to that
platform; the aliyuncs.com Token Plan host is a DIFFERENT platform.
The video API is the DashScope async task protocol; see references/provider-notes.md.

Outputs one JSON object on stdout (except --help); progress logs go to stderr.
Exit codes: 0 success, 2 usage/local error, 3 API/generation error.
"""

import argparse
import base64
import io
import json
import math
import mimetypes
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

DEFAULT_HOST = "https://token-plan.maas.qianwenaiapi.com"
SUBMIT_PATH = "/api/v1/services/aigc/video-generation/video-synthesis"
TASK_PATH = "/api/v1/tasks/"

MODELS = ("wan3.0-video", "wan3.0-video-prime")
DEFAULT_MODEL = "wan3.0-video"
RESOLUTIONS = ("480P", "720P", "1080P")
RATIOS = ("adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16")
STAGES = ("video", "frames", "sheet", "all")

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MIN_IMAGE_SIDE = 240
MAX_IMAGE_SIDE = 8000
MAX_ASPECT = 8.0

LOCK_PREFIX = ("固定机位，镜头完全静止，无任何推拉摇移、变焦或镜头切换。"
               "角色始终完整位于画面内，身体比例与画面占比保持不变。")
FIRST_FRAME_ROLE = ("图1为精确首帧，定义构图、角色姿态、服装、道具与机位；"
                    "不得改变其身份、比例与道具归属。")
LOOP_SUFFIX = "动作在结尾精确回到起始姿态，形成可无缝循环的周期动作。"
EDIT_PREFIX = ("视频1为唯一编辑母版。只修改提示词指明的对象、区域或声音，"
               "其余画面、机位、运动、时序、遮挡与事件顺序全部保持不变。"
               "被替换对象须沿用原对象的出现时机、运动路径、速度与遮挡位置，且原对象不再出现。")
EXTEND_DIRECTIONS = {
    "forward": "向前延长，从视频1的末帧继续",
    "backward": "向后延长，衔接至视频1的首帧",
}
EXTEND_PREFIX = ("在视频1的基础上{direction}。先保持边界处的姿态与朝向、道具、场景、构图、"
                 "光照与运动趋势连续，再展开新动作；不得改动原视频内容，"
                 "每个延续的角色或物件保持为同一个连续实例，不复制、不拆分、不改变数量。")
FLAT_BG_HINT = "背景保持平整的单一纯色，不添加任何纹理、景物、光影或渐变变化。"
FLAT_BG_HINT_COLORED = "背景保持平整的纯{cn}色，不添加任何纹理、景物、光影或渐变变化。"
# Named so the matte stage can ask for the exact key color it will remove.
BG_COLOR_NAMES = {"ffffff": "白", "000000": "黑", "00b140": "绿", "ff00a8": "品红",
                  "1683ff": "蓝", "00cfd1": "青", "808080": "灰"}


def flat_bg_hint(alpha, matte_color):
    if alpha != "matte":
        return FLAT_BG_HINT
    name = BG_COLOR_NAMES.get(matte_color.lower().lstrip("#"))
    return FLAT_BG_HINT_COLORED.format(cn=name) if name else FLAT_BG_HINT

API_ERRORS = {"API_ERROR", "TASK_FAILED", "TIMEOUT", "DOWNLOAD_FAILED", "NETWORK_ERROR",
              "INVALID_RESPONSE", "INVALID_VIDEO", "MISSING_DEPENDENCY"}


class GenerationError(Exception):
    def __init__(self, code, message, **extra):
        super().__init__(message)
        self.code = code
        self.extra = extra


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        fail("INVALID_ARGUMENTS", message)


def video_host():
    explicit = os.environ.get("QWEN_VIDEO_BASE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    return DEFAULT_HOST


def api_key():
    # ANTHROPIC_AUTH_TOKEN is the official Token Plan docs' env name and the
    # user's designated key source; it wins over legacy QWEN_API_KEY.
    return (os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("QWEN_API_KEY")
            or os.environ.get("TOKEN_PLAN_API_KEY") or "").strip()


def redact(text):
    key = api_key()
    return text.replace(key, "[REDACTED]") if key else text


def log(msg):
    print(redact(msg), file=sys.stderr, flush=True)


def fail(code, message, **extra):
    raise GenerationError(code, message, **extra)


def http_request(url, data=None, headers=None, timeout=120):
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


def parse_json(body):
    try:
        data = json.loads(body)
    except (ValueError, UnicodeError):
        fail("INVALID_RESPONSE", "Provider response is not valid JSON")
    if not isinstance(data, dict):
        fail("INVALID_RESPONSE", "Provider response must be a JSON object")
    return data


# ---------------------------------------------------------------------------
# Input image handling
# ---------------------------------------------------------------------------

def numpy_and_pil():
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        fail("MISSING_DEPENDENCY",
             "Frame processing requires Pillow and numpy: "
             "python -m pip install -r <skill-dir>/requirements.txt")
    return np, Image


def load_character_image(path, flatten_color):
    """Read, validate and flatten the character art to an opaque RGB data URI."""
    np, Image = numpy_and_pil()
    src = Path(path)
    if not src.is_file():
        fail("CHARACTER_NOT_FOUND", "Character image not found: %s" % path)
    if src.stat().st_size > MAX_IMAGE_BYTES:
        fail("CHARACTER_TOO_LARGE", "Character image exceeds %d MB" % (MAX_IMAGE_BYTES // 1048576))
    try:
        img = Image.open(src)
        img.load()
    except OSError as exc:
        fail("INVALID_IMAGE", "Character image does not decode: %s" % exc)
    if img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        flat = Image.new("RGB", img.size, flatten_color)
        flat.paste(img, mask=img.split()[-1])
        img = flat
        log("flattened alpha channel onto #%02x%02x%02x (API rejects transparent input)"
            % tuple(flatten_color))
    else:
        img = img.convert("RGB")
    w, h = img.size
    if min(w, h) < MIN_IMAGE_SIDE or max(w, h) > MAX_IMAGE_SIDE:
        scale = min(MAX_IMAGE_SIDE / max(w, h), 1.0)
        if min(w, h) * scale < MIN_IMAGE_SIDE:
            fail("INVALID_IMAGE", "Character image side outside [%d, %d] px" % (MIN_IMAGE_SIDE, MAX_IMAGE_SIDE))
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
        log("downscaled character image to %dx%d" % img.size)
    if max(img.size) / min(img.size) > MAX_ASPECT:
        fail("INVALID_IMAGE", "Character aspect ratio exceeds %.0f:1" % MAX_ASPECT)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    blob = buf.getvalue()
    if len(blob) > MAX_IMAGE_BYTES:
        fail("CHARACTER_TOO_LARGE", "Flattened PNG exceeds %d MB" % (MAX_IMAGE_BYTES // 1048576))
    mime = mimetypes.guess_type(src.name)[0] or "image/png"
    mime = "image/png"
    return "data:%s;base64,%s" % (mime, base64.b64encode(blob).decode("ascii")), img.size


def parse_color(text):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", text or "")
    if not m:
        fail("INVALID_ARGUMENTS", "--flatten-color must be a 6-digit hex color")
    v = int(m.group(1), 16)
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


# ---------------------------------------------------------------------------
# Stage: video
# ---------------------------------------------------------------------------

def task_mode(args):
    if args.edit_from:
        return "edit"
    if args.extend_from:
        return "extend"
    return "generate"


def probe_video_meta(path):
    """Cheap duration/fps probe; never decodes every frame into memory."""
    try:
        import imageio_ffmpeg  # noqa: F401
        import imageio.v3 as iio
        meta = iio.immeta(str(path), plugin="FFMPEG")
        fps = float(meta.get("fps") or 0)
        duration = float(meta.get("duration") or 0)
        if fps and duration:
            return fps, duration
    except Exception:
        pass
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        count = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        cap.release()
        if fps and count:
            return fps, count / fps
    except Exception:
        pass
    try:
        import av
        container = av.open(str(path))
        stream = container.streams.video[0]
        fps = float(stream.average_rate) if stream.average_rate else 0.0
        duration = (float(container.duration) / 1_000_000 if container.duration
                    else float(stream.duration * stream.time_base) if stream.duration else 0.0)
        container.close()
        if duration:
            return fps, duration
    except Exception:
        pass
    return 0.0, 0.0


def resolve_source_video(args, probe=True):
    """reference_video accepts only a public/OSS URL, never base64.

    A local file is usable only through the .source.json sidecar written when the
    CLI downloaded it, which records the provider URL (valid 24 h).
    """
    source = args.edit_from or args.extend_from
    if re.match(r"^https?://", source, re.IGNORECASE):
        if probe:
            log("source is a remote URL; duration limits are validated by the provider")
        return source
    local = Path(source)
    if not local.is_file():
        fail("SOURCE_VIDEO_NOT_FOUND", "Source video not found: %s" % source)
    sidecar = Path(str(local) + ".source.json")
    url = None
    if sidecar.is_file():
        try:
            url = json.loads(sidecar.read_text(encoding="utf-8")).get("video_url")
        except ValueError:
            url = None
    if not isinstance(url, str) or not url.startswith("http"):
        fail("SOURCE_URL_REQUIRED",
             "reference_video needs a public or OSS URL; this CLI cannot upload local video. "
             "Use the provider URL recorded in <file>.source.json (valid 24 h), or host the file publicly.")
    if probe:
        fps, duration = probe_video_meta(local)
        if duration:
            if not 1 <= duration <= 15:
                fail("SOURCE_DURATION",
                     "reference_video clips must be 1-15 s; source is %.2f s" % duration)
            if task_mode(args) == "extend" and duration + args.duration > 30:
                fail("SOURCE_DURATION",
                     "input plus extension must not exceed 30 s (%.2f + %d)" % (duration, args.duration))
        else:
            log("could not probe source duration locally; provider limits still apply")
    return url


def build_payload(args, data_uri):
    mode = task_mode(args)
    parameters = {
        "resolution": args.resolution,
        "audio": args.audio,
        "prompt_extend": not args.no_prompt_extend,
        "watermark": False,
    }
    if args.seed is not None:
        parameters["seed"] = args.seed

    if mode == "generate":
        media = [{"type": "first_frame", "url": data_uri}]
        if args.loop:
            media.append({"type": "last_frame", "url": data_uri})
        prompt = LOCK_PREFIX + FIRST_FRAME_ROLE + args.context.strip()
        if args.loop:
            prompt += LOOP_SUFFIX
        if args.alpha in ("rembg", "matte") and not args.no_bg_hint:
            prompt += flat_bg_hint(args.alpha, args.matte_color)
        parameters.update(ratio=args.ratio, duration=args.duration)
    else:
        # Frame slots and reference slots are mutually exclusive in the API.
        media = [{"type": "reference_video", "url": args.source_video_url}]
        if mode == "edit":
            prompt = EDIT_PREFIX + args.context.strip()
            # Edit inherits the source timing; -1 asks the model to choose.
            parameters.update(ratio="adaptive", duration=-1)
        else:
            prompt = EXTEND_PREFIX.format(
                direction=EXTEND_DIRECTIONS[args.extend_direction]) + args.context.strip()
            parameters.update(ratio="adaptive", duration=args.duration)
    return {
        "model": args.model,
        "input": {"prompt": prompt, "media": media},
        "parameters": parameters,
    }


def poll_task(task_id, key, interval, max_wait):
    deadline = time.monotonic() + max_wait
    headers = {"Authorization": "Bearer " + key}
    polls = 0
    while time.monotonic() < deadline:
        time.sleep(min(interval, max(0.0, deadline - time.monotonic())))
        if time.monotonic() >= deadline:
            break
        polls += 1
        status, body = http_request(video_host() + TASK_PATH + task_id, headers=headers, timeout=60)
        text = body.decode("utf-8", "replace")
        if status != 200:
            fail("API_ERROR", "Task query failed (HTTP %d): %s" % (status, text[:500]),
                 http_status=status)
        data = parse_json(text)
        output = data.get("output") or {}
        task_status = str(output.get("task_status") or "").upper()
        log("poll %d: task %s -> %s" % (polls, task_id, task_status or "UNKNOWN"))
        if task_status in ("SUCCEEDED", "SUCCESS"):
            return data, polls
        if task_status in ("FAILED", "CANCELED", "CANCELLED", "UNKNOWN"):
            fail("TASK_FAILED", output.get("message") or data.get("message") or "Generation task failed",
                 task_id=task_id, provider_code=output.get("code") or data.get("code"))
    fail("TIMEOUT", "Task %s did not finish within %d s" % (task_id, max_wait), task_id=task_id)


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9._-]", "_", text).strip("_") or "clip"


def download_video(url, out_dir, model, name=None, task_id=None):
    status, blob = http_request(url, timeout=600)
    if status != 200:
        fail("DOWNLOAD_FAILED", "Failed to download result video (HTTP %d)" % status)
    if len(blob) < 64 or b"ftyp" not in blob[:64]:
        fail("INVALID_VIDEO", "Downloaded payload is not an MP4 container")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    label = safe_name(name) if name else safe_name(model)
    with tempfile.NamedTemporaryFile(mode="wb", dir=str(out_dir), delete=False,
                                     prefix="%s-%s-" % (stamp, label), suffix=".mp4") as target:
        path = Path(target.name)
        target.write(blob)
    # The signed result URL is kept in a sidecar, not echoed to stdout: it is the
    # only way to reuse this clip as reference_video within its 24 h validity.
    sidecar = Path(str(path) + ".source.json")
    sidecar.write_text(json.dumps({
        "schema": "cs-game-anim-gen/video-source@1",
        "video_url": url,
        "task_id": task_id,
        "model": model,
        "name": name,
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "url_valid_hours": 24,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"path": str(path.resolve()), "bytes": len(blob),
            "source_sidecar": str(sidecar.resolve())}


def finish_task(args, task_id, key, resumed=False):
    result, polls = poll_task(task_id, key, args.poll_interval, args.max_poll_time)
    out = result.get("output") or {}
    video_url = out.get("video_url")
    if not isinstance(video_url, str) or not video_url.startswith("http"):
        fail("INVALID_RESPONSE", "Succeeded task has no video_url")
    model = result.get("model") or args.model
    usage = result.get("usage") or {}
    file_info = download_video(video_url, Path(args.out), model, args.name, task_id)
    return {
        "status": "success",
        "stage": "video",
        "model": model,
        "task_id": task_id,
        "polls": polls,
        "usage": usage,
        "video": file_info,
        "loop": args.loop,
        "resumed": resumed,
    }


def write_task_record(args, task_id, task_status, payload):
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "schema": "cs-game-anim-gen/task@1",
        "task_id": task_id,
        "task_status": task_status,
        "model": args.model,
        "mode": task_mode(args),
        "name": args.name,
        "context": args.context,
        "loop": bool(args.loop),
        "parameters": payload["parameters"],
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
        "resume": ("python gen_anim.py --stage all --task-id %s --out %s"
                   % (task_id, out_dir)),
    }
    path = out_dir / ("task-%s.json" % safe_name(task_id))
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path.resolve())


def run_video_stage(args, data_uri):
    key = api_key()
    if not args.dry_run and not key:
        fail("MISSING_API_KEY", "Set ANTHROPIC_AUTH_TOKEN (or QWEN_API_KEY / TOKEN_PLAN_API_KEY)")

    if args.task_id:
        log("resuming task %s (no new submission)" % args.task_id)
        return finish_task(args, args.task_id, key, resumed=True)

    payload = build_payload(args, data_uri)
    if args.dry_run:
        preview = json.loads(json.dumps(payload))
        for item in preview["input"]["media"]:
            if str(item["url"]).startswith("data:"):
                item["url"] = "data:...base64 (%d chars omitted)" % (len(item["url"]) - 30)
        return {"status": "dry-run", "endpoint": video_host() + SUBMIT_PATH, "payload": preview}

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json",
               "X-DashScope-Async": "enable"}
    log("submit model=%s mode=%s duration=%s resolution=%s ratio=%s loop=%s"
        % (args.model, task_mode(args), payload["parameters"]["duration"],
           args.resolution, payload["parameters"]["ratio"], args.loop))
    status, text = http_request(video_host() + SUBMIT_PATH, data=body, headers=headers, timeout=120)
    raw = text.decode("utf-8", "replace")
    if status != 200:
        hint = " Check that QWEN_API_KEY matches the endpoint host." if status in (401, 403) else ""
        fail("API_ERROR", "Video submission failed (HTTP %d):%s %s" % (status, hint, raw[:800]),
             http_status=status)
    data = parse_json(raw)
    output = data.get("output") or {}
    task_id = output.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        fail("INVALID_RESPONSE", "Submission response has no task_id: %s" % raw[:500])
    log("task submitted: %s" % task_id)

    if args.submit_only:
        record = write_task_record(args, task_id, output.get("task_status") or "PENDING", payload)
        return {
            "status": "submitted",
            "stage": "video",
            "model": args.model,
            "task_id": task_id,
            "task_status": output.get("task_status") or "PENDING",
            "task_record": record,
            "resume": ("python gen_anim.py --stage all --task-id %s --out %s"
                       % (task_id, Path(args.out))),
        }
    return finish_task(args, task_id, key)


# ---------------------------------------------------------------------------
# Video decoding
# ---------------------------------------------------------------------------

def decode_video(path):
    """Return (fps, [HxWx3 uint8 RGB frames]) using the first available backend."""
    np, _ = numpy_and_pil()
    target = Path(path)
    if not target.is_file():
        fail("VIDEO_NOT_FOUND", "Source video not found: %s" % path)

    try:
        import imageio_ffmpeg  # noqa: F401  (ensures the bundled ffmpeg binary)
        import imageio.v3 as iio
        meta = iio.immeta(str(target), plugin="FFMPEG")
        frames = [np.asarray(f, dtype=np.uint8) for f in iio.imiter(str(target), plugin="FFMPEG")]
        fps = float(meta.get("fps") or 30.0)
        if frames:
            return fps, frames, "imageio-ffmpeg"
    except Exception as exc:  # fall through to the next backend
        log("imageio/FFMPEG backend unavailable: %s" % exc)

    try:
        import cv2
        cap = cv2.VideoCapture(str(target))
        if not cap.isOpened():
            raise RuntimeError("cv2 cannot open %s" % target)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
        frames = []
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()
        if frames:
            return fps, frames, "opencv"
    except Exception as exc:
        log("opencv backend unavailable: %s" % exc)

    try:
        import av
        container = av.open(str(target))
        stream = container.streams.video[0]
        fps = float(stream.average_rate) if stream.average_rate else 30.0
        frames = [np.asarray(f.to_rgb().to_ndarray(), dtype=np.uint8)
                  for f in container.decode(stream)]
        container.close()
        if frames:
            return fps, frames, "pyav"
    except Exception as exc:
        log("pyav backend unavailable: %s" % exc)

    fail("MISSING_DEPENDENCY",
         "No video decoder available. Install one of: imageio-ffmpeg, opencv-python-headless, av")


def sample_indices(count, src_fps, target_fps, loop):
    ratio = src_fps / max(1.0, target_fps)
    candidates = {max(1, math.floor(ratio)), max(1, math.ceil(ratio))}
    step = min(candidates, key=lambda s: (abs(src_fps / s - target_fps), s))
    # For a seamless cycle the final source frame repeats frame 0, so exclude it.
    usable = count - 1 if (loop and count > 1) else count
    return list(range(0, usable, step)), step


# ---------------------------------------------------------------------------
# Stage: frames
# ---------------------------------------------------------------------------

def cut_alpha(frame, np):
    """Return (rgba uint8 HxWx4, bbox or None) using rembg."""
    try:
        from rembg import remove, new_session
    except ImportError:
        fail("MISSING_DEPENDENCY",
             "AI cutout requires rembg: python -m pip install rembg  "
             "(or pass --alpha matte for a dependency-free color key on a flat background)")
    global _REMBG_SESSION
    if _REMBG_SESSION is None:
        _REMBG_SESSION = new_session("u2net")
    png = remove(frame, session=_REMBG_SESSION)
    arr = np.asarray(png, dtype=np.uint8)
    if arr.ndim != 3 or arr.shape[2] != 4:
        fail("INVALID_IMAGE", "rembg did not return an RGBA image")
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > 8)
    if ys.size == 0:
        return arr, None
    return arr, (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


_REMBG_SESSION = None


def matte_cut(frame, np, color, tolerance):
    """Border-connected color key.

    Removes only the background color reachable from the frame border, so the same
    color inside the character (eyes, highlights, cloth) survives. Requires no
    third-party dependency beyond numpy; use --alpha rembg for painted scenes.
    """
    from collections import deque
    # int32, not int16: a single channel difference of 245 already overflows int16 when squared.
    rgb = frame[:, :, :3].astype(np.int32)
    bg = ((rgb - np.array(color, np.int32)) ** 2).sum(axis=2) <= tolerance * tolerance
    h, w = bg.shape
    visited = np.zeros((h, w), dtype=bool)
    queue = deque()

    def push(y, x):
        if bg[y, x] and not visited[y, x]:
            visited[y, x] = True
            queue.append((y, x))

    for x in range(w):
        push(0, x)
        push(h - 1, x)
    for y in range(h):
        push(y, 0)
        push(y, w - 1)
    if not queue:
        fail("MATTE_NO_BORDER",
             "No border pixels match --matte-color within --matte-tolerance; "
             "use --alpha rembg, another --matte-color or a larger tolerance")
    while queue:
        y, x = queue.popleft()
        if y > 0:
            push(y - 1, x)
        if y + 1 < h:
            push(y + 1, x)
        if x > 0:
            push(y, x - 1)
        if x + 1 < w:
            push(y, x + 1)
    alpha = np.where(visited, 0, 255).astype(np.uint8)
    rgba = np.dstack([frame[:, :, :3], alpha])
    ys, xs = np.where(alpha > 8)
    if ys.size == 0:
        return rgba, None
    return rgba, (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def scale_nearest(img, Image, scale):
    if scale == 1.0:
        return img
    w, h = img.size
    return img.resize((max(1, int(round(w * scale))), max(1, int(round(h * scale)))),
                      Image.Resampling.NEAREST)


def build_palette(cells, Image, colors):
    """One shared palette for the whole sequence: per-frame palettes flicker."""
    stride = max(1, len(cells) // 8)
    sample = cells[::stride][:8] or cells[:1]
    width = sample[0].width
    montage = Image.new("RGB", (width * len(sample), sample[0].height), (0, 0, 0))
    for i, im in enumerate(sample):
        montage.paste(im.convert("RGB"), (i * width, 0))
    return montage.quantize(colors=colors, method=Image.Quantize.FASTOCTREE,
                            dither=Image.Dither.NONE)


def quantize_to_palette(img, palette, Image):
    alpha = img.getchannel("A")
    rgb = img.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE).convert("RGB")
    rgb.putalpha(alpha)
    return rgb


def run_frames_stage(args):
    np, Image = numpy_and_pil()
    fps, frames, backend = decode_video(args.from_video)
    log("decoded %d frames @%.2ffps via %s" % (len(frames), fps, backend))
    idx, step = sample_indices(len(frames), fps, args.fps, args.loop)
    if not idx:
        fail("INVALID_VIDEO", "No frames sampled from source video")
    if args.max_frames and len(idx) > args.max_frames:
        keep = np.linspace(0, len(idx) - 1, args.max_frames).round().astype(int)
        idx = [idx[i] for i in sorted(set(keep))]
        step = max(1, int(round(len(frames) / float(len(idx)))))
    # Sprite fps is quantized to src_fps / integer step; report the real rate.
    effective_fps = round(fps / step, 3)
    log("sampling %d sprite frames: step %d -> %.3f fps (requested %d) from %.2f fps source"
        % (len(idx), step, effective_fps, args.fps, fps))

    cut = []
    for i, fi in enumerate(idx):
        frame = frames[fi]
        if args.alpha == "rembg":
            rgba, bbox = cut_alpha(frame, np)
        elif args.alpha == "matte":
            rgba, bbox = matte_cut(frame, np, args.matte_rgb, args.matte_tolerance)
        else:
            rgba = np.dstack([frame, np.full(frame.shape[:2], 255, np.uint8)])
            alpha = rgba[:, :, 3]
            ys, xs = np.where(alpha > 8)
            bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1) if ys.size else None
        if bbox is None:
            fail("EMPTY_FRAME", "Frame %d (source %d) has no visible subject after alpha cut" % (i, fi))
        cut.append((i, fi, rgba, bbox))

    x0 = min(b[0] for _, _, _, b in cut) - args.pad
    y0 = min(b[1] for _, _, _, b in cut) - args.pad
    x1 = max(b[2] for _, _, _, b in cut) + args.pad
    y1 = max(b[3] for _, _, _, b in cut) + args.pad
    h, w = frames[0].shape[:2]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    cw, ch = x1 - x0, y1 - y0
    if cw + ch < 2:
        fail("EMPTY_FRAME", "Union subject box is degenerate")
    log("union canvas %dx%d at offset (%d,%d)" % (cw, ch, x0, y0))

    out_dir = Path(args.out) / "frames"
    out_dir.mkdir(parents=True, exist_ok=True)
    cells = []
    for i, fi, rgba, bbox in cut:
        cell = np.zeros((ch, cw, 4), np.uint8)
        dx0, dy0 = bbox[0] - x0, bbox[1] - y0
        rw, rh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        cell[dy0:dy0 + rh, dx0:dx0 + rw] = rgba[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        cells.append(Image.fromarray(cell, "RGBA"))

    palette = None
    if args.scale != 1.0:
        cells = [scale_nearest(im, Image, args.scale) for im in cells]
        log("nearest-neighbour scale %.3f -> %dx%d canvas" % (args.scale, *cells[0].size))
    if args.colors:
        palette = build_palette(cells, Image, args.colors)
        cells = [quantize_to_palette(im, palette, Image) for im in cells]
        log("quantized sequence to a shared %d-color palette (no dither)" % args.colors)
    cw, ch = cells[0].size

    files, coverage = [], []
    for i, (fi, img) in enumerate(zip([c[1] for c in cut], cells)):
        name = "frame-%03d.png" % i
        img.save(out_dir / name)
        files.append({"index": i, "source_frame": fi, "file": name})
        coverage.append(float((np.asarray(img)[:, :, 3] > 8).mean()))

    sheet_grid = contact_sheet(out_dir, files, args)
    metrics = {
        "coverage_min": round(min(coverage), 4),
        "coverage_mean": round(sum(coverage) / len(coverage), 4),
        "empty_frames": [],
    }
    if args.loop and len(cut) > 1:
        first = np.asarray(Image.open(out_dir / files[0]["file"]), np.uint8).astype(np.float32)
        last = np.asarray(Image.open(out_dir / files[-1]["file"]), np.uint8).astype(np.float32)
        metrics["loop_seam_mean_abs_diff"] = round(float(np.abs(first - last).mean()), 3)
    meta = {
        "schema": "cs-game-anim-gen/frames-meta@1",
        "source_fps": round(fps, 3),
        "step": step,
        "effective_fps": effective_fps,
        "requested_fps": args.fps,
        "loop": bool(args.loop),
        "alpha": args.alpha,
        "cell": {"width": cw, "height": ch},
        "offset": {"x": x0, "y": y0},
        "pixel_art": {"scale": args.scale, "colors": args.colors,
                      "shared_palette": bool(args.colors)},
        "metrics": metrics,
    }
    if args.alpha == "matte":
        meta["matte"] = {"color": args.matte_color, "tolerance": args.matte_tolerance}
    (Path(args.out) / "frames" / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "status": "success",
        "stage": "frames",
        "decoder": backend,
        "effective_fps": effective_fps,
        "source_fps": round(fps, 3),
        "target_fps": args.fps,
        "frame_count": len(files),
        "cell": {"width": cw, "height": ch},
        "offset": {"x": x0, "y": y0},
        "alpha": args.alpha,
        "pixel_art": meta["pixel_art"],
        "frames_dir": str(out_dir.resolve()),
        "frames": files,
        "contact_sheet": sheet_grid,
        "metrics": metrics,
    }


def contact_sheet(frames_dir, files, args):
    np, Image = numpy_and_pil()
    n = len(files)
    cols = min(3, n)
    rows = math.ceil(n / cols)
    pick = [files[int(round(i * (n - 1) / max(1, rows * cols - 1)))] for i in range(rows * cols)] \
        if n > 1 else files * (rows * cols)
    imgs = [Image.open(frames_dir / f["file"]).convert("RGBA") for f in pick]
    w, h = imgs[0].size
    scale = 256 / max(w, h)
    tw, th = max(1, int(w * scale)), max(1, int(h * scale))
    canvas = Image.new("RGBA", (tw * cols, th * rows), (40, 40, 40, 255))
    for i, im in enumerate(imgs):
        canvas.paste(im.resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
    out = Path(args.out) / "contact-sheet.png"
    canvas.convert("RGB").save(out)
    return str(out.resolve())


# ---------------------------------------------------------------------------
# Stage: sheet
# ---------------------------------------------------------------------------

def run_sheet_stage(args, frames_result=None):
    np, Image = numpy_and_pil()
    out_dir = Path(args.out)
    frames_dir = out_dir / "frames"
    if not frames_dir.is_dir():
        fail("MISSING_FRAMES", "No frames directory at %s; run --stage frames first" % frames_dir)
    names = sorted(p.name for p in frames_dir.glob("frame-*.png"))
    if not names:
        fail("MISSING_FRAMES", "No frame-*.png files in %s" % frames_dir)
    imgs = [Image.open(frames_dir / n).convert("RGBA") for n in names]
    cw, ch = imgs[0].size
    if any(im.size != (cw, ch) for im in imgs):
        fail("INVALID_FRAMES", "Frame canvas sizes differ; regenerate frames in one pass")
    n = len(imgs)
    cols = args.sheet_cols or int(math.ceil(math.sqrt(n)))
    rows = math.ceil(n / cols)
    sheet = Image.new("RGBA", (cw * cols, ch * rows), (0, 0, 0, 0))
    for i, im in enumerate(imgs):
        sheet.paste(im, ((i % cols) * cw, (i // cols) * ch))
    sheet_path = out_dir / "sprite-sheet.png"
    sheet.save(sheet_path)

    meta_path = frames_dir / "meta.json"
    meta = {}
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except ValueError:
            log("frames/meta.json is not valid JSON; falling back to --fps")
    fps = float(meta.get("effective_fps") or args.fps)
    if meta and abs(fps - args.fps) > 0.01:
        log("using effective fps %.3f from frames/meta.json (requested %d)" % (fps, args.fps))

    gif_path = out_dir / "preview.gif"
    ms = max(1, int(round(1000.0 / fps)))
    pal_frames = []
    for im in imgs:
        alpha = im.split()[3]
        p = im.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255)
        mask = alpha.point(lambda a: 255 if a <= 128 else 0)
        p.paste(255, mask)
        pal_frames.append(p)
    pal_frames[0].save(gif_path, save_all=True, append_images=pal_frames[1:],
                       duration=ms, loop=0, transparency=255, disposal=2)

    manifest = {
        "schema": "cs-game-anim-gen/manifest@1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "name": args.name,
        "mode": task_mode(args),
        "model": args.model,
        "source_video": str(Path(args.from_video).resolve()) if args.from_video else None,
        "context": args.context,
        "loop": bool(meta.get("loop", args.loop)),
        "fps": fps,
        "requested_fps": args.fps,
        "frame_count": n,
        "duration_seconds": round(n / fps, 3),
        "cell": meta.get("cell") or {"width": cw, "height": ch},
        "grid": {"cols": cols, "rows": rows},
        "sheet": str(sheet_path.resolve()),
        "gif": str(gif_path.resolve()),
        "frames_dir": str(frames_dir.resolve()),
        "frames": [{"index": i, "file": names[i]} for i in range(n)],
        "alpha": meta.get("alpha", args.alpha),
    }
    metrics = (frames_result or {}).get("metrics") or meta.get("metrics")
    if metrics:
        manifest["metrics"] = metrics
    if meta.get("source_fps") or (frames_result or {}).get("source_fps"):
        manifest["source_fps"] = meta.get("source_fps") or frames_result.get("source_fps")
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "status": "success",
        "stage": "sheet",
        "sheet": str(sheet_path.resolve()),
        "gif": str(gif_path.resolve()),
        "manifest": str(manifest_path.resolve()),
        "grid": {"cols": cols, "rows": rows},
        "frame_count": n,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def generate():
    parser = JsonArgumentParser(
        description="Generate 2D animation assets (video, frames, sprite sheet) via wan3.0-video.")
    parser.add_argument("character_image", nargs="?", help="Character art: local path or HTTP(S) URL")
    parser.add_argument("context", nargs="?", help="Animation context: action, facing, loop intent, style")
    parser.add_argument("--stage", choices=STAGES, default="all")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="wan3.0-video or wan3.0-video-prime")
    parser.add_argument("--from-video", help="Reuse an existing MP4; skips the paid video stage")
    parser.add_argument("--submit-only", action="store_true",
                        help="Submit the task and return immediately with its task_id; no polling")
    parser.add_argument("--task-id", help="Resume an existing task: poll and download without resubmitting")
    parser.add_argument("--edit-from", help="Edit an existing clip (reference_video): URL, or a local "
                                            "MP4 with its .source.json sidecar")
    parser.add_argument("--extend-from", help="Extend an existing clip (reference_video): same input rules")
    parser.add_argument("--extend-direction", choices=tuple(EXTEND_DIRECTIONS), default="forward",
                        help="Extend forward from the last frame or backward to the first (default forward)")
    parser.add_argument("--name", help="Descriptive asset name used in file names and the manifest")
    parser.add_argument("--loop", action="store_true",
                        help="Seamless cycle: sends the character as both first and last frame")
    parser.add_argument("--duration", type=int, default=3, help="Video seconds, 2-30 (default 3)")
    parser.add_argument("--resolution", choices=RESOLUTIONS, default="480P",
                        help="Output tier (default 480P; the API default 1080P is deliberately not used)")
    parser.add_argument("--ratio", choices=RATIOS, default="adaptive")
    parser.add_argument("--fps", type=int, default=12, help="Sprite frame rate (default 12)")
    parser.add_argument("--max-frames", type=int, default=48, help="Cap sampled frames (default 48)")
    parser.add_argument("--alpha", choices=("rembg", "matte", "none"), default="rembg",
                        help="Background cutout: rembg (AI, painted scenes), matte "
                             "(border-connected color key, no extra dependency), none")
    parser.add_argument("--matte-color", default="ffffff",
                        help="Key color for --alpha matte, 6-digit hex (default ffffff)")
    parser.add_argument("--matte-tolerance", type=int, default=30,
                        help="Color distance tolerance for --alpha matte, 0-120 (default 30)")
    parser.add_argument("--no-bg-hint", action="store_true",
                        help="Do not ask the model for a flat solid background")
    parser.add_argument("--flatten-color", default="ffffff",
                        help="Hex color used when flattening transparent input (default ffffff)")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="Nearest-neighbour frame scale, 0.125-8 (pixel-art downscale)")
    parser.add_argument("--colors", type=int,
                        help="Reduce the whole sequence to one shared palette of N colors, 2-255")
    parser.add_argument("--pad", type=int, default=4, help="Padding around the union subject box")
    parser.add_argument("--sheet-cols", type=int, help="Sprite sheet columns (auto if omitted)")
    parser.add_argument("--audio", action="store_true",
                        help="Request an audio track (off by default; game sprites rarely need it)")
    parser.add_argument("--seed", type=int, help="Reproduction seed")
    parser.add_argument("--no-prompt-extend", action="store_true")
    parser.add_argument("--out", default="generated-animations", help="Output directory")
    parser.add_argument("--poll-interval", type=int, default=10)
    parser.add_argument("--max-poll-time", type=int, default=900)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the request payload and exit without calling the API")
    args = parser.parse_args()

    mode = task_mode(args)
    # edit/extend take one positional: the instruction. argparse would otherwise
    # fill character_image first, so shift a lone positional into context.
    if mode != "generate" and args.context is None and args.character_image is not None:
        args.context = args.character_image
        args.character_image = None
    resuming = bool(args.task_id)
    needs_generation = (args.stage in ("video", "all") and not args.from_video
                        and not resuming and mode == "generate")
    if args.edit_from and args.extend_from:
        fail("INVALID_ARGUMENTS", "--edit-from and --extend-from are mutually exclusive")
    if resuming and args.submit_only:
        fail("INVALID_ARGUMENTS", "--task-id resumes a task; it cannot be combined with --submit-only")
    if resuming and (args.from_video or args.edit_from or args.extend_from):
        fail("INVALID_ARGUMENTS", "--task-id only polls an existing task; drop the source arguments")
    if args.submit_only and args.from_video:
        fail("INVALID_ARGUMENTS", "--submit-only submits a new task; drop --from-video")
    if mode != "generate":
        if args.loop:
            fail("INVALID_ARGUMENTS", "--loop applies to generation only, not edit/extend")
        if args.character_image:
            fail("INVALID_ARGUMENTS", "edit/extend takes a source clip, not a character image")
        if args.stage in ("frames", "sheet"):
            fail("INVALID_ARGUMENTS", "edit/extend are generation modes; use --stage video or all")
    if resuming and args.stage in ("frames", "sheet"):
        fail("INVALID_ARGUMENTS", "--task-id resumes the video stage; use --stage video or all")

    requires_context = args.dry_run or needs_generation or mode != "generate"
    if requires_context and not args.context:
        fail("INVALID_ARGUMENTS", "<context> is required")
    if (needs_generation or (args.dry_run and mode == "generate")) and not args.character_image:
        fail("INVALID_ARGUMENTS", "<character_image> is required for generation")
    if args.model not in MODELS:
        fail("INVALID_MODEL", "Unknown model '%s'. Allowed: %s" % (args.model, ", ".join(MODELS)))
    if mode != "edit" and not 2 <= args.duration <= 30:
        fail("INVALID_DURATION", "--duration must be between 2 and 30 seconds")
    if args.fps < 1 or args.fps > 30:
        fail("INVALID_FPS", "--fps must be between 1 and 30")
    if args.max_frames < 1:
        fail("INVALID_ARGUMENTS", "--max-frames must be positive")
    if args.pad < 0:
        fail("INVALID_ARGUMENTS", "--pad must not be negative")
    if args.sheet_cols and args.sheet_cols < 1:
        fail("INVALID_ARGUMENTS", "--sheet-cols must be positive")
    if args.poll_interval <= 0 or args.max_poll_time <= 0:
        fail("INVALID_POLL_TIME", "Poll interval and maximum poll time must be positive")
    if args.stage in ("frames", "sheet") and not args.from_video:
        fail("INVALID_ARGUMENTS", "--stage frames/sheet requires --from-video <mp4>")
    if args.stage == "video" and args.from_video:
        fail("INVALID_ARGUMENTS",
             "--stage video generates a new video; drop --from-video or use --stage frames/sheet/all")
    if args.loop and args.stage in ("frames", "sheet"):
        log("note: --loop only affects generation; frame sampling already assumes a cycle")

    args.matte_rgb = parse_color(args.matte_color)
    # Flattening a transparent input onto the key color keeps the generated
    # background removable by --alpha matte.
    if (args.alpha == "matte" and args.flatten_color.lower().lstrip("#") == "ffffff"
            and args.matte_color.lower().lstrip("#") != "ffffff"):
        args.flatten_color = args.matte_color
        log("flattening transparent input onto the matte key color #%s"
            % args.matte_color.lower().lstrip("#"))
    flatten = parse_color(args.flatten_color)
    if not 0 <= args.matte_tolerance <= 120:
        fail("INVALID_ARGUMENTS", "--matte-tolerance must be between 0 and 120")
    if not 0.125 <= args.scale <= 8:
        fail("INVALID_ARGUMENTS", "--scale must be between 0.125 and 8")
    if args.colors is not None and not 2 <= args.colors <= 255:
        fail("INVALID_ARGUMENTS", "--colors must be between 2 and 255")
    data_uri = None
    if mode == "generate" and (needs_generation or args.dry_run):
        if re.match(r"^https?://", args.character_image, re.IGNORECASE):
            data_uri = args.character_image
        else:
            data_uri, _ = load_character_image(args.character_image, flatten)
    args.source_video_url = (resolve_source_video(args, probe=not args.dry_run)
                             if mode != "generate" else None)

    results = []
    if args.stage in ("video", "all") and not args.from_video:
        results.append(run_video_stage(args, data_uri))
        last = results[-1]
        if last.get("status") == "dry-run":
            return last
        if last.get("status") == "submitted":
            return {"status": "submitted", "stages": results,
                    "task_id": last["task_id"], "resume": last["resume"]}
        args.from_video = last["video"]["path"]
    frames_result = None
    if args.stage in ("frames", "all"):
        frames_result = run_frames_stage(args)
        results.append(frames_result)
    if args.stage in ("sheet", "all"):
        results.append(run_sheet_stage(args, frames_result))

    payload = {"status": "success", "stages": results, "visual_review": "pending"}
    if results and results[0].get("video"):
        payload["video"] = results[0]["video"]
    return payload


def main():
    exit_code = 0
    try:
        payload = generate()
    except GenerationError as exc:
        payload = {"status": "error", "error": exc.code, "message": str(exc), **exc.extra}
        exit_code = 3 if exc.code in API_ERRORS else 2
    except OSError as exc:
        payload = {"status": "error", "error": "IO_ERROR", "message": str(exc)}
        exit_code = 2
    print(redact(json.dumps(payload, ensure_ascii=False, indent=2)))
    if exit_code:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
