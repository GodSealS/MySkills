<#
.SYNOPSIS
  Builds cross-platform adapters from the authoritative CodeBuddy source (.codebuddy/).

.DESCRIPTION
  The single source of truth is .codebuddy/ (skills, agents, commands, references).
  This script regenerates platform-neutral artifacts so the pack installs cleanly to
  Codex, CodeBuddy, and .gemini:

    skills/         -> canonical neutral skills (name + description frontmatter only)
    agents/         -> canonical neutral personas
    references/     -> canonical checklists
    commands/       -> canonical slash commands (markdown)
    .gemini/        -> Gemini CLI adapter (skills + commands/*.toml + agents + GEMINI.md)
    .agents/        -> Codex skill adapter (.agents/skills)
    .codex/         -> Codex adapter (prompts/ + agents/)

  CodeBuddy keeps its own .codebuddy/ tree and is unchanged by this script.

  Run:  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-adapters.ps1
#>

$ErrorActionPreference = 'Stop'
$Repo = Resolve-Path (Join-Path $PSScriptRoot '..')
$SrcSkills   = Join-Path $Repo '.codebuddy\skills'
$SrcAgents   = Join-Path $Repo '.codebuddy\agents'
$SrcCommands = Join-Path $Repo '.codebuddy\commands'
$SrcRefs     = Join-Path $Repo '.codebuddy\references'

# Skills excluded from neutral adapters.
# (None currently excluded — all skills sync to all platforms.)
$ExcludeSkills = @()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Clear-Dir($path) {
    if (Test-Path $path) { Remove-Item -Recurse -Force $path }
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}

function Neutralize-Frontmatter($content) {
    # Keep name + description; strip CodeBuddy-only fields
    # (argument-hint, user-invocable, allowed-tools, agent).
    # Filtering (not rebuilding) preserves multi-line descriptions.
    if ($content -match '(?s)^(---\r?\n)(.*?)(\r?\n---\r?\n)') {
        $open  = $matches[1]
        $fm    = $matches[2]
        $close = $matches[3]
        $body  = $content.Substring($matches[0].Length)
        $keep  = @()
        foreach ($l in ($fm -split "`r?`n")) {
            if ($l -match '^(argument-hint|user-invocable|allowed-tools|agent)\s*:') { continue }
            $keep += $l
        }
        return $open + ($keep -join "`n") + $close + $body
    }
    return $content
}

function Fix-Refs($text) {
    # Normalize every reference link to ../../references/<file> so it resolves from
    # skills/<name>/, .gemini/skills/<name>/ and .agents/skills/<name>/ (all 2 levels deep).
    $text = $text -replace '(?i)\S*references/([A-Za-z0-9_\-]+\.md)', '../../references/$1'
    # cs-code-query references its own sub-files via an absolute .codebuddy path.
    # Rewrite to a relative path so it resolves from within the skill directory
    # (skills/cs-code-query/, .gemini/skills/cs-code-query/, .agents/skills/cs-code-query/).
    $text = $text -replace '\.codebuddy/skills/code-query/', ''
    return $text
}

function Copy-Tree($src, $dst, [switch]$NeutralizeSkill, [switch]$RewriteRefs) {
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    $items = Get-ChildItem -Path $src -Recurse
    foreach ($item in $items) {
        $rel = $item.FullName.Substring($src.Length).TrimStart('\', '/')
        $target = Join-Path $dst $rel
        if ($item.PSIsContainer) { New-Item -ItemType Directory -Force -Path $target | Out-Null; continue }
        if ($item.Extension -eq '.md') {
            $c = Get-Content -Raw -Path $item.FullName
            if ($NeutralizeSkill -and ($item.Name -eq 'SKILL.md')) { $c = Neutralize-Frontmatter $c }
            if ($RewriteRefs) { $c = Fix-Refs $c }
            Set-Content -NoNewline -Path $target -Value $c -Encoding UTF8
        } else {
            Copy-Item -Path $item.FullName -Destination $target -Force
        }
    }
}

# ---------------------------------------------------------------------------
# 1. Skills  ->  skills/  +  .gemini/skills/  +  .agents/skills/
# ---------------------------------------------------------------------------
$skillDirs = Get-ChildItem -Path $SrcSkills -Directory | Where-Object { $ExcludeSkills -notcontains $_.Name }

$dstSkillsCanon = Join-Path $Repo 'skills'
$dstSkillsGem   = Join-Path $Repo '.gemini\skills'
$dstSkillsCodex = Join-Path $Repo '.agents\skills'
Clear-Dir $dstSkillsCanon; Clear-Dir $dstSkillsGem; Clear-Dir $dstSkillsCodex

foreach ($sd in $skillDirs) {
    Copy-Tree -src $sd.FullName -dst (Join-Path $dstSkillsCanon $sd.Name) -NeutralizeSkill -RewriteRefs
    Copy-Tree -src $sd.FullName -dst (Join-Path $dstSkillsGem   $sd.Name) -NeutralizeSkill -RewriteRefs
    Copy-Tree -src $sd.FullName -dst (Join-Path $dstSkillsCodex $sd.Name) -NeutralizeSkill -RewriteRefs
}
Write-Host "Skills: $($skillDirs.Count) -> skills/ .gemini/skills/ .agents/skills/"

# ---------------------------------------------------------------------------
# 2. References  ->  references/  +  .gemini/references/  +  .agents/references/
# ---------------------------------------------------------------------------
$dstRefsCanon = Join-Path $Repo 'references'
$dstRefsGem   = Join-Path $Repo '.gemini\references'
$dstRefsCodex = Join-Path $Repo '.agents\references'
Clear-Dir $dstRefsCanon; Clear-Dir $dstRefsGem; Clear-Dir $dstRefsCodex
foreach ($rf in (Get-ChildItem -Path $SrcRefs -File)) {
    foreach ($d in @($dstRefsCanon, $dstRefsGem, $dstRefsCodex)) {
        Copy-Item -Path $rf.FullName -Destination (Join-Path $d $rf.Name) -Force
    }
}
Write-Host "References: $((Get-ChildItem -Path $SrcRefs -File).Count) -> references/ .gemini/references/ .agents/references/"

# ---------------------------------------------------------------------------
# 3. Agents  ->  agents/  +  .gemini/agents/  +  .codex/agents/
# ---------------------------------------------------------------------------
$dstAgentsCanon = Join-Path $Repo 'agents'
$dstAgentsGem   = Join-Path $Repo '.gemini\agents'
$dstAgentsCodex = Join-Path $Repo '.codex\agents'
Clear-Dir $dstAgentsCanon; Clear-Dir $dstAgentsGem; Clear-Dir $dstAgentsCodex
foreach ($ag in (Get-ChildItem -Path $SrcAgents -File)) {
    foreach ($d in @($dstAgentsCanon, $dstAgentsGem, $dstAgentsCodex)) {
        Copy-Item -Path $ag.FullName -Destination (Join-Path $d $ag.Name) -Force
    }
}
Write-Host "Agents: $((Get-ChildItem -Path $SrcAgents -File).Count) -> agents/ .gemini/agents/ .codex/agents/"

# ---------------------------------------------------------------------------
# 4. Commands
#    canonical commands/*.md ; Gemini .gemini/commands/*.toml
#
#    Codex renders files in .codex/prompts/ in its slash-command menu. Those
#    entries must therefore use the actual skill names, not this pack's legacy
#    workflow aliases (build, plan, review, ...).
# ---------------------------------------------------------------------------
$dstCmdCanon = Join-Path $Repo 'commands'
$dstCmdGem   = Join-Path $Repo '.gemini\commands'
$dstCmdCodex = Join-Path $Repo '.codex\prompts'
Clear-Dir $dstCmdCanon; Clear-Dir $dstCmdGem; Clear-Dir $dstCmdCodex

foreach ($cmd in (Get-ChildItem -Path $SrcCommands -File -Filter *.md)) {
    $base = $cmd.BaseName
    # Canonical markdown copy
    Copy-Item -Path $cmd.FullName -Destination (Join-Path $dstCmdCanon "$base.md") -Force

    $raw = Get-Content -Raw -Path $cmd.FullName
    $desc = if ($raw -match '(?m)^description:\s*(.+?)\s*$') { $matches[1].Trim().Trim('"') } else { $base }
    $body = if ($raw -match '(?s)^---\s*\r?\n.*?\r?\n---\s*\r?\n(.*)$') { $matches[1] } else { $raw }

    # Gemini TOML command
    $descEsc = $desc.Replace('\', '\\').Replace('"', '\"')
    if ($body.Contains("'''")) {
        $promptStr = '"""' + ($body.Replace('\', '\\').Replace('"', '\"')) + '"""'
    } else {
        $promptStr = "'''$body'''"
    }
    $toml = "description = `"$descEsc`"`n`nprompt = $promptStr`n"
    Set-Content -NoNewline -Path (Join-Path $dstCmdGem "$base.toml") -Value $toml -Encoding UTF8

}
Write-Host "Commands: $((Get-ChildItem -Path $SrcCommands -File -Filter *.md).Count) -> commands/ .gemini/commands/"

# Codex slash commands are a thin launch surface for each auto-discovered
# skill. Keep the body deliberately small so SKILL.md remains the single source
# of truth for each workflow.
foreach ($sd in $skillDirs) {
    $definition = Join-Path $sd.FullName 'SKILL.md'
    if (-not (Test-Path $definition)) {
        Write-Warning "Skill definition missing, skipped Codex prompt: $definition"
        continue
    }

    $raw = Get-Content -Raw -Path $definition
    $skillName = if ($raw -match '(?m)^name:\s*(.+?)\s*$') { $matches[1].Trim().Trim('"') } else { $sd.Name }
    $skillDesc = if ($raw -match '(?m)^description:\s*(.+?)\s*$') { $matches[1].Trim().Trim('"') } else { $skillName }
    $skillDesc = $skillDesc.Replace('"', '\"')

    $codexPrompt = "---`ndescription: `"$skillDesc`"`nargument-hint: `"[args]`"`n---`n`nInvoke the $skillName skill and follow its workflow for: `$ARGUMENTS"
    Set-Content -NoNewline -Path (Join-Path $dstCmdCodex "$skillName.md") -Value $codexPrompt -Encoding UTF8
}
Write-Host "Codex prompts: $($skillDirs.Count) skill names -> .codex/prompts/"

Write-Host "`nDone. Adapter tree built under $Repo"
