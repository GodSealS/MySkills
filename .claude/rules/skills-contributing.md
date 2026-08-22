---
description: Anti-duplication guardrail for adding or changing skills
paths:
  - "skills/**"
  - ".codebuddy/skills/**"
---

# Adding or changing a skill

This pack already covers most of the development lifecycle, so most new-skill ideas overlap an existing skill or an open skill catalog. Before creating a new `skills/<name>/` (or `.codebuddy/skills/<name>/`) directory or significantly reworking an existing one:

- Search the existing catalog under `.codebuddy/skills/` and `skills/` for an overlap.
- Justify the gap in one line (what lifecycle phase is missing, and which skill is the closest neighbor).
- Follow the frontmatter / body anatomy used by the other skills (name + description in frontmatter; Overview / When to Use / Process / Red Flags / Verification in body).
- Prefer extending an existing skill over adding a near-duplicate.

`CLAUDE.md` (Claude Code), `AGENTS.md` (Codex / CodeBuddy router) and `GEMINI.md` (Gemini CLI router) are the single source of truth for the skill catalog — do not duplicate their content here, link to them.