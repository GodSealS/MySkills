# Team: cs-team-review implementation

- Run: `tasks/team-build/20260910-1015-team-review/`
- Design: `Idea/team-review-design-plan.md` v3 (Implementation-ready)
- Checkpoint: APPROVED — the user's 2026-09-10 `开始实施` instruction authorizes implementation after the accepted design revisions.
- Scope: implement the new review skill, its machine-readable validator/fixtures, routing and adapter integration. No product source or design document changes.

## Roster

| Member | Required phase | Responsibility | Why selected |
|---|---|---|---|
| `cs-architect` | Phase 1, task owner for contracts/routing | Owns skill process text, public artifact contracts, routing, persona metadata, adapter policy, and triage | The design is primarily an orchestration and cross-platform contract; architect must preserve dependency direction and the approved safety gates. |
| `cs-backend-lead` | Phase 2 implementation | Owns `scripts/validate-team-review.py` and JSON/fixture behavior | The validator is executable contract logic with schema, hashing, state, and deterministic verdict checks; it needs an implementation owner separate from the plan author. |
| `cs-code-reviewer` | Every task review round | Reviews staged task diffs across correctness, readability, architecture, security, and performance | Mandatory independent review prevents the architect from approving its own orchestration and validator decisions. |
| `cs-test-engineer` | Phase 3 test sweep | Runs adapter/conformance/validator verification and writes the test report | The design requires an independent full-sweep coverage assessment after all slices are complete; this role is not an implementation owner. |

## Not selected

- `cs-frontend-lead`: no UI, browser interaction, or frontend-owned files are in scope.
- `cs-security-auditor`: security-sensitive path and isolation rules are reviewed by the code reviewer in each slice; call this specialist only if a task introduces a concrete trust-boundary implementation beyond the documented validator/path checks.
- `cs-web-perf-auditor`: no user-facing rendering or performance-budgeted path is changed.

## Operating constraints

- The host skill is the only orchestrator; personas do not fan out or invoke one another.
- Each implementation handoff must name its exact run directory and write allowlist.
- Domain leads stage only their task files and do not commit; Team Build commits once after review approval.
- The user's approval above is the Phase 1 checkpoint. Later ambiguity, failed validation, manifest drift, or a three-round review cap still escalates to the human.
