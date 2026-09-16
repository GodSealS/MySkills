---
name: cs-vibe-coding
description: "Explicitly captures a fragmentary change as a reviewed pre-design proposal in SysDocs/VibeCoding/, even when no project library exists. Keeps future design separate from implemented architecture; creates no source code or full documentation baseline. / 显式把碎片需求保存为 SysDocs/VibeCoding/ 前置方案并审查；允许尚无项目文档库，明确区分未来设计与现状，不写源码、不强制全量初始化。"
argument-hint: "<title> \"<structured content>\""
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, ListDir
agent: cs-architect
---

# Vibe Coding — Fragmentary Change, Pre-Design

## Overview

Capture and review a proposal before implementation, preserving the user's goals and a traceable distinction between current facts and future design. Invoke only when the user explicitly requests this skill. Read [the shared protocol](../../references/sysdocs-system.md), [design context](../../references/sysdocs-design-context.md), and [vibe template](../../references/sysdocs-vibe-template.md).

A project can be **UNINITIALIZED**, **PARTIAL-INITIALIZED**, or **INITIALIZED**. No formal SysDocs library is required. Creating only `SysDocs/VibeCoding/` and reports leaves project documentation **UNINITIALIZED**; it does not lock out later init or silently satisfy a full documentation request.

## Invocation and Inputs

CodeBuddy: `/cs-vibe-coding <title> "<structured content>"`; other hosts use their equivalent skill entry. A title and natural-language content are sufficient. `#` may identify multiple targets and subheadings/lists their proposed steps; do not invent missing user intent to fit a parser.

Normalize `operation`, `project_root`, `mode`, `source_scope`, `yes`, title and targets. Record only sanitized input. Reuse the existing request's authorization to create a reversible proposal. `--yes` is optional for automation, not a new gate when the user already authorized writing. Neither absent interactivity nor unavailable subagents prevents a supported proposal draft.

## Write Authorization

Only create/modify `SysDocs/VibeCoding/**` and, when needed, audit reports under `SysDocs/.meta/reports/**` in the resolved project root. Never write current `README.md`, `SYSTEM_ROOT.md`, architecture/modules/files pages, external requirements, KB indexes or business source. Unknown future schema remains read-only under the shared gate; do not mutate a library whose schema cannot be safely understood.

- Validate the slug: lowercase letters, digits and hyphens, 1–80 characters; reject separators, `..`, control characters and Windows reserved names. Derive a meaningful safe slug from non-Latin titles while preserving the readable title in the document.
- Resolve paths and symlinks to stay within the allowlist; reject escapes. Use exclusive-create with `-2`, `-3` on filename collision; never overwrite a different proposal. Temp files stay in the allowlist and land by atomic rename.
- Sanitize tokens, passwords, keys, connection strings and personal data before writing input/review text; use redaction markers and identify redacted input. Reports contain no source dumps or unsanitized arguments.

## Process

### 1. Read task-relevant context

Apply shared dual-layout inventory without an init prerequisite. Read the existing entry/navigation if present, then relevant accepted requirements and decisions. Extract summaries to select candidate bodies, including key symbol responsibilities and important boundaries. Combine document candidates with actual available KB/source candidates; inspect discrepancies and verify current facts in source. Legacy or external documents without summaries require body/link fallback.

For responsibility, module, transaction, permission, ownership, recovery or dependency changes, inspect related flow explanations even without direct matches; expand to all flows if the relevant set cannot be determined. Source inspection can establish enough evidence without a KB. Record actual index coverage/freshness and remaining gaps; never install/bootstrap a KB.

If no library exists, derive the proposal from source and available authoritative requirements. If evidence is missing, identify assumptions precisely. Use stable module IDs when existing targets resolve; otherwise keep descriptive proposed targets with an explicit unresolved/planned mapping, rather than inventing a manifest or forcing whole-library repair. Unrelated missing documents do not block this draft.

### 2. Write the proposal draft

Create `SysDocs/VibeCoding/<YYYYMMDD-HHMM>-<slug>[-N].md` using the current vibe template. Include current-state evidence, design goals, proposed changes, verification criteria, context gaps and the sanitized review exchange.

