---
name: cs-grill-me
model: DeepSeek-V4-Flash
description: "A relentless interview to sharpen a plan or design. Stress-tests assumptions, exposes blind spots, and hardens decisions before code or commitment. / 通过无情的提问来打磨计划或设计。压力测试假设，暴露盲点，在投入代码或承诺之前强化决策。"
---

# Grill Me — Relentless Interview

## Overview

Most failures come from an assumption that was never tested. This skill runs a structured grilling session — one question at a time — to surface hidden risks, gaps, and contradictions in a plan or design before you commit to it.

## When to Use

- A plan, spec, architecture, or design that feels "good enough" but hasn't been challenged
- A high-stakes decision where the cost of being wrong is high
- Before presenting a proposal to stakeholders
- The user explicitly invokes: "grill me", "grill this plan", "stress-test my design"
- Before a gate check or review meeting

**When NOT to use:** Trivial decisions, already-reviewed items, pure information requests, mechanical operations.

## The Process

### Step 1: Understand What to Grill

Ask the user to state or paste the plan/design/decision. If it's in a file, use Glob/Grep/Read to load it.

### Step 2: Hypothesize Weak Spots

Before asking anything, write your hypothesis of where the plan is weakest:

```
HYPOTHESIS: The timeline is aggressive given the dependency on Team X.
CONFIDENCE: ~40%
```

### Step 3: Ask One Question at a Time

Ask exactly one pointed question per turn. Wait for the user's answer before asking the next.

Focus areas (cycle through):
- **Assumptions**: What are you assuming that, if wrong, breaks everything?
- **Evidence**: What data supports this? What would change your mind?
- **Risks**: What's the worst that can happen? What's your mitigation?
- **Trade-offs**: What did you explicitly NOT do? What did you defer?
- **Timing**: Why now? What changes if you wait 3 months?
- **Stakeholders**: Who disagrees? Who hasn't been consulted?
- **Second order**: What happens after this succeeds? What breaks?

### Step 4: Pivot When Needed

If the user's answers reveal a deeper issue (wrong problem, wrong scope), shift focus. The goal is not to follow the script but to find the actual weakness.

### Step 5: Summarize Vulnerabilities

When you've hit the key issues (typically 3-5 rounds), summarize:

```
VULNERABILITIES FOUND:
1. [vulnerability with severity: HIGH/MEDIUM/LOW]
2. [vulnerability with severity]
3. [vulnerability with severity]

RECOMMENDATION: [one sentence on what to address first]
```

### Step 6: Confirm

Ask if the user wants to address the vulnerabilities now or proceed with awareness.

## Interaction with Other Skills

- `cs-interview-me`: upstream — clarifies what the user actually wants before a plan exists
- `cs-idea-refine`: upstream — generates variations before grilling a specific option
- `cs-spec-driven`: upstream — produces the spec that should be grilled before planning
- `cs-planning`: downstream — break the grilled-and-hardened design into tasks
- `cs-doubt-driven`: post-decision artifact review (grill the code/spec, not the plan)
- `/cs-plan` and `/cs-build`: workflow gates that require the resulting `## Grill Review` decision before planning or autonomous implementation

## Verification

- [ ] The plan/design was loaded or stated explicitly
- [ ] At least one hypothesis with confidence was written
- [ ] Questions asked one at a time (never more than one per turn)
- [ ] At least 3 focus areas were explored
- [ ] A vulnerability summary with severity was produced
- [ ] User confirmed next step (address now or proceed aware)
