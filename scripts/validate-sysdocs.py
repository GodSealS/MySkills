#!/usr/bin/env python3
"""Validate a SysDocs tree using the shared protocol rule IDs.

This is a repository test utility, not a runtime deployed to consuming projects.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit("validate-sysdocs.py requires PyYAML") from exc

SCHEMA = 1
STATUSES = {"draft", "active", "stale", "archived"}
DOC_TYPES = {"overview", "module", "page", "vibe"}
MERMAID_TYPES = {"flowchart", "sequenceDiagram", "stateDiagram", "classDiagram", "erDiagram", "graph"}
SYMBOL_RE = re.compile(r"(?:ts|js|py|cpp|cs)\|[^\s:`]+:[^\s`]+")
SECRET_RE = re.compile(r"(?i)(?:api[_-]?key|password|secret|token|private[_-]?key)\s*[:=]\s*([^\s,;`]+)")


def issue(items, rule_id, severity, path, message, suggestion=""):
    items.append({"rule_id": rule_id, "severity": severity, "path": path, "message": message, "suggestion": suggestion})


def read_doc(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    raw = text[3:end]
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        data = None
    return data, text[end + 4 :]


def validate(root: Path):
    issues = []
    files = sorted(root.rglob("*.md"))
    docs = {}
    for path in files:
        rel = path.relative_to(root.parent).as_posix()
        fm, body = read_doc(path)
        docs[path] = (rel, fm, body)
        if fm is None:
            issue(issues, "SYSDOC-FM-01", "blocking", rel, "frontmatter missing or invalid")
            continue
        if not isinstance(fm, dict):
            issue(issues, "SYSDOC-FM-01", "blocking", rel, "frontmatter must be a mapping")
            continue
        if not isinstance(fm.get("schema"), int) or fm["schema"] > SCHEMA:
            issue(issues, "SYSDOC-FM-02", "blocking", rel, "schema is newer than validator")
        if fm.get("doc_type") not in DOC_TYPES:
            issue(issues, "SYSDOC-FM-03", "blocking", rel, "invalid or missing doc_type")
        if fm.get("status") not in STATUSES:
            issue(issues, "SYSDOC-FM-03", "blocking", rel, "invalid or missing status")
        if fm.get("doc_type") == "overview" and not isinstance(fm.get("modules"), list):
            issue(issues, "SYSDOC-FM-04", "blocking", rel, "overview.modules must be a list")
        if fm.get("doc_type") == "module" and not isinstance(fm.get("module_id"), str):
            issue(issues, "SYSDOC-FM-03", "blocking", rel, "module_id is required")
        if fm.get("doc_type") == "page" and not all(isinstance(fm.get(k), str) for k in ("module_id", "page_id")):
            issue(issues, "SYSDOC-FM-03", "blocking", rel, "page requires module_id and page_id")
        if fm.get("doc_type") == "vibe" and not isinstance(fm.get("vibe_id"), str):
            issue(issues, "SYSDOC-FM-03", "blocking", rel, "vibe_id is required")

        opens = [m.start() for m in re.finditer(r"<!-- human:start -->", body)]
        closes = [m.start() for m in re.finditer(r"<!-- human:end -->", body)]
        if len(opens) != len(closes):
            issue(issues, "SYSDOC-HUMAN-01", "blocking", rel, "human markers are not paired")
        depth = 0
        for marker in re.finditer(r"<!-- human:(start|end) -->", body):
            depth += 1 if marker.group(1) == "start" else -1
            if depth < 0 or depth > 1:
                issue(issues, "SYSDOC-HUMAN-02", "blocking", rel, "human blocks are nested or misordered")
                break

        for link in re.findall(r"\[[^]]+\]\(([^)]+)\)", body):
            if link.startswith(("http://", "https://", "#")):
                continue
            target = (path.parent / link.split("#", 1)[0]).resolve()
            if root.resolve() not in target.parents and target != root.resolve():
                issue(issues, "SYSDOC-LINK-02", "blocking", rel, "link escapes project root")
            elif not target.exists():
                issue(issues, "SYSDOC-LINK-01", "blocking", rel, f"link target missing: {link}")

        for block in re.findall(r"```([^\n]*)\n(.*?)```", body, flags=re.S):
            language = block[0].strip()
            if language == "mermaid":
                first = next((line.strip().split()[0] for line in block[1].splitlines() if line.strip()), "")
                if first not in MERMAID_TYPES:
                    issue(issues, "SYSDOC-MERMAID-01", "blocking", rel, "unsupported Mermaid diagram type")

        symbols = SYMBOL_RE.findall(body)
        if symbols and len(symbols) != len(set(symbols)):
            issue(issues, "SYSDOC-REF-02", "warning", rel, "duplicate symbol reference")
        for match in SECRET_RE.finditer(body):
            value = match.group(1)
            if not value.startswith("[REDACTED:") and value not in {"<value>", "<redacted>"}:
                issue(issues, "SYSDOC-SEC-01", "blocking", rel, "possible secret value in document")

    overview = root / "SYSTEM_ROOT.md"
    if overview.exists():
        fm, _ = read_doc(overview)
        manifest = fm.get("modules", []) if isinstance(fm, dict) else []
        declared = {entry.get("id"): entry for entry in manifest if isinstance(entry, dict)}
        module_files = {p.stem: p for p in (root / "modules").glob("*.md")} if (root / "modules").exists() else {}
        if set(declared) != set(module_files):
            issue(issues, "SYSDOC-MAN-01", "blocking", "SysDocs/SYSTEM_ROOT.md", "manifest and module files differ")
        for module_id, entry in declared.items():
            rel_path = entry.get("path")
            if not isinstance(rel_path, str) or not (root / rel_path).exists():
                issue(issues, "SYSDOC-MAN-01", "blocking", "SysDocs/SYSTEM_ROOT.md", f"manifest path missing: {rel_path}")
            module_path = module_files.get(module_id)
            if module_path:
                module_fm, _ = read_doc(module_path)
                if not isinstance(module_fm, dict) or module_fm.get("module_id") != module_id:
                    issue(issues, "SYSDOC-MAN-02", "blocking", module_path.relative_to(root.parent).as_posix(), "module_id does not match manifest")
            registered_pages = entry.get("pages", []) if isinstance(entry, dict) else []
            if not isinstance(registered_pages, list):
                issue(issues, "SYSDOC-FM-04", "blocking", "SysDocs/SYSTEM_ROOT.md", f"pages must be a list for {module_id}")
                registered_pages = []
            registered_paths = set()
            for page_ref in registered_pages:
                page_path = root / page_ref
                registered_paths.add(page_path.resolve())
                if not page_path.exists():
                    issue(issues, "SYSDOC-MAN-03", "blocking", "SysDocs/SYSTEM_ROOT.md", f"page path missing: {page_ref}")
                    continue
                page_fm, _ = read_doc(page_path)
                if not isinstance(page_fm, dict) or page_fm.get("doc_type") != "page" or page_fm.get("module_id") != module_id:
                    issue(issues, "SYSDOC-MAN-03", "blocking", page_ref, "page metadata does not match manifest")
            page_dir = root / "modules" / module_id
            if page_dir.exists():
                for page_path in page_dir.glob("*.md"):
                    if page_path.resolve() not in registered_paths:
                        issue(issues, "SYSDOC-MAN-03", "blocking", page_path.relative_to(root.parent).as_posix(), "page is not registered")

    blocking = [item for item in issues if item["severity"] == "blocking"]
    status = "FAILED" if blocking else ("PARTIAL" if issues else "COMPLETE")
    return status, issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    root = args.root.resolve()
    status, issues = validate(root)
    report = {"schema": 1, "status": status, "root": root.as_posix(), "issues": issues}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status != "FAILED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
