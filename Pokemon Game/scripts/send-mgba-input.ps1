param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$Id,
    [int]$Mask=0,
    [int]$Frames=2,
    [int]$Settle=60,
    [string]$Evidence='m1'
)
$directory=Join-Path $PSScriptRoot "../evidence/$Evidence"
for ($attempt=0; $attempt -lt 50; $attempt++) {
    try {
        Set-Content (Join-Path $directory 'input.txt') "$Id $Mask $Frames $Settle" -Encoding ascii -ErrorAction Stop
        break
    } catch {
        if ($attempt -eq 49) { throw }
        Start-Sleep -Milliseconds 20
    }
}
$deadline=[DateTime]::UtcNow.AddSeconds(55)
while ([DateTime]::UtcNow -lt $deadline) {
    if (Test-Path (Join-Path $directory "$Id.png")) { Write-Output (Join-Path $directory "$Id.png"); exit 0 }
    Start-Sleep -Milliseconds 100
}
throw "mGBA did not finish input $Id. Inspect emulator state before retrying."
