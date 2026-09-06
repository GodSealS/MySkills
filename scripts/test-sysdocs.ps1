<#
.SYNOPSIS
  Static + fixture assertion suite for the SysDocs skill pack.

.DESCRIPTION
  Verifies the SysDocs deliverables WITHOUT running the skills as a runtime
  (the skills are agent workflows; the validator is a shared protocol, not a
  deployed runtime). It asserts:
    A. deliverables exist (3 skills + 4 references)
    B. skill frontmatter conformance (no model:, agent cs-architect, invocable)
    C. reference completeness (three-state, schema 1, doc_type, 8 rules,
       reverse-lookup, exclusion table, validator rule IDs, report schema)
    D. cross-references mention the three new skills
    E. fixture three-state classification
    F. fixture structural assertions (manifest, module_id, vibe fields)
    G. human-block pairing
  It never compares agent natural-language prose byte-for-byte.

  Run:  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test-sysdocs.ps1
#>

$ErrorActionPreference = 'Stop'
$Repo = Resolve-Path (Join-Path $PSScriptRoot '..')
$Skills = Join-Path $Repo '.codebuddy\skills'
$Refs   = Join-Path $Repo '.codebuddy\references'
$Fix    = Join-Path $Repo 'tests\fixtures\sysdocs'

$Pass = 0
$Fail = 0
$Failures = @()

function Check([string]$name, [bool]$ok) {
    if ($ok) {
        $script:Pass++
        Write-Host "  PASS  $name"
    } else {
        $script:Fail++
        $script:Failures += $name
        Write-Host "  FAIL  $name"
    }
}

function Section([string]$title) {
    Write-Host ""
    Write-Host "== $title =="
}

# ---------------------------------------------------------------------------
# A. Deliverables exist
# ---------------------------------------------------------------------------
Section "A. Deliverables"
$newSkills = @('cs-sysdocs-init', 'cs-sysdocs-update', 'cs-vibe-coding')
$newRefs = @('sysdocs-system.md', 'sysdocs-overview-template.md', 'sysdocs-module-template.md', 'sysdocs-vibe-template.md')

foreach ($s in $newSkills) {
    Check "skill exists: $s" (Test-Path (Join-Path $Skills "$s\SKILL.md"))
}
foreach ($r in $newRefs) {
    Check "reference exists: $r" (Test-Path (Join-Path $Refs $r))
}

# ---------------------------------------------------------------------------
# B. Skill frontmatter conformance
# ---------------------------------------------------------------------------
Section "B. Skill frontmatter"
foreach ($s in $newSkills) {
    $raw = Get-Content -Raw -Path (Join-Path $Skills "$s\SKILL.md")
    Check "${s}: no model: field" (-not ($raw -match '(?m)^\s*model\s*:'))
    Check "${s}: has name" ($raw -match '(?m)^name\s*:')
    Check "${s}: has description" ($raw -match '(?m)^description\s*:')
    Check "${s}: user-invocable true" ($raw -match '(?m)^user-invocable\s*:\s*true\s*$')
    Check "${s}: agent cs-architect" ($raw -match '(?m)^agent\s*:\s*cs-architect\s*$')
    Check "${s}: allowed-tools incl Task+ListDir" ($raw -match '(?m)^allowed-tools\s*:.*Task.*ListDir')
}

# ---------------------------------------------------------------------------
# C. Reference completeness
# ---------------------------------------------------------------------------
Section "C. Reference completeness"
$sys = Get-Content -Raw -Path (Join-Path $Refs 'sysdocs-system.md')
Check "system: three-state inventory" ($sys -match '未初始化' -and $sys -match '部分初始化' -and $sys -match '已初始化')
Check "system: schema: 1" ($sys -match 'schema\s*:\s*1')
Check "system: doc_type" ($sys -match 'doc_type\s*:\s*overview \| module \| page \| vibe')
Check "system: 8 rules" ($sys -match '引用唯一可定位' -and $sys -match '术语唯一' -and $sys -match '数值具体')
Check "system: reverse-lookup order" ($sys -match 'workspaceSymbol' -and $sys -match 'understand-chat' -and $sys -match 'Grep')
Check "system: exclusion table" ($sys -match 'node_modules' -and $sys -match 'vendor' -and $sys -match '\.env')
Check "system: validator rule IDs" ($sys -match 'SYSDOC-FM-01' -and $sys -match 'SYSDOC-SEC-02')
Check "system: report schema" ($sys -match 'run_id' -and $sys -match 'operation' -and $sys -match 'redactions')

