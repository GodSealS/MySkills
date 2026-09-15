#!/bin/sh
set -eu

# macOS/POSIX installer. Run build-adapters.sh first when source files changed.
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
. "$ROOT/scripts/agent-resources.sh"
TARGET=all
DESTINATION=.
USER_HOME=0
USER_HOME_PATH=

usage() {
  cat <<'EOF'
Usage: scripts/install.sh [--target codebuddy|gemini|codex|claude|all]
                         [--destination PATH] [--user-home]
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; TARGET=$2; shift 2 ;;
    --destination) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; DESTINATION=$2; shift 2 ;;
    --user-home) USER_HOME=1; shift ;;
    --user-home-path) [ "$#" -ge 2 ] || { usage >&2; exit 2; }; USER_HOME_PATH=$2; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

case "$TARGET" in codebuddy|gemini|codex|claude|all) ;; *) usage >&2; exit 2 ;; esac

if [ "$USER_HOME" -eq 1 ]; then
  DESTINATION=${USER_HOME_PATH:-${HOME:?HOME is not set}}
fi
DESTINATION=$(CDPATH= cd -- "$DESTINATION" 2>/dev/null && pwd || { mkdir -p "$DESTINATION"; CDPATH= cd -- "$DESTINATION" && pwd; })

copy_file_safe() (
  src=$1
  dst=$2
  key=$3
  manifest=$4
  mkdir -p "$(dirname -- "$dst")"
  source_hash=$(resource_sha256 "$src")
  known_hash=$(awk -v key="$key" '$1 == key { print $2; exit }' "$manifest" 2>/dev/null || true)
  if [ ! -e "$dst" ] || cmp -s "$src" "$dst" || { [ -n "$known_hash" ] && [ "$(resource_sha256 "$dst")" = "$known_hash" ]; }; then
    cp "$src" "$dst"
    tmp="$manifest.tmp.$$"
    awk -v key="$key" '$1 != key { print }' "$manifest" > "$tmp" 2>/dev/null || true
    printf '%s %s\n' "$key" "$source_hash" >> "$tmp"
    mv "$tmp" "$manifest"
  else
    printf 'Skipped user-owned file: %s\n' "$dst" >&2
  fi
)

merge_tree_safe() (
  src=$1
  dst=$2
  [ -d "$src" ] || return 0
  mkdir -p "$dst"
  manifest="$dst/.agent-skills-manifest"
  # Check resource ancestors before ordinary persona files can be copied.
  if [ "${src##*/}" = agents ]; then
    sync_agent_resources "$src" "$dst"
  elif [ -d "$src/agents" ]; then
    sync_agent_resources "$src/agents" "$dst/agents"
  fi
  [ -f "$manifest" ] || : > "$manifest"
  find "$src" -type f -print | while IFS= read -r file; do
    rel=${file#"$src"/}
    case "$rel" in agents/*/*|agents/.agent-resources-manifest) continue ;; esac
    if [ "${src##*/}" = agents ]; then
      case "$rel" in */*|.agent-resources-manifest) continue ;; esac
    fi
    copy_file_safe "$file" "$dst/$rel" "$rel" "$manifest"
  done
)

install_tree() (
  src=$1
  dst=$2
  merge_tree_safe "$src" "$dst"
  printf 'Installed %s -> %s\n' "$src" "$dst"
)

install_codebuddy() (
  install_tree "$ROOT/.codebuddy" "$DESTINATION/.codebuddy"
)

install_gemini() (
  install_tree "$ROOT/.gemini" "$DESTINATION/.gemini"
  copy_file_safe "$ROOT/GEMINI.md" "$DESTINATION/GEMINI.md" GEMINI.md "$DESTINATION/.agent-skills-root-manifest"
)

install_codex() (
  if [ "$USER_HOME" -eq 1 ]; then
    install_tree "$ROOT/.agents/skills" "$DESTINATION/.codex/skills"
    install_tree "$ROOT/.agents/references" "$DESTINATION/.codex/references"
  else
    install_tree "$ROOT/.agents" "$DESTINATION/.agents"
  fi
  install_tree "$ROOT/.codex" "$DESTINATION/.codex"
  copy_file_safe "$ROOT/AGENTS.md" "$DESTINATION/AGENTS.md" AGENTS.md "$DESTINATION/.agent-skills-root-manifest"
)

install_claude() (
  if [ "$USER_HOME" -eq 1 ]; then
    # Use Claude-adapted skills and agents, never the neutral top-level tree.
    install_tree "$ROOT/.claude/skills" "$DESTINATION/.claude/skills"
    install_tree "$ROOT/.claude/agents" "$DESTINATION/.claude/agents"
    install_tree "$ROOT/.claude/commands" "$DESTINATION/.claude/commands"
    install_tree "$ROOT/.claude/rules" "$DESTINATION/.claude/rules"
  else
    install_tree "$ROOT/.claude" "$DESTINATION/.claude"
    install_tree "$ROOT/plugins/claude" "$DESTINATION/plugins/claude"
    install_tree "$ROOT/.claude-plugin" "$DESTINATION/.claude-plugin"
    copy_file_safe "$ROOT/CLAUDE.md" "$DESTINATION/CLAUDE.md" CLAUDE.md "$DESTINATION/.agent-skills-root-manifest"
  fi
)

case "$TARGET" in
  codebuddy) install_codebuddy ;;
  gemini) install_gemini ;;
  codex) install_codex ;;
  claude) install_claude ;;
  all) install_codebuddy; install_gemini; install_codex; install_claude ;;
esac
