---
name: cs-team-build
description: "Manually runs a design document through a coordinated agent team — the architect decomposes, leads implement, a reviewer audits, an advisor recommends fixes for expert verification, and a test engineer verifies the whole. Invoke only through an explicit skill request or the team-build command; never auto-select it from task intent. / 手动用 Agent 团队把设计文档落地：仅可由显式技能请求或团队构建命令触发，不得按任务意图自动选择。"
argument-hint: "<path-to-design-doc>"
user-invocable: true
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task
---

# Team Build — Multi-Agent Implementation

## Overview

A single agent implementing a non-trivial design doc fails in a predictable way: it writes plausible code, reviews its own work, and declares victory. This skill replaces that with a **team** — a fixed cast of personas, a file-based handoff trail, and a **bounded** review loop (max 3 rounds per task) that cannot spin forever.

The team is not a chat. Every handoff is a **file** under a unique run directory, `tasks/team-build/<run-id>/`. That makes the loop auditable, resumable, and safe to re-run without overwriting another run.

Two rules hold throughout:

1. **The skill orchestrates, not the personas.** Personas never call each other. Every fan-out is issued by this skill. (See `../../references/cs-orchestration-patterns.md` — this skill is the sanctioned orchestrator for the team loop.)
2. **Files are the handoff medium.** No "as we discussed" context. If it isn't in the handoff doc, it doesn't exist.

## When to Use

**Manual invocation only.** Run this workflow only when the user explicitly invokes `cs-team-build` or an approved command that invokes it (currently `/cs-team-coding`). Do not select or start it solely because a request contains a design/spec document, spans multiple modules, or mentions a team.

- You have a design/spec document and want it implemented end-to-end
- The change spans modules or domains (frontend + backend), so one agent won't hold it all in context
- You want implementation to come with review, test, and triage — not just code
- You want a resumable trail you can audit or hand to a human mid-flight

**When NOT to use:**

- Single-file or obvious-scope change → `cs-incremental`
- No document yet, only an idea → `cs-spec-driven`
- You just want a review of existing code → `cs-code-review`
- You want a multi-agent review without implementation → `cs-team-review`
- Emergency hotfix where a 3-round loop is the wrong shape → `cs-debugging`

## Team Roster

A team has **at least 4 members**. Three are mandatory:

| Member | Required | Role in the loop |
|---|---|---|
| `cs-architect` | **Always** | Decomposes tasks, proposes implementation owners, implements structural artifacts, and answers architecture questions |
| `cs-review-advisor` | **Always** | Reviews the plan, proposes focused fixes and report synthesis; relevant experts verify its advice |
| `cs-code-reviewer` | **Always** | Five-axis review of every implemented slice (correctness, readability, architecture, security, performance) |
| `cs-backend-lead` | If the doc implies API / data / server work | Implements backend-owned tasks via `/cs-build` |
| `cs-frontend-lead` | If the doc implies UI / interaction / browser work | Implements frontend-owned tasks via `/cs-build` |
| `cs-security-auditor` | On demand, triggered by the host | Assists a round when the slice touches a trust boundary |
| `cs-web-perf-auditor` | On demand, triggered by the host | Assists a round when the slice is user-facing or perf-budgeted |
| `cs-test-engineer` | Phase 3 (always, once) | Runs the full suite, analyzes coverage, writes `<run-dir>/test-report.md` |
| `cs-knowledge-base-admin` | Phase 5 (always, once) | Refreshes only knowledge bases that already exist in the project |

The architect proposes implementation owners and the host validates the roster. The minimum is `cs-architect` + `cs-review-advisor` + `cs-code-reviewer` + one domain lead; these roles need not occupy simultaneous concurrency slots.

## Artifact Layout

Everything lives under `tasks/team-build/<run-id>/` at the repo root. Create a fresh run directory before writing; never overwrite an existing run (see AGENTS.md "Defensive File Writing"). Record the run directory in every handoff.

