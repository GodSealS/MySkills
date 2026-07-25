---
name: cs-cicd
description: "Automates CI/CD pipeline setup. Use when setting up or modifying build and deployment pipelines. Use when you need to automate quality gates, configure test runners in CI, or establish deployment strategies. / 自动化CI/CD流水线设置。用于建立或修改构建部署流水线——自动化质量门禁、配置CI测试运行器、建立部署策略。"
argument-hint: "[pipeline or automation setup]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
agent: cs-code-reviewer
---

# CI/CD and Automation

## Overview

Automate quality gates so that no change reaches production without passing tests, lint, type checking, and build. CI/CD is the enforcement mechanism for every other skill — it catches what humans and agents miss, consistently on every single change.

**Shift Left:** Catch problems as early as possible. A bug caught in linting costs minutes; the same bug caught in production costs hours.

**Faster is Safer:** Smaller batches and more frequent releases reduce risk. A deployment with 3 changes is easier to debug than one with 30.

## When to Use

- Setting up a new project's CI pipeline
- Adding or modifying automated checks
- Configuring deployment pipelines
- When a change should trigger automated verification
- Debugging CI failures

## The Quality Gate Pipeline

Every change goes through these gates before merge:

```
Pull Request Opened
    │
    ├── Lint & Format Check
    ├── Type Check
    ├── Unit Tests
    ├── Integration Tests
    ├── Build
    ├── Security Audit
    └── (Optional) E2E Tests / Deploy Preview
            │
            ▼
    Merge to main
```

## CI Configuration Principles

1. **Run on every PR:** Don't allow PRs without CI checks passing
2. **Fail fast:** Run fastest checks first (lint before build before tests)
3. **Cache dependencies:** Speed up subsequent runs
4. **Parallel jobs:** Run independent checks concurrently
5. **Artifacts:** Save build outputs and test reports

## Deployment Strategies

- **Feature Flags:** Deploy code behind flags, enable incrementally
- **Blue-Green:** Two identical environments, swap traffic instantly
- **Canary:** Gradual rollout to increasing percentages of users
- **Rolling:** Update instances one at a time

## Failure Feedback Loops

When CI fails:
1. Notify the committer immediately
2. Block merge until resolved
3. Auto-assign the failure to the person who pushed
4. Track CI failure rate as a team health metric

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's just a small change, skip CI" | Small changes break things too. CI is always-on. |
| "CI is too slow" | Optimize CI speed — parallel jobs, caching, smarter test selection. |
| "We'll add CI later" | Adding CI late means adding it to a codebase that already has issues. |

## Verification

- [ ] All quality gates run on every PR
- [ ] Failed checks block merge
- [ ] Pipeline completes in < 15 minutes
- [ ] Dependencies are cached for speed
- [ ] Deployment strategy documented
- [ ] Rollback procedure tested
