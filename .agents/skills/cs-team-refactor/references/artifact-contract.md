# Team Refactor artifact and recovery contract

Read before starting or resuming a run. This is `team-refactor-v1`; its `schema: 1` describes run state, independently of SysDocs schema 2. Markdown carries analysis; JSON carries resume state and content identities. The host is the only state writer.

## Paths

Create a unique `<run-id>` for the target project. Never overwrite an existing run or a completed result.

```text
Idea/team-refactor/<run-id>/
  proposal.md                unique proposal entry; draft until final
  implementation-plan.md     staged tasks, dependencies and acceptance
  decisions.md               optional proposed decisions, never accepted ADRs
tasks/team-refactor/<run-id>/
  scope.md                   target, focus, constraints, context and capability gaps
  team.md                    roster, assignments, installed role/protocol paths and review-advisor-v1 source
  state.json                 host state and assignment progress
  manifest.json              inputs and accepted outputs with content identities
  baseline.md                observable behavior, requirements and measured baseline
  findings.md                F-NNN observations and decisions
  diagnostics/<batch>-<role>.md
  measurements/              only if real, redacted results exist
  reviews/r<N>-<role>.md      never replace an earlier review
  drafts/r<N>-proposal.md    never replace an earlier candidate
  drafts/r<N>-implementation-plan.md
  drafts/r<N>-decisions.md   when decisions are part of this candidate
  human-decisions.md         only for actual user answers
```

Only the current run paths are writable. Proposed current-architecture or decision changes remain in these proposal files. Scope expansion for **reading** direct callers/callees and high-risk flows is recorded; it does not authorize changing a wider scope. Existing authoritative specs and ADRs stay in place. An accepted ADR superseded later needs a new decision and supersession relationship, not edits to its historical conclusion.

## State and manifest

Use JSON at least equivalent to:

```json
{
  "schema": 1,
  "protocol": "team-refactor-v1",
  "run_id": "20260916-example",
  "status": "running",
  "phase": "preflight",
  "focus": "both",
  "round": 0,
  "input_manifest": "manifest.json",
  "completed_assignments": [],
  "pending_assignments": [],
  "decision_refs": [],
  "verdict": null
}
```

`status`: `running | blocked | pending-human | complete`. `phase`: `preflight | baseline | diagnose | options | plan | review | finalize`. `round` is 0 before first review and 1–3 in review. Each assignment needs ID, role, input content identity, exact output path, status and failure count. `complete` can carry `READY`, `RESEARCH REQUIRED` or `NO CHANGE`; `BLOCKED` carries `blocked` or `pending-human` and never masquerades as an approved proposal.

The manifest separates **inputs** from run **outputs**. Record project root, Git HEAD or `unversioned`, staged/unstaged/untracked inputs actually used, accepted specs/ADRs and documentation used, relative path, size and SHA-256. For each bounded source/document directory or path pattern selected as a read scope, also record the included relative-path inventory and its identity. This is a bounded run record, not a permanent full-repository fingerprint database; source contents stay in their original files. Capture output identities only after accepting isolated artifacts; generating or revising a run file must not invalidate the target input snapshot.

## Review versions

Before each review round, freeze `proposal.md`, `implementation-plan.md` and applicable `decisions.md` in the round's `drafts/r<N>-*.md` files. Record each frozen path, SHA-256 and corresponding final proposal path in the manifest; record explicitly when no decisions file applies. Keep earlier candidates and reviews unchanged. Each review assignment's input identity includes both the target snapshot and this complete candidate bundle; its review artifact names the round and those identities.

A change to any candidate document invalidates confirmations affected by that change. Freeze the revised bundle in the next round and rerun affected reviews; carry forward an unaffected confirmation only with its original version reference and an explicit reason it still applies. These revisions count toward the skill's three-round limit. Adding or removing a decisions file also changes the bundle. An unchanged target snapshot alone does not preserve approval of a changed plan.

Before publication, compare all final proposal files with the reviewed bundle and verify that each required confirmation covers that version or has documented unaffected reuse. Draft/final labels and relative links may be adjusted for publication only with a recorded diff showing no change to the reviewed meaning; substantive edits, including synthesis edits, require the same affected review. If the review limit is exhausted, preserve the revised draft and unresolved list with `BLOCKED` rather than publishing an unreviewed version.

## Recovery

Before resume or publication, validate the protocol version, state fields, phase dependencies, input identities, accepted artifact integrity and review bindings. Re-enumerate the recorded read scopes; an added/deleted path is drift even when it was not previously read. A changed target input freezes the old run and starts a linked new run. Reuse unchanged artifacts only with their provenance and applicability rechecked. Candidate edits within unchanged target inputs follow Review versions in the same run. Completed runs remain immutable.

Resume only missing, failed or invalidated assignments. Retry a required expert once on unchanged assignment inputs; then block the affected conclusion. If a prior run lacks a complete review binding, preserve its evidence but treat the affected review as unverified and obtain it within the remaining rounds; if none remain, return `BLOCKED`.

Maintain a single writer using the host's supported atomic lock or equivalent. If the host cannot enforce it, say concurrent resume is unsupported and avoid parallel resume. An expert may write only its one assigned output in an isolated environment. Host verifies location and content, then accepts it into the run. On an out-of-scope write, stop and report what changed; never blindly restore it.

## Implementation task fields

Each `T-NN` task includes:

- Type (`baseline | refactor | performance | migration | docs`), source `F-NNN` IDs, goal and evidence links.
- Primary owner, collaborators, actual/proposed modules and likely files, verified current behavior, effective compatibility contract and separately approved behavior corrections.
- Dependencies on prior tasks, measurements, data or decisions; one deliverable slice and any API/data coexistence or failure handling.
- For each temporary migration mechanism (such as an adapter or dual operation), an observable exit condition, a linked removal task with owner and dependencies, and acceptance proving the temporary path can be retired while preserving the required behavior. Record when no temporary mechanism is introduced.
- Observable acceptance, exact verification environment and steps or a specifically marked tool to build. Separate structure checks, source/behavior checks and comparable performance measurements. Include a guard metric when performance is claimed.
- Rollback trigger, procedure, data recovery limits and irreversibility.
- Documentation semantic impact, candidate sources/disagreements, extra flow reading for risky boundaries, affected architecture/flow/file pages, summaries, indexes, incoming links and applicable requirements/ADRs. Synchronize and verify these **in the same implementation slice before its fixed review snapshot**, or give a concrete no-impact reason. Do not require unrelated whole-library repair.
- Work estimate as a range with assumptions, risk and confidence. Do not state an unsupported precise benefit.

Research-only outcomes put safe evidence-gathering tasks in the executable plan and label unverified production changes as candidates. `READY` hands the proposal to Team Build only when explicitly requested later; it does not bypass that workflow's prerequisites or checkpoints.