# ---------------------------------------------------------------------------
# D. Cross-references
# ---------------------------------------------------------------------------
Section "D. Cross-references"
$crossRefFiles = @(
    (Join-Path $Repo 'AGENTS.md'),
    (Join-Path $Repo '.codebuddy\AGENTS.md'),
    (Join-Path $Repo '.codebuddy\CODEBUDDY.md'),
    (Join-Path $Skills 'cs-using\SKILL.md'),
    (Join-Path $Skills 'cs-docs-adrs\SKILL.md'),
    (Join-Path $Skills 'cs-spec-driven\SKILL.md'),
    (Join-Path $Skills 'cs-planning\SKILL.md'),
    (Join-Path $Skills 'cs-team-build\SKILL.md'),
    (Join-Path $Skills 'cs-incremental\SKILL.md'),
    (Join-Path $Skills 'cs-git-workflow\SKILL.md'),
    (Join-Path $Repo '.codebuddy\agents\cs-architect.md')
)
foreach ($f in $crossRefFiles) {
    $name = Split-Path $f -Leaf
    $content = Get-Content -Raw -Path $f
    $mentions = ($content -match 'cs-sysdocs-init' -or $content -match 'cs-sysdocs-update' -or $content -match 'cs-vibe-coding')
    Check "cross-ref mentions sysdocs: $name" $mentions
}

# ---------------------------------------------------------------------------
# E. Fixture three-state classification
# ---------------------------------------------------------------------------
Section "E. Fixture three-state"
function Get-ManifestIds([string]$sysRoot) {
    if (-not (Test-Path $sysRoot)) { return @() }
    $raw = Get-Content -Raw -Path $sysRoot
    # crude: extract id: lines inside the modules list
    $ids = @()
    foreach ($m in [regex]::Matches($raw, '(?m)^\s*-\s+id:\s*(\S+)')) { $ids += $m.Groups[1].Value }
    return $ids
}
function Get-ModuleFiles([string]$modDir) {
    if (-not (Test-Path $modDir)) { return @() }
    return @(Get-ChildItem -Path $modDir -File -Filter *.md | ForEach-Object { $_.BaseName })
}

function Get-ManifestEntry([string]$sysRoot, [string]$id) {
    if (-not (Test-Path $sysRoot)) { return $null }
    $raw = Get-Content -Raw -Path $sysRoot
    $pattern = '(?ms)^\s*-\s+id:\s*' + [regex]::Escape($id) + '\s*$.*?(?=^\s*-\s+id:|^---\s*$)'
    $m = [regex]::Match($raw, $pattern)
    if (-not $m.Success) { return $null }
    return $m.Value
}

# C3: vibecoding-only -> UNINITIALIZED
$c3root = Join-Path $Fix 'vibecoding-only\SysDocs'
$c3HasRoot = Test-Path (Join-Path $c3root 'SYSTEM_ROOT.md')
Check "C3 vibecoding-only classified UNINITIALIZED" (-not $c3HasRoot)

