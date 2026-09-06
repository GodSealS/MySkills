---
name: cs-team-build
description: "Runs a design document through a coordinated agent team — the architect decomposes it into tasks, domain leads implement them, a reviewer audits each slice, the architect triages findings, and a test engineer verifies the whole. Use when a design or spec document exists and you want it implemented by a multi-agent team with bounded review loops. / 用 Agent 团队把设计文档落地：架构师拆解任务、领域负责人实现、审查员逐片审查、架构师裁决修改意见、测试工程师整体验证。用于已有设计/规范文档、希望由多 Agent 团队带审查闭环交付时。"
---

# Team Build — Multi-Agent Implementation

## Overview

A single agent implementing a non-trivial design doc fails in a predictable way: it writes plausible code, reviews its own work, and declares victory. This skill replaces that with a **team** — a fixed cast of personas, a file-based handoff trail, and a **bounded** review loop (max 3 rounds per task) that cannot spin forever.

The team is not a chat. Every handoff is a **file** under a unique run directory, `tasks/team-build/<run-id>/`. That makes the loop auditable, resumable, and safe to re-run without overwriting another run.

Two rules hold throughout:

1. **The skill orchestrates, not the personas.** Personas never call each other. Every fan-out is issued by this skill. (See `../../references/cs-orchestration-patterns.md` — this skill is the sanctioned orchestrator for the team loop.)
2. **Files are the handoff medium.** No "as we discussed" context. If it isn't in the handoff doc, it doesn't exist.

## When to Use

- You have a design/spec document and want it implemented end-to-end
- The change spans modules or domains (frontend + backend), so one agent won't hold it all in context
- You want implementation to come with review, test, and triage — not just code
- You want a resumable trail you can audit or hand to a human mid-flight

**When NOT to use:**

- Single-file or obvious-scope change → `cs-incremental`
- No document yet, only an idea → `cs-spec-driven`
- You just want a review of existing code → `cs-code-review`
- Emergency hotfix where a 3-round loop is the wrong shape → `cs-debugging`

## Team Roster

A team has **at least 3 members**. Two are mandatory:

| Member | Required | Role in the loop |
|---|---|---|
| `cs-architect` | **Always** | Reads the design doc, picks the rest of the team, decomposes into tasks, triages every review, writes fix directives, synthesizes the test report |
| `cs-code-reviewer` | **Always** | Five-axis review of every implemented slice (correctness, readability, architecture, security, performance) |
| `cs-backend-lead` | If the doc implies API / data / server work | Implements backend-owned tasks via `/cs-build` |
| `cs-frontend-lead` | If the doc implies UI / interaction / browser work | Implements frontend-owned tasks via `/cs-build` |
| `cs-security-auditor` | On demand, decided by the architect | Assists a round when the slice touches a trust boundary |
| `cs-web-perf-auditor` | On demand, decided by the architect | Assists a round when the slice is user-facing or perf-budgeted |
| `cs-test-engineer` | Phase 3 (always, once) | Runs the full suite, analyzes coverage, writes `<run-dir>/test-report.md` |

The architect decides the roster — see Phase 1. A roster of exactly `cs-architect` + `cs-code-reviewer` + one domain lead is valid; `cs-architect` + `cs-code-reviewer` alone is not (nobody would implement).

## Artifact Layout

Everything lives under `tasks/team-build/<run-id>/` at the repo root. Create a fresh run directory before writing; never overwrite an existing run (see AGENTS.md "Defensive File Writing"). Record the run directory in every handoff.

```
tasks/team-build/<run-id>/
├── team.md                      # roster + why each member was picked
├── plan.md                      # cs-planning output — the task breakdown
├── todo.md                      # checklist: id, title, owner, status, rounds used
├── reviews/
│   ├── T01-r1-code-review.md    # cs-code-reviewer, round 1
│   ├── T01-r1-security.md       # optional, only when the architect calls it
│   ├── T01-r1-perf.md           # optional, only when the architect calls it
│   └── T01-r1-fixes.md          # cs-architect's change directive for round 2
├── test-report.md               # cs-test-engineer (Phase 3)
└── final-report.md              # cs-architect synthesis (Phase 4)
```

## Process

