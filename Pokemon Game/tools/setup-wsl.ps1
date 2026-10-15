$ErrorActionPreference = 'Stop'
$logPath = Join-Path $PSScriptRoot '../evidence/m0/wsl-admin-install.log'
Start-Transcript -Path $logPath -Force
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    Write-Output ('Administrator: ' + $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))
    & C:\Windows\System32\wsl.exe --install
    Write-Output ('WSL exit code: ' + $LASTEXITCODE)
} finally {
    Stop-Transcript
}
