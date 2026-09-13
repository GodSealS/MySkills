<#
.SYNOPSIS
  Runs the PowerShell adapter builder in an isolated temporary tree.

.DESCRIPTION
  Windows counterpart to test-adapters.sh. It verifies regeneration from the
  .codebuddy source tree without mutating the working tree.
#>

$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Temp = Join-Path ([IO.Path]::GetTempPath()) ('agent-skills-adapter-test-' + [guid]::NewGuid().ToString('N'))

function Assert([string]$Name, [bool]$Ok) {
    if (-not $Ok) { throw "FAIL: $Name" }
    Write-Host "PASS: $Name"
}

try {
    New-Item -ItemType Directory -Path $Temp -Force | Out-Null
    foreach ($path in @('.codebuddy', 'scripts', '.claude\rules')) {
        $src = Join-Path $Repo $path
        if (Test-Path $src) {
            Copy-Item -LiteralPath $src -Destination (Join-Path $Temp $path) -Recurse -Force
        }
    }

    $before = @(Get-ChildItem -LiteralPath $Repo -Recurse -File | ForEach-Object {
        "$($_.FullName)|$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)"
    })

    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Temp 'scripts\build-adapters.ps1')
    if ($LASTEXITCODE -ne 0) { throw "builder exited with $LASTEXITCODE" }

    $newSkills = @('cs-sysdocs-init', 'cs-sysdocs-update', 'cs-vibe-coding', 'cs-team-review')
    foreach ($tree in @('skills', '.agents\skills', '.gemini\skills', '.claude\skills', 'plugins\claude\skills')) {
        foreach ($skill in $newSkills) {
            $file = Join-Path $Temp "$tree\$skill\SKILL.md"
            Assert "generated $tree/$skill" (Test-Path $file)
            $raw = Get-Content -Raw $file
            Assert "$tree/$skill has no model field" (-not ($raw -match '(?m)^model\s*:'))
            if ($skill -like 'cs-sysdocs-*' -or $skill -eq 'cs-vibe-coding') {
                Assert "$tree/$skill has resolvable reference path" ($raw -match '\.\./\.\./references/sysdocs-system\.md')
            }
        }
    }
    foreach ($tree in @('commands', '.gemini\commands', '.claude\commands', '.codex\prompts')) {
        $suffix = if ($tree -eq '.gemini\commands') { '.toml' } elseif ($tree -eq '.codex\prompts') { '.md' } else { '.md' }
        Assert "generated $tree/cs-team-review" (Test-Path (Join-Path $Temp "$tree\cs-team-review$suffix"))
    }
    foreach ($ref in @('sysdocs-system.md', 'sysdocs-overview-template.md', 'sysdocs-module-template.md', 'sysdocs-vibe-template.md')) {
        foreach ($tree in @('references', '.agents\references', '.gemini\references', '.claude\references', 'plugins\claude\references')) {
            Assert "generated $tree/$ref" (Test-Path (Join-Path $Temp "$tree\$ref"))
        }
    }
    Assert 'no SysDocs command source was added' (-not (Test-Path (Join-Path $Temp '.codebuddy\commands\cs-sysdocs-init.md')) -and -not (Test-Path (Join-Path $Temp '.codebuddy\commands\cs-sysdocs-update.md')) -and -not (Test-Path (Join-Path $Temp '.codebuddy\commands\cs-vibe-coding.md')))

    $after = @(Get-ChildItem -LiteralPath $Repo -Recurse -File | ForEach-Object {
        "$($_.FullName)|$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)"
    })
    Assert 'builder does not mutate source working tree' (($before -join "`n") -ceq ($after -join "`n"))
    Write-Host 'test-adapters.ps1: passed'
}
finally {
    if (Test-Path $Temp) { Remove-Item -LiteralPath $Temp -Recurse -Force }
}
