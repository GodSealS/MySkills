---
name: cs-agent-brief-review
model: gpt-5.6-terra
description: 审查 Agent Brief 的质量——按持久性、行为驱动、验收标准、范围边界四轴诊断。Use when reviewing an agent brief, issue spec, PR description for an AFK agent, or when asked to evaluate whether a task spec is agent-ready.
---

# Agent Brief Review

Read the target agent brief (GitHub issue body, PR description, or task spec meant for an AFK agent), then run this review. Every finding traces to the principles in [AGENT-BRIEF.md](F:\Tools\skills\skills\engineering\triage\AGENT-BRIEF.md).

An agent brief is the authoritative specification an AFK agent works from. The original discussion is context — the brief is the contract. A good brief answers one question completely: **can an agent with no prior context read this and produce the right change?**

## Step 1 — Durability Audit

Check whether the brief will survive a changing codebase. The brief may sit in a queue for days or weeks while files move.

**Red flags:**
- File paths (`src/triage/handler.ts`)
- Line numbers (`around line 150`, `on line 42`)
- Assumptions about current implementation structure ("the switch statement in the main handler")

**Green flags:**
- Type names and function signatures (`SkillMetadata`, `triage list --json`)
- Behavioral contracts ("When a user runs `/triage` with no arguments…")
- Config shapes and interface descriptions

For each red flag, suggest the durable replacement. For example: `src/triage/handler.ts` → "the command handler registered for `/triage`".

Findings: tag `durability-ok` or `durability-fragile`. For fragile items, state the durable alternative.

## Step 2 — Behavioral Purity Check

The brief should describe **what** the system should do, not **how** to implement it. The agent will explore the codebase fresh.

**Good** (behavioral):
- "The `SkillConfig` type should accept an optional `schedule` field of type `CronExpression`"
- "When a user runs `/triage` with no arguments, they should see a summary of issues needing attention"

**Bad** (procedural):
- "Open src/types/skill.ts and add a schedule field on line 42"
- "Add a switch statement in the main handler function"

Flag any procedural instructions. For each, rewrite as a behavioral statement.

Findings: tag `behavioral-ok` or `procedure-leak`. For leaks, provide the behavioral rewrite.

## Step 3 — Acceptance Criteria Quality

Every agent brief must have concrete, testable acceptance criteria. Each criterion must be independently verifiable — the agent can tell done from not-done without ambiguity.

**Sharp** (checkable):
- "Running `gh issue list --label needs-triage` returns issues that have been through initial classification"
- "Descriptions over 1024 chars are truncated at the last word boundary before 1024 chars"
- "Default (non-JSON) output is byte-for-byte unchanged"

**Vague** (uncheckable):
- "Triage should work correctly"
- "The output should look good"
- "Performance should be acceptable"

Rate every criterion: `sharp` or `vague`. For vague criteria, suggest a checkable rewrite.

Also check: are there _enough_ criteria? A bug brief typically needs 3-5 criteria (happy path + edge cases + error handling). An enhancement brief needs criteria covering the new behavior plus any non-regression on existing paths.

Findings: tag each criterion `ac-sharp` or `ac-vague`. State if the set is `ac-complete` or `ac-gap` (missing coverage — name what's missing).

## Step 4 — Scope Boundary Check

State what is **out of scope** explicitly. Missing boundaries invite the agent to gold-plate, make assumptions about adjacent features, or waste time on work the brief never asked for.

**Checklist:**
- [ ] Is there an explicit "Out of scope" section?
- [ ] Does it exclude adjacent features that could plausibly be confused with the task?
- [ ] Does it exclude real implementation temptations (e.g., "don't add `--json` to other commands" when adding it to one)?
- [ ] Are the boundaries concrete ("Bug reports only" → not specific enough; "Only enhancement rejections go to `.out-of-scope/`" → specific)?

Findings: tag `scope-ok`, `scope-missing` (no section at all), or `scope-gap` (section exists but misses key exclusions). For gaps, name what should be excluded.

## Step 5 — Structural Completeness

A well-formed agent brief has six required elements:

| Element | Present? | Quality |
|---|---|---|
| **Category** | bug / enhancement / refactor | Must be explicit |
| **Summary** | One-line description | Must be self-contained |
| **Current behavior** | What happens now | Must describe the baseline — for bugs, the broken behavior; for enhancements, the status quo |
| **Desired behavior** | What should happen after | Must cover edge cases and error conditions |
| **Key interfaces** | Types, signatures, config shapes affected | Must be durable (Step 1) |
| **Acceptance criteria** | Testable completion conditions | Must be sharp and complete (Step 3) |
| **Out of scope** | Explicit exclusions | Must be present and concrete (Step 4) |

## Step 6 — PR Brief Special Case

If the brief targets a PR (finish or fix an existing diff), apply additional checks:

- **Current behavior = state of the diff**, not the pre-PR codebase. Describe what the PR already does and what gaps remain.
- **Desired behavior = what the merged diff should do**, not a from-scratch spec.
- **Key interfaces** should reference what the PR already introduced — "reuse the existing serializer the PR already added; don't introduce a second one."

Flag PR briefs that read like from-scratch issues rather than diff-aware instructions.

## Output

Produce a review report:

```
## Agent Brief Review: <brief-identifier>

### Verdict
`agent-ready` | `needs-revision` | `not-agent-ready`
One-line summary of the biggest gap.

### Durability
- [ok/fragile] finding → durable alternative

### Behavioral Purity
- [ok/leak] finding → behavioral rewrite

### Acceptance Criteria
- [sharp/vague] "criterion text" → rewrite (if vague)
- Overall: [complete/gap] — missing: <what>

### Scope Boundaries
- [ok/missing/gap] finding → suggested exclusion

### Structural Completeness
- [present/missing] Category
- [present/missing] Summary
- [present/missing] Current behavior
- [present/missing] Desired behavior
- [present/missing] Key interfaces
- [present/missing] Acceptance criteria
- [present/missing] Out of scope

### PR-Specific (if applicable)
- [ok/issue] finding
```

Every gap gets a concrete fix. A brief that passes all checks is `agent-ready` — celebrate that, don't force-find problems.
