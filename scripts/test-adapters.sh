#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

fail() {
  printf '%s\n' "test-adapters.sh: $*" >&2
  exit 1
}

assert_contains() {
  grep -Fq "$2" "$1" || fail "expected $1 to contain: $2"
}

assert_same() {
  cmp -s "$1" "$2" || fail "expected $1 and $2 to match"
}

sh "$ROOT/scripts/build-adapters.sh"

if command -v python3.11 >/dev/null 2>&1; then
  python3.11 - "$ROOT" <<'PY'
import pathlib
import sys
import tomllib

for path in pathlib.Path(sys.argv[1], '.gemini', 'commands').glob('*.toml'):
    with path.open('rb') as handle:
        tomllib.load(handle)
PY
fi

for target in agents .gemini/agents .codex/agents .claude/agents plugins/claude/agents; do
  for agent in cs-architect cs-frontend-lead cs-backend-lead; do
    [ -f "$ROOT/$target/$agent.md" ] || fail "missing $target/$agent.md"
  done
done

assert_contains "$ROOT/.gemini/agents/cs-architect.md" 'model: gemini-2.5-pro'
assert_contains "$ROOT/.codex/agents/cs-frontend-lead.md" 'model: gpt-5.6-sol'
assert_contains "$ROOT/.claude/agents/cs-backend-lead.md" 'model: opus'
assert_contains "$ROOT/.gemini/agents/cs-test-engineer.md" 'model: gemini-2.5-flash'
assert_contains "$ROOT/.codex/agents/cs-web-perf-auditor.md" 'model: gpt-5.6-terra'

for command in cs-build cs-plan cs-spec; do
  assert_same "$ROOT/.codebuddy/commands/$command.md" "$ROOT/commands/$command.md"
  assert_same "$ROOT/.codebuddy/commands/$command.md" "$ROOT/.claude/commands/$command.md"
done
assert_contains "$ROOT/.gemini/commands/cs-build.toml" 'routed by primary owner'
assert_contains "$ROOT/.gemini/commands/cs-plan.toml" 'primary owner'
assert_contains "$ROOT/.gemini/commands/cs-spec.toml" 'cs-architect'
assert_contains "$ROOT/.codex/prompts/cs-incremental.md" 'Invoke the cs-incremental skill'

printf '%s\n' 'test-adapters.sh: passed'
