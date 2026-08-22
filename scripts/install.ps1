<#
.SYNOPSIS
  Copies the platform-relevant files of the Agent-Skills pack to a target location.

.DESCRIPTION
  -Target codebuddy  -> install .codebuddy/ (skills/agents/commands/references/hooks + AGENTS.md/settings.json/CODEBUDDY.md)
  -Target gemini     -> install .gemini/ + GEMINI.md
  -Target codex      -> install project adapters, or register skills under ~/.codex/skills
  -Target claude     -> install .claude/ + canonical skills/ + CLAUDE.md, or register skills under ~/.claude/skills
  -Target all        -> all of the above

  By default -Destination is the current directory (a project root). Use -UserHome to install into
  the user's home config directory (~/.codebuddy, ~/.gemini, ~/.codex, ~/.claude).

  Install mode:
    -Merge (default)  Merge into the destination. Only the pack's own files/subdirs are written;
                      pre-existing destination files (e.g. graphify user skills) are preserved.
                      Safe for user-level config dirs.
    -Clean            Replace generated platform directories for project installs. It is
                      intentionally downgraded to a safe merge for user-level installs.

  Example:
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install.ps1 -Target codebuddy -UserHome
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install.ps1 -Target all -Clean
#>

param(
    [ValidateSet('codex', 'codebuddy', 'gemini', 'claude', 'all')]
    [string]$Target = 'all',
    [string]$Destination = '.',
    [switch]$UserHome,
    [string]$UserHomePath,
    [switch]$Merge,
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'
$Repo = Resolve-Path (Join-Path $PSScriptRoot '..')

if ($UserHome) {
    $homeBase = if ($UserHomePath) { [System.IO.Path]::GetFullPath($UserHomePath) } elseif ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
    $destCodebuddy = Join-Path $homeBase '.codebuddy'
    $destGemini    = Join-Path $homeBase '.gemini'
    $destCodex     = Join-Path $homeBase '.codex'
    $destClaude    = Join-Path $homeBase '.claude'
    $destRoot      = $homeBase
} else {
    $destCodebuddy = Join-Path $Destination '.codebuddy'
    $destGemini    = Join-Path $Destination '.gemini'
    $destCodex     = Join-Path $Destination '.codex'
    $destClaude    = Join-Path $Destination '.claude'
    $destAgents    = Join-Path $Destination '.agents'
    $destRoot      = $Destination
}

<#
 .SYNOPSIS
  Merge-copy a source directory into a destination directory.

 .DESCRIPTION
  Only the source's own children (subdirs + files) are copied into the
  destination. Existing destination files NOT in the source are preserved.
  This avoids wiping user-installed skills (e.g. graphify) when installing
  to a user-level config dir like ~/.codebuddy.
#>
function Merge-Platform($src, $dst, [string]$label) {
    if (-not (Test-Path $src)) { Write-Warning "Source missing, skipped: $src"; return }
    if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Force -Path $dst | Out-Null }
    Copy-Item -Recurse -Force -Path (Join-Path $src '*') -Destination $dst
    Write-Host "Merged $label -> $dst"
}

<#
 .SYNOPSIS
  Replace a destination directory completely (delete first, then copy).

 .DESCRIPTION
  Only use this for a fresh project root or when you intentionally want to
  wipe the target. Never use on a user-level config dir that holds other
  skills (e.g. ~/.codebuddy with graphify installed).
#>
function Replace-Platform($src, $dst, [string]$label) {
    if (-not (Test-Path $src)) { Write-Warning "Source missing, skipped: $src"; return }
    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
    Copy-Item -Recurse -Force -Path $src -Destination $dst
    Write-Host "Replaced $label -> $dst"
}

function Copy-File($src, $dst, [string]$label) {
    if (-not (Test-Path $src)) { Write-Warning "Source missing, skipped: $src"; return }
    if (-not (Test-Path (Split-Path $dst))) { New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null }
    Copy-Item -Force -Path $src -Destination $dst
    Write-Host "Installed $label -> $dst"
}

function Get-Sha256($path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
}

function Read-CodexManifest($path) {
    $known = @{}
    if (-not (Test-Path $path)) { return $known }

    try {
        $manifest = Get-Content -Raw -Path $path | ConvertFrom-Json
        foreach ($entry in @($manifest.files)) {
            if ($entry.path -and $entry.sha256) { $known[$entry.path] = $entry.sha256 }
        }
    } catch {
        Write-Warning "Ignoring unreadable Codex install manifest: $path"
    }
    return $known
}

