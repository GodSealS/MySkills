#!/usr/bin/env python3
"""Generate game art via the Qianwen platform Token Plan image API.

Supported models: wan2.7-image-pro (default), wan2.7-image, qwen-image-3.0-pro.
Auth: ANTHROPIC_AUTH_TOKEN (sk-sp- Token Plan key, the official docs' env name),
falling back to QWEN_API_KEY, then TOKEN_PLAN_API_KEY (never printed).
Endpoint host: QWEN_IMAGE_BASE_URL, else QWEN_BASE_URL with any
"/compatible-mode/v1" suffix stripped, else https://token-plan.maas.qianwenaiapi.com.
The sk-sp- key belongs to that platform; the aliyuncs.com Token Plan host is a
DIFFERENT platform and rejects this key with 401.

Usage:
  python gen_image.py [model] <prompt> [reference_image] [options]

Official request contract (platform.qianwenai.com docs, checked 2026-11-18;
see references/provider-notes.md for scope):
  POST {host}/api/v1/services/aigc/multimodal-generation/generation
  {"model": ..., "input": {"messages": [{"role": "user",
    "content": [{"image": "<url|data-uri>"}, {"text": "<prompt>"}]}]},
   "parameters": {"size": "1024*1024", "n": 1-4, "negative_prompt": ...,
                  "prompt_extend": bool, "enable_sequential": bool}}
  -> 200 sync; images at output.choices[].message.content[].image (PNG, 24 h).
  T2I content is a single text object; reference-image (I2I) content adds 1-3
  image objects before the text. enable_sequential is a legacy wan-set feature,
  unverified on this platform. Defensive /api/v1/tasks/<id> polling is kept for
  gateways that answer with a task_id.

Outputs one JSON object on stdout (except --help); progress logs go to stderr.
Success covers decoding, count and explicit pixel dimensions; visual review is pending.
Exit codes: 0 success, 2 usage/local error, 3 API/generation error.
"""

import argparse
import base64
import http.client
import io
import json
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
GEN_PATH = "/api/v1/services/aigc/multimodal-generation/generation"
TASK_PATH = "/api/v1/tasks/"


def resolve_host():
    base = (os.environ.get("QWEN_IMAGE_BASE_URL", "").strip()
            or os.environ.get("QWEN_BASE_URL", "").strip())
    if base:
        return re.sub(r"/compatible-mode/v\d+/?$", "", base.rstrip("/"))
    return DEFAULT_HOST


def resolve_api_key():
    # ANTHROPIC_AUTH_TOKEN is the official Token Plan docs' env name and the
    # user's designated key source; it wins over legacy QWEN_API_KEY.
    for var in ("ANTHROPIC_AUTH_TOKEN", "QWEN_API_KEY", "TOKEN_PLAN_API_KEY"):
        key = os.environ.get(var, "").strip()
        if key:
            return key
    return ""


MODELS = ("wan2.7-image-pro", "wan2.7-image", "qwen-image-3.0-pro")
DEFAULT_MODEL = "wan2.7-image-pro"
MAX_REF_BYTES = 10 * 1024 * 1024
HTTP_TIMEOUT = 240
API_ERRORS = {"API_ERROR", "TASK_FAILED", "TIMEOUT", "DOWNLOAD_FAILED", "NETWORK_ERROR",
              "INVALID_RESPONSE", "INVALID_IMAGE", "IMAGE_COUNT_MISMATCH", "IMAGE_SIZE_MISMATCH"}


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
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
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
    if "output" in data and not isinstance(data["output"], dict):
        fail("INVALID_RESPONSE", "Provider output must be a JSON object")
    return data


def image_decoder():
    try:
        from PIL import Image
    except ImportError:
        fail("MISSING_DEPENDENCY", "Image decoding requires Pillow: python -m pip install Pillow")
    return Image


