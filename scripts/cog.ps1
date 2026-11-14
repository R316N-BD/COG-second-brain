# Native Windows launcher. No activation, Bash, or administrator required.
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $Root
try {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m cog_core @args
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m cog_core @args
    } else {
        throw 'Python 3.10+ is required. Install Python from python.org and reopen PowerShell.'
    }
    $Code = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $Code
