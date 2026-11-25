"""Offline CLI regressions; no server or GPU calls are used.

Run: python -B -m unittest discover -s tests -p test_game_audio_gen.py -v
Set GAME_AUDIO_GEN_SKILL_DIR to run the same contract against an adapter bundle.
"""

import array
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import wave


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path(os.environ.get(
    "GAME_AUDIO_GEN_SKILL_DIR", ROOT / ".codebuddy/skills/cs-game-audio-gen"))
SPEC = importlib.util.spec_from_file_location("game_audio_gen", BUNDLE / "scripts/gen_audio.py")
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def wav_bytes(seconds=0.5, rate=22050):
    stream = io.BytesIO()
    with wave.open(stream, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x40" * int(rate * seconds))
    return stream.getvalue()


def float_wav_bytes(seconds=0.5, rate=22050, channels=1, value=0.5):
    """ACE-Step style IEEE-float WAV (fmt tag 3) that stdlib wave cannot read."""
    frames = int(rate * seconds)
    samples = array.array("f", [value] * frames * channels)
    payload = samples.tobytes()
    fmt = struct.pack("<HHIIHH", 3, channels, rate, rate * channels * 4, channels * 4, 32)
    body = (b"fmt " + struct.pack("<I", len(fmt)) + fmt
            + b"data" + struct.pack("<I", len(payload)) + payload)
    return b"RIFF" + struct.pack("<I", len(body) + 4) + b"WAVE" + body


def ok(data):
    return 200, json.dumps({"data": data, "code": 200, "error": None}).encode("utf-8")


def health_response(initialized=True):
    return ok({"status": "ok", "service": "ACE-Step API", "models_initialized": initialized})


def release_response(task_id="t1"):
    return ok({"task_id": task_id, "status": "queued"})


def query_response(task_id="t1", status=1, file_url="/v1/audio?path=%2Ftmp%2Fx.wav"):
    result = json.dumps([{"file": file_url, "status": status,
                          "metas": {"bpm": 90, "duration": 30.0, "keyscale": "C Major"},
                          "seed_value": "42", "dit_model": "acestep-v15-turbo",
                          "lm_model": "acestep-5Hz-lm-0.6B"}])
    return ok([{"task_id": task_id, "status": status, "result": result}])


class GameAudioGenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="game-audio-gen-test-")
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        # Fail closed: every test blocks the real transport even if a mock is missed.
        self.network = patch.object(gen.urllib.request, "urlopen",
                                    side_effect=AssertionError("Unexpected network call"))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.sleep = patch.object(gen.time, "sleep")
        self.sleep.start()
        self.addCleanup(self.sleep.stop)

    def invoke(self, *args, responses=None, env=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        environment = {"ACESTEP_API_KEY": "", "ACESTEP_API_URL": "", "ACESTEP_HOME": ""}
        environment.update(env or {})
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, environment))
            stack.enter_context(patch.object(gen.sys, "argv", ["gen_audio.py", *args]))
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
        self.assertNotIn("Traceback", stderr.getvalue())
        return exit_code, result

    def write_tracks(self, tracks, name="tracks.json"):
        path = self.out / name
        path.write_text(json.dumps(tracks, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def success_responses(self, audio=None, running_first=False):
        seq = [health_response(), release_response()]
        if running_first:
            seq.append(query_response(status=0))
        seq.append(query_response())
        seq.append((200, audio if audio is not None else wav_bytes()))
        return seq

    # --- dry run and argument validation ---------------------------------

    def test_dry_run_music_needs_no_server(self):
        code, result = self.invoke("calm menu theme", "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "dry-run")
        fields = result["tasks"][0]["fields"]
        self.assertEqual(fields["lyrics"], "[Instrumental]")
        self.assertEqual(fields["task_type"], "text2music")
        self.assertEqual(fields["audio_duration"], 30.0)
        self.assertEqual(fields["audio_format"], "mp3")
        self.assertEqual(fields["batch_size"], 1)
        self.assertIsNone(result["tasks"][0]["reference_audio_upload"])

    def test_dry_run_sfx_defaults_wav_and_ten_seconds(self):
        code, result = self.invoke("sword clash hit, no music", "--kind", "sfx", "--dry-run")
        self.assertEqual(code, 0)
        fields = result["tasks"][0]["fields"]
        self.assertEqual(fields["audio_format"], "wav")
        self.assertEqual(fields["audio_duration"], 10.0)
        self.assertEqual(fields["lyrics"], "[Instrumental]")

    def test_dry_run_reference_audio_sets_cover_strength(self):
        ref = self.out / "ref.wav"
        ref.write_bytes(wav_bytes())
        code, result = self.invoke("battle variation", "--reference-audio", str(ref),
                                   "--cover-strength", "0.4", "--dry-run")
        self.assertEqual(code, 0)
        task = result["tasks"][0]
        self.assertEqual(task["fields"]["audio_cover_strength"], 0.4)
        self.assertEqual(task["reference_audio_upload"], str(ref.resolve()))

    def test_dry_run_batch_tracks(self):
        path = self.write_tracks([
            {"id": "a", "prompt": "menu theme", "bpm": 90},
            {"id": "b", "prompt": "hit", "kind": "sfx", "trim_start": 0, "trim_end": 2},
        ])
        code, result = self.invoke("--tracks", path, "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual([t["id"] for t in result["tasks"]], ["a", "b"])
        self.assertEqual(result["tasks"][1]["kind"], "sfx")

    def test_empty_prompt_rejected(self):
        code, result = self.invoke("   ", "--dry-run")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "EMPTY_PROMPT")

    def test_duration_out_of_range_rejected(self):
        for value in ("5", "601"):
            code, result = self.invoke("x", "--duration", value, "--dry-run")
            self.assertEqual(code, 2)
            self.assertEqual(result["error"], "INVALID_PARAMETERS")

    def test_bpm_out_of_range_rejected(self):
        code, result = self.invoke("x", "--bpm", "400", "--dry-run")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_PARAMETERS")

    def test_trim_requires_wav_and_pair(self):
        code, result = self.invoke("x", "--trim-start", "0", "--trim-end", "2", "--dry-run")
        self.assertEqual(code, 2)  # music defaults to mp3
        self.assertEqual(result["error"], "INVALID_PARAMETERS")
        code, result = self.invoke("x", "--kind", "sfx", "--trim-start", "0", "--dry-run")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_PARAMETERS")

    def test_cover_strength_requires_reference(self):
        code, result = self.invoke("x", "--cover-strength", "0.5", "--dry-run")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_PARAMETERS")

    def test_missing_reference_file_rejected(self):
        code, result = self.invoke("x", "--reference-audio", str(self.out / "nope.wav"),
                                   "--dry-run")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "REFERENCE_NOT_FOUND")

    def test_sfx_rejects_vocal_lyrics(self):
        code, result = self.invoke("x", "--kind", "sfx", "--lyrics", "hello world",
                                   "--dry-run")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_PARAMETERS")

    def test_duplicate_track_ids_rejected(self):
        path = self.write_tracks([{"id": "a", "prompt": "x"}, {"id": "a", "prompt": "y"}])
        code, result = self.invoke("--tracks", path, "--dry-run")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_TRACKS")

    def test_prompt_and_tracks_conflict(self):
        path = self.write_tracks([{"id": "a", "prompt": "x"}])
        code, result = self.invoke("x", "--tracks", path, "--dry-run")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_ARGUMENTS")

    # --- audio probing / normalization / trimming -------------------------

    def test_probe_pcm_wav(self):
        probe = gen.probe_audio(wav_bytes(0.5, 22050))
        self.assertEqual(probe["format"], "wav")
        self.assertAlmostEqual(probe["duration_seconds"], 0.5, places=2)
        self.assertEqual(probe["sample_rate"], 22050)

    def test_probe_float_wav_normalizes_to_pcm(self):
        probe = gen.probe_audio(float_wav_bytes(0.5, 48000, channels=2))
        self.assertEqual(probe["format"], "wav")
        self.assertAlmostEqual(probe["duration_seconds"], 0.5, places=2)
        self.assertEqual(probe["sample_rate"], 48000)
        self.assertEqual(probe["channels"], 2)
        normalized = gen.normalize_wav(float_wav_bytes(0.25, 22050, value=0.5))
        with wave.open(io.BytesIO(normalized)) as w:
            self.assertEqual(w.getsampwidth(), 2)
            frame = w.readframes(1)
        self.assertAlmostEqual(struct.unpack("<h", frame)[0] / 32767.0, 0.5, places=3)

    def test_normalize_passes_pcm_and_mp3_through(self):
        pcm = wav_bytes()
        self.assertEqual(gen.normalize_wav(pcm), pcm)
        mp3 = b"ID3" + b"\x00" * 32
        self.assertEqual(gen.normalize_wav(mp3), mp3)

    def test_probe_mp3_sniff(self):
        probe = gen.probe_audio(b"ID3" + b"\x00" * 32)
        self.assertEqual(probe["format"], "mp3")
        self.assertIsNone(probe["duration_seconds"])

    def test_probe_rejects_garbage(self):
        with self.assertRaises(gen.GenerationError) as ctx:
            gen.probe_audio(b"not audio at all")
        self.assertEqual(ctx.exception.code, "INVALID_AUDIO")

    def test_trim_wav_cut_and_bounds(self):
        trimmed = gen.trim_wav(wav_bytes(2.0, 22050), 0.5, 1.5)
        probe = gen.probe_audio(trimmed)
        self.assertAlmostEqual(probe["duration_seconds"], 1.0, places=2)
        with self.assertRaises(gen.GenerationError) as ctx:
            gen.trim_wav(wav_bytes(1.0), 0.0, 5.0)
        self.assertEqual(ctx.exception.code, "INVALID_TRIM")

    def test_trim_float_wav(self):
        trimmed = gen.trim_wav(float_wav_bytes(2.0, 48000, channels=2), 0.0, 1.0)
        probe = gen.probe_audio(trimmed)
        self.assertAlmostEqual(probe["duration_seconds"], 1.0, places=2)
        self.assertEqual(probe["channels"], 2)

    # --- mocked end-to-end flow -------------------------------------------

    def test_success_saves_take_and_manifest(self):
        code, result = self.invoke("calm menu theme", "--name", "menu_01",
                                   "--out", str(self.out), responses=self.success_responses())
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["audio_review"], "pending")
        entry = result["tracks"][0]
        self.assertEqual(entry["id"], "menu_01")
        self.assertEqual(entry["dit_model"], "acestep-v15-turbo")
        self.assertEqual(entry["seed_value"], "42")
        saved = Path(entry["path"])
        self.assertTrue(saved.is_file())
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["backend"], "ace-step")
        self.assertEqual(manifest["tracks"][0]["id"], "menu_01")

    def test_polls_through_running_state(self):
        code, result = self.invoke("x", "--name", "t", "--out", str(self.out),
                                   responses=self.success_responses(running_first=True))
        self.assertEqual(code, 0)
        self.assertEqual(result["count"], 1)

    def test_float_wav_deliverable_is_pcm(self):
        code, result = self.invoke("hit", "--kind", "sfx", "--name", "sfx_01",
                                   "--out", str(self.out),
                                   responses=self.success_responses(audio=float_wav_bytes(1.0, 48000, 2)))
        self.assertEqual(code, 0)
        with wave.open(result["tracks"][0]["path"]) as w:
            self.assertEqual(w.getsampwidth(), 2)
            self.assertEqual(w.getnchannels(), 2)

    def test_reference_audio_uploads_multipart(self):
        ref = self.out / "ref.wav"
        ref.write_bytes(wav_bytes())
        calls = []

        def recorder(url, data=None, headers=None, timeout=None):
            calls.append((url, data, headers))
            return self.success_responses()[len(calls) - 1]

        with patch.object(gen, "http_request", side_effect=recorder):
            code, result = self.invoke("battle variation", "--name", "b2",
                                       "--reference-audio", str(ref), "--out", str(self.out))
        self.assertEqual(code, 0)
        release = next(c for c in calls if c[0].endswith("/release_task"))
        self.assertTrue(release[2]["Content-Type"].startswith("multipart/form-data"))
        self.assertIn(b'name="reference_audio"', release[1])
        self.assertIn(b"audio_cover_strength", release[1])
        self.assertEqual(result["tracks"][0]["cover_strength"], 0.2)

    def test_file_exists_protects_approved_take(self):
        (self.out / "menu_01.mp3").write_bytes(b"ID3" + b"\x00" * 32)
        code, result = self.invoke("x", "--name", "menu_01", "--out", str(self.out),
                                   responses=self.success_responses())
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "FILE_EXISTS")

    def test_server_down_is_exit_three_with_instructions(self):
        def refuse(url, data=None, headers=None, timeout=None):
            raise gen.GenerationError("NETWORK_ERROR", "connection refused")

        with patch.object(gen, "http_request", side_effect=refuse):
            code, result = self.invoke("x", "--out", str(self.out))
        self.assertEqual(code, 3)
        self.assertEqual(result["error"], "SERVER_DOWN")
        self.assertIn("acestep.api_server", result["message"])

    def test_generation_failure_is_exit_three(self):
        responses = [health_response(), release_response(), query_response(status=2)]
        code, result = self.invoke("x", "--out", str(self.out), responses=responses)
        self.assertEqual(code, 3)
        self.assertEqual(result["error"], "GENERATION_FAILED")

    def test_batch_partial_continues_and_preserves_manifest(self):
        (self.out / "a.mp3").write_bytes(b"ID3" + b"\x00" * 32)  # a already exists
        path = self.write_tracks([{"id": "a", "prompt": "x"}, {"id": "b", "prompt": "y"}])
        responses = [health_response(), release_response("t2"), query_response("t2"),
                     (200, wav_bytes())]
        code, result = self.invoke("--tracks", path, "--out", str(self.out),
                                   responses=responses)
        # FILE_EXISTS is a local-error class (exit 2), matching the family contract.
        self.assertEqual(code, 2)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["failed"], 1)
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        ids = {t["id"]: t for t in manifest["tracks"]}
        self.assertEqual(ids["b"]["status"], "success")
        self.assertEqual(ids["a"]["status"], "error")

    def test_failed_retry_keeps_approved_manifest_entry(self):
        first = self.success_responses()
        code, _ = self.invoke("x", "--name", "keep", "--out", str(self.out), responses=first)
        self.assertEqual(code, 0)
        # Batch retry: "keep" now hits FILE_EXISTS (its take is on disk) and "keep2"
        # fails at submission. The approved "keep" entry must survive with last_error,
        # and the failed "keep2" must be recorded rather than silently dropped.
        path = self.write_tracks([{"id": "keep", "prompt": "x"}, {"id": "keep2", "prompt": "y"}])
        responses = [health_response(),
                     (400, json.dumps({"detail": "bad params"}).encode("utf-8"))]
        code, result = self.invoke("--tracks", path, "--out", str(self.out),
                                   responses=responses)
        self.assertEqual(code, 3)
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        ids = {t["id"]: t for t in manifest["tracks"]}
        self.assertEqual(ids["keep"]["status"], "success")
        self.assertEqual(ids["keep"]["last_error"]["error"], "FILE_EXISTS")
        self.assertEqual(ids["keep2"]["status"], "error")

    def test_api_key_redacted_and_sent_as_bearer(self):
        calls = []

        def recorder(url, data=None, headers=None, timeout=None):
            calls.append(headers or {})
            return self.success_responses()[len(calls) - 1]

        with patch.object(gen, "http_request", side_effect=recorder):
            code, result = self.invoke("x", "--name", "k", "--out", str(self.out),
                                       env={"ACESTEP_API_KEY": "secret-test-key-123"})
        self.assertEqual(code, 0)
        self.assertTrue(all(h.get("Authorization") == "Bearer secret-test-key-123"
                            for h in calls if h))
        self.assertNotIn("secret-test-key-123", json.dumps(result))

    def test_lyrics_file_and_vocal_entry(self):
        lyrics = self.out / "theme.txt"
        lyrics.write_text("[Verse]\nhello\n[Chorus]\nworld", encoding="utf-8")
        code, result = self.invoke("uplifting opening theme", "--lyrics-file", str(lyrics),
                                   "--language", "zh", "--name", "vocal",
                                   "--out", str(self.out), responses=self.success_responses())
        self.assertEqual(code, 0)
        self.assertIn("[Chorus]", result["tracks"][0]["lyrics"])


