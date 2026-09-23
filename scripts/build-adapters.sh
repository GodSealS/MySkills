#!/bin/sh
set -eu

# macOS/POSIX adapter builder. .codebuddy is the source of truth.
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$ROOT/scripts/agent-resources.sh"
SRC_SKILLS="$ROOT/.codebuddy/skills"
SRC_AGENTS="$ROOT/.codebuddy/agents"
SRC_COMMANDS="$ROOT/.codebuddy/commands"
SRC_REFS="$ROOT/.codebuddy/references"
REF_SCRIPT="$ROOT/.build-adapter-refs.sed.$$"

die() { printf '%s\n' "build-adapters.sh: $*" >&2; exit 1; }
[ -d "$SRC_SKILLS" ] || die "missing $SRC_SKILLS"
[ -d "$SRC_AGENTS" ] || die "missing $SRC_AGENTS"

: > "$REF_SCRIPT"
for ref in "$SRC_REFS"/*.md; do
  [ -f "$ref" ] || continue
  name=$(basename "$ref")
  printf 's#[^][()<>[:space:]`]*references/%s#../../references/%s#g\n' "$name" "$name" >> "$REF_SCRIPT"
done
printf '%s\n' 's#\.codebuddy/skills/code-query/##g' >> "$REF_SCRIPT"
trap 'rm -f "$REF_SCRIPT"' EXIT HUP INT TERM

copy_tree() (
  source_path=$1
  destination_path=$2
  mkdir -p "$destination_path"
  cp -R "$source_path"/. "$destination_path"/
)

# Read a simple single-line frontmatter value. Source skills use both quoted
# and unquoted descriptions, so normalize either form before adapting it.
frontmatter_value() {
  key=$1
  file=$2
  value=$(sed -n "s/^${key}:[[:space:]]*//p" "$file" | head -n 1)
  case "$value" in
    \"*\") value=${value#\"}; value=${value%\"} ;;
  esac
  printf '%s' "$value"
}

# Skills never pin a model — the host runs them with its currently active
# model. Only the persona agents keep a per-role model, mapped per platform.
platform_model() {
  platform=$1
  model=$2
  case "$platform:$model" in
    claude:DeepSeek-V4-Pro) printf '%s\n' opus ;;
    claude:DeepSeek-V4-Flash) printf '%s\n' sonnet ;;
    codex:DeepSeek-V4-Pro) printf '%s\n' gpt-5.6-sol ;;
    codex:DeepSeek-V4-Flash) printf '%s\n' gpt-5.6-luna ;;
    gemini:DeepSeek-V4-Pro) printf '%s\n' gemini-2.5-pro ;;
    gemini:DeepSeek-V4-Flash) printf '%s\n' gemini-2.5-flash ;;
    *) die "unsupported model '$model' for platform '$platform'" ;;
  esac
}

replace_model() {
  file=$1
  model=$2
  tmp="$file.tmp.$$"
  awk -v model="$model" 'BEGIN { replaced = 0 } /^model:[[:space:]]/ && !replaced { print "model: " model; replaced = 1; next } { print }' "$file" > "$tmp"
  mv "$tmp" "$file"
}

strip_skill_frontmatter() {
  file=$1
  tmp="$file.tmp.$$"
  awk '
    /^---[[:space:]]*$/ { in_fm = !in_fm; print; next }
    in_fm && $0 ~ /^(argument-hint|user-invocable|allowed-tools|agent|model):[[:space:]]/ { next }
    { print }
  ' "$file" > "$tmp"
  mv "$tmp" "$file"
}

strip_claude_agent_frontmatter() {
  file=$1
  tmp="$file.tmp.$$"
  awk '
    /^---[[:space:]]*$/ { in_fm = !in_fm; print; next }
    in_fm && $0 ~ /^(thinkingLevel|agentMode|subagent|enabled|enabledAutoRun):[[:space:]]/ { next }
    in_fm && $0 ~ /^tools:[[:space:]]/ { sub(/(,[[:space:]]*)?Task(,[[:space:]]*)?/, ""); sub(/,[[:space:]]*$/, ""); print; next }
    { print }
  ' "$file" > "$tmp"
  mv "$tmp" "$file"
}

