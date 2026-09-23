---
name: cs-sysdocs-init
description: "Explicitly generates a human-readable SysDocs library for an undocumented project: overview, architecture, important flows, and source-file responsibilities. Uses source evidence with optional knowledge-base assistance. Only for UNINITIALIZED inventory; maintenance and explicit migration belong to cs-sysdocs-update. / 显式为未梳理项目生成面向人的 SysDocs 概览、架构、关键流程和文件职责；知识库可选，源码核实必需。只用于未初始化状态，维护和显式迁移交给 cs-sysdocs-update。"
argument-hint: "[project_root] [--type code|spec] [--source-roots <dirs>] [--kb <backend>] [--source-scope committed|committed+working-tree|unversioned] [--yes]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, ListDir
agent: cs-architect
---

# SysDocs Init — Human-Readable Project Documentation

## Overview

Generate a navigable explanation of what the project does, its runtime boundaries, module responsibilities, important flows, and where to read the implementation. This is an explicitly requested full documentation deliverable, not a prerequisite for ordinary development or a small design proposal.

Read [the shared protocol](../../references/sysdocs-system.md) first. It owns the schema, inventory, summaries, evidence, protection and validation rules. Use its overview, module, file-index and flow templates; do not reproduce a second schema here.

## When to Use

- The user requests project documentation and inventory is **UNINITIALIZED**: no formal library, including a project with only `VibeCoding/` and reports.
- Code or accepted design evidence identifies the requested project scope.
- **PARTIAL-INITIALIZED** → use `cs-sysdocs-update` repair; **INITIALIZED** → update within the requested scope. Never reinitialize, silently migrate, or overwrite an existing library.
- Ordinary work without SysDocs continues with task evidence. A proposal alone uses `cs-vibe-coding` and does not trigger full initialization.

## Inputs and Authorization

Normalize `operation`, `project_root`, `mode`, `source_scope`, `--type`, `--source-roots`, `--kb`, and `yes`. Resolve the explicitly named project root, defaulting to the current workspace; do not discover a different parent or child root silently.

- `--type code|spec` only overrides project classification; it does not override exclusions or evidence requirements.
- `--source-roots` declares the business-source scope. Record exclusions with reasons.
- `--kb` selects the actual requested backend; `none` disables KB use. Selection, availability, coverage and freshness follow `cs-code-query`.
- `source_scope` is `committed`, `committed+working-tree`, or `unversioned`. Use task authorization to select the scope; explicitly include intended working changes rather than silently ignoring them.
- Reuse existing authorization for this documentation deliverable. Present the intended scope and proceed when already authorized; `--yes` is an automation convenience, not a requirement to reapprove the same work. Ask only if a material scope or constraint choice remains unresolved.

## Write Authorization

Only write `SysDocs/**` beneath the resolved project root, including temporary files and reports. Resolve real paths and symlinks before writes; reject escape paths. Do not modify source, external authoritative specs/ADRs, installed skills, or knowledge-base indexes; do not install or create a KB. Link existing authoritative material in its original location.

Architect boundary reviews, when available, use short read-only briefs. A persona already running this workflow performs its own assigned checks and does not invoke another persona. Missing delegation alone is not evidence of incorrect documentation or an automatic `PARTIAL` result.

Verification evidence should reuse the enclosing task artifact. If that artifact is outside this skill's write allowlist, return the results to the host for authorized recording; do not widen the allowlist or create a duplicate report merely for routing.

## Process

### 1. Inventory and source baseline

Apply the shared dual-layout inventory: legacy `SYSTEM_ROOT.md` / `modules/` and schema 2 `README.md` / `architecture/` / `files/`. A mixed interrupted migration is repair work, not a new init. Unknown future schema is read-only `FAILED`; preserve everything.

Identify runtime, entry points, packages and existing authoritative requirements. Record the inspected revision and declared source paths. Committed scope uses the actual commit contents; working-tree scope records the base SHA plus included staged, unstaged and untracked files in existing task evidence; its required `evidence` metadata points to that project-relative file, optionally with an anchor. Without Git, use explicit source paths and `unversioned`; do not invent a SHA. Recheck relevant source state before publishing; changes invalidate affected evidence.

Exclude dependency caches, generated/build output and sensitive material. Business code in `components/` remains eligible. Tests, configuration and assets may have separate reading guidance or directory-level explanations; exclusions must not hide business source.

For a spec-only project, document the project purpose, existing requirements and the fact that no implementation exists. Use empty source scope and no invented modules; prospective designs remain proposals/specs. The required architecture overview states that implementation does not yet exist and links its authoritative requirements; do not invent module pages or create other empty directories.

### 2. Query evidence, with source fallback

Use `cs-code-query` to check the actual backend, project/index identity, queryability, file coverage and source revision. Directory or CLI existence is not proof of usable evidence. Prefer existing usable indexes; never bootstrap here. A requested backend that fails is reported; do not silently substitute another.

