param(
    [Parameter(Mandatory=$true)][string]$Python,
    [string]$Repository=(Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
)
$ErrorActionPreference='Stop'
$repositoryPath=(Resolve-Path -LiteralPath $Repository).Path
$pythonPath=(Resolve-Path -LiteralPath $Python).Path
$outputPath=Join-Path $repositoryPath 'agent-local'
$timer=[Diagnostics.Stopwatch]::StartNew()
# Code-only prevents semantic/LLM calls. Graphify's manifest refreshes changed files.
& $pythonPath -m graphify extract $repositoryPath --code-only --no-cluster --no-dedup --max-workers 4 --out $outputPath --timing
if ($LASTEXITCODE -ne 0) { throw 'Local Graphify refresh failed; inspect output before using the graph.' }
$timer.Stop()
$graph=Join-Path $outputPath 'graphify-out/graph.json'
if (!(Test-Path -LiteralPath $graph)) { throw 'Refresh produced no graph.json' }
$commit=(& git -C $repositoryPath rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot record source commit' }
$branch=(& git -C $repositoryPath branch --show-current).Trim()
$dirty=@(& git -C $repositoryPath status --porcelain).Count -gt 0
[ordered]@{
    source_commit=$commit; branch=$branch; dirty=$dirty
    graph_sha256=(Get-FileHash -LiteralPath $graph -Algorithm SHA256).Hash.ToLowerInvariant()
    elapsed_seconds=[Math]::Round($timer.Elapsed.TotalSeconds,3)
    indexed_at_utc=[DateTime]::UtcNow.ToString('o')
    mode='code-only; local AST; no strict hooks; documentation remains source/GitHub search'
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputPath 'provenance.json') -Encoding utf8
