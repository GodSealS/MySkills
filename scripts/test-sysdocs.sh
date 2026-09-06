#!/usr/bin/env sh
# Static + fixture assertion suite for the SysDocs skill pack (POSIX).
# Mirrors scripts/test-sysdocs.ps1; asserts structure/rules, never compares
# agent natural-language prose byte-for-byte.
# Run: sh scripts/test-sysdocs.sh

set -u

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS="$REPO/.codebuddy/skills"
REFS="$REPO/.codebuddy/references"
FIX="$REPO/tests/fixtures/sysdocs"
VALIDATOR_TMP=$(mktemp -d "${TMPDIR:-/tmp}/sysdocs-validator.XXXXXX")
trap 'rm -rf "$VALIDATOR_TMP"' EXIT HUP INT TERM

PASS=0
FAIL=0
FAILURES=""

check() {
  name="$1"; ok="$2"
  if [ "$ok" = "1" ]; then
    PASS=$((PASS+1)); echo "  PASS  $name"
  else
    FAIL=$((FAIL+1)); FAILURES="$FAILURES\n  - $name"; echo "  FAIL  $name"
  fi
}

section() { echo ""; echo "== $1 =="; }

contains() { grep -Eq "$2" "$1"; }

# A. Deliverables
section "A. Deliverables"
for s in cs-sysdocs-init cs-sysdocs-update cs-vibe-coding; do
  [ -f "$SKILLS/$s/SKILL.md" ] && check "skill exists: $s" 1 || check "skill exists: $s" 0
done
for r in sysdocs-system.md sysdocs-overview-template.md sysdocs-module-template.md sysdocs-vibe-template.md; do
  [ -f "$REFS/$r" ] && check "reference exists: $r" 1 || check "reference exists: $r" 0
done

# B. Skill frontmatter
section "B. Skill frontmatter"
for s in cs-sysdocs-init cs-sysdocs-update cs-vibe-coding; do
  f="$SKILLS/$s/SKILL.md"
  grep -qE '^\s*model\s*:' "$f" && check "$s: no model" 0 || check "$s: no model" 1
  grep -qE '^agent\s*:\s*cs-architect\s*$' "$f" && check "$s: agent cs-architect" 1 || check "$s: agent cs-architect" 0
  grep -qE '^user-invocable\s*:\s*true\s*$' "$f" && check "$s: user-invocable true" 1 || check "$s: user-invocable true" 0
done

# C. Reference completeness
section "C. Reference completeness"
sys="$REFS/sysdocs-system.md"
contains "$sys" 'schema[[:space:]]*:[[:space:]]*1' && check "system: schema 1" 1 || check "system: schema 1" 0
contains "$sys" 'doc_type[[:space:]]*:[[:space:]]*overview[[:space:]]*\|[[:space:]]*module[[:space:]]*\|[[:space:]]*page[[:space:]]*\|[[:space:]]*vibe' && check "system: doc_type" 1 || check "system: doc_type" 0
contains "$sys" 'SYSDOC-FM-01' && check "system: validator rule IDs" 1 || check "system: validator rule IDs" 0
contains "$sys" 'run_id' && check "system: report schema" 1 || check "system: report schema" 0
contains "$sys" '7\.3 知识库能力矩阵' && check "system: KB capability matrix" 1 || check "system: KB capability matrix" 0

# D. Cross-references
section "D. Cross-references"
for f in \
  "$REPO/AGENTS.md" \
  "$REPO/.codebuddy/AGENTS.md" \
  "$REPO/.codebuddy/CODEBUDDY.md" \
  "$SKILLS/cs-using/SKILL.md" \
  "$SKILLS/cs-docs-adrs/SKILL.md" \
  "$SKILLS/cs-spec-driven/SKILL.md" \
  "$SKILLS/cs-planning/SKILL.md" \
  "$SKILLS/cs-team-build/SKILL.md" \
  "$SKILLS/cs-incremental/SKILL.md" \
  "$SKILLS/cs-git-workflow/SKILL.md" \
  "$REPO/.codebuddy/agents/cs-architect.md"; do
  n="$(basename "$f")"
  if grep -qE 'cs-sysdocs-init|cs-sysdocs-update|cs-vibe-coding' "$f"; then check "cross-ref: $n" 1; else check "cross-ref: $n" 0; fi
done

# E. Fixture three-state
section "E. Fixture three-state"
[ ! -f "$FIX/vibecoding-only/SysDocs/SYSTEM_ROOT.md" ] && check "C3 UNINITIALIZED" 1 || check "C3 UNINITIALIZED" 0

