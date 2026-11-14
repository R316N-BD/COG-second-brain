# Preview only: native update application is deliberately not implemented yet.
param([switch]$Offline)
$ErrorActionPreference = 'Stop'
$Options = @('update-preview')
if ($Offline) { $Options += '--offline' }
& powershell.exe -NoProfile -File (Join-Path $PSScriptRoot 'cog.ps1') @Options
exit $LASTEXITCODE
