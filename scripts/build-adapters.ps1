<#
.SYNOPSIS
  Builds cross-platform adapters from the authoritative CodeBuddy source (.codebuddy/).

.DESCRIPTION
  The single source of truth is .codebuddy/ (skills, agents, commands, references).
  This script regenerates platform-neutral artifacts so the pack installs cleanly to
  Codex, CodeBuddy, Claude Code, and Gemini CLI:

    skills/             -> canonical neutral skills (name + description frontmatter only)
    agents/             -> canonical neutral personas
    references/         -> canonical checklists
    commands/           -> canonical slash commands (markdown)
    .gemini/            -> Gemini CLI adapter (skills + commands/*.toml + agents + GEMINI.md)
    .agents/            -> Codex skill adapter (.agents/skills/<name>/SKILL.md + agents/openai.yaml)
    .codex/             -> Codex adapter (prompts/ + agents/)
    .claude/            -> Claude Code adapter (skills/ + agents/ + commands/ + rules/)
    .claude-plugin/     -> Claude Code plugin manifest
    CLAUDE.md           -> Claude Code top-level project context (only if missing)

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

function Neutralize-AgentFrontmatter($content) {
    if ($content -match '(?s)^(---\r?\n)(.*?)(\r?\n---\r?\n)') {
        $open  = $matches[1]
        $fm    = $matches[2]
        $close = $matches[3]
        $body  = $content.Substring($matches[0].Length)
        $keep  = @()
        foreach ($l in ($fm -split "`r?`n")) {
            if ($l -match '^(thinkingLevel|agentMode|subagent|enabled|enabledAutoRun)\s*:') { continue }
            if ($l -match '^tools\s*:') { $l = $l -replace '(,\s*)?Task(,\s*)?', '' }
            $keep += $l
        }
        return $open + ($keep -join "`n") + $close + $body
    }
    return $content
}

# Filenames of the shared checklists under .codebuddy/references/. Only these
# are rewritten by Fix-Refs — skill-local references/ dirs (e.g.
# cs-huashu-design/references/) keep their relative paths untouched.
$PublicRefNames = @(Get-ChildItem -Path $SrcRefs -File | ForEach-Object { $_.Name })

function Fix-Refs($text, [string[]]$publicRefs) {
    # Normalize references to shared checklists to ../../references/<file> so they
    # resolve from every adapter tree (skills/<name>/, .gemini/skills/<name>/,
    # .agents/skills/<name>/, .claude/skills/<name>/, all 2 levels deep).
    # Whitelist by filename so references to a skill's own references/ folder
    # (e.g. cs-huashu-design/references/brand-asset-protocol.md) are left intact.
    foreach ($name in $publicRefs) {
        $esc = [regex]::Escape($name)
        $text = $text -replace "(?i)\S*references/$esc", "../../references/$name"
    }
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
            if ($RewriteRefs) { $c = Fix-Refs $c $PublicRefNames }
            Set-Content -NoNewline -Path $target -Value $c -Encoding UTF8
        } else {
            Copy-Item -Path $item.FullName -Destination $target -Force
        }
    }
}

# Map the canonical CodeBuddy model tier to each platform's native model IDs.
# The source skills use DeepSeek-V4-Pro/Flash as stable complexity markers;
# adapters must emit models understood by their own host runtime.
$PlatformModels = @{
    'claude' = @{
        'DeepSeek-V4-Pro' = 'opus'
        'DeepSeek-V4-Flash' = 'sonnet'
    }
    'codex' = @{
        'DeepSeek-V4-Pro' = 'gpt-5.6-sol'
        'DeepSeek-V4-Flash' = 'gpt-5.6-terra'
    }
    'gemini' = @{
        'DeepSeek-V4-Pro' = 'gemini-2.5-pro'
        'DeepSeek-V4-Flash' = 'gemini-2.5-flash'
    }
}

function Get-PlatformModel([string]$sourceModel, [string]$platform) {
    if (-not $PlatformModels.ContainsKey($platform)) {
        throw "Unsupported skill platform: $platform"
    }
    $models = $PlatformModels[$platform]
    if (-not $models.ContainsKey($sourceModel)) {
        throw "Unsupported canonical skill model: $sourceModel"
    }
    return $models[$sourceModel]
}

function Set-SkillPlatformModel([string]$path, [string]$platform) {
    $content = Get-Content -Raw -Path $path
    $sourceModel = if ($content -match '(?m)^model:\s*(.+?)\s*$') { $matches[1].Trim() } else { return }
    $targetModel = Get-PlatformModel $sourceModel $platform
    $content = $content -replace '(?m)^model:\s*.+?\s*$', "model: $targetModel"
    Set-Content -NoNewline -Path $path -Value $content -Encoding UTF8
}

function Set-AgentPlatformModel([string]$path, [string]$platform) {
    $content = Get-Content -Raw -Path $path
    $agentName = if ($content -match '(?m)^name:\s*(.+?)\s*$') { $matches[1].Trim() } else { throw "Agent name missing: $path" }
    $highReasoningAgents = @('cs-code-reviewer', 'cs-security-auditor')
    $isHighReasoning = $highReasoningAgents -contains $agentName
    $targetModel = switch ($platform) {
        'claude' { if ($isHighReasoning) { 'opus' } else { 'sonnet' } }
        'codex'  { if ($isHighReasoning) { 'gpt-5.6-sol' } else { 'gpt-5.6-terra' } }
        'gemini' { if ($isHighReasoning) { 'gemini-2.5-pro' } else { 'gemini-2.5-flash' } }
        default  { throw "Unsupported agent platform: $platform" }
    }
    $content = $content -replace '(?m)^model:\s*.+?\s*$', "model: $targetModel"
    Set-Content -NoNewline -Path $path -Value $content -Encoding UTF8
}

function Copy-AgentPlatform([string]$source, [string]$destination, [string]$platform) {
    $content = Get-Content -Raw -Path $source
    if ($platform -eq 'claude') { $content = Neutralize-AgentFrontmatter $content }
    Set-Content -NoNewline -Path $destination -Value $content -Encoding UTF8
    Set-AgentPlatformModel $destination $platform
}

# ---------------------------------------------------------------------------
# 1. Skills  ->  skills/  +  .gemini/skills/  +  .agents/skills/
# ---------------------------------------------------------------------------
$skillDirs = Get-ChildItem -Path $SrcSkills -Directory | Where-Object { $ExcludeSkills -notcontains $_.Name }

$dstSkillsCanon  = Join-Path $Repo 'skills'
$dstSkillsGem    = Join-Path $Repo '.gemini\skills'
$dstSkillsCodex  = Join-Path $Repo '.agents\skills'
$dstSkillsClaude = Join-Path $Repo '.claude\skills'
Clear-Dir $dstSkillsCanon; Clear-Dir $dstSkillsGem; Clear-Dir $dstSkillsCodex; Clear-Dir $dstSkillsClaude

foreach ($sd in $skillDirs) {
    Copy-Tree -src $sd.FullName -dst (Join-Path $dstSkillsCanon  $sd.Name) -NeutralizeSkill -RewriteRefs
    $geminiSkill = Join-Path $dstSkillsGem $sd.Name
    $codexSkill = Join-Path $dstSkillsCodex $sd.Name
    $claudeSkill = Join-Path $dstSkillsClaude $sd.Name
    Copy-Tree -src $sd.FullName -dst $geminiSkill -NeutralizeSkill -RewriteRefs
    Copy-Tree -src $sd.FullName -dst $codexSkill -NeutralizeSkill -RewriteRefs
    Copy-Tree -src $sd.FullName -dst $claudeSkill -NeutralizeSkill -RewriteRefs
    Set-SkillPlatformModel (Join-Path $geminiSkill 'SKILL.md') 'gemini'
    Set-SkillPlatformModel (Join-Path $codexSkill 'SKILL.md') 'codex'
    Set-SkillPlatformModel (Join-Path $claudeSkill 'SKILL.md') 'claude'
}
Write-Host "Skills: $($skillDirs.Count) -> skills/ .gemini/skills/ .agents/skills/ .claude/skills/"

# Title-case a hyphenated name, keeping known acronyms uppercase.
# e.g. "code-review" -> "Code Review",  "frontend-ui" -> "Frontend UI"
function ConvertTo-TitleCase([string]$name, [string[]]$acronyms) {
    $parts = $name -split '-'
    $result = @()
    foreach ($p in $parts) {
        $upper = $p.ToUpper()
        $match = $false
        foreach ($a in $acronyms) { if ($upper -eq $a) { $result += $a; $match = $true; break } }
        if (-not $match) { $result += $p.Substring(0,1).ToUpper() + $p.Substring(1).ToLower() }
    }
    return $result -join ' '
}

# ---------------------------------------------------------------------------
# 1b. Generate Codex UI metadata (agents/openai.yaml) per skill
#
# Codex CLI requires agents/openai.yaml in each skill directory to properly
# render the skill list UI (/ menu). Without this file, installed skills
# are invisible or display incorrectly.
# ---------------------------------------------------------------------------
$codexSkillDirs = Get-ChildItem -Path $dstSkillsCodex -Directory
$codexMetaCount = 0
foreach ($sd in $codexSkillDirs) {
    $skillMd = Join-Path $sd.FullName 'SKILL.md'
    if (-not (Test-Path $skillMd)) { continue }

    $raw = Get-Content -Raw -Path $skillMd -ErrorAction SilentlyContinue
    if (-not $raw) { continue }

    $skillName = if ($raw -match '(?m)^name:\s*(.+?)\s*$') { $matches[1].Trim().Trim('"') } else { $sd.Name }
    $desc     = if ($raw -match '(?m)^description:\s*(.+?)\s*$') { $matches[1].Trim().Trim('"') } else { '' }

    # Compute display_name: "cs-planning" -> "CS Planning"
    # Known acronyms kept uppercase (case-insensitive in skill name)
    $Acronyms = @('UI', 'CI', 'CD', 'API', 'TDD', 'ADR', 'ADRS', 'CICD', 'MCP', 'DOM', 'CSS')
    $displayName = $skillName
    if ($displayName -match '^cs-(.+)$') {
        $rest = $matches[1]
        $displayName = "CS " + (ConvertTo-TitleCase $rest $Acronyms)
    } else {
        $displayName = ConvertTo-TitleCase $displayName $Acronyms
    }

    # Compute short_description: extract the readable English portion.
    # Two valid source layouts:
    #   1) "English description. ...Use when... / 中文翻译。"      -> keep prefix before " / "
    #   2) "中文描述。English description. Use when..."           -> drop leading CJK segment
    $shortDesc = $desc.Trim()
    $cjkAfter = $shortDesc -match '/\s*(?:[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff])'
    if ($cjkAfter -and $shortDesc -match '^(.+?)\s+/\s+') {
        $shortDesc = $matches[1].Trim()
    } elseif ($shortDesc -match '^[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]') {
        # Chinese-first layout: drop text up to and including the first Chinese
        # sentence terminator (。 / ！ / ？), then keep the English tail.
        foreach ($terminator in @('。','！','？')) {
            $idx = $shortDesc.IndexOf($terminator)
            if ($idx -ge 0 -and ($idx + 1) -lt $shortDesc.Length) {
                $shortDesc = $shortDesc.Substring($idx + 1).TrimStart()
                break
            }
        }
    }
    if ($shortDesc.Length -eq 0) { $shortDesc = $displayName }
    # Truncate at first sentence boundary (period or newline), max ~120 chars
    if ($shortDesc -match '^(.{1,120}?)[\.\?\!]') { $shortDesc = $matches[1].Trim() + '.' }
    elseif ($shortDesc.Length -gt 150) {
        # Codex UI cards can typically render ~150 chars; truncate at a word
        # boundary rather than mid-word to keep the prompt readable.
        $trunc = $shortDesc.Substring(0, 147)
        $lastSpace = $trunc.LastIndexOf(' ')
        if ($lastSpace -gt 60) { $trunc = $trunc.Substring(0, $lastSpace) }
        $shortDesc = $trunc.TrimEnd(',;') + '.'
    }
    if ($shortDesc.Length -eq 0) { $shortDesc = $displayName }

    # Write agents/openai.yaml
    $agentDir = Join-Path $sd.FullName 'agents'
    if (-not (Test-Path $agentDir)) { New-Item -ItemType Directory -Force -Path $agentDir | Out-Null }

    $yaml = @"
interface:
  display_name: "$displayName"
  short_description: "$shortDesc"
"@
    Set-Content -NoNewline -Path (Join-Path $agentDir 'openai.yaml') -Value $yaml -Encoding UTF8
    $codexMetaCount++
}
Write-Host "Codex UI metadata: $codexMetaCount skills -> .agents/skills/*/agents/openai.yaml"

# ---------------------------------------------------------------------------
# 2. References  ->  references/  +  .gemini/references/  +  .agents/references/
# ---------------------------------------------------------------------------
$dstRefsCanon  = Join-Path $Repo 'references'
$dstRefsGem    = Join-Path $Repo '.gemini\references'
$dstRefsCodex  = Join-Path $Repo '.agents\references'
$dstRefsClaude = Join-Path $Repo '.claude\references'
Clear-Dir $dstRefsCanon; Clear-Dir $dstRefsGem; Clear-Dir $dstRefsCodex; Clear-Dir $dstRefsClaude
foreach ($rf in (Get-ChildItem -Path $SrcRefs -File)) {
    foreach ($d in @($dstRefsCanon, $dstRefsGem, $dstRefsCodex, $dstRefsClaude)) {
        Copy-Item -Path $rf.FullName -Destination (Join-Path $d $rf.Name) -Force
    }
}
Write-Host "References: $((Get-ChildItem -Path $SrcRefs -File).Count) -> references/ .gemini/references/ .agents/references/ .claude/references/"

# ---------------------------------------------------------------------------
# 3. Agents  ->  agents/  +  .gemini/agents/  +  .codex/agents/  +  .claude/agents/
# ---------------------------------------------------------------------------
$dstAgentsCanon = Join-Path $Repo 'agents'
$dstAgentsGem   = Join-Path $Repo '.gemini\agents'
$dstAgentsCodex = Join-Path $Repo '.codex\agents'
$dstAgentsClaude = Join-Path $Repo '.claude\agents'
foreach ($d in @($dstAgentsCanon, $dstAgentsGem, $dstAgentsCodex, $dstAgentsClaude)) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}
foreach ($ag in (Get-ChildItem -Path $SrcAgents -File)) {
    Copy-Item -Path $ag.FullName -Destination (Join-Path $dstAgentsCanon $ag.Name) -Force
    Copy-AgentPlatform $ag.FullName (Join-Path $dstAgentsGem $ag.Name) 'gemini'
    Copy-AgentPlatform $ag.FullName (Join-Path $dstAgentsCodex $ag.Name) 'codex'
    Copy-AgentPlatform $ag.FullName (Join-Path $dstAgentsClaude $ag.Name) 'claude'
}
Write-Host "Agents: $((Get-ChildItem -Path $SrcAgents -File).Count) -> agents/ .gemini/agents/ .codex/agents/ .claude/agents/"

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
Write-Host "Codex prompts: $($skillDirs.Count) skill names -> .codex/prompts/"

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
# ---------------------------------------------------------------------------
# 5. Claude Code adapter
#
# Claude Code reads project skills from `.claude/skills/<name>/SKILL.md`
# (generated in Section 1 alongside the other neutral trees), slash commands
# from `.claude/commands/`, project rules from `.claude/rules/`, and a
# top-level `CLAUDE.md` for project context. We also drop
# `.claude-plugin/plugin.json` + `marketplace.json` so the pack can be loaded
# as a plugin or a local marketplace.
#
# Slash command names mirror the upstream agent-skills short workflow names
# (build/spec/plan/review/test/ship/code-simplify/webperf) instead of the
# `cs-<skill>` names used for Codex / Gemini. Each command body still invokes
# the underlying `cs-<skill>` so the canonical skill is the single source of truth.
# ---------------------------------------------------------------------------
$dstCmdClaude = Join-Path $Repo '.claude\commands'
$dstRulesClaude = Join-Path $Repo '.claude\rules'
Clear-Dir $dstCmdClaude
Clear-Dir $dstRulesClaude

