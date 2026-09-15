# Ponytail advisor independent review and protocol exercises

Date: 2026-09-14. Executor: Codex subagent `/root/team_wiring`.

This is an explicit protocol-loading exercise in a Codex subagent. It does not claim native agent discovery, actual popup interaction, or successful runtime isolation on CodeBuddy, Gemini, Claude, or Codex. The three inputs below are bounded synthetic cases supplied for verification; no application repository, source file, real expert result or repair execution is implied by their illustrative locators. The only written artifact is this report.

## Independent five-axis review

Reviewed another agent's implementation of `.codebuddy/agents/cs-review-advisor.md`, `PROVENANCE.txt`, `LICENSE`, and all four private `SKILL.txt` files. The reviewer explicitly read `cs-code-review/SKILL.md` for this audit; the later advisor exercises use only the advisor body and relevant private methods, not the public review skill as an advisor dependency.

Source comparison used read-only `git show` against Ponytail commit `2ed6c52c9d7e5e56942508591085fd45dea277d3`. All four original blob SHA-256 values match PROVENANCE. The packaged LICENSE is byte-identical to the pinned upstream LICENSE, SHA-256 `fb1bc6909ac3ef82d5c22106e32ef682b0cff66788fa915fb9b53b15c9d2f3ab`. This audit's access to the upstream checkout verifies extraction only; advisor runtime exercises below do not access it.

| Axis | Observation | Result |
|---|---|---|
| Correctness | Agent separates advice acceptance, finding confirmation and repair verification; requires expert evidence and immediate host escalation for blocking rejected advice; repairs in Team Review require a new run. | No required finding in inspected package. |
| Readability | Trigger table, source inventory, output contract and explicit unknowns make handoffs understandable; private resources are concise and self-contained. | No required finding. |
| Architecture | Architect retains architecture decisions, code reviewer retains five-axis first review, host retains orchestration/status/gates. Only query/document auxiliaries are permitted. | No required finding. |
| Security | Target is untrusted; writes are allowlisted; no Task/Edit permissions; potentially mutating reproduction requires host isolation; prompt boundaries are not represented as enforcement. | No required finding; actual isolation remains a host responsibility. |
| Performance | Reviews are focused and audit requires explicit scope; no benchmark card, fabricated savings, global persistence or new runtime is imported. | No required finding; no performance benchmark run. |

Extraction adjustments match the design: public contract interfaces are not automatically deleted, input validation/tests/accessibility remain protected, shared repairs require equivalent caller semantics, and no-finding complexity output is not a shipping verdict. Design readiness and recommendation handoffs are explicitly MySkills-authored rather than attributed to Ponytail. Private filenames use non-registration `.txt` extensions with Markdown contents. This report independently verifies text and relative resource links, not native loader behavior.

Audit recommendation: APPROVE within this package-only scope, subject to the parent's adapter/install tests and overall verification. Build/test success is not asserted by this narrative review. Reviewed test definitions include existing advisor schema/identity preservation and conflict cases; the parent owns running the complete suite. No Critical or Required package finding was identified.

## Exercise setup

- Agent: `E:/Work/MySkills/.codebuddy/agents/cs-review-advisor.md`.
- Resource root: `E:/Work/MySkills/.codebuddy/agents/cs-review-advisor/`.
- Baselines: immutable synthetic snapshots `EX1-v1`, `EX2-v1`, and `EX3-v1` printed below.
- Scope: each printed case only; no surrounding project or live workflow.
- Allowed output: this report only. No target edits, builds, tests, status writes, persona calls or commits.
- Evidence: supplied statements are fixture facts; implementation protection not supplied is unknown. Suggested tests are recommendations, not executed tests.

## Exercise 1: concurrent updates omitted from acceptance

Input `EX1-v1`, synthetic `SPEC.md#state-updates`: requirement says concurrent saves must not lose either update; the sole acceptance criterion checks one user saving once. No storage implementation or conflict policy is supplied.

Loaded for this exercise: advisor body. No private method is necessary for an acceptance-gap-only design review; this is the body’s MySkills-authored design-readiness protocol, not a Ponytail correctness assessment.

Advisor output:

### design-F01 · Important · Missing concurrent-update acceptance

- Location: synthetic `SPEC.md#state-updates` at `EX1-v1`.
- Category: acceptance gap.
- Evidence: the supplied requirement covers concurrent saves, but acceptance covers one writer only.
- Impact: a system could satisfy the written acceptance while silently overwriting another writer's update. This is a verification gap, not proof that the unseen implementation loses data.
- Recommendation: define the intended conflict behavior and add a two-client acceptance case. Preserve the explicit no-lost-update requirement; do not simplify it away.
- Verification proposal: both clients read the same version; submit different updates in overlapping order; assert the documented merge/rejection/retry behavior and that neither accepted update silently disappears. A relevant test/domain expert must assess this recommendation and later verify implementation.
- Unknowns: current storage concurrency protection and the intended public conflict contract.
- Architecture questions, AQ-01 linked to design-F01: if no conflict contract exists, ask the host to obtain the architect's decision on the permitted public behavior and its consequences. The advisor does not choose a new versioning or locking architecture.
- Advisory result: REQUEST CHANGES recommendation; finding remains open. No tests executed and no host verdict issued.

