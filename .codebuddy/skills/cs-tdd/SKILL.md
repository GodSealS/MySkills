---
name: cs-tdd
description: "Drives development with tests. Use when implementing any logic, fixing any bug, or changing any behavior. Use when you need to prove that code works, when a bug report arrives, or when you're about to modify existing functionality. / 以测试驱动开发。用于实现任何逻辑、修复Bug或变更行为——需要证明代码正确、收到Bug报告、或即将修改已有功能时（RED→GREEN→REFACTOR）。"
argument-hint: "[feature or bug to test-drive]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
agent: cs-test-engineer
---

# Test-Driven Development

## Overview

Write a failing test before writing the code that makes it pass. For bug fixes, reproduce the bug with a test before attempting a fix. Tests are proof — "seems right" is not done.

**Boundary with `cs-minimal`:** when both are active, RED-GREEN-REFACTOR takes full priority. `cs-minimal` may remove worthless scaffolding only, and never limits fixtures, parameterization, or test case count.

## When to Use

- Implementing any new logic or behavior
- Fixing any bug (the Prove-It Pattern)
- Modifying existing functionality
- Adding edge case handling
- Any change that could break existing behavior

**Owner Routing:** Tests stay with the slice owner. The host handles ordinary work; delegate to a domain lead only for a concrete independent task or an explicit team workflow. Independent test-coverage review remains separate from implementation.

Documentation-only and low-impact configuration edits use relevant validators and inspection; do not create tests that merely mirror instruction wording.

## The TDD Cycle

```
    RED                GREEN              REFACTOR
 Write a test    Write minimal code    Clean up the
 that fails  →  to make it pass    →  implementation  →  (repeat)
```

### Step 1: RED — Write a Failing Test
Write the test first. It must fail. A test that passes immediately proves nothing.

### Step 2: GREEN — Make It Pass
Write the minimum code to make the test pass. Don't over-engineer.

### Step 3: REFACTOR — Clean Up
With tests green, improve the code without changing behavior. Run tests after every refactor step.

## The Prove-It Pattern (Bug Fixes)

When a bug is reported, do NOT start by trying to fix it. Start by writing a test that reproduces it:
1. Write a test that demonstrates the bug (must FAIL)
2. Confirm the test fails
3. Implement the fix
4. Test PASSES (proving the fix works)
5. Run affected regression tests; use the shared Definition of Done for integration/final checks.

## The Test Pyramid

```
          /\
         /  \         E2E Tests (~5%)
        /    \        Full user flows
       /------\
      /        \      Integration Tests (~15%)
     /          \     Component interactions
    /------------\
   /              \   Unit Tests (~80%)
  /                \  Pure logic, isolated
 /──────────────────\
```

**The Beyonce Rule:** If you liked it, you should have put a test on it.

## Writing Good Tests

### Test State, Not Interactions
Assert on the *outcome* of an operation, not on which methods were called.

### DAMP Over DRY in Tests
In tests, DAMP (Descriptive And Meaningful Phrases) is better than DRY. Each test should tell a complete story.

### Prefer Real Implementations Over Mocks
Preference order: Real implementation > Fake > Stub > Mock. Use mocks only when the real implementation is too slow, non-deterministic, or has uncontrollable side effects.

### Use Arrange-Act-Assert
```typescript
it('marks overdue tasks when deadline has passed', () => {
  // Arrange
  const task = createTask({ title: 'Test', deadline: new Date('2025-01-01') });
  // Act
  const result = checkOverdue(task, new Date('2025-01-02'));
  // Assert
  expect(result.isOverdue).toBe(true);
});
```

## Test Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Testing implementation details | Tests break on refactor | Test inputs and outputs |
| Flaky tests | Erode trust in suite | Deterministic assertions |
| Testing framework code | Wasted time | Only test YOUR code |
| Snapshot abuse | Nobody reviews | Use sparingly |
| Mocking everything | Production breaks | Prefer real implementations |


## Verification

- [ ] Every new behavior has a test
- [ ] Affected tests pass; required integration/final checks follow the shared Definition of Done
- [ ] Bug fixes include a reproduction test
- [ ] Test names describe the behavior
- [ ] No tests were skipped or disabled
- [ ] Coverage hasn't decreased

## See Also

See [Definition of Done](../../references/cs-definition-of-done.md) for check frequency and `.codebuddy/references/cs-testing-patterns.md` for detailed patterns and framework-specific examples.
