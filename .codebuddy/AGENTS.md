# Agent Skills for CodeBuddy

This directory contains the **agent-skills** collection — production-grade engineering skills, specialist agent personas, lifecycle hooks, and reference checklists — ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT License).

## Skill Discovery

When a task arrives, identify the development phase and apply the corresponding skill:

```
Task arrives
    │
    ├── Don't know what you want yet? ──────→ cs-interview-me
    ├── Have a rough concept? ───────────────→ cs-idea-refine
    ├── Design ready, need stress-test? ─────→ grill-me
    ├── New project/feature/change? ─────────→ cs-spec-driven
    ├── Have a spec, need tasks? ────────────→ cs-planning
    ├── Team build/review requested? ─────────→ do not auto-select; require explicit skill or command invocation
    ├── Implementing code? ──────────────────→ cs-incremental
    │   ├── Choosing minimal solution? ───────→ cs-minimal
    │   ├── UI work? ────────────────────────→ cs-frontend-ui
    │   ├── API work? ───────────────────────→ cs-api-design
    │   ├── Need better context? ────────────→ cs-context-eng
    │   ├── Need doc-verified code? ─────────→ cs-source-driven
    │   └── Stakes high? ────────────────────→ cs-doubt-driven
    ├── Writing/running tests? ──────────────→ cs-tdd
    │   └── Browser-based? ──────────────────→ cs-browser-test
    ├── Something broke? ────────────────────→ cs-debugging
    ├── Reviewing code? ─────────────────────→ cs-code-review
    │   ├── Too complex? ────────────────────→ cs-simplify
    │   ├── Security concerns? ───────────────→ cs-security
    │   └── Performance concerns? ───────────→ cs-perf-opt
    ├── Committing/branching? ───────────────→ cs-git-workflow
    ├── CI/CD pipeline work? ────────────────→ cs-cicd
    ├── Deprecating/migrating? ──────────────→ cs-deprecation
    ├── Writing docs/ADRs? ──────────────────→ cs-docs-adrs
    ├── Building system docs? ────────────────→ cs-sysdocs-init / cs-sysdocs-update
    ├── Fragmentary change, pre-design? ─────→ cs-vibe-coding
    ├── Adding logs/metrics/alerts? ─────────→ cs-observability
    └── Deploying/launching? ────────────────→ cs-shipping
```

## Lifecycle Mapping

```
  DEFINE                 PLAN           BUILD          VERIFY         REVIEW          SHIP
 ┌──────┐      ┌──────┐   ┌──────┐   ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐
 │ Idea │ ───▶ │ Spec │ ─▶│ Grill│ ─▶│ Code │ ───▶ │ Test │ ───▶ │  QA  │ ───▶ │  Go  │
 │Refine│      │  PRD │   │Review│   │ Impl │      │Debug │      │ Gate │      │ Live │
 └──────┘      └──────┘   └──────┘   └──────┘      └──────┘      └──────┘      └──────┘
                            │
                            └── Record findings or an explicit skip with accepted risks
```

## Agent Personas

| Agent | File | Role | Invoked by |
|-------|------|------|------------|
| Architect | `.codebuddy/agents/cs-architect.md` | Module boundaries, dependency direction, ADRs | `cs-spec-driven`, `cs-planning` fan-out; manual-only team workflows |
| Frontend Lead | `.codebuddy/agents/cs-frontend-lead.md` | Frontend domain owner: UI, state, browser verification | frontend-owned build skills; manual-only team workflows |
| Backend Lead | `.codebuddy/agents/cs-backend-lead.md` | Backend domain owner: API, data, server security/perf | backend-owned build skills; manual-only team workflows |
| Code Reviewer | `.codebuddy/agents/cs-code-reviewer.md` | Five-axis code review | `cs-code-review`, `cs-shipping`; manual-only team workflows |
| Security Auditor | `.codebuddy/agents/cs-security-auditor.md` | Vulnerability detection | `cs-security`, `cs-shipping`; manual-only team workflows |
| Test Engineer | `.codebuddy/agents/cs-test-engineer.md` | Test strategy & coverage | `cs-tdd`, `cs-shipping`; manual-only team workflows |
| Web Perf Auditor | `.codebuddy/agents/cs-web-perf-auditor.md` | Core Web Vitals audit | `cs-perf-opt`, `cs-shipping`; manual-only team workflows |
| Knowledge Base Administrator | `.codebuddy/agents/cs-knowledge-base-admin.md` | Refresh existing project knowledge bases only | final subagent step of `/cs-build` and `cs-team-build` |