### Phase 0 — Preflight (skill, no fan-out)

1. Resolve the design doc from `$ARGUMENTS`. If missing or unreadable, **stop** and ask for the path.
2. Confirm a clean baseline: `git status --porcelain`. If there are uncommitted changes outside the selected `<run-dir>/`, stop and ask the user to commit, stash, or confirm.
3. Create a fresh `tasks/team-build/<run-id>/reviews/` directory (for example, a timestamp plus short random suffix). If the selected run directory already exists, stop and choose a new run id; never overwrite prior handoffs.

### Phase 1 — Architect decomposes (FAN-OUT → `cs-architect`)

Fan-out to `cs-architect` with the design doc path. The architect:

1. Reads the whole design doc.
2. **Decides the roster.** Which domain leads are actually needed — `cs-backend-lead`, `cs-frontend-lead`, or both — and says why in one line each. Record it in `<run-dir>/team.md`.
3. **Invokes the `cs-planning` skill** to break the doc into executable tasks. Vertical slices, not horizontal layers. Every task needs: id, title, description, **primary owner** (`arch` / `frontend` / `backend`), acceptance criteria, verification steps, dependencies, files likely touched.
4. Writes `<run-dir>/plan.md` (full breakdown) and `<run-dir>/todo.md` (tracking checklist with a `Rounds` column).
5. Constraint: `arch` tasks are limited to public contracts, module skeletons, and cross-cutting config. Business features go to a domain lead.

**Checkpoint:** present `<run-dir>/team.md` + `<run-dir>/plan.md` to the human. Get an unambiguous affirmative before any code is written. This is the only gate before the loop; after it, the team runs task by task without stopping.

### Phase 2 — Execution loop (per task, max 3 rounds)

For each task `T<NN>` in dependency order, run at most **3 rounds**. A round has three steps.

**Step 1 — IMPLEMENT.** FAN-OUT to the task's primary owner:

- `backend` → `cs-backend-lead`
- `frontend` → `cs-frontend-lead`
- `arch` → `cs-architect`

Instruct the lead to follow `/cs-build` (`cs-incremental` + `cs-tdd`) for exactly this task: read acceptance criteria → RED → GREEN → regression suite → build → **stage only this task's files and stop before committing**. Team Build owns the single task commit after review approval.

For round 1 the input is `<run-dir>/plan.md#T<NN>`. For rounds 2-3 the input is `<run-dir>/reviews/T<NN>-r<k>-fixes.md` — the lead implements the directive, stages only this task's files, and does nothing else. Scope discipline applies: no drive-by refactors, no "while I'm here" changes.

**Step 2 — REVIEW.** FAN-OUT to `cs-code-reviewer` (`cs-code-review`). Review the task's staged diff (`git diff --cached`), not the whole branch; the handoff must include the base commit and the exact staged file list. Review across all five axes and write the result to `<run-dir>/reviews/T<NN>-r<k>-code-review.md` using the reviewer's standard output template, ending with a verdict:

**Verdict:** `APPROVE` | `REQUEST CHANGES`

**Step 3 — TRIAGE.** FAN-OUT to `cs-architect` with the review file. The architect:

a. **Before deciding approval**, apply the specialist trigger table to every round. If the slice matches a trigger, run that audit even when the code reviewer says `APPROVE`; merge its findings into triage.

b. **If the merged verdict is `APPROVE` with no Critical and no Important findings** → commit the staged task files once, mark the task DONE in `<run-dir>/todo.md`, and **move to the next task**. No extra round is burned on Suggestions alone; note them and carry on.

c. **Otherwise** → decide the fix directive from the merged findings:

| Specialist | Call it when the slice touches |
|---|---|
| `cs-security-auditor` | authn/authz, user input crossing a trust boundary, data access / queries / SQL, secrets or env, file upload, external integrations, payments |
| `cs-web-perf-auditor` | user-facing UI, list/table/image rendering, bundle size, Core Web Vitals budget, animation or scroll paths |

Optional assistants run **within the same round**; their findings are merged, not queued. Each writes `<run-dir>/reviews/T<NN>-r<k>-security.md` / `-perf.md`.

