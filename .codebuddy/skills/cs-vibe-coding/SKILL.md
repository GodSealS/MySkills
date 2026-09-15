---
name: cs-vibe-coding
description: "Captures a fragmentary change as a pre-design VibeCoding doc under SysDocs/VibeCoding/ and routes it through cs-architect design review before any code is written. Requires the project to be PARTIAL-INITIALIZED or INITIALIZED; UNINITIALIZED is rejected. Explicitly invoked only — in CodeBuddy: /cs-vibe-coding <title> \"<structured content>\". Never writes SYSTEM_ROOT.md, modules/, or source. / 把碎片需求作为「前置设计」VibeCoding 文档写入 SysDocs/VibeCoding/ 并先经 cs-architect 设计审查，再写代码。要求项目处于「部分初始化」或「已初始化」，未初始化拒绝。仅显式调用——CodeBuddy 语法：/cs-vibe-coding <标题> \"<结构化内容>\"。绝不写 SYSTEM_ROOT.md、modules/ 或源码。"
argument-hint: "<title> \"<structured content>\""
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, ListDir
agent: cs-architect
---

# Vibe Coding — Fragmentary Change, Pre-Design

## Overview

Capture a fragmentary adjustment as a **pre-design** document under `SysDocs/VibeCoding/` and route it through `cs-architect` design review **before** any code is written. This is forward design, not after-the-fact recording. The doc is marked `draft` and later merged by `cs-sysdocs-update` under the four conditions.

Read the shared convention first: `../../references/sysdocs-system.md`, plus `sysdocs-vibe-template.md`.

## When to Use

- Project is **PARTIAL-INITIALIZED** or **INITIALIZED**, and the user explicitly invokes this skill for a fragmentary change.

**When NOT to use:**

- **UNINITIALIZED** → **stop**, require `cs-sysdocs-init` first. This skill must never create `SysDocs/` on an uninitialized project (it would lock init).
- Implicit/inferred fragmentary edits without an explicit call.

## Invocation (explicit only)

CodeBuddy: `/cs-vibe-coding <title> "<structured content>"`. This is a skill-invocation syntax, **not** a new command file. One title = one doc. `#` = targets (multiple allowed), `##` / `###` / `1.` / `2.` = sub-steps / reference notes.

## Inputs (normalize first)

Normalize into `operation`, `project_root`, `mode`, `source_scope`, `yes`; output `status`, `run_id`, `written`, `skipped`, `issues`. Record normalized inputs + confirm/reject results into the run report.

## Write Authorization (allowlist)

Only create/modify `SysDocs/VibeCoding/**` and the mandatory audit reports under
`SysDocs/.meta/reports/**` within the current project root. Never write
`SYSTEM_ROOT.md`, `modules/**`, source code, or paths outside the project root.
Architect fan-out briefs must not ask the subagent to modify business code.

- `<title>` → lowercase-hyphen slug, only `[a-z0-9-]`, length 1–80; reject empty, `..`, path separators, control chars, Windows reserved names.
- Resolved path must stay under `SysDocs/VibeCoding/`; no symlink/absolute/Bash escape outside.
- Filename collision → exclusive-create / lock-retry assign `-2`, `-3`; never overwrite. Temp file + atomic rename; failure cleans the temp file and keeps the old file.
- Raw call arguments may be recorded, but sanitize tokens/passwords/API keys/connection strings/private keys/PII before writing, and mark "原始参数已脱敏" in the doc. Never copy secrets into frontmatter, review round-trips, or logs.

The `.meta/reports/**` exception is report-only: report files must use the shared
schema and contain no source contents or unsanitized arguments.

## Process

### Phase 0 — Read SysDocs Context

After resolving `project_root` and checking the three-state gate, follow `../../references/sysdocs-design-context.md`: read `SysDocs/SYSTEM_ROOT.md` first when available, then the affected module documents and registered pages before deriving the proposal. Map input targets to manifest module IDs and stable section IDs; collect current responsibilities, contracts, dependency direction, and constraints. For PARTIAL-INITIALIZED projects, record missing context and preserve unresolved targets as `awaiting-repair`; retain the existing UNINITIALIZED rejection and write allowlist.

### Phase 1 — Parse structured input

Extract targets + steps. Write `SysDocs/VibeCoding/<YYYYMMDD-HHMM>-<slug>[ -N].md` from the vibe template (design goals → plan/steps → raw args + review round-trip at the bottom). In the plan/steps section, include the context summary and explain how each proposed step reuses or changes the documented system; label assumptions that depend on missing or stale evidence.

### Phase 2 — Architect review

