---
name: cs-using
model: DeepSeek-V4-Flash
description: "Discovers and invokes agent skills. Use when starting a session or when you need to discover which skill applies to the current task. This is the meta-skill that governs how all other skills are discovered and invoked. / 发现和调用Agent技能。用于启动会话或发现当前任务适用哪个技能——这是管理所有其他技能发现与调用的元技能。"
argument-hint: "[task description]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
agent: cs-code-reviewer
---

# Using Agent Skills

## Overview

Agent Skills is a collection of engineering workflow skills organized by development phase. Each skill encodes a specific process that senior engineers follow. This meta-skill helps you discover and apply the right skill for your current task.

## Skill Discovery

When a task arrives, identify the development phase and apply the corresponding skill:

```
Task arrives
    │
    ├── Don't know what you want yet? ──────→ cs-interview-me
    ├── Have a rough concept, need variants? → cs-idea-refine
    ├── New project/feature/change? ──→ cs-spec-driven
    ├── Have a spec, need tasks? ──────→ cs-planning
    ├── Implementing code? ────────────→ cs-incremental
    │   ├── UI work? ─────────────────→ cs-frontend-ui
    │   ├── API work? ────────────────→ cs-api-design
    │   ├── Need better context? ─────→ cs-context-eng
    │   ├── Need doc-verified code? ───→ cs-source-driven
    │   └── Stakes high / unfamiliar code? ──→ cs-doubt-driven
    ├── Writing/running tests? ────────→ cs-tdd
    │   └── Browser-based? ───────────→ cs-browser-test
    ├── Something broke? ──────────────→ cs-debugging
    ├── Reviewing code? ───────────────→ cs-code-review
    │   ├── Too complex? ─────────────→ cs-simplify
    │   ├── Security concerns? ───────→ cs-security
    │   └── Performance concerns? ────→ cs-perf-opt
    ├── Committing/branching? ─────────→ cs-git-workflow
    ├── CI/CD pipeline work? ──────────→ cs-cicd
    ├── Deprecating/migrating? ────────→ cs-deprecation
    ├── Writing docs/ADRs? ───────────→ cs-docs-adrs
    ├── Adding logs/metrics/alerts? ───→ cs-observability
    └── Deploying/launching? ─────────→ cs-shipping
```

## Core Operating Behaviors

These behaviors apply at all times, across all skills. They are non-negotiable.

### 1. Surface Assumptions

Before implementing anything non-trivial, explicitly state your assumptions:

```
ASSUMPTIONS I'M MAKING:
1. [assumption about requirements]
2. [assumption about architecture]
3. [assumption about scope]
→ Correct me now or I'll proceed with these.
```

### 2. Manage Confusion Actively

When you encounter inconsistencies:
1. **STOP.** Do not proceed with a guess.
2. Name the specific confusion.
3. Present the tradeoff or ask the clarifying question.
4. Wait for resolution before continuing.

### 3. Push Back When Warranted

- Point out the issue directly
- Explain the concrete downside (quantify when possible)
- Propose an alternative
- Accept the human's decision if they override with full information

### 4. Enforce Simplicity

Before finishing any implementation, ask:
- Can this be done in fewer lines?
- Are these abstractions earning their complexity?
- Would a staff engineer look at this and say "why didn't you just..."?

### 5. Maintain Scope Discipline

Touch only what you're asked to touch. Do NOT:
- Remove comments you don't understand
- "Clean up" code orthogonal to the task
- Refactor adjacent systems as a side effect
- Delete code that seems unused without explicit approval
- Add features not in the spec

### 6. Verify, Don't Assume

Every skill includes a verification step. "Seems right" is never sufficient — there must be evidence. See `.codebuddy/references/cs-definition-of-done.md`.

## Skill Rules

1. **Check for an applicable skill before starting work.**
2. **Skills are workflows, not suggestions.** Follow steps in order.
3. **Multiple skills can apply.** A feature might involve many skills in sequence.
4. **When in doubt, start with a spec.** Use `cs-spec-driven`.

## Quick Reference

| Phase | Skill | One-Line Summary |
|-------|-------|-----------------|
| Define | cs-interview-me | Surface what the user actually wants |
| Define | cs-idea-refine | Refine ideas through structured thinking |
| Define | cs-spec-driven | Requirements before code |
| Plan | cs-planning | Decompose into verifiable tasks |
| Build | cs-incremental | Thin vertical slices |
| Build | cs-source-driven | Verify against official docs |
| Build | cs-doubt-driven | Adversarial review of decisions |
| Build | cs-context-eng | Right context at right time |
| Build | cs-frontend-ui | Production-quality UI |
| Build | cs-api-design | Stable interfaces |
| Verify | cs-tdd | Failing test first |
| Verify | cs-browser-test | Chrome DevTools MCP verification |
| Verify | cs-debugging | Reproduce → localize → fix → guard |
| Review | cs-code-review | Five-axis review |
| Review | cs-simplify | Reduce complexity, preserve behavior |
| Review | cs-security | OWASP prevention |
| Review | cs-perf-opt | Measure first, optimize what matters |
| Ship | cs-git-workflow | Atomic commits |
| Ship | cs-cicd | Automated quality gates |
| Ship | cs-deprecation | Remove old systems safely |
| Ship | cs-docs-adrs | Document the why |
| Ship | cs-observability | Structured logs, metrics, traces |
| Ship | cs-shipping | Pre-launch checklist, rollback plan |