fix_refs() (
  target_file=$1
  # Resolve all shared reference paths in one sed pass. This keeps the POSIX
  # builder fast enough for the full adapter tree while retaining the same
  # path contract as the PowerShell builder.
  tmp="$target_file.tmp.$$"
  sed -f "$REF_SCRIPT" "$target_file" > "$tmp"
  mv "$tmp" "$target_file"
)

build_skills() (
  dst=$1
  mkdir -p "$dst"
  for src in "$SRC_SKILLS"/*; do
    [ -d "$src" ] || continue
    name=$(basename "$src")
    target="$dst/$name"
    copy_tree "$src" "$target"
    definition="$target/SKILL.md"
    strip_skill_frontmatter "$definition"
    find "$target" -type f -name '*.md' | while IFS= read -r file; do
      fix_refs "$file"
    done
  done
)

codex_skill_metadata() (
  skill_dir=$1
  definition="$skill_dir/SKILL.md"
  [ -f "$definition" ] || return 0
  skill_name=$(frontmatter_value name "$definition")
  [ -n "$skill_name" ] || skill_name=$(basename "$skill_dir")
  display_source=${skill_name#cs-}
  display_name=$(printf '%s\n' "$display_source" | awk -F- '
    {
      result=""
      for (i = 1; i <= NF; i++) {
        word=$i
        if (word == "api" || word == "ci" || word == "cd" || word == "ui" || word == "tdd" || word == "adr" || word == "mcp" || word == "dom") {
          word=toupper(word)
        } else {
          word=toupper(substr(word, 1, 1)) substr(word, 2)
        }
        result=result (i == 1 ? "" : " ") word
      }
      print result
    }')
  display_name="CS $display_name"
  short_description=$(frontmatter_value description "$definition")
  case "$short_description" in
    *" / "*) short_description=${short_description%% / *} ;;
  esac
  short_description=$(printf '%s' "$short_description" | sed 's/[.!?].*//')
  [ -n "$short_description" ] || short_description="$display_name"
  display_name=$(printf '%s' "$display_name" | sed 's/\\/\\\\/g; s/"/\\"/g')
  short_description=$(printf '%s' "$short_description" | sed 's/\\/\\\\/g; s/"/\\"/g')
  metadata_dir="$skill_dir/agents"
  mkdir -p "$metadata_dir"
  {
    printf 'interface:\n'
    printf '  display_name: "%s"\n' "$display_name"
    printf '  short_description: "%s"\n' "$short_description"
    if grep -Eq '^disable-model-invocation:[[:space:]]*true[[:space:]]*$' "$definition"; then
      printf 'policy:\n  allow_implicit_invocation: false\n'
    fi
  } > "$metadata_dir/openai.yaml"
)

