# Observability Checklist

> Ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT)

## Before Launch — Instrumentation

- [ ] Structured logging with correlation IDs
- [ ] RED metrics instrumented (Rate, Errors, Duration) per endpoint
- [ ] Distributed tracing configured (OpenTelemetry)
- [ ] Key business events logged (auth, payments, data mutations)
- [ ] No PII or secrets in log output

## Alerting

- [ ] Alerts defined on symptoms, not causes
- [ ] Error rate threshold defined (e.g., >5% for 5 minutes)
- [ ] P95/P99 latency threshold defined
- [ ] Alert routing configured (who gets paged)
- [ ] Runbooks linked in alert descriptions

## Monitoring Setup

- [ ] Dashboard for key business metrics
- [ ] Dashboard for infrastructure health (CPU, memory, disk)
- [ ] Dashboard for deployment tracking (version, deploy time)
- [ ] Log aggregation working
- [ ] Trace sampling rate configured (100% dev, ~10% production)

## Post-Launch Verification

- [ ] Logs flowing and queryable
- [ ] Metrics populating in dashboards
- [ ] Traces visible for critical user flows
- [ ] Alert test triggered and received
- [ ] Health check endpoint responding

## On-Call Questions

Your instrumentation should answer these without code changes:
1. Is the system healthy right now?
2. What changed in the last deploy?
3. What's the error rate per endpoint?
4. What's the latency distribution per endpoint?
5. Which users are affected by this issue?

## See Also

- `cs-observability` skill for instrumentation workflow
- `cs-shipping` skill for launch monitoring