```
tasks/team-build/<run-id>/
├── team.md                      # roster + why each member was picked
├── plan.md                      # cs-planning output — the task breakdown
├── todo.md                      # checklist: id, title, owner, status, rounds used
├── reviews/
│   ├── 00-plan-review.md        # advisor recommendations + expert verification
│   ├── T01-r1-code-review.md    # cs-code-reviewer, round 1
│   ├── T01-r1-security.md       # when the host trigger matches
│   ├── T01-r1-perf.md           # when the host trigger matches
│   └── T01-r1-fixes.md          # advisor recommendations + expert verification
├── test-report.md               # cs-test-engineer (Phase 3)
├── final-report.md              # advisor draft + expert evidence + host verdict
└── knowledge-base-report.md     # cs-knowledge-base-admin (Phase 5; only when at least one supported KB exists)
```

## Process

### Phase 0 — Preflight (skill, no fan-out)

1. Resolve the design doc from `$ARGUMENTS`. If missing or unreadable, **stop** and ask for the path.
2. Confirm a clean baseline: `git status --porcelain`. If there are uncommitted changes outside the selected `<run-dir>/`, stop and ask the user to commit, stash, or confirm.
3. Create a fresh `tasks/team-build/<run-id>/reviews/` directory (for example, a timestamp plus short random suffix). If the selected run directory already exists, stop and choose a new run id; never overwrite prior handoffs.
4. Establish task-specific context using `../../references/sysdocs-design-context.md` and the dual-layout inventory in `../../references/sysdocs-system.md`. Read relevant accepted specs/ADRs, then schema 2 navigation/summaries or the legacy manifest and necessary bodies; verify key facts with source and available KB candidates. Record state, affected modules, source/document evidence and gaps in `<run-dir>/team.md`. Missing SysDocs or unrelated old defects do not force init, full repair or refresh before decomposition. Required task constraints/evidence must be available; explicitly requested full documentation remains an acceptance condition.

### Phase 1 — Architect decomposes (FAN-OUT → `cs-architect`)

Fan-out to `cs-architect` with the design doc path and the preflight SysDocs context. The architect:

1. Reads the whole design doc.
2. **Proposes the roster, including the three mandatory roles.** Which domain leads are actually needed — `cs-backend-lead`, `cs-frontend-lead`, or both — and says why in one line each. Record it in `<run-dir>/team.md`; the host validates it.
3. **Invokes the `cs-planning` skill** to break the doc into executable tasks. Vertical slices, not horizontal layers. Every task needs: id, title, description, **primary owner** (`arch` / `frontend` / `backend`), acceptance criteria, verification steps, dependencies, files likely touched.
4. Writes `<run-dir>/plan.md` (full breakdown) and `<run-dir>/todo.md` (tracking checklist with a `Rounds` column).
5. Constraint: `arch` tasks are limited to public contracts, module skeletons, and cross-cutting config. Business features go to a domain lead.
6. Each task references affected modules and verified boundaries, maps requirements to acceptance criteria, and records semantic/documentation impact or a specific no-impact reason. Proposed boundaries require architect decisions and corresponding navigation/index updates in the active layout; absent documentation does not justify invented established module IDs.

**Plan review:** the host fans out `cs-review-advisor` with the plan, constraints, preflight SysDocs context, allowed context and `<run-dir>/reviews/00-plan-review.md`. The advisor checks executability, module traceability and acceptance gaps. The host sends its recommendations to relevant experts under the Advice and verification protocol below; architecture questions return to `cs-architect`. Record how each plan finding was addressed or explicitly accepted as risk before presenting the plan. The host records `review-advisor-v1`, this skill path and its source version in `team.md`.

**Checkpoint:** present `<run-dir>/team.md` + `<run-dir>/plan.md` + plan review to the human. Get an unambiguous affirmative before any code is written. After it, the team runs task by task, subject to the existing escalation gates and immediate blocking-dispute rule below.

### Phase 2 — Execution loop (per task, max 3 rounds)

For each task `T<NN>` in dependency order, run at most **3 rounds**. A round has three steps.

**Step 1 — IMPLEMENT.** FAN-OUT to the task's primary owner:

- `backend` → `cs-backend-lead`
- `frontend` → `cs-frontend-lead`
- `arch` → `cs-architect`

Supply applicable specs/ADRs, affected descriptions and source evidence to the lead using the shared task-context protocol. Instruct the lead to reuse only `/cs-build`'s implementation cycle (`cs-incremental` + `cs-tdd`) for exactly this task: read acceptance criteria → RED → GREEN → regression suite → build → **stage only this task's files and stop before committing**. Skip the final knowledge-base-administrator step; Team Build owns its single invocation in Phase 5. Team Build also owns the single task commit after review approval.

