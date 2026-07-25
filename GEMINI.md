# Agent-Skills for Gemini CLI

This project is a prompt pack of engineering workflow skills. Skills are auto-discovered from
`.gemini/skills/<name>/SKILL.md`; slash commands from `.gemini/commands/<name>.toml`.

## Always-on skills

Load these proactively as standing context:
- `cs-using` — discover and invoke the right skill (meta-skill)
- `cs-spec-driven` — write a spec before coding
- `cs-planning` — break work into tasks
- `cs-incremental` — deliver in small working slices
- `cs-tdd` — test-driven development
- `cs-code-review` — five-axis review
- `cs-simplify` — simplify for clarity
- `cs-debugging` — root-cause debugging
- `cs-security` — harden against vulnerabilities
- `cs-git-workflow` — git workflow and versioning
- `cs-shipping` — prepare production launches

## Slash commands

- `/spec` — start spec-driven development
- `/plan` — plan and break down tasks
- `/build` — incremental delivery
- `/test` — test-driven development
- `/review` — five-axis code review
- `/webperf` — web performance audit
- `/code-simplify` — simplify code
- `/ship` — shipping and launch checklist

## Conventions

- Every skill is a process with steps, checkpoints, and exit criteria.
- Verification is non-negotiable — require evidence, not "seems right".
- Reference existing skills instead of duplicating content.