**Orchestration model:** Agents are invoked **by skills** (fan-out), not by user commands. `cs-team-build` and `cs-team-review` sequence multiple personas only after an explicit skill invocation or their approved commands (`/cs-team-coding`, `/cs-team-review`); intent routing must never auto-start either workflow.

`cs-knowledge-base-admin` is a low-cost final-step subagent for `/cs-build` and `cs-team-build`. It updates only existing `.codegraph/`, `.understand-anything/`, and `graphify-out/` directories and never creates a knowledge base. If none of the three exists, it terminates with a prerequisite message. Personas with an `Optional Skill Roster` may autonomously load only skills listed in their own roster; personas without that section follow only their explicitly assigned skill protocol.

## Core Operating Behaviors

1. **Surface Assumptions** — State assumptions before implementing
2. **Manage Confusion** — Stop and ask, don't guess
3. **Push Back** — Point out problems in approaches
4. **Enforce Simplicity** — Ask: can this be done in fewer lines?
5. **Scope Discipline** — Touch only what you're asked to touch
6. **Verify, Don't Assume** — Evidence required, "seems right" is not sufficient
7. **Defensive File Writing** — Before ANY `Write`/`Edit` to a new path:
   - Check if the parent directory exists (`list_dir` or `bash "test -d ..."`)
   - If missing: `bash "mkdir -p <parent_dir>"` FIRST, then write
   - Rationale: `write_to_file` does NOT auto-create parent directories;
     silent failures waste entire agent sessions (e.g., `design/gdd/` was
     referenced by 66 docs but didn't exist until 2026-07-03)

## Quick Reference

| Phase | Skill | Summary |
|-------|-------|---------|
| Meta | cs-using | Skill discovery and routing |
| Define | cs-interview-me | Extract what user actually wants |
| Define | cs-idea-refine | Structured divergent/convergent thinking |
| Define | grill-me | Stress-test design before committing |
| Define | cs-spec-driven | Requirements before code |
| Plan | cs-planning | Decompose into verifiable tasks |
| Manual only | cs-team-build | Explicit skill/command invocation: agent team implements a design doc |
| Manual only | cs-team-review | Explicit skill/command invocation: multi-agent review |
| Build | cs-incremental | Thin vertical slices |
| Build | cs-minimal | Minimal solution before writing code |
| Build | cs-tdd | Failing test first, then make it pass |
| Build | cs-context-eng | Right context at right time |
| Build | cs-source-driven | Verify against official docs |
| Build | cs-doubt-driven | Adversarial review of decisions |
| Build | cs-frontend-ui | Production-quality UI |
| Build | cs-api-design | Stable interfaces |
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
| SysDocs | cs-sysdocs-init | One-time full SysDocs generation |
| SysDocs | cs-sysdocs-update | Repair / incremental / rebuild-boundaries |
| SysDocs | cs-vibe-coding | Fragmentary change pre-design |

## SysDocs — System Project Documentation

`SysDocs/` is a project-documentation system (`SYSTEM_ROOT.md` + per-module docs) with three skills:

- `cs-sysdocs-init` — one-time full generation (UNINITIALIZED only)
- `cs-sysdocs-update` — the only maintenance entry (repair / incremental / rebuild-boundaries)
- `cs-vibe-coding` — fragmentary change pre-design, architect-reviewed

Shared templates + validator protocol live in `.codebuddy/references/sysdocs-*.md`. `SysDocs/` deploys on the consuming project's root.

## References

See `.codebuddy/references/` for checklists and detailed patterns:
- Definition of Done
- Testing Patterns
- Security Checklist
- Performance Checklist
- Accessibility Checklist
- Observability Checklist
- Orchestration Patterns
- SysDocs convention + overview/module/vibe templates
