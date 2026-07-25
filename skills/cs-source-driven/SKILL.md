---
name: cs-source-driven
description: "Grounds every implementation decision in official documentation. Use when you want authoritative, source-cited code free from outdated patterns. Use when building with any framework or library where correctness matters. / 将每个实现决策建立在官方文档基础上。用于需要权威、有源码引用的代码——使用任何框架或库且正确性重要时（DETECT→FETCH→IMPLEMENT→CITE）。"
---

# Source-Driven Development

## Overview

Every framework-specific code decision must be backed by official documentation. Don't implement from memory — verify, cite, and let the user see your sources. Training data goes stale, APIs get deprecated, best practices evolve. This skill ensures code that users can trust because every pattern traces back to an authoritative source they can check.

## When to Use

- The user wants code that follows current best practices for a given framework
- Building boilerplate, starter code, or patterns that will be copied across a project
- The user explicitly asks for documented, verified, or "correct" implementation
- Implementing features where the framework's recommended approach matters
- Reviewing or improving code that uses framework-specific patterns
- Any time you are about to write framework-specific code from memory

**When NOT to use:** Pure logic that works the same across all versions, or when the user wants speed over verification.

## The Process

```
DETECT → FETCH → IMPLEMENT → CITE
```

### Step 1: DETECT — Identify what needs verification
Map every framework-specific call, pattern, and assumption in the plan.

### Step 2: FETCH — Pull official documentation
Use WebFetch to pull the current official docs for each identified API. Prefer official sources over tutorials or blog posts.

### Step 3: IMPLEMENT — Build from verified sources
Write code that follows the documented patterns exactly. Flag any pattern seen in training data but absent from current docs — it may be deprecated.

### Step 4: CITE — Document your sources
```markdown
## Sources
- Next.js App Router: `https://nextjs.org/docs/app/building-your-application/routing` (v14.2)
- React Server Components: `https://react.dev/reference/rsc/server-components` (React 19)
```

## Verification Rules

1. Never implement framework-specific code from memory — fetch current docs first
2. Cite the source URL for every framework API used
3. If docs conflict with training data, docs win — flag the discrepancy
4. Tag unverified code explicitly: `// UNVERIFIED: No current docs found for this pattern`

## Interaction with Other Skills

- `cs-doubt-driven`: SDD verifies facts; DDD verifies decisions. They complement each other.
- `cs-interview-me`: SDD verifies technical correctness; interview-me verifies intent. Orthogonal concerns.

## Verification

- [ ] All framework-specific code is backed by official documentation
- [ ] All sources are cited with URLs and version numbers
- [ ] Any unverified code is explicitly tagged
- [ ] Docs were fetched during this session, not recalled from memory
