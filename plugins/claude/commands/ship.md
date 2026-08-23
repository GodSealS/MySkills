---
description: "Run the pre-launch checklist via parallel fan-out to specialist personas, then synthesize a go/no-go decision / 通过并行扇出到专家角色执行发布前检查清单，生成上线/不上线决策"
---

Invoke the `cs-shipping` skill.

`/ship` is a **fan-out orchestrator**. It runs three specialist personas in parallel against the current change, then merges their reports into a single go/no-go decision with a rollback plan. The personas operate independently — no shared state, no ordering — which is what makes parallel execution safe and useful here.

## Phase A — Parallel fan-out

Spawn three subagents concurrently using the Agent tool. **Issue all three Agent tool calls in a single assistant turn so they execute in parallel** — sequential calls defeat the purpose of this command.

1. **`cs-code-reviewer`** — Run a five-axis review (correctness, readability, architecture, security, performance) on the staged changes or recent commits. Output the standard review template.
2. **`cs-security-auditor`** — Run a vulnerability and threat-model pass. Check OWASP Top 10, secrets handling, auth/authz, dependency CVEs. Output the standard audit report.
3. **`cs-test-engineer`** — Analyze test coverage for the change. Identify gaps in happy path, edge cases, error paths, and concurrency scenarios. Output the standard coverage analysis.

In other harnesses without an Agent tool, invoke each persona's system prompt sequentially and treat their outputs as if returned in parallel — the merge phase still works.

Constraints:
- Subagents cannot spawn other subagents — do not let one persona delegate to another.
- Each subagent gets its own context window and returns only its report to this main session.

**Persona resolution.** If you've defined your own `cs-code-reviewer`, `cs-security-auditor`, or `cs-test-engineer` in `.codebuddy/agents/`, those take precedence over this plugin's versions.

## Phase B — Merge in main context

Once all three reports are back, the main agent (not a sub-persona) synthesizes them:

1. **Code Quality** — Aggregate Critical/Important findings from `cs-code-reviewer`. Resolve duplicates.
2. **Security** — Promote any Critical/High `cs-security-auditor` findings to launch blockers.
3. **Performance** — Pull from `cs-code-reviewer`'s performance axis; cross-check Core Web Vitals if applicable.
4. **Accessibility** — Verify keyboard nav, screen reader support, contrast.
5. **Infrastructure** — Env vars, migrations, monitoring, feature flags.
6. **Documentation** — README, ADRs, changelog.

## Phase C — Decision and rollback

Produce a single output:

```markdown
## Ship Decision: GO | NO-GO

### Blockers (must fix before ship)
- [Source persona: Critical finding + file:line]

### Recommended fixes (should fix before ship)
- [Source persona: Important finding + file:line]

### Acknowledged risks (shipping anyway)
- [Risk + mitigation]

### Rollback plan
- Trigger conditions: [what signals would prompt rollback]
- Rollback procedure: [exact steps]
- Recovery time objective: [target]

### Specialist reports (full)
- [code-reviewer report]
- [security-auditor report]
- [test-engineer report]
```

## Rules

1. The three Phase A personas run in parallel — never sequentially.
2. Personas do not call each other. The main agent merges in Phase B.
3. The rollback plan is mandatory before any GO decision.
4. If any persona returns a Critical finding, the default verdict is NO-GO unless the user explicitly accepts the risk.
5. **Skip the fan-out only if all of the following are true:** the change touches 2 files or fewer, the diff is under 50 lines, and it does not touch auth, payments, data access, or config/env. Otherwise, default to fan-out.
