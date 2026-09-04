# Agent-Skills for Claude Code

This is the **agent-skills** pack — production-grade engineering workflow skills for Claude Code, ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT).

## Skills

Skills are discovered from `.claude/skills/<name>/SKILL.md` (project) and `~/.claude/skills/<name>/SKILL.md` (personal), all `cs-` prefixed. Claude auto-invokes a skill when its `description` matches the task; you can also type the skill name directly to call it. The slash command shortcuts in `.claude/commands/` cover the main workflows.

## Router

`AGENTS.md` at the repo root is the universal router (also used by Codex / CodeBuddy / Gemini CLI). Read it to map an inbound task to the right skill.

## Conventions

- One `cs-<name>` per lifecycle phase; do not duplicate phases across skills.
- Every skill follows the same anatomy — frontmatter (`name`, `description`) + body (`Overview`, `When to Use`, `Process`, `Common Rationalizations`, `Red Flags`, `Verification`).
- Cross-reference other skills instead of paraphrasing their content.