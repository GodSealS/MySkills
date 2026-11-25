"""Offline CLI regressions; no credentials or provider calls are used.

Run: python -B -m unittest discover -s tests -p test_game_image_gen.py -v
Set GAME_IMAGE_GEN_SKILL_DIR to run the same contract against an adapter bundle.
"""

import contextlib
import builtins
import http.client
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch
import urllib.error

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path(os.environ.get(
    "GAME_IMAGE_GEN_SKILL_DIR", ROOT / ".codebuddy/skills/cs-game-image-gen"))
SPEC = importlib.util.spec_from_file_location("game_image_gen", BUNDLE / "scripts/gen_image.py")
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def api_response(urls):
    return {"output": {"choices": [{"message": {
        "content": [{"type": "image", "image": url} for url in urls]}}]}}


def encoded(data):
    return 200, json.dumps(data).encode("utf-8")


def image_bytes(fmt="PNG", size=(16, 8)):
    stream = io.BytesIO()
    Image.new("RGB", size, "#705030").save(stream, format=fmt)
    return stream.getvalue()


class GameImageGenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="game-image-gen-test-")
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.ref = self.out / "reference image.png"
        self.ref.write_bytes(image_bytes())
        self.url = "https://example.invalid/result.png"
        # Fail closed: every test blocks the real transport even if a mock is missed.
        self.network = patch.object(gen.urllib.request, "urlopen",
                                    side_effect=AssertionError("Unexpected network call"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def invoke(self, *args, responses=None, env=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        environment = {"QWEN_API_KEY": "offline-test-placeholder", "TOKEN_PLAN_API_KEY": "",
                       "ANTHROPIC_AUTH_TOKEN": "", "QWEN_BASE_URL": "", "QWEN_IMAGE_BASE_URL": ""}
        environment.update(env or {})
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, environment))
            stack.enter_context(patch.object(gen.sys, "argv", ["gen_image.py", *args]))
            stack.enter_context(contextlib.redirect_stdout(stdout))
            stack.enter_context(contextlib.redirect_stderr(stderr))
            if responses is not None:
                stack.enter_context(patch.object(gen, "http_request", side_effect=responses))
            exit_code = 0
            try:
                gen.main()
            except SystemExit as exc:
                exit_code = exc.code
        # json.loads also rejects duplicate/trailing JSON documents on stdout.
        result = json.loads(stdout.getvalue())
        self.assertNotIn("offline-test-placeholder", stdout.getvalue() + stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        return exit_code, result

    def generate(self, *args, responses=None):
        return self.invoke("knight", "--out", str(self.out / "results"),
                           *args, responses=responses)

    def test_optional_model_and_reference_forms(self):
        for explicit in (False, True):
            for reference in (None, str(self.ref), self.url):
                with self.subTest(explicit=explicit, reference=reference):
                    args = ([gen.DEFAULT_MODEL] if explicit else []) + ["knight"]
                    if reference:
                        args.append(reference)
                    code, result = self.invoke(*args, "--dry-run", env={"QWEN_API_KEY": ""})
                    self.assertEqual(code, 0)
                    payload = result["payload"]
                    self.assertEqual(payload["model"], gen.DEFAULT_MODEL)
                    self.assertEqual(payload["input"]["messages"][0]["content"][-1], {"text": "knight"})
                    self.assertEqual(len(payload["input"]["messages"][0]["content"]), 2 if reference else 1)
                    self.assertNotIn("modalities", payload)

    def test_named_model_and_reference(self):
        code, result = self.invoke("knight", "--model", "qwen-image-3.0-pro",
                                   "--reference", self.url, "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(result["payload"]["model"], "qwen-image-3.0-pro")
        self.assertEqual(result["payload"]["input"]["messages"][0]["content"][0], {"image": self.url})

    def test_invalid_arguments_are_json(self):
        for args in ([], ["knight", "--n", "bad"], [gen.DEFAULT_MODEL],
                     ["knight", "--unknown"], ["knight", self.url, "--reference", self.url]):
            with self.subTest(args=args):
                code, result = self.invoke(*args, "--dry-run")
                self.assertEqual(code, 2)
                self.assertEqual(result["error"], "INVALID_ARGUMENTS")

    def test_invalid_model(self):
        code, result = self.invoke("knight", "--model", "bad-model", "--dry-run")
        self.assertEqual((code, result["error"]), (2, "INVALID_MODEL"))

    def test_invalid_local_values(self):
        for args, error in (([" "], "EMPTY_PROMPT"), (["knight", "--n", "0"], "INVALID_N"),
                            (["knight", "--n", "5"], "INVALID_N"),
                            (["knight", "--poll-interval", "0"], "INVALID_POLL_TIME"),
                            (["knight", "--max-poll-time", "-1"], "INVALID_POLL_TIME")):
            with self.subTest(args=args):
                code, result = self.invoke(*args, "--dry-run")
                self.assertEqual((code, result["error"]), (2, error))

    def test_missing_key(self):
        code, result = self.invoke("knight", env={"QWEN_API_KEY": ""})
        self.assertEqual((code, result["error"]), (2, "MISSING_API_KEY"))

    def test_key_resolution_prefers_anthropic_auth_token(self):
        with patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN": "token-a", "QWEN_API_KEY": "token-q",
                                     "TOKEN_PLAN_API_KEY": "token-t"}):
            self.assertEqual(gen.resolve_api_key(), "token-a")
        with patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN": "", "QWEN_API_KEY": "token-q",
                                     "TOKEN_PLAN_API_KEY": "token-t"}):
            self.assertEqual(gen.resolve_api_key(), "token-q")

    def test_missing_reference(self):
        code, result = self.invoke("knight", str(self.out / "absent.png"), "--dry-run")
        self.assertEqual((code, result["error"]), (2, "REFERENCE_NOT_FOUND"))

    def test_reference_payload_and_dry_run_redaction(self):
        code, result = self.invoke("knight", str(self.ref), "--dry-run", "--size", "2K",
                                   "--n", "4", "--sequential", "--negative", "blur",
                                   "--no-prompt-extend")
        self.assertEqual(code, 0)
        payload = result["payload"]
        self.assertEqual(payload["parameters"], {"size": "2K", "n": 4,
                         "enable_sequential": True, "negative_prompt": "blur", "prompt_extend": False})
        self.assertNotIn("size", payload)
        self.assertIn("omitted", payload["input"]["messages"][0]["content"][0]["image"])

    def test_task_failure_preserves_provider_code(self):
        for state in ("FAILED", "CANCELED"):
            with self.subTest(state=state), patch.object(gen.time, "sleep"):
                code, result = self.generate(responses=[encoded({"output": {"task_id": "task-1"}}),
                    encoded({"output": {"task_status": state, "code": "BadPrompt", "message": "rejected"}})])
                self.assertEqual((code, result["error"]), (3, "TASK_FAILED"))
                self.assertEqual(result["provider_code"], "BadPrompt")
                self.assertEqual(result["message"], "rejected")
                self.assertEqual(result["task_id"], "task-1")

    def test_async_success(self):
        final = api_response([self.url])
        final["output"]["task_status"] = "SUCCEEDED"
        with patch.object(gen.time, "sleep"):
            code, result = self.generate(responses=[encoded({"output": {"task_id": "task-1"}}),
                encoded({"output": {"task_status": "RUNNING"}}), encoded(final), (200, image_bytes())])
        self.assertEqual((code, result["count"]), (0, 1))

    def test_network_failures_are_json(self):
        for error in (urllib.error.URLError("mock disconnected"), TimeoutError("mock timeout"),
                      http.client.IncompleteRead(b"incomplete")):
            with self.subTest(error=error), patch.object(gen.urllib.request, "urlopen", side_effect=error):
                code, result = self.generate()
                self.assertEqual((code, result["error"]), (3, "NETWORK_ERROR"))

    def test_http_error_transport_is_preserved(self):
        error = urllib.error.HTTPError("https://example.invalid/api", 429, "Too Many Requests", {},
                                      io.BytesIO(b'{"code":"Throttling","message":"slow down"}'))
        with patch.object(gen.urllib.request, "urlopen", side_effect=error):
            code, result = self.generate()
        self.assertEqual((code, result["error"], result["http_status"]), (3, "API_ERROR", 429))
        self.assertIn("Throttling", result["message"])

    def test_missing_decoder_prevents_paid_request(self):
        real_import = builtins.__import__

        def without_pillow(name, *args, **kwargs):
            if name == "PIL":
                raise ImportError("mock missing dependency")
            return real_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=without_pillow):
            code, result = self.generate()
        self.assertEqual((code, result["error"]), (2, "MISSING_DEPENDENCY"))

    def test_poll_deadline_stops_before_next_http_request(self):
        with patch.object(gen.time, "monotonic", side_effect=[0, 0, 0, 2]), patch.object(gen.time, "sleep"):
            code, result = self.generate("--max-poll-time", "1", responses=[
                encoded({"output": {"task_id": "task-1"}})])
        self.assertEqual((code, result["error"]), (3, "TIMEOUT"))
        self.assertEqual(result["task_id"], "task-1")

    def test_credentials_redacted_from_provider_error(self):
        code, result = self.generate(responses=[(400, b'{"message":"offline-test-placeholder"}')])
        self.assertEqual(code, 3)
        self.assertIn("[REDACTED]", result["message"])

    def test_sequential_rejects_unsupported_model(self):
        code, result = self.invoke("knight", "--model", "qwen-image-3.0-pro", "--sequential", "--dry-run")
        self.assertEqual((code, result["error"]), (2, "INVALID_PARAMETERS"))

    def test_invalid_response_is_json(self):
        for body in (b"<html>proxy error</html>", b"[]", b'{"output": []}',
                     b'{"output": {"choices": 123}}', b'{"output": {"choices": [null]}}'):
            with self.subTest(body=body):
                code, result = self.generate(responses=[(200, body)])
                self.assertEqual((code, result["error"]), (3, "INVALID_RESPONSE"))

    def test_invalid_poll_response_is_json(self):
        with patch.object(gen.time, "sleep"):
            code, result = self.generate(responses=[encoded({"output": {"task_id": "task-1"}}),
                                                   (200, b"not json")])
        self.assertEqual((code, result["error"]), (3, "INVALID_RESPONSE"))

    def test_http_failure(self):
        code, result = self.generate(responses=[(401, b'{"code":"InvalidApiKey","message":"rejected"}')])
        self.assertEqual((code, result["error"]), (3, "API_ERROR"))
        self.assertIn("InvalidApiKey", result["message"])

    def test_decode_metadata_and_extension(self):
        for fmt, extension in (("PNG", ".png"), ("JPEG", ".jpg"), ("WEBP", ".webp")):
            with self.subTest(fmt=fmt):
                code, result = self.generate("--size", "16*8", responses=[
                    encoded(api_response([self.url])), (200, image_bytes(fmt))])
                self.assertEqual((code, result["status"]), (0, "success"))
                self.assertEqual(result["visual_review"], "pending")
                entry = result["files"][0]
                self.assertEqual((entry["width"], entry["height"], entry["format"]), (16, 8, fmt))
                self.assertEqual(Path(entry["path"]).suffix, extension)
                self.assertTrue(Path(entry["path"]).is_absolute())

    def test_corrupt_image_rejected_before_save(self):
        for data in (b"", b"not an image", image_bytes()[:45]):
            with self.subTest(data=data):
                code, result = self.generate(responses=[encoded(api_response([self.url])), (200, data)])
                self.assertEqual((code, result["error"]), (3, "INVALID_IMAGE"))
                self.assertEqual(list((self.out / "results").glob("*")), [])

    def test_size_mismatch_preserves_download_and_reports_error(self):
        code, result = self.generate("--size", "32*32", responses=[
            encoded(api_response([self.url])), (200, image_bytes())])
        self.assertEqual((code, result["error"]), (3, "IMAGE_SIZE_MISMATCH"))
        self.assertTrue(Path(result["files"][0]["path"]).is_file())

    def test_short_count_preserves_download_and_reports_error(self):
        code, result = self.generate("--n", "4", responses=[
            encoded(api_response([self.url])), (200, image_bytes())])
        self.assertEqual((code, result["error"]), (3, "IMAGE_COUNT_MISMATCH"))
        self.assertEqual((result["requested"], result["count"]), (4, 1))
        self.assertTrue(Path(result["files"][0]["path"]).is_file())

    def test_duplicate_result_url_does_not_satisfy_count(self):
        code, result = self.generate("--n", "2", responses=[
            encoded(api_response([self.url, self.url])), (200, image_bytes())])
        self.assertEqual((code, result["error"], result["count"]), (3, "IMAGE_COUNT_MISMATCH", 1))

    def test_complete_batch(self):
        urls = ["https://example.invalid/%d.png" % i for i in range(4)]
        code, result = self.generate("--n", "4", "--sequential", responses=[
            encoded(api_response(urls)), *[(200, image_bytes()) for _ in urls]])
        self.assertEqual((code, result["status"], result["count"]), (0, "success", 4))
        self.assertEqual(len({item["path"] for item in result["files"]}), 4)

    def test_same_second_calls_preserve_both_files(self):
        with patch.object(gen, "datetime") as clock:
            clock.now.return_value.strftime.return_value = "20261116-120000"
            paths = []
            for fmt in ("PNG", "PNG"):
                code, result = self.generate(responses=[encoded(api_response([self.url])), (200, image_bytes(fmt))])
                self.assertEqual(code, 0)
                paths.append(Path(result["files"][0]["path"]))
        self.assertNotEqual(paths[0], paths[1])
        self.assertTrue(all(path.is_file() for path in paths))

    def test_download_failure_lists_already_saved_files(self):
        code, result = self.generate("--n", "2", responses=[
            encoded(api_response([self.url, "https://example.invalid/second.png"])),
            (200, image_bytes()), (503, b"unavailable")])
        self.assertEqual((code, result["error"]), (3, "DOWNLOAD_FAILED"))
        self.assertEqual(result["count"], 1)
        self.assertTrue(Path(result["files"][0]["path"]).is_file())

    def test_local_write_error_is_json(self):
        with patch.object(gen.Path, "mkdir", side_effect=PermissionError("mock read-only directory")):
            code, result = self.generate(responses=[encoded(api_response([self.url])), (200, image_bytes())])
        self.assertEqual((code, result["error"]), (2, "IO_ERROR"))

    def test_real_cli_from_another_working_directory(self):
        result = subprocess.run([sys.executable, "-B", str((BUNDLE / "scripts/gen_image.py").resolve()),
                                 "knight", str(self.ref), "--dry-run"], cwd=self.out,
                                capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "dry-run")


if __name__ == "__main__":
    unittest.main()