# 5a. Slash commands (one per legacy workflow file under commands/*.md).
# Strip CodeBuddy-only frontmatter fields (user-invocable/allowed-tools/agent/
# when_to_use/disable-model-invocation) which Claude Code does not recognize.
# Keep `description:` (and `argument-hint:`, which Claude Code supports).
$claudeCmdCount = 0
$claudeCmdNames = @{}
foreach ($cmd in (Get-ChildItem -Path $SrcCommands -File -Filter *.md)) {
    $base = $cmd.BaseName
    $raw = Get-Content -Raw -Path $cmd.FullName

    $clean = $raw
    if ($clean -match '(?s)^---\r?\n(.*?)\r?\n---\r?\n') {
        $fm = $matches[1]
        $body = $clean.Substring($matches[0].Length)
        $keep = @()
        foreach ($l in ($fm -split "`r?`n")) {
            if ($l -match '^(user-invocable|allowed-tools|agent|when_to_use|disable-model-invocation)\s*:') { continue }
            $keep += $l
        }
        $clean = '---' + "`n" + ($keep -join "`n") + "`n---" + "`n" + $body
    }

    Set-Content -NoNewline -Path (Join-Path $dstCmdClaude "$base.md") -Value $clean -Encoding UTF8
    $claudeCmdCount++
    $claudeCmdNames[$base] = $true
}

