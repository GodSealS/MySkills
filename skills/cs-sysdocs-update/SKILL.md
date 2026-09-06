---
name: cs-sysdocs-update
description: "The single maintenance entry for a SysDocs documentation library: repair (partial-initialized), incremental (initialized, refresh drifted modules + merge vibe docs), and rebuild-boundaries (boundary review gate). Runs schema migration, symbol reverse-lookup, drift refresh, vibe four-condition merge, and the shared validator. Use for any update after the project is PARTIAL-INITIALIZED or INITIALIZED. Never calls back into init. / SysDocs 文档库的唯一维护入口：repair（部分初始化）、incremental（已初始化，刷新漂移模块 + 并入 vibe）、rebuild-boundaries（边界复审门控）。执行 schema 迁移、符号反查、漂移刷新、vibe 四条件并入与统一 validator。用于项目处于「部分初始化」或「已初始化」之后的任何更新。绝不回调 init。"
---

# SysDocs Update — The Only Maintenance Entry

## Overview

The single maintenance entry for a SysDocs library once the project is **PARTIAL-INITIALIZED** or **INITIALIZED**. Three internal modes:

| mode | when |
|---|---|
| `repair` | PARTIAL-INITIALIZED (missing files, manifest mismatch, interrupted init) |
| `incremental` | INITIALIZED — refresh drifted modules by git range + merge vibe docs |
| `rebuild-boundaries` | boundary review gate hit (kb_bootstrap pending + KB ready, or module-count deviation) |

Read the shared convention first: `../../references/sysdocs-system.md`.

## When to Use

- Inventory = PARTIAL-INITIALIZED → `repair`.
- Inventory = INITIALIZED → boundary gate first, then `incremental`.
- Boundary rebuild triggers (see gate below).

**When NOT to use:**

- Inventory = UNINITIALIZED → **stop**, report the state and require `cs-sysdocs-init` first. Never call back into init.

## Inputs (normalize first)

Normalize into: `operation`, `project_root`, `mode`, `source_scope`, `yes`, `--kb`, `--files`. Record normalized inputs and confirm/reject results into the run report.

## Invocation examples

```text
cs-sysdocs-update --project-root . --mode incremental --source-scope committed
cs-sysdocs-update --project-root . --mode repair --files src/order/service.ts --yes
cs-sysdocs-update --project-root . --mode rebuild-boundaries --kb codegraph --yes
```

If `Task` is unavailable, perform the local checks without fan-out and record
`architect_review: unavailable`; unresolved boundary or symbol uncertainty must
remain `PARTIAL`. If interactive confirmation is unavailable, `--yes` is required.

## Write Authorization (allowlist)

Only modify `SysDocs/**` under the current project root. `repair`, `incremental`, `rebuild-boundaries` are each limited to their corresponding manifest / module docs / VibeCoding files; never touch source code. Resolve real paths (incl. symlinks) before every write and confirm they stay inside the allowlist; failure = immediate reject. `Task` fan-out briefs are read-only; the subagent never writes the target project.

## Process

### Phase 1 — Determine state

UNINITIALIZED → stop, require init. PARTIAL-INITIALIZED → `repair`. INITIALIZED → run the boundary gate (§below), then `incremental`.

### Phase 2 — Schema gate

Run before touching content. `schema` < template `schema` → migrate frontmatter/section headers via registered one-way migration steps, then incrementally rewrite. `schema` > template → read-only FAIL, never downgrade/overwrite/delete unknown fields, verdict `FAILED`. Migration failure → keep the original file, save diagnostics; re-running the same migration must not add diff. Unknown frontmatter fields are preserved by default.

### Phase 3 — Update knowledge base

If the chosen KB is READY and its update capability is available, call the matching `cs-code-query` update sub-process; do not guide install/create when not ready. Update failure → keep old docs, degrade to source, verdict `PARTIAL`.

### Phase 4 — Locate affected modules

First verify `generated_from` SHA exists and is reachable in the repo, then run `git diff --name-status -M <generated_from>..HEAD` (includes rename/delete) and combine with KB query. Separately check staged/unstaged/untracked working-tree changes — by default only report, do not fold into refresh. Extract the symbol list and reverse-lookup in **batch** (§7.1 of the convention).

### Phase 5 — Rewrite

Update only drifted module docs + affected SYSTEM_ROOT sections. **Skip `<!-- human:start -->` blocks.** Refresh `generated_from` / `updated`.

### Phase 6 — Filter + merge VibeCoding

Merge a vibe doc only when **all four conditions** hold (see below). Otherwise: still-advanceable → keep `draft` + record missing conditions; target module/source baseline changed and needs re-eval → `stale`; only explicit user abandonment / replaced / explicitly requested → `archived`, and **keep the file, never delete**.

### Phase 7 — Ambiguity self-check + verdict

Run the shared validator (convention §11). Write sanitized `.meta/reports/<run-id>.json`. Verdict COMPLETE/PARTIAL/FAILED. On drift, set affected docs `stale` first, restore `active` only after links/symbols/Mermaid revalidate.

## Git Snapshot & Working-Tree Rules

