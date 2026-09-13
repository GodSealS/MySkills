#!/usr/bin/env python3
"""Validate cs-team-review run artifacts without executing any agents."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SEVERITIES = {"Critical", "Important", "Suggestion"}
LIFECYCLES = {"open", "resolved", "dismissed", "blocked"}
DECISIONS = {"CONFIRM", "REJECT", "REFINE", "NEW", "ABSENT"}
RUN_STATUSES = {"running", "blocked", "pending-human", "complete"}
DOMAIN_STATUSES = {"complete", "unconfirmed", "failed"}
VERDICTS = {"APPROVE", "REQUEST CHANGES", "REJECT"}
REVIEW_TYPES = {"code", "design", "mixed"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ID = re.compile(r"^[a-z][a-z0-9-]*-(?:F|N)[0-9]{2,}$")
SENSITIVE = re.compile(r"(^|/)(\.env(?:\.|$)|.*(?:secret|token|password|private[-_]?key).*)", re.I)
MAX_MANIFEST_FILES = 2000
MAX_MANIFEST_BYTES = 50 * 1024 * 1024
RUN_ARTIFACTS = {
    "scope.json", "scope.md", "team.md", "run-status.md", "state.json",
    "assignments.json", "findings.json", "case.json", "run.lock",
    "final-review.md", "final-review.draft.md", "human-decision.md",
    "block-reason.json",
}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON artifact: {path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid JSON: {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"JSON root must be an object: {path.name}")
    return value


def require(obj: dict[str, Any], key: str, path: str) -> Any:
    if key not in obj:
        raise ValidationError(f"{path}: missing {key}")
    return obj[key]


def canonical_manifest_hash(manifest: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        sorted(manifest, key=lambda item: item["path"]),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_case(root: Path) -> dict[str, Any] | None:
    path = root / "case.json"
    if not path.exists():
        return None
    case = load_json(path)
    if require(case, "schema", path.name) != 1:
        raise ValidationError("case.json: schema must be 1")
    expected_valid = require(case, "expected_valid", path.name)
    if not isinstance(expected_valid, bool):
        raise ValidationError("case.json: expected_valid must be boolean")
    expected_status = require(case, "expected_status", path.name)
    if expected_status not in RUN_STATUSES:
        raise ValidationError("case.json: expected_status is invalid")
    if not expected_valid:
        expected_error = require(case, "expected_error", path.name)
        if not isinstance(expected_error, str) or not expected_error.strip():
            raise ValidationError("case.json: expected_error is required for invalid fixtures")
    if "case" not in case or not str(case["case"]).strip():
        raise ValidationError("case.json: case is required")
    return case


def validate_phase0(scope: dict[str, Any], review_type: str) -> None:
    phase0 = scope.get("phase0")
    if review_type not in {"code", "mixed"}:
        if phase0 is not None and not isinstance(phase0, dict):
            raise ValidationError("scope.json: phase0 must be an object")
        return
    if not isinstance(phase0, dict):
        raise ValidationError("scope.json: phase0 metadata is required for code/mixed review")
    for key in ("head", "patch_sha256", "patch_files", "patch_lines", "size"):
        require(phase0, key, "scope.json: phase0")
    if not HEX40.fullmatch(str(phase0["head"])):
        raise ValidationError("scope.json: phase0.head must be a Git SHA-1")
    if not HEX64.fullmatch(str(phase0["patch_sha256"])):
        raise ValidationError("scope.json: phase0.patch_sha256 must be SHA-256")
    if any(isinstance(phase0[key], bool) or not isinstance(phase0[key], int) for key in ("patch_files", "patch_lines")):
        raise ValidationError("scope.json: phase0 patch counts must be integers")
    files = phase0["patch_files"]
    lines = phase0["patch_lines"]
    if not 0 <= files <= 40 or not 0 <= lines <= 1000:
        raise ValidationError("scope.json: phase0 patch exceeds supported limits")
    expected_size = "small" if files <= 20 and lines <= 300 else "large"
    if phase0["size"] != expected_size:
        raise ValidationError("scope.json: phase0.size does not match patch limits")


def is_run_artifact(relative: str) -> bool:
    parts = relative.split("/")
    return parts[0] in {"reviews", ".git", "__pycache__"} or relative in RUN_ARTIFACTS


def iter_manifest_root_files(root: Path, manifest_root: Path) -> set[str]:
    """Return ordinary files that the manifest must explicitly allow.

    Manifest entries are always relative to ``manifest_root``.  Run artifacts
    are excluded only when the run directory itself is the manifest root;
    a reviewed target may legitimately contain a directory called ``reviews``.
    """
    files: set[str] = set()
    for candidate in manifest_root.rglob("*"):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        relative = candidate.relative_to(manifest_root).as_posix()
        if manifest_root.resolve() == root.resolve() and is_run_artifact(relative):
            continue
        files.add(relative)
    return files


def validate_scope(root: Path, *, portable: bool = False) -> dict[str, Any]:
    scope = load_json(root / "scope.json")
    if require(scope, "schema", "scope.json") != 1:
        raise ValidationError("scope.json: schema must be 1")
    review_type = require(scope, "review_type", "scope.json")
    if review_type not in REVIEW_TYPES:
        raise ValidationError("scope.json: invalid review_type")
    validate_phase0(scope, review_type)
    fixture_mode = scope.get("fixture_mode")
    if fixture_mode is not None and fixture_mode != "portable":
        raise ValidationError("scope.json: invalid fixture_mode")
    if fixture_mode == "portable" and not portable:
        raise ValidationError("scope.json: portable fixture mode requires explicit fixture mode and case.json.fixture_mode=portable")
    isolation = require(scope, "isolation", "scope.json")
    if isolation not in {"isolated", "degraded"}:
        raise ValidationError("scope.json: invalid isolation")
    manifest_sha256 = require(scope, "manifest_sha256", "scope.json")
    if not HEX64.fullmatch(str(manifest_sha256)):
        raise ValidationError("scope.json: manifest_sha256 must be SHA-256")
    manifest = require(scope, "manifest", "scope.json")
    if not isinstance(manifest, list):
        raise ValidationError("scope.json: manifest must be a list")
    if len(manifest) > MAX_MANIFEST_FILES:
        raise ValidationError("scope.json: manifest exceeds file-count limit")
    total_size = 0
    paths: set[str] = set()
    for index, entry in enumerate(manifest):
        if not isinstance(entry, dict):
            raise ValidationError(f"scope.json: manifest[{index}] must be an object")
        for key in ("path", "size", "mtime", "sha256"):
            require(entry, key, f"scope.json: manifest[{index}]")
        path_value = str(entry["path"]).replace("\\", "/")
        if (
            path_value.startswith(("/", "//")) or path_value == ""
            or "/../" in f"/{path_value}/" or path_value.startswith("../")
            or re.match(r"^[A-Za-z]:", path_value) or ":" in path_value
            or any(ord(char) < 32 for char in path_value)
        ):
            raise ValidationError(f"scope.json: manifest[{index}].path must be repository-relative")
        if path_value in paths:
            raise ValidationError(f"scope.json: manifest[{index}].path is duplicated")
        paths.add(path_value)
        if SENSITIVE.search(path_value):
            raise ValidationError(f"scope.json: manifest[{index}].path is sensitive")
        try:
            size = int(entry["size"])
            mtime = int(entry["mtime"])
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"scope.json: manifest[{index}] size/mtime must be integers") from exc
        if size < 0:
            raise ValidationError(f"scope.json: manifest[{index}].size must be non-negative")
        if mtime < 0:
            raise ValidationError(f"scope.json: manifest[{index}].mtime must be non-negative")
        total_size += size
        if not HEX64.fullmatch(str(entry["sha256"])):
            raise ValidationError(f"scope.json: manifest[{index}].sha256 must be SHA-256")
    if total_size > MAX_MANIFEST_BYTES:
        raise ValidationError("scope.json: manifest exceeds byte limit")
    if canonical_manifest_hash(manifest) != manifest_sha256:
        raise ValidationError("scope.json: manifest_sha256 does not match manifest")
    manifest_root_value = scope.get("manifest_root", ".")
    manifest_root = Path(str(manifest_root_value))
    if not manifest_root.is_absolute():
        manifest_root = root / manifest_root
    try:
        manifest_root = manifest_root.resolve(strict=True)
    except OSError as exc:
        raise ValidationError("scope.json: manifest_root must be an existing directory") from exc
    if not manifest_root.is_dir():
        raise ValidationError("scope.json: manifest_root must be a directory")
    for index, entry in enumerate(manifest):
        candidate = manifest_root / str(entry["path"]).replace("/", os.sep)
        try:
            resolved = candidate.resolve(strict=True)
        except OSError as exc:
            raise ValidationError(f"scope.json: manifest[{index}].path does not exist") from exc
        try:
            resolved.relative_to(manifest_root)
        except ValueError as exc:
            raise ValidationError(f"scope.json: manifest[{index}].path escapes manifest_root") from exc
        if not resolved.is_file() or resolved.is_symlink():
            raise ValidationError(f"scope.json: manifest[{index}].path is not a regular file")
        stat = resolved.stat()
        if stat.st_size != int(entry["size"]):
            raise ValidationError(f"scope.json: manifest[{index}].size does not match file")
        if not (portable and int(entry["mtime"]) == 0) and stat.st_mtime_ns != int(entry["mtime"]):
            raise ValidationError(f"scope.json: manifest[{index}].mtime does not match file")
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
        if digest != str(entry["sha256"]):
            raise ValidationError(f"scope.json: manifest[{index}].sha256 does not match file")
    actual_files = iter_manifest_root_files(root, manifest_root)
    manifest_files = {
        str(entry["path"]).replace("\\", "/") for entry in manifest
    }
    extras = sorted(actual_files - manifest_files)
    if extras:
        raise ValidationError(f"allowlist violation: unlisted file {extras[0]}")
    return scope


def validate_finding(finding: dict[str, Any], path: str) -> None:
    for key in ("id", "severity", "locators", "category", "summary", "evidence", "fix", "domains", "lifecycle", "sources", "fingerprint"):
        require(finding, key, path)
    finding_id = str(finding["id"])
    if not ID.fullmatch(finding_id):
        raise ValidationError(f"{path}.id is invalid")
    if finding["severity"] not in SEVERITIES:
        raise ValidationError(f"{path}.severity is invalid")
    if finding["lifecycle"] not in LIFECYCLES:
        raise ValidationError(f"{path}.lifecycle is invalid")
    if not isinstance(finding["locators"], list) or not finding["locators"]:
        raise ValidationError(f"{path}.locators must be non-empty")
    if not isinstance(finding["evidence"], list) or not finding["evidence"]:
        raise ValidationError(f"{path}.evidence must be non-empty")
    if not isinstance(finding["domains"], list) or not isinstance(finding["sources"], list):
        raise ValidationError(f"{path}.domains and sources must be lists")
    contract = str(finding.get("affected_contract", ""))
    normalized = "|".join(sorted(str(item).strip().replace("\\", "/") for item in finding["locators"]))
    expected_fingerprint = hashlib.sha256(f"{normalized}|{finding['category']}|{contract}".encode("utf-8")).hexdigest()
    if str(finding["fingerprint"]) != expected_fingerprint:
        raise ValidationError(f"{path}.fingerprint must be SHA-256")


def validate_findings(root: Path) -> dict[str, Any]:
    data = load_json(root / "findings.json")
    if require(data, "schema", "findings.json") != 1:
        raise ValidationError("findings.json: schema must be 1")
    findings = require(data, "findings", "findings.json")
    if not isinstance(findings, list):
        raise ValidationError("findings.json: findings must be a list")
    ids: set[str] = set()
    for index, finding in enumerate(findings):
        path = f"findings.json: findings[{index}]"
        if not isinstance(finding, dict):
            raise ValidationError(f"{path} must be an object")
        validate_finding(finding, path)
        finding_id = str(finding["id"])
        if finding_id in ids:
            raise ValidationError(f"{path}.id is invalid or duplicated")
        ids.add(finding_id)
    return {"data": data, "ids": ids}


def validate_assignments(root: Path, finding_ids: set[str]) -> dict[str, Any]:
    data = load_json(root / "assignments.json")
    if require(data, "schema", "assignments.json") != 1:
        raise ValidationError("assignments.json: schema must be 1")
    domains = require(data, "domains", "assignments.json")
    if not isinstance(domains, list):
        raise ValidationError("assignments.json: domains must be a list")
    if not domains:
        state = load_json(root / "state.json")
        if state.get("status") == "complete":
            raise ValidationError("assignments.json: complete run requires at least one domain")
    seen: set[str] = set()
    for index, domain in enumerate(domains):
        path = f"assignments.json: domains[{index}]"
        if not isinstance(domain, dict):
            raise ValidationError(f"{path} must be an object")
        name = str(require(domain, "domain", path))
        if name in seen:
            raise ValidationError(f"{path}.domain duplicated")
        seen.add(name)
        status = require(domain, "status", path)
        if status not in DOMAIN_STATUSES:
            raise ValidationError(f"{path}.status is invalid")
        assigned = require(domain, "finding_ids", path)
        if not isinstance(assigned, list) or not set(assigned).issubset(finding_ids):
            raise ValidationError(f"{path}.finding_ids references unknown finding")
    return {"data": data, "domains": domains}


def validate_confirmations(root: Path, scope: dict[str, Any], assignments: dict[str, Any], finding_ids: set[str]) -> None:
    reviews = root / "reviews"
    decisions: dict[str, set[str]] = {}
    for domain in assignments["domains"]:
        name = str(domain["domain"])
        expected = set(domain["finding_ids"])
        candidates = list(reviews.glob(f"*-{name}-confirm.json"))
        if len(candidates) > 1:
            raise ValidationError(f"multiple confirmations for domain: {name}")
        if not candidates:
            if domain["status"] == "complete":
                raise ValidationError(f"missing confirmation for complete domain: {name}")
            continue
        data = load_json(candidates[0])
        if require(data, "schema", candidates[0].name) != 1:
            raise ValidationError(f"{candidates[0].name}: schema must be 1")
        if data.get("domain") != name:
            raise ValidationError(f"{candidates[0].name}: domain mismatch")
        if data.get("run") != scope.get("run"):
            raise ValidationError(f"{candidates[0].name}: run mismatch")
        target_hash = require(data, "target_manifest_sha256", candidates[0].name)
        if target_hash != scope.get("manifest_sha256"):
            raise ValidationError(f"{candidates[0].name}: target manifest mismatch")
        responses = require(data, "responses", candidates[0].name)
        if not isinstance(responses, list):
            raise ValidationError(f"{candidates[0].name}: responses must be a list")
        new_findings = data.get("new_findings", [])
        if not isinstance(new_findings, list):
            raise ValidationError(f"{candidates[0].name}: new_findings must be a list")
        new_ids: set[str] = set()
        for index, finding in enumerate(new_findings):
            if not isinstance(finding, dict):
                raise ValidationError(f"{candidates[0].name}: new_findings[{index}] must be an object")
            validate_finding(finding, f"{candidates[0].name}: new_findings[{index}]")
            finding_id = str(finding["id"])
            if finding_id in finding_ids or finding_id in new_ids:
                raise ValidationError(f"{candidates[0].name}: duplicate new finding id")
            new_ids.add(finding_id)
        responded: set[str] = set()
        for response in responses:
            if not isinstance(response, dict):
                raise ValidationError(f"{candidates[0].name}: response must be an object")
            finding_id = str(require(response, "finding_id", candidates[0].name))
            decision = require(response, "decision", candidates[0].name)
            if finding_id not in expected or finding_id in responded:
                raise ValidationError(f"{candidates[0].name}: invalid or duplicate response id")
            if decision not in DECISIONS:
                raise ValidationError(f"{candidates[0].name}: invalid decision")
            decisions.setdefault(finding_id, set()).add(str(decision))
            if decision == "NEW" and not new_findings:
                raise ValidationError(f"{candidates[0].name}: NEW requires new_findings")
            if decision in {"CONFIRM", "REFINE"} and not response.get("fix"):
                raise ValidationError(f"{candidates[0].name}: {decision} requires fix")
            if decision in {"CONFIRM", "REFINE", "NEW"} and not response.get("evidence"):
                raise ValidationError(f"{candidates[0].name}: {decision} requires evidence")
            if decision == "REJECT" and not response.get("reason"):
                raise ValidationError(f"{candidates[0].name}: REJECT requires reason")
            responded.add(finding_id)
        if domain["status"] == "complete" and responded != expected:
            raise ValidationError(f"{candidates[0].name}: incomplete required responses")
        if domain["status"] == "complete" and any(item.get("decision") == "ABSENT" for item in responses):
            raise ValidationError(f"{candidates[0].name}: ABSENT cannot complete a domain")
    for finding_id, finding_decisions in decisions.items():
        if "REJECT" in finding_decisions and finding_decisions & {"CONFIRM", "REFINE"}:
            raise ValidationError(f"conflicting expert decisions for {finding_id}")


def validate_lock(root: Path, scope: dict[str, Any]) -> None:
    lock = load_json(root / "run.lock")
    if require(lock, "schema", "run.lock") != 1:
        raise ValidationError("run.lock: schema must be 1")
    if lock.get("run") != scope.get("run"):
        raise ValidationError("run.lock: run mismatch")
    if not str(require(lock, "owner", "run.lock")).strip():
        raise ValidationError("run.lock: owner is required")
    try:
        pid = int(require(lock, "pid", "run.lock"))
    except (TypeError, ValueError) as exc:
        raise ValidationError("run.lock: pid must be an integer") from exc
    if pid < 0 or not str(require(lock, "created_at", "run.lock")).strip():
        raise ValidationError("run.lock: invalid pid/created_at")


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValidationError("final-review.md: missing YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValidationError("final-review.md: unterminated frontmatter")
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def validate_review_type(scope: dict[str, Any], findings: dict[str, Any], review_type: str) -> None:
    all_findings = findings["data"]["findings"]
    sources: set[str] = set()
    for finding in all_findings:
        finding_id = str(finding["id"])
        finding_sources = {str(source) for source in finding["sources"]}
        if not finding_sources or not finding_sources <= {"code", "design"}:
            raise ValidationError("finding sources must contain only code or design")
        if finding_id.startswith("code-") and "code" not in finding_sources:
            raise ValidationError("code finding id must use code source")
        if finding_id.startswith("design-") and "design" not in finding_sources:
            raise ValidationError("design finding id must use design source")
        sources.update(finding_sources)
        if review_type == "code" and "code" not in finding_sources:
            raise ValidationError("code review must contain only code findings")
        if review_type == "design" and "design" not in finding_sources:
            raise ValidationError("design review must contain only design findings")
    if review_type == "mixed" and all_findings and not {"code", "design"} <= sources:
        raise ValidationError("mixed review must contain independent code and design findings")
    if scope.get("review_type") != review_type:
        raise ValidationError("review type mismatch")


def validate_final(root: Path, scope: dict[str, Any], assignments: dict[str, Any], findings: dict[str, Any]) -> None:
    required = ("run.lock", "team.md", "scope.md", "run-status.md", "scope.json", "state.json", "assignments.json", "findings.json")
    for name in required:
        if not (root / name).exists():
            raise ValidationError(f"missing required artifact: {name}")
    validate_lock(root, scope)
    state = load_json(root / "state.json")
    if require(state, "schema", "state.json") != 1:
        raise ValidationError("state.json: schema must be 1")
    status = require(state, "status", "state.json")
    if status not in RUN_STATUSES:
        raise ValidationError("state.json: invalid status")
    status_text = (root / "run-status.md").read_text(encoding="utf-8").lower()
    if status not in status_text:
        raise ValidationError("run-status.md does not match state.json")
    conflict_file = root / "reviews" / "90-conflicts.json"
    if conflict_file.exists():
        conflicts = load_json(conflict_file)
        if require(conflicts, "schema", conflict_file.name) != 1 or not isinstance(conflicts.get("conflicts"), list) or not conflicts["conflicts"]:
            raise ValidationError("90-conflicts.json: conflicts must be a non-empty list")
        if status != "pending-human":
            raise ValidationError("unresolved conflicts require pending-human status")
    if status == "blocked":
        reason = root / "block-reason.json"
        if not reason.is_file():
            raise ValidationError("blocked run is missing block-reason.json")
        reason_data = load_json(reason)
        if require(reason_data, "schema", reason.name) != 1 or not str(require(reason_data, "reason", reason.name)).strip():
            raise ValidationError("block-reason.json: reason is required")
    final = root / "final-review.md"
    if status != "complete":
        if final.exists():
            raise ValidationError("final-review.md must not exist before complete")
        return
    if scope["isolation"] != "isolated":
        raise ValidationError("complete run cannot use degraded isolation")
    if any(domain["status"] != "complete" for domain in assignments["domains"]):
        raise ValidationError("complete run has incomplete domain")
    if not final.is_file():
        raise ValidationError("complete run is missing final-review.md")
    values = frontmatter(final)
    required_metadata = ("schema", "status", "review-type", "verdict", "run", "base-commit", "severity-counts", "isolation", "unconfirmed-domains")
    missing = [key for key in required_metadata if key not in values]
    if missing:
        raise ValidationError(f"final-review.md: missing metadata: {', '.join(missing)}")
    if values.get("schema") != "1" or values.get("status") != "complete":
        raise ValidationError("final-review.md: invalid schema/status")
    review_type = values.get("review-type")
    if review_type not in REVIEW_TYPES:
        raise ValidationError("final-review.md: invalid review-type")
    validate_review_type(scope, findings, review_type)
    if values.get("verdict") not in VERDICTS:
        raise ValidationError("final-review.md: invalid verdict")
    if values.get("run") != scope.get("run"):
        raise ValidationError("final-review.md: run mismatch")
    if values.get("isolation") != scope.get("isolation"):
        raise ValidationError("final-review.md: isolation mismatch")
    if values.get("unconfirmed-domains") != "[]":
        raise ValidationError("final-review.md: complete run cannot have unconfirmed domains")
    open_severities = {
        str(item["severity"])
        for item in findings["data"]["findings"]
        if item["lifecycle"] == "open"
    }
    if values["verdict"] == "APPROVE" and open_severities & {"Critical", "Important"}:
        raise ValidationError("final-review.md: APPROVE cannot contain open Critical or Important findings")
    if values["verdict"] == "REQUEST CHANGES" and not open_severities & {"Critical", "Important"}:
        raise ValidationError("final-review.md: REQUEST CHANGES requires an open Critical or Important finding")
    if values["verdict"] == "REJECT":
        if review_type not in {"design", "mixed"}:
            raise ValidationError("final-review.md: REJECT is only valid for design or mixed review")
        if not any(item.get("hard_constraint") is True and item["lifecycle"] == "open" for item in findings["data"]["findings"]):
            raise ValidationError("final-review.md: REJECT requires an open hard constraint")


def validate(root: Path) -> None:
    case = load_case(root)
    scope_preview = load_json(root / "scope.json")
    portable = bool(
        case
        and case.get("expected_valid") is True
        and case.get("fixture_mode") == "portable"
        and scope_preview.get("fixture_mode") == "portable"
    )
    scope = validate_scope(root, portable=portable)
    findings = validate_findings(root)
    assignments = validate_assignments(root, findings["ids"])
    validate_confirmations(root, scope, assignments, findings["ids"])
    validate_final(root, scope, assignments, findings)
    if case is not None:
        state = load_json(root / "state.json")
        expected_status = case["expected_status"]
        if state.get("status") != expected_status:
            raise ValidationError(f"case.json: expected status {expected_status}")
        expected_verdict = case.get("expected_verdict")
        if expected_verdict:
            values = frontmatter(root / "final-review.md")
            if values.get("verdict") != expected_verdict:
                raise ValidationError(f"case.json: expected verdict {expected_verdict}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--all", action="store_true", help="validate every immediate fixture directory")
    args = parser.parse_args()
    roots = sorted(p for p in args.root.iterdir() if p.is_dir()) if args.all else [args.root]
    failures: list[str] = []
    if args.all and not roots:
        print(f"FAIL {args.root}: --all found no fixture directories")
        return 1
    for root in roots:
        case: dict[str, Any] | None = None
        try:
            case = load_case(root)
            if args.all and case is None:
                raise ValidationError("case.json is required for --all fixture validation")
            validate(root)
        except (OSError, ValidationError) as exc:
            if args.all and case is not None and case.get("expected_valid") is False and str(case.get("expected_error", "")) in str(exc):
                print(f"PASS expected-invalid {root}: {exc}")
                continue
            failures.append(f"FAIL {root}: {exc}")
            print(failures[-1])
        else:
            if case is not None and case.get("expected_valid") is False:
                failures.append(f"FAIL {root}: expected validator rejection")
                print(failures[-1])
            else:
                print(f"PASS {root}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
