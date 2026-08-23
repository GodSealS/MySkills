#!/bin/sh
set -eu

# macOS/POSIX adapter builder. .codebuddy is the source of truth.
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
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

source_model() {
  awk '$1 == "model:" { print $2; exit }' "$1"
}

platform_model() {
  platform=$1
  model=$2
  case "$platform:$model" in
    claude:DeepSeek-V4-Pro) printf '%s\n' opus ;;
    claude:DeepSeek-V4-Flash) printf '%s\n' sonnet ;;
    codex:DeepSeek-V4-Pro) printf '%s\n' gpt-5.6-sol ;;
    codex:DeepSeek-V4-Flash) printf '%s\n' gpt-5.6-terra ;;
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
    in_fm && $0 ~ /^(argument-hint|user-invocable|allowed-tools|agent):[[:space:]]/ { next }
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
  for ref in "$SRC_REFS"/*.md; do
    [ -f "$ref" ] || continue
    name=$(basename "$ref")
    tmp="$target_file.tmp.$$"
    sed "s#[^[:space:]]*references/$name#../../references/$name#g; s#\.codebuddy/skills/code-query/##g" "$target_file" > "$tmp"
    mv "$tmp" "$target_file"
  done
)

build_skills() (
  platform=$1
  dst=$2
  mkdir -p "$dst"
  for src in "$SRC_SKILLS"/*; do
    [ -d "$src" ] || continue
    name=$(basename "$src")
    target="$dst/$name"
    copy_tree "$src" "$target"
    definition="$target/SKILL.md"
    strip_skill_frontmatter "$definition"
    fix_refs "$definition"
    if [ "$platform" != neutral ]; then
      replace_model "$definition" "$(platform_model "$platform" "$(source_model "$src/SKILL.md")")"
    fi
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
      case "$(basename "$src")" in
        cs-code-reviewer.md|cs-security-auditor.md) tier=DeepSeek-V4-Pro ;;
        cs-test-engineer.md|cs-web-perf-auditor.md) tier=DeepSeek-V4-Flash ;;
        *) die "unsupported persona $(basename "$src")" ;;
      esac
      replace_model "$target" "$(platform_model "$platform" "$tier")"
    fi
  done
)

build_refs() (
  dst=$1
  mkdir -p "$dst"
  for src in "$SRC_REFS"/*.md; do [ -f "$src" ] && cp "$src" "$dst/"; done
)

build_skills neutral "$ROOT/skills"
build_skills gemini "$ROOT/.gemini/skills"
build_skills codex "$ROOT/.agents/skills"
build_skills claude "$ROOT/.claude/skills"

build_agents neutral "$ROOT/agents"
build_agents gemini "$ROOT/.gemini/agents"
build_agents codex "$ROOT/.codex/agents"
build_agents claude "$ROOT/.claude/agents"

build_refs "$ROOT/references"
build_refs "$ROOT/.gemini/references"
build_refs "$ROOT/.agents/references"
build_refs "$ROOT/.claude/references"

# Keep existing command adapters and refresh the canonical/Claude markdown copies.
mkdir -p "$ROOT/commands" "$ROOT/.claude/commands"
for src in "$ROOT/.codebuddy/commands"/*.md; do
  [ -f "$src" ] || continue
  cp "$src" "$ROOT/commands/$(basename "$src")"
  cp "$src" "$ROOT/.claude/commands/$(basename "$src")"
done

# Claude plugins must contain Claude-native skills and agents at plugin root.
PLUGIN="$ROOT/plugins/claude"
mkdir -p "$PLUGIN"
copy_tree "$ROOT/.claude/skills" "$PLUGIN/skills"
copy_tree "$ROOT/.claude/agents" "$PLUGIN/agents"
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
