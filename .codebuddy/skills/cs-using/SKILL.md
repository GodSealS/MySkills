---
name: cs-using
description: "Select a workflow when skill routing is unclear. / 在技能选择不明确时选择合适工作流。"
---

# Skill Routing

Use the host's available skill descriptions first. Read this router only when selection
is unclear; load the chosen skill, not every related skill or reference.

## Intent Mapping

| Task | Skill |
|---|---|
| Extract intent / refine an idea / stress-test a design | `cs-interview-me` / `cs-idea-refine` / `cs-grill-me` |
| Missing requirements for a significant change | `cs-spec-driven` |
| Clear requirements need dependency ordering and tasks | `cs-planning` |
| Implement several verifiable outcomes | `cs-incremental` |
| Choose the smallest implementation / simplify existing code | `cs-minimal` / `cs-simplify` |
| UI / public interfaces / executable behavior tests | `cs-frontend-ui` / `cs-api-design` / `cs-tdd` |
| Browser verification / failures | `cs-browser-test` / `cs-debugging` |
| Code review / concrete security or performance concerns | `cs-code-review` / `cs-security` / `cs-perf-opt` |
| High-risk, unproven assumptions / framework fact verification | `cs-doubt-driven` / `cs-source-driven` |
| Git / pipelines / migration | `cs-git-workflow` / `cs-cicd` / `cs-deprecation` |
| Decisions and docs / instrumentation / production launch | `cs-docs-adrs` / `cs-observability` / `cs-shipping` |
| Context setup / code questions | `cs-context-eng` / `cs-code-query` |
| Review a task brief / skill | `cs-agent-brief-review` / `cs-skill-review` |
| Explicit full documentation / existing documentation maintenance | `cs-sysdocs-init` / `cs-sysdocs-update` |
| Explicit fragmentary pre-design | `cs-vibe-coding` |

`cs-team-build`, `cs-team-review` and `cs-team-refactor` start only after explicit invocation
of that skill or `/cs-team-coding`, `/cs-team-review`, `/cs-team-refactor`, respectively.
An ordinary implementation request does not select a team workflow.

## Composition

- Pick one primary workflow. Add supporting skills only for an actual unresolved need.
  Cross-references identify options, not a checklist of skills to load.
- Clear local work needs no formal spec, duplicate task list, Grill Review or extra approval.
  Reuse accepted decisions and valid verification evidence for unchanged inputs.
- Ordinary implementation stays with the host. Delegate a bounded independent task only
  when useful and authorized, or when the explicitly selected workflow requires it.
  Personas never invoke other personas; their optional rosters are allowlists, not quotas.
- Team-role handoffs follow [orchestration patterns](../../references/cs-orchestration-patterns.md)
  only when a team or specialist handoff is active. Load private advisor protocols solely
  for that role's assigned review.
- Verify the selected workflow's actual outcome with relevant evidence. Use
  [Definition of Done](../../references/cs-definition-of-done.md) for delivery checks.

## Verification

- [ ] The selected workflow matches the requested deliverable and scope.
- [ ] Conditional reviews, references and delegation have concrete triggers.
- [ ] Existing authorization, decisions and unchanged evidence were reused.
