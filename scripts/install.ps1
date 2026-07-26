<#
.SYNOPSIS
  Copies the platform-relevant files of the Agent-Skills pack to a target location.

.DESCRIPTION
  -Target codebuddy  -> install .codebuddy/ (skills/agents/commands/references/hooks + AGENTS.md/settings.json/CODEBUDDY.md)
  -Target gemini     -> install .gemini/ + GEMINI.md
  -Target codex      -> install .agents/ + .codex/ + AGENTS.md
  -Target all        -> all of the above

  By default -Destination is the current directory (a project root). Use -UserHome to install into
  the user's home config directory (~/.codebuddy, ~/.gemini, ~/.agents, ~/.codex).

  Install mode:
    -Merge (default)  Merge into the destination. Only the pack's own files/subdirs are written;
                      pre-existing destination files (e.g. graphify user skills) are preserved.
                      Safe for user-level config dirs.
    -Clean            Replace the destination completely (delete first). Use only for a fresh
                      project root or when you intentionally want to wipe the target.

  Example:
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install.ps1 -Target codebuddy -UserHome
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install.ps1 -Target all -Clean
#>

param(
    [ValidateSet('codex', 'codebuddy', 'gemini', 'all')]
    [string]$Target = 'all',
    [string]$Destination = '.',
    [switch]$UserHome,
    [switch]$Merge,
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'
$Repo = Resolve-Path (Join-Path $PSScriptRoot '..')

if ($UserHome) {
    $homeBase = $env:USERPROFILE
    $destCodebuddy = Join-Path $homeBase '.codebuddy'
    $destGemini    = Join-Path $homeBase '.gemini'
    $destCodex     = Join-Path $homeBase '.codex'
    $destAgents    = Join-Path $homeBase '.agents'
    $destRoot      = $homeBase
} else {
    $destCodebuddy = Join-Path $Destination '.codebuddy'
    $destGemini    = Join-Path $Destination '.gemini'
    $destCodex     = Join-Path $Destination '.codex'
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

# Resolve install mode. -Clean wins; otherwise -Merge (incl. default) merges.
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
# Gemini / Codex: generated platform dirs. Obey the selected mode (merge/clean).
if ($doGemini) {
    & $DirCopy (Join-Path $Repo '.gemini') $destGemini 'Gemini'
    Copy-File (Join-Path $Repo 'GEMINI.md') (Join-Path $destRoot 'GEMINI.md') 'GEMINI.md'
}
if ($doCodex) {
    & $DirCopy (Join-Path $Repo '.agents') $destAgents 'Codex skills'
    & $DirCopy (Join-Path $Repo '.codex')  $destCodex  'Codex prompts/agents'
    Copy-File (Join-Path $Repo 'AGENTS.md') (Join-Path $destRoot 'AGENTS.md') 'AGENTS.md'
}

Write-Host "`nDone."