# C1: initialized -> manifest consistent
$c1root = Join-Path $Fix 'initialized\SysDocs'
$c1ids = Get-ManifestIds (Join-Path $c1root 'SYSTEM_ROOT.md')
$c1files = Get-ModuleFiles (Join-Path $c1root 'modules')
$c1consistent = ($c1ids.Count -gt 0) -and ($c1ids.Count -eq $c1files.Count)
Check "C1 initialized manifest consistent ($($c1ids.Count) ids vs $($c1files.Count) files)" $c1consistent
$c1entry = Get-ManifestEntry (Join-Path $c1root 'SYSTEM_ROOT.md') 'order-service'
Check "C1 manifest path points to existing module" ($null -ne $c1entry -and $c1entry -match 'path:\s*modules/order-service\.md' -and (Test-Path (Join-Path $c1root 'modules\order-service.md')))
$c1modForManifest = Get-Content -Raw -Path (Join-Path $c1root 'modules\order-service.md')
Check "C1 module_id matches manifest id" ($null -ne $c1entry -and $c1modForManifest -match '(?m)^module_id:\s*order-service\s*$')
Check "C1 pages field is registered and empty" ($null -ne $c1entry -and $c1entry -match '(?m)^\s*pages:\s*\[\]\s*$')

# C2: partial -> manifest declares 2, disk has 1
$c2root = Join-Path $Fix 'partial\SysDocs'
$c2ids = Get-ManifestIds (Join-Path $c2root 'SYSTEM_ROOT.md')
$c2files = Get-ModuleFiles (Join-Path $c2root 'modules')
Check "C2 partial manifest(2) > disk(1) -> repair" (($c2ids.Count -eq 2) -and ($c2files.Count -eq 1))
Check "C2 missing manifest target is detected" (-not (Test-Path (Join-Path $c2root 'modules\payment-service.md')))

# ---------------------------------------------------------------------------
# F. Fixture structural assertions
# ---------------------------------------------------------------------------
Section "F. Fixture structure"
$c1sys = Get-Content -Raw -Path (Join-Path $c1root 'SYSTEM_ROOT.md')
Check "C1 SYSTEM_ROOT doc_type overview" ($c1sys -match 'doc_type\s*:\s*overview')
Check "C1 SYSTEM_ROOT kb_bootstrap" ($c1sys -match 'kb_bootstrap\s*:')
Check "C1 SYSTEM_ROOT has modules manifest" ($c1sys -match '(?m)^modules\s*:')

$c1mod = Get-Content -Raw -Path (Join-Path $c1root 'modules\order-service.md')
Check "C1 module doc_type module + module_id" ($c1mod -match 'doc_type\s*:\s*module' -and $c1mod -match 'module_id\s*:\s*order-service')
Check "C1 module has symbol ref format" ($c1mod -match 'ts\|src/order/service\.ts:OrderService')

$c3vibe = Get-Content -Raw -Path (Join-Path $c3root 'VibeCoding\20260905-1200-fix-timeout.md')
Check "C3 vibe doc_type vibe + vibe_id + targets" ($c3vibe -match 'doc_type\s*:\s*vibe' -and $c3vibe -match 'vibe_id\s*:' -and $c3vibe -match 'targets\s*:')
Check "C3 vibe implementation + merge" ($c3vibe -match 'implementation\s*:' -and $c3vibe -match 'merge\s*:')

# ---------------------------------------------------------------------------
# G. Human-block pairing
# ---------------------------------------------------------------------------
Section "G. Human block"
$c4mod = Get-Content -Raw -Path (Join-Path $Fix 'module-with-human\SysDocs\modules\order-service.md')
$openCount = ([regex]::Matches($c4mod, '<!-- human:start -->')).Count
$closeCount = ([regex]::Matches($c4mod, '<!-- human:end -->')).Count
Check "C4 human blocks paired ($openCount/$closeCount)" (($openCount -gt 0) -and ($openCount -eq $closeCount))
Check "C4 owned_by mixed" ($c4mod -match 'owned_by\s*:\s*mixed')

