---
name: cs-incremental
model: sonnet
description: "Delivers changes incrementally. Use when implementing any feature or change that touches more than one file. Use when you're about to write a large amount of code at once, or when a task feels too big to land in one step. / 增量交付变更。用于跨多文件的特性实现、大量代码编写或任务过大无法一步完成时——垂直切片、合约优先、风险优先。"
---

# Incremental Implementation

## Overview

Build in thin vertical slices — implement one piece, test it, verify it, then expand. Avoid implementing an entire feature in one pass. Each increment should leave the system in a working, testable state.

**Owner Routing:** Each slice carries a primary owner from the plan (`arch` / `frontend` / `backend`) and may name collaborators. Route the slice to the primary domain lead via FAN-OUT (`cs-architect` / `cs-frontend-lead` / `cs-backend-lead`) before or during implementation; consult collaborators only at their boundary. For a separately delivered contract, implement it before frontend consumption.

## When to Use

- Implementing any multi-file change
- Building a new feature from a task breakdown
- Refactoring existing code
- Any time you're tempted to write more than ~100 lines before testing

**When NOT to use:** Single-file, single-function changes where the scope is already minimal.

## The Increment Cycle

```
Implement ──→ Test ──→ Verify ──→ Commit ──→ Next slice
```

For each slice:
1. **Implement** the smallest complete piece of functionality
2. **Test** — run the test suite (or write a test if none exists)
3. **Verify** — confirm the slice works as expected
4. **Commit** — save your progress (see `cs-git-workflow`)
5. **Move to the next slice**

## Slicing Strategies

### Vertical Slices (Preferred)
Build one complete path through the stack. Each slice delivers working end-to-end functionality.

### Contract-First Slicing
When backend and frontend develop in parallel: define the API contract first, then implement both sides independently, then integrate.

### Risk-First Slicing
Tackle the riskiest or most uncertain piece first. If it fails, you discover it before investing in dependent work.

## Implementation Rules

### Rule 0: Simplicity First
Before writing any code, ask: "What is the simplest thing that could work?" Three similar lines of code is better than a premature abstraction.

### Rule 0.5: Scope Discipline
Touch only what the task requires. Do NOT "clean up" adjacent code, refactor imports in unrelated files, remove comments you don't understand, or add features not in the spec.

### Rule 1: One Thing at a Time
Each increment changes one logical thing. Don't mix concerns.

### Rule 2: Keep It Compilable
After each increment, the project must build and existing tests must pass.

### Rule 3: Feature Flags for Incomplete Features
If a feature isn't ready for users but you need to merge increments, use feature flags.

### Rule 4: Safe Defaults
New code should default to safe, conservative behavior.

### Rule 5: Rollback-Friendly
Each increment should be independently revertable.

## Increment Checklist

- [ ] The change does one thing and does it completely
- [ ] All existing tests still pass
- [ ] The build succeeds
- [ ] Type checking passes
- [ ] Linting passes
- [ ] The new functionality works as expected
- [ ] The change is committed with a descriptive message

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll test it all at the end" | Bugs compound. A bug in Slice 1 makes Slices 2-5 wrong. |
| "It's faster to do it all at once" | It feels faster until something breaks and you can't find which line caused it. |
| "These changes are too small to commit separately" | Small commits are free. Large commits hide bugs. |

## Verification

- [ ] Each increment was individually tested and committed
- [ ] The full test suite passes
- [ ] The build is clean
- [ ] The feature works end-to-end as specified
- [ ] No uncommitted changes remain

## Orchestration

- **frontend-owned slices** → `cs-frontend-ui` → FAN-OUT to `cs-frontend-lead`
- **backend-owned slices** → `cs-api-design` → FAN-OUT to `cs-backend-lead`
- **architecture/contract decisions** → FAN-OUT to `cs-architect`
- **tests** → `cs-tdd`; **browser verification** → `cs-browser-test`
- Scope discipline applies per-slice: each lead touches only files within its slice

## See Also

See `../../references/cs-definition-of-done.md` for the project-wide bar.