c1root="$FIX/initialized/SysDocs"
c1_ids=$(grep -cE '^\s*-\s+id:' "$c1root/SYSTEM_ROOT.md")
c1_files=$(ls "$c1root/modules"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$c1_ids" -gt 0 ] && [ "$c1_ids" -eq "$c1_files" ] && check "C1 manifest consistent" 1 || check "C1 manifest consistent" 0
grep -qE '^\s*-\s+id:\s+order-service\s*$' "$c1root/SYSTEM_ROOT.md" && check "C1 manifest id order-service" 1 || check "C1 manifest id order-service" 0
grep -qE '^\s+path:\s+modules/order-service\.md\s*$' "$c1root/SYSTEM_ROOT.md" && [ -f "$c1root/modules/order-service.md" ] && check "C1 manifest path exists" 1 || check "C1 manifest path exists" 0
grep -qE '^module_id:\s*order-service\s*$' "$c1root/modules/order-service.md" && check "C1 module_id matches" 1 || check "C1 module_id matches" 0
grep -qE '^\s+pages:\s+\[\]\s*$' "$c1root/SYSTEM_ROOT.md" && check "C1 pages registered" 1 || check "C1 pages registered" 0

c2root="$FIX/partial/SysDocs"
c2_ids=$(grep -cE '^\s*-\s+id:' "$c2root/SYSTEM_ROOT.md")
c2_files=$(ls "$c2root/modules"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$c2_ids" -eq 2 ] && [ "$c2_files" -eq 1 ] && check "C2 partial -> repair" 1 || check "C2 partial -> repair" 0
[ ! -f "$c2root/modules/payment-service.md" ] && check "C2 missing manifest target" 1 || check "C2 missing manifest target" 0

# F. Fixture structure
section "F. Fixture structure"
contains "$c1root/SYSTEM_ROOT.md" 'doc_type[[:space:]]*:[[:space:]]*overview' && check "C1 doc_type overview" 1 || check "C1 doc_type overview" 0
contains "$c1root/modules/order-service.md" 'module_id[[:space:]]*:[[:space:]]*order-service' && check "C1 module_id" 1 || check "C1 module_id" 0
c3vibe="$FIX/vibecoding-only/SysDocs/VibeCoding/20260905-1200-fix-timeout.md"
contains "$c3vibe" 'doc_type[[:space:]]*:[[:space:]]*vibe' && check "C3 vibe doc_type" 1 || check "C3 vibe doc_type" 0

# G. Human block
section "G. Human block"
c4mod="$FIX/module-with-human/SysDocs/modules/order-service.md"
c4open=$(grep -c '<!-- human:start -->' "$c4mod")
c4close=$(grep -c '<!-- human:end -->' "$c4mod")
[ "$c4open" -gt 0 ] && [ "$c4open" -eq "$c4close" ] && check "C4 human paired" 1 || check "C4 human paired" 0
contains "$c4mod" 'owned_by[[:space:]]*:[[:space:]]*mixed' && check "C4 owned_by mixed" 1 || check "C4 owned_by mixed" 0

# H. Protocol and adapters
section "H. Protocol and adapters"
contains "$sys" 'READY' && contains "$sys" 'STALE' && contains "$sys" 'UNINITIALIZED' && check "system: KB capability matrix" 1 || check "system: KB capability matrix" 0
vibe_skill="$SKILLS/cs-vibe-coding/SKILL.md"
contains "$vibe_skill" 'SysDocs/\.meta/reports' && check "vibe allowlist includes audit reports" 1 || check "vibe allowlist includes audit reports" 0
contains "$vibe_skill" 'cs-vibe-coding --project-root' && check "vibe invocation examples" 1 || check "vibe invocation examples" 0
report="$FIX/initialized/SysDocs/.meta/reports/fixture-init.json"
[ -f "$report" ] && check "C1 sanitized report exists" 1 || check "C1 sanitized report exists" 0
contains "$c1root/SYSTEM_ROOT.md" 'kb:[[:space:]]*codegraph' && contains "$c1root/SYSTEM_ROOT.md" 'confidence:[[:space:]]*high' && contains "$c1root/SYSTEM_ROOT.md" 'kb_bootstrap:[[:space:]]*done' && check "C1 active fixture uses READY KB" 1 || check "C1 active fixture uses READY KB" 0
contains "$c1root/modules/order-service.md" '```mermaid' && contains "$c1root/modules/order-service.md" '自检清单' && check "C1 module contains Mermaid and self-check" 1 || check "C1 module contains Mermaid and self-check" 0
PYTHON=
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import yaml' >/dev/null 2>&1; then
    PYTHON=$candidate
    break
  fi
done
if [ -n "$PYTHON" ]; then
  "$PYTHON" "$REPO/scripts/validate-sysdocs.py" "$c1root" --json >"$VALIDATOR_TMP/c1.json" && check "shared validator accepts initialized fixture" 1 || check "shared validator accepts initialized fixture" 0
  if "$PYTHON" "$REPO/scripts/validate-sysdocs.py" "$c2root" --json >"$VALIDATOR_TMP/c2.json"; then code=0; else code=$?; fi
  [ "$code" -eq 2 ] && grep -q '"status": "FAILED"' "$VALIDATOR_TMP/c2.json" && check "shared validator rejects partial manifest" 1 || check "shared validator rejects partial manifest" 0
else
  check "shared validator available" 0
fi
for adapter in skills .agents/skills .gemini/skills .claude/skills plugins/claude/skills; do
  for s in cs-sysdocs-init cs-sysdocs-update cs-vibe-coding; do
    [ -f "$REPO/$adapter/$s/SKILL.md" ] && check "adapter $adapter has $s" 1 || check "adapter $adapter has $s" 0
  done
done
for adapter in references .agents/references .gemini/references .claude/references plugins/claude/references; do
  for r in sysdocs-system.md sysdocs-overview-template.md sysdocs-module-template.md sysdocs-vibe-template.md; do
    [ -f "$REPO/$adapter/$r" ] && check "adapter $adapter has $r" 1 || check "adapter $adapter has $r" 0
  done
done

# Summary
section "Summary"
echo "Pass: $PASS  Fail: $FAIL"
if [ "$FAIL" -gt 0 ]; then
  printf "%b\n" "$FAILURES"
  exit 1
fi
echo "All SysDocs assertions passed."
exit 0