def encode_reference(ref):
    """Return an image reference usable in the API payload: URL passthrough or base64 data URI."""
    if re.match(r"^https?://", ref, re.IGNORECASE):
        return ref
    path = Path(ref)
    if not path.is_file():
        fail("REFERENCE_NOT_FOUND", "Reference image not found: %s" % ref)
    size = path.stat().st_size
    if size > MAX_REF_BYTES:
        fail("REFERENCE_TOO_LARGE",
             "Reference image %s is %.1f MB, limit is %d MB" % (
                 path.name, size / 1048576, MAX_REF_BYTES // 1048576))
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return "data:%s;base64,%s" % (mime, data)


def build_payload(args):
    content = []
    if args.reference:
        content.append({"image": encode_reference(args.reference)})
    content.append({"text": args.prompt})

    parameters = {"prompt_extend": not args.no_prompt_extend}
    if args.size:
        parameters["size"] = args.size
    if args.n > 1:
        parameters["n"] = args.n
    if args.negative:
        parameters["negative_prompt"] = args.negative
    if args.sequential:
        parameters["enable_sequential"] = True

    return {
        "model": args.model,
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": parameters,
    }


def extract_image_urls(data):
    urls = []
    output = data.get("output", data)
    choices = output.get("choices") or []
    results = output.get("results") or []
    if not isinstance(choices, list) or not isinstance(results, list):
        fail("INVALID_RESPONSE", "Provider choices/results must be arrays")
    for choice in choices:
        if not isinstance(choice, dict):
            fail("INVALID_RESPONSE", "Provider choice must be an object")
        message = choice.get("message") or {}
        if not isinstance(message, dict):
            fail("INVALID_RESPONSE", "Provider message must be an object")
        content = message.get("content") or []
        if isinstance(content, str):
            continue  # Text-only choice; it contains no generated images.
        if not isinstance(content, list):
            fail("INVALID_RESPONSE", "Provider content must be an array or text")
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("image"):
                urls.append(item["image"])
            elif item.get("type") == "image_url" and isinstance(item.get("image_url"), dict):
                urls.append(item["image_url"].get("url"))
    for result in results:
        if isinstance(result, dict) and result.get("url"):
            urls.append(result["url"])
    if any(not isinstance(url, str) or not re.match(r"^https?://", url, re.IGNORECASE)
           for url in urls):
        fail("INVALID_RESPONSE", "Result images must have HTTP(S) URLs")
    return list(dict.fromkeys(urls))


def poll_task(host, task_id, api_key, interval, max_wait):
    deadline = time.monotonic() + max_wait
    headers = {"Authorization": "Bearer " + api_key}
    while time.monotonic() < deadline:
        time.sleep(min(interval, max(0, deadline - time.monotonic())))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        status, body = http_request(host + TASK_PATH + task_id, headers=headers,
                                    timeout=min(HTTP_TIMEOUT, remaining))
        text = body.decode("utf-8", errors="replace")
        if status != 200:
            fail("API_ERROR", "Task query failed (HTTP %d): %s" % (status, text[:500]),
                 http_status=status)
        data = parse_response(body)
        output = data.get("output") or {}
        task_status = output.get("task_status") or ""
        if not isinstance(task_status, str):
            fail("INVALID_RESPONSE", "Provider task_status must be text")
        task_status = task_status.upper()
        log("task %s: %s" % (task_id, task_status or "UNKNOWN"))
        if task_status in ("SUCCEEDED", "SUCCESS"):
            return data
        if task_status in ("FAILED", "CANCELED", "CANCELLED", "UNKNOWN_ERROR"):
            fail("TASK_FAILED",
                 output.get("message") or data.get("message") or "Generation task failed",
                 task_id=task_id, provider_code=output.get("code") or data.get("code"))
    fail("TIMEOUT", "Task %s did not finish within %d s" % (task_id, max_wait), task_id=task_id)


def download_image(url, dest_dir, index, model):
    status, data = http_request(url, timeout=300)
    if status != 200:
        fail("DOWNLOAD_FAILED", "Failed to download result image (HTTP %d) from %s" % (status, url[:200]))
    Image = image_decoder()
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
        with Image.open(io.BytesIO(data)) as img:
            img.load()  # Header recognition alone does not prove the pixels decode.
            width, height, fmt = img.width, img.height, img.format
        ext = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}.get(fmt)
        if not ext:
            fail("INVALID_IMAGE", "Unsupported output image format: %s" % fmt)
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
        fail("INVALID_IMAGE", "Result does not decode as a complete image: %s" % exc)

    dest_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_model = re.sub(r"[^A-Za-z0-9._-]", "_", model)
    # NamedTemporaryFile uses random names and exclusive creation, including across processes.
    with tempfile.NamedTemporaryFile(mode="wb", dir=str(dest_dir), delete=False,
            prefix="%s-%s-%d-" % (stamp, safe_model, index), suffix=ext) as target:
        path = Path(target.name)
        try:
            target.write(data)
            target.flush()
        except OSError:
            target.close()
            path.unlink()
            raise
    return {"path": str(path.resolve()), "url": url, "width": width, "height": height, "format": fmt}


def generate():
    parser = JsonArgumentParser(description="Generate images via Aliyun Bailian models.")
    parser.add_argument("inputs", nargs="+", metavar="ARG", help="[model] prompt [reference_image]")
    parser.add_argument("--model", help="Explicit model id (avoids positional ambiguity)")
    parser.add_argument("--reference", help="Reference image: local path or HTTP(S) URL")
    parser.add_argument("--size", help='Image size, e.g. "1K", "2K", "1024*1024" (model default if omitted)')
    parser.add_argument("--n", type=int, default=1, help="Number of images (1-4, default 1)")
    parser.add_argument("--negative", help="Negative prompt")
    parser.add_argument("--sequential", action="store_true",
                        help="Enable sequential consistency for multi-image sets (wan models)")
    parser.add_argument("--no-prompt-extend", action="store_true",
                        help="Disable server-side prompt expansion")
    parser.add_argument("--out", default="generated-images",
                        help="Output directory (default: ./generated-images)")
    parser.add_argument("--poll-interval", type=int, default=5, help="Async poll interval seconds (default 5)")
    parser.add_argument("--max-poll-time", type=int, default=600, help="Max async wait seconds (default 600)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the request payload and exit without calling the API")
    args = parser.parse_args()

    # A recognized leading model is optional; two other positionals mean prompt + reference.
    values = list(args.inputs)
    if args.model is None:
        args.model = values.pop(0) if values[0] in MODELS else DEFAULT_MODEL
    if not 1 <= len(values) <= 2 or (len(values) == 2 and args.reference is not None):
        fail("INVALID_ARGUMENTS", "Use [model] prompt [reference], or prompt --model MODEL --reference IMAGE")
    args.prompt = values[0]
    if len(values) == 2:
        args.reference = values[1]
    if args.model not in MODELS:
        fail("INVALID_MODEL", "Unknown model '%s'. Allowed: %s" % (args.model, ", ".join(MODELS)))
    if not args.prompt.strip():
        fail("EMPTY_PROMPT", "Prompt must not be empty")
    if args.n < 1 or args.n > 4:
        fail("INVALID_N", "--n must be between 1 and 4")
    if args.poll_interval <= 0 or args.max_poll_time <= 0:
        fail("INVALID_POLL_TIME", "Poll interval and maximum poll time must be positive")
    if args.sequential and not args.model.startswith("wan"):
        fail("INVALID_PARAMETERS", "--sequential is supported only for wan models")

    api_key = resolve_api_key()
    if not args.dry_run and not api_key:
        fail("MISSING_API_KEY", "Set ANTHROPIC_AUTH_TOKEN (or QWEN_API_KEY / TOKEN_PLAN_API_KEY)")

    host = resolve_host()
    gen_endpoint = host + GEN_PATH
    payload = build_payload(args)

    if args.dry_run:
        preview = json.loads(json.dumps(payload))
        for item in preview["input"]["messages"][0]["content"]:
            if "image" in item and str(item["image"]).startswith("data:"):
                item["image"] = "data:...base64 (%d chars omitted)" % (len(item["image"]) - 30)
        return {"status": "dry-run", "endpoint": gen_endpoint, "payload": preview}

    image_decoder()  # Check the local decoder before making a paid generation request.

    log("model=%s n=%d size=%s reference=%s endpoint=%s" % (
        args.model, args.n, args.size or "default", "yes" if args.reference else "no", gen_endpoint))

    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    status, body = http_request(gen_endpoint, data=data, headers=headers)
    text = body.decode("utf-8", errors="replace")
    if status != 200:
        hint = ""
        if status in (401, 403):
            hint = (" Check that the key matches the endpoint platform: sk-sp- Token Plan"
                    " keys belong to token-plan.maas.qianwenaiapi.com (QWEN_IMAGE_BASE_URL).")
        fail("API_ERROR", "Generation request failed (HTTP %d):%s %s" % (status, hint, text[:800]),
             http_status=status)

    resp = parse_response(body)
    output = resp.get("output") or {}
    if output.get("task_id") and not extract_image_urls(resp):
        if not isinstance(output["task_id"], str):
            fail("INVALID_RESPONSE", "Provider task_id must be text")
        log("async task submitted: %s" % output["task_id"])
        resp = poll_task(host, output["task_id"], api_key, args.poll_interval, args.max_poll_time)

    urls = extract_image_urls(resp)
    if not urls:
        fail("API_ERROR", "No image URLs in API response: %s" % json.dumps(resp, ensure_ascii=False)[:800])

    out_dir = Path(args.out)
    files = []
    try:
        for i, url in enumerate(urls, start=1):
            entry = download_image(url, out_dir, i, args.model)
            files.append(entry)
            log("saved %s" % entry["path"])
        exact_size = re.fullmatch(r"(\d+)[*x](\d+)", args.size or "")
        if exact_size:
            expected = tuple(map(int, exact_size.groups()))
            if any((entry["width"], entry["height"]) != expected for entry in files):
                fail("IMAGE_SIZE_MISMATCH", "Decoded image dimensions differ from --size",
                     expected_width=expected[0], expected_height=expected[1])
        if len(files) != args.n:
            fail("IMAGE_COUNT_MISMATCH", "Generated image count differs from --n")
    except OSError as exc:
        fail("IO_ERROR", str(exc), model=args.model, requested=args.n, count=len(files), files=files)
    except GenerationError as exc:
        exc.extra.update(model=args.model, requested=args.n, count=len(files), files=files)
        raise

    return {
        "status": "success",
        "model": args.model,
        "requested": args.n,
        "count": len(files),
        "files": files,
        "visual_review": "pending",
    }


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
