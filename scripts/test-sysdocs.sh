#!/usr/bin/env sh
# Check source resources and shared validator behavior, not prompt wording.
# Platform generation is checked separately by test-adapters.sh.
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$REPO"

PYTHON=
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -B -c 'import yaml' >/dev/null 2>&1; then
    PYTHON=$candidate
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo 'Python with PyYAML is required for SysDocs validation.' >&2
  exit 1
fi

"$PYTHON" -B - <<'PY'
from pathlib import Path
import yaml

skills = ('cs-sysdocs-init', 'cs-sysdocs-update', 'cs-vibe-coding')
for name in skills:
    path = Path('.codebuddy/skills') / name / 'SKILL.md'
    parts = path.read_text(encoding='utf-8-sig').split('---', 2)
    if len(parts) != 3 or parts[0].strip():
        raise SystemExit(f'{path}: missing leading frontmatter')
    fields = yaml.safe_load(parts[1])
    if not isinstance(fields, dict) or fields.get('name') != name:
        raise SystemExit(f'{path}: invalid name/frontmatter')
    for key in ('description', 'allowed-tools', 'agent'):
        if not isinstance(fields.get(key), str) or not fields[key].strip():
            raise SystemExit(f'{path}: missing or invalid {key}')
    if fields.get('user-invocable') is not True:
        raise SystemExit(f'{path}: user-invocable must be true')
for name in ('system', 'overview-template', 'module-template', 'files-template', 'flow-template', 'vibe-template'):
    path = Path('.codebuddy/references') / f'sysdocs-{name}.md'
    if not path.is_file() or not path.read_text(encoding='utf-8-sig').strip():
        raise SystemExit(f'{path}: missing or empty resource')
print('SysDocs source resources: PASS')
PY
"$PYTHON" -B -m unittest discover -s tests -p test_validate_sysdocs.py