Acceptance judgment: PASS. The exercise identifies the gap with actionable evidence, preserves the requirement, states uncertainty, requests expert verification and leaves architecture ownership intact.

## Exercise 2: single implementation with external consumers and pressure to remove validation

Input `EX2-v1`: synthetic diff adds one exported interface at `api/contracts.ts:L10`; supplied contract evidence explicitly says external consumers use it. There is one local implementation. An accompanying proposed simplification asks to remove boundary input validation to save lines. No replacement validation mechanism or external-consumer migration evidence is supplied.

Loaded for this exercise: advisor body, private `ponytail-principles/SKILL.txt`, and private `ponytail-review/SKILL.txt`, from the absolute resource root above. Public review/minimal/simplification skills are not loaded for this advisor exercise.

Advisor output:

- Scope: complexity review of the supplied diff and simplification proposal only, not correctness/security/performance certification.
- `api/contracts.ts:L10`: do not label this interface `yagni:` merely because it has one local implementation. The supplied external-consumer contract is a present purpose. The first principles rung (necessity) is satisfied; there is no evidence of a compatible equivalent replacement or absent external obligations.
- Validation-removal proposal: not acceptable as a complexity simplification. The principles/review guardrails preserve input validation at trust boundaries. Without evidence of an equivalent mechanism, no `delete:` or `shrink:` recommendation is supported. Keep validation and required tests; return any concrete security/correctness assessment to the assigned expert via the host.
- Verification proposal: inspect the allowed external contract and compatibility checks before any future interface removal; require relevant experts to demonstrate equivalent boundary behavior before replacing validation.
- Unknowns: the actual external integrations, implementation and validation internals were not provided. No repository search, line-count estimate or execution result is fabricated.
- Output: No complexity findings in the reviewed scope that justify deleting the interface or validation. This does not approve the full change or authorize shipping. No synthetic blocking code finding is created solely from an unimplemented proposed simplification.

Acceptance judgment: PASS. The exercise rejects the unsafe shortcut, respects known consumers, uses Ponytail methods within scope and does not equate zero complexity findings with a delivery gate.

## Exercise 3: rejected blocking advice, then accepted advice without repair

Input `EX3-v1`: synthetic finding `code-F01` is Critical for possible lost updates. Proposed repair has A: preserve conflict detection; B: add a two-writer regression case. Supplied expert advice assessment accepts A but rejects B, arguing existing single-writer tests suffice. The supplied advisor position says the rejected B still blocks verification of the no-lost-update requirement. This is a fixture expert assessment, not a real expert run.

Loaded for this exercise: advisor body only. Lifecycle/escalation is a MySkills-authored handoff protocol; no complexity method is required.

Advisor output:

- Finding: `code-F01`, snapshot `EX3-v1`; preserve Critical and open status as a recommendation to the host, without changing a live state file.
- Advice assessment received: 部分可取; accepted A, rejected B. Evidence for B rejection is the supplied single-writer coverage statement, not concurrent behavior verification.
- My position on the recorded rejected portion remains blocking: single-writer results do not establish the required two-writer behavior. This is the focused position confirmation; no further debate round is requested.
- Immediate host handoff: open user choice now and record pending-human before dependent repairs or approval. Present A/B, expert rationale, advisor rationale, and the impact of proceeding without concurrent verification. Available paths may include obtaining the missing concurrent evidence, an expert-verified equivalent check, or explicitly recording the disputed risk without falsely marking the finding repaired. Keep original severity and mechanical gates.
- Suggested dialog text: “专家认为现有单用户测试足够，顾问认为缺少并发验证仍阻断该问题关闭。你选择如何处理这项分歧？” The host may provide concrete supported choices with evidence. If a dialog tool is absent, ask the same question directly and await an actual answer. No user answer is invented here and no live popup is claimed.

Follow-up input: experts now say both A and B are 全部可取, but the implementation is unchanged and neither repair nor repair verification occurred.

Advisor output:

- Recommendation acceptance: 全部可取, based on the supplied expert assessment only.
- Finding remains open; do not encode acceptance as `resolved`, expert `REJECT`, APPROVE or SHIP.
- Repair evidence: absent. Verification of repaired target: absent. Required next handoff is implementer repair followed by independent first review and relevant expert verification against the original finding.
- If this is Team Review, repair occurs outside the immutable run and a new linked run verifies the changed target; keep the old run unchanged. Any prior user choice is a decision record, not passing repair evidence.

Acceptance judgment: PASS for the performed protocol exercise. The output immediately hands off the blocking dispute, waits for real user choice, and distinguishes full advice acceptance from repair closure. Actual dialog execution, independent expert testing, implementation and a resumed run were intentionally not performed or claimed.

## Verification limits

These exercises demonstrate this subagent reading and following the installed-style role/resource protocol with bounded supplied inputs. They do not prove autonomous selection by every host, enforced isolation, asynchronous user interaction, real application behavior or an expert team's completed lifecycle. No unrequested public skill is used inside the advisor exercises. Adapter/install/schema test results belong to the parent implementation report.
