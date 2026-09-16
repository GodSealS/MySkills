# Agent-Skills for CodeBuddy

This is the **agent-skills** collection — production-grade engineering skills for AI coding agents, ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT License).

Skills encode the workflows, quality gates, and best practices that senior engineers use when building software. They cover the full development lifecycle: Define → Plan → Build → Verify → Review → Ship.

## Project Structure

```
.codebuddy/
├── agents/                   → 9 reusable specialist personas
│   ├── cs-architect.md           (build-side: architecture, ADRs)
│   ├── cs-frontend-lead.md       (build-side: frontend domain owner)
│   ├── cs-backend-lead.md        (build-side: backend domain owner)
│   ├── cs-code-reviewer.md
│   ├── cs-review-advisor.md     (advice only; experts recheck)
│   ├── cs-review-advisor/       (private Ponytail resources, not public skills)
│   ├── cs-security-auditor.md
│   ├── cs-test-engineer.md
│   ├── cs-web-perf-auditor.md
│   └── cs-knowledge-base-admin.md
├── skills/                   → Core skills (SKILL.md per directory)
│   ├── cs-using/        Meta: skill discovery
│   ├── cs-interview-me/ Define
│   ├── cs-idea-refine/  Define
│   ├── grill-me/        Define: stress-test an existing plan, spec, or design
│   ├── cs-spec-driven/  Define
│   ├── cs-planning/     Plan
│   ├── cs-incremental/  Build
│   ├── cs-tdd/          Build
│   ├── cs-context-eng/  Build
│   ├── cs-source-driven/Build
│   ├── cs-doubt-driven/ Build
│   ├── cs-frontend-ui/  Build
│   ├── cs-api-design/   Build
│   ├── cs-team-build/   Build
│   ├── cs-team-review/  Review
│   ├── cs-minimal/      Build
│   ├── cs-browser-test/ Verify
│   ├── cs-debugging/    Verify
│   ├── cs-code-review/  Review
│   ├── cs-simplify/     Review
│   ├── cs-security/     Review
│   ├── cs-perf-opt/     Review
│   ├── cs-git-workflow/ Ship
│   ├── cs-cicd/         Ship
│   ├── cs-deprecation/  Ship
│   ├── cs-docs-adrs/    Ship
│   ├── cs-observability/Ship
│   ├── cs-shipping/     Ship
│   ├── cs-sysdocs-init/   SysDocs: one-time full doc generation
│   ├── cs-sysdocs-update/ SysDocs: affected updates / repair / explicit migration or rebuild
│   └── cs-vibe-coding/  SysDocs: fragmentary change pre-design
├── commands/                 → 10 slash commands (orchestration layer)
│   ├── cs-spec.md
│   ├── cs-plan.md
│   ├── cs-build.md
│   ├── cs-team-coding.md
│   ├── cs-test.md
│   ├── cs-review.md
│   ├── cs-webperf.md
│   ├── cs-code-simplify.md
│   └── cs-ship.md
├── hooks/                    → Session lifecycle hooks
│   ├── cs-session-start.sh
│   ├── cs-sdd-cache-pre.sh
│   ├── cs-sdd-cache-post.sh
│   └── cs-simplify-ignore.sh
├── references/               → Supplementary checklists
│   ├── cs-definition-of-done.md
│   ├── cs-testing-patterns.md
│   ├── cs-security-checklist.md
│   ├── cs-performance-checklist.md
│   ├── cs-accessibility-checklist.md
│   ├── cs-observability-checklist.md
│   ├── cs-orchestration-patterns.md
│   ├── sysdocs-system.md
│   ├── sysdocs-overview-template.md
│   ├── sysdocs-module-template.md
│   ├── sysdocs-files-template.md
│   ├── sysdocs-flow-template.md
│   └── sysdocs-vibe-template.md
├── AGENTS.md                 → Skill discovery router and intent mapping
├── settings.json             → Hook registration and permissions
└── CODEBUDDY.md              → This file
```

## Skills by Phase

**Define:** cs-interview-me, cs-idea-refine, grill-me, cs-spec-driven
**Plan:** cs-planning
**Build:** cs-incremental, cs-minimal, cs-tdd, cs-context-eng, cs-source-driven, cs-doubt-driven, cs-frontend-ui, cs-api-design
**Verify:** cs-browser-test, cs-debugging
**Review:** cs-code-review, cs-simplify, cs-security, cs-perf-opt
**Manual only:** cs-team-build (explicit skill or `/cs-team-coding`), cs-team-review (explicit skill or `/cs-team-review`)
**Ship:** cs-git-workflow, cs-cicd, cs-deprecation, cs-docs-adrs, cs-observability, cs-shipping
**SysDocs:** cs-sysdocs-init, cs-sysdocs-update, cs-vibe-coding

## How Skills Work

Every skill follows a consistent anatomy:

```
┌─ Frontmatter ───────────────────────────────┐
│ name: cs-xxx                      │
│ description: Guides agents through [task].  │
│              Use when…                      │
│ argument-hint: "[hint for arguments]"       │
│ user-invocable: true                        │
│ allowed-tools: Read, Glob, Grep, ...        │
│ agent: cs-code-reviewer           │
└─────────────────────────────────────────────┘
│ Overview         → What this skill does     │
│ When to Use      → Triggering conditions    │
│ Process          → Step-by-step workflow    │
│ Rationalizations → Excuses + rebuttals      │
│ Red Flags        → Signs something's wrong  │
│ Verification     → Evidence requirements    │
└─────────────────────────────────────────────┘
```

