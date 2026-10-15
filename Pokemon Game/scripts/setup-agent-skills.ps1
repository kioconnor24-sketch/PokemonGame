param(
    [string]$Repository=(Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
)
$ErrorActionPreference='Stop'
$repositoryPath=(Resolve-Path -LiteralPath $Repository).Path
$canonical=Join-Path $repositoryPath '.agents/skills'
if (!(Test-Path -LiteralPath $canonical -PathType Container)) { throw 'Canonical shared skills are missing' }
$claudePath=Join-Path $repositoryPath '.claude'
New-Item -ItemType Directory -Path $claudePath -Force | Out-Null
$linkPath=Join-Path $claudePath 'skills'
if (Test-Path -LiteralPath $linkPath) {
    $existing=Get-Item -LiteralPath $linkPath
    $existingTarget=@($existing.Target)[0]
    if (!$existingTarget -or [IO.Path]::GetFullPath($existingTarget) -ne $canonical) {
        throw 'Existing Claude skills differ; preserve them and resolve manually rather than overwriting.'
    }
} else {
    if ($env:OS -eq 'Windows_NT') {
        New-Item -ItemType Junction -Path $linkPath -Target $canonical | Out-Null
    } else {
        New-Item -ItemType SymbolicLink -Path $linkPath -Target $canonical | Out-Null
    }
}
Write-Output "Shared skill directory: $canonical"
Write-Output 'Codex repository discovery and Claude skills now reference the same files; verify each client after reload.'
