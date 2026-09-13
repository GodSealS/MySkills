# Plan: implement `cs-team-review`

## Context and architecture

The authoritative design is `Idea/team-review-design-plan.md` v3. The implementation source of truth is `.codebuddy/`; generated `skills/`, `.agents/`, `.gemini/`, `.claude/`, `plugins/`, and `commands/` trees are adapter outputs. The new skill is an orchestrator, not a reviewer: it sequences persona fan-out, persists file handoffs, validates JSON contracts, and blocks incomplete or unsafe runs.

Dependency direction:

`SKILL.md` contract + schema validator -> command/router/persona references -> adapter tests and fixtures -> generated adapters -> independent skill review.

No task may edit product source, `Idea/team-review-design-plan.md`, hooks, settings, or install logic.

## T01 — Canonical orchestration skill

**Description:** Create `.codebuddy/skills/cs-team-review/SKILL.md` as the sole implementation source. Encode Phase 0-3 behavior, code/design/mixed classification, isolation and allowlist contract, manifest/hash checks, JSON handoffs, deterministic finding merge, verdict gates, failure/resume state machine, and self-contained templates. Keep the skill directory to `SKILL.md` only.

**Primary owner:** `arch`

**Acceptance criteria:**
- [ ] Frontmatter has `name: cs-team-review`, a multi-agent team-review trigger description, `agent: cs-architect`, and `user-invocable: true`; it has no `model:`.
- [ ] Process defines Phase 0-3, `code | design | mixed`, the AND体量门槛, object-routing exits, isolation degradation rule, canonical path/symlink checks, run lock, manifests, and resume drift behavior.
- [ ] JSON schema v1 is the machine fact source; Markdown is a rendered view; `unconfirmed`, `failed`, `blocked`, and `pending-human` cannot produce complete/APPROVE output.
- [ ] Finding IDs/fingerprints, expert decisions, deterministic merge precedence, conflict routing, and verdict calculation are explicit and executable by the validator.
- [ ] The skill does not invoke `cs-grill-me`, does not permit persona nesting, and explicitly separates code-reviewer verdicts from top-level `REJECT`.

**Verification:**
- [ ] Static frontmatter and forbidden-field checks using `rg`/PowerShell.
- [ ] `cs-skill-review` fixture/validator later confirms all required sections and failure modes.
- [ ] Code reviewer checks the staged `SKILL.md` for line-addressed contract gaps.

**Dependencies:** None

**Files likely touched:** `.codebuddy/skills/cs-team-review/SKILL.md`

**Estimated scope:** Large (1 long contract file)

## T02 — Schema validator and contract fixtures

**Description:** Implement the schema v1 validator for findings, confirmations, assignments, run state, and final-review frontmatter. Add deterministic fingerprint/hash checks, enum validation, required-expert completeness checks, degraded-isolation verdict blocking, and fixtures for valid/invalid artifacts and merge edge cases.

**Primary owner:** `backend`

**Acceptance criteria:**
- [ ] `scripts/validate-team-review.py` validates every artifact class named in the design and returns non-zero for malformed JSON, invalid enums, missing evidence/fix, fingerprint mismatch, manifest/patch mismatch, incomplete experts, and illegal complete/APPROVE states.
- [ ] Valid complete and valid blocked/pending-human fixtures pass their expected checks; REJECT+CONFIRM, empty CONFIRM, NEW finding, and mixed-source alias cases follow deterministic rules.
- [ ] Canonical SHA-256 normalization is documented in code/help and covered by fixtures; path traversal/symlink and oversized/sensitive manifest entries are rejected.
- [ ] Validator has no network, product-code writes, or dependency on generated adapter trees.

**Verification:**
- [ ] `python scripts/validate-team-review.py tests/fixtures/team-review --all`.
- [ ] Focused negative cases assert non-zero exit and actionable diagnostics.
- [ ] Code reviewer inspects staged validator and fixture diff.

**Dependencies:** None (the v3 design already locks the schema; T01 consumes and documents the same contract)