# 5a1. Detect `/command` references that have no matching file in
# .claude/commands/ (e.g. `/grill-me` in spec/plan/build) and generate a thin
# wrapper that routes to the underlying `cs-<name>` skill.
$missingRefs = [System.Collections.Generic.SortedSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($cmd in (Get-ChildItem -Path $SrcCommands -File -Filter *.md)) {
    $raw = Get-Content -Raw -Path $cmd.FullName
    foreach ($m in [regex]::Matches($raw, '/([A-Za-z][A-Za-z0-9\-]*)')) {
        $name = $m.Groups[1].Value.ToLower()
        if ($name -and -not $claudeCmdNames.ContainsKey($name)) { [void]$missingRefs.Add($name) }
    }
}
foreach ($name in $missingRefs) {
    $skillMd = Join-Path $SrcSkills "cs-$name\SKILL.md"
    if (-not (Test-Path $skillMd)) { continue }
    $skillRaw = Get-Content -Raw -Path $skillMd
    $desc = if ($skillRaw -match '(?m)^description:\s*(.+?)\s*$') { $matches[1].Trim().Trim('"') } else { $name }
    $wrapper = "---`ndescription: `"$desc`"`n---`n`nInvoke the ``cs-$name`` skill and follow its workflow.`n"
    Set-Content -NoNewline -Path (Join-Path $dstCmdClaude "$name.md") -Value $wrapper -Encoding UTF8
    $claudeCmdCount++
}
Write-Host "Claude commands: $claudeCmdCount -> .claude/commands/"

# 5b. Project rule against skill duplication (mirrors .claude/rules in upstream
# agent-skills so Claude Code surfaces the CONTRIBUTING.md pre-flight check).
$ruleBody = @'
---
description: Anti-duplication guardrail for adding or changing skills
paths:
  - "skills/**"
  - ".codebuddy/skills/**"
---

# Adding or changing a skill

This pack already covers most of the development lifecycle, so most new-skill ideas overlap an existing skill or an open skill catalog. Before creating a new `skills/<name>/` (or `.codebuddy/skills/<name>/`) directory or significantly reworking an existing one:

- Search the existing catalog under `.codebuddy/skills/` and `skills/` for an overlap.
- Justify the gap in one line (what lifecycle phase is missing, and which skill is the closest neighbor).
- Follow the frontmatter / body anatomy used by the other skills (name + description in frontmatter; Overview / When to Use / Process / Red Flags / Verification in body).
- Prefer extending an existing skill over adding a near-duplicate.

`CLAUDE.md` (Claude Code), `AGENTS.md` (Codex / CodeBuddy router) and `GEMINI.md` (Gemini CLI router) are the single source of truth for the skill catalog — do not duplicate their content here, link to them.
'@
Set-Content -NoNewline -Path (Join-Path $dstRulesClaude 'skills-contributing.md') -Value $ruleBody -Encoding UTF8
Write-Host "Claude rules: 1 -> .claude/rules/skills-contributing.md"

# 5c. Claude plugin package. A plugin discovers `skills/` and `agents/` from
# its own root, so it must use a dedicated Claude-adapted tree rather than the
# platform-neutral top-level `skills/` and `agents/` directories.
$dstClaudePluginPackage = Join-Path $Repo 'plugins\claude'
Clear-Dir $dstClaudePluginPackage
Copy-Tree -src $dstSkillsClaude -dst (Join-Path $dstClaudePluginPackage 'skills')
Copy-Tree -src $dstAgentsClaude -dst (Join-Path $dstClaudePluginPackage 'agents')
Copy-Tree -src $dstCmdClaude -dst (Join-Path $dstClaudePluginPackage 'commands')
Copy-Tree -src $dstRulesClaude -dst (Join-Path $dstClaudePluginPackage 'rules')
$dstClaudePluginMeta = Join-Path $dstClaudePluginPackage '.claude-plugin'
New-Item -ItemType Directory -Force -Path $dstClaudePluginMeta | Out-Null
$pluginJson = @'
{
  "name": "agent-skills-cs",
  "version": "1.0.0",
  "description": "Production-grade engineering workflow skills (cs-*) for Claude Code, sourced from .codebuddy/.",
  "author": { "name": "agent-skills" }
}
'@
Set-Content -NoNewline -Path (Join-Path $dstClaudePluginMeta 'plugin.json') -Value $pluginJson -Encoding UTF8

# The root marketplace selects the dedicated package. Remove the old root
# plugin manifest so a direct install cannot accidentally discover neutral
# DeepSeek-configured artifacts.
$pluginDir = Join-Path $Repo '.claude-plugin'
if (-not (Test-Path $pluginDir)) { New-Item -ItemType Directory -Force -Path $pluginDir | Out-Null }
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $pluginDir 'plugin.json')

# Marketplace manifest so the pack can also be added as a local plugin
# marketplace: `claude plugin marketplace add <path>` then install from it.
$marketplaceJson = @'
{
  "name": "agent-skills-cs",
  "owner": { "name": "agent-skills" },
  "plugins": [
    { "source": "./plugins/claude" }
  ]
}
'@
Set-Content -NoNewline -Path (Join-Path $pluginDir 'marketplace.json') -Value $marketplaceJson -Encoding UTF8
Write-Host "Claude plugin package: 1 -> plugins/claude; marketplace: 1 -> .claude-plugin/marketplace.json"

# 5d. CLAUDE.md (top-level Claude project context). Generated only when no
# user-owned CLAUDE.md already exists at the repo root — that file is the
# user's own persistent context and we must not clobber it on rebuild.
$dstClaudeMd = Join-Path $Repo 'CLAUDE.md'
if (-not (Test-Path $dstClaudeMd)) {
    $claudeMdBody = @'
# Agent-Skills for Claude Code

This is the **agent-skills** pack — production-grade engineering workflow skills for Claude Code, ported from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (MIT).

## Skills

Skills are discovered from `.claude/skills/<name>/SKILL.md` (project) and `~/.claude/skills/<name>/SKILL.md` (personal) — 29 skills, all `cs-` prefixed. Claude auto-invokes a skill when its `description` matches the task; you can also type the skill name directly to call it. The slash command shortcuts in `.claude/commands/` cover the main workflows.

## Router

`AGENTS.md` at the repo root is the universal router (also used by Codex / CodeBuddy / Gemini CLI). Read it to map an inbound task to the right skill.

## Conventions

- One `cs-<name>` per lifecycle phase; do not duplicate phases across skills.
- Every skill follows the same anatomy — frontmatter (`name`, `description`) + body (`Overview`, `When to Use`, `Process`, `Common Rationalizations`, `Red Flags`, `Verification`).
- Cross-reference other skills instead of paraphrasing their content.
'@
    Set-Content -NoNewline -Path $dstClaudeMd -Value $claudeMdBody -Encoding UTF8
    Write-Host "Claude project context: 1 -> CLAUDE.md (created)"
} else {
    Write-Host "Claude project context: existing CLAUDE.md preserved"
}

Write-Host "`nDone. Adapter tree built under $Repo"
