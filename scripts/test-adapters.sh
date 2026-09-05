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

assert_not_contains() {
  grep -Fq "$2" "$1" && fail "expected $1 not to contain: $2"
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
for agent in "$ROOT"/.codebuddy/agents/*.md "$ROOT"/.gemini/agents/*.md "$ROOT"/.codex/agents/*.md "$ROOT"/.claude/agents/*.md "$ROOT"/plugins/claude/agents/*.md; do
  assert_not_contains "$agent" 'skills:'
  assert_contains "$agent" '候选技能，不是自动加载清单'
done

# Skills run on the host's active model, so no skill tree may pin one.
for skill in "$ROOT"/.codebuddy/skills/*/SKILL.md "$ROOT"/skills/*/SKILL.md "$ROOT"/.agents/skills/*/SKILL.md "$ROOT"/.claude/skills/*/SKILL.md "$ROOT"/.gemini/skills/*/SKILL.md "$ROOT"/plugins/claude/skills/*/SKILL.md; do
  if grep -Eq '^model:' "$skill"; then
    fail "skill must not pin a model: $skill"
  fi
done

for command in cs-build cs-plan cs-spec; do
  assert_same "$ROOT/.codebuddy/commands/$command.md" "$ROOT/commands/$command.md"
  assert_same "$ROOT/.codebuddy/commands/$command.md" "$ROOT/.claude/commands/$command.md"
done
assert_contains "$ROOT/.gemini/commands/cs-build.toml" 'routed by primary owner'
assert_contains "$ROOT/.gemini/commands/cs-plan.toml" 'primary owner'
assert_contains "$ROOT/.gemini/commands/cs-spec.toml" 'cs-architect'
assert_contains "$ROOT/.codex/prompts/cs-incremental.md" 'Invoke the cs-incremental skill'
assert_contains "$ROOT/.codex/prompts/cs-agent-brief-review.md" 'description: "审查 Agent Brief'
assert_contains "$ROOT/.codex/prompts/cs-skill-review.md" 'description: "审查一个 skill'

printf '%s\n' 'test-adapters.sh: passed'
