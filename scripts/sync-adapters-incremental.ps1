<#
.SYNOPSIS
  Additive adapter sync from the authoritative CodeBuddy source (.codebuddy/).

.DESCRIPTION
  Same skill transforms as build-adapters.ps1 (frontmatter neutralization, shared
  reference rewriting, Codex UI metadata, Codex prompts), but WITHOUT clearing the
  destination trees first. Use when the safe-delete bulk guard blocks a full
  rebuild, or when only additions/edits need to propagate. Removed skills are NOT
  cleaned up by this script — run the full build for that when the guard allows.

  Run:  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-adapters-incremental.ps1
#>

$ErrorActionPreference = 'Stop'
$Repo = Resolve-Path (Join-Path $PSScriptRoot '..')
$SrcSkills = Join-Path $Repo '.codebuddy\skills'
$SrcRefs   = Join-Path $Repo '.codebuddy\references'

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
function Write-TextFile($path, $content) {
    $full = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($path)
    [System.IO.File]::WriteAllText($full, $content, $Utf8NoBom)
}

function Neutralize-Frontmatter($content) {
    if ($content -match '(?s)^(---\r?\n)(.*?)(\r?\n---\r?\n)') {
        $open  = $matches[1]
        $fm    = $matches[2]
        $close = $matches[3]
        $body  = $content.Substring($matches[0].Length)
        $keep  = @()
        foreach ($l in ($fm -split "`r?`n")) {
            if ($l -match '^(argument-hint|user-invocable|allowed-tools|agent|model)\s*:') { continue }
            $keep += $l
        }
        return $open + ($keep -join "`n") + $close + $body
    }
    return $content
}

$PublicRefNames = @(Get-ChildItem -Path $SrcRefs -File | ForEach-Object { $_.Name })

function Fix-Refs($text, [string[]]$publicRefs) {
    foreach ($name in $publicRefs) {
        $esc = [regex]::Escape($name)
        $refPattern = '(?i)[^\s`\[\]()<>]*references/' + $esc
        $text = $text -replace $refPattern, "../../references/$name"
    }
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
            if ($RewriteRefs) { $c = Fix-Refs $c $PublicRefNames }
            Write-TextFile $target $c
        } else {
            Copy-Item -Path $item.FullName -Destination $target -Force
        }
    }
}

function ConvertTo-TitleCase([string]$name, [string[]]$acronyms) {
    $parts = $name -split '-'
    $result = @()
    foreach ($p in $parts) {
        $upper = $p.ToUpper()
        $match = $false
        foreach ($a in $acronyms) {
            if ($upper -eq $a) { $result += $a; $match = $true; break }
        }
        if (-not $match) { $result += $p.Substring(0,1).ToUpper() + $p.Substring(1).ToLower() }
    }
    return $result -join ' '
}

# ---------------------------------------------------------------------------
# 1. Skills -> skills/ + .gemini/skills/ + .agents/skills/ + .claude/skills/
# ---------------------------------------------------------------------------
$skillDirs = Get-ChildItem -Path $SrcSkills -Directory
foreach ($sd in $skillDirs) {
    foreach ($tree in @('skills', '.gemini\skills', '.agents\skills', '.claude\skills')) {
        Copy-Tree -src $sd.FullName -dst (Join-Path $Repo (Join-Path $tree $sd.Name)) -NeutralizeSkill -RewriteRefs
    }
}
Write-Host "Skills: $($skillDirs.Count) -> skills/ .gemini/skills/ .agents/skills/ .claude/skills/ (additive)"

