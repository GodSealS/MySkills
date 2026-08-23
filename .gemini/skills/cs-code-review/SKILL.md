---
name: cs-code-review
model: gemini-2.5-pro
description: "Conducts multi-axis code review. Use before merging any change. Use when reviewing code written by yourself, another agent, or a human. Use when you need to assess code quality across multiple dimensions before it enters the main branch. / 进行多轴代码审查。用于合并前审查任何代码变更——自己、其他Agent或人类编写的代码。在代码进入主分支前从多个维度评估质量。"
---

# Code Review and Quality

## Overview

Multi-dimensional code review with quality gates. Every change gets reviewed before merge. Review covers five axes: correctness, readability, architecture, security, and performance.

## When to Use

- Before merging any PR or change
- After completing a feature implementation
- When another agent or model produced code to evaluate
- When refactoring existing code
- After any bug fix (review both fix and regression test)

## The Five-Axis Review

### 1. Correctness
- Does it match the spec or task requirements?
- Are edge cases handled?
- Are error paths handled?
- Does it pass all tests?

### 2. Readability & Simplicity
- Are names descriptive and consistent?
- Is control flow straightforward?
- Is the code organized logically?
- Could this be done in fewer lines?
- Are abstractions earning their complexity?
- Are there dead code artifacts?

### 3. Architecture
- Does it follow existing patterns or introduce a new one?
- Does it maintain clean module boundaries?
- Are dependencies flowing in the right direction?
- Does this refactor reduce complexity or just relocate it?

### 4. Security
> For detailed guidance see `cs-security`.

- Is user input validated and sanitized?
- Are secrets kept out of code, logs, and version control?
- Are queries parameterized?

### 5. Performance
> For detailed guidance see `cs-perf-opt`.

- Any N+1 query patterns?
- Any unbounded loops?
- Any missing pagination?

## Review Process

### Step 1: Understand the Context
- What is this change trying to accomplish?
- What spec or task does it implement?
- What is the expected behavior change?

### Step 2: Review the Tests First
Tests reveal intent and coverage.

### Step 3: Review the Implementation
Walk through code with the five axes in mind.

### Step 4: Categorize Findings

| Prefix | Meaning | Author Action |
|--------|---------|---------------|
| *(no prefix)* | Required | Must address before merge |
| **Critical:** | Blocks merge | Security, data loss, broken functionality |
| **Nit:** | Minor, optional | Author may ignore |
| **Optional:** | Suggestion | Worth considering |
| **FYI** | Information | No action needed |

### Step 5: Verify the Verification
- What tests were run?
- Did the build pass?
- Was it tested manually?

## Change Sizing

```
~100 lines changed   → Good. Reviewable in one sitting.
~300 lines changed   → Acceptable if single logical change.
~1000 lines changed  → Too large. Split it.
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It works, that's good enough" | Working code that's unreadable creates compounding debt. |
| "AI-generated code is probably fine" | AI code needs more scrutiny, not less. |
| "The tests pass, so it's good" | Tests don't catch architecture, security, or readability issues. |

## Verification

- [ ] All Critical issues resolved
- [ ] All Required changes resolved or deferred with justification
- [ ] Tests pass
- [ ] Build succeeds
- [ ] Verification story documented

## See Also

- ../../references/cs-security-checklist.md`
- ../../references/cs-performance-checklist.md`
