#!/bin/bash
# cs-sdd-cache-post.sh — PostToolUse hook for WebFetch (CodeBuddy)
# Caches WebFetch results with HTTP validators for future revalidation.
# Dependencies: jq, curl, shasum (or sha256sum).

set -euo pipefail

command -v jq   >/dev/null 2>&1 || exit 0
command -v curl >/dev/null 2>&1 || exit 0

if [ -t 0 ]; then INPUT="{}"; else INPUT=$(cat); fi

URL=$(printf '%s' "$INPUT" | jq -r '.tool_input.url // empty' 2>/dev/null || true)
if [ -z "$URL" ]; then exit 0; fi

# Extract HTTP response headers from the tool result or fetch them
HEAD_RESULT=$(curl -sI -o /dev/null -w '%{http_code}\n%header{etag}\n%header{last-modified}' --max-time 5 -L "$URL" 2>/dev/null || echo -e "000\n\n")
HTTP_CODE=$(echo "$HEAD_RESULT" | sed -n '1p')
ETAG=$(echo "$HEAD_RESULT" | sed -n '2p' | tr -d '\r')
LAST_MOD=$(echo "$HEAD_RESULT" | sed -n '3p' | tr -d '\r')

# Only cache if we have validators
if [ "$HTTP_CODE" = "200" ] && { [ -n "$ETAG" ] || [ -n "$LAST_MOD" ]; }; then
  CACHE_DIR="${PWD}/.codebuddy/.sdd-cache"
  mkdir -p "$CACHE_DIR"

  hash_key() {
    if command -v shasum >/dev/null 2>&1; then
      printf '%s' "$1" | shasum -a 256 | cut -c1-32
    else
      printf '%s' "$1" | sha256sum | cut -c1-32
    fi
  }

  CONTENT=$(printf '%s' "$INPUT" | jq -r '.tool_result // empty' 2>/dev/null || true)
  PROMPT=$(printf '%s' "$INPUT" | jq -r '.tool_input.prompt // empty' 2>/dev/null || true)

  if [ -n "$CONTENT" ]; then
    jq -n \
      --arg etag "$ETAG" \
      --arg last_modified "$LAST_MOD" \
      --arg content "$CONTENT" \
      --arg prompt "$PROMPT" \
      --arg fetched_at "$(date +%s)" \
      '{etag: $etag, last_modified: $last_modified, content: $content, prompt: $prompt, fetched_at: ($fetched_at | tonumber)}' \
      > "$CACHE_DIR/$(hash_key "$URL").json"
  fi
fi

exit 0
