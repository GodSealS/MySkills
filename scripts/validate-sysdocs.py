#!/usr/bin/env python3
"""Validate a SysDocs tree using the shared protocol rule IDs.

This is a repository test utility, not a runtime deployed to consuming projects.
"""
from __future__ import annotations

import argparse
import datetime
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit("validate-sysdocs.py requires PyYAML") from exc

SCHEMA = 2
STATUSES = {"draft", "active", "stale", "archived"}
DOC_TYPES = {"overview", "module", "page", "vibe"}
MERMAID_TYPES = {"flowchart", "sequenceDiagram", "stateDiagram", "classDiagram", "erDiagram", "graph"}
SYMBOL_RE = re.compile(r"(?:ts|js|py|cpp|cs)\|[^\s:`]+:[^\s`]+")
SECRET_RE = re.compile(r"(?i)(?:api[_-]?key|password|secret|token|private[_-]?key)\s*[:=]\s*([^\s,;`]+)")


def issue(items, rule_id, severity, path, message, suggestion=""):
    items.append({"rule_id": rule_id, "severity": severity, "path": path, "message": message, "suggestion": suggestion})


def read_doc(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    raw = text[3:end]
    try:
        data = yaml.safe_load(raw) or {}
    except (yaml.YAMLError, ValueError, TypeError):
        data = None
    return data, text[end + 4 :]


def validate_legacy(root: Path, documents=None, requested=None):
    issues = []
    files = sorted(documents) if documents is not None else [p for p in sorted(root.rglob("*.md")) if ".meta" not in p.relative_to(root).parts]
    docs = {}
    for path in files:
        rel = path.relative_to(root.parent).as_posix()
        if not path.resolve().is_relative_to(root):
            issue(issues, "SYSDOC-PATH-02", "blocking", rel, "document escapes SysDocs")
            continue
        try:
            fm, body = documents[path] if documents is not None else read_doc(path)
        except (OSError, UnicodeError):
            issue(issues, "SYSDOC-FM-01", "blocking", rel, "document cannot be read as UTF-8")
            continue
        docs[path] = (rel, fm, body)
        if requested is not None and path not in requested:
            check_body(path, root, body, issues, requested)
            continue
        # Proposals and authorities do not change the surrounding fact layout.
        if path.relative_to(root).parts[0] in {"specs", "decisions", "VibeCoding"}:
            check_metadata(path, root, fm, body, issues)
            check_body(path, root, body, issues)
            continue
        if fm is None:
            issue(issues, "SYSDOC-FM-01", "blocking", rel, "frontmatter missing or invalid")
            continue
        if not isinstance(fm, dict):
            issue(issues, "SYSDOC-FM-01", "blocking", rel, "frontmatter must be a mapping")
            continue
        if type(fm.get("schema")) is not int or fm["schema"] != 1:
            issue(issues, "SYSDOC-FM-02", "blocking", rel, "schema is newer than validator")
        if not isinstance(fm.get("doc_type"), str) or fm["doc_type"] not in DOC_TYPES:
            issue(issues, "SYSDOC-FM-03", "blocking", rel, "invalid or missing doc_type")
        if not isinstance(fm.get("status"), str) or fm["status"] not in STATUSES:
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
            if not target.is_relative_to(root.parent.resolve()):
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
    if overview in docs and (requested is None or overview in requested):
        _, fm, _ = docs[overview]
        manifest = fm.get("modules", []) if isinstance(fm, dict) else []
        if not isinstance(manifest, list):
            manifest = []
        declared = {entry["id"]: entry for entry in manifest if isinstance(entry, dict) and isinstance(entry.get("id"), str)}
        if len(declared) != len(manifest):
            issue(issues, "SYSDOC-FM-04", "blocking", "SysDocs/SYSTEM_ROOT.md", "module entries must have unique string ids")
        module_files = {p.stem: p for p in docs if p.parent == root / "modules"}
        if set(declared) != set(module_files):
            issue(issues, "SYSDOC-MAN-01", "blocking", "SysDocs/SYSTEM_ROOT.md", "manifest and module files differ")
        for module_id, entry in declared.items():
            rel_path = entry.get("path")
            if not isinstance(rel_path, str) or not (root / rel_path).resolve().is_relative_to(root) or not (root / rel_path).is_file():
                issue(issues, "SYSDOC-MAN-01", "blocking", "SysDocs/SYSTEM_ROOT.md", f"manifest path missing: {rel_path}")
            module_path = module_files.get(module_id)
            if module_path:
                _, module_fm, _ = docs[module_path]
                if not isinstance(module_fm, dict) or module_fm.get("module_id") != module_id:
                    issue(issues, "SYSDOC-MAN-02", "blocking", module_path.relative_to(root.parent).as_posix(), "module_id does not match manifest")
            registered_pages = entry.get("pages", []) if isinstance(entry, dict) else []
            if not isinstance(registered_pages, list):
                issue(issues, "SYSDOC-FM-04", "blocking", "SysDocs/SYSTEM_ROOT.md", f"pages must be a list for {module_id}")
                registered_pages = []
            registered_paths = set()
            for page_ref in registered_pages:
                if not isinstance(page_ref, str) or not (root / page_ref).resolve().is_relative_to(root):
                    issue(issues, "SYSDOC-PATH-02", "blocking", "SysDocs/SYSTEM_ROOT.md", "registered page escapes SysDocs or has invalid path")
                    continue
                page_path = (root / page_ref).resolve()
                registered_paths.add(page_path.resolve())
                if page_path not in docs or not page_path.is_file():
                    issue(issues, "SYSDOC-MAN-03", "blocking", "SysDocs/SYSTEM_ROOT.md", f"page path missing: {page_ref}")
                    continue
                _, page_fm, _ = docs[page_path]
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


FACT_TYPES = {"overview", "architecture", "files"}
NEW_TYPES = FACT_TYPES | {"spec", "decision", "vibe"}
SOURCE_SCOPES = {"committed", "committed+working-tree", "unversioned"}
REQUIRED = ("README.md", "PROJECT-MAP.md", "architecture/overview.md", "files/README.md")


def summary(body):
    """Extract the fixed header section without sending the body to the caller."""
    match = re.search(r"(?m)^## 检索摘要\s*$", body)
    if not match:
        return None
    before = body[:match.start()]
    if any(line.strip() and not line.startswith("# ") for line in before.splitlines()):
        return None
    rest = body[match.end():]
    end = re.search(r"(?m)^#{1,2} ", rest)
    return rest[:end.start() if end else len(rest)].strip() or None


def links(body):
    # Deliberately limited to inline Markdown links; not a full Markdown parser.
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    return [m.strip("<>") for m in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body)]


