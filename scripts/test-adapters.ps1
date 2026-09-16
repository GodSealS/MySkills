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

    foreach ($commandPath in @('.codebuddy\commands\cs-build.md', 'commands\cs-build.md', '.gemini\commands\cs-build.toml', '.claude\commands\cs-build.md', 'plugins\claude\commands\cs-build.md')) {
        $commandFile = Join-Path $Temp $commandPath
        $commandRaw = Get-Content -Raw -LiteralPath $commandFile
        $reference = [regex]::Match($commandRaw, '`([^`]+/sysdocs-design-context\.md)`')
        Assert "$commandPath declares the design context reference" $reference.Success
        $target = Join-Path (Split-Path -Parent $commandFile) $reference.Groups[1].Value
        Assert "$commandPath resolves the design context reference" (Test-Path -LiteralPath $target -PathType Leaf)
    }

    $newSkills = @('cs-sysdocs-init', 'cs-sysdocs-update', 'cs-vibe-coding', 'cs-team-review', 'cs-team-refactor')
    foreach ($tree in @('skills', '.agents\skills', '.gemini\skills', '.claude\skills', 'plugins\claude\skills')) {
        foreach ($skill in $newSkills) {
            $file = Join-Path $Temp "$tree\$skill\SKILL.md"
            Assert "generated $tree/$skill" (Test-Path $file)
            $raw = Get-Content -Raw $file
            Assert "$tree/$skill has no model field" (-not ($raw -match '(?m)^model\s*:'))
            if ($skill -like 'cs-sysdocs-*' -or $skill -eq 'cs-vibe-coding') {
                Assert "$tree/$skill has resolvable reference path" ($raw -match '\.\./\.\./references/sysdocs-system\.md')
                $sourceRaw = Get-Content -Raw (Join-Path $Temp ".codebuddy\skills\$skill\SKILL.md")
                $linkPattern = '\[[^\]\r\n]+\]\([^\)\r\n]+\)'
                $sourceLinks = @([regex]::Matches($sourceRaw, $linkPattern) | ForEach-Object { $_.Value })
                $generatedLinks = @([regex]::Matches($raw, $linkPattern) | ForEach-Object { $_.Value })
                Assert "$tree/$skill preserves Markdown link labels and targets" (($sourceLinks -join "`n") -ceq ($generatedLinks -join "`n"))
            }
            if ($skill -eq 'cs-team-refactor') {
                foreach ($ref in @('artifact-contract.md', 'evidence-and-measurement.md')) {
                    Assert "$tree/$skill includes $ref" (Test-Path (Join-Path $Temp "$tree\$skill\references\$ref"))
                }
                foreach ($ref in @('sysdocs-design-context.md', 'sysdocs-system.md')) {
                    Assert "$tree/$skill resolves shared $ref" (Test-Path (Join-Path $Temp "$tree\$skill\..\..\references\$ref"))
                }
                Assert "$tree/$skill retains manual invocation policy" ($raw -match '(?m)^disable-model-invocation:\s*true\s*$')
                $codexMeta = Join-Path $Temp '.agents\skills\cs-team-refactor\agents\openai.yaml'
                Assert 'Codex cs-team-refactor disables implicit invocation' ((Get-Content -Raw $codexMeta) -match 'allow_implicit_invocation:\s*false')
            }
        }
    }
    foreach ($tree in @('commands', '.gemini\commands', '.claude\commands', '.codex\prompts')) {
        $suffix = if ($tree -eq '.gemini\commands') { '.toml' } elseif ($tree -eq '.codex\prompts') { '.md' } else { '.md' }
        Assert "generated $tree/cs-team-review" (Test-Path (Join-Path $Temp "$tree\cs-team-review$suffix"))
        Assert "generated $tree/cs-team-refactor" (Test-Path (Join-Path $Temp "$tree\cs-team-refactor$suffix"))
    }
    foreach ($commandPath in @('.codebuddy\commands\cs-team-refactor.md', 'commands\cs-team-refactor.md', '.gemini\commands\cs-team-refactor.toml', '.claude\commands\cs-team-refactor.md')) {
        $raw = Get-Content -Raw -LiteralPath (Join-Path $Temp $commandPath)
        Assert "$commandPath forwards the user's arguments" ($raw -match '\$ARGUMENTS')
    }
    $knowledgeBaseAdminModels = [ordered]@{
        'agents' = 'DeepSeek-V4-Flash'
        '.gemini\agents' = 'gemini-2.5-flash'
        '.codex\agents' = 'gpt-5.6-luna'
        '.claude\agents' = 'sonnet'
        'plugins\claude\agents' = 'sonnet'
    }
    foreach ($tree in $knowledgeBaseAdminModels.Keys) {
        $file = Join-Path $Temp "$tree\cs-knowledge-base-admin.md"
        Assert "generated $tree/cs-knowledge-base-admin" (Test-Path $file)
        $raw = Get-Content -Raw $file
        $expectedModel = [regex]::Escape($knowledgeBaseAdminModels[$tree])
        Assert "$tree/cs-knowledge-base-admin uses the platform low-cost model" ($raw -match "(?m)^model:\s*$expectedModel\s*$")
    }
    foreach ($agent in @('cs-test-engineer', 'cs-web-perf-auditor', 'cs-knowledge-base-admin')) {
        $file = Join-Path $Temp ".codex\agents\$agent.md"
        $raw = Get-Content -Raw $file
        Assert ".codex/agents/$agent uses gpt-5.6-luna" ($raw -match '(?m)^model:\s*gpt-5\.6-luna\s*$')
    }
    $knowledgeBaseAdmin = Get-Content -Raw (Join-Path $Temp '.codex\agents\cs-knowledge-base-admin.md')
    Assert 'knowledge-base admin requires an existing supported knowledge base' ($knowledgeBaseAdmin -match 'At least one supported knowledge base must already exist')
    Assert 'knowledge-base admin terminates when no supported knowledge base exists' ($knowledgeBaseAdmin -match 'TERMINATED — no supported knowledge base exists')
    Assert 'knowledge-base admin does not prohibit refresh-time deletion' ($knowledgeBaseAdmin -notmatch 'created, installed, repaired, or deleted')
    foreach ($agent in @('cs-architect', 'cs-backend-lead', 'cs-frontend-lead', 'cs-code-reviewer', 'cs-security-auditor', 'cs-test-engineer', 'cs-web-perf-auditor')) {
        $raw = Get-Content -Raw (Join-Path $Temp ".codex\agents\$agent.md")
        Assert ".codex/agents/$agent limits autonomous skill loading to its own roster" ($raw -match 'may autonomously load 2–3 skills when their triggers match; it must not load skills outside this roster')
        $roster = [regex]::Match($raw, '(?ms)^## Optional Skill Roster\s*(.*?)(?=^## |\z)').Groups[1].Value
        Assert ".codex/agents/$agent has an Optional Skill Roster" ($roster.Length -gt 0)
        Assert ".codex/agents/$agent Optional Skill Roster is English-only" ($roster -notmatch '[\u3400-\u9fff]')
    }
    $advisor = Get-Content -Raw (Join-Path $Temp '.codex\agents\cs-review-advisor.md')
    Assert 'advisor has no minimum skill count' ($advisor -match 'there is no minimum skill count')
    Assert 'advisor allows only the two external auxiliaries' ($advisor -match 'Only the following external auxiliaries' -and $advisor -match '\| `cs-code-query` \|' -and $advisor -match '\| `cs-docs-adrs` \|')
    $teamBuild = Get-Content -Raw (Join-Path $Temp '.agents\skills\cs-team-build\SKILL.md')
    Assert 'team-build skips nested knowledge-base refreshes during task implementation' ($teamBuild -match 'Skip the final knowledge-base-administrator step; Team Build owns its single invocation in Phase 5')
    foreach ($ref in @('sysdocs-system.md', 'sysdocs-overview-template.md', 'sysdocs-module-template.md', 'sysdocs-vibe-template.md', 'sysdocs-files-template.md', 'sysdocs-flow-template.md')) {
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
    if (Test-Path $Temp) {
        $cleanupPath = (Resolve-Path -LiteralPath $Temp).Path
        $tempParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/')
        if ((Split-Path -Parent $cleanupPath) -ne $tempParent -or (Split-Path -Leaf $cleanupPath) -notlike 'agent-skills-adapter-test-*') {
            throw "Refusing adapter test cleanup outside its temporary directory: $cleanupPath"
        }
        Remove-Item -LiteralPath $cleanupPath -Recurse -Force
    }
}