- Clean repo → use `HEAD` snapshot, `source_scope: committed`, reachable `generated_from` SHA.
- With staged/unstaged/untracked changes: interactive mode must choose `committed` / `committed+working-tree` / cancel; non-interactive must pass `--source-scope`.
- `committed+working-tree` still records the generating `HEAD`; later updates that find related source still uncommitted must not claim content is synced — return `PARTIAL` or require a file list.
- Untracked files participate only when explicitly included in working-tree scope or via a file list; otherwise report only.
- `generated_from` missing/unreachable/shallow-clone/no-git and no file list → do not guess affected modules; structural check only + `PARTIAL`.
- After user confirms and before actually scanning, re-read `HEAD` + working-tree state; baseline changed → stop writing this round, `PARTIAL`, do not overwrite newer content.

## Vibe Merge — Four Conditions (all must hold)

1. The vibe doc was architect-reviewed with no unhandled **target-level** defects (review conclusion is in the doc).
2. Code landed, **or** user explicitly confirmed "docs only, code later". `implementation.status: code-landed | docs-only-confirmed` with evidence (git diff / file list / user confirmation).
3. No conflict with the target module's MUST / MUST NOT.
4. `targets[].module_id` uniquely points to a module, using stable section IDs.

All targets must satisfy all four or the **whole** vibe stays `draft`/`stale` — never silently partial-merge. On success: keep the original, write `merge.status: merged` + target section + `merged_at` + merge run, then set the original `archived`.

## Boundary Review Gate

Checked at the start of every update. When hit, run update's own `rebuild-boundaries` (never init):

1. **Primary**: `SYSTEM_ROOT.md` `kb_bootstrap: pending` **and** current KB READY → rebuild once, then set `kb_bootstrap: done` (**latched** — never re-trigger every update).
2. **Secondary**: module count vs excluded-dir/package count deviation **> 30% and absolute ≥ 3** → **prompt the user**, default no auto-rebuild (rebuild is destructive; only rebuild on confirmation).

Rebuild is transactional: dry-run first (old→new module mapping, file moves, human-block migration report). On slug conflict, unclosed/duplicate human markers, or unmappable files → do not overwrite; verdict `FAILED`/`PARTIAL` → `repair`. Human blocks move with their file, only paired and non-nested.

Rebuild commit rules: (1) auto `kb_bootstrap` review also dry-runs first; split/merge/delete/human-block migration requires explicit confirmation (interactive `yes`/`approve`, non-interactive `--yes`); (2) generate full result in a temp dir, validate manifest/links/symbols/Mermaid, then atomic replace, with a recoverable backup or reverse patch of the old `SysDocs/`; (3) any validation/commit failure → keep old docs, keep temp diagnostics for next `repair`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Not initialized, I'll just init" | update never calls init. Report the state and require `cs-sysdocs-init`. |
| "Content looks old, I'll rewrite it" | Drift detection is `git diff <generated_from>..HEAD`, not eyeballing or mtime. |
| "Multiple hits, I'll pick one" | Ambiguous symbol = `PARTIAL`, list candidates for the user; never silently choose. |
| "I'll auto-merge that vibe" | Four conditions, all targets. Otherwise `draft`/`stale`, never partial-merge. |
| "kb_bootstrap is pending, rebuild again" | It's latched — one rebuild, then `done`. |
| "Module count is off, rebuild now" | Deviation only prompts; default no destructive rebuild without confirmation. |

## Red Flags

- Calling back into `cs-sysdocs-init`
- Overwriting a `<!-- human:start/end -->` block
- Deleting an unmatched module doc instead of keeping it `stale` + orphan report
- Skipping the schema gate or the dry-run before rebuild
- Faking `COMPLETE` with unverified symbols still pending
- Writing outside the resolved-path allowlist

## Verification

- [ ] State determined correctly; UNINITIALIZED stopped with init requirement
- [ ] Schema gate applied; migration idempotent; future schema read-only-failed
- [ ] Drift located by reachable SHA + `git diff --name-status -M`; working-tree handled per source_scope
- [ ] Symbol reverse-lookup batched; ghosts repaired, ambiguity = `PARTIAL`
- [ ] Human blocks preserved; `owned_by: mixed` respected
- [ ] Vibe merged only on all four conditions; otherwise draft/stale/archived with file kept
- [ ] `kb_bootstrap` latched; deviation prompted, not auto-rebuilt
- [ ] Rebuild was dry-run + temp-dir + atomic, with backup/reverse patch
- [ ] Shared validator ran; sanitized report written; verdict recorded

## Interaction with Other Skills

- `cs-sysdocs-init`: upstream — only runs when UNINITIALIZED; never called from here.
- `cs-vibe-coding`: upstream — produces the vibe docs this skill merges.
- `cs-code-query`: KB query/update base; never its Phase 3 bootstrap; never `findReferences` as a KB API.
- `cs-architect` (agent): short read-only briefs for boundary validation / design review.
- `cs-incremental` / `cs-git-workflow`: they remind the user to run this before slice/commit.

## See Also

- `../../references/sysdocs-system.md` — shared convention (schema migration, drift, validator, report)
- `../../references/sysdocs-module-template.md` — module doc shape (rewrite target)
- `../../references/sysdocs-vibe-template.md` — vibe doc shape (merge source)