def local_target(path, link):
    try:
        parsed = urlsplit(link)
    except ValueError:
        return None
    if parsed.scheme or parsed.netloc:
        return None
    return (path.parent / unquote(parsed.path)).resolve()


def compatibility_page(body):
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return bool(links(body)) and all(line.startswith("# ") or re.fullmatch(r"\[[^\]]+\]\([^)]+\)", line) for line in lines)


def check_source_path(project, value, rel, issues):
    if not isinstance(value, str) or not value or Path(value).is_absolute() or any(c in value for c in "*?["):
        issue(issues, "SYSDOC-PATH-02", "blocking", rel, "source path must be a project-relative file or directory")
        return None
    target = (project / value).resolve()
    if not target.is_relative_to(project):
        issue(issues, "SYSDOC-PATH-02", "blocking", rel, "source path escapes project root")
        return None
    if not target.exists():
        issue(issues, "SYSDOC-PATH-01", "blocking", rel, f"source path missing: {value}")
    return target


def check_metadata(path, root, fm, body, issues):
    rel = path.relative_to(root.parent).as_posix()
    legacy_redirect = (path == root / "SYSTEM_ROOT.md" or path.is_relative_to(root / "modules")) and compatibility_page(body)
    if fm is None and (path.relative_to(root).parts[0] in {"specs", "decisions", "VibeCoding"} or legacy_redirect):
        return  # Existing authority and link-only redirects need not be rewritten.
    if not isinstance(fm, dict):
        issue(issues, "SYSDOC-FM-01", "blocking", rel, "frontmatter missing, invalid or not a mapping")
        return
    if path.relative_to(root).parts[0] in {"specs", "decisions"} and "schema" not in fm and "doc_type" not in fm:
        return  # Historical authority metadata is not a SysDocs schema declaration.
    if fm.get("schema") == 1 and fm.get("doc_type") == "vibe" and path.relative_to(root).parts[0] == "VibeCoding":
        if not isinstance(fm.get("vibe_id"), str) or not isinstance(fm.get("status"), str) or fm["status"] not in STATUSES:
            issue(issues, "SYSDOC-FM-03", "blocking", rel, "legacy proposal requires vibe_id and status")
        return
    if type(fm.get("schema")) is not int or fm["schema"] != SCHEMA:
        issue(issues, "SYSDOC-FM-02", "blocking", rel, "unsupported schema; retain original, read-only")
        return
    doc_type = fm.get("doc_type")
    if not isinstance(doc_type, str) or doc_type not in NEW_TYPES:
        issue(issues, "SYSDOC-FM-03", "blocking", rel, "invalid doc_type")
        return
    expected_type = "overview" if path == root / "README.md" else "architecture" if path == root / "PROJECT-MAP.md" or path.is_relative_to(root / "architecture") else "files" if path.is_relative_to(root / "files") else None
    if expected_type and doc_type != expected_type:
        issue(issues, "SYSDOC-FM-03", "blocking", rel, f"this location requires doc_type {expected_type}")
    if "status" in fm and (not isinstance(fm["status"], str) or fm["status"] not in STATUSES):
        issue(issues, "SYSDOC-FM-03", "blocking", rel, "invalid optional status")
    try:
        datetime.datetime.fromisoformat(str(fm.get("updated")))
    except ValueError:
        issue(issues, "SYSDOC-FM-03", "blocking", rel, "updated must be an ISO date")
    if fm.get("doc_type") not in FACT_TYPES:
        return
    if not summary(body):
        issue(issues, "SYSDOC-SUMMARY-01", "blocking", rel, "nonempty header retrieval summary required before details")
    source_scope = fm.get("source_scope")
    if not isinstance(source_scope, str) or source_scope not in SOURCE_SCOPES:
        issue(issues, "SYSDOC-BASELINE-01", "blocking", rel, "invalid source_scope")
        source_scope = None
    source_paths = fm.get("source_paths")
    if not isinstance(source_paths, list):
        issue(issues, "SYSDOC-FM-03", "blocking", rel, "source_paths must be a list")
    else:
        for value in source_paths:
            check_source_path(root.parent, value, rel, issues)
    if source_scope in {"committed", "committed+working-tree"}:
        sha = fm.get("generated_from")
        valid = isinstance(sha, str) and re.fullmatch(r"[0-9a-fA-F]{7,40}", sha)
        if valid:
            try:
                result = subprocess.run(["git", "-C", str(root.parent), "merge-base", "--is-ancestor", sha, "HEAD"], capture_output=True)
                valid = result.returncode == 0
            except OSError:
                valid = False
        if not valid:
            issue(issues, "SYSDOC-BASELINE-01", "blocking", rel, "generated_from must be a reachable commit, not a working-tree snapshot")
    if fm.get("source_scope") == "committed+working-tree":
        evidence = fm.get("evidence")
        if not evidence:
            issue(issues, "SYSDOC-BASELINE-01", "blocking", rel, "working-tree source requires an evidence reference beyond HEAD")
        else:
            check_source_path(root.parent, evidence.split("#", 1)[0] if isinstance(evidence, str) else evidence, rel, issues)
    if path.parent in {root / "architecture/modules", root / "files"} and path.name != "README.md":
        if fm.get("module_id") != path.stem:
            issue(issues, "SYSDOC-MAN-02", "blocking", rel, "module_id must match the module filename")


