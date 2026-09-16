---
name: cs-interview-me
description: "Extracts what the user actually wants instead of what they think they should want. Achieves this through one-question-at-a-time interview until ~95% confidence. Use when an ask is underspecified, when the user invokes 'interview me', or when you catch yourself silently filling in ambiguous requirements. Use grill-me instead when an existing plan, spec, or design needs stress-testing. / 通过一问一答式访谈提取用户真实需求（非表面需求）。用于需求不明确、用户要求\"面试我\"、或发现自己在填补模糊需求时；已有计划、规范或设计需要压力测试时改用 grill-me。"
argument-hint: "[project or idea to clarify]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
agent: cs-code-reviewer
---

# Interview Me

## Overview

What people ask for and what they actually want are different things. The cheapest moment to find this gap is before any plan, spec, or code exists.

## When to Use

- The ask is missing at least one of: who, why, what success looks like, binding constraint
- The request is conventional rather than specific
- You're tempted to start with assumptions you haven't surfaced
- The user explicitly invokes: "interview me"
- No concrete plan, spec, or design artifact exists yet

**Routing boundary:** If the user provides an existing plan, spec, or design and asks to challenge it, invoke `grill-me` instead.

**When NOT to use:** Unambiguous asks, pure information requests, mechanical operations.

## The Process

### Step 0: Read SysDocs Context

Before forming the hypothesis or asking questions, follow `../../references/sysdocs-design-context.md`: read relevant accepted specs/ADRs, then active-layout navigation/summaries and necessary bodies; verify key facts with source and record necessary gaps. Use documented users, capabilities and constraints to focus questions on unresolved intent and requested changes, without forcing whole-library initialization.

### Step 1: Hypothesize with a Confidence Number

Before asking anything, write your best read in one sentence with an honest confidence number (0-100%):

```
HYPOTHESIS: You want a way to answer "how are we doing?" in standup.
CONFIDENCE: ~30% — missing: who it's for, what "metrics" are, and what success looks like
```

### Step 2: Ask One Question at a Time, Each with a Guess Attached

```
Q: [one focused question]
GUESS: [your hypothesis with reasoning]
```

Wait for the user to react before asking the next question. Why one at a time: the third question often depends on the answer to the first. Why attach a guess: the user reacts faster to a wrong guess than generates from scratch.

### Step 3: Listen for "Want vs. Should Want"

Watch for answers that pattern-match best-practice talk without specifics. When you hear these, ask: *"If you didn't have to justify this to anyone, what would you actually want?"*

### Step 4: Restate Intent in the User's Own Words

When confidence is high:
```
Here's what I now think you want:
- Outcome: [one line]
- User: [one line — who benefits]
- Why now: [one line — what changed]
- Success: [one line — how we know]
- Constraint: [one line — binding limit]
- Out of scope: [one line — explicitly not doing]

Yes / no / refine?
```

### Step 5: Confirm — Explicit Yes Required

The following are NOT yes: "Whatever you think is best", "Sounds good", "Sure, let's go." Loop until explicit yes.

### The 95% Confidence Stop

You're done when you can answer yes to: *Can I predict the user's reaction to the next three questions I would ask?*

## Interaction with Other Skills

- `cs-idea-refine`: downstream, generates variations from confirmed intent
- `cs-spec-driven`: downstream, writes the spec from confirmed intent
- `cs-planning`: two hops downstream (after spec)
- `cs-doubt-driven`: opposite end — post-decision artifact review

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The ask is clear enough" | If you can't write the outcome in one sentence, it isn't clear. |
| "Asking too many questions wastes time" | Building the wrong thing is enormously more expensive. |
| "They said 'whatever you think'" | That's delegation, not decision. Re-ask with two concrete options. |

## Verification

- [ ] Context summary records SysDocs references and relevant constraints, or the missing/not-applicable baseline; hypotheses distinguish documented facts from requested changes and unknowns
- [ ] An explicit hypothesis with confidence number was stated
- [ ] Questions asked one at a time, each with guess attached
- [ ] At least one "what would you actually want?" probe ran
- [ ] A concrete restate (6 lines) was written back
- [ ] The user confirmed with an explicit yes
- [ ] Agent could predict reactions to next three questions
