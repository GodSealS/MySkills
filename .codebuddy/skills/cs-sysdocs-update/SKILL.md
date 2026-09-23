---
name: cs-sysdocs-update
description: "The only SysDocs maintenance entry: repair incomplete libraries, update affected descriptions and references, explicitly migrate legacy layouts, or refresh an explicitly requested full scope. Cross-check documentation summaries, knowledge-base candidates and source evidence while preserving human text and authoritative requirements. / SysDocs 唯一维护入口：修复、按影响同步、显式旧布局迁移或获准的全量刷新；交叉核查摘要、知识库候选与源码，保护人工内容及规范权威位置。"
argument-hint: "[project_root] [--mode repair|incremental|migrate|rebuild-boundaries|full-refresh] [--source-scope committed|committed+working-tree|unversioned] [--kb <backend>] [--yes] [--files <source-files>]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, ListDir
agent: cs-architect
---

# SysDocs Update — The Only Maintenance Entry

## Overview

Maintain documentation within the actual change's impact, including related pages and incoming links. Read [the shared protocol](../../references/sysdocs-system.md) and [design-context protocol](../../references/sysdocs-design-context.md) first. They define schema, dual-layout inventory, evidence and protection rules.

| Mode | Scope |
|---|---|
| `repair` | Restore necessary missing or interrupted documentation without silently moving the library |
| `incremental` | Refresh affected descriptions, file ownership, summaries, navigation and references |
| `migrate` | Explicitly authorized schema 1 to schema 2 directory/content migration |
| `rebuild-boundaries` | Authorized restructuring justified by actual responsibility or dependency changes |
| `full-refresh` | Explicitly requested full-library review and refresh |

A KB becoming usable after `kb_bootstrap: pending`, or a module-count heuristic, never automatically triggers migration or a boundary rebuild. Ordinary work has no full-library baseline or refresh prerequisite.

## Inputs and Authorization

Normalize `operation`, `project_root`, `mode`, `source_scope`, `yes`, `--kb`, and `--files`. Here `--files` identifies source files to inspect; the validator's `--files` option instead takes affected **document** paths relative to the project root. Derive both lists from evidence rather than conflating them.

Reuse the user's existing authorization for necessary reversible documentation synchronization. `--yes` supports automation; absence of this flag does not revoke already granted authorization. A new directory migration, deletion, changed business constraint, or unresolved target conflict outside the approved scope requires a concrete user decision. Complete a read-only mapping/preview before requesting any missing migration authorization.

Only write `SysDocs/**` within the resolved project root. Check symlinks and real paths before writes. Never alter source or KB directories. External authoritative specs/ADRs remain at their original location; link them and report needed changes for the enclosing authorized task to handle. Do not bypass this skill's allowlist to edit them.

Verification evidence should reuse the enclosing task artifact. If that artifact is outside this skill's write allowlist, return the results to the host for authorized recording; do not widen the allowlist or create a duplicate report merely for routing.

## Process

### 1. Inventory and schema gate

Recognize both legacy `SYSTEM_ROOT.md` / `modules/` and schema 2 `README.md` / `architecture/` / `files/`. Existing incomplete or interrupted work uses repair. If only proposals/reports exist, state is **UNINITIALIZED**: maintain a proposal through `cs-vibe-coding`, or report that a requested full project library needs `cs-sysdocs-init`. Do not initiate it automatically or block unrelated development.

Read all relevant metadata before mutation. Supported schema 1 pages can receive local maintenance in their existing layout; old schema alone never authorizes migration. Fresh full generation uses schema 2. Unknown future schema is read-only `FAILED`, with no downgrade or field deletion. Mixed interrupted migrations resume from their mapping/recovery record; do not choose an entry by filename existence alone.

### 2. Fix source scope and evidence

Establish the actual change range and verify any generating SHA is reachable before using `git diff --name-status -M <baseline>..HEAD`. Include rename/delete, staged, unstaged and explicitly included untracked changes according to the task's scope. A file list can support source re-verification when Git history is unavailable; do not infer historical changes from mtime.

