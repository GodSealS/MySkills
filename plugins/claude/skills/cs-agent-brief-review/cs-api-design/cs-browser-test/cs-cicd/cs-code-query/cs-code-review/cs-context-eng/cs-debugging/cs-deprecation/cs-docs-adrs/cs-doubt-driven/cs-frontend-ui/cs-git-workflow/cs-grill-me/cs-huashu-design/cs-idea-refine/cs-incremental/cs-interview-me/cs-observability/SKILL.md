---
name: cs-observability
model: sonnet
description: "Instruments code so production behavior is visible and diagnosable. Use when adding logging, metrics, tracing, or alerting. Use when shipping any feature that runs in production and you need evidence it works. / 代码插桩使生产行为可观测可诊断。用于添加日志、指标、追踪或告警——确保上线的功能有证据证明其正常工作。"
---

# Observability and Instrumentation

## Overview

Code you can't observe is code you can't operate. Observability is the ability to answer "what is the system doing and why?" from the outside. Instrumentation is not a post-launch add-on — it's written alongside the feature, the same way tests are.

## When to Use

- Building any feature that will run in production
- Adding a new service, endpoint, background job, or external integration
- A production incident took too long to diagnose
- Setting up or reviewing alerting rules
- Reviewing a PR that adds I/O, retries, queues, or cross-service calls

**NOT for:** Debugging a current failure (use `cs-debugging`), performance profiling (use `cs-perf-opt`), launch checklists (use `cs-shipping`).

## The Three Pillars

### 1. Structured Logging
- Log in JSON format (machine-parseable)
- Include correlation IDs for request tracing
- Log at appropriate levels: DEBUG, INFO, WARN, ERROR
- Never log secrets, PII, or credentials
- Log key decision points: "user authenticated", "payment processed", "cache miss"

### 2. Metrics (RED Method)

| Aspect | Metric | Example |
|--------|--------|---------|
| **Rate** | Request rate | Requests per second |
| **Errors** | Error rate | Failed requests per second |
| **Duration** | Latency distribution | p50, p95, p99 response times |

Also track USE metrics for infrastructure: Utilization, Saturation, Errors.

### 3. Distributed Tracing
- Propagate trace context across service boundaries
- Use OpenTelemetry for vendor-neutral instrumentation
- Trace every request from entry to exit
- Include key spans: database queries, external API calls, cache operations

## Symptom-Based Alerting

Alert on symptoms, not causes:
- **Good:** "Error rate > 5% for 5 minutes" (symptom the user experiences)
- **Bad:** "CPU > 80%" (cause that may or may not matter)

Alert thresholds:
- Error rate spike → Critical
- P95 latency degradation → Warning
- Zero traffic when traffic is expected → Critical
- Disk/memory approaching limits → Warning

## Instrumentation Patterns

```typescript
// Structured logging with correlation
logger.info('Order processed', {
  orderId: order.id,
  userId: user.id,
  amount: order.total,
  duration: Date.now() - startTime,
  correlationId: ctx.correlationId,
});

// Metric recording
metrics.increment('orders.created', { status: order.status });
metrics.gauge('orders.value', order.total);
metrics.histogram('orders.processing_time', duration);
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We'll add monitoring later" | Add it before launch. You can't debug what you can't see. |
| "Logging everything is better" | Noise hides signal. Log what you'll actually query. |
| "Metrics are ops' problem" | Instrumentation is the developer's responsibility. Ops consumes the output. |

## Verification

- [ ] Structured logging with correlation IDs
- [ ] Key metrics (RED) instrumented for each endpoint/job
- [ ] Distributed tracing configured for cross-service calls
- [ ] Alerting rules defined with thresholds
- [ ] No secrets or PII in log output
- [ ] Log levels are appropriate (not everything is ERROR)

## See Also

- ../../references/cs-observability-checklist.md`
