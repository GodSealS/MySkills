---
name: cs-simplify
description: "Simplifies code for clarity. Use when refactoring code for clarity without changing behavior. Use when code works but is harder to read, maintain, or extend than it should be. Use when reviewing code that has accumulated unnecessary complexity. / 简化代码提升清晰度。用于不改变行为的前提下重构代码——代码能工作但难读/难维护/难扩展，或代码积累了不必要的复杂度时。"
---

# Code Simplification

## Overview

Simplify code by reducing complexity while preserving exact behavior. The goal is not fewer lines — it's code that is easier to read, understand, modify, and debug. Every simplification must pass a simple test: "Would a new team member understand this faster than the original?"

## When to Use

- After a feature is working but the implementation feels heavier than needed
- During code review when readability or complexity issues are flagged
- When you encounter deeply nested logic, long functions, or unclear names
- When refactoring code written under time pressure

**When NOT to use:** Code is already clean, you don't understand the code yet, it's performance-critical, or about to be rewritten.

## The Five Principles

### 1. Preserve Behavior Exactly
All inputs, outputs, side effects, error behavior, and edge cases must remain identical.

### 2. Follow Project Conventions
Simplification means making code more consistent with the codebase, not imposing external preferences.

### 3. Prefer Clarity Over Cleverness
Explicit code is better than compact code when the compact version requires a mental pause.

### 4. Maintain Balance
Over-simplification traps: inlining too aggressively, combining unrelated logic, removing necessary abstraction, optimizing for line count.

### 5. Scope to What Changed
Default to simplifying recently modified code. Avoid drive-by refactors.

## The Simplification Process

### Step 1: Understand Before Touching (Chesterton's Fence)
Before changing anything, understand why it exists: What's its responsibility? What calls it? What are the edge cases?

### Step 2: Identify Simplification Opportunities

**Structural complexity:** deep nesting (3+ levels → guard clauses), long functions (50+ lines → split), nested ternaries → if/else, boolean parameter flags → options objects.

**Naming and readability:** generic names → descriptive, abbreviated names → full words, misleading names → accurate names.

**Redundancy:** duplicated logic → shared function, dead code → remove, unnecessary abstractions → inline, over-engineered patterns → simplify.

### Step 3: Apply Changes Incrementally
One simplification at a time. Run tests after each. The Rule of 500: if a refactor touches >500 lines, use automation (codemods) instead of manual edits.

### Step 4: Verify the Result
Is the simplified version genuinely easier to understand? Did you introduce inconsistent patterns? Is the diff clean and reviewable?

## Language-Specific Guidance

### TypeScript / JavaScript
```typescript
// SIMPLIFY: Unnecessary async wrapper
// Before: async function getUser(id) { return await service.findById(id); }
// After:  function getUser(id) { return service.findById(id); }

// SIMPLIFY: Nested conditionals → guard clauses
// Before: if (data) { if (data.valid) { if (data.hasPerm) { return work(data); } } }
// After:  if (!data) throw Error; if (!data.valid) throw Error; if (!data.hasPerm) throw Error; return work(data);

// SIMPLIFY: Redundant boolean return
// Before: if (input.length > 0 && input.length < 100) return true; return false;
// After:  return input.length > 0 && input.length < 100;
```

### Python
```python
# SIMPLIFY: Verbose dict building → comprehension
# Before: result = {}; for item in items: result[item.id] = item.name
# After:  result = {item.id: item.name for item in items}

# SIMPLIFY: Nested conditionals → guard clauses
# Before: if data is not None: if data.is_valid(): if data.has_perm(): return do_work(data)
# After:  if data is None: raise TypeError; if not data.is_valid(): raise ValueError; return do_work(data)
```

### React / JSX
```tsx
// SIMPLIFY: Verbose conditional rendering
// Before: if (user.isAdmin) return <Badge variant="admin">Admin</Badge>; else return <Badge>User</Badge>;
// After:  const variant = user.isAdmin ? 'admin' : 'default'; return <Badge variant={variant}>{variant === 'admin' ? 'Admin' : 'User'}</Badge>;
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's working, no need to touch it" | Hard-to-read code will be hard to fix when it breaks. |
| "Fewer lines is always simpler" | A 1-line nested ternary is not simpler than a 5-line if/else. |
| "I'll refactor while adding this feature" | Separate refactoring from feature work. Mixed changes are harder to review. |

## Verification

- [ ] All existing tests pass without modification
- [ ] Build succeeds with no new warnings
- [ ] Linter/formatter passes
- [ ] Each simplification is an incremental, reviewable change
- [ ] No error handling was removed or weakened
- [ ] Simplified code follows project conventions
