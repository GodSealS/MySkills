---
description: "Implement the next task; auto or all executes the authorized plan / 实现下一任务；auto 或 all 连续执行已授权计划"
---

Invoke `cs-incremental`; apply `cs-tdd` to executable logic and behavior changes.
For documentation follow `../references/sysdocs-design-context.md`, synchronize affected
content before review/delivery, and reuse valid evidence. Missing SysDocs does not require
initialization; knowledge-graph refresh does not prove documentation correctness.

## Modes

- `/cs-build`: complete the next pending task, then stop.
- `/cs-build auto` or `/cs-build all`: execute all authorized tasks in dependency order.

## Process

1. Read selected requirements and the authoritative plan. If decomposition is needed,
   invoke `cs-planning` once. Clear requirements suffice; a formal spec and Grill Review
   section are optional. Reuse approval for unchanged scope; resolve material missing
   decisions before dependent implementation.
2. Inspect the worktree. Preserve unrelated user changes and stage only this task's files.
   Ask only when changes conflict or their ownership cannot be safely separated.
3. Execute tasks through `cs-incremental`. The host handles ordinary slices; delegation
   requires a concrete independent task or explicit team workflow, not an owner tag.
   Pass focused context when delegating.
4. Run affected tests/checks after each slice. Run project-required full regression,
   build, lint and type checks at integration/final delivery, or earlier when shared
   infrastructure or uncertain impact warrants them. Reuse passing evidence for unchanged
   inputs. Documentation-only changes use content, link and format checks.
5. Record status and evidence in the authoritative plan. Commit coherent validated
   increments when requested or established by project workflow; workspace delivery is
   valid otherwise. Follow `cs-debugging` for failures without stopping for routine fixes.
6. At the end of the entire plan, the host checks whether `.codegraph/`,
   `.understand-anything/`, or `graphify-out/` exists and indexed source changed.
   If both apply, FAN-OUT once to `cs-knowledge-base-admin` as the final execution step,
   passing project root and changed scope. Otherwise skip without spawning. Single-task
   invocations defer refresh while tasks remain pending; an explicit refresh request may
   override deferral. Under Team Build, its final refresh owns this step.
7. Summarize completed tasks, verification, remaining work and any refresh result briefly.

Unresolved high-risk decisions use `cs-doubt-driven`. Ask for authorization only when the
next action is outside existing authorization or is materially irreversible.
