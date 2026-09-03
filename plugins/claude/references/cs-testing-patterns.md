# Testing Patterns

> Ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)

## Test Structure (Arrange-Act-Assert)

```typescript
it('describes the expected behavior', () => {
  // Arrange: Set up test data and conditions
  // Act: Execute the behavior under test
  // Assert: Verify the outcome
});
```

## Naming Convention

```typescript
describe('[Module/Function name]', () => {
  it('[expected behavior in plain English]', () => { ... });
  it('throws [ErrorType] when [condition]', () => { ... });
});
```

## Test Coverage by Scenario

| Scenario | What to Test |
|----------|-------------|
| Happy path | Valid input produces expected output |
| Empty input | Empty string, empty array, null, undefined |
| Boundary values | Min, max, zero, negative |
| Error paths | Invalid input, network failure, timeout |
| Concurrency | Rapid repeated calls, out-of-order responses |

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|------------|---------|-----|
| Testing implementation details | Breaks on refactor | Test inputs and outputs |
| Flaky tests (timing) | Erodes trust | Deterministic assertions |
| Mocking everything | Production breaks | Prefer real > fake > stub > mock |
| Snapshot abuse | Nobody reviews | Use sparingly |

## See Also

- `cs-tdd` skill for the full TDD workflow
- `cs-test-engineer` agent for test strategy
