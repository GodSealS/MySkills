---
name: cs-sysdocs-init
description: "Generates the SysDocs system documentation set (SYSTEM_ROOT.md + one module doc per module) for a target project in one pass. Use only when the three-state inventory says the project is UNINITIALIZED — no SysDocs/ dir, empty, only VibeCoding/, or no valid SYSTEM_ROOT.md/module docs yet. Never runs re-init or repairs; that is cs-sysdocs-update's job. / 一次性全量生成项目 SysDocs 系统文档（SYSTEM_ROOT.md + 每个模块一份模块文档）。仅当三态清单判定项目为「未初始化」时使用——无 SysDocs/ 目录、为空、只有 VibeCoding/、或尚无有效 SYSTEM_ROOT.md/模块文档。绝不执行 re-init 或 repair，那是 cs-sysdocs-update 的职责。"
argument-hint: "[project_root] [--type code|spec] [--source-roots <dirs>] [--kb <backend>] [--source-scope committed|committed+working-tree|unversioned] [--yes]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, ListDir
agent: cs-architect
---

# SysDocs Init — One-Pass Full Generation

## Overview

Generate the **SysDocs** system documentation set — `SYSTEM_ROOT.md` (the single overview entry point) plus one module doc per identified module — for a target project. This is the **one-time, full-generation** entry point. It runs **only** when the three-state inventory (§2 of the shared convention) says the project is **UNINITIALIZED**. Re-init and boundary rebuild live in `cs-sysdocs-update`, never here.

Read the shared convention first: `../../references/sysdocs-system.md`, then the three templates `sysdocs-overview-template.md`, `sysdocs-module-template.md`, `sysdocs-vibe-template.md`.

## When to Use

- Inventory state = **UNINITIALIZED** (no `SysDocs/`, empty, only `VibeCoding/`, or no valid `SYSTEM_ROOT.md` / module docs).
- A code project that has never been documented, OR a spec-only project (just landed from `cs-spec-driven`) that needs the skeleton.

**When NOT to use:**

- **PARTIAL-INITIALIZED** → stop; hand to `cs-sysdocs-update` mode=`repair`.
- **INITIALIZED** → stop; hand to `cs-sysdocs-update` incremental.
- Boundary rebuild / re-init → `cs-sysdocs-update` mode=`rebuild-boundaries`, never init.

## Inputs (normalize first)

Normalize all arguments into one object before doing anything: `operation`, `project_root`, `mode`, `source_scope`, `yes`, plus `--type`, `--source-roots`, `--kb`, and the file list when no git. Record the normalized inputs and every confirm/reject result into the run report — do not rely on natural-language dialogue alone.

- `project_root`: explicit workspace-relative dir; default = current workspace root. Never search up to a parent or down into a child automatically.
- `--type code|spec`: override project-type detection only. Cannot override project_root, the exclusion table, path allowlist, or sensitive-data rules.
- `--source-roots <dirs>`: explicit source dirs/packages.
- `--kb <backend>`: force codegraph / understand-anything / graphify.
- `--source-scope committed|committed+working-tree|unversioned`: default `committed`.
- `--yes`: non-interactive confirmation. **Without `--yes`, do not auto-continue** past the module-list preview.

## Invocation examples

```text
cs-sysdocs-init --project-root . --type code --source-roots src --kb none --yes
cs-sysdocs-init --project-root ../demo --type spec --source-scope unversioned --yes
```

On hosts without `Task`, continue boundary identification with source tools but
record `architect_review: unavailable`, use `confidence: low`/`PARTIAL`, and never
claim high-confidence module boundaries. Hosts without interactive confirmation
must require `--yes`; otherwise stop before writing.

## Write Authorization (allowlist)

Tool declaration ≠ write authorization. This skill may only create/modify `SysDocs/**` under the current project root:

- Never write source code, KB directories, the skill pack, or paths outside project root.
- Before every `Write`/`Edit`/`Bash` write, resolve the real path (including symlinks) and confirm it stays inside the allowlist; a path check failure is an immediate reject — no fallback path.
- `Bash` is only for non-destructive probing, temp files, and atomic rename; never recursive delete, overwrite outside the allowlist, source-mutation commands, or installing dependencies.
- `Task` fan-out briefs to `cs-architect` are **read-only**; the subagent must not write the target project. All fan-out output is sanitized and validated by this skill before this skill lands it.

## Process

### Phase 1 — Survey the project

Identify language / runtime / config format / directory structure (feeds SYSTEM_ROOT §4–§7). Apply the exclusion table (§9 of the convention): `node_modules/`, `vendor/`, `dist/`, `build/`, `.git/`, `generated/`, `*.g.cs`, protobuf/openapi generated dirs, wide frontend buckets (`src/components/`, `src/assets/`, `src/styles/`), pure test/resource dirs, and sensitive sources (`.env*`, keys/certs, credential dirs, logs, dumps).

Classify project type using the **evidence matrix**, never a single extension:

