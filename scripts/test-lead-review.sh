#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
HOOK="$ROOT/.codebuddy/hooks/cs-lead-review.sh"

fail() {
  printf '%s\n' "test-lead-review.sh: $*" >&2
  exit 1
}

run_hook() {
  jq -cn --arg tool "$1" --arg path "$2" \
    '{tool_name: $tool, tool_input: {file_path: $path}}' | bash "$HOOK"
}

assert_contains() {
  printf '%s' "$1" | grep -Fq "$2" || fail "expected output to contain: $2"
}

assert_empty() {
  [ -z "$1" ] || fail "expected no output, got: $1"
}

command -v jq >/dev/null 2>&1 || fail "jq is required"

TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/cs-lead-review.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM

architect=$(run_hook Write 'docs/adr/ADR-001.md')
assert_contains "$architect" 'cs-architect'
assert_contains "$architect" '建议 fan-out'
if printf '%s' "$architect" | grep -Fq '自动触发'; then
  fail 'hook must not claim that fan-out has already happened'
fi

backend=$(run_hook Edit 'src/api/users.ts')
assert_contains "$backend" 'cs-backend-lead'

frontend=$(run_hook Write 'src/components/UserCard.tsx')
assert_contains "$frontend" 'cs-frontend-lead'

quoted=$(run_hook Write 'src/api/a"b.ts')
printf '%s' "$quoted" | jq -e '.priority == "ADVISORY"' >/dev/null || fail 'hook output must be valid JSON'

newline_path=$(printf 'src/api/line\nbreak.ts')
newline=$(run_hook Write "$newline_path")
assert_contains "$newline" 'cs-backend-lead'
printf '%s' "$newline" | jq -e '.priority == "ADVISORY"' >/dev/null || fail 'newline path must produce valid JSON'

frontend_ts="$TMP_DIR/component.ts"
printf '%s\n' "import React, { useState } from 'react';" 'export function View() { const [count] = useState(0); return count; }' > "$frontend_ts"
frontend_heuristic=$(run_hook Write "$frontend_ts")
assert_contains "$frontend_heuristic" 'cs-frontend-lead'

backend_ts="$TMP_DIR/handler.ts"
printf '%s\n' "import express from 'express';" 'export const app = express();' > "$backend_ts"
backend_heuristic=$(run_hook Write "$backend_ts")
assert_contains "$backend_heuristic" 'cs-backend-lead'

mixed_ts="$TMP_DIR/mixed.ts"
printf '%s\n' "import React from 'react';" "import express from 'express';" 'export const app = express();' > "$mixed_ts"
mixed_heuristic=$(run_hook Write "$mixed_ts")
assert_contains "$mixed_heuristic" 'cs-backend-lead'

ignored=$(run_hook Read 'src/api/users.ts')
assert_empty "$ignored"

printf '%s\n' 'test-lead-review.sh: passed'