**Files likely touched:** `scripts/validate-team-review.py`, `tests/fixtures/team-review/**`, `tests/test_validate_team_review.py` (if the repository's test convention supports it)

**Estimated scope:** Large (3-5 logical files plus fixtures)

## T03 — CodeBuddy command surface

**Description:** Add the thin `/cs-team-review` command that routes to the canonical skill without duplicating workflow prose.

**Primary owner:** `arch`

**Acceptance criteria:**
- [ ] `.codebuddy/commands/cs-team-review.md` contains the command frontmatter and a minimal invocation of `cs-team-review` with `$ARGUMENTS`.
- [ ] It does not embed a second implementation of Phase 0-3.

**Verification:**
- [ ] Compare command source with generated `commands/cs-team-review.md` after adapter build.
- [ ] Gemini TOML and Codex prompt generation tests find the command/skill entry.

**Dependencies:** T01

**Files likely touched:** `.codebuddy/commands/cs-team-review.md`

**Estimated scope:** Small (1 file)

## T04 — Router integration

**Description:** Update root and CodeBuddy router/context files so team review has a distinct trigger boundary from single-person code review and shipping.

**Primary owner:** `arch`

**Acceptance criteria:**
- [ ] Root `AGENTS.md`, `.codebuddy/AGENTS.md`, and `.codebuddy/CODEBUDDY.md` map multi-agent/team review requests to `cs-team-review`; single-person code review and shipping remain distinct.
- [ ] Router/context wording states that the host skill orchestrates and personas never fan out.

**Verification:**
- [ ] `rg -n "cs-team-review|team review|cs-code-review|cs-shipping"` across the listed files; inspect each match.
- [ ] Code reviewer checks bidirectional trigger wording and stale-reference absence.

**Dependencies:** T01, T03

**Files likely touched:** `AGENTS.md`, `.codebuddy/AGENTS.md`, `.codebuddy/CODEBUDDY.md`

**Estimated scope:** Medium (3 files)

## T05 — Skill cross-reference integration

**Description:** Update `cs-using`, `cs-team-build`, `cs-code-review`, and orchestration references so team review is the second sanctioned skill orchestrator, with distinct trigger and handoff boundaries.

**Primary owner:** `arch`

**Acceptance criteria:**
- [ ] Cross-references describe `cs-team-build` and `cs-team-review` as the only skill-level persona serializers and state that personas never fan out.
- [ ] `cs-code-review` distinguishes single-person review from multi-agent review; no reference claims PR-number support in v1 or points at a nonexistent `DESIGN.md`.

**Verification:**
- [ ] `rg -n "cs-team-review|sanctioned|PR|DESIGN.md"` across the listed files; inspect each match.
- [ ] Code reviewer checks bidirectional trigger wording and stale-reference absence.

**Dependencies:** T01, T03

**Files likely touched:** `.codebuddy/skills/cs-using/SKILL.md`, `.codebuddy/skills/cs-team-build/SKILL.md`, `.codebuddy/skills/cs-code-review/SKILL.md`, `.codebuddy/references/cs-orchestration-patterns.md`

**Estimated scope:** Medium (4 files)

## T06 — Core persona roster and read-only boundaries

**Description:** Add `cs-team-review` to the architect, backend, code-reviewer, and frontend persona Skill Rosters/Invoked-by sections; document that frontend/backend leads act as domain reviewers here and no persona may nest fan-out.

**Primary owner:** `arch`

**Acceptance criteria:**
- [ ] `cs-architect`, `cs-backend-lead`, `cs-code-reviewer`, and `cs-frontend-lead` mention `cs-team-review` in the appropriate roster.
- [ ] Frontend/backend wording forbids implementation in this workflow; all four personas forbid nested Task/fan-out.
- [ ] Generated platform agents inherit the canonical wording after adapter build.

**Verification:**
- [ ] `rg -l "cs-team-review" .codebuddy/agents/cs-architect.md .codebuddy/agents/cs-backend-lead.md .codebuddy/agents/cs-code-reviewer.md .codebuddy/agents/cs-frontend-lead.md` returns all four personas.
- [ ] Adapter test checks generated agent copies and no unintended tool/model changes.

**Dependencies:** T01

**Files likely touched:** `.codebuddy/agents/cs-architect.md`, `.codebuddy/agents/cs-backend-lead.md`, `.codebuddy/agents/cs-code-reviewer.md`, `.codebuddy/agents/cs-frontend-lead.md`

**Estimated scope:** Medium (4 files)

## T07 — Specialist persona roster and read-only boundaries

**Description:** Add `cs-team-review` to the security, test, and performance persona rosters and document their narrow review-only boundaries.

**Primary owner:** `arch`

**Acceptance criteria:**
- [ ] `cs-security-auditor`, `cs-test-engineer`, and `cs-web-perf-auditor` mention `cs-team-review` in the appropriate roster.
- [ ] Test engineer wording forbids business-test execution and test-file edits; all three personas forbid nested Task/fan-out.
- [ ] Generated platform agents inherit the canonical wording after adapter build.

**Verification:**
- [ ] `rg -l "cs-team-review" .codebuddy/agents/cs-security-auditor.md .codebuddy/agents/cs-test-engineer.md .codebuddy/agents/cs-web-perf-auditor.md` returns all three personas.
- [ ] Adapter test checks generated agent copies and no unintended tool/model changes.

**Dependencies:** T01

**Files likely touched:** `.codebuddy/agents/cs-security-auditor.md`, `.codebuddy/agents/cs-test-engineer.md`, `.codebuddy/agents/cs-web-perf-auditor.md`

**Estimated scope:** Small (3 files)

## T08 — Adapter builder and conformance tests

**Description:** Ensure Windows/POSIX adapter tests include `cs-team-review`, its command, validator-adjacent source checks, all generated skill trees, and the no-`DESIGN.md`/no-`model:` invariants.

**Primary owner:** `arch`

**Acceptance criteria:**
- [ ] Both adapter tests copy/build/assert `cs-team-review` and `/cs-team-review`.
- [ ] Tests cover `skills`, `.agents/skills`, `.gemini/skills`, `.claude/skills`, and `plugins/claude/skills`, plus command adapters and absence of `DESIGN.md`/skill `model:`.
- [ ] Existing SysDocs and persona model assertions remain intact; builder source tree remains unchanged by isolated test execution.

**Verification:**
- [ ] `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test-adapters.ps1`.
- [ ] `sh scripts/test-adapters.sh` when a POSIX shell is available; otherwise record the environment limitation.

**Dependencies:** T01, T03, T04, T05, T06, T07

**Files likely touched:** `scripts/test-adapters.ps1`, `scripts/test-adapters.sh`

**Estimated scope:** Medium (2 files)

## T09 — End-to-end and failure fixtures

**Description:** Add reproducible inputs/expected artifacts for code, design, and mixed runs plus timeout/failure, REJECT+CONFIRM, conflict resume, unauthorized write, and manifest drift cases.

**Primary owner:** `backend`

**Acceptance criteria:**
- [ ] Each fixture declares input scope, expected phase artifacts, expected verdict/state, and failure reason.
- [ ] Mixed fixture preserves independent design/code findings when the proposal and implementation disagree; duplicate findings merge only with matching fingerprint.
- [ ] Resume fixtures prove drift starts a new run and incomplete required experts remain blocked.

**Verification:**
- [ ] Validator executes all fixtures and reports case IDs.
- [ ] Test engineer maps every fixture to at least one acceptance criterion in the final test report.

**Dependencies:** T01, T02

**Files likely touched:** `tests/fixtures/team-review/**`, `tests/test_validate_team_review.py`

**Estimated scope:** Medium (3-5 logical fixture/test files)

## T10 — Build and verification checkpoint

**Description:** Run validator, adapter builders/tests, static checks, and generated-tree consistency checks from a clean isolated test copy; record exact Windows/POSIX results in the run handoff.

**Primary owner:** `arch`

**Acceptance criteria:**
- [ ] Validator and focused fixture tests pass with expected negative cases.
- [ ] Windows adapter build/test passes; POSIX result is separately recorded, never conflated.
- [ ] Generated trees contain the new skill and command, and `git diff --check` is clean for implementation files.

**Verification:**
- [ ] Commands from design §7.1, with raw exit codes and counts recorded.
- [ ] `rg --files` confirms no `DESIGN.md` under the new skill directory.

**Dependencies:** T02, T08, T09

**Files likely touched:** `tasks/team-build/20260910-1015-team-review/test-report.md` (handoff only), generated adapter outputs as produced by builder

**Estimated scope:** Medium (verification artifacts only)

## T11 — Skill quality review and synthesis

**Description:** Run `cs-skill-review` against the canonical skill and validator-facing contracts, resolve Critical/Required findings, and write the final implementation report with residual risk and deferred items.

**Primary owner:** `arch`

**Acceptance criteria:**
- [ ] Six-axis skill review has no unresolved Critical/Required findings.
- [ ] Final report states tasks, rounds, commits, tests, deferred suggestions, and residual risks; it does not claim clean status when known failures remain.
- [ ] Any unresolved Important finding is explicitly escalated rather than silently accepted.

**Verification:**
- [ ] `cs-skill-review` output is persisted under this run's reviews directory.
- [ ] Final report references the independent test report and exact verification commands.

**Dependencies:** T01-T10

**Files likely touched:** `tasks/team-build/20260910-1015-team-review/reviews/**`, `tasks/team-build/20260910-1015-team-review/final-report.md`

**Estimated scope:** Medium (handoff artifacts)

## Execution order and checkpoints

1. Parallel contract setup: T01 and T02 (T02 may begin from the locked design schema; T01 remains the normative text owner).
2. Integration surfaces: T03, T04, T05, T06, T07 after T01.
3. Verification expansion: T08 after T03-T07; T09 after T01-T02.
4. Checkpoint: T10 after T02/T08/T09.
5. Final quality gate: T11 after all implementation and verification tasks.

Every task is reviewed in at most three rounds. A repeated P0 in round 2 triggers re-slicing; a third failed round escalates to the human. Suggestions alone do not consume another round.