Place `## 检索摘要` before the detailed body. Name key existing classes/structures with one-sentence responsibilities where applicable; use real functions/modules/processes otherwise. Mark proposed symbols and future boundaries as **拟议／未实施**. Include cross-module effects and relevant transaction/permission/ownership/recovery boundaries without listing every internal symbol.

Maintain `status: draft` and implementation evidence as prescribed by the shared template. A reviewed design is not implemented architecture or an accepted requirement by default.

### 3. Review the design

When running as the host with delegation available, give `cs-architect` a short read-only brief: goals, targets, relevant document/source paths, applicable constraints, candidate differences and evidence gaps. The reviewer reads the relevant material rather than receiving a pasted full library. A persona already running this skill performs the assigned review locally and must not invoke another persona.

Assess responsibility, dependency direction, constraint compatibility, necessary interfaces and proposed verification. Record structured findings: `id`, `level: target|step`, `severity: blocking|warning`, `target`, `message`, `resolution: pending|accepted|fixed`. Evidence-dependent conclusions remain provisional until verified. If separate review is unavailable, record the actual local review method and limit; do not fabricate a reviewer or declare an unchecked design reviewed. A draft can still be delivered.

### 4. Resolve target-level choices

Request a user decision only when the review exposes a material **unresolved** target change:

1. The proposed targets conflict.
2. A target is infeasible.
3. A target needs reduced scope or phasing.
4. A target conflicts with applicable hard requirements or responsibilities.

Reuse an existing explicit decision that already resolves the same issue; do not ask again. Present concrete alternatives and their effects. No answer means the disputed target stays pending in the draft; do not implement or merge it. Step-level repairs within the accepted target are made directly and documented. Accepting a risk cannot silently override an authoritative hard constraint; identify the required authorized constraint change.

### 5. Verify and hand off

Record review conclusions and repairs near the top **after** the fixed retrieval summary. Verify links, permitted targets, metadata, summary-body consistency and the distinction between existing facts and proposed design. Run shared structural validation for the proposal scope only; it must not demand a complete project library. Separately record source/content evidence and unresolved findings.

Deliver the draft with sanitized scoped verification evidence, distinguishing draft completion from design readiness and implementation. Prefer the proposal's own review section or existing task evidence; no separate report is required. If the enclosing task evidence is outside this skill's write allowlist, return the results to its host instead of editing that file. A draft may be complete as a capture artifact while necessary design questions remain explicitly pending; never label unresolved design as implementation-ready.

Later integration uses `cs-sysdocs-update` when appropriate destinations exist. Verified implementation can update current descriptions; an authorized docs-only proposal can update intended specifications/decisions or links while remaining unimplemented. Do not merge future design into current architecture or create a library merely to obtain a merge target.

## Verification

- [ ] Explicit invocation established; all inventory states permitted and proposal-only remains UNINITIALIZED.
- [ ] Relevant current facts, accepted requirements, KB/source evidence and gaps recorded without full-library prerequisites.
- [ ] Summary contains key real symbols/responsibilities and boundaries; proposed symbols clearly marked.
- [ ] Paths/slugs/collisions validated; writes restricted to proposals and any needed sanitized reports.
- [ ] Review method and structured findings are truthful; missing delegation does not fabricate review evidence.
- [ ] New unresolved target changes receive a user decision; existing authorization and decisions are reused.
- [ ] Draft, readiness and implementation states remain distinct; unresolved targets are preserved.
- [ ] Structure checks and content checks are separate; no architecture/source/KB writes occurred.

## Interaction with Other Skills

- `cs-sysdocs-init`: can initialize a formal library later; proposal creation neither invokes nor blocks it.
- `cs-sysdocs-update`: integrates eligible proposals into appropriate existing destinations without losing their history.
- `cs-code-query`: optional actual index evidence and source fallback.
- `cs-architect`: read-only review at the host's direction; no persona-to-persona invocation.

## See Also

- [Shared protocol](../../references/sysdocs-system.md)
- [Design context](../../references/sysdocs-design-context.md)
- [Vibe template](../../references/sysdocs-vibe-template.md)
