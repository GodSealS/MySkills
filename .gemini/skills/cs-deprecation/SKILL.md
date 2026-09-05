---
name: cs-deprecation
description: "Manages deprecation and migration. Use when removing old systems, APIs, or features. Use when migrating users from one implementation to another. Use when deciding whether to maintain or sunset existing code. / 管理废弃与迁移。用于移除旧系统、API或功能——从旧实现迁移到新实现，或决定是否维护/淘汰现有代码。"
---

# Deprecation and Migration

## Overview

Code is a liability, not an asset. Every line of code has ongoing maintenance cost — bugs to fix, dependencies to update, security patches to apply. Deprecation is the discipline of removing code that no longer earns its keep, and migration is the process of moving users safely from the old to the new.

## When to Use

- Replacing an old system, API, or library with a new one
- Sunsetting a feature that's no longer needed
- Consolidating duplicate implementations
- Removing dead code
- Planning the lifecycle of a new system (deprecation planning starts at design time)

## Core Principles

### Code Is a Liability
Every line has ongoing cost. When the same functionality can be provided with less code, the old code should go.

### Hyrum's Law Makes Removal Hard
Users depend on all observable behaviors, not just documented ones. Plan migration carefully.

## Deprecation Lifecycle

```
1. ANNOUNCE — Notify users of upcoming deprecation with timeline
2. WARN — Add deprecation warnings in code
3. MIGRATE — Provide migration guide and tools
4. BLOCK — Prevent new usage of the deprecated system
5. REMOVE — Delete the old code
```

## Migration Patterns

### Strangler Fig Pattern
Gradually replace pieces of a legacy system until the old system can be removed entirely.

### Parallel Run
Run old and new systems simultaneously, compare outputs, switch over when verified.

### Feature Flag Migration
Use feature flags to toggle between old and new implementations per-user or per-request.

## Zombie Code Removal

Before removing code, verify:
1. Is it actually unreferenced? (grep the codebase)
2. Is it exported as a public API? (check consumers)
3. Is it referenced in documentation or config?
4. Could removing it break a CI pipeline?

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's not hurting anyone" | Every line has cost. Dead code confuses readers, slows builds, and needs maintenance. |
| "Someone might need it later" | Git history preserves it. If needed later, it's there. |
| "Removing code is risky" | Keeping dead code is riskier — it may be called accidentally or harbor bugs. |

## Verification

- [ ] Deprecation timeline announced to users
- [ ] Migration guide published
- [ ] All consumers migrated before removal
- [ ] Dead code fully removed (no commented-out blocks left)
- [ ] Documentation updated to reflect removal
- [ ] Tests pass after removal