`Task` fan-out to `cs-architect` with a short brief: targets + steps, project root, relevant document paths or readable snapshots, constraint summary, and context gaps. Do not paste the full `SYSTEM_ROOT.md` into the brief; the architect reads it when available and the affected module documents/pages before reviewing, and records those references in the review. Assess module responsibility, dependency direction, and contract compatibility against this baseline, keeping conclusions dependent on missing evidence provisional. Findings are structured: `id`, `level: target|step`, `severity: blocking|warning`, `target`, `message`, `resolution: pending|accepted|fixed`. All blocking findings must be fixed or explicitly accepted = no unhandled target-level defects.

### Phase 3 — Target-change gate (interrupting)

If a **target-level** defect hits a target-change condition, the main skill **stops to ask the user**, accepting only an explicit answer. No answer / timeout → keep doc `draft`, execute no code, merge nothing. Step-level findings are self-adjusted by the architect, no interruption.

Target-change conditions (any one triggers asking):

1. Multiple targets' solutions logically conflict.
2. A single target is infeasible.
3. A single target needs downgrade / phasing.
4. A target violates hard constraints (MUST / module responsibility boundary).

### Phase 4 — Fix and record

Revise per the review; record "审查结论 + 修复点" at the top of the doc.

### Phase 5 — Mark for merge

`status: draft`; later merged by `cs-sysdocs-update` under the four conditions.

## Invocation examples

```text
/cs-vibe-coding "fix-order-timeout" "# order-service\n## Reduce timeout to 2 seconds\n1. Update the service constraint"
cs-vibe-coding --project-root . --yes "fix-order-timeout" "# order-service ..."
cs-vibe-coding --project-root . --source-scope committed --yes "fix-order-timeout" "# order-service ..."
```

`--yes` is required for non-interactive hosts. `project_root` defaults to the
current workspace root; `source_scope` is recorded when supplied. When `Task` or
interactive confirmation is unavailable, keep the document `draft`, record
`architect_review: unavailable` or the rejected confirmation in the report, and
do not merge it.

## Cross-Platform Equivalence

CodeBuddy uses the `user-invocable` skill entry; Codex / Gemini / Claude use the builder-generated equivalent. All four must pass the same title + structured content + reject/write result through the same flow; a platform lacking slash syntax cannot bypass preconditions or safety checks. Behavior is what's guaranteed, not the tool name: parse → project-root/state check → preview → confirm → authorized read/write → validate → verdict. When `Task` is unavailable → main skill does the check and records `architect_review: unavailable`; vibe stays `draft`, never merged. No LSP → KB or Grep. No interactive confirm → without `--yes`, refuse to write.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll record it after coding" | This is pre-design, before code; after-the-fact is not the same thing. |
| "No docs yet, I'll create SysDocs here" | UNINITIALIZED is rejected — never create SysDocs/ here, it locks init. |
| "The architect found issues, I'll fix silently" | Target-level findings must be asked; step-level the architect self-adjusts. |
| "I'll merge it right into the module doc" | Only writes VibeCoding/; merge is cs-sysdocs-update's job, under four conditions. |
| "The raw args can go in verbatim" | Sanitize secrets before writing; mark "原始参数已脱敏". |

## Red Flags

- Creating `SysDocs/` or writing `SYSTEM_ROOT.md` / `modules/**`
- Writing source code from this skill
- Overwriting an existing vibe file instead of exclusive-create `-N`
- Skipping the interrupting target-change gate on a target-level defect
- Recording secrets verbatim into frontmatter / review round-trips / logs

## Verification

- [ ] State was PARTIAL-INITIALIZED or INITIALIZED; UNINITIALIZED rejected
- [ ] Draft and architect review cite the SysDocs documents actually read, affected modules, constraints, and proposed differences; missing/stale context and awaiting-repair targets remain explicit
- [ ] Doc written only under `SysDocs/VibeCoding/` via resolved-path allowlist
- [ ] Slug validated; exclusive-create with `-N`; temp-file + atomic rename
- [ ] Architect review recorded with structured findings; all blocking target-level defects fixed or accepted
- [ ] Target-change gate interrupted for target-level findings; no answer → `draft`
- [ ] Raw args sanitized + marked; no secrets in frontmatter/logs
- [ ] Doc marked `draft`, not `active`, not merged
- [ ] Sanitized `.meta/reports/<run-id>.json` written; verdict recorded

## Interaction with Other Skills

- `cs-sysdocs-init` / `cs-sysdocs-update`: upstream/downstream — this skill requires init/update to have reached PARTIAL-INITIALIZED or INITIALIZED; update later merges the vibe.
- `cs-architect` (agent): design review fan-out (short, read-only brief).
- `cs-code-query`: symbol/KB query fallback when needed.

## See Also

- `../../references/sysdocs-system.md` — shared convention (inventory, frontmatter, validator, report)
- `../../references/sysdocs-vibe-template.md` — vibe doc shape
