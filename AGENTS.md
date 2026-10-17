# Agent-Skills Router

Select skills from the available descriptions; load `cs-using` only when routing is unclear.
Use one primary workflow and add supporting skills only when the task needs them.
Clear local edits do not require a formal spec, Grill Review, or a separate planning round.
Reuse existing authorization, accepted decisions and valid evidence for unchanged scope.

`cs-team-build`, `cs-team-review`, and `cs-team-refactor` are manual-only: invoke them only
when named explicitly or through `/cs-team-coding`, `/cs-team-review`, `/cs-team-refactor`.
Persona dispatch is limited to `cs-frontend-lead` assigning Cocos client work to
`cs-cocos-specialist`, and `cs-backend-lead` assigning Cocos server work to
`cs-network-programmer`. Both workers only execute; their assigning lead decides design changes.
Other persona orchestration stays with the host. Follow the selected skill's verification and boundaries.

When editing this skill pack, `.codebuddy/` is authoritative. Regenerate adapters with
`scripts/build-adapters.ps1` or `scripts/build-adapters.sh`; see `README.md` for installation
and `cs-skill-review` for skill quality checks.