Then write `<run-dir>/reviews/T<NN>-r<k>-fixes.md` — the change directive — and increment the round counter. Do not commit until a merged review approves the task; this preserves one commit per task across all rounds.

The directive is not a summary. It is an actionable work order:

```markdown
# Fix Directive: T03 — <title> · Round 1 → 2
Source: <run-dir>/reviews/T03-r1-code-review.md (+ -security.md, -perf.md)

## P0 — must fix before this task can pass
- [ ] [file:line] [what is wrong] → [concrete fix]  (owner: backend)

## P1 — should fix
- [ ] [file:line] [what is wrong] → [concrete fix]

## P2 — optional, do not spend a round on these
- [ ] [file:line] [suggestion]

## Notes for the implementer
- [Constraint the reviewer raised that isn't a code change: e.g. "keep the contract shape, fix the handler"]

## Definition of done for round 2
- [ ] P0 and P1 closed
- [ ] Full suite green, build green
- [ ] Changes staged, this task's files only; Team Build commits once after approval
```

**Round budget — 3. Enforced.** After round 3, if the task still fails review, **stop the loop and escalate to the human**: summarize the unresolved findings, the rounds spent, and the recommended path (re-slice the task / clarify the design doc / accept the risk). Never silently start a 4th round.

**Same finding twice is a signal, not a round.** If round 2 repeats a P0 from round 1, the task is mis-specified or the design doc is ambiguous. Stop, go back to `cs-architect` for a re-slice (Phase 1) rather than implementing the third time.

### Phase 3 — Test sweep (all tasks done, FAN-OUT → `cs-test-engineer`)

Fan-out to `cs-test-engineer` with `<run-dir>/plan.md` and `<run-dir>/todo.md`. The test engineer:

1. Runs the full suite (and build) — record the exact commands and raw results
2. Analyzes coverage against the acceptance criteria of every task
3. Reports missing tests where a task's behavior is unverified (Prove-It pattern for anything failing); it does not modify source or test files in this phase. Any requested test change becomes a new task after human approval.
4. Invokes `cs-browser-test` for user-facing flows where a browser is available
5. Writes `<run-dir>/test-report.md`:

```markdown
## Test Report

### Run
- Command / result / timestamp
- Totals: [x] passed, [y] failed, [z] skipped

### Coverage vs. plan
- T01: [covered / partial / gap → which acceptance criterion is unverified]

### Failures
- [Test] → [observed] → [suspected cause]

### Gaps
- [What is untested and why it matters]

### Recommended next tests (priority)
- Critical / High / Medium / Low
```

### Phase 4 — Architect synthesis (FAN-OUT → `cs-architect`)

Fan-out to `cs-architect` with `<run-dir>/test-report.md`. The architect does **not** re-review code line by line — it triages the report and writes `<run-dir>/final-report.md`:

1. **Verdict:** `SHIP` | `FIX FIRST`
2. **Fix priorities** — restated from the test report and promoted/demoted by architectural risk. A flaky integration test on a core flow outranks a missing unit test on a utility.
3. **Fix approach per item** — for each P0/P1: which owner should take it, which files, the suggested technique, and the risk if it's done wrong. This is the part the test report does not provide.
4. **Deferred items** — what is being accepted, with the rationale.
5. **Residual risk** — what the human should know before shipping.

If the verdict is `FIX FIRST`, do **not** auto-start the fixes. Present the prioritized list and get approval — then each fix re-enters Phase 2 as a new task with a fresh 3-round budget.

### Phase 5 — Wrap-up

- Update `<run-dir>/todo.md` so every task shows a final status
- Report to the human: tasks completed, rounds used per task, commits made, tests added, open P1/P2 items
- Stop or dismiss any persistent team members using the host platform's supported lifecycle operation, if one was created; do not invent tool calls.

## Handoff Protocol

Every handoff document is self-contained — the receiving agent must be able to act without any chat history:

- **Context:** design doc path + run directory + task spec location
- **What was done:** specific, with file paths
- **Review range:** base commit, exact staged file list, and `git diff --cached` command when code is awaiting review
- **Findings:** severity, `file:line`, concrete fix — never "consider improving X"
- **Next:** numbered, verifiable actions
- **Done-criteria:** how the receiver knows the handoff is satisfied

