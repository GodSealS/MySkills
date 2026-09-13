# Orchestration Patterns

> Ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)

## Layers

This project has three composable layers:

- **Skills** (`.codebuddy/skills/cs-*/SKILL.md`) — workflows with steps and exit criteria. The *how*.
- **Personas** (`.codebuddy/agents/cs-*.md`) — roles with a perspective and output format. The *who*.
- **AGENTS.md** — the skill discovery router. The *when*.

## Composition Rule

The user (or AGENTS.md intent mapping) is the orchestrator. Personas do not invoke other personas. A persona may invoke skills.

## Agent Families

Personas split into two families:

- **Build-side owners** (triggered by Define/Plan/Build skills):
  - `cs-architect` — architecture, module boundaries, ADRs (via `cs-spec-driven`, `cs-planning`)
  - `cs-frontend-lead` — frontend domain owner (via `cs-frontend-ui`, `cs-browser-test`, `cs-tdd`, frontend security/performance work, and `cs-incremental`)
  - `cs-backend-lead` — backend domain owner (via `cs-api-design`, `cs-tdd`, backend security/performance work, and `cs-incremental`)
- **Review-side auditors** (triggered by Review/Ship skills):
  - `cs-code-reviewer`, `cs-security-auditor`, `cs-test-engineer`, `cs-web-perf-auditor`

Both families are invoked **by skills** — never by user slash commands directly.

## Endorsed Pattern: Parallel Fan-Out with Merge

`cs-team-build` and `cs-team-review` are the sanctioned skills that sequence multiple personas. Both issue fan-outs from the skill layer; personas never invoke one another.

Used by `cs-shipping` and `cs-team-review` to run specialist personas concurrently:

```
User invokes cs-shipping
    │
    ├── Spawn cs-code-reviewer     (parallel)
    ├── Spawn cs-security-auditor  (parallel)
    └── Spawn cs-test-engineer     (parallel)
            │
            ▼
    Main agent merges all three reports
            │
            ▼
    GO / NO-GO decision with rollback plan
```

The same pattern drives the build side:

```
cs-spec-driven (after objective approved)
    │
    └── Spawn cs-architect → ADRs → docs/adr/

cs-incremental (per end-to-end slice, by primary owner)
    ├── frontend primary → Spawn cs-frontend-lead
    ├── backend primary  → Spawn cs-backend-lead
    └── arch primary     → Spawn cs-architect
```

Cross-domain work remains one end-to-end slice with a primary owner and optional collaborator. Contract-first ordering applies only when a contract is independently delivered, shared, or needed before parallel frontend work.

## Anti-Patterns

- **Router Persona:** Do not build a persona that decides which other persona to call. That's the job of AGENTS.md intent mapping.
- **Chain of Personas:** Persona A calling Persona B calling Persona C. Use skills instead.
- **Persona Override of User Intent:** A persona should never make orchestration decisions without user approval.

## Persona Resolution

If you define custom agents in `.codebuddy/agents/`, they take precedence over the plugin-provided agent-skills personas. This allows customization while keeping the plugin as a fallback.
