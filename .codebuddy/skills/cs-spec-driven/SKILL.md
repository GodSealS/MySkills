---
name: cs-spec-driven
description: "Specify a new project or significant change when requirements or design boundaries are missing. / 为需求或设计边界不完整的新项目、重大变更编写规格。"
argument-hint: "[project or feature to spec]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
---

# Spec-Driven Development

## Scope

Create or update the authoritative specification when requirements need definition.
Clear, self-contained edits can proceed from user requirements without a separate spec.
Preserve existing specifications instead of recreating them.

## Process

1. Establish objective, acceptance criteria, constraints and exclusions from the request
   and source. Ask only about missing information that changes the design. State
   consequential assumptions briefly and reuse decisions already made by the user.
2. Follow the [task-context protocol](../../references/sysdocs-design-context.md).
   Reference existing commands, conventions and accepted ADRs rather than copying the
   project's setup into every feature specification.
3. Describe target behavior, affected interfaces, verification and material risks.
   For a new project also define stack, structure, executable commands, code conventions
   and test strategy. Keep a small change's spec proportionate to its scope.
4. Consult `cs-architect` only for new or materially changed architectural boundaries,
   public contracts, dependency direction or unresolved architectural conflicts.
   Reuse unchanged accepted architecture. Record significant, durable decisions with
   `cs-docs-adrs`; routine implementation choices stay in task notes.
5. Save at the existing authoritative path, otherwise `SysDocs/specs/<topic>.md`.
   New SysDocs specs use schema 2 metadata (`schema`, `doc_type: spec`, `updated`)
   and a retrieval summary identifying relevant modules and proposed symbols as unimplemented.
   Preserve external/historical formats; a spec alone does not initialize a full library.
6. Resolve material open choices with the user. Reuse authorization for unchanged scope.
   Use `cs-planning` once for dependency ordering and task breakdown when needed; do not
   create separate PLAN and TASKS approval rounds. Stop after the spec when that is the
   requested deliverable; continue implementation only within authorized scope.

## Optional Design Review

Use `cs-grill-me` for explicit stress-test requests or major design assumptions that remain
uncertain. Record findings and decisions when a review occurs. Ordinary specifications
need no `Grill Review` section or formal skip declaration.

## Verification

- [ ] Objective, scope, intended behavior and success criteria are concrete.
- [ ] Changed boundaries and significant risks have evidence or explicit open decisions.
- [ ] Verification is executable; existing conventions are linked rather than duplicated.
- [ ] One authoritative spec separates proposed behavior from current implementation.
- [ ] Required user decisions are resolved; existing approvals are reused for unchanged scope.

Update the spec when accepted scope or decisions change. Implement using `cs-incremental`
and apply `cs-tdd` to executable behavior changes.
