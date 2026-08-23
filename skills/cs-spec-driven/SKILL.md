---
name: cs-spec-driven
model: DeepSeek-V4-Pro
description: "Creates specs before coding. Use when starting a new project, feature, or significant change and no specification exists yet. Use when requirements are unclear, ambiguous, or only exist as a vague idea. / 编码前先创建规范。用于启动新项目、新功能或重大变更且尚无规范时——需求不明确、模糊或仅作为粗略想法存在时（SPECIFY→PLAN→TASKS→IMPLEMENT）。"
---

# Spec-Driven Development

## Overview

Write a structured specification before writing any code. The spec is the shared source of truth between you and the human engineer — it defines what we're building, why, and how we'll know it's done. Code without a spec is guessing.

## When to Use

- Starting a new project or feature
- Requirements are ambiguous or incomplete
- The change touches multiple files or modules
- You're about to make an architectural decision
- The task would take more than 30 minutes to implement

**When NOT to use:** Single-line fixes, typo corrections, or changes where requirements are unambiguous and self-contained.

## The Gated Workflow

```
SPECIFY ──→ PLAN ──→ TASKS ──→ IMPLEMENT
   │          │        │          │
   ▼          ▼        ▼          ▼
 Human      Human    Human      Human
 reviews    reviews  reviews    reviews
```

### Phase 1: Specify

Start with a high-level vision. Ask the human clarifying questions until requirements are concrete.

**Surface assumptions immediately:**

```
ASSUMPTIONS I'M MAKING:
1. This is a web application (not native mobile)
2. Authentication uses session-based cookies (not JWT)
3. The database is PostgreSQL (based on existing Prisma schema)
4. We're targeting modern browsers only (no IE11)
→ Correct me now or I'll proceed with these.
```

**Write a spec document covering six core areas:**

1. **Objective** — What are we building and why?
2. **Commands** — Full executable commands with flags
3. **Project Structure** — Where source code, tests, docs live
4. **Code Style** — One real code snippet showing style
5. **Testing Strategy** — Framework, location, coverage expectations
6. **Boundaries** — Always/Ask First/Never rules

**Architecture Fan-Out:** After the human approves the objective, **FAN-OUT to `cs-architect`** (via `Task`) to produce the architecture: module boundaries, dependency direction, tech stack, and an ADR for each significant decision (written via `cs-docs-adrs` to `docs/adr/`). The architect's output is a required input for the spec's Project Structure section.

**Spec template:**

```markdown
# Spec: [Project/Feature Name]

## Objective
[What we're building and why. User stories or acceptance criteria.]

## Tech Stack
[Framework, language, key dependencies with versions]

## Commands
[Build, test, lint, dev — full commands]

## Project Structure
[Directory layout with descriptions]

## Code Style
[Example snippet + key conventions]

## Testing Strategy
[Framework, test locations, coverage requirements]

## Boundaries
- Always: [...]
- Ask first: [...]
- Never: [...]

## Success Criteria
[How we'll know this is done]

## Open Questions
[Anything unresolved that needs human input]

## Grill Review
- Status: pending
- Findings: [Run `/grill-me SPEC.md` and summarize the vulnerabilities, or explicitly record a skip decision.]
- Decision: [Address now / proceed with accepted risks / skipped with accepted risks]
```

### Phase 2: Plan

> Follow `cs-planning` for the full dependency-graph and vertical-slicing mechanics.

### Phase 3: Tasks

> Follow `cs-planning` for task-sizing and dependency-ordering mechanics.

### Phase 4: Implement

Execute tasks one at a time following `cs-incremental` and `cs-tdd`.

## Grill Review Gate

Before invoking `cs-planning`, run `/grill-me <spec-path>` and replace the `pending` Grill Review entry with the vulnerabilities found and the user's decision. A review may be skipped only when the spec explicitly records the accepted risks.

## Keeping the Spec Alive

- **Update when decisions change**
- **Update when scope changes**
- **Commit the spec** alongside code
- **Reference the spec in PRs**

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This is simple, I don't need a spec" | Simple tasks need acceptance criteria. A two-line spec is fine. |
| "I'll write the spec after I code it" | That's documentation, not specification. |
| "The spec will slow us down" | A 15-minute spec prevents hours of rework. |
| "Requirements will change anyway" | An outdated spec is still better than no spec. |

## Red Flags

- Starting to write code without any written requirements
- Asking "should I just start building?" before clarifying "done"
- Implementing features not mentioned in any spec or task list
- Skipping the spec because "it's obvious what to build"

## Interaction with Other Skills

- `cs-interview-me`: upstream — extracts what the user actually wants before specifying
- `cs-idea-refine`: upstream — generates and refines options before writing a spec
- `grill-me`: required gate before planning — stress-test the spec, then record the findings and decision in `## Grill Review`
- `cs-architect` (agent): fan-out after the objective is approved — produces module boundaries, dependency direction, tech stack, and ADRs (via `cs-docs-adrs`, stored in `docs/adr/`)
- `cs-planning`: downstream — break the spec into verifiable tasks

## Verification

- [ ] The spec covers all six core areas
- [ ] The human has reviewed and approved the spec
- [ ] Architecture fan-out to `cs-architect` completed and ADRs recorded (see `cs-docs-adrs`)
- [ ] `## Grill Review` records completed findings and a decision, or an explicit skip with accepted risks
- [ ] Success criteria are specific and testable
- [ ] Boundaries (Always/Ask First/Never) are defined
- [ ] The spec is saved to a file in the repository
