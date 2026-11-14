param([string]$DataDir = '')
$ErrorActionPreference = 'Stop'
$Launcher = Join-Path $PSScriptRoot 'cog.ps1'
$Options = @()
if ($DataDir) { $Options += @('--data-dir', $DataDir) }
# Invoke in child process: launcher exits with the underlying Python status.
& powershell.exe -NoProfile -File $Launcher @Options validate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& powershell.exe -NoProfile -File $Launcher @Options init
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& powershell.exe -NoProfile -File $Launcher @Options doctor
exit $LASTEXITCODE
