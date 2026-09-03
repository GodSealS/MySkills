# Agent-Skills — Universal Router

This is a multi-platform prompt pack of engineering workflow skills, ported from
[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT). It installs to
**Codex**, **CodeBuddy**, and **Gemini CLI** from a single source of truth (`.codebuddy/`).

## How skills are discovered

Skills are plain Markdown. Each platform reads them from its own location, but they are all
generated from `.codebuddy/skills/<name>/SKILL.md`:

| Platform   | Skill location                          | Slash commands            | Router / context file |
|------------|------------------------------------------|---------------------------|-----------------------|
| Codex      | `.agents/skills/<name>/SKILL.md`         | `.codex/prompts/<n>.md`   | `AGENTS.md` (this file) |
| CodeBuddy  | `.codebuddy/skills/<name>/SKILL.md`      | `.codebuddy/commands/*.md`| `.codebuddy/AGENTS.md` |
| Gemini CLI | `.gemini/skills/<name>/SKILL.md`         | `.gemini/commands/<n>.toml`| `GEMINI.md`          |

Reference a skill by its `name` (all are `cs-` prefixed, e.g. `cs-spec-driven`).

## Intent → skill mapping

Identify the development phase of the incoming task, then apply the matching skill.

**Define** (clarify the problem before building)
- `cs-interview-me` — extract what the user actually wants via one-question-at-a-time interview
- `cs-idea-refine` — refine a vague idea into a sharp, actionable concept
- `cs-grill-me` — stress-test an existing plan/spec/design with adversarial questions
- `cs-spec-driven` — write a structured spec before coding (SPECIFY→PLAN→TASKS→IMPLEMENT)

**Plan**
- `cs-planning` — break work into ordered, verifiable tasks

**Build**
- `cs-incremental` — deliver changes in small, working vertical slices
- `cs-tdd` — drive implementation with tests (RED→GREEN→REFACTOR)
- `cs-context-eng` — optimize agent context setup
- `cs-source-driven` — ground every decision in official docs
- `cs-doubt-driven` — adversarial review of non-trivial decisions
- `cs-frontend-ui` — build production-quality UI
- `cs-api-design` — design stable APIs and interfaces
- `cs-team-build` — implement a design document through a coordinated agent team

**Verify**
- `cs-browser-test` — test in a real browser via DevTools
- `cs-debugging` — systematic root-cause debugging

**Review**
- `cs-code-review` — five-axis code review (correctness, readability, architecture, security, performance)
- `cs-simplify` — simplify code for clarity without changing behavior
- `cs-security` — harden against vulnerabilities
- `cs-perf-opt` — optimize performance / Core Web Vitals

**Ship**
- `cs-git-workflow` — structure git workflow
- `cs-cicd` — automate CI/CD pipelines
- `cs-deprecation` — manage deprecation and migration
- `cs-docs-adrs` — record decisions and documentation
- `cs-observability` — instrument code for production visibility
- `cs-shipping` — prepare production launches

**Meta / utility**
- `cs-using` — discover and invoke the right skill (start here)
- `cs-code-query` — route code questions to a project knowledge graph
- `cs-agent-brief-review` — review an agent brief for readiness
- `cs-skill-review` — review a skill for predictability

## Personas (agents/)

| Agent | Role | Use when | Invoked by (skill fan-out) |
|-------|------|----------|-----------------------------|
| cs-architect | System Architect | module boundaries, dependency direction, tech stack, ADRs | cs-spec-driven, cs-planning, cs-team-build |
| cs-frontend-lead | Frontend Lead | UI implementation, state, browser verification | frontend-owned cs-incremental, cs-frontend-ui, cs-browser-test, cs-tdd, security, performance, cs-team-build |
| cs-backend-lead | Backend Lead | API implementation, data layer, server security/perf | backend-owned cs-incremental, cs-api-design, cs-tdd, security, performance, cs-team-build |
| cs-code-reviewer | Senior Staff Engineer | five-axis code review | cs-code-review, cs-shipping, cs-team-build |
| cs-security-auditor | Security Engineer | vulnerability detection, threat modeling | cs-security, cs-shipping, cs-team-build |
| cs-test-engineer | QA Specialist | test strategy, coverage analysis | cs-tdd, cs-shipping, cs-team-build |
| cs-web-perf-auditor | Web Perf Engineer | Core Web Vitals audit | cs-perf-opt, cs-shipping, cs-team-build |

Personas may invoke skills, but do not invoke other personas — only the user (or this router) orchestrates. Agents are triggered **by skills** (fan-out) when their owning skill enters the relevant phase — no user command needed.

## Process

1. Classify the task into a phase using the mapping above.
2. Load the matching skill (`skills/<name>/SKILL.md`) and follow its Process section.
3. Never skip the skill's Verification step — "seems right" is never sufficient.
4. Cross-reference existing skills instead of duplicating content.
