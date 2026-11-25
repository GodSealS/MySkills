"""Offline CLI regressions for cs-game-anim-gen; no credentials or provider calls.

Run: python -B -m unittest discover -s tests -p test_game_anim_gen.py -v
Set GAME_ANIM_GEN_SKILL_DIR to run the same contract against an adapter bundle.
"""

import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path(os.environ.get(
    "GAME_ANIM_GEN_SKILL_DIR", ROOT / ".codebuddy/skills/cs-game-anim-gen"))
SPEC = importlib.util.spec_from_file_location("game_anim_gen", BUNDLE / "scripts/gen_anim.py")
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)

try:
    import cv2
except ImportError:  # pragma: no cover - decoder availability is environment specific
    cv2 = None


def mp4_bytes():
    return b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2mp41" + b"\x00" * 64


def write_synthetic_mp4(path, frames=30, size=(96, 96), fps=30):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    for i in range(frames):
        frame = np.full((size[1], size[0], 3), 200, np.uint8)
        x = 8 + (i * 2) % (size[0] - 32)
        frame[24:64, x:x + 24] = (40, 40, 200)
        writer.write(frame)
    writer.release()


class GameAnimGenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="game-anim-gen-test-")
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "out"
        self.char = Path(self.temp.name) / "char.png"
        Image.new("RGB", (300, 300), "#8899aa").save(self.char)
        self.network = patch.object(gen.urllib.request, "urlopen",
                                    side_effect=AssertionError("Unexpected network call"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def invoke(self, *args, responses=None, env=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        environment = {"QWEN_API_KEY": "offline-test-placeholder", "TOKEN_PLAN_API_KEY": "",
                       "ANTHROPIC_AUTH_TOKEN": "", "QWEN_VIDEO_BASE_URL": ""}
        environment.update(env or {})
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, environment))
            stack.enter_context(patch.object(gen.sys, "argv", ["gen_anim.py", *args]))
            stack.enter_context(contextlib.redirect_stdout(stdout))
            stack.enter_context(contextlib.redirect_stderr(stderr))
            if responses is not None:
                stack.enter_context(patch.object(gen, "http_request", side_effect=responses))
            exit_code = 0
            try:
                gen.main()
            except SystemExit as exc:
                exit_code = exc.code
        text = stdout.getvalue()
        result = json.loads(text) if text.strip() else None
        self.assertNotIn("offline-test-placeholder", text + stderr.getvalue())
        return exit_code, result, stderr.getvalue()

    def test_key_resolution_prefers_anthropic_auth_token(self):
        with patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN": "token-a", "QWEN_API_KEY": "token-q",
                                     "TOKEN_PLAN_API_KEY": "token-t"}):
            self.assertEqual(gen.api_key(), "token-a")
        with patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN": "", "QWEN_API_KEY": "token-q",
                                     "TOKEN_PLAN_API_KEY": "token-t"}):
            self.assertEqual(gen.api_key(), "token-q")

    # -- payload contract -------------------------------------------------

    def test_dry_run_payload_uses_async_video_contract(self):
        code, result, _ = self.invoke(str(self.char), "idle breathing", "--dry-run", "--loop")
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "dry-run")
        self.assertTrue(result["endpoint"].endswith(
            "/api/v1/services/aigc/video-generation/video-synthesis"))
        payload = result["payload"]
        self.assertEqual(payload["model"], "wan3.0-video")
        self.assertEqual([m["type"] for m in payload["input"]["media"]],
                         ["first_frame", "last_frame"])
        self.assertEqual(payload["parameters"]["resolution"], "480P")
        self.assertFalse(payload["parameters"]["audio"])
        self.assertFalse(payload["parameters"]["watermark"])
        prompt = payload["input"]["prompt"]
        self.assertIn(gen.LOCK_PREFIX, prompt)
        self.assertIn(gen.LOOP_SUFFIX, prompt)
        self.assertIn(gen.FLAT_BG_HINT, prompt)
        self.assertIn("idle breathing", prompt)

    def test_dry_run_without_loop_omits_last_frame_and_bg_hint(self):
        code, result, _ = self.invoke(str(self.char), "attack slash", "--dry-run",
                                      "--no-bg-hint", "--resolution", "720P", "--duration", "4")
        self.assertEqual(code, 0)
        payload = result["payload"]
        self.assertEqual([m["type"] for m in payload["input"]["media"]], ["first_frame"])
        self.assertNotIn(gen.FLAT_BG_HINT, payload["input"]["prompt"])
        self.assertNotIn(gen.LOOP_SUFFIX, payload["input"]["prompt"])
        self.assertEqual(payload["parameters"]["resolution"], "720P")
        self.assertEqual(payload["parameters"]["duration"], 4)

    def test_transparent_input_is_flattened_before_upload(self):
        rgba = Path(self.temp.name) / "alpha.png"
        base = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
        base.paste(Image.new("RGBA", (120, 120), (200, 60, 60, 255)), (70, 70))
        base.save(rgba)
        data_uri, size = gen.load_character_image(str(rgba), (255, 255, 255))
        self.assertTrue(data_uri.startswith("data:image/png;base64,"))
        decoded = Image.open(io.BytesIO(__import__("base64").b64decode(data_uri.split(",", 1)[1])))
        self.assertEqual(decoded.mode, "RGB")
        self.assertEqual(decoded.getpixel((5, 5)), (255, 255, 255))
        self.assertEqual(decoded.getpixel((130, 130)), (200, 60, 60))
        self.assertEqual(size, (260, 260))

    # -- video stage ------------------------------------------------------

    def test_video_stage_submits_polls_and_downloads(self):
        submit = (200, json.dumps({"output": {"task_id": "t-1", "task_status": "PENDING"}}).encode())
        running = (200, json.dumps({"output": {"task_id": "t-1", "task_status": "RUNNING"}}).encode())
        done = (200, json.dumps({"output": {"task_id": "t-1", "task_status": "SUCCEEDED",
                                            "video_url": "https://example.invalid/v.mp4"},
                                 "usage": {"duration": 3.0, "fps": 30, "SR": 480,
                                           "ratio": "1:1"}}).encode())
        video = (200, mp4_bytes())
        code, result, err = self.invoke(
            str(self.char), "idle", "--stage", "video", "--out", str(self.out),
            "--poll-interval", "1",
            responses=[submit, running, done, video])
        self.assertEqual(code, 0, err)
        stage = result["stages"][0]
        self.assertEqual(stage["stage"], "video")
        self.assertEqual(stage["task_id"], "t-1")
        self.assertEqual(stage["polls"], 2)
        self.assertTrue(Path(stage["video"]["path"]).is_file())
        self.assertEqual(stage["usage"]["fps"], 30)
        self.assertEqual(result["visual_review"], "pending")

    def test_video_stage_reports_failed_task(self):
        submit = (200, json.dumps({"output": {"task_id": "t-2", "task_status": "PENDING"}}).encode())
        failed = (200, json.dumps({"output": {"task_id": "t-2", "task_status": "FAILED",
                                              "code": "InvalidParameter",
                                              "message": "bad combo"}}).encode())
        code, result, err = self.invoke(
            str(self.char), "idle", "--stage", "video", "--out", str(self.out),
            "--poll-interval", "1", responses=[submit, failed])
        self.assertEqual(code, 3)
        self.assertEqual(result["error"], "TASK_FAILED")
        self.assertIn("bad combo", result["message"])

    # -- async submit / resume --------------------------------------------

    def test_submit_only_returns_task_id_without_polling(self):
        submit = (200, json.dumps({"output": {"task_id": "t-async", "task_status": "PENDING"}}).encode())
        code, result, err = self.invoke(
            str(self.char), "idle", "--stage", "video", "--submit-only",
            "--out", str(self.out), responses=[submit])
        self.assertEqual(code, 0, err)
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(result["task_id"], "t-async")
        self.assertIn("--task-id t-async", result["resume"])
        record = json.loads(Path(result["stages"][0]["task_record"]).read_text(encoding="utf-8"))
        self.assertEqual(record["task_id"], "t-async")
        self.assertEqual(record["parameters"]["resolution"], "480P")

    def test_task_id_resumes_without_resubmitting(self):
        running = (200, json.dumps({"output": {"task_id": "t-9", "task_status": "RUNNING"}}).encode())
        done = (200, json.dumps({"output": {"task_id": "t-9", "task_status": "SUCCEEDED",
                                            "video_url": "https://example.invalid/v.mp4"},
                                 "model": "wan3.0-video",
                                 "usage": {"duration": 3.0, "fps": 30}}).encode())
        video = (200, mp4_bytes())
        code, result, err = self.invoke(
            "--stage", "video", "--task-id", "t-9", "--out", str(self.out),
            "--poll-interval", "1", responses=[running, done, video])
        self.assertEqual(code, 0, err)
        stage = result["stages"][0]
        self.assertTrue(stage["resumed"])
        self.assertEqual(stage["task_id"], "t-9")
        self.assertTrue(Path(stage["video"]["path"]).is_file())
        sidecar = json.loads(Path(stage["video"]["source_sidecar"]).read_text(encoding="utf-8"))
        self.assertEqual(sidecar["task_id"], "t-9")
        self.assertEqual(sidecar["video_url"], "https://example.invalid/v.mp4")

    def test_resume_and_submit_argument_conflicts(self):
        for extra in (["--submit-only"], ["--from-video", "x.mp4"], ["--edit-from", "https://e.invalid/a.mp4"]):
            code, result, _ = self.invoke("--stage", "video", "--task-id", "t-1", *extra)
            self.assertEqual(code, 2, extra)
            self.assertEqual(result["error"], "INVALID_ARGUMENTS")

    # -- edit / extend via reference_video ---------------------------------

    def test_edit_payload_uses_reference_video_and_inherits_timing(self):
        code, result, _ = self.invoke(
            "--dry-run", "--edit-from", "https://example.invalid/src.mp4", "把剑改成红色")
        self.assertEqual(code, 0)
        payload = result["payload"]
        self.assertEqual([m["type"] for m in payload["input"]["media"]], ["reference_video"])
        self.assertEqual(payload["input"]["media"][0]["url"], "https://example.invalid/src.mp4")
        self.assertEqual(payload["parameters"]["ratio"], "adaptive")
        self.assertEqual(payload["parameters"]["duration"], -1)
        self.assertIn(gen.EDIT_PREFIX, payload["input"]["prompt"])
        self.assertNotIn(gen.LOCK_PREFIX, payload["input"]["prompt"])

    def test_extend_payload_keeps_duration_and_direction(self):
        code, result, _ = self.invoke(
            "--dry-run", "--extend-from", "https://example.invalid/src.mp4",
            "继续挥剑收招", "--duration", "4", "--extend-direction", "backward")
        self.assertEqual(code, 0)
        payload = result["payload"]
        self.assertEqual(payload["parameters"]["duration"], 4)
        self.assertEqual(payload["parameters"]["ratio"], "adaptive")
        self.assertIn("向后延长", payload["input"]["prompt"])
        self.assertIn(gen.EXTEND_DIRECTIONS["backward"], payload["input"]["prompt"])

    def test_edit_from_local_requires_recorded_source_url(self):
        local = Path(self.temp.name) / "clip.mp4"
        local.write_bytes(mp4_bytes())
        code, result, _ = self.invoke("--dry-run", "--edit-from", str(local), "改色")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "SOURCE_URL_REQUIRED")
        Path(str(local) + ".source.json").write_text(
            json.dumps({"video_url": "https://example.invalid/recorded.mp4"}), encoding="utf-8")
        code, result, _ = self.invoke("--dry-run", "--edit-from", str(local), "改色")
        self.assertEqual(code, 0)
        self.assertEqual(result["payload"]["input"]["media"][0]["url"],
                         "https://example.invalid/recorded.mp4")

    def test_edit_rejects_loop_and_character_image(self):
        code, result, _ = self.invoke("--dry-run", "--edit-from", "https://e.invalid/a.mp4",
                                      "改色", "--loop")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_ARGUMENTS")
        code, result, _ = self.invoke(str(self.char), "改色", "--dry-run",
                                      "--edit-from", "https://e.invalid/a.mp4")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_ARGUMENTS")

    @unittest.skipUnless(cv2 is not None, "needs a video encoder for the fixture")
    def test_extend_rejects_input_plus_output_over_30s(self):
        video = Path(self.temp.name) / "long.mp4"
        write_synthetic_mp4(video, frames=60)  # 2 s at 30 fps
        Path(str(video) + ".source.json").write_text(
            json.dumps({"video_url": "https://example.invalid/long.mp4"}), encoding="utf-8")
        code, result, _ = self.invoke("--stage", "video", "--extend-from", str(video),
                                      "继续", "--duration", "29", "--out", str(self.out))
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "SOURCE_DURATION")

    # -- prompt discipline and naming --------------------------------------

    def test_generate_prompt_declares_first_frame_role(self):
        code, result, _ = self.invoke(str(self.char), "idle", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn(gen.FIRST_FRAME_ROLE, result["payload"]["input"]["prompt"])

    def test_descriptive_name_reaches_files_and_manifest(self):
        submit = (200, json.dumps({"output": {"task_id": "t-n", "task_status": "PENDING"}}).encode())
        done = (200, json.dumps({"output": {"task_id": "t-n", "task_status": "SUCCEEDED",
                                            "video_url": "https://example.invalid/v.mp4"}}).encode())
        code, result, err = self.invoke(
            str(self.char), "idle", "--stage", "video", "--name", "hero-idle",
            "--out", str(self.out), "--poll-interval", "1",
            responses=[submit, done, (200, mp4_bytes())])
        self.assertEqual(code, 0, err)
        self.assertIn("hero-idle", Path(result["stages"][0]["video"]["path"]).name)

    @unittest.skipUnless(cv2 is not None, "needs a video encoder for the fixture")
    def test_manifest_records_name_and_mode(self):
        video = Path(self.temp.name) / "named.mp4"
        write_synthetic_mp4(video, frames=9)
        code, result, err = self.invoke(
            "--stage", "all", "--from-video", str(video), "--alpha", "none",
            "--fps", "10", "--name", "hero-walk", "--out", str(self.out))
        self.assertEqual(code, 0, err + json.dumps(result))
        manifest = json.loads(Path(result["stages"][1]["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "hero-walk")
        self.assertEqual(manifest["mode"], "generate")

    # -- argument guards --------------------------------------------------

    def test_frames_stage_requires_from_video(self):
        code, result, _ = self.invoke("--stage", "frames", "--out", str(self.out))
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_ARGUMENTS")

    def test_video_stage_rejects_from_video(self):
        code, result, _ = self.invoke(str(self.char), "idle", "--stage", "video",
                                      "--from-video", "x.mp4")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_ARGUMENTS")

    def test_duration_and_model_guards(self):
        code, result, _ = self.invoke(str(self.char), "idle", "--dry-run", "--duration", "31")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_DURATION")
        code, result, _ = self.invoke(str(self.char), "idle", "--dry-run", "--model", "wan9")
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "INVALID_MODEL")

    def test_missing_api_key_blocks_paid_run(self):
        code, result, _ = self.invoke(str(self.char), "idle", "--stage", "video",
                                      "--out", str(self.out), env={"QWEN_API_KEY": ""})
        self.assertEqual(code, 2)
        self.assertEqual(result["error"], "MISSING_API_KEY")

    # -- sampling math ----------------------------------------------------

    def test_sample_indices_prefers_closest_rate_and_drops_loop_duplicate(self):
        idx, step = gen.sample_indices(30, 30.0, 12, loop=False)
        self.assertEqual(step, 3)
        self.assertEqual(len(idx), 10)
        idx_loop, step_loop = gen.sample_indices(30, 30.0, 12, loop=True)
        self.assertEqual(idx_loop, list(range(0, 29, 3)))
        self.assertNotIn(29, idx_loop)
        idx_exact, step_exact = gen.sample_indices(60, 30.0, 10, loop=False)
        self.assertEqual(step_exact, 3)
        self.assertEqual(len(idx_exact), 20)

    # -- local post-processing --------------------------------------------

    @unittest.skipUnless(cv2 is not None, "needs a video encoder for the fixture")
    def test_frames_and_sheet_stages_round_trip(self):
        video = Path(self.temp.name) / "src.mp4"
        write_synthetic_mp4(video)
        code, result, err = self.invoke(
            "--stage", "all", "--from-video", str(video), "--alpha", "none",
            "--fps", "10", "--out", str(self.out))
        self.assertEqual(code, 0, err + json.dumps(result))
        stages = {s["stage"]: s for s in result["stages"]}
        frames, sheet = stages["frames"], stages["sheet"]
        self.assertEqual(frames["effective_fps"], 10.0)
        self.assertEqual(frames["frame_count"], 10)
        self.assertGreater(frames["metrics"]["coverage_min"], 0)
        manifest = json.loads(Path(sheet["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["fps"], 10.0)
        self.assertEqual(manifest["frame_count"], 10)
        self.assertTrue(Path(sheet["gif"]).is_file())
        self.assertTrue(Path(frames["contact_sheet"]).is_file())

        sheet_img = np.asarray(Image.open(sheet["sheet"]).convert("RGBA"))
        frame0 = np.asarray(Image.open(self.out / "frames" / "frame-000.png").convert("RGBA"))
        cw, ch = manifest["cell"]["width"], manifest["cell"]["height"]
        self.assertTrue(np.array_equal(sheet_img[0:ch, 0:cw], frame0))
        cols = manifest["grid"]["cols"]
        frame1 = np.asarray(Image.open(self.out / "frames" / "frame-001.png").convert("RGBA"))
        self.assertTrue(np.array_equal(sheet_img[0:ch, cw * (1 % cols):cw * (1 % cols + 1)], frame1))

    # -- border-connected color key ----------------------------------------

    def test_matte_cut_removes_only_border_connected_background(self):
        frame = np.full((40, 40, 3), 255, np.uint8)
        frame[10:30, 12:28] = (30, 60, 200)
        frame[18:22, 18:22] = (255, 255, 255)  # enclosed white must survive
        rgba, bbox = gen.matte_cut(frame, np, (255, 255, 255), 30)
        self.assertEqual(bbox, (12, 10, 28, 30))
        self.assertEqual(rgba[0, 0, 3], 0)      # border background removed
        self.assertEqual(rgba[15, 15, 3], 255)  # subject kept
        self.assertEqual(rgba[20, 20, 3], 255)  # enclosed same-color region kept

    def test_matte_cut_fails_without_matching_border(self):
        frame = np.full((16, 16, 3), 10, np.uint8)
        with self.assertRaises(gen.GenerationError) as ctx:
            gen.matte_cut(frame, np, (255, 255, 255), 30)
        self.assertEqual(ctx.exception.code, "MATTE_NO_BORDER")

    def test_dry_run_names_the_matte_key_color(self):
        code, result, _ = self.invoke(str(self.char), "idle", "--dry-run",
                                      "--alpha", "matte", "--matte-color", "00b140")
        self.assertEqual(code, 0)
        self.assertIn("纯绿色", result["payload"]["input"]["prompt"])

    @unittest.skipUnless(cv2 is not None, "needs a video encoder for the fixture")
    def test_frames_stage_matte_alpha_cuts_background(self):
        video = Path(self.temp.name) / "src-matte.mp4"
        write_synthetic_mp4(video, frames=9)
        code, result, err = self.invoke(
            "--stage", "frames", "--from-video", str(video), "--alpha", "matte",
            "--matte-color", "c8c8c8", "--matte-tolerance", "40",
            "--fps", "10", "--out", str(self.out))
        self.assertEqual(code, 0, err + json.dumps(result))
        stage = result["stages"][0]
        self.assertGreater(stage["metrics"]["coverage_min"], 0)
        self.assertLess(stage["metrics"]["coverage_mean"], 1.0)
        frame0 = np.asarray(Image.open(self.out / "frames" / "frame-000.png"))
        self.assertEqual(frame0[0, 0, 3], 0)   # corner background is transparent
        self.assertEqual(frame0[:, :, 3].max(), 255)

    # -- pixel-art post-processing -----------------------------------------

    @unittest.skipUnless(cv2 is not None, "needs a video encoder for the fixture")
    def test_scale_and_shared_palette_apply_to_whole_sequence(self):
        video = Path(self.temp.name) / "src-pixel.mp4"
        write_synthetic_mp4(video, frames=9)
        base_out = Path(self.temp.name) / "base"
        code, base, err = self.invoke(
            "--stage", "frames", "--from-video", str(video), "--alpha", "matte",
            "--matte-color", "c8c8c8", "--matte-tolerance", "40", "--fps", "10",
            "--out", str(base_out))
        self.assertEqual(code, 0, err + json.dumps(base))
        code, result, err = self.invoke(
            "--stage", "all", "--from-video", str(video), "--alpha", "matte",
            "--matte-color", "c8c8c8", "--matte-tolerance", "40", "--fps", "10",
            "--scale", "0.5", "--colors", "8", "--out", str(self.out))
        self.assertEqual(code, 0, err + json.dumps(result))
        stage = result["stages"][0]
        unscaled = base["stages"][0]["cell"]
        self.assertEqual(stage["cell"], {"width": max(1, round(unscaled["width"] * 0.5)),
                                         "height": max(1, round(unscaled["height"] * 0.5))})
        self.assertEqual(stage["pixel_art"], {"scale": 0.5, "colors": 8, "shared_palette": True})
        manifest = json.loads(Path(result["stages"][1]["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["cell"], stage["cell"])
        palette = set()
        for name in sorted(os.listdir(self.out / "frames")):
            if not name.startswith("frame-"):
                continue
            arr = np.asarray(Image.open(self.out / "frames" / name).convert("RGBA"))
            colors = {tuple(px) for px in arr[arr[:, :, 3] > 0][:, :3]}
            self.assertLessEqual(len(colors), 8, name)
            palette |= colors
        self.assertLessEqual(len(palette), 8)  # one shared palette, no per-frame flicker

    def test_pixel_art_argument_guards(self):
        for extra in (["--scale", "16"], ["--colors", "1"], ["--matte-tolerance", "200"]):
            code, result, _ = self.invoke(str(self.char), "idle", "--dry-run", *extra)
            self.assertEqual(code, 2, extra)
            self.assertEqual(result["error"], "INVALID_ARGUMENTS")

    @unittest.skipUnless(cv2 is not None, "needs a video encoder for the fixture")
    def test_sheet_stage_reuses_effective_fps_from_meta(self):
        video = Path(self.temp.name) / "src2.mp4"
        write_synthetic_mp4(video, frames=60)
        code, _, err = self.invoke("--stage", "frames", "--from-video", str(video),
                                   "--alpha", "none", "--fps", "12", "--out", str(self.out))
        self.assertEqual(code, 0, err)
        code, result, err = self.invoke("--stage", "sheet", "--from-video", str(video),
                                        "--alpha", "none", "--fps", "12", "--out", str(self.out))
        self.assertEqual(code, 0, err)
        manifest = json.loads(Path(result["stages"][0]["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["fps"], 10.0)
        self.assertEqual(manifest["requested_fps"], 12)


if __name__ == "__main__":
    unittest.main()
