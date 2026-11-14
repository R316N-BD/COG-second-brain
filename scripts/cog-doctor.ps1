param([string]$DataDir = '')
$ErrorActionPreference = 'Stop'
$Options = @()
if ($DataDir) { $Options += @('--data-dir', $DataDir) }
& powershell.exe -NoProfile -File (Join-Path $PSScriptRoot 'cog.ps1') @Options doctor
exit $LASTEXITCODE