Use KB results as candidates, then read the source/configuration supporting important facts. Without a usable KB, source reads and reference searches may fully support the deliverable. Record KB limitations separately; only unresolved necessary facts reduce the result to `PARTIAL`.

### 3. Establish reading structure

Derive modules from responsibilities and actual dependency direction, using packages/directories as evidence rather than treating every directory as a module. Identify the key flows and exception paths readers need. Preview modules, source scope, exclusions and evidence gaps as a progress update. Existing authorization permits reversible generation to continue.

Where helpful and the host supports it, request a read-only `cs-architect` review of the short boundary table. Do not send entire module bodies. Resolve material boundary ambiguity using evidence; if a needed user choice is absent, retain it as unresolved rather than inventing a business decision.

### 4. Generate schema 2 pages

- `SysDocs/README.md`: purpose, terminology, running boundaries and a short reading route.
- `SysDocs/PROJECT-MAP.md`: required root-level current architecture, module execution flow, module relationships and project workflow diagrams, using the [project map template](../../references/sysdocs-project-map-template.md). Link it directly from README; mark unavailable/unimplemented views explicitly rather than inventing facts.
- `architecture/overview.md`: implemented system and deployment boundaries; for a spec-only project, explain that no implementation exists and link the design requirements.
- `architecture/modules/<module-id>.md`: responsibilities, collaborators, key entry points and important limitations.
- `architecture/flows/<flow-id>.md`: important cross-module normal and exceptional paths when independently useful.
- `files/README.md`: declared source scope, directory navigation and exclusions with reasons.
- `files/<module-id>.md`: the complete file-responsibility table for the declared module scope, paired with its module page; a shared file has one detailed owner.
- Link accepted specs/ADRs at their authoritative locations. Create `specs/` or `decisions/` content only when warranted and authorized; do not invent accepted requirements or design reasons.

Use schema 2 metadata from the shared protocol. Source-derived pages record `source_scope`, `source_paths`, and a verified base `generated_from` when Git-based. Navigation replaces the old duplicated editable module manifest.

Each generated overview, architecture and file page starts with `## 检索摘要` after metadata (an H1 may precede it). List only key entry or responsibility-bearing classes/structures, each with a one-sentence responsibility; use real functions, modules, configuration or processes where no class exists. Include important cross-module and transaction, permission, ownership or recovery boundaries. Do not build an exhaustive symbol list or a duplicate summary index.

Write files through temporary files and atomic rename. Preserve existing proposals, unknown fields and human material. Record interrupted progress so update repair can resume without replacing completed pages.

### 5. Verify structure and content separately

Run the shared validator for the **whole requested library**: metadata, summaries, paths, navigation, file coverage and unique ownership. Separately verify source-backed responsibilities, important dependencies/flows, summary-body agreement and constraints against evidence. Record actual methods and missing parser capabilities; formatting checks cannot prove symbol semantics or Mermaid correctness.

Record sanitized results with declared scope, checked items, failures and uncovered items in existing task/review evidence. Use a `.meta/reports/` file only when a separate durable artifact is needed; do not require a duplicate report. `COMPLETE` requires full requested coverage and necessary content evidence, not simply a successful validator exit. Only mark applicable pages `active` after both kinds of checks. Missing KB or an unavailable subagent is not by itself a failure.

## Verification

- [ ] Explicit full-documentation request and UNINITIALIZED inventory established; proposals alone do not count as initialization.
- [ ] Source scope, actual baseline, exclusions and accepted source locations are recorded; no sensitive material copied.
- [ ] KB queried only when usable; limitations and source verification are distinguished.
- [ ] README, architecture and file navigation explain the project; every declared business file has one detailed responsibility owner.
- [ ] PROJECT-MAP covers all four views, with source-backed diagrams where applicable, navigable evidence and explicit gaps; diagram syntax checks and content verification are reported separately.
- [ ] Summaries use key real symbols plus one-sentence responsibilities and significant boundaries; no duplicated index.
- [ ] Future designs remain identified as unimplemented; requirements/ADRs retain one authoritative location.
- [ ] All writes stay in the allowlist; existing human text and proposals survive.
- [ ] Full structure checks and separate content checks support the scoped verdict; existing task evidence or any needed report is sanitized.

## Interaction with Other Skills

- `cs-sysdocs-update`: sole repair, affected maintenance, explicit refresh or migration entry.
- `cs-vibe-coding`: may create a proposal before any library exists.
- `cs-code-query`: actual index/query evidence and source fallback, without automatic creation.
- `cs-spec-driven`: specifications do not automatically require full initialization.

## See Also

- [Shared protocol](../../references/sysdocs-system.md)
- [Overview template](../../references/sysdocs-overview-template.md)
- [Module template](../../references/sysdocs-module-template.md)
- [Design context](../../references/sysdocs-design-context.md)
