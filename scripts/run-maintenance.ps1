# Explicit owner invocation. Can be registered in Task Scheduler manually.
param([string]$DataDir = '')
$ErrorActionPreference = 'Stop'
$Options = @()
if ($DataDir) { $Options += @('--data-dir', $DataDir) }
$Options += @('maintenance', 'index-refresh')
& powershell.exe -NoProfile -File (Join-Path $PSScriptRoot 'cog.ps1') @Options
exit $LASTEXITCODE