For round 1 the input is `<run-dir>/plan.md#T<NN>`. For rounds 2-3 the input is `<run-dir>/reviews/T<NN>-r<k>-fixes.md` — the lead implements the directive, stages only this task's files, and does nothing else. Scope discipline applies: no drive-by refactors, no "while I'm here" changes.

Before fixing each review snapshot, synchronize the slice's affected descriptions, summaries, file indexes, incoming links and approved requirements/decisions; use `cs-sysdocs-update` when maintaining a library. Existing authorization covers necessary reversible synchronization. Combine KB and summary candidates, verify source, and expand high-risk flow reading as the shared protocol requires. Stage corresponding document changes with the task and record scoped structural checks separately from content/behavior verification in the round's existing handoff. Reuse valid evidence; a specific no-impact explanation needs no empty update report. Current-change omissions block DONE; unrelated inherited defects are recorded separately. Later related changes invalidate affected reviews and require new verification.

**Step 2 — REVIEW.** FAN-OUT to `cs-code-reviewer` (`cs-code-review`). Review the task's staged diff (`git diff --cached`), not the whole branch; the handoff must include the base commit and the exact staged file list. Review across all five axes and write the result to `<run-dir>/reviews/T<NN>-r<k>-code-review.md` using the reviewer's standard output template, ending with a verdict:

**Verdict:** `APPROVE` | `REQUEST CHANGES`

**Step 3 — ADVICE AND EXPERT VERIFICATION.** The host applies the specialist triggers below in every round, even if the code reviewer says `APPROVE`. It fans out triggered specialists and then `cs-review-advisor` with all review files, original finding IDs, constraints, the fixed staged snapshot, and the allowed `-fixes.md` path. The advisor performs focused evidence review and proposes fixes or approval; it does not repeat an unrestricted five-axis review or commit files.

| Specialist | Call it when the slice touches |
|---|---|
| `cs-security-auditor` | authn/authz, user input crossing a trust boundary, data access / queries / SQL, secrets or env, file upload, external integrations, payments |
| `cs-web-perf-auditor` | user-facing UI, list/table/image rendering, bundle size, Core Web Vitals budget, animation or scroll paths |

Specialists run **within the same round**, writing `<run-dir>/reviews/T<NN>-r<k>-security.md` / `-perf.md`. The host sends advisor proposals to relevant experts for fresh detection under the protocol below and collects their evidence in the existing `-fixes.md` handoff. Use the relevant domain expert, code reviewer or test engineer for each recommendation; an implementer cannot independently approve its own structural or feature change. Missing verification blocks approval. Advisor discoveries retain their source and undergo expert confirmation rather than becoming facts through synthesis.

The host merges original reviews and verified advice. Only `APPROVE` with no open Critical or Important findings, completed specialist triggers, required fix verification, and passing SysDocs synchronization/validation evidence for the reviewed snapshot permits the host to commit staged task files once (when authorized), mark DONE, and continue. A user instruction not to commit takes precedence; report the uncommitted result. Suggestions alone never consume another round.

Otherwise the advisor writes actionable recommendations to `<run-dir>/reviews/T<NN>-r<k>-fixes.md`; the host records expert verification and accepted instructions there, then increments the round counter. Unresolved blocking disputes immediately follow the user escalation protocol below, before another implementation round. Architecture changes or repeated P0 require `cs-architect` consultation/re-slicing in Phase 1, retaining round and approval history.

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
- [ ] Changes staged, this task's files only; host commits once after approval when authorized
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

### Phase 4 — Advisor synthesis (FAN-OUT → `cs-review-advisor`)

Before synthesis, aggregate still-valid slice documentation evidence and check only new impacts or unresolved required gaps; do not unconditionally refresh or validate the entire library again. Any resulting target changes return through affected review and verification gates. Fan-out to `cs-review-advisor` with open findings, verification history, `<run-dir>/test-report.md`, and the scoped document/source evidence. It writes a draft in `<run-dir>/final-report.md` without replacing actual test evidence. The host obtains relevant expert verification, consults `cs-architect` only for architecture consequences, then records the final verdict:

