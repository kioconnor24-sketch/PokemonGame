param(
    [Parameter(Mandatory=$true)][string[]]$Sync,
    [switch]$NativeTests,
    [switch]$SaveLayoutTests,
    [ValidateRange(1,20)][int]$Jobs=12
)
$ErrorActionPreference='Stop'
$workspace=Split-Path $PSScriptRoot -Parent
foreach ($file in $Sync) {
    if ($file -notmatch '^[A-Za-z0-9_./-]+$' -or $file -match '(^|/)\.\.(/|$)' -or $file.StartsWith('/')) {
        throw "Expected a relative engine source path: $file"
    }
    if (-not (Test-Path -LiteralPath (Join-Path "$workspace/engine" $file) -PathType Leaf)) {
        throw "Missing engine source: $file"
    }
}
$stamp=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$logs=Join-Path $workspace "evidence/builds/$stamp"
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$wslWorkspace=(& wsl.exe -d Ubuntu -u root --exec wslpath -u $workspace).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the project path in WSL.' }
# Paths are positional arguments, never interpolated into shell command code.
$command=@'
set -e
workspace="$1"; stamp="$2"; jobs="$3"; tests="$4"; saves="$5"
shift 5
cd /root/averon/engine
for source in "$@"; do
    mkdir -p -- "$(dirname "$source")"
    if ! cmp -s -- "$workspace/engine/$source" "$source"; then cp -- "$workspace/engine/$source" "$source"; fi
done
run_logged() {
    log="$workspace/evidence/builds/$stamp/$1"; shift
    if "$@" > "$log" 2>&1; then tail -8 "$log"; else tail -45 "$log"; return 1; fi
}
if [ "$tests" = True ]; then run_logged native-tests.log make check -j"$jobs" TESTS=Averon; fi
if [ "$saves" = True ]; then run_logged save-layout-tests.log make check -j"$jobs" TESTS=test/save.c; fi
run_logged build.log make -j"$jobs" -O all
'@
& wsl.exe -d Ubuntu -u root --exec bash -lc $command -- $wslWorkspace $stamp $Jobs $NativeTests.IsPresent $SaveLayoutTests.IsPresent @Sync
if ($LASTEXITCODE -ne 0) { throw "Build/check failed; previous output ROM preserved. Inspect $logs" }
function Read-TestSummary([string]$Name) {
    $raw=Get-Content -LiteralPath (Join-Path $logs $Name) -Raw
    $plain=$raw -replace '\x1b\[[0-9;]*m',''
    $passed=[regex]::Match($plain,'Tests\s+PASSED\s*:\s*(\d+)')
    $total=[regex]::Match($plain,'Tests\s+TOTAL\s*:\s*(\d+)')
    if (-not $passed.Success -or -not $total.Success -or
        [int]$total.Groups[1].Value -eq 0 -or
        [int]$passed.Groups[1].Value -ne [int]$total.Groups[1].Value) {
        throw "Missing, empty or incomplete test results in $Name; previous output ROM preserved."
    }
    return [ordered]@{passed=[int]$passed.Groups[1].Value; total=[int]$total.Groups[1].Value; log=$Name}
}
$nativeSummary=$null
$saveSummary=$null
if ($NativeTests) { $nativeSummary=Read-TestSummary 'native-tests.log' }
if ($SaveLayoutTests) { $saveSummary=Read-TestSummary 'save-layout-tests.log' }
# Publish only after both the build and requested test summaries are verified.
New-Item -ItemType Directory -Force -Path "$workspace/build-output" | Out-Null
& wsl.exe -d Ubuntu -u root --exec cp /root/averon/engine/pokeemerald.gba "$wslWorkspace/build-output/Pokemon-Averon-Test-Build.gba"
if ($LASTEXITCODE -ne 0) { throw 'Could not copy the successful ROM into build-output.' }
$rom=Get-Item -LiteralPath "$workspace/build-output/Pokemon-Averon-Test-Build.gba"
$shared=Join-Path $workspace 'shared-repo'
$reference=(& git -C $shared rev-parse HEAD).Trim()
$inputs=@{}
$dirty=$false
foreach ($file in $Sync) {
    $inputs[$file]=(Get-FileHash -LiteralPath "$workspace/engine/$file" -Algorithm SHA256).Hash.ToLowerInvariant()
    $peer="$shared/Pokemon Game/engine/$file"
    if (-not (Test-Path -LiteralPath $peer) -or (Get-FileHash -LiteralPath $peer).Hash.ToLowerInvariant() -ne $inputs[$file]) { $dirty=$true }
}
$manifest=[ordered]@{
    file=$rom.Name; reference_source_commit=$reference; input_differs_from_reference=$dirty
    build_command="make -j$Jobs -O all"; build_exit_code=0; size_bytes=$rom.Length
    sha256=(Get-FileHash -LiteralPath $rom.FullName).Hash.ToLowerInvariant()
    native_tests_requested=$NativeTests.IsPresent; save_layout_tests_requested=$SaveLayoutTests.IsPresent
    native_test_results=$nativeSummary; save_layout_test_results=$saveSummary
    synchronized_source_hashes=$inputs; logs=$logs
    status='BUILT — FULL GAMEPLAY ACCEPTANCE PENDING'
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$workspace/build-output/BUILD-MANIFEST.json" -Encoding utf8
Write-Output "Built $($rom.FullName)"
Write-Output "SHA256 $($manifest.sha256)"
Write-Output "Source reference $reference; input differs: $dirty"
