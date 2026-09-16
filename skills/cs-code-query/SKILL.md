---
name: cs-code-query
description: "Answers code questions using an available project knowledge graph and source verification; falls back to source search when no usable index exists. Supports CodeGraph, Understand-Anything, and Graphify. / 使用已有项目知识库定位并核实源码；无可用索引时直接源码检索，支持三种后端及显式创建、更新操作。"
---

# Code Query with Source Verification

Use an existing knowledge graph to locate evidence, then verify implementation claims
against the target project's source. A graph is neither a specification nor proof that
SysDocs matches the implementation. Ordinary queries do not require installing,
creating, refreshing, or repairing a knowledge base.

## Phase 1: Recognize Intent and Project

Resolve the target project root (including the actual worktree), question, and operation.
General questions default to **query**. Only explicit graph creation or already-authorized
setup routes to **create**; explicit refresh or an already-authorized maintenance task
routes to **update**. Selecting a backend alone does not authorize creation/installation.
A source-editing request alone does not authorize refresh; an owning workflow may
explicitly include it in the task scope.

Accept `--kb CG|US|GR`, full backend names, or unambiguous standalone selectors:

| Selector | Backend | Default project data |
|---|---|---|
| CG / codegraph | CodeGraph | `.codegraph/` |
| US / understand-anything | Understand-Anything | `.understand-anything/knowledge-graph.json` |
| GR / graphify | Graphify | `graphify-out/graph.json` |

Honor an explicitly configured index location. Some Understand versions also support
`.ua/`; consult the installed skill before resolving this alternative. Never use a
different checkout's graph without identifying that source and its coverage gap.

## Phase 2: Check Three Independent States

For each relevant backend, record these independently:

1. **Existence:** actual graph/database artifacts at the resolved project location,
   not merely an empty directory or tool source checkout.
2. **Queryability:** discover callable MCP tools or the installed CLI/skill and its
   actual schema/help, then perform a bounded query for a known project symbol/path.
   Readable supported graph JSON can serve as a direct query interface. Distinguish
   successful queries with no matching results from failed calls or unreadable data.
3. **Coverage and freshness:** compare indexed files/symbols and available metadata
   against this task's source scope, committed differences, staged changes, unstaged
   changes, and untracked files. A recent directory timestamp, equal HEAD, available
   CLI, or watcher capability proves none of these by itself. Missing provenance or
   unsupported languages mean **unknown/partial coverage**, not fresh.

Discover executables with `Get-Command codegraph, graphify -ErrorAction SilentlyContinue`
in PowerShell, or `command -v` in a POSIX shell. Read installed help and the selected
backend's `query.md` before invoking version-sensitive commands. MCP availability is
independent of CLI availability: discover actual tools instead of assuming a bridge
connected. A health probe must not create a missing index. For strict read-only work,
check for query side effects; read existing graph data or fall back to source if the
backend would write logs, update indexes, or start refresh.

## Phase 3: Select Backend and Route

- **Explicit backend:** use only that backend for graph results. If missing,
  unqueryable, or incomplete, report the limitation and continue source verification;
  do not silently switch backends or bootstrap the selected one.
- **No selector:** prefer an existing queryable index. Among usable indexes, prefer
  CodeGraph, then Understand-Anything, then Graphify; select only after checking relevant
  coverage. A stale/partial index can supply labeled candidates, never a completeness
  guarantee. If another backend is chosen, identify it and why.
- **No usable knowledge base:** proceed immediately with `rg --files`, `rg`, and
  targeted source reads (or available equivalents). Do not interrupt an ordinary
  query to ask which tool to install or demand graph creation.
- **Explicit multi-backend query:** query each requested available backend, label
  sources independently, retain single-backend discoveries, and report unavailable
  backends and disagreements. Do not create missing ones.
- **Explicit create/update:** load only the selected operation file. For create
  without a selection, reuse an already-configured backend or default to available
  CodeGraph; if no creation interface is available, report the concrete prerequisite.
  For update, require an existing index; do not turn maintenance into creation.

Resolve these paths relative to this installed skill directory, not the caller's cwd:
`codegraph/`, `understand-anything/`, or `graphify/`, each with
`create.md`, `query.md`, and `update.md`. Do not substitute `/understand-chat` for
CodeGraph or Graphify: that skill reads Understand-Anything's own graph.

## Phase 4: Verify Source and Document Candidates

Treat returned locations/relationships as candidates. Check relevant current source
and configuration before stating implementation facts. Verify source location and
snapshot even when a backend includes source excerpts. Distinguish inferred
relationships from observed ones; empty graph results do not prove no callers or impact.

For SysDocs design or maintenance, follow
`../../references/sysdocs-design-context.md` and
`../../references/sysdocs-system.md` for the owning workflow:

1. Read applicable specifications and accepted decisions as requirements, separately
   from current implementation facts.
2. Form candidates from graph impact results **and** SysDocs retrieval summaries,
   key class/structure names with one-sentence responsibilities, business terms,
   source diffs/references, and document inbound links. Take their **union**, never
   only their intersection. Preserve where each candidate came from.
3. Investigate unmatched candidates: renamed/new symbols absent from the graph,
   symbols missing from summaries, documents referring to removed symbols, and
   prose-only cross-module relations. Read legacy/external documents without a
   summary through their text or canonical links; do not exclude them.
4. Reconcile disagreements using source. Matching graph and summary claims may both
   be stale. For transaction, permission, data ownership, module split or responsibility
   boundary changes, inspect relevant flow bodies; if scope cannot be narrowed reliably,
   expand to all flow documents and report remaining gaps.

A query supplies evidence; it does not authorize rewriting specifications, historical
ADRs, or documents during a read-only review. Graph refresh never counts as document
content verification or completion of a SysDocs synchronization gate.

## Verification and Verdict

Verify selected backend/project path, successful interface use (or labeled source
fallback), task-specific coverage, and current source evidence. For create/update,
perform a real post-operation query and check changed, new, renamed, and removed
items in scope; directory existence or mtime is insufficient.

- **COMPLETE:** requested operation and evidence checks completed for the stated scope.
  An ordinary question can be COMPLETE via source fallback; identify that source and
  do not claim it was answered by a graph.
- **PARTIAL:** useful evidence exists but requested graph coverage, backend access, or
  verification remains incomplete. Explicit graph-only/multi-backend requests remain
  PARTIAL if source fallback cannot fulfill their requested graph operation.
- **FAILED:** requested operation could not complete; identify the failure and what
  source work was still possible.

Report actual backend/interface and index location, source/worktree scope, coverage
gaps, and relevant source references. Keep routine reports short. Do not claim graph
freshness, exhaustive impact discovery, or documentation correctness without evidence.
