---
name: cs-docs-adrs
description: "Records decisions and documentation. Use when making architectural decisions, changing public APIs, shipping features, or when you need to record context that future engineers and agents will need to understand the codebase. / 记录决策与文档。用于架构决策、变更公开API、发布功能、或记录未来工程师和Agent需要的上下文。"
argument-hint: "[decision or documentation to write]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
agent: cs-code-reviewer
---

# Documentation and ADRs

## Overview

Document decisions, not just code. The most valuable documentation captures the *why* — the context, constraints, and trade-offs that led to a decision. Code shows *what* was built; documentation explains *why it was built this way* and *what alternatives were considered*.

## When to Use

- Making a significant architectural decision
- Choosing between approaches with significant, durable architectural consequences
- Adding or changing a public API
- Shipping a feature that changes user-facing behavior
- Onboarding new team members (or agents)

**When NOT to use:** Don't document obvious code. Don't restate what the code already says.

## Architecture Decision Records (ADRs)

Routine implementation choices belong in task notes. Reuse accepted ADRs for unchanged decisions.

### ADR Template

For a newly created ADR under `SysDocs/decisions/`, include schema 2 metadata and an applicable retrieval summary as below. Existing external ADRs and historical formats remain authoritative; do not rewrite them merely to adopt this template or mark a decision Accepted without acceptance evidence.

```markdown
---
schema: 2
doc_type: decision
updated: <ISO date or timestamp>
---

# ADR-[NNN]: [Title]

## 检索摘要
[Key classes/structures or actual modules/processes, their one-sentence responsibilities, and the decision boundary; label future symbols as proposed.]

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context
[What is the situation? What constraints exist?]

## Decision
[What we decided and why.]

## Consequences
### Positive
[What becomes easier, faster, or better]

### Negative
[What trade-offs we're accepting]

### Mitigations
[How we'll manage the negative consequences]

## Alternatives Considered
- [Alternative A]: [Why rejected]
- [Alternative B]: [Why rejected]
```

## When to Write What

| Situation | Document | Location |
|-----------|----------|----------|
| Architecture decision | ADR | Existing authoritative ADR location; new projects default to `SysDocs/decisions/ADR-NNN.md` |
| API reference | API docs | Inline JSDoc + generated docs |
| How to use a module | Module doc | `SysDocs/architecture/modules/<slug>.md`; full file responsibilities in `SysDocs/files/<slug>.md` (see `cs-sysdocs-update`) |
| Project setup | README | Root `README.md` |
| Design rationale | Design doc | `docs/design/[feature].md` |
| Changelog entries | CHANGELOG | `CHANGELOG.md` |

Keep existing accepted specs/ADRs in their authoritative locations and link them from SysDocs. New requirements default to `SysDocs/specs/`; creating a spec or ADR does not initialize an entire documentation library. Legacy SysDocs layouts remain locally maintainable until an explicit migration through `cs-sysdocs-update`.

Preserve accepted ADR bodies. A changed decision uses a new ADR and supersession link; only locator/status corrections belong in an old record. Implementation facts cannot automatically become MUST requirements. Follow [the shared context protocol](../../references/sysdocs-design-context.md) for source-backed descriptions, header summaries and affected synchronization; proposed changes must remain visibly unimplemented.

## Documentation Standards

### API Documentation
- Every public function has JSDoc/TSDoc
- Include parameter descriptions and return types
- Include usage examples for non-obvious APIs
- Document error conditions and thrown exceptions

### Inline Comments
- Explain *why*, not *what*
- Document non-obvious side effects
- Reference related ADRs and issues


## Interaction with Other Skills

- `cs-sysdocs-init` / `cs-sysdocs-update`: SysDocs separates current architecture/files, expected requirements and historical decisions. Link each authoritative source once and synchronize affected content within the authorized task.

## Verification

- [ ] ADRs created for significant architectural decisions
- [ ] Public APIs have JSDoc/T SDoc with examples
- [ ] README is current and accurate
- [ ] Inline comments explain why, not what
- [ ] Changelog updated for user-facing changes
