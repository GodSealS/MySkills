# Private agent bundles are byte-for-byte resources, never persona/skill adapters.
function Assert-ResourcePathNoLink([string]$Path, [string]$StopAt) {
    $trim = [char[]]@('\', '/')
    $cursor = [IO.Path]::GetFullPath($Path)
    $stop = if ($StopAt) { [IO.Path]::GetFullPath($StopAt).TrimEnd($trim) } else { '' }
    while ($cursor) {
        $item = Get-Item -LiteralPath $cursor -Force -ErrorAction SilentlyContinue
        if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Resource ownership path contains a link: $cursor" }
        # Only the destination tree is owned here; ancestors may be links.
        if ($stop -and [string]::Compare($cursor.TrimEnd($trim), $stop, [StringComparison]::OrdinalIgnoreCase) -eq 0) { break }
        $cursor = Split-Path -Parent $cursor
    }
}

function Sync-AgentResources([string]$Source, [string]$Destination) {
    if (-not (Test-Path -LiteralPath $Source)) { return }
    $root = [IO.Path]::GetFullPath($Destination).TrimEnd('\', '/')
    $manifestPath = Join-Path $root '.agent-resources-manifest'
    Assert-ResourcePathNoLink -Path $manifestPath -StopAt $root
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    $known = @{}
    if (Test-Path -LiteralPath $manifestPath) {
        foreach ($line in (Get-Content -LiteralPath $manifestPath)) {
            if ($line -match '^([a-fA-F0-9]{64}) (.+)$') { $known[$matches[2]] = $matches[1] }
        }
    }
    $current = @{}
    foreach ($bundle in (Get-ChildItem -LiteralPath $Source -Directory)) {
        if (-not (Test-Path -LiteralPath (Join-Path $Source ($bundle.Name + '.md')))) { continue }
        foreach ($file in (Get-ChildItem -LiteralPath $bundle.FullName -Recurse -File)) {
            $key = ($bundle.Name + '/' + $file.FullName.Substring($bundle.FullName.Length).TrimStart('\', '/')).Replace('\', '/')
            $current[$key] = $file.FullName
        }
    }
    $next = @{}
    foreach ($key in @(@($known.Keys) + @($current.Keys) | Sort-Object -Unique)) {
        if ($key -notmatch '^[^./\\:]+/[^:]+$' -or @($key -split '[/\\]' | Where-Object { $_ -eq '..' -or $_ -eq '.' }).Count) {
            throw "Unsafe private resource manifest path: $key"
        }
        $target = [IO.Path]::GetFullPath((Join-Path $root $key))
        if (-not $target.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "Resource escapes destination: $key" }
        # Refuse symlinks/junctions before either copying or deleting a file.
        $cursor = $target
        while ($cursor -and $cursor.Length -ge $root.Length) {
            if ((Test-Path -LiteralPath $cursor) -and ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Resource path contains a link: $cursor" }
            $cursor = Split-Path -Parent $cursor
        }
        $existing = if (Test-Path -LiteralPath $target -PathType Leaf) { (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
        if ($current.ContainsKey($key)) {
            $hash = (Get-FileHash -LiteralPath $current[$key] -Algorithm SHA256).Hash.ToLowerInvariant()
            if (-not $existing -or $existing -eq $hash -or ($known.ContainsKey($key) -and $existing -eq $known[$key])) {
                New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
                Copy-Item -LiteralPath $current[$key] -Destination $target -Force
                $next[$key] = $hash
            } else { Write-Warning "Preserved user resource: $target" }
        } elseif ($existing -and $existing -eq $known[$key]) {
            Remove-Item -LiteralPath $target -Force
        }
    }
    $lines = @($next.Keys | Sort-Object | ForEach-Object { $next[$_] + ' ' + $_ })
    [IO.File]::WriteAllLines($manifestPath, [string[]]$lines, (New-Object Text.UTF8Encoding($false)))
}
