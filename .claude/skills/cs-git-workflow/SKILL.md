---
name: cs-git-workflow
description: "Structures git workflow practices. Use when making any code change. Use when committing, branching, resolving conflicts, or when you need to organize work across multiple parallel streams. / 结构化Git工作流实践。用于任何代码变更——提交、分支、冲突解决、多并行流工作组织。"
---

# Git Workflow and Versioning

## Overview

Git is your safety net. Treat commits as save points, branches as sandboxes, and history as documentation. With AI agents generating code at high speed, disciplined version control is the mechanism that keeps changes manageable, reviewable, and reversible.

## When to Use

Always. Every code change flows through git.

## Core Principles

### Trunk-Based Development (Recommended)

Keep `main` always deployable. Work in short-lived feature branches that merge back within 1-3 days. Feature flags > long branches.

### 1. Commit Early, Commit Often
Each successful increment gets its own commit. Commits are save points.

### 2. Atomic Commits
Each commit does one logical thing. Message format:
```
<type>: <short description>
<optional body explaining why>
```
Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

### 3. Descriptive Messages
Explain the *why*, not just the *what*.

### 4. Keep Concerns Separate
Don't combine formatting changes with behavior changes. Separate refactoring from feature work.

### 5. Size Your Changes
Target ~100 lines per commit. Changes over ~1000 lines should be split.

## Branch Naming
```
feature/<short-description>  → feature/task-creation
fix/<short-description>      → fix/duplicate-tasks
chore/<short-description>    → chore/update-deps
refactor/<short-description> → refactor/auth-module
```

## Working with Worktrees
```bash
git worktree add ../project-feature-a feature/task-creation
# Multiple agents can work in parallel without interfering
```

## The Save Point Pattern
```
Implement slice → Test → Verify → Commit → Next slice
```
If an agent goes off the rails, `git reset --hard HEAD` takes you back.

## Pre-Commit Hygiene
```bash
git diff --staged
git diff --staged | grep -i "password\|secret\|api_key\|token"
npm test
npm run lint
npx tsc --noEmit
```


## Verification

- [ ] Commit does one logical thing
- [ ] Message explains the why, follows type conventions
- [ ] Tests pass before committing
- [ ] No secrets in the diff
- [ ] No formatting-only changes mixed with behavior changes
- [ ] `.gitignore` covers standard exclusions

## Interaction with Other Skills

- `cs-sysdocs-update`: include the authorized change's documentation impact and necessary synchronization in the same commit/PR (or workspace delivery when not committing). Follow [the task-context protocol](../../references/sysdocs-design-context.md); verify the affected scope before review, reuse valid evidence, and report unrelated old gaps separately. Do not turn each update into a repeated permission prompt or unconditional full-library refresh.