**Key design choices:**

- **Process, not prose.** Skills are workflows with steps, checkpoints, and exit criteria.
- **Anti-rationalization.** Every skill includes common excuses agents use to skip steps with documented counter-arguments.
- **Verification is non-negotiable.** Every skill ends with evidence requirements. "Seems right" is never sufficient.
- **Progressive disclosure.** Main SKILL.md is the entry point. Supporting references load only when needed.

## Skill Discovery

CodeBuddy discovers and activates skills based on `AGENTS.md` intent mapping. When a task arrives, the agent identifies the development phase and applies the corresponding skill. See `AGENTS.md` for the full discovery flowchart.

## Agent Personas

| Agent | Role | Use When | Invoked by (skill fan-out) |
|-------|------|----------|-----------------------------|
| cs-architect | System Architect | Module boundaries, dependency direction, tech stack, ADRs | cs-spec-driven, cs-planning, cs-sysdocs-init, cs-sysdocs-update, cs-vibe-coding; manual-only team workflows |
| cs-frontend-lead | Frontend Lead | UI implementation, state, browser verification | frontend-owned build skills; manual-only team workflows |
| cs-backend-lead | Backend Lead | API implementation, data layer, server security/perf | backend-owned build skills; manual-only team workflows |
| cs-code-reviewer | Senior Staff Engineer | Five-axis code review | cs-code-review, cs-shipping; manual-only team workflows |
| cs-review-advisor | Review Advisor | Design review and focused recommendations verified by experts | explicit review assignment; manual-only team workflows |
| cs-security-auditor | Security Engineer | Vulnerability detection, threat modeling | cs-security, cs-shipping; manual-only team workflows |
| cs-test-engineer | QA Specialist | Test strategy, coverage analysis | cs-tdd, cs-shipping; manual-only team workflows |
| cs-web-perf-auditor | Web Perf Engineer | Core Web Vitals audit | cs-perf-opt, cs-shipping; manual-only team workflows |
| cs-knowledge-base-admin | Knowledge Base Administrator | Refresh existing project knowledge bases only | final subagent step of `/cs-build` and `cs-team-build` |

Personas follow the composition rule: **only the user (or AGENTS.md intent mapping) is the orchestrator. Personas do not invoke other personas.** A persona may invoke skills. **Agents are triggered by skills** (fan-out) when their owning skill enters the relevant phase. `cs-team-build` and `cs-team-review` are sanctioned multi-persona orchestrators, but are manual-only: explicit skill invocation or `/cs-team-coding` / `/cs-team-review` is required.

`cs-knowledge-base-admin` uses the lowest-cost model tier and runs only as the final subagent of `/cs-build` or `cs-team-build`. It refreshes existing `.codegraph/`, `.understand-anything/`, and `graphify-out/` directories without creating a knowledge base. If none exists, it terminates with a prerequisite message. Personas with an `Optional Skill Roster` may autonomously load only skills listed in their own roster.

## Conventions

- Every skill lives in `skills/cs-<name>/SKILL.md`
- CodeBuddy frontmatter with `name`, `description`, `argument-hint`, `user-invocable`, `allowed-tools`, `agent`
- Description starts with what the skill does (third person), followed by trigger conditions ("Use when...")
- Every skill has: Overview, When to Use, Process, Common Rationalizations, Red Flags, Verification
- References are in `references/`, not inside skill directories
- Cross-references use the target skill's declared name, such as `cs-xxx` or `grill-me`
- Agent personas have: `thinkingLevel`, `name`, `description`, `tools`, `model`, `maxTurns`, `agentMode`, `subagent`, `enabled`, `enabledAutoRun`

## SysDocs — System Project Documentation

The pack ships a project-documentation system (`SysDocs/`) plus three skills:
`cs-sysdocs-init` (one-time full generation), `cs-sysdocs-update` (the only
maintenance entry: affected updates / repair / explicit migration or rebuild), and
`cs-vibe-coding` (fragmentary pre-design, also without an initialized library). Schema 2
uses README, architecture, files, applicable specs/decisions and proposal directories.
Header summaries list key classes/structures with one-sentence responsibilities;
KB and documentation candidates are combined and verified against source. Legacy
layouts remain readable until explicit migration. The shared
templates and validator protocol live in `references/sysdocs-*.md`. `SysDocs/`
deploys on the consuming project's root, not this skill-pack repo.

## Coexistence with CodeSquad

This `.codebuddy/cs-*/` directory coexists with `.codesquad/`:

- `.codesquad/` → Game development specialists (UE/Unity/Godot/Cocos)
- `.codebuddy/cs-*/` → General software engineering best practices

Both systems are active simultaneously. Skills from both directories are available to CodeBuddy.

## Boundaries

- Always: Reference existing skills before duplicating content
- Always: Follow the skill anatomy format for consistency
- Always: Include Common Rationalizations and Verification sections
- Never: Add skills that are vague advice instead of actionable processes
- Never: Duplicate content between skills — reference instead

---

> Ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT License) on 2026-07-02.
> Original author: Addy Osmani
> Platform adaptation: Claude Code → CodeBuddy