def check_body(path, root, body, issues, incoming_to=None):
    rel = path.relative_to(root.parent).as_posix()
    for link in links(body):
        target = local_target(path, link)
        if incoming_to is not None and target not in incoming_to:
            continue
        try:
            urlsplit(link)
        except ValueError:
            issue(issues, "SYSDOC-LINK-01", "blocking", rel, "invalid link URL")
            continue
        if target is None:
            continue
        if not target.is_relative_to(root.parent):
            issue(issues, "SYSDOC-LINK-02", "blocking", rel, "link escapes project root")
        elif not target.exists():
            issue(issues, "SYSDOC-LINK-01", "blocking", rel, f"link target missing: {link}")
    if incoming_to is not None:
        return
    depth = 0
    for marker in re.finditer(r"<!-- human:(start|end) -->", body):
        depth += 1 if marker[1] == "start" else -1
        if depth not in (0, 1):
            issue(issues, "SYSDOC-HUMAN-02", "blocking", rel, "human blocks nested or misordered")
            break
    if depth:
        issue(issues, "SYSDOC-HUMAN-01", "blocking", rel, "human markers are not paired")
    for block in re.findall(r"```mermaid\s*\n(.*?)```", body, re.S):
        first = next((line.strip().split()[0] for line in block.splitlines() if line.strip()), "")
        if first not in MERMAID_TYPES:
            issue(issues, "SYSDOC-MERMAID-01", "blocking", rel, "unsupported Mermaid diagram type")
    for match in SECRET_RE.finditer(body):
        if not match[1].startswith("[REDACTED:") and match[1] not in {"<value>", "<redacted>"}:
            issue(issues, "SYSDOC-SEC-01", "blocking", rel, "possible secret value in document")