- `committed`: read the selected commit contents, not a dirty working copy mislabeled as that commit.
- `committed+working-tree`: record the base SHA and included files/review diff in existing task evidence; required `evidence` metadata points to that project-relative file, optionally with an anchor. The base is not the complete snapshot or the future commit SHA.
- `unversioned`: declare explicit source paths and limitations; omit invented Git metadata.
- Missing/unreachable baseline or lost working evidence: reverify explicit source scope. Necessary unresolved facts yield `PARTIAL`; unavailable history alone need not prevent complete present-state verification.

Record the source state before review and recheck HEAD plus relevant staged/unstaged/untracked content before landing. If relevant content changed, invalidate affected evidence and reverify; do not overwrite newer user edits. Do not introduce a fingerprint database or a second full-source snapshot.

### 3. Discover the affected document scope

First describe the **semantic change**, such as responsibility movement, ownership, transaction boundaries, contracts or failure handling. A path-only file list is not an impact analysis.

1. Query available KBs through `cs-code-query`, recording actual backend, project/index, coverage and revision. Never install/create/refresh an index implicitly in this documentation-only write scope. Index refresh, when separately authorized, is a different action and cannot replace content verification.
2. Extract documentation summaries with the shared validator's `--summaries` mode. Use paths and summaries to select candidates before loading their bodies. Search business terms, old/new symbols, module names and moved paths across the library and relevant authoritative linked material.
3. Take the **union** of KB and documentation candidates; source diffs/reference searches add new or renamed symbols missing from the index. Investigate each meaningful mismatch: missing summary, stale graph, missing documentation, or a supported no-impact explanation. Record the outcome.
4. Read relevant bodies and incoming links. Missing summaries on legacy pages, historical ADRs or external sources require body/link fallback; they do not exclude the source. No summary match is not proof of no impact.
5. For module split/merge, responsibility, dependency, transaction, permission, data ownership or recovery changes, read all related business-flow explanations and constraints even if their summaries do not match. If scope cannot be narrowed reliably, expand to **all flow explanations**, including flows embedded in module pages and external authoritative docs. This expands reading, not indiscriminate rewriting.

Verify key claims against source even when the KB and summaries agree: both can be stale. A requested KB failure uses source fallback and reports the gap, not silent substitution or automatic `PARTIAL`. Necessary unresolved impact remains explicitly unverified.

Keep a short impact record in the existing task/review artifact: change, semantic effect, candidate sources and differences, affected descriptions/requirements/decisions, expanded checks and evidence gaps. A substantiated no-impact result requires a concrete reason, not an empty generated report.

### 4. Update the necessary pages

Maintain `SysDocs/PROJECT-MAP.md` under the shared protocol's root project-map contract and [template](../../references/sysdocs-project-map-template.md). In schema 2 repair, supply a missing map and README navigation; migration/full-refresh also require it. For incremental work, assess architecture, execution paths, module/interface dependencies and project workflow changes, then update affected views and their evidence alongside the detailed pages. An unrelated inherited absence does not force full-library repair; schema 1 stays under its legacy contract until explicit migration.

Update affected module/flow descriptions, file responsibilities, summary text, navigation and incoming references in the existing supported layout. Use schema 2 templates for schema 2 pages. The summary names only key entry/major-responsibility classes or structures with a one-sentence responsibility each, real alternatives where classes are absent, and important cross-module boundaries. Complete file coverage belongs to `files/`, not a second symbol list.

Preserve unknown metadata, manually owned material and all `<!-- human:start -->` / `<!-- human:end -->` contents. Unpaired, nested or ambiguous human markers prevent an unsafe rewrite. Keep unclassifiable original text and report it. Preserve the body of accepted ADRs; changed decisions need a new decision and supersession link. Source behavior does not automatically replace accepted requirements.

Refresh baseline fields only for reverified pages. Unverified changed descriptions remain `stale` when using status metadata. Unrelated historical defects are reported separately and do not block a supported local deliverable. A defect introduced by this change or needed to establish its safety/completeness does block its completion.

### 5. Integrate eligible VibeCoding proposals

All intended targets must meet the shared integration conditions:

1. Architect review has no unresolved blocking target-level findings; evidence-dependent findings remain provisional until verified.
2. Implementation evidence supports the destination: verified landed code may update current architecture/files; `docs-only-confirmed` proposals may update authorized target specs/decisions or proposal links, **never describe future architecture as implemented**.
3. There is no unresolved conflict with applicable accepted requirements or constraints.
4. Each destination is uniquely resolved to its authoritative page/section in the active layout; a module target uses the stable `module_id` when applicable.