1. **Verdict:** `SHIP` | `FIX FIRST`
2. **Fix priorities** — proposed from the test report and open findings, with relevant expert evidence; architectural consequences require architect consultation. A flaky integration test on a core flow outranks a missing unit test on a utility.
3. **Fix approach per item** — for each P0/P1: which owner should take it, which files, the suggested technique, and the risk if it's done wrong. This is the part the test report does not provide.
4. **Deferred items** — what is being accepted, with the rationale.
5. **Residual risk** — what the human should know before shipping.
6. **Documentation verification** — affected modules and document changes (or a concrete no-impact result), existing evidence locations, structural method/result, separate content/behavior checks, source scope and unresolved necessary gaps. Required missing/failed evidence or current-change omissions require `FIX FIRST`; unrelated old defects are separate. A KB refresh or structural PASS cannot replace content verification.

If the verdict is `FIX FIRST`, do **not** auto-start the fixes. Present the prioritized list and get approval — then each fix re-enters Phase 2 as a new task with a fresh 3-round budget.

### Phase 5 — Wrap-up

- Update `<run-dir>/todo.md` so every task shows a final status
- **Final operational step — FAN-OUT to `cs-knowledge-base-admin`.** Pass the project root and `<run-dir>/knowledge-base-report.md`. The administrator checks only `.codegraph/`, `.understand-anything/`, and `graphify-out/` directly under that root. If all three are absent, it terminates with a prerequisite message, creates nothing, and does not write the report. Otherwise it refreshes each existing knowledge base independently; missing directories or unavailable update mechanisms are `SKIPPED`, not errors. Include its report or termination message in the final handoff.
- Report to the human: tasks completed, rounds used per task, commits made, tests added, open P1/P2 items
- Stop or dismiss any persistent team members using the host platform's supported lifecycle operation, if one was created; do not invent tool calls.

## Advice and verification protocol

The advisor only recommends. For every recommendation, the host assigns a relevant expert to examine the target again and record **全部可取 / 部分可取 / 完全不可取** (fully / partly / not acceptable), identifying accepted and rejected parts with finding ID, suggestion, target snapshot, method, result and unknowns. Record this separately from finding confirmation and repair verification in the current approved plan review, `-fixes.md`, or final report. Preserve original severities and sources; Suggestions must not be promoted merely to enforce preference.

Every advisor brief includes the installed agent file and private resource directory as absolute paths, target/baseline snapshot, purpose, constraints, permitted context and exact output paths. Private resources resolve from that installed location, never the target cwd. Missing resources mean an incomplete installation, not permission to substitute public review skills. The host collects isolated drafts into approved handoffs; experts and advisors never overwrite one another's evidence.

Include the advisor's task-specific Documentation-driven review inputs in each relevant brief: project root, inventory evidence, applicable specs/ADRs, affected document/source snapshots and phase-appropriate structural/content evidence. Use the active layout; record absent or unnecessary documentation honestly without forcing initialization. Permitted read context grants no advisor writes. The host owns authorized maintenance and records gaps in existing plan, round or final artifacts.

Return the expert's rejected parts and evidence to the advisor, unless its recorded position already explicitly covers that rejection and supporting evidence. Allow at most one focused position confirmation to establish whether the rejected part remains blocking; do not infer its stance or start a debate loop. Missing confirmation blocks dependent approval; a confirmed blocking disagreement triggers the next paragraph immediately.

If an expert rejects any part (including all) and the advisor still regards that rejected part as blocking, the host **immediately opens a user-choice dialog**, showing disputed parts, both evidence sets, impacts and available paths. Record the actual answer in the current handoff. Keep the task `pending-human` in its Markdown tracking record and pause dependent repair/approval until the user answers; do not spend another discussion round or wait for round 3. If the host has no dialog tool, ask the same question directly and await the answer. Fact disputes likewise require human resolution.

Accepted advice does not close a finding. The implementer must complete the repair and the relevant expert must verify the repaired snapshot against the original finding before the host records it resolved. Record implementation and verification evidence separately; user risk choices are not repair evidence. Structural artifacts implemented by `cs-architect` still require independent first review and expert verification.

For new modules, dependency changes, public contracts, technology choices or ADR tradeoffs, the advisor writes `Architecture questions` with finding ID, current constraints, alternatives, impacts and the exact decision needed. The host consults `cs-architect` and retains its answer in the current handoff. Unanswered questions stay open/blocked; fact disputes take precedence and become pending-human.