## Escalation — Stop and Ask

- Design doc is ambiguous on a point a task depends on → ask; do not invent requirements
- A test cannot be made to pass → `cs-debugging`
- A task is high-risk or irreversible → `cs-doubt-driven`, get explicit sign-off
- Round budget exhausted → escalate with the summary described in Phase 2
- Any agent wants to touch files outside its task → stop, that's scope creep

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The reviewer approved, so it's done" | Verdict `APPROVE` with outstanding Important findings is not approval. Check the body, not the header. |
| "One more round will fix it" | The budget is 3. Round 4 means the task was sliced wrong — re-slice. |
| "We already wrote tests for that task" | Per-task tests prove the slice. Phase 3 proves the composition. Both are required. |
| "The architect can just fix this line, it's faster" | The architect triages; the lead implements. Blur that line and you lose the review record. |
| "Security/perf review can wait until the end" | By then every slice has been built on the same wrong assumption. Decide within the round. |
| "Skip the roster, just use both leads" | An unnecessary lead writes code nobody asked for. The architect decides. |
| "Suggestions are worth another round" | No. Note them, move to the next task. |
| "The plan is approved, don't stop again" | The gate is per-run, not per-decision. Ambiguity and exhausted rounds still stop you. |

## Red Flags

- A review document with no `file:line` references — the reviewer didn't actually read the diff
- Two consecutive rounds with the same P0 — the task is mis-sliced, go back to Phase 1
- An implementer committing files outside its task
- The architect editing feature code instead of writing directives
- `<run-dir>/reviews/` empty but all tasks marked DONE — the loop was skipped
- Rounds consumed evenly at 3 across every task — systemic problem (unclear doc), not per-task variance
- `<run-dir>/test-report.md` written from the plan instead of from an actual test run
- A final report that lists problems without a fix approach per item

## Verification

- [ ] `<run-dir>/team.md` lists ≥3 members, including `cs-architect` and `cs-code-reviewer`, with a reason for each
- [ ] `<run-dir>/plan.md` exists; every task has acceptance criteria, verification, and a primary owner
- [ ] The human approved the roster + plan before implementation started
- [ ] Every task ran ≤3 rounds; any task that hit the cap was escalated, not silently continued
- [ ] Every round has a `<run-dir>/reviews/T<NN>-r<k>-code-review.md` with an explicit verdict and base commit/staged file list
- [ ] Every non-approved round has a matching `-fixes.md` directive with P0/P1/P2 and concrete fixes
- [ ] Optional security/perf audits were decided by the architect, with the trigger recorded
- [ ] One commit per task, containing only that task's files, created after review approval
- [ ] `<run-dir>/test-report.md` records an actual run — commands, counts, coverage vs. acceptance criteria
- [ ] `<run-dir>/final-report.md` has a verdict, prioritized fixes, a fix approach per item, deferred items, residual risk
- [ ] `<run-dir>/todo.md` reflects final status for every task

## Interaction with Other Skills

- `cs-spec-driven` / `grill-me` — upstream; this skill assumes the design doc is already stress-tested
- `cs-planning` — invoked **by `cs-architect`** inside Phase 1 to produce the task breakdown
- `/cs-build` — the implementation protocol every domain lead follows
- `cs-code-review` — the review protocol `cs-code-reviewer` applies each round
- `cs-security` / `cs-perf-opt` — the protocols the on-demand auditors apply
- `cs-tdd` — the RED → GREEN discipline inside `cs-build`
- `cs-debugging` — the escape hatch when a test can't be made to pass
- `cs-doubt-driven` — for high-risk or irreversible tasks before implementing
- `cs-shipping` — downstream, once the final report says SHIP
- `cs-sysdocs-update` / `SysDocs/` — when a `SysDocs/` library exists, the architect decomposes from SYSTEM_ROOT + relevant module docs instead of re-guessing boundaries

## See Also

- `../../references/cs-orchestration-patterns.md` — fan-out rules; this skill is the sanctioned exception where a skill (not a persona) sequences personas
- `../../references/cs-definition-of-done.md` — the bar every task clears
- `../../references/cs-testing-patterns.md` — test strategy used in Phase 3
