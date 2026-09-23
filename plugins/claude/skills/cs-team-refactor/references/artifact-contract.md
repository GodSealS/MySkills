# Team Refactor artifact and recovery contract

Read before starting or resuming a run. This is `team-refactor-v1`; its `schema: 1` describes run state, independently of SysDocs schema 2. Markdown carries analysis; JSON carries resume state and content identities. The host is the only state writer.

## Paths

Create a unique `<run-id>` for the target project. Never overwrite an existing run or a completed result.

```text
Idea/team-refactor/<run-id>/
  proposal.md                unique entry with architecture/workflow comparisons and interface/design assessment; draft until final
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
- Primary owner, collaborators, actual/proposed modules and likely files, verified current behavior, effective compatibility contract and separately approved behavior corrections; link affected interface-ledger entries and comparison-diagram changes.
- Dependencies on prior tasks, measurements, data or decisions; one deliverable slice and any API/data coexistence or failure handling.
- For each temporary migration mechanism (such as an adapter or dual operation), an observable exit condition, a linked removal task with owner and dependencies, and acceptance proving the temporary path can be retired while preserving the required behavior. Record when no temporary mechanism is introduced.
- Observable acceptance, exact verification environment and steps or a specifically marked tool to build. Separate structure checks, source/behavior checks and comparable performance measurements. Include a guard metric when performance is claimed.
- Rollback trigger, procedure, data recovery limits and irreversibility.
- Documentation semantic impact, candidate sources/disagreements, extra flow reading for risky boundaries, affected architecture/flow/file pages, summaries, indexes, incoming links and applicable requirements/ADRs. Synchronize and verify these **in the same implementation slice before its fixed review snapshot**, or give a concrete no-impact reason. Do not require unrelated whole-library repair.
- Work estimate as a range with assumptions, risk and confidence. Do not state an unsupported precise benefit.

Research-only outcomes put safe evidence-gathering tasks in the executable plan and label unverified production changes as candidates. `READY` hands the proposal to Team Build only when explicitly requested later; it does not bypass that workflow's prerequisites or checkpoints.

## Proposal analysis

After the required `## 检索摘要`, `proposal.md` includes the following source-backed views. They are part of the frozen review bundle, not separate unreviewed attachments. Keep full evidence in baseline/diagnostics and link it from the proposal.

### Architecture and workflow comparisons

- **架构变动对比图:** paired Mermaid diagrams (or clearly separated before/after subgraphs) showing current versus proposed modules, responsibility/deployment boundaries, interfaces and dependency direction. Label additions, removals, merges and retained relationships in text, not color alone.
- **工作流程变动对比图:** paired flow/sequence diagrams for affected end-to-end paths: trigger, participants, call ordering, input/output, state and error/compensation. Include development/build/release workflow comparisons when those paths change; distinguish them from runtime execution.
- Use the same module/step IDs across each pair, explain rename/split/merge mappings, and link changed nodes/edges to `F-NNN` findings, interface entries and `T-NN` tasks. Mark the after view as **proposed, unimplemented**. Current edges require source/configuration evidence; proposed edges require rationale and validation, never invented current behavior.
- For `NO CHANGE`, show retained structure/flow and explain why. For research-only or blocked drafts, label alternatives and unknowns rather than fabricate a settled after view. If a view is genuinely inapplicable, state why with evidence. Verify diagram syntax/rendering when tools are available and report any unsupported check separately from source verification.

### Interface-change ledger

Use one row per changed interface (API, module contract, event, data boundary or shared component contract). Identify real interfaces by source path and qualified symbol/signature, or method/route or message/schema identity; proposed names must be labeled.

| Interface / finding | Current → proposed contract and change type | Why change / coupling addressed | Providers, consumers and affected flows | Compatibility, migration and rollback | Validation / task |
|---|---|---|---|---|---|

Explain additions, removal, merge/split, ownership moves and signature/semantic changes, including applicable errors, permissions, ordering and data guarantees. If no interface changes, say so with scope evidence. Do not leave empty template rows in the published result.

### Global coupling, consolidation and extension assessment

Architect and relevant domain owners examine the target in context: direct callers/callees, shared contracts/data, dependency cycles and change propagation. Record inspected boundaries and gaps; a module-only scan cannot justify a whole-project conclusion. Report these three decisions in concise tables or prose, linking findings, source evidence and affected tasks:

1. **Unnecessary versus beneficial coupling.** Reducing unnecessary coupling is the first priority. **Coupling that improves runtime performance is acceptable.** Identify the retained coupling, the runtime benefit, maintenance/change cost and why that balance is acceptable. With measurements, record workload/environment, baseline and guard metrics; without measurements, label the benefit a hypothesis and assign verification before the dependent decision. Lack of measurement alone is not an instruction to remove coupling. Respect correctness, security and accepted compatibility constraints.
2. **Interfaces that can be merged.** Name candidate interfaces, semantic overlap, providers/consumers and duplicate responsibilities; compare merge versus keeping separate. Recommend consolidation only where contracts, ownership and evolution fit. Explain rejected merges where superficially similar interfaces serve different permissions, lifecycles or failure guarantees, or would create wider coupling. If none qualify, record the inspected candidates and reason.
3. **Modules where a design pattern aids extension.** Identify the concrete variation point and likely supported change, then compare an applicable pattern (for example Strategy, Adapter or Observer) with a simpler local design and the current design. State extension benefit, dependency direction, complexity/runtime cost, migration and tests. Choose a pattern only when it solves that module's demonstrated problem; retaining the existing design or using no pattern is a valid conclusion. Avoid speculative frameworks and unmeasured performance claims.

The host verifies that diagrams, the ledger, findings and tasks agree, all applicable interface changes are covered, retained performance coupling is reasoned, and independent experts reviewed the same candidate version. Proposal work never claims these changes have been implemented.