def index_rows(body):
    in_table = False
    for line in body.splitlines():
        cells = [part.strip().strip("`") for part in line.strip().strip("|").split("|")]
        if cells == ["源码路径", "职责", "模块"]:
            in_table = True
        elif in_table and line.startswith("|") and len(cells) == 3 and not all(re.fullmatch(r":?-+:?", c) for c in cells):
            yield cells
        elif in_table and not line.startswith("|"):
            in_table = False


def check_coverage(root, docs, selected, issues, full):
    owned = {}
    for path, (fm, body) in docs.items():
        if path.parent != root / "files" or path.name == "README.md":
            continue
        for source, responsibility, module_id in index_rows(body):
            source_target = (root.parent / source).resolve()
            owned.setdefault(source_target, []).append(path)
            if path not in selected:
                continue
            rel = path.relative_to(root.parent).as_posix()
            checked = check_source_path(root.parent, source, rel, issues)
            if checked is not None and checked.exists() and not checked.is_file():
                issue(issues, "SYSDOC-PATH-01", "blocking", rel, "file responsibility rows must reference files, not directories")
            if not responsibility or not isinstance(fm, dict) or module_id != fm.get("module_id"):
                issue(issues, "SYSDOC-COVERAGE-01", "blocking", rel, "file row requires responsibility and owning module_id")
    for source, owners in owned.items():
        if len(owners) > 1 and any(path in selected for path in owners):
            issue(issues, "SYSDOC-COVERAGE-02", "blocking", owners[0].relative_to(root.parent).as_posix(), "duplicate file ownership after resolving path aliases")
    scope_doc = root / "files/README.md"
    if not full and not any(p.parent == root / "files" for p in selected):
        return
    if scope_doc not in docs:
        return
    fm = docs[scope_doc][0]
    if not isinstance(fm, dict) or not isinstance(fm.get("source_paths"), list):
        return
    exclusions = fm.get("exclusions", [])
    if not isinstance(exclusions, list) or not all(isinstance(x, str) for x in exclusions):
        issue(issues, "SYSDOC-FM-03", "blocking", "SysDocs/files/README.md", "exclusions must be a list of project-relative patterns")
        exclusions = []
    checked_paths = fm["source_paths"] if full else [value for path in selected if path.parent == root / "files" for data in [docs[path][0]] if isinstance(data, dict) and isinstance(data.get("source_paths"), list) for value in data["source_paths"]]
    for value in checked_paths:
        if not isinstance(value, str):
            continue
        source_root = (root.parent / value).resolve()
        if not source_root.is_relative_to(root.parent) or not source_root.exists():
            continue
        for source_path in ([source_root] if source_root.is_file() else source_root.rglob("*")):
            if not source_path.is_file():
                continue
            source = source_path.relative_to(root.parent).as_posix()
            if not source_path.resolve().is_relative_to(root.parent):
                issue(issues, "SYSDOC-PATH-02", "blocking", "SysDocs/files/README.md", f"source symlink escapes project: {source}")
                continue
            if any(fnmatch.fnmatchcase(source, pattern) or source.startswith(pattern.rstrip("/") + "/") for pattern in exclusions):
                continue
            if source_path.resolve() not in owned:
                issue(issues, "SYSDOC-COVERAGE-01", "blocking", "SysDocs/files/README.md", f"source file has no owner: {source}")