class GameAudioGenPreflightTests(unittest.TestCase):
    """Startup model check/auto-download; subprocess and transport are mocked."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="game-audio-preflight-test-")
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.home = self.out / "ACE-Step"
        self.network = patch.object(gen.urllib.request, "urlopen",
                                    side_effect=AssertionError("Unexpected network call"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def make_home(self, with_venv=True):
        self.home.mkdir(parents=True, exist_ok=True)
        if with_venv:
            for rel in (".venv/Scripts/python.exe", ".venv/bin/python"):
                py = self.home / rel
                py.parent.mkdir(parents=True, exist_ok=True)
                py.write_bytes(b"")
        return self.home

    def check_result(self, main_ready=True, lm_ready=True):
        payload = json.dumps({"checkpoints_dir": str(self.home / "checkpoints"),
                              "main_ready": main_ready, "lm_default_ready": lm_ready})
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=payload + "\n", stderr="")

    def fake_popen(self, returncode=0):
        proc = unittest.mock.MagicMock()
        proc.stdout = iter(["downloading...\n", "done\n"])
        proc.wait.return_value = returncode
        proc.__enter__.return_value = proc
        proc.__exit__.return_value = False
        return proc

    def invoke(self, *args, run=None, popen=None, http=None, env=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        environment = {"ACESTEP_API_KEY": "", "ACESTEP_API_URL": "", "ACESTEP_HOME": ""}
        environment.update(env or {})
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, environment))
            stack.enter_context(patch.object(gen.sys, "argv", ["gen_audio.py", *args]))
            stack.enter_context(contextlib.redirect_stdout(stdout))
            stack.enter_context(contextlib.redirect_stderr(stderr))
            if run is not None:
                stack.enter_context(patch.object(gen.subprocess, "run", side_effect=run))
            if popen is not None:
                stack.enter_context(patch.object(gen.subprocess, "Popen", side_effect=popen))
            if http is not None:
                stack.enter_context(patch.object(gen, "http_request", side_effect=http))
            exit_code = 0
            try:
                gen.main()
            except SystemExit as exc:
                exit_code = exc.code
        result = json.loads(stdout.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        return exit_code, result

    def test_preflight_only_requires_home(self):
        code, result = self.invoke("--preflight-only")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "MISSING_ACESTEP_HOME")

    def test_preflight_missing_install(self):
        code, result = self.invoke("--preflight-only", "--acestep-home", str(self.home))
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "ACESTEP_NOT_INSTALLED")

    def test_preflight_missing_venv(self):
        self.make_home(with_venv=False)
        code, result = self.invoke("--preflight-only", "--acestep-home", str(self.home))
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "ACESTEP_NOT_INSTALLED")

    def test_preflight_weights_ready_no_download(self):
        self.make_home()
        with patch.object(gen.subprocess, "Popen",
                          side_effect=AssertionError("Unexpected download")) as popen:
            code, result = self.invoke("--preflight-only", "--acestep-home", str(self.home),
                                       run=[self.check_result()], http=[health_response()])
        self.assertEqual(code, 0)
        self.assertEqual(result["preflight"]["downloaded"], [])
        self.assertTrue(result["preflight"]["main_ready"])
        self.assertTrue(result["server"]["up"])
        popen.assert_not_called()

    def test_preflight_downloads_missing_main_and_lm(self):
        self.make_home()
        runs = [self.check_result(main_ready=False, lm_ready=False), self.check_result()]
        popen = self.fake_popen()
        code, result = self.invoke("--preflight-only", "--acestep-home", str(self.home),
                                   run=runs, popen=[popen, popen], http=[health_response()])
        self.assertEqual(code, 0)
        self.assertEqual(result["preflight"]["downloaded"], ["main", gen.DEFAULT_LM_MODEL])
        self.assertTrue(result["preflight"]["main_ready"])

    def test_preflight_download_failure_is_exit_three(self):
        self.make_home()
        runs = [self.check_result(main_ready=False)]
        code, result = self.invoke("--preflight-only", "--acestep-home", str(self.home),
                                   run=runs, popen=[self.fake_popen(returncode=1)])
        self.assertEqual(code, 3)
        self.assertEqual(result["error"], "MODEL_DOWNLOAD_FAILED")

    def test_preflight_reports_server_down_without_failing(self):
        self.make_home()

        def refuse(url, data=None, headers=None, timeout=None):
            raise gen.GenerationError("NETWORK_ERROR", "connection refused")

        code, result = self.invoke("--preflight-only", "--acestep-home", str(self.home),
                                   run=[self.check_result()], http=refuse)
        self.assertEqual(code, 0)
        self.assertFalse(result["server"]["up"])
        self.assertIn("acestep.api_server", result["server"]["hint"])

    def test_generation_runs_preflight_when_home_set(self):
        self.make_home()
        code, result = self.invoke("calm menu theme", "--name", "m", "--out", str(self.out),
                                   run=[self.check_result()],
                                   http=[health_response(), release_response(),
                                         query_response(), (200, wav_bytes())],
                                   env={"ACESTEP_HOME": str(self.home)})
        self.assertEqual(code, 0)
        self.assertIn("preflight", result)
        self.assertTrue(result["preflight"]["main_ready"])

    def test_generation_without_home_skips_preflight(self):
        with patch.object(gen.subprocess, "run",
                          side_effect=AssertionError("Unexpected model check")) as run:
            code, result = self.invoke("x", "--name", "t", "--out", str(self.out),
                                       http=[health_response(), release_response(),
                                             query_response(), (200, wav_bytes())])
        self.assertEqual(code, 0)
        self.assertNotIn("preflight", result)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()