# ---------------------------------------------------------------------------
# 1b. Codex UI metadata (agents/openai.yaml) per skill
# ---------------------------------------------------------------------------
$codexSkillDirs = Get-ChildItem -Path (Join-Path $Repo '.agents\skills') -Directory
$codexMetaCount = 0
foreach ($sd in $codexSkillDirs) {
    $skillMd = Join-Path $sd.FullName 'SKILL.md'
    if (-not (Test-Path $skillMd)) { continue }
    $raw = Get-Content -Raw -Path $skillMd -ErrorAction SilentlyContinue
    if (-not $raw) { continue }
    $skillName = if ($raw -match '(?m)^name:\s*(.+?)\s*$') { $matches[1].Trim().Trim('"') } else { $sd.Name }
    $desc     = if ($raw -match '(?m)^description:\s*(.+?)\s*$') { $matches[1].Trim().Trim('"') } else { '' }
    $Acronyms = @('UI', 'CI', 'CD', 'API', 'TDD', 'ADR', 'ADRS', 'CICD', 'MCP', 'DOM', 'CSS')
    $displayName = $skillName
    if ($displayName -match '^cs-(.+)$') {
        $rest = $matches[1]
        $displayName = "CS " + (ConvertTo-TitleCase $rest $Acronyms)
    } else {
        $displayName = ConvertTo-TitleCase $displayName $Acronyms
    }
    $shortDesc = $desc.Trim()
    $cjkAfter = $shortDesc -match '/\s*(?:[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff])'
    if ($cjkAfter -and $shortDesc -match '^(.+?)\s+/\s+') {
        $shortDesc = $matches[1].Trim()
    } elseif ($shortDesc -match '^[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]') {
        foreach ($terminator in @('。','！','？')) {
            $idx = $shortDesc.IndexOf($terminator)
            if ($idx -ge 0 -and ($idx + 1) -lt $shortDesc.Length) {
                $shortDesc = $shortDesc.Substring($idx + 1).TrimStart()
                break
            }
        }
    }
    if ($shortDesc.Length -eq 0) { $shortDesc = $displayName }
    if ($shortDesc -match '^(.{1,120}?)[\.\?\!]') { $shortDesc = $matches[1].Trim() + '.' }
    elseif ($shortDesc.Length -gt 150) {
        $trunc = $shortDesc.Substring(0, 147)
        $lastSpace = $trunc.LastIndexOf(' ')
        if ($lastSpace -gt 60) { $trunc = $trunc.Substring(0, $lastSpace) }
        $shortDesc = $trunc.TrimEnd(',;') + '.'
    }
    if ($shortDesc.Length -eq 0) { $shortDesc = $displayName }
    $agentDir = Join-Path $sd.FullName 'agents'
    if (-not (Test-Path $agentDir)) { New-Item -ItemType Directory -Force -Path $agentDir | Out-Null }
    $yaml = @"
interface:
  display_name: "$displayName"
  short_description: "$shortDesc"
"@
    if ($raw -match '(?m)^disable-model-invocation:\s*true\s*$') {
        $yaml += "`npolicy:`n  allow_implicit_invocation: false"
    }
    Write-TextFile (Join-Path $agentDir 'openai.yaml') $yaml
    $codexMetaCount++
}
Write-Host "Codex UI metadata: $codexMetaCount skills -> .agents/skills/*/agents/openai.yaml"

# ---------------------------------------------------------------------------
# 2. Claude plugin package skills (mirror of the .claude/skills tree)
# ---------------------------------------------------------------------------
$dstClaudePluginSkills = Join-Path $Repo 'plugins\claude\skills'
New-Item -ItemType Directory -Force -Path $dstClaudePluginSkills | Out-Null
foreach ($sd in $skillDirs) {
    Copy-Tree -src (Join-Path $Repo (Join-Path '.claude\skills' $sd.Name)) `
              -dst (Join-Path $dstClaudePluginSkills $sd.Name)
}
Write-Host "Claude plugin skills: $($skillDirs.Count) -> plugins/claude/skills/ (additive)"

# ---------------------------------------------------------------------------
# 3. Codex prompts (thin launch surface per skill)
# ---------------------------------------------------------------------------
$dstCmdCodex = Join-Path $Repo '.codex\prompts'
New-Item -ItemType Directory -Force -Path $dstCmdCodex | Out-Null
foreach ($sd in $skillDirs) {
    $definition = Join-Path $sd.FullName 'SKILL.md'
    if (-not (Test-Path $definition)) { continue }
    $raw = Get-Content -Raw -Path $definition
    $skillName = if ($raw -match '(?m)^name:\s*(.+?)\s*$') { $matches[1].Trim().Trim('"') } else { $sd.Name }
    $skillDesc = if ($raw -match '(?m)^description:\s*(.+?)\s*$') { $matches[1].Trim().Trim('"') } else { $skillName }
    $skillDesc = $skillDesc.Replace('"', '\"')
    $codexPrompt = "---`ndescription: `"$skillDesc`"`nargument-hint: `"[args]`"`n---`n`nInvoke the $skillName skill and follow its workflow for: `$ARGUMENTS"
    Write-TextFile (Join-Path $dstCmdCodex "$skillName.md") $codexPrompt
}
Write-Host "Codex prompts: $($skillDirs.Count) -> .codex/prompts/ (additive)"

Write-Host "`nDone. Incremental adapter sync complete under $Repo"