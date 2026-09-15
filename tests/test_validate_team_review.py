import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_team_review", ROOT / "scripts" / "validate-team-review.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class TeamReviewValidatorTests(unittest.TestCase):
    fixture = ROOT / "tests" / "fixtures" / "team-review" / "complete"

    def _copy_fixture(self, temp):
        root = Path(temp) / "run"
        shutil.copytree(self.fixture, root)
        return root

    def test_complete_fixture_is_valid(self):
        MODULE.validate(self.fixture)

    def test_complete_run_requires_at_least_one_domain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            assignments = json.loads((root / "assignments.json").read_text(encoding="utf-8"))
            assignments["domains"] = []
            (root / "assignments.json").write_text(json.dumps(assignments), encoding="utf-8")
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate(root)

    def test_manifest_must_describe_real_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            scope = json.loads((root / "scope.json").read_text(encoding="utf-8"))
            scope["manifest"][0]["path"] = "src/missing.py"
            scope["manifest_sha256"] = MODULE.canonical_manifest_hash(scope["manifest"])
            (root / "scope.json").write_text(json.dumps(scope), encoding="utf-8")
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate(root)

    def test_manifest_requires_mtime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            scope = json.loads((root / "scope.json").read_text(encoding="utf-8"))
            scope["manifest"][0].pop("mtime")
            scope["manifest_sha256"] = MODULE.canonical_manifest_hash(scope["manifest"])
            (root / "scope.json").write_text(json.dumps(scope), encoding="utf-8")
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate(root)

    def test_malformed_new_finding_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            confirmation = root / "reviews" / "11-backend-confirm.json"
            data = json.loads(confirmation.read_text(encoding="utf-8"))
            data["new_findings"] = [{"id": "backend-N01"}]
            confirmation.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate(root)

    def test_final_review_requires_review_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            final = root / "final-review.md"
            final.write_text(
                "\n".join(line for line in final.read_text(encoding="utf-8").splitlines() if not line.startswith("review-type:")),
                encoding="utf-8",
            )
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate(root)

    def test_complete_degraded_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            scope = json.loads((root / "scope.json").read_text(encoding="utf-8"))
            scope["isolation"] = "degraded"
            (root / "scope.json").write_text(json.dumps(scope), encoding="utf-8")
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate(root)

    def test_missing_required_response_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            confirmation = root / "reviews" / "11-backend-confirm.json"
            data = json.loads(confirmation.read_text(encoding="utf-8"))
            data["responses"] = []
            confirmation.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate(root)

    def test_manifest_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            scope = json.loads((root / "scope.json").read_text(encoding="utf-8"))
            scope["manifest"][0]["size"] = 11
            (root / "scope.json").write_text(json.dumps(scope), encoding="utf-8")
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate(root)

    def test_missing_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            (root / "run.lock").unlink()
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate(root)

    def test_windows_absolute_manifest_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            scope = json.loads((root / "scope.json").read_text(encoding="utf-8"))
            scope["manifest"][0]["path"] = "C:/src/example.py"
            (root / "scope.json").write_text(json.dumps(scope), encoding="utf-8")
            with self.assertRaises(MODULE.ValidationError):
                MODULE.validate(root)

    def test_portable_fixture_is_valid(self):
        MODULE.validate(self.fixture)

    def test_production_mode_rejects_zero_mtime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            scope = json.loads((root / "scope.json").read_text(encoding="utf-8"))
            scope.pop("fixture_mode", None)
            scope["manifest"][0]["mtime"] = 0
            scope["manifest_sha256"] = MODULE.canonical_manifest_hash(scope["manifest"])
            (root / "scope.json").write_text(json.dumps(scope), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "mtime does not match"):
                MODULE.validate(root)

    def test_manifest_root_unlisted_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            (root / "src" / "unlisted.py").write_text("unlisted = True\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "allowlist violation"):
                MODULE.validate(root)

    def test_non_json_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            (root / "run.lock").write_text("locked", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "invalid JSON: run.lock"):
                MODULE.validate(root)

    def test_review_type_and_finding_source_must_match(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            findings = json.loads((root / "findings.json").read_text(encoding="utf-8"))
            findings["findings"][0]["sources"] = ["design"]
            (root / "findings.json").write_text(json.dumps(findings), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "code finding id must use code source"):
                MODULE.validate(root)

    def test_mixed_requires_code_and_design_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            scope = json.loads((root / "scope.json").read_text(encoding="utf-8"))
            scope["review_type"] = "mixed"
            (root / "scope.json").write_text(json.dumps(scope), encoding="utf-8")
            final = root / "final-review.md"
            final.write_text(final.read_text(encoding="utf-8").replace("review-type: code", "review-type: mixed"), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "mixed review must contain independent code and design findings"):
                MODULE.validate(root)

    def test_code_review_requires_phase0(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            scope = json.loads((root / "scope.json").read_text(encoding="utf-8"))
            scope.pop("phase0", None)
            (root / "scope.json").write_text(json.dumps(scope), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "phase0 metadata is required"):
                MODULE.validate(root)

    def test_blocked_run_requires_block_reason(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            (root / "state.json").write_text(json.dumps({"schema": 1, "status": "blocked"}), encoding="utf-8")
            (root / "run-status.md").write_text("status: blocked\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "block-reason.json"):
                MODULE.validate(root)

    def test_conflicting_expert_decisions_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            confirm = json.loads((root / "reviews" / "11-backend-confirm.json").read_text(encoding="utf-8"))
            reject = json.loads(json.dumps(confirm))
            reject["domain"] = "backend-2"
            reject["responses"][0]["decision"] = "REJECT"
            reject["responses"][0]["reason"] = "not a problem"
            assignments = json.loads((root / "assignments.json").read_text(encoding="utf-8"))
            assignments["domains"].append({"domain": "backend-2", "status": "complete", "finding_ids": ["code-F01"]})
            (root / "assignments.json").write_text(json.dumps(assignments), encoding="utf-8")
            (root / "reviews" / "11-backend-2-confirm.json").write_text(json.dumps(reject), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "conflicting expert decisions"):
                MODULE.validate(root)


    def _cli(self, root, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/validate-team-review.py"), str(root), *args], capture_output=True, text=True)

    def test_all_fixture_expectations_and_single_negative_exit_codes(self):
        result = self._cli(self.fixture.parent, "--all")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("PASS expected-invalid"), 3)
        for name in ("manifest-drift", "unauthorized-write", "reject-confirm"):
            with self.subTest(name=name):
                root = self.fixture.parent / name
                case = json.loads((root / "case.json").read_text(encoding="utf-8"))
                result = self._cli(root)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn(case["expected_error"], result.stdout)

    def test_invalid_case_cannot_match_its_own_expectation_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            case = json.loads((root / "case.json").read_text(encoding="utf-8"))
            case.update(expected_valid=False, expected_error="expected-invalid fixture was accepted")
            (root / "case.json").write_text(json.dumps(case), encoding="utf-8")
            result = self._cli(Path(temp), "--all")
            self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_invalid_case_wrong_error_does_not_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            case = json.loads((root / "case.json").read_text(encoding="utf-8"))
            case.update(expected_valid=False, expected_error="sha256 does not match file")
            (root / "case.json").write_text(json.dumps(case), encoding="utf-8")
            scope = json.loads((root / "scope.json").read_text(encoding="utf-8"))
            scope.pop("fixture_mode", None)
            for entry in scope["manifest"]:
                entry["mtime"] = (root / entry["path"]).stat().st_mtime_ns
            scope["manifest_sha256"] = MODULE.canonical_manifest_hash(scope["manifest"])
            (root / "scope.json").write_text(json.dumps(scope), encoding="utf-8")
            scope_hash = scope["manifest_sha256"]
            for review in (root / "reviews").glob("*-confirm.json"):
                data = json.loads(review.read_text(encoding="utf-8"))
                data["target_manifest_sha256"] = scope_hash
                review.write_text(json.dumps(data), encoding="utf-8")
            (root / "run.lock").write_text("locked", encoding="utf-8")
            result = self._cli(Path(temp), "--all")
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("invalid JSON: run.lock", result.stdout)

    def test_all_requires_case_metadata_and_nonempty_suite(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self._cli(Path(temp), "--all")
            self.assertNotEqual(result.returncode, 0)
            root = self._copy_fixture(temp)
            (root / "case.json").unlink()
            result = self._cli(Path(temp), "--all")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("case.json", result.stdout)

    def test_complete_can_have_zero_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            (root / "findings.json").write_text(json.dumps({"schema": 1, "findings": []}), encoding="utf-8")
            assignments = json.loads((root / "assignments.json").read_text(encoding="utf-8"))
            assignments["domains"][0]["finding_ids"] = []
            (root / "assignments.json").write_text(json.dumps(assignments), encoding="utf-8")
            path = root / "reviews/11-backend-confirm.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["responses"] = []
            path.write_text(json.dumps(data), encoding="utf-8")
            final = root / "final-review.md"
            final.write_text(final.read_text(encoding="utf-8").replace("suggestion: 1", "suggestion: 0"), encoding="utf-8")
            MODULE.validate(root)

    def test_domain_new_finding_is_allowed_in_code_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            for name in ("findings.json", "assignments.json", "reviews/11-backend-confirm.json"):
                path = root / name
                path.write_text(path.read_text(encoding="utf-8").replace("code-F01", "backend-N01"), encoding="utf-8")
            MODULE.validate(root)

    def test_merged_mixed_finding_can_have_both_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            scope = json.loads((root / "scope.json").read_text(encoding="utf-8"))
            scope["review_type"] = "mixed"
            (root / "scope.json").write_text(json.dumps(scope), encoding="utf-8")
            path = root / "findings.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["findings"][0].update(sources=["code", "design"], aliases=["design-F01"])
            path.write_text(json.dumps(data), encoding="utf-8")
            final = root / "final-review.md"
            final.write_text(final.read_text(encoding="utf-8").replace("review-type: code", "review-type: mixed"), encoding="utf-8")
            MODULE.validate(root)

    def test_pending_human_accepts_documented_real_conflict(self):
        MODULE.validate(self.fixture.parent / "conflict-resume")

    def test_advisor_role_handoff_preserves_schema_and_finding_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            before = (root / "findings.json").read_bytes()
            (root / "team.md").write_text(
                "# Team\n\nProtocol: review-advisor-v1\n"
                "Code first review: cs-code-reviewer\n"
                "Advice: cs-review-advisor\nExpert recheck: backend\n"
                "Final verdict: host\n",
                encoding="utf-8",
            )
            MODULE.validate(root)
            self.assertEqual((root / "findings.json").read_bytes(), before)

    def test_accepted_advice_cannot_approve_an_unrepaired_blocker(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            path = root / "findings.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["findings"][0].update(
                severity="Important",
                fix="Expert checked the advisor recommendation: wholly applicable; repair not implemented.",
            )
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "APPROVE cannot contain open"):
                MODULE.validate(root)

    def test_rejected_blocking_advice_requires_human_pending_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "run"
            shutil.copytree(self.fixture.parent / "conflict-resume", root)
            conflict = root / "reviews/90-conflicts.json"
            data = json.loads(conflict.read_text(encoding="utf-8"))
            data["conflicts"][0]["reason"] = (
                "Expert rechecked advice and rejected part of it; advisor maintains "
                "that the rejected part is blocking. User choice requested immediately."
            )
            conflict.write_text(json.dumps(data), encoding="utf-8")
            MODULE.validate(root)
            state = root / "state.json"
            data = json.loads(state.read_text(encoding="utf-8"))
            data["status"] = "running"
            state.write_text(json.dumps(data), encoding="utf-8")
            (root / "run-status.md").write_text("status: running\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "unresolved conflicts require pending-human"):
                MODULE.validate(root)

    def test_complete_rejects_unconfirmed_domains(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self._copy_fixture(temp)
            final = root / "final-review.md"
            final.write_text(final.read_text(encoding="utf-8").replace("unconfirmed-domains: []", "unconfirmed-domains: [security]"), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ValidationError, "unconfirmed domains"):
                MODULE.validate(root)

    def test_pending_human_cannot_publish_approve(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "run"
            shutil.copytree(self.fixture.parent / "conflict-resume", root)
            shutil.copyfile(self.fixture / "final-review.md", root / "final-review.md")
            with self.assertRaisesRegex(MODULE.ValidationError, "must not exist before complete"):
                MODULE.validate(root)

    def test_phase0_rejects_oversized_and_noninteger_counts(self):
        for field, value in (("patch_lines", 1001), ("patch_files", 41), ("patch_files", 1.5), ("patch_lines", True)):
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as temp:
                root = self._copy_fixture(temp)
                path = root / "scope.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                data["phase0"][field] = value
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaisesRegex(MODULE.ValidationError, "phase0"):
                    MODULE.validate(root)


if __name__ == "__main__":
    unittest.main()
