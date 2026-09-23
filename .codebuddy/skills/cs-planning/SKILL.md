---
name: cs-planning
description: "Break clear requirements into ordered, verifiable tasks when dependencies or scope need planning. / 将明确需求拆成有依赖顺序和验收条件的任务。"
argument-hint: "[requirements or spec to plan]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
---

# Planning and Task Breakdown

## Scope

Use when work needs decomposition. Reuse an adequate existing task list; handle obvious
local edits directly. Clear user requirements suffice: a formal spec and Grill Review
section are not prerequisites.

## Process

1. Read selected requirements and relevant source using the shared
   [task-context protocol](../../references/sysdocs-design-context.md). Reuse valid
   evidence and accepted ADRs; inspect changed or unresolved boundaries.
2. Identify dependencies and risks. The host validates ordinary dependency ordering.
   Consult `cs-architect` only for new or materially changed module boundaries, public
   contracts, dependency direction, or unresolved architectural conflicts. Supply a
   focused question and prior evidence rather than reopening the entire design.
3. Slice into independently verifiable end-to-end outcomes. Keep cross-domain features
   together unless a shared or independently delivered contract must land first.
   Size by coherent outcome and reviewability, not a fixed file-count limit.
4. Record each task's outcome, acceptance criteria, verification command or procedure,
   dependencies, likely files, and documentation impact (or a concrete no-impact reason).
   Add primary owner (`arch` / `frontend` / `backend`) and collaborators only when work
   will actually be delegated or an explicit team workflow requires them.
5. Save one authoritative task list, normally `tasks/plan.md`, including status. Reuse an
   existing location. If a consumer requires `tasks/todo.md`, keep only IDs, status and
   links there; keep acceptance criteria in the authoritative plan.
6. Present the plan with unresolved decisions. Reuse approval for unchanged scope;
   ask only for material choices or authorization still missing. A planning-only request
   ends here; already-authorized implementation may continue.

## Optional Design Review

Use `cs-grill-me` when explicitly requested or when a major design has unresolved
assumptions needing stress-testing. Record actual findings and decisions in the existing
design. Ordinary plans need neither a review round nor a formal skip record.

## Verification

- [ ] Every task has an observable outcome, acceptance criteria and appropriate verification.
- [ ] Dependencies and material boundary questions are resolved or explicitly blocked.
- [ ] Accepted decisions and valid evidence were reused; changed assumptions were checked.
- [ ] Tasks have one source of truth; delegation metadata is present when needed.
- [ ] Documentation impact and outstanding user decisions are explicit.

Implementation follows `cs-incremental`; project verification follows
[Definition of Done](../../references/cs-definition-of-done.md).