def check_navigation(root, docs, issues):
    readme = root / "README.md"
    project_map = root / "PROJECT-MAP.md"
    if project_map in docs and readme in docs:
        if project_map not in {local_target(readme, link) for link in links(docs[readme][1])}:
            issue(issues, "SYSDOC-LAYOUT-01", "blocking", "SysDocs/PROJECT-MAP.md", "project map requires a direct README navigation link")
    reachable = set()
    pending = [root / "README.md"]
    while pending:
        path = pending.pop()
        if path in reachable or path not in docs:
            continue
        reachable.add(path)
        pending.extend(target for link in links(docs[path][1]) if (target := local_target(path, link)) in docs)
    for path in docs:
        if path.is_relative_to(root / "architecture") or path.is_relative_to(root / "files"):
            if path not in reachable:
                issue(issues, "SYSDOC-LAYOUT-01", "blocking", path.relative_to(root.parent).as_posix(), "fact page is not reachable from README navigation")


def redact(value):
    """Never echo a detected credential value in summaries or diagnostics."""
    if isinstance(value, str):
        return SECRET_RE.sub(lambda m: m[0][:m.start(1) - m.start()] + "[REDACTED:possible-secret]", value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def inspect(root, files=None, summaries=False):
    root = root.resolve()
    project = root.parent
    issues = []
    read_issues = []
    docs = {}
    for path in sorted(root.rglob("*.md")):
        if ".meta" in path.relative_to(root).parts:
            continue
        if not path.resolve().is_relative_to(root):
            issue(issues, "SYSDOC-PATH-02", "blocking", path.relative_to(project).as_posix(), "document symlink escapes SysDocs")
            continue
        try:
            docs[path] = read_doc(path)
        except (OSError, UnicodeError):
            issue(read_issues, "SYSDOC-FM-01", "blocking", path.relative_to(project).as_posix(), "document cannot be read as UTF-8")
    selected = set(docs)
    requested = set(docs)
    if files is not None:
        requested = {(project / value).resolve() for value in files}
        if any(not path.is_relative_to(root) for path in requested):
            issue(issues, "SYSDOC-PATH-02", "blocking", "SysDocs", "--files must identify documents inside SysDocs")
        selected = {path for path in requested if path in docs}
        # One-hop incoming links, not recursive expansion through all navigation.
        selected.update(path for path, (_, body) in docs.items() if any(local_target(path, link) in requested for link in links(body)))
        if not selected:
            issue(issues, "SYSDOC-SCOPE-01", "blocking", "SysDocs", "requested scope has no documents or incoming links")
    # Local module changes still depend on the paired description/index and scope.
    layout_scope = set(requested)
    for path in requested:
        if path.parent == root / "architecture/modules":
            layout_scope.add(root / "files" / path.name)
        elif path.parent == root / "files" and path.name != "README.md":
            layout_scope.add(root / "architecture/modules" / path.name)
            layout_scope.add(root / "files/README.md")
    required_reads = layout_scope | {
        local_target(path, link) for path in requested if path in docs
        for link in links(docs[path][1])
    }
    out_of_scope_issues = []
    for item in read_issues:
        if files is None or project / item["path"] in required_reads:
            issues.append(item)
        else:
            out_of_scope_issues.append(item)
    # An interrupted library still has a layout even when its entry is missing.
    new = any(p in {root / "README.md", root / "PROJECT-MAP.md"} or p.relative_to(root).parts[0] in {"architecture", "files"} for p in docs)
    old = root / "SYSTEM_ROOT.md" in docs and isinstance(docs[root / "SYSTEM_ROOT.md"][0], dict)
    fact_docs = [p for p in docs if p.relative_to(root).parts[0] not in {"VibeCoding", "specs", "decisions"}]
    inventory = "UNINITIALIZED" if not fact_docs else "PARTIAL-INITIALIZED"
    if new:
        layout_issues = []
        for required in REQUIRED:
            if root / required not in docs:
                issue(layout_issues, "SYSDOC-LAYOUT-01", "blocking", "SysDocs/" + required, "required schema 2 navigation missing")
        if old or any(p.relative_to(root).parts[0] == "modules" and not compatibility_page(body) for p, (_, body) in docs.items()):
            issue(layout_issues, "SYSDOC-LAYOUT-02", "blocking", "SysDocs", "mixed legacy and schema 2 bodies require migration repair")
        modules = {p.stem for p in docs if p.parent == root / "architecture/modules"}
        indexes = {p.stem for p in docs if p.parent == root / "files" and p.name != "README.md"}
        for module_id in sorted(modules ^ indexes):
            missing = root / ("files" if module_id in modules else "architecture/modules") / (module_id + ".md")
            issue(layout_issues, "SYSDOC-MAN-01", "blocking", missing.relative_to(project).as_posix(), "module descriptions and file indexes must correspond")
        inventory = "PARTIAL-INITIALIZED" if layout_issues else "INITIALIZED"
        if files is None:
            issues.extend(layout_issues)
            check_navigation(root, docs, issues)
        else:
            issues.extend(item for item in layout_issues if project / item["path"] in layout_scope)
    elif old:
        legacy_status, legacy_issues = validate_legacy(root, docs)
        inventory = "INITIALIZED" if legacy_status == "COMPLETE" else "PARTIAL-INITIALIZED"
        if files is not None:
            _, legacy_issues = validate_legacy(root, docs, requested)
        issues.extend(legacy_issues)
    if inventory == "UNINITIALIZED" and not summaries and files is None:
        issue(issues, "SYSDOC-LAYOUT-01", "warning", "SysDocs", "project documentation is uninitialized; proposals alone do not initialize it")
    if not old or new:
        for path in sorted(selected):
            fm, body = docs[path]
            if path in requested:
                check_metadata(path, root, fm, body, issues)
            check_body(path, root, body, issues, None if path in requested else requested)
        check_coverage(root, docs, selected & requested, issues, files is None)
    if inventory == "INITIALIZED" and (read_issues or any(x["severity"] == "blocking" for x in issues)):
        inventory = "PARTIAL-INITIALIZED"
    status = "FAILED" if any(x["severity"] == "blocking" for x in issues) else "PARTIAL" if issues else "COMPLETE"
    report = {
        "schema": 2, "status": status, "root": root.as_posix(), "inventory": inventory,
        "validation_kind": "structure", "content_verification": "not_performed",
        "scope": {"mode": "affected" if files is not None else "full", "documents": sorted(p.relative_to(project).as_posix() for p in selected), "incoming_links_only": sorted(p.relative_to(project).as_posix() for p in selected - requested)},
        "issues": issues,
        "out_of_scope_issues": out_of_scope_issues,
        "unverified": ["semantic accuracy and completeness of impact candidates", "symbol resolution and full Mermaid parsing", "Markdown reference links and heading anchors", "working-tree evidence contents and freshness"],
    }
    if out_of_scope_issues:
        report["unverified"].append("incoming links could not be checked in unreadable out-of-scope documents: " + ", ".join(item["path"] for item in out_of_scope_issues))
    if summaries:
        report["validation_kind"] = "summary_extraction"
        report["summaries"] = [{"path": p.relative_to(project).as_posix(), "summary": summary(docs[p][1])} for p in sorted(selected) if summary(docs[p][1])]
        report["fallback_required"] = [p.relative_to(project).as_posix() for p in sorted(selected) if not summary(docs[p][1])]
    return redact(report)


def validate(root: Path):
    report = inspect(root)
    return report["status"], report["issues"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--files", nargs="+", help="project-relative affected document paths; includes incoming links")
    parser.add_argument("--summaries", action="store_true", help="extract header summaries and missing-summary fallbacks")
    args = parser.parse_args()
    root = args.root.resolve()
    report = inspect(root, args.files, args.summaries)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] != "FAILED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
