---
name: cs-perf-opt
model: opus
description: "Optimizes application performance. Use when performance requirements exist, when you suspect performance regressions, or when Core Web Vitals or load times need improvement. Use when profiling reveals bottlenecks that need fixing. / 优化应用性能。用于存在性能需求、怀疑性能回退、Core Web Vitals或加载时间需改善、性能分析发现需修复的瓶颈时。"
---

# Performance Optimization

## Overview

Measure before optimizing. Performance work without measurement is guessing — and guessing leads to premature optimization that adds complexity without improving what matters. Profile first, identify the actual bottleneck, fix it, measure again.

## When to Use

- Performance requirements exist (load time budgets, response time SLAs)
- Users or monitoring report slow behavior
- Core Web Vitals scores below thresholds
- You suspect a change introduced a regression
- Building features handling large datasets or high traffic

**When NOT to use:** Don't optimize before you have evidence of a problem.

## Core Web Vitals Targets

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **LCP** | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| **INP** | ≤ 200ms | ≤ 500ms | > 500ms |
| **CLS** | ≤ 0.1 | ≤ 0.25 | > 0.25 |

## The Optimization Workflow

```
MEASURE → PROFILES → OPTIMIZE → MEASURE (repeat)
```

### Step 1: Measure Baseline
Establish current performance before any changes. Use Lighthouse, DevTools Performance tab, or production monitoring.

### Step 2: Profile and Identify
Find the specific bottleneck — not the general area. Browser DevTools flame charts, server-side profilers, database query analyzers.

### Step 3: Optimize the Bottleneck
Apply the smallest change that fixes the measured bottleneck. Common optimizations:
- Bundle splitting and lazy loading
- Image optimization (WebP/AVIF, responsive sizes, lazy loading)
- Database query optimization (indexes, N+1 fixes)
- Caching strategies (CDN, in-memory, HTTP cache headers)
- Code splitting and tree shaking

### Step 4: Measure Again
Confirm the optimization actually improved the metric. If not, revert and try a different approach.

## Common Anti-patterns

- Optimizing without measurement
- Micro-optimizations with no measurable impact
- Premature abstraction for performance
- Caching everything without invalidation strategy
- Neglecting Core Web Vitals in favor of custom metrics

## Verification

- [ ] Baseline measurements documented before optimization
- [ ] Target metric improved measurably after optimization
- [ ] No regression in other metrics
- [ ] Tests still pass
- [ ] Optimization doesn't add unreasonable complexity

## See Also

- ../../references/cs-performance-checklist.md`
