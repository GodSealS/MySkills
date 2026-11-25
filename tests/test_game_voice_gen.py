"""Offline CLI regressions; no credentials or provider calls are used.

Run: python -B -m unittest discover -s tests -p test_game_voice_gen.py -v
Set GAME_VOICE_GEN_SKILL_DIR to run the same contract against an adapter bundle.
"""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import wave


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path(os.environ.get(
    "GAME_VOICE_GEN_SKILL_DIR", ROOT / ".codebuddy/skills/cs-game-voice-gen"))
SPEC = importlib.util.spec_from_file_location("game_voice_gen", BUNDLE / "scripts/gen_voice.py")
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def wav_bytes(seconds=0.5, rate=22050):
    stream = io.BytesIO()
    with wave.open(stream, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * int(rate * seconds))
    return stream.getvalue()


def wav_bytes_lying_header(seconds=0.5, rate=22050):
    """Stream-written WAV: header claims a huge frame count, payload is short."""
    data = bytearray(wav_bytes(seconds, rate))
    idx = data.find(b"data")
    data[idx + 4:idx + 8] = (0xFFFFFFF0).to_bytes(4, "little")
    data[4:8] = (0xFFFFFFF0).to_bytes(4, "little")
    return bytes(data)


def encoded(data):
    return 200, json.dumps(data).encode("utf-8")


def audio_url_response(url="https://example.invalid/take.wav"):
    return {"output": {"finish_reason": "stop",
                       "audio": {"data": "", "url": url, "id": "audio_x", "expires_at": 1772697707}},
            "usage": {"characters": 15}}


class GameVoiceGenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="game-voice-gen-test-")
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        # Fail closed: every test blocks the real transport even if a mock is missed.
        self.network = patch.object(gen.urllib.request, "urlopen",
                                    side_effect=AssertionError("Unexpected network call"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def invoke(self, *args, responses=None, env=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        environment = {"QWEN_API_KEY": "offline-test-placeholder", "TOKEN_PLAN_API_KEY": "",
                       "ANTHROPIC_AUTH_TOKEN": "", "QWEN_TTS_BASE_URL": ""}
        environment.update(env or {})
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, environment))
            stack.enter_context(patch.object(gen.sys, "argv", ["gen_voice.py", *args]))
            stack.enter_context(contextlib.redirect_stdout(stdout))
            stack.enter_context(contextlib.redirect_stderr(stderr))
            if responses is not None:
                stack.enter_context(patch.object(gen, "http_request", side_effect=responses))
            exit_code = 0
            try:
                gen.main()
            except SystemExit as exc:
                exit_code = exc.code
        result = json.loads(stdout.getvalue())
        self.assertNotIn("offline-test-placeholder", stdout.getvalue() + stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        return exit_code, result

    def write_lines(self, lines, name="lines.json"):
        path = self.out / name
        path.write_text(json.dumps(lines, ensure_ascii=False), encoding="utf-8")
        return str(path)

    # --- dry run and argument validation ---------------------------------

    def test_dry_run_single_needs_no_key(self):
        code, result = self.invoke("你终于来了。", "--voice", "longanlingxin",
                                   "--instructions", "低沉克制", "--dry-run",
                                   env={"QWEN_API_KEY": ""})
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "dry-run")
        self.assertEqual(result["endpoint"], gen.DEFAULT_HOST + gen.GEN_PATH)
        payload = result["payloads"][0]
        self.assertEqual(payload["model"], gen.DEFAULT_MODEL)
        self.assertEqual(payload["input"]["voice"], "longanlingxin")
        self.assertEqual(payload["input"]["format"], "wav")
        self.assertEqual(payload["input"]["instruction"], "低沉克制")
        self.assertNotIn("parameters", payload)
        self.assertNotIn("optimize_instructions", payload["input"])

    def test_dry_run_batch_fallbacks_and_auto_ids(self):
        lines = self.write_lines([{"text": "第一句", "voice": "longanlingxin"},
                                  {"text": "第二句", "instructions": "怒吼"}])
        code, result = self.invoke("--lines", lines, "--voice", "longanlufeng", "--dry-run")
        self.assertEqual(code, 0)
        payloads = result["payloads"]
        self.assertEqual(payloads[0]["input"]["voice"], "longanlingxin")
        self.assertEqual(payloads[1]["input"]["voice"], "longanlufeng")
        self.assertEqual(payloads[1]["input"]["instruction"], "怒吼")
        self.assertNotIn("instruction", payloads[0]["input"])

    def test_delivery_knobs_map_into_input(self):
        code, result = self.invoke("受死吧！", "--voice", "longanlufeng",
                                   "--instructions", "爆发性怒吼", "--rate", "1.2",
                                   "--pitch", "0.9", "--volume", "70", "--seed", "42",
                                   "--sample-rate", "24000", "--dry-run")
        self.assertEqual(code, 0)
        inp = result["payloads"][0]["input"]
        self.assertEqual(inp["rate"], 1.2)
        self.assertEqual(inp["pitch"], 0.9)
        self.assertEqual(inp["volume"], 70)
        self.assertEqual(inp["seed"], 42)
        self.assertEqual(inp["sample_rate"], 24000)

    def test_default_knobs_are_omitted(self):
        code, result = self.invoke("台词", "--voice", "longanlingxin", "--dry-run")
        self.assertEqual(code, 0)
        inp = result["payloads"][0]["input"]
        for field in ("rate", "pitch", "volume", "seed", "sample_rate", "instruction"):
            self.assertNotIn(field, inp)

    def test_invalid_model_rejected(self):
        code, result = self.invoke("test", "--model", "bad-model", "--dry-run")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_MODEL")

    def test_qwen3_tts_family_not_accepted(self):
        # Qwen3-TTS is a different API family; this wrapper speaks Qwen-Audio-TTS only.
        code, result = self.invoke("test", "--model", "qwen3-tts-flash", "--dry-run")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_MODEL")

    def test_invalid_knob_ranges_rejected(self):
        cases = [["--rate", "3"], ["--pitch", "0.1"], ["--volume", "200"],
                 ["--seed", "99999"], ["--sample-rate", "11025"]]
        for extra in cases:
            with self.subTest(extra=extra):
                code, result = self.invoke("test", "--voice", "longanlingxin", *extra)
                self.assertEqual(code, 2)
                self.assertEqual(result["error"], "INVALID_PARAMETERS")

    def test_missing_key_rejected(self):
        code, result = self.invoke("test", "--voice", "longanlingxin", env={"QWEN_API_KEY": ""})
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "MISSING_API_KEY")

    def test_key_resolution_prefers_anthropic_auth_token(self):
        with patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN": "token-a", "QWEN_API_KEY": "token-q",
                                     "TOKEN_PLAN_API_KEY": "token-t"}):
            self.assertEqual(gen.resolve_api_key(), "token-a")
        with patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN": "", "QWEN_API_KEY": "token-q",
                                     "TOKEN_PLAN_API_KEY": "token-t"}):
            self.assertEqual(gen.resolve_api_key(), "token-q")

    def test_missing_voice_rejected(self):
        code, result = self.invoke("test")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "MISSING_VOICE")

    def test_empty_text_rejected(self):
        code, result = self.invoke("   ", "--voice", "longanlingxin")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "EMPTY_TEXT")

    def test_duplicate_batch_ids_rejected(self):
        lines = self.write_lines([{"id": "a", "text": "一"}, {"id": "a", "text": "二"}])
        code, result = self.invoke("--lines", lines, "--voice", "longanlingxin")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_LINES")

    def test_piper_only_flags_rejected(self):
        for extra in (["--instructions", "x"], ["--format", "mp3"], ["--rate", "1.5"],
                      ["--seed", "1"]):
            with self.subTest(extra=extra):
                code, result = self.invoke("test", "--backend", "piper",
                                           "--model", "voice.onnx", *extra)
                self.assertEqual(code, 2)
                self.assertEqual(result["error"], "INVALID_PARAMETERS")

    def test_piper_batch_per_line_instructions_rejected(self):
        lines = self.write_lines([{"id": "a", "text": "一", "instructions": "怒吼"}])
        code, result = self.invoke("--lines", lines, "--backend", "piper", "--model", "voice.onnx")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_PARAMETERS")

    # --- qwen success paths ----------------------------------------------

    def test_qwen_url_audio_success_and_manifest(self):
        responses = [encoded(audio_url_response()), (200, wav_bytes(0.5))]
        code, result = self.invoke("你终于来了。", "--voice", "longanlingxin", "--character", "hero",
                                   "--name", "hero_greet_01", "--out", str(self.out / "v"),
                                   responses=responses)
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "success")
        entry = result["lines"][0]
        self.assertEqual(entry["id"], "hero_greet_01")
        self.assertEqual(entry["character"], "hero")
        self.assertEqual(entry["format"], "wav")
        self.assertAlmostEqual(entry["duration_seconds"], 0.5, places=2)
        self.assertEqual(entry["sample_rate"], 22050)
        self.assertEqual(entry["usage"], {"characters": 15})
        self.assertEqual(entry["source_url_expires_at"], 1772697707)
        self.assertTrue(Path(entry["path"]).is_file())
        manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["lines"][0]["id"], "hero_greet_01")
        self.assertEqual(result["audio_review"], "pending")

    def test_wav_duration_clamped_to_actual_frames(self):
        # Provider stream-written WAVs may claim a placeholder frame count in the
        # header (observed live: 44739 s for a ~5 s line). Duration must reflect the
        # frames actually present, not the header claim.
        responses = [encoded(audio_url_response()), (200, wav_bytes_lying_header(0.5))]
        code, result = self.invoke("台词", "--voice", "longanlingxin", "--out", str(self.out / "v"),
                                   responses=responses)
        self.assertEqual(code, 0)
        entry = result["lines"][0]
        self.assertAlmostEqual(entry["duration_seconds"], 0.5, places=2)

    def test_qwen_base64_audio_success(self):
        import base64
        responses = [encoded({"output": {"audio": {"data": base64.b64encode(wav_bytes()).decode()}}})]
        code, result = self.invoke("台词", "--voice", "longanlingxin", "--out", str(self.out / "v"),
                                   responses=responses)
        self.assertEqual(code, 0)
        self.assertEqual(result["count"], 1)

    # --- qwen failure paths ----------------------------------------------

    def test_qwen_401_is_api_error_with_platform_hint(self):
        responses = [(401, b'{"code":"InvalidApiKey"}')]
        code, result = self.invoke("台词", "--voice", "longanlingxin", responses=responses)
        self.assertEqual(code, 3)
        self.assertEqual(result["error"], "API_ERROR")
        self.assertEqual(result["http_status"], 401)
        self.assertIn("QWEN_TTS_BASE_URL", result["message"])

    def test_qwen_invalid_audio_bytes(self):
        responses = [encoded(audio_url_response()), (200, b"not audio at all")]
        code, result = self.invoke("台词", "--voice", "longanlingxin", "--out", str(self.out / "v"),
                                   responses=responses)
        self.assertEqual(code, 3)
        self.assertEqual(result["error"], "INVALID_AUDIO")

    def test_qwen_no_audio_in_response(self):
        responses = [encoded({"output": {}})]
        code, result = self.invoke("台词", "--voice", "longanlingxin", responses=responses)
        self.assertEqual(code, 3)
        self.assertEqual(result["error"], "API_ERROR")

    def test_file_exists_protects_take_before_paid_request(self):
        target_dir = self.out / "v"
        target_dir.mkdir()
        original = wav_bytes(0.25)
        (target_dir / "hero_greet_01.wav").write_bytes(original)
        # No responses: the guard must fail BEFORE any paid request is made.
        code, result = self.invoke("台词", "--voice", "longanlufeng", "--name", "hero_greet_01",
                                   "--out", str(target_dir), responses=[])
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "FILE_EXISTS")
        self.assertEqual((target_dir / "hero_greet_01.wav").read_bytes(), original)

    def test_batch_partial_keeps_approved_manifest_entry(self):
        target_dir = self.out / "v"
        target_dir.mkdir()
        (target_dir / "a.wav").write_bytes(wav_bytes())
        approved = {"updated_at": "x", "backend": "qwen", "model": "m", "lines": [
            {"id": "a", "text": "旧台词", "status": "success", "path": str(target_dir / "a.wav"),
             "duration_seconds": 0.5}]}
        (target_dir / "manifest.json").write_text(json.dumps(approved), encoding="utf-8")
        lines = self.write_lines([{"id": "a", "text": "新台词"}, {"id": "b", "text": "第二句"}])
        responses = [encoded(audio_url_response()), (200, wav_bytes())]
        code, result = self.invoke("--lines", lines, "--voice", "longanlufeng", "--out", str(target_dir),
                                   responses=responses)
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["count"], 1)
        manifest = json.loads((target_dir / "manifest.json").read_text(encoding="utf-8"))
        entries = {e["id"]: e for e in manifest["lines"]}
        self.assertEqual(entries["a"]["status"], "success")
        self.assertEqual(entries["a"]["text"], "旧台词")
        self.assertEqual(entries["a"]["last_error"]["error"], "FILE_EXISTS")
        self.assertEqual(entries["b"]["status"], "success")

    # --- piper backend ----------------------------------------------------

    def fake_piper(self, returncode=0, audio=None):
        def run(cmd, input=None, capture_output=None, timeout=None):
            if returncode == 0:
                target = Path(cmd[cmd.index("--output_file") + 1])
                target.write_bytes(audio if audio is not None else wav_bytes())
            return subprocess.CompletedProcess(cmd, returncode, b"", b"piper stderr")
        return run

    def test_piper_success(self):
        model = self.out / "voice.onnx"
        model.write_bytes(b"fake-onnx")
        with patch.object(gen.shutil, "which", return_value="piper"), \
             patch.object(gen.subprocess, "run", side_effect=self.fake_piper()):
            code, result = self.invoke("你好。", "--backend", "piper", "--model", str(model),
                                       "--name", "npc_01", "--out", str(self.out / "p"))
        self.assertEqual(code, 0)
        entry = result["lines"][0]
        self.assertEqual(entry["voice"], "voice")
        self.assertEqual(entry["format"], "wav")
        self.assertTrue(Path(entry["path"]).is_file())

    def test_piper_missing_binary(self):
        with patch.object(gen.shutil, "which", return_value=None):
            code, result = self.invoke("你好。", "--backend", "piper", "--model", "voice.onnx")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "PIPER_NOT_FOUND")

    def test_piper_missing_model_file(self):
        with patch.object(gen.shutil, "which", return_value="piper"):
            code, result = self.invoke("你好。", "--backend", "piper",
                                       "--model", str(self.out / "absent.onnx"))
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "MODEL_NOT_FOUND")

    def test_piper_failure_cleans_partial_file(self):
        model = self.out / "voice.onnx"
        model.write_bytes(b"fake-onnx")
        with patch.object(gen.shutil, "which", return_value="piper"), \
             patch.object(gen.subprocess, "run", side_effect=self.fake_piper(returncode=1)):
            code, result = self.invoke("你好。", "--backend", "piper", "--model", str(model),
                                       "--name", "npc_01", "--out", str(self.out / "p"))
        self.assertEqual(code, 3)
        self.assertEqual(result["error"], "PIPER_FAILED")
        self.assertFalse((self.out / "p" / "npc_01.wav").exists())

    def test_piper_dry_run_needs_no_binary(self):
        code, result = self.invoke("你好。", "--backend", "piper", "--model", "voice.onnx",
                                   "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "dry-run")
        self.assertEqual(result["commands"][0]["stdin"], "你好。")


if __name__ == "__main__":
    unittest.main()
