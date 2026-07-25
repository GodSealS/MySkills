# Orchestration Patterns

> Ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)

## Layers

This project has three composable layers:

- **Skills** (`.codebuddy/skills/cs-*/SKILL.md`) — workflows with steps and exit criteria. The *how*.
- **Personas** (`.codebuddy/agents/cs-*.md`) — roles with a perspective and output format. The *who*.
- **AGENTS.md** — the skill discovery router. The *when*.

## Composition Rule

The user (or AGENTS.md intent mapping) is the orchestrator. Personas do not invoke other personas. A persona may invoke skills.

## Endorsed Pattern: Parallel Fan-Out with Merge

Used by `cs-shipping` to run `cs-code-reviewer`, `cs-security-auditor`, and `cs-test-engineer` concurrently:

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

## Anti-Patterns

- **Router Persona:** Do not build a persona that decides which other persona to call. That's the job of AGENTS.md intent mapping.
- **Chain of Personas:** Persona A calling Persona B calling Persona C. Use skills instead.
- **Persona Override of User Intent:** A persona should never make orchestration decisions without user approval.

## Persona Resolution

If you define custom agents in `.codebuddy/agents/`, they take precedence over the plugin-provided agent-skills personas. This allows customization while keeping the plugin as a fallback.
