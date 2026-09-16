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
  - `cs-code-reviewer`, `cs-review-advisor`, `cs-security-auditor`, `cs-test-engineer`, `cs-web-perf-auditor`

Both families are invoked **by skills** — never by user slash commands directly.

## Endorsed Pattern: Parallel Fan-Out with Merge

`cs-team-build`, `cs-team-review` and `cs-team-refactor` are the sanctioned skills that sequence multiple personas. They issue fan-outs from the skill layer; personas never invoke one another.

All three team workflows remain manual-only. The host executes their protocol and is not bound to any persona. Team Refactor reads an existing project and writes only its `Idea/` proposal and `tasks/` evidence; it neither changes target code nor invokes Team Build/Review. `cs-architect` retains Team Build decomposition, structural implementation and architecture consultation; in Team Refactor it proposes architecture and migration tasks without writing accepted ADRs. `cs-code-reviewer` retains the independent five-axis code first pass. `cs-review-advisor` proposes classification/assignment, reviews plans/designs, and gives focused recommendations and synthesis; these proposals do not grant orchestration or adjudication authority. Its private resources belong only to that role and are not public skills or another persona's roster.

The host sends advice to relevant experts for fresh detection with itemized fully/partly/not acceptable conclusions. If a rejected part remains blocking in the advisor's view, immediately open user choice and pause dependent operations as pending-human; without dialog support ask directly and wait. Keep advice acceptance, finding confirmation and actual repair verification separate. Only completed repair plus expert verification supports closure; user choices are not repair evidence. Team Refactor only confirms findings and plan advice; implementation repair is downstream. Architecture questions return through the host to `cs-architect`; fact conflicts retain human resolution. Team Review repairs require a new linked run, preserving the old run. New runs identify `review-advisor-v1` and the source protocol; legacy runs retain their recorded protocol or are preserved while a new run starts.

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
