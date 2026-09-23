# Authoring Agent Skills

Source: `.codebuddy/skills`, `agents`, `commands`, `references` and `hooks`.
Build other platforms with `scripts/build-adapters.ps1` or `scripts/build-adapters.sh`.
The pack is adapted from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT).

- Skills use `cs-` names, concise trigger descriptions, actionable steps and verification.
- Keep only guidance that changes behavior. Examples, rationalizations and red flags are
  optional; include them only for demonstrated failure modes.
- Keep each rule in one authoritative place; commands delegate to skills instead of
  restating their workflow. Load branch-specific references only when that branch applies.
- Skill-local resources may live beside the skill; shared protocols belong in `references/`.
- Ordinary tasks reuse decisions and evidence. Team workflows remain explicit and retain
  their review boundaries; read `references/cs-orchestration-patterns.md` for actual handoffs.
- SysDocs work uses `cs-sysdocs-init`, `cs-sysdocs-update` or explicit `cs-vibe-coding`.
  Ordinary changes synchronize affected documentation without forcing full initialization.

Verify changed skills, references and generated adapters. Keep installation paths and
platform metadata working; preserve user-owned files during installation.
