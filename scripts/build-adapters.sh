#!/bin/sh
set -eu

# macOS/POSIX adapter builder. .codebuddy is the source of truth.
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$ROOT/scripts/agent-resources.sh"
SRC_SKILLS="$ROOT/.codebuddy/skills"
SRC_AGENTS="$ROOT/.codebuddy/agents"
SRC_REFS="$ROOT/.codebuddy/references"

die() { printf '%s\n' "build-adapters.sh: $*" >&2; exit 1; }
[ -d "$SRC_SKILLS" ] || die "missing $SRC_SKILLS"
[ -d "$SRC_AGENTS" ] || die "missing $SRC_AGENTS"

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
  # Resolve shared reference paths for generated adapter trees.
  # The leading character class excludes backticks so a markdown-inline
  # `references/<file>` keeps its opening backtick after rewriting.
  bt='`'
  for ref in "$SRC_REFS"/*.md; do
    [ -f "$ref" ] || continue
    name=$(basename "$ref")
    tmp="$target_file.tmp.$$"
    sed "s#[^[:space:]$bt]*references/$name#../../references/$name#g; s#\.codebuddy/skills/code-query/##g" "$target_file" > "$tmp"
    mv "$tmp" "$target_file"
  done
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
    fix_refs "$definition"
  done
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

build_refs() (
  dst=$1
  mkdir -p "$dst"
  for src in "$SRC_REFS"/*.md; do [ -f "$src" ] && cp "$src" "$dst/"; done
)

build_skills "$ROOT/skills"
build_skills "$ROOT/.gemini/skills"
build_skills "$ROOT/.agents/skills"
build_skills "$ROOT/.claude/skills"

build_agents neutral "$ROOT/agents"
build_agents gemini "$ROOT/.gemini/agents"
build_agents codex "$ROOT/.codex/agents"
build_agents claude "$ROOT/.claude/agents"

build_refs "$ROOT/references"
build_refs "$ROOT/.gemini/references"
build_refs "$ROOT/.agents/references"
build_refs "$ROOT/.claude/references"

# Refresh command adapters from the canonical CodeBuddy commands.
mkdir -p "$ROOT/commands" "$ROOT/.claude/commands" "$ROOT/.gemini/commands" "$ROOT/.codex/prompts"
for src in "$ROOT/.codebuddy/commands"/*.md; do
  [ -f "$src" ] || continue
  name=$(basename "$src")
  cp "$src" "$ROOT/commands/$name"
  cp "$src" "$ROOT/.claude/commands/$name"

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
  "description": "Production-grade engineering workflow skills for Claude Code.",
  "author": { "name": "agent-skills" }
}
JSON
rm -f "$ROOT/.claude-plugin/plugin.json"
cat > "$ROOT/.claude-plugin/marketplace.json" <<'JSON'
{
  "name": "agent-skills-cs",
  "owner": { "name": "agent-skills" },
  "plugins": [{ "source": "./plugins/claude" }]
}
JSON

printf 'Built adapters: skills=%s agents=%s\n' \
  "$(find "$SRC_SKILLS" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')" \
  "$(find "$SRC_AGENTS" -maxdepth 1 -type f -name '*.md' | wc -l | tr -d ' ')"
