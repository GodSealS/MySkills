---
description: "Run a resumable multi-agent review of a code, design, or mixed target and synthesize a deterministic verdict / 对代码、设计或混合目标执行可恢复多 Agent 审查并生成确定性结论"
---

Invoke the `cs-team-review` skill with `$ARGUMENTS` as a local path, local git ref/diff, or existing run-id.

The skill is the orchestrator. It writes all handoffs under a unique `tasks/team-review/<run-id>/` directory, validates schema v1 JSON artifacts, and never modifies the reviewed code or design. Use `cs-code-review` for a single-agent review and `cs-shipping` for a release gate.