build_agents() (
  platform=$1
  dst=$2
  mkdir -p "$dst"
  for src in "$SRC_AGENTS"/*.md; do
    [ -f "$src" ] || continue
    name=$(basename "$src")
    target="$dst/$name"
    cp "$src" "$target"
    if [ "$platform" = claude ]; then strip_claude_agent_frontmatter "$target"; fi
    if [ "$platform" != neutral ]; then
      case "$name" in
        cs-architect.md|cs-backend-lead.md|cs-frontend-lead.md|cs-code-reviewer.md|cs-security-auditor.md|cs-review-advisor.md) tier=DeepSeek-V4-Pro ;;
        cs-test-engineer.md|cs-web-perf-auditor.md|cs-knowledge-base-admin.md) tier=DeepSeek-V4-Flash ;;
        *) die "unsupported persona $name" ;;
      esac
      replace_model "$target" "$(platform_model "$platform" "$tier")"
    fi
  done
  sync_agent_resources "$SRC_AGENTS" "$dst"
)

clear_generated_dir() {
  target=$1
  case "$target" in
    "$ROOT"/*) ;;
    *) die "refusing to clear path outside repository: $target" ;;
  esac
  if [ -L "$target" ]; then
    die "refusing to clear linked adapter path: $target"
  fi
  rm -rf "$target"
  mkdir -p "$target"
}

strip_claude_command_frontmatter() {
  file=$1
  tmp="$file.tmp.$$"
  awk '
    /^---[[:space:]]*$/ { in_fm = !in_fm; print; next }
    in_fm && $0 ~ /^(user-invocable|allowed-tools|agent|when_to_use|disable-model-invocation):[[:space:]]/ { next }
    { print }
  ' "$file" > "$tmp"
  mv "$tmp" "$file"
}

build_refs() (
  dst=$1
  mkdir -p "$dst"
  for src in "$SRC_REFS"/*.md; do [ -f "$src" ] && cp "$src" "$dst/"; done
)

clear_generated_dir "$ROOT/skills"
clear_generated_dir "$ROOT/.gemini/skills"
clear_generated_dir "$ROOT/.agents/skills"
clear_generated_dir "$ROOT/.claude/skills"
build_skills "$ROOT/skills"
build_skills "$ROOT/.gemini/skills"
build_skills "$ROOT/.agents/skills"
build_skills "$ROOT/.claude/skills"
for skill_dir in "$ROOT/.agents/skills"/*; do
  [ -d "$skill_dir" ] || continue
  codex_skill_metadata "$skill_dir"
done

mkdir -p "$ROOT/agents" "$ROOT/.gemini/agents" "$ROOT/.codex/agents" "$ROOT/.claude/agents"
build_agents neutral "$ROOT/agents"
build_agents gemini "$ROOT/.gemini/agents"
build_agents codex "$ROOT/.codex/agents"
build_agents claude "$ROOT/.claude/agents"

clear_generated_dir "$ROOT/references"
clear_generated_dir "$ROOT/.gemini/references"
clear_generated_dir "$ROOT/.agents/references"
clear_generated_dir "$ROOT/.claude/references"
build_refs "$ROOT/references"
build_refs "$ROOT/.gemini/references"
build_refs "$ROOT/.agents/references"
build_refs "$ROOT/.claude/references"

# Refresh command adapters from the canonical CodeBuddy commands.
clear_generated_dir "$ROOT/commands"
clear_generated_dir "$ROOT/.claude/commands"
clear_generated_dir "$ROOT/.gemini/commands"
clear_generated_dir "$ROOT/.codex/prompts"
for src in "$SRC_COMMANDS"/*.md; do
  [ -f "$src" ] || continue
  name=$(basename "$src")
  cp "$src" "$ROOT/commands/$name"
  cp "$src" "$ROOT/.claude/commands/$name"
  strip_claude_command_frontmatter "$ROOT/.claude/commands/$name"

  description=$(frontmatter_value description "$src")
  [ -n "$description" ] || description=${name%.md}
  body=$(awk 'BEGIN { delimiters = 0 } /^---[[:space:]]*$/ { delimiters++; next } delimiters >= 2 { print }' "$src")
  escaped_description=$(printf '%s' "$description" | sed 's/\\/\\\\/g; s/"/\\"/g')
  case "$body" in
    *"'''"*)
      escaped_body=$(printf '%s' "$body" | sed 's/\\/\\\\/g; s/"/\\"/g')
      prompt="\"\"\"$escaped_body\"\"\""
      ;;
    *) prompt="'''$body'''" ;;
  esac
  printf 'description = "%s"\n\nprompt = %s\n' "$escaped_description" "$prompt" > "$ROOT/.gemini/commands/${name%.md}.toml"
done

# Some canonical commands refer to a skill directly (for example
# /cs-grill-me) without having a dedicated CodeBuddy command file. Claude Code
# still needs a concrete slash-command target, so create a thin wrapper for
# each referenced skill. Use awk instead of a grep pattern beginning with `/`;
# Git Bash can reinterpret such arguments as Windows paths.
for src in "$SRC_COMMANDS"/*.md; do
  [ -f "$src" ] || continue
  refs=$(awk '{
    line = $0
    while (match(line, /\/cs-[A-Za-z0-9-]+/)) {
      print substr(line, RSTART + 1, RLENGTH - 1)
      line = substr(line, RSTART + RLENGTH)
    }
  }' "$src" || true)
  for skill_name in $refs; do
    target="$ROOT/.claude/commands/$skill_name.md"
    [ -f "$target" ] && continue
    skill_definition="$SRC_SKILLS/$skill_name/SKILL.md"
    [ -f "$skill_definition" ] || continue
    description=$(frontmatter_value description "$skill_definition")
    [ -n "$description" ] || description="$skill_name"
    {
      printf '%s\n' '---'
      printf 'description: "%s"\n' "$(printf '%s' "$description" | sed 's/\\/\\\\/g; s/"/\\"/g')"
      printf '%s\n\n' '---'
      printf 'Invoke the `%s` skill and follow its workflow.\n' "$skill_name"
    } > "$target"
  done
done

clear_generated_dir "$ROOT/.claude/rules"
cat > "$ROOT/.claude/rules/skills-contributing.md" <<'EOF'
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
- Follow the frontmatter / body anatomy used by the other skills (name + description in frontmatter; Overview / When to Use / Process / Verification in body).
- Prefer extending an existing skill over adding a near-duplicate.

`CLAUDE.md` (Claude Code), `AGENTS.md` (Codex / CodeBuddy router) and `GEMINI.md` (Gemini CLI router) are the single source of truth for the skill catalog — do not duplicate their content here, link to them.
EOF

# Codex prompts are a thin launch surface for every auto-discovered skill.
for src in "$SRC_SKILLS"/*/SKILL.md; do
  [ -f "$src" ] || continue
  skill_name=$(sed -n 's/^name:[[:space:]]*\([^[:space:]]*\)[[:space:]]*$/\1/p' "$src" | head -n 1)
  [ -n "$skill_name" ] || skill_name=$(basename "$(dirname "$src")")
  skill_description=$(frontmatter_value description "$src")
  escaped_description=$(printf '%s' "$skill_description" | sed 's/\\/\\\\/g; s/"/\\"/g')
  printf '%s\n' '---' "description: \"$escaped_description\"" 'argument-hint: "[args]"' '---' '' "Invoke the $skill_name skill and follow its workflow for: \$ARGUMENTS" > "$ROOT/.codex/prompts/$skill_name.md"
done

# Claude plugins must contain Claude-native skills and agents at plugin root.
PLUGIN="$ROOT/plugins/claude"
mkdir -p "$PLUGIN"
for child in skills references commands rules .claude-plugin; do
  clear_generated_dir "$PLUGIN/$child"
done
copy_tree "$ROOT/.claude/skills" "$PLUGIN/skills"
mkdir -p "$PLUGIN/agents"
cp "$ROOT/.claude/agents/"*.md "$PLUGIN/agents/"
sync_agent_resources "$SRC_AGENTS" "$PLUGIN/agents"
copy_tree "$ROOT/.claude/references" "$PLUGIN/references"
copy_tree "$ROOT/.claude/commands" "$PLUGIN/commands"
copy_tree "$ROOT/.claude/rules" "$PLUGIN/rules"
mkdir -p "$PLUGIN/.claude-plugin" "$ROOT/.claude-plugin"
cat > "$PLUGIN/.claude-plugin/plugin.json" <<'JSON'
{
  "name": "agent-skills-cs",
  "version": "1.0.0",
  "description": "Production-grade engineering workflow skills (cs-*) for Claude Code, sourced from .codebuddy/.",
  "author": { "name": "agent-skills" }
}
JSON
rm -f "$ROOT/.claude-plugin/plugin.json"
cat > "$ROOT/.claude-plugin/marketplace.json" <<'JSON'
{
  "name": "agent-skills-cs",
  "owner": { "name": "agent-skills" },
  "plugins": [
    { "source": "./plugins/claude" }
  ]
}
JSON

if [ ! -f "$ROOT/CLAUDE.md" ]; then
  cat > "$ROOT/CLAUDE.md" <<'EOF'
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
EOF
fi

printf 'Built adapters: skills=%s agents=%s\n' \
  "$(find "$SRC_SKILLS" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')" \
  "$(find "$SRC_AGENTS" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')"
