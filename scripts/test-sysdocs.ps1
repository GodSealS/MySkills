<#
.SYNOPSIS
  Validate SysDocs source resources and run the shared validator behavior tests.
.DESCRIPTION
  Platform generation is checked separately by test-adapters.ps1.
  These checks do not prove natural-language workflow or documentation correctness.
#>
$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $Repo
try {
    $ResourceChecks = @"
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
"@
    $ResourceChecks | & python -B -
    if ($LASTEXITCODE -ne 0) { throw 'SysDocs source resource checks failed.' }
    & python -B -m unittest discover -s tests -p test_validate_sysdocs.py
    if ($LASTEXITCODE -ne 0) { throw 'SysDocs validator behavior tests failed.' }
} finally {
    Pop-Location
}
