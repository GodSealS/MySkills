---
name: cs-shipping
model: DeepSeek-V4-Pro
description: "Prepares production launches. Use when preparing to deploy to production. Use when you need a pre-launch checklist, when setting up monitoring, when planning a staged rollout, or when you need a rollback strategy. / 准备生产发布。用于部署到生产环境——发布前检查清单、监控设置、分阶段上线计划、回滚策略。"
---

# Shipping and Launch

## Overview

Ship with confidence. The goal is not just to deploy — it's to deploy safely, with monitoring in place, a rollback plan ready, and a clear understanding of what success looks like.

## When to Use

- Deploying a feature to production
- Releasing a significant change to users
- Migrating data or infrastructure
- Opening a beta or early access program
- Any deployment that carries risk (all of them)

## The Pre-Launch Checklist

### Code Quality
- [ ] All tests pass (unit, integration, e2e)
- [ ] Build succeeds with no warnings
- [ ] Lint and type checking pass
- [ ] Code reviewed and approved
- [ ] No TODO comments that should be resolved
- [ ] No `console.log` debugging statements in production code

### Security
- [ ] No secrets in code or version control
- [ ] `npm audit` shows no critical or high vulnerabilities
- [ ] Input validation on all user-facing endpoints
- [ ] Authentication and authorization checks in place
- [ ] Security headers configured (CSP, HSTS, etc.)
- [ ] Rate limiting on authentication endpoints

### Performance
- [ ] Core Web Vitals within "Good" thresholds
- [ ] No N+1 queries in critical paths
- [ ] Images optimized
- [ ] Bundle size within budget
- [ ] Database queries have appropriate indexes

### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader can convey page content
- [ ] Color contrast meets WCAG 2.1 AA (4.5:1)
- [ ] Focus management correct for modals and dynamic content

### Infrastructure
- [ ] Environment variables set in production
- [ ] Database migrations applied
- [ ] DNS and SSL configured
- [ ] CDN configured for static assets
- [ ] Health check endpoint exists and responds

### Documentation
- [ ] README updated
- [ ] API documentation current
- [ ] ADRs written for architectural decisions
- [ ] Changelog updated
- [ ] User-facing documentation updated

## Feature Flag Strategy

Ship behind feature flags to decouple deployment from release:
1. DEPLOY with flag OFF
2. ENABLE for team/beta
3. GRADUAL ROLLOUT: 5% → 25% → 50% → 100%
4. MONITOR at each stage
5. CLEAN UP: Remove flag within 2 weeks of full rollout

## Staged Rollout

```
1. DEPLOY to staging → Full test suite + smoke test
2. DEPLOY to production (flag OFF) → Verify health check
3. ENABLE for team → 24-hour monitoring window
4. CANARY rollout (5%) → Monitor error rates, latency, behavior
5. GRADUAL increase (25% → 50% → 100%)
6. FULL rollout → Monitor 1 week, clean up flag
```

### Rollback Triggers
Roll back immediately if:
- Error rate increases by more than 2x baseline
- P95 latency increases by more than 50%
- User-reported issues spike
- Data integrity issues detected
- Security vulnerability discovered

## Rollback Strategy

Every deployment needs a rollback plan:
```markdown
## Rollback Plan

### Trigger Conditions
- Error rate > 2x baseline
- P95 latency > [X]ms

### Rollback Steps
1. Disable feature flag OR deploy previous version
2. Verify rollback: health check, error monitoring
3. Communicate: notify team

### Time to Rollback
- Feature flag: < 1 minute
- Redeploy: < 5 minutes
- Database rollback: < 15 minutes
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It works in staging, it'll work in production" | Production has different data, traffic, edge cases. Monitor. |
| "We don't need feature flags" | Every feature benefits from a kill switch. |
| "Monitoring is overhead" | Without it, you discover problems from user complaints. |

## Verification

**Before deploying:**
- [ ] Pre-launch checklist completed (all sections green)
- [ ] Feature flag configured (if applicable)
- [ ] Rollback plan documented
- [ ] Monitoring dashboards set up
- [ ] Team notified of deployment

**After deploying:**
- [ ] Health check returns 200
- [ ] Error rate is normal
- [ ] Latency is normal
- [ ] Critical user flow works
- [ ] Logs are flowing
