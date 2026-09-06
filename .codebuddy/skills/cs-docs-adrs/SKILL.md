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
- Choosing between competing approaches
- Adding or changing a public API
- Shipping a feature that changes user-facing behavior
- Onboarding new team members (or agents)

**When NOT to use:** Don't document obvious code. Don't restate what the code already says.

## Architecture Decision Records (ADRs)

### ADR Template
```markdown
# ADR-[NNN]: [Title]

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
| Architecture decision | ADR | `docs/adr/ADR-NNN.md` |
| API reference | API docs | Inline JSDoc + generated docs |
| How to use a module | Module doc | `SysDocs/modules/<slug>.md` (see `cs-sysdocs-update`) |
| Project setup | README | Root `README.md` |
| Design rationale | Design doc | `docs/design/[feature].md` |
| Changelog entries | CHANGELOG | `CHANGELOG.md` |

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

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The code is self-documenting" | Code shows what; docs explain why. Both are needed. |
| "I'll write docs later" | Context evaporates. Write docs while the reasoning is fresh. |
| "Nobody reads documentation" | Future you will. And future agents. |

## Interaction with Other Skills

- `cs-sysdocs-init` / `cs-sysdocs-update`: SysDocs = what/how, ADR = why. Module docs link ADRs; this skill's "How to use a module" points to `SysDocs/modules/<slug>.md`, not `src/module/README.md` (avoid double-writing).

## Verification

- [ ] ADRs created for significant architectural decisions
- [ ] Public APIs have JSDoc/T SDoc with examples
- [ ] README is current and accurate
- [ ] Inline comments explain why, not what
- [ ] Changelog updated for user-facing changes
