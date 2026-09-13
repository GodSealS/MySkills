---
description: "Implement a design doc with an agent team — architect decomposes, leads build, reviewer audits, test engineer verifies. / 用 Agent 团队实现设计文档——架构师拆解、领域负责人实现、审查员审查、测试工程师验证。"
---

Invoke the `cs-team-build` skill with `$ARGUMENTS` as the path to the design document.

The skill is the orchestrator. It runs five phases and writes every handoff to a unique `tasks/team-build/<run-id>/` directory; it never overwrites a prior run:

1. **Preflight** — resolve the design doc, confirm a clean `git status`, create `<run-dir>/reviews/`
2. **Decompose** — FAN-OUT to `cs-architect`: pick the roster (≥3 members, must include `cs-architect` + `cs-code-reviewer`, plus `cs-backend-lead` / `cs-frontend-lead` as needed), invoke `cs-planning`, write `<run-dir>/team.md` + `plan.md` + `todo.md`. **Stop for human approval here.**
3. **Execute** — for each task, up to 3 rounds of: domain lead implements and stages only task files via `/cs-build` → `cs-code-reviewer` reviews `git diff --cached` → required security/perf audits run when their trigger matches → `cs-architect` triages and writes `<run-dir>/reviews/T<NN>-r<k>-fixes.md`. A clean merged review commits once and moves to the next task. Round 3 still failing → escalate to the human.
4. **Test** — FAN-OUT to `cs-test-engineer`: run the full suite, analyze coverage, report gaps without editing code, write `<run-dir>/test-report.md`
5. **Synthesize** — FAN-OUT to `cs-architect`: triage the test report into `<run-dir>/final-report.md` with a verdict, fix priorities, a fix approach per item, and deferred items

Do not implement code yourself. Fan out, and let the files carry the handoffs.
