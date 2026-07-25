<#
.SYNOPSIS
  Copies the platform-relevant files of the Agent-Skills pack to a target location.

.DESCRIPTION
  -Target codebuddy  -> copies .codebuddy/
  -Target gemini     -> copies .gemini/ + GEMINI.md
  -Target codex      -> copies .agents/ + .codex/ + AGENTS.md
  -Target all        -> all of the above

  By default -Destination is the current directory (a project root). Use -Home to install into
  the user's home config directory (~/.codebuddy, ~/.gemini, ~/.agents, ~/.codex).

  Example:
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/install.ps1 -Target all -Home
#>

param(
    [ValidateSet('codex', 'codebuddy', 'gemini', 'all')]
    [string]$Target = 'all',
    [string]$Destination = '.',
    [switch]$UserHome
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

function Copy-Platform($src, $dst, [string]$label) {
    if (-not (Test-Path $src)) { Write-Warning "Source missing, skipped: $src"; return }
    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
    Copy-Item -Recurse -Force -Path $src -Destination $dst
    Write-Host "Installed $label -> $dst"
}

function Copy-File($src, $dst, [string]$label) {
    if (-not (Test-Path $src)) { Write-Warning "Source missing, skipped: $src"; return }
    Copy-Item -Force -Path $src -Destination $dst
    Write-Host "Installed $label -> $dst"
}

$doCodebuddy = ($Target -eq 'codebuddy') -or ($Target -eq 'all')
$doGemini    = ($Target -eq 'gemini')    -or ($Target -eq 'all')
$doCodex     = ($Target -eq 'codex')     -or ($Target -eq 'all')

if ($doCodebuddy) { Copy-Platform (Join-Path $Repo '.codebuddy') $destCodebuddy 'CodeBuddy' }
if ($doGemini) {
    Copy-Platform (Join-Path $Repo '.gemini') $destGemini 'Gemini'
    Copy-File     (Join-Path $Repo 'GEMINI.md') (Join-Path $destRoot 'GEMINI.md') 'GEMINI.md'
}
if ($doCodex) {
    Copy-Platform (Join-Path $Repo '.agents') $destAgents 'Codex skills'
    Copy-Platform (Join-Path $Repo '.codex')  $destCodex  'Codex prompts/agents'
    Copy-File     (Join-Path $Repo 'AGENTS.md') (Join-Path $destRoot 'AGENTS.md') 'AGENTS.md'
}

Write-Host "`nDone."
