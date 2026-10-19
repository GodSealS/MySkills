# Orchestration Patterns

> Ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)

## Layers

This project has three composable layers:

- **Skills** (`.codebuddy/skills/cs-*/SKILL.md`) — workflows with steps and exit criteria. The *how*.
- **Personas** (`.codebuddy/agents/cs-*.md`) — roles with a perspective and output format. The *who*.
- **AGENTS.md** — the skill discovery router. The *when*.

## Composition Rule

The user (or AGENTS.md intent mapping) is the orchestrator. A persona may invoke skills.
Persona dispatch is limited to two fixed pairs: `cs-frontend-lead` directs
`cs-cocos-specialist` for Cocos client work, and `cs-backend-lead` directs
`cs-network-programmer` for Cocos server work. Workers only execute approved work; each
assigning lead orders tasks, accepts results, requests rework and decides design changes. Use the installed
agent tool where available, otherwise the host relays the lead's brief and returns the result
to the assigning lead. Other persona orchestration stays with the host. Neither worker delegates.

Each lead's Cocos dispatch contract defines required inputs and decision handoffs.
For Cocos client/server implementation, the assigning lead first records the task breakdown and
externally exposed interface agreements in one authoritative plan file (normally
`tasks/plan.md`). It dispatches only tasks marked `READY` at an identified plan revision;
the worker reads that plan and returns missing or ambiguous contracts to its assigning lead.
Design/interface changes must be recorded in the plan before affected implementation resumes.
Each lead's Agent definition owns the TDD applicability decision and verification plan.
Workers follow that recorded decision and the plan's steps, returning gaps and execution
evidence to the lead for acceptance under the same dispatch contract.
The private Cocos engine bundle belongs only to `cs-cocos-specialist` and travels with its install;
`cs-network-programmer` uses its own execution skill roster. Client and server work share the
accepted protocol revision. Decisions beyond a lead's authority are resolved by the host with
the relevant owner, then communicated to the worker through its assigning lead. A read-only assignment stays
read-only, and this scoped dispatch does not activate a manual team workflow.

## Agent Families

Personas split into two families:

- **Build-side owners** (triggered by Define/Plan/Build skills):
  - `cs-architect` — architecture, module boundaries, ADRs (via `cs-spec-driven`, `cs-planning`)
  - `cs-frontend-lead` — frontend domain owner (via `cs-frontend-ui`, `cs-browser-test`, `cs-tdd`, frontend security/performance work, and `cs-incremental`)
  - `cs-cocos-specialist` — execution-only Cocos worker directed by `cs-frontend-lead`; private subsystem skills, no design decision authority
  - `cs-backend-lead` — backend domain owner (via `cs-api-design`, `cs-tdd`, backend security/performance work, and `cs-incremental`)
  - `cs-network-programmer` — execution-only Cocos game server worker directed by `cs-backend-lead`; no design decision authority
  - `cs-blender-operator` — host-dispatched Blender asset operator; five private skills for mesh, materials, textures, animation and camera work; no persona delegation
- **Review-side auditors** (triggered by Review/Ship skills):
  - `cs-code-reviewer`, `cs-review-advisor`, `cs-security-auditor`, `cs-test-engineer`, `cs-web-perf-auditor`

Regular owners and auditors are invoked **by skills**. The Cocos client/server workers are
assigned by their respective leads under the dispatch contracts above.
The host assigns Blender asset work directly to `cs-blender-operator`; this adds no new
persona-to-persona dispatch exception and does not activate a team workflow.

For concept-image assets, `cs-img2threejs` is public and may be invoked directly or loaded by
`cs-cocos-specialist` within its lead's approved plan. Generation/export produces a concrete
asset handoff; the host dispatches `cs-blender-operator` for isolated-vertex, broken-surface
and UV cleanup, then returns the repaired asset to the caller for integration. The skill's
`references/blender-handoff.md` owns the payload and evidence contract. The Cocos worker
does not delegate, and frontend design changes still require `cs-frontend-lead` adjudication.

## Endorsed Pattern: Parallel Fan-Out with Merge

`cs-team-build`, `cs-team-review` and `cs-team-refactor` are the sanctioned team skills that sequence multiple personas. They issue fan-outs from the skill layer; the two scoped Cocos dispatch pairs above are the only persona-to-persona exceptions.

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

Ordinary build work stays with the host. A new or materially changed architectural
boundary can justify one focused architect consultation; accepted unchanged ADRs are reused.
Delegate a concrete independent slice only when useful and authorized, or when an explicit
team workflow requires it. Owner tags describe responsibility rather than mandating a spawn.
Cross-domain work remains one end-to-end slice unless an independent/shared contract must
land first. Pass only task-specific evidence and gaps to the delegated role.

For `/cs-build`, the host checks for an existing knowledge base and changed indexed source
before the final refresh. Defer refresh until all planned slices complete; when neither
condition applies, skip without spawning an administrator. Explicit team workflows retain
their own final-step contract.

## Anti-Patterns

- **Router Persona:** General persona selection belongs to AGENTS.md intent mapping; the two leads' fixed Cocos workers are the scoped exceptions above.
- **Chain of Personas:** Keep Cocos dispatch to each lead and its assigned execution-only worker; other multi-role sequencing belongs to the host/skills.
- **Persona Override of User Intent:** A persona should never make orchestration decisions without user approval.

## Persona Resolution

If you define custom agents in `.codebuddy/agents/`, they take precedence over the plugin-provided agent-skills personas. This allows customization while keeping the plugin as a fallback.
