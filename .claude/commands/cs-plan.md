---
description: "Break work into small verifiable tasks with acceptance criteria and dependency ordering / 将工作拆分为小粒度的可验证任务，含验收标准和依赖排序"
---

Invoke the `cs-planning` skill.

Read the existing spec (`SPEC.md` or equivalent) and the relevant codebase sections.

Before planning, require a `## Grill Review` section in the spec. It must either summarize the completed `/cs-grill-me` findings and decision, or explicitly state that the review was skipped and the risks were accepted. If it is absent, stop and direct the user to run `/cs-grill-me <spec-path>` or record an explicit skip decision.

Then:

1. Enter plan mode — read only, no code changes
2. Identify the dependency graph between components — FAN-OUT to `cs-architect` to validate module boundaries and dependency direction
3. Slice work vertically (one complete path per task, not horizontal layers)
4. Write tasks with acceptance criteria, verification steps, a **primary owner** tag (`arch` / `frontend` / `backend`), and optional collaborators; keep cross-domain work as an end-to-end slice unless its contract must be independently delivered first.
5. Add checkpoints between phases
6. Present the plan for human review

Save the plan to tasks/plan.md and task list to tasks/todo.md.
