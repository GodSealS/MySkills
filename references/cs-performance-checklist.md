# Performance Checklist

> Ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)

## Core Web Vitals Targets

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| INP | ≤ 200ms | ≤ 500ms | > 500ms |
| CLS | ≤ 0.1 | ≤ 0.25 | > 0.25 |

## Loading

- [ ] LCP-critical resources preloaded with `fetchpriority="high"`
- [ ] Images in modern formats (WebP, AVIF) with responsive `srcset`
- [ ] Fonts self-hosted, preloaded, `font-display: swap`
- [ ] Initial JS bundle under 200KB gzipped
- [ ] Code splitting applied for routes and heavy features
- [ ] Third-party scripts loaded with `async`/`defer`

## Rendering

- [ ] No unnecessary full-page re-renders
- [ ] Long lists virtualized
- [ ] Animations use `transform` and `opacity` (compositor-only)
- [ ] No layout thrashing (read-write-read loops)

## Network

- [ ] Static assets cached with long `max-age` + content hashing
- [ ] HTTP/2 or HTTP/3 enabled
- [ ] API responses paginated
- [ ] Response compression enabled (gzip/brotli)
- [ ] No sequential awaits where `Promise.all` would work

## Database

- [ ] No N+1 query patterns
- [ ] Appropriate indexes on queried columns
- [ ] Connection pooling configured
- [ ] Query timeouts set

## See Also

- `cs-perf-opt` skill for optimization workflow
- `cs-web-perf-auditor` agent for CWV audits