function Install-CodexUserFile($src, $dst, [string]$key, $known, $next) {
    $sourceHash = Get-Sha256 $src
    $install = -not (Test-Path -LiteralPath $dst)

    if (-not $install) {
        $destinationHash = Get-Sha256 $dst
        $install = ($destinationHash -eq $sourceHash) -or
            ($known.ContainsKey($key) -and $known[$key] -eq $destinationHash)

        if (-not $install) {
            Write-Warning "Skipped existing user file (not owned by this pack): $dst"
            return
        }
    }

    $parent = Split-Path -Parent $dst
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Copy-Item -Force -LiteralPath $src -Destination $dst
    $next[$key] = $sourceHash
}

function Install-CodexUserTree($src, $dst, [string]$prefix, $known, $next) {
    if (-not (Test-Path $src)) { Write-Warning "Source missing, skipped: $src"; return }

    foreach ($file in (Get-ChildItem -Path $src -File -Recurse)) {
        $relativePath = $file.FullName.Substring($src.Length).TrimStart('\', '/')
        $key = ($prefix + '/' + $relativePath).Replace('\', '/')
        Install-CodexUserFile $file.FullName (Join-Path $dst $relativePath) $key $known $next
    }
}

function Install-CodexUserSkills($src, $dst, $known, $next) {
    if (-not (Test-Path $src)) { Write-Warning "Source missing, skipped: $src"; return }

    foreach ($skill in (Get-ChildItem -Path $src -Directory)) {
        $key = ('skills/' + $skill.Name + '/SKILL.md')
        $sourceDefinition = Join-Path $skill.FullName 'SKILL.md'
        $destinationDefinition = Join-Path (Join-Path $dst $skill.Name) 'SKILL.md'

        # A skill directory is a single ownership unit. Do not blend the pack's
        # auxiliary files into a user-maintained skill with the same name.
        if ((Test-Path -LiteralPath $destinationDefinition) -and
            ((Get-Sha256 $sourceDefinition) -ne (Get-Sha256 $destinationDefinition)) -and
            (-not ($known.ContainsKey($key) -and $known[$key] -eq (Get-Sha256 $destinationDefinition)))) {
            Write-Warning "Skipped existing user skill (not owned by this pack): $($skill.Name)"
            continue
        }

        Install-CodexUserTree $skill.FullName (Join-Path $dst $skill.Name) ('skills/' + $skill.Name) $known $next
    }
}

function Write-CodexManifest($path, $files) {
    $entries = foreach ($key in ($files.Keys | Sort-Object)) {
        [ordered]@{ path = $key; sha256 = $files[$key] }
    }
    $manifest = [ordered]@{ version = 1; files = @($entries) }
    Set-Content -Path $path -Value ($manifest | ConvertTo-Json -Depth 3) -Encoding UTF8
}

# Resolve install mode. -Clean wins; otherwise -Merge (incl. default) merges.
if ($Clean -and $UserHome) {
    Write-Warning '-Clean is disabled for user-level installs to preserve existing skills and configuration.'
    $Clean = $false
}

if ($Clean) {
    $mode = 'Replace'
    $DirCopy = ${function:Replace-Platform}
} else {
    $mode = 'Merge'
    $DirCopy = ${function:Merge-Platform}
}
Write-Host "Install mode: $mode"

$doCodebuddy = ($Target -eq 'codebuddy') -or ($Target -eq 'all')
$doGemini    = ($Target -eq 'gemini')    -or ($Target -eq 'all')
$doCodex     = ($Target -eq 'codex')     -or ($Target -eq 'all')
$doClaude    = ($Target -eq 'claude')    -or ($Target -eq 'all')

# CodeBuddy: skills/agents/commands/references/hooks + AGENTS.md/settings.json/CODEBUDDY.md.
# CodeBuddy skills live in a single flat namespace, so we always MERGE its
# subdirs (even in -Clean mode) to avoid wiping co-located user skills like
# graphify. -Clean only governs the generated platform dirs (.gemini/.codex).
if ($doCodebuddy) {
    foreach ($d in @('skills', 'agents', 'commands', 'references', 'hooks')) {
        $s = Join-Path $Repo (Join-Path '.codebuddy' $d)
        if (Test-Path $s) { Merge-Platform $s (Join-Path $destCodebuddy $d) "CodeBuddy/$d" }
    }
    Copy-File (Join-Path $Repo '.codebuddy\AGENTS.md')      (Join-Path $destCodebuddy 'AGENTS.md')      'CodeBuddy/AGENTS.md'
    Copy-File (Join-Path $Repo '.codebuddy\settings.json')  (Join-Path $destCodebuddy 'settings.json')  'CodeBuddy/settings.json'
    Copy-File (Join-Path $Repo '.codebuddy\CODEBUDDY.md')   (Join-Path $destCodebuddy 'CODEBUDDY.md')   'CodeBuddy/CODEBUDDY.md'
}
# Gemini: generated platform dir. Obey the selected mode (merge/clean).
if ($doGemini) {
    & $DirCopy (Join-Path $Repo '.gemini') $destGemini 'Gemini'
    Copy-File (Join-Path $Repo 'GEMINI.md') (Join-Path $destRoot 'GEMINI.md') 'GEMINI.md'
}
if ($doCodex) {
    if ($UserHome) {
        # Codex discovers global skills from ~/.codex/skills, not ~/.agents/skills.
        # Keep a manifest so pack updates never overwrite an unrelated or edited file.
        $manifestPath = Join-Path $destCodex '.agent-skills-manifest.json'
        $known = Read-CodexManifest $manifestPath
        $next = @{}
        Install-CodexUserSkills (Join-Path $Repo '.agents\skills') (Join-Path $destCodex 'skills') $known $next
        Install-CodexUserTree (Join-Path $Repo '.agents\references') (Join-Path $destCodex 'references') 'references' $known $next
        Install-CodexUserTree (Join-Path $Repo '.codex\prompts') (Join-Path $destCodex 'prompts') 'prompts' $known $next
        Install-CodexUserTree (Join-Path $Repo '.codex\agents') (Join-Path $destCodex 'agents') 'agents' $known $next
        Install-CodexUserFile (Join-Path $Repo 'AGENTS.md') (Join-Path $destCodex 'AGENTS.md') 'AGENTS.md' $known $next
        Write-CodexManifest $manifestPath $next
        Write-Host "Installed Codex user-level adapters -> $destCodex"
    } else {
        & $DirCopy (Join-Path $Repo '.agents') $destAgents 'Codex skills'
        & $DirCopy (Join-Path $Repo '.codex')  $destCodex  'Codex prompts/agents'
        Copy-File (Join-Path $Repo 'AGENTS.md') (Join-Path $destRoot 'AGENTS.md') 'AGENTS.md'
    }
}

# Claude Code: project-level uses `.claude/skills/` (Claude auto-discovers
# skills there), `.claude/commands/` + `.claude/rules/`, optional
# `.claude-plugin/` for plugin/marketplace discovery, and `CLAUDE.md` for
# top-level context. User-level installs mirror content into
# `~/.claude/skills/`, `~/.claude/commands/`, etc., with the same
# manifest-protection pattern used for Codex to avoid clobbering user-edited
# skill files.
if ($doClaude) {
    $manifestPath = if ($UserHome) { Join-Path $destClaude '.agent-skills-manifest.json' } else { $null }

    if ($UserHome) {
        $known = if ($manifestPath) { Read-CodexManifest $manifestPath } else { @{} }
        $next = @{}
        # Skills: copy each full `skills/<name>/` tree (SKILL.md plus its
        # references/, assets/, scripts/ etc.) to ~/.claude/skills/<name>/.
        # Reuses the manifest-protected skill-tree installer shared with Codex.
        $srcSkillsCanon = Join-Path $Repo 'skills'
        if (Test-Path $srcSkillsCanon) {
            $destClaudeSkills = Join-Path $destClaude 'skills'
            if (-not (Test-Path $destClaudeSkills)) { New-Item -ItemType Directory -Force -Path $destClaudeSkills | Out-Null }
            Install-CodexUserSkills $srcSkillsCanon $destClaudeSkills $known $next
        }
        # Slash commands: ~/.claude/commands/<name>.md
        Install-CodexUserTree (Join-Path $Repo '.claude\commands') (Join-Path $destClaude 'commands') 'commands' $known $next
        # Rules: ~/.claude/rules/<name>.md
        Install-CodexUserTree (Join-Path $Repo '.claude\rules') (Join-Path $destClaude 'rules') 'rules' $known $next
        # CLAUDE.md (only write if missing — never overwrite user-owned content).
        $claudeMdSrc = Join-Path $Repo 'CLAUDE.md'
        if (Test-Path $claudeMdSrc) { Install-CodexUserFile $claudeMdSrc (Join-Path $destClaude 'CLAUDE.md') 'CLAUDE.md' $known $next }
        Write-CodexManifest $manifestPath $next
        Write-Host "Installed Claude user-level adapters -> $destClaude"
    } else {
        # Project-level install: copy .claude/ (skills, commands, rules),
        # the plugin manifest, and the top-level CLAUDE.md. We use the same
        # merge-by-default behavior as CodeBuddy so co-located user skills
        # in `.claude/skills/` (e.g. team-internal) are not wiped on update.
        if (Test-Path (Join-Path $Repo '.claude')) { Merge-Platform (Join-Path $Repo '.claude') $destClaude 'Claude' }
        $pluginDir = Join-Path $Repo '.claude-plugin'
        if (Test-Path $pluginDir) { & $DirCopy $pluginDir (Join-Path $destRoot '.claude-plugin') 'Claude plugin manifest' }
        Copy-File (Join-Path $Repo 'CLAUDE.md') (Join-Path $destRoot 'CLAUDE.md') 'CLAUDE.md'
    }
}

Write-Host "`nDone."