- **Code evidence**: ≥1 source file/package not filtered by the exclusion table, with an identifiable language and entry point / export symbols / parseable syntax. README, config, test data, resources, and generated artifacts alone are NOT code evidence.
- **Spec evidence**: `SPEC.md`, `spec/`, `design/`, or an explicitly user-specified spec file whose content is readable.
- Code only → full init. Spec only (no code) → skeleton (`SYSTEM_ROOT.md` §0–§3 + empty module manifest, empty `modules/`; module bodies later via update repair). Neither → **stop**, ask for project type or `source_roots`. Both → treat as code project and list both evidence kinds in the preview.
- Record evidence, exclusions, overrides, and the final choice into the init report for later repair/audit.

### Phase 2 — Probe knowledge base (never install)

Run only `cs-code-query` Phase 2 (directory/CLI status probe). Do **not** load its Phase 3 bootstrap/create wizard. Select a READY backend by the capability matrix (§5.2.1 of the plan). No usable backend → say **one line** "no KB, low-confidence degraded generation this round", write `kb: none`, `confidence: low`, `kb_bootstrap: pending`, and fall back to Glob/Grep/Read.

### Phase 3 — Identify module boundaries (strategy C + exclusion table)

Directory/package as skeleton; AI + KB add business semantics, split/merge wide buckets, and write the rationale. May fan-out `cs-architect` to validate the **module list table** (short brief: slug / dir / one-line responsibility / split-merge rationale — never module bodies).

### Phase 4 — Module list preview (confirmation gate)

Present the module list (id / path / description / source_roots / split-merge rationale) for confirmation. Interactive mode: only an explicit `yes`/`approve` continues to write; reject, timeout, or no reply → stop, landed checkpoints stay `draft`. Non-interactive: must pass `--yes`; record input source, assumptions, and risk into the result.

### Phase 5 — Generate SYSTEM_ROOT.md

Write `SYSTEM_ROOT.md` from the overview template: frontmatter (with `modules` manifest + `kb_bootstrap`), `generated_from` = current HEAD (or omit + note in body when no git), §0–§7.

### Phase 6 — Generate each module doc (checkpointed)

Write each module doc from the module template; land each one and update SYSTEM_ROOT §3 after each. Interrupt is allowed — after an interrupt the inventory is PARTIAL-INITIALIZED and `cs-sysdocs-update` repair resumes. Verify class references exist via the reverse-lookup order (§7.1 of the convention).

### Phase 7 — Ambiguity self-check + verdict

Run the **shared validator** (convention §11) before any `active` status or atomic replace. Write the sanitized `.meta/reports/<run-id>.json` (convention §12). Verdict: `COMPLETE` / `PARTIAL` / `FAILED`. Only set `active` after all required docs + self-check pass; an interrupt leaves `draft`.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The dir exists, so it's initialized" | The gate is the three-state inventory, not dir existence. A dir with only VibeCoding/ is UNINITIALIZED. |
| "I can just re-run init to fix gaps" | init is one-time. Gaps = PARTIAL-INITIALIZED = update repair. |
| "No KB, so I'll install one" | Never install/bootstrap here. Degrade with Glob/Grep/Read and `kb_bootstrap: pending`. |
| "I'll auto-proceed without asking" | The module-list preview is a hard gate. No `--yes` → stop. |
| "I'll document every class" | Class references are tiered; hard cap ~400 lines / 15 detailed classes. |

## Red Flags

- Writing anywhere outside `SysDocs/**` under project root
- Loading `cs-code-query` Phase 3 bootstrap/create, or calling `findReferences`/`workspaceSymbol` as if the KB skill provides them
- Marking docs `active` before the validator passes
- Continuing past the module-list preview without explicit confirmation / `--yes`
- Guessing project type instead of applying the evidence matrix
- Leaving a half-written file instead of temp-file + atomic replace

## Verification

- [ ] Inventory state was UNINITIALIZED before starting
- [ ] Project type decided by evidence matrix; evidence/exclusions/overrides recorded in the report
- [ ] KB probed, not installed; `kb` / `confidence` / `kb_bootstrap` set per the capability matrix
- [ ] Module list previewed and explicitly confirmed (or `--yes` recorded with source/assumptions/risk)
- [ ] `SYSTEM_ROOT.md` has full frontmatter + `modules` manifest + §0–§7
- [ ] Every module doc follows the module template, with tiered class references and self-check
- [ ] All Write/Edit/Bash ops stayed inside the resolved-path allowlist
- [ ] Shared validator ran; sanitized `.meta/reports/<run-id>.json` written
- [ ] Verdict COMPLETE/PARTIAL/FAILED recorded; `active` only after all checks pass

## Interaction with Other Skills

- `cs-code-query`: KB probe / query base — Phase 2 detection only, never Phase 3 bootstrap.
- `cs-architect` (agent): boundary list validation fan-out (short, read-only brief).
- `cs-sysdocs-update`: downstream — repair (partial) / incremental (initialized) / rebuild-boundaries.
- `cs-vibe-coding`: downstream — requires PARTIAL-INITIALIZED or INITIALIZED first.
- `cs-spec-driven`: upstream — spec-only project lands here to produce the skeleton.

## See Also

- `../../references/sysdocs-system.md` — shared convention (inventory, frontmatter, rules, validator, report schema)
- `../../references/sysdocs-overview-template.md` — SYSTEM_ROOT.md shape
- `../../references/sysdocs-module-template.md` — module doc shape
