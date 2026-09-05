---
name: cs-doubt-driven
description: "Subjects every non-trivial decision to a fresh-context adversarial review before it stands. Use when correctness matters more than speed, when working in unfamiliar code, when stakes are high, or any time a confident output would be cheaper to verify now than to debug later. / 对非平凡决策进行对抗性审查（CLAIM→EXTRACT→DOUBT→RECONCILE→STOP）。用于正确性大于速度、不熟悉的代码、高风险决策——现在验证比将来调试便宜。"
---

# Doubt-Driven Development

## Overview

A confident answer is not a correct one. Long sessions accumulate context that quietly turns assumptions into "facts" without anyone noticing. Doubt-driven development is the discipline of materializing a fresh-context reviewer — biased to disprove, not approve — before any non-trivial output stands.

## When to Use

A decision is non-trivial when:
- It introduces or modifies branching logic
- It crosses a module or service boundary
- It asserts a property the type system cannot verify
- Its blast radius is irreversible (production deploy, data migration, public API change)

Apply when:
- About to make an architectural decision under uncertainty
- Working in code you don't fully understand
- Stakes are high (production, security, auth, payments)

## The Process: CLAIM → EXTRACT → DOUBT → RECONCILE → STOP

### CLAIM
State what you're about to assert or implement, clearly and testably.

### EXTRACT
Extract the specific assumptions the claim rests on. Be exhaustive.

### DOUBT
For each assumption, ask: "Is this definitely true? What would prove it false?" Actively try to disprove, don't just seek confirmation.

### RECONCILE
Resolve each doubt: verify against docs, test against edge cases, check against existing code.

### STOP
If a doubt can't be resolved, stop and surface it to the user. Don't proceed with unverified assumptions on high-stakes decisions.

## Cross-Model Escalation (Optional)

For the highest-stakes decisions, spawn a subagent with fresh context as the adversarial reviewer. The subagent's sole job is to find flaws — it does not propose solutions. This is an optional escalation, not the default.

## Interaction with Other Skills

- `cs-source-driven`: SDD verifies framework facts; DDD verifies your decisions and assumptions.
- `cs-interview-me`: interview-me is pre-decision intent extraction; DDD is post-decision artifact review.
- `cs-code-review`: review is a verdict on finished artifacts; DDD runs in-flight while correction is cheap.

## Verification

- [ ] Every non-trivial claim has been subjected to the CLAIM→EXTRACT→DOUBT→RECONCILE loop
- [ ] Unresolved doubts have been surfaced to the user
- [ ] No high-stakes decision proceeds with unverified assumptions
- [ ] The adversarial reviewer found no remaining contradictions