## Run protocol compatibility

New runs record `review-advisor-v1`, the skill path and source version in `team.md`. Completed runs stay unchanged. An in-progress legacy run completes under its recorded original role protocol; if that protocol cannot be reliably obtained, preserve the legacy run and start a new run from the same target. Never silently replace its authors or overwrite its history.

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
| "The architect can just fix this line, it's faster" | The advisor recommends, experts verify, and the lead implements. Blur that line and you lose the review record. |
| "Security/perf review can wait until the end" | By then every slice has been built on the same wrong assumption. Decide within the round. |
| "Skip the roster, just use both leads" | An unnecessary lead writes code nobody asked for. The architect proposes owners; the host validates the roster. |
| "Suggestions are worth another round" | No. Note them, move to the next task. |
| "The plan is approved, don't stop again" | The gate is per-run, not per-decision. Ambiguity and exhausted rounds still stop you. |

## Red Flags

- A review document with no `file:line` references — the reviewer didn't actually read the diff
- Two consecutive rounds with the same P0 — the task is mis-sliced, go back to Phase 1
- An implementer committing files outside its task
- The advisor editing target code or the architect implementing business features
- `<run-dir>/reviews/` empty but all tasks marked DONE — the loop was skipped
- Rounds consumed evenly at 3 across every task — systemic problem (unclear doc), not per-task variance
- `<run-dir>/test-report.md` written from the plan instead of from an actual test run
- A final report that lists problems without a fix approach per item

## Verification

- [ ] `<run-dir>/team.md` lists ≥4 members, including `cs-architect`, `cs-review-advisor`, and `cs-code-reviewer`, with a reason for each
- [ ] Preflight records task-specific inventory, authoritative constraints, relevant document/source evidence and gaps without forcing unrelated initialization or repair.
- [ ] Each slice synchronizes its affected scope and separates structure/content evidence; final synthesis reuses valid checks. Current-change omissions or required gaps prevent DONE/SHIP, while unrelated old defects remain separate.
- [ ] `<run-dir>/plan.md` exists; every task has acceptance criteria, verification, and a primary owner
- [ ] The human approved the roster + plan before implementation started
- [ ] Every task ran ≤3 rounds; any task that hit the cap was escalated, not silently continued
- [ ] Every round has a `<run-dir>/reviews/T<NN>-r<k>-code-review.md` with an explicit verdict and base commit/staged file list
- [ ] Every non-approved round has a matching `-fixes.md` directive with P0/P1/P2 and concrete fixes
- [ ] Required security/perf audits were issued by the host, with the trigger recorded
- [ ] One host-owned commit per task only when authorized, containing only task files after approval; an explicit no-commit instruction is honored
- [ ] `<run-dir>/test-report.md` records an actual run — commands, counts, coverage vs. acceptance criteria
- [ ] `<run-dir>/final-report.md` has a verdict, prioritized fixes, a fix approach per item, deferred items, residual risk
- [ ] `<run-dir>/todo.md` reflects final status for every task
- [ ] If a supported knowledge base exists, `<run-dir>/knowledge-base-report.md` records every existing/missing supported knowledge base and confirms none was created; otherwise the final handoff records the administrator's prerequisite termination message

- [ ] Plan advice and subsequent recommendations have itemized expert acceptability evidence; approval of advice was not treated as repair closure
- [ ] Blocking disagreement caused immediate user choice and pending-human suspension; repair verification is required even after a user choice
- [ ] Architecture questions were delegated by the host only; legacy run protocol and authorship were preserved

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
- `cs-sysdocs-init` / `cs-sysdocs-update` / `SysDocs/` — the host follows the shared task-context protocol, synchronizes affected slice documents, and reuses valid evidence at delivery. Full initialization/refresh occurs only when requested; legacy and schema 2 layouts are both readable.
- `cs-knowledge-base-admin` — final subagent refreshes existing knowledge bases only; it never bootstraps one

## See Also

- `../../references/cs-orchestration-patterns.md` — fan-out rules; this skill is the sanctioned exception where a skill (not a persona) sequences personas
- `../../references/cs-definition-of-done.md` — the bar every task clears
- `../../references/cs-testing-patterns.md` — test strategy used in Phase 3
