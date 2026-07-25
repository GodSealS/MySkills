# Definition of Done

> Ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)

The project-wide standing bar that every change must clear, regardless of which skill is active.

## Required for Every Change

- [ ] Code compiles and builds without errors
- [ ] All existing tests pass (no regressions)
- [ ] New behavior has corresponding tests (unit, integration, or E2E as appropriate)
- [ ] Linting and type checking pass
- [ ] No secrets, credentials, or sensitive data in code or logs
- [ ] Code review completed and approved
- [ ] Behavior verified at runtime (manual test, browser check, or automated E2E)

## Per-Task Acceptance Criteria

In addition to the project-wide Definition of Done, each task has its own acceptance criteria defined during planning (via `cs-planning`). These answer "did we build the right thing?" while the Definition of Done answers "did we build it right?"

## Verification Evidence

"Seems right" is never sufficient. Evidence includes:
- Passing test output
- Successful build logs
- Runtime screenshots or terminal output
- Before/after comparisons for performance/visual changes
