#!/bin/bash
# cs-simplify-ignore.sh — Hook for Read (PreToolUse), Edit|Write (PostToolUse), Stop
# Protects code blocks marked with simplify-ignore-start/end comments from being simplified.
# Dependencies: jq, shasum or sha1sum (auto-detected)

set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  printf '%s\n' "error: missing jq" >&2; exit 1
fi

CACHE="${PWD}/.codebuddy/.simplify-ignore-cache"
if [ -t 0 ]; then INPUT="{}"; else INPUT=$(cat); fi

TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null) || true
FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || true

hash_cmd() {
  if command -v shasum >/dev/null 2>&1; then shasum
  elif command -v sha1sum >/dev/null 2>&1; then sha1sum
  else printf '%s\n' "error: missing shasum or sha1sum" >&2; exit 1; fi
}
file_id() { printf '%s' "$1" | hash_cmd | cut -c1-16; }

# Stop: restore all files from backup
if [ -z "$TOOL_NAME" ]; then
  [ -d "$CACHE" ] || exit 0
  for bak in "$CACHE"/*.bak; do
    [ -f "$bak" ] || continue
    fid="${bak##*/}"; fid="${fid%.bak}"
    pathfile="$CACHE/${fid}.path"
    [ -f "$pathfile" ] || { rm -f "$bak"; continue; }
    orig=$(cat "$pathfile")
    if [ -f "$orig" ]; then
      cat "$bak" > "$orig"
      rm -f "$bak" "$pathfile" "$CACHE/${fid}".block.*
    fi
  done
  exit 0
fi

[ -z "$FILE_PATH" ] && exit 0

# PreToolUse Read: Replace simplify-ignore blocks with placeholders
if [ "$TOOL_NAME" = "Read" ]; then
  [ -f "$FILE_PATH" ] || exit 0
  mkdir -p "$CACHE"
  ID=$(file_id "$FILE_PATH")
  [ -f "$CACHE/${ID}.bak" ] && exit 0

  grep -q 'simplify-ignore-start' -- "$FILE_PATH" || exit 0

  cp "$FILE_PATH" "$CACHE/${ID}.bak"
  printf '%s' "$FILE_PATH" > "$CACHE/${ID}.path"

  # Simple placeholder substitution
  awk '
    /simplify-ignore-start/ { in_block=1; print gensub(/simplify-ignore-start.*/, "/* BLOCK_PROTECTED: do not simplify */", "g"); next }
    /simplify-ignore-end/   { in_block=0; next }
    !in_block               { print }
  ' "$FILE_PATH" > "${FILE_PATH}.filtered"
  mv "${FILE_PATH}.filtered" "$FILE_PATH"
  exit 0
fi

# PostToolUse Edit|Write: Restore blocks from backup
if [ "$TOOL_NAME" = "Edit" ] || [ "$TOOL_NAME" = "Write" ]; then
  ID=$(file_id "$FILE_PATH")
  [ -f "$CACHE/${ID}.bak" ] || exit 0

  # Restore original
  cat "$CACHE/${ID}.bak" > "$FILE_PATH"
  rm -f "$CACHE/${ID}.bak" "$CACHE/${ID}.path"
  exit 0
fi

exit 0