If one intended target is unresolved, retain the proposal as draft/stale with `merge.status: pending`. Record which implementation facts are already verified and synchronized, but never present partial implementation as a fully merged proposal. On a complete integration, preserve the proposal, record destinations, evidence, merge run/date and archived status. A docs-only integration remains explicitly unimplemented. Missing library/module targets can stay in the proposal until meaningful destinations exist; they never force full initialization. Explicit abandonment/supersession may archive a proposal without calling it merged. Never delete the original.

### 6. Explicit migration or boundary rebuild

Do this only when the approved task includes it. Read-only assessment first: map every legacy page/section to its destination, stable module IDs, human text, unknown fields, external authority locations and incoming links. Preserve VibeCoding files and historical `.meta/` reports unchanged unless their own live content needs an authorized update.

Use the shared migration mapping: root overview/navigation to README; module structure to `architecture/modules/`; complete file responsibilities to `files/`; useful cross-module flows to `architecture/flows/`. Separate confirmed constraints and reasons from implementation facts. Preserve unresolved original sections instead of inventing Accepted decisions.

Protect current user edits with a recoverable backup or reverse patch that includes uncommitted content. Stage the result within the write allowlist, validate full structure/coverage, compare preserved human text and verify important content. Unmapped pages, slug collisions or unsafe human markers remain intact with a blocking/pending mapping; do not delete them to pass checks.

Land a validated result with a recovery record for multi-file replacement; on interruption restore or resume without losing originals. Keep the old entry as a link-only compatibility page when useful; avoid maintaining duplicate bodies. Repeating a finished migration is idempotent. Failure retains original files, staging diagnostics and recovery information. Unknown schema remains read-only even in migration mode.

### 7. Verify and report

Run shared structural validation over affected documents and their incoming links. Initialization-equivalent full refresh and migration require full-library structure and source-coverage checks. Explicitly distinguish full-library results from affected-scope results.

Separately verify summary-body agreement, important symbols/responsibilities, dependency/flow descriptions, source versions, candidate discrepancies and high-risk expanded reading. Behavior or contract checks establish requirement compliance. Report actual Mermaid/symbol methods and unsupported checks; a static scan is not semantic validation.

Record declared scope, verified items, failed checks and uncovered items in existing sanitized task/review evidence. Reuse that artifact; a separate `.meta/reports/` file is optional when persistence needs it, not mandatory for every update. `COMPLETE` refers only to the stated verified scope; unresolved necessary facts mean `PARTIAL`, unsafe schema/path operations mean `FAILED`. Only revalidated pages may return to `active`. Reuse still-valid slice evidence; recheck conclusions touched by subsequent changes.

## Verification

- [ ] Dual layout/state and schema checked; no implicit initialization, migration or KB-triggered rebuild.
- [ ] Existing authorization reused; any additional migration scope was made concrete before seeking approval.
- [ ] Source scope reflects commit/working content; relevant changes invalidate affected checks.
- [ ] KB, summaries and source candidates are combined; mismatches and missing-summary fallbacks resolved or reported.
- [ ] High-risk changes inspect related flow bodies; unclear scope expands to all flow explanations.
- [ ] Affected descriptions, file ownership, summaries and incoming links are synchronized; unrelated old gaps remain distinct.
- [ ] Applicable PROJECT-MAP views and README navigation match current module/flow/workflow evidence; missing-map repair and unimplemented views follow the shared contract.
- [ ] Human text, unknown fields, historical ADR bodies and authoritative locations are preserved.
- [ ] Proposal integration satisfies all conditions; future designs remain explicitly unimplemented.
- [ ] Migration/rebuild, if authorized, is staged, recoverable, idempotent and preserves unmapped originals.
- [ ] Structure and content evidence are separate; verdict states its scope and outstanding gaps.

## See Also

- [Shared protocol](../../references/sysdocs-system.md)
- [Design context](../../references/sysdocs-design-context.md)
- [Module template](../../references/sysdocs-module-template.md)
- [Vibe template](../../references/sysdocs-vibe-template.md)
