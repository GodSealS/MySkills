---
description: "Start spec-driven development — write a structured specification before writing code / 启动规范驱动开发——在编码前编写结构化技术规范"
---

Invoke the `cs-spec-driven` skill.

Begin by understanding what the user wants to build. Ask clarifying questions about:
1. The objective and target users
2. Core features and acceptance criteria
3. Tech stack preferences and constraints
4. Known boundaries (what to always do, ask first about, and never do)

Then generate a structured spec covering all six core areas: objective, commands, project structure, code style, testing strategy, and boundaries.

Save the spec at its existing authoritative location or, for a new project, `SysDocs/specs/<topic>.md`. New SysDocs specs/ADRs follow schema 2 metadata and applicable summaries; this alone does not initialize a full documentation library. After objective approval, FAN-OUT to `cs-architect` for architecture and ADRs via `cs-docs-adrs`: preserve an existing ADR location, otherwise use `SysDocs/decisions/`. Run `/cs-grill-me <actual-spec-path>` before planning, or record an explicit skip and accepted risks in `## Grill Review`. Confirm the recorded decision with the user before proceeding.
