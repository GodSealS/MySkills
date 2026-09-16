---
description: "Implement a design doc with an agent team — architect decomposes, leads build, reviewer audits, advisor recommends, experts verify. / 用 Agent 团队实现设计文档——架构师拆解、领域负责人实现、审查员首审、顾问建议、专家复验。"
---

This command is an approved manual entry point. Invoke the `cs-team-build` skill with `$ARGUMENTS` as the path to the design document.

The host executes the skill as orchestrator. It writes every handoff to a unique `tasks/team-build/<run-id>/` directory; it never overwrites a prior run:

1. **Preflight** — resolve the design doc, confirm a clean `git status`, create `<run-dir>/reviews/`, and establish the skill's task-specific document/source context; pass applicable specs/ADRs, active-layout descriptions and necessary gaps to the architect/advisor. No automatic full initialization or unrelated repair.
2. **Decompose and review plan** — FAN-OUT to `cs-architect`: propose the roster (≥4 members, including `cs-architect` + `cs-review-advisor` + `cs-code-reviewer`, plus at least one domain lead), invoke `cs-planning`, write `<run-dir>/team.md` + `plan.md` + `todo.md`. The host validates the roster and sends the plan to `cs-review-advisor`, then relevant experts verify recommendations in `reviews/00-plan-review.md`. **Present plan and review for human approval here.**
3. **Execute** — per task, at most 3 rounds: owner implements and stages task files via `/cs-build` → independent `cs-code-reviewer` reviews `git diff --cached` → host runs triggered security/perf audits even on APPROVE → `cs-review-advisor` recommends → relevant experts re-detect and itemize fully/partly/not acceptable advice in `reviews/T<NN>-r<k>-fixes.md`. Accepted advice leaves findings open until repair and expert verification pass. The host commits once after all gates only when authorized; explicit no-commit instructions take precedence. Blocking rejected advice immediately opens user choice and pauses dependent actions as pending-human; do not wait for round 3. Round 3 still failing → escalate; repeated P0 returns to architect re-slicing.
4. **Test** — FAN-OUT to `cs-test-engineer`: run the full suite, analyze coverage, report gaps without editing code, write `<run-dir>/test-report.md`
5. **Synthesize** — host aggregates valid slice documentation evidence and checks only new/unresolved impacts, then FAN-OUT to `cs-review-advisor`: draft `<run-dir>/final-report.md` from tests, findings and scoped structural/content verification; experts verify recommendations and the host computes `SHIP|FIX FIRST`. Missing required evidence or current-change omissions prevent SHIP; unrelated old defects remain separate. Consult `cs-architect` only for architecture consequences.
6. **Wrap up** — host updates status; `cs-knowledge-base-admin` remains the final operational subagent and refreshes existing knowledge bases only.

Follow the skill's `review-advisor-v1` run protocol and legacy-run compatibility rules. The advisor never invokes personas, commits, or closes findings. User dispute choices are not repair verification evidence; without dialog support ask directly and await the answer.

Before each review snapshot, the host synchronizes affected descriptions, summaries, indexes, links and applicable requirements, with separate structure/content verification. Reuse existing authorization and valid evidence; no empty update report or unconditional whole-library refresh. Combine KB/summary/source candidates and expand high-risk flow reading per the shared context protocol. Later related changes invalidate affected reviews; required documentation gaps block DONE or committing.

Do not implement code yourself. Fan out, and let the files carry the handoffs.