# ---------------------------------------------------------------------------
# H. Protocol and adapter coverage
# ---------------------------------------------------------------------------
Section "H. Protocol and adapters"
Check "system: KB capability matrix" ($sys -match '7\.3 知识库能力矩阵' -and $sys -match 'READY' -and $sys -match 'STALE' -and $sys -match 'UNINITIALIZED')
$vibeSkill = Get-Content -Raw -Path (Join-Path $Skills 'cs-vibe-coding\SKILL.md')
Check "vibe allowlist includes audit reports" ($vibeSkill -match 'SysDocs/\.meta/reports')
Check "vibe still forbids source/modules writes" ($vibeSkill -match 'Never write\s+`SYSTEM_ROOT\.md`, `modules/\*\*`, source code')
Check "vibe invocation examples" ($vibeSkill -match 'cs-vibe-coding --project-root' -and $vibeSkill -match '--yes')

$report = Join-Path $c1root '.meta\reports\fixture-init.json'
Check "C1 sanitized report exists" (Test-Path $report)
if (Test-Path $report) {
    $reportRaw = Get-Content -Raw $report
    Check "C1 report schema fields" ($reportRaw -match '"schema"\s*:\s*1' -and $reportRaw -match '"run_id"' -and $reportRaw -match '"status"' -and $reportRaw -match '"redactions"')
}
Check "C1 active fixture uses READY KB" ($c1sys -match 'kb:\s*codegraph' -and $c1sys -match 'confidence:\s*high' -and $c1sys -match 'kb_bootstrap:\s*done')
Check "C1 module contains Mermaid and self-check" ($c1mod -match '```mermaid' -and $c1mod -match '自检清单')
$validator = Join-Path $Repo 'scripts\validate-sysdocs.py'
$validatorJson = & python $validator (Join-Path $Fix 'initialized\SysDocs') --json
if ($LASTEXITCODE -ne 0) { throw "validator failed for initialized fixture" }
$validatorResult = $validatorJson | ConvertFrom-Json
Check "shared validator accepts initialized fixture" ($validatorResult.status -eq 'COMPLETE')
$partialJson = & python $validator (Join-Path $Fix 'partial\SysDocs') --json
Check "shared validator rejects partial manifest" ($LASTEXITCODE -eq 2 -and (($partialJson | ConvertFrom-Json).status -eq 'FAILED'))
$initSkill = Get-Content -Raw -Path (Join-Path $Skills 'cs-sysdocs-init\SKILL.md')
$updateSkill = Get-Content -Raw -Path (Join-Path $Skills 'cs-sysdocs-update\SKILL.md')
Check "init has evidence matrix and confirmation gate" ($initSkill -match 'evidence matrix' -and $initSkill -match 'module-list preview' -and $initSkill -match '--yes')
Check "update has schema gate and future-version failure" ($updateSkill -match 'Schema gate' -and $updateSkill -match 'schema.*>' -and $updateSkill -match 'read-only FAIL')
Check "update has transactional rebuild rules" ($updateSkill -match 'dry-run' -and $updateSkill -match 'atomic replace' -and $updateSkill -match 'backup')
Check "update has four-condition vibe merge" ($updateSkill -match 'Four Conditions' -and $updateSkill -match 'All targets')

foreach ($adapter in @('skills','.agents\skills','.gemini\skills','.claude\skills','plugins\claude\skills')) {
    foreach ($s in $newSkills) {
        Check "adapter $adapter has $s" (Test-Path (Join-Path $Repo "$adapter\$s\SKILL.md"))
    }
}
foreach ($adapterRefs in @('references','.agents\references','.gemini\references','.claude\references','plugins\claude\references')) {
    foreach ($r in $newRefs) {
        Check "adapter $adapterRefs has $r" (Test-Path (Join-Path $Repo "$adapterRefs\$r"))
    }
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Section "Summary"
Write-Host "Pass: $Pass  Fail: $Fail"
if ($Failures.Count -gt 0) {
    Write-Host "Failures:"
    $Failures | ForEach-Object { Write-Host "  - $_" }
    exit 1
}
Write-Host "All SysDocs assertions passed."
exit 0
