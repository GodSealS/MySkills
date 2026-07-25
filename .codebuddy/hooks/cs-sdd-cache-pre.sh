#!/bin/bash
# cs-sdd-cache-pre.sh — PreToolUse hook for WebFetch (CodeBuddy)
# HTTP resource cache keyed by URL. On 304, serves cached content.
# Dependencies: jq, curl, shasum (or sha256sum).

set -euo pipefail

command -v jq   >/dev/null 2>&1 || exit 0
command -v curl >/dev/null 2>&1 || exit 0
command -v shasum >/dev/null 2>&1 || command -v sha256sum >/dev/null 2>&1 || exit 0

if [ -t 0 ]; then INPUT="{}"; else INPUT=$(cat); fi

dbg() {
  local dir="${PWD}/.codebuddy/.sdd-cache"
  [ "${SDD_CACHE_DEBUG:-0}" = "1" ] || [ -f "$dir/.debug" ] || return 0
  mkdir -p "$dir"
  printf '%s [pre]  %s\n' "$(date -u +%FT%TZ)" "$*" >> "$dir/.debug.log"
}

URL=$(printf '%s' "$INPUT" | jq -r '.tool_input.url // empty' 2>/dev/null || true)
if [ -z "$URL" ]; then exit 0; fi

hash_key() {
  if command -v shasum >/dev/null 2>&1; then
    printf '%s' "$1" | shasum -a 256 | cut -c1-32
  else
    printf '%s' "$1" | sha256sum | cut -c1-32
  fi
}

CACHE_DIR="${PWD}/.codebuddy/.sdd-cache"
CACHE_FILE="$CACHE_DIR/$(hash_key "$URL").json"

if [ ! -f "$CACHE_FILE" ]; then exit 0; fi

ETAG=$(jq -r '.etag // empty' "$CACHE_FILE" 2>/dev/null || true)
LAST_MOD=$(jq -r '.last_modified // empty' "$CACHE_FILE" 2>/dev/null || true)

if [ -z "$ETAG" ] && [ -z "$LAST_MOD" ]; then exit 0; fi

HEADERS=()
[ -n "$ETAG" ]     && HEADERS+=(-H "If-None-Match: $ETAG")
[ -n "$LAST_MOD" ] && HEADERS+=(-H "If-Modified-Since: $LAST_MOD")

STATUS=$(curl -sI -o /dev/null -w "%{http_code}" --max-time 5 -L "${HEADERS[@]}" "$URL" 2>/dev/null || echo "000")

if [ "$STATUS" != "304" ]; then exit 0; fi

CONTENT=$(jq -r '.content // empty' "$CACHE_FILE" 2>/dev/null || true)
if [ -z "$CONTENT" ]; then exit 0; fi

printf '%s\n' "$CONTENT" >&2
exit 2
