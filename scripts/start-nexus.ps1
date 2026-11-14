$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $Root
try {
    $Python = Join-Path $Root '.venv\Scripts\python.exe'
    if (!(Test-Path -LiteralPath $Python)) {
        & py -3.12 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Python environment setup failed.' }
    }
    & $Python -m pip install -r requirements-nexus.txt -r requirements-mcp.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency setup failed.' }
    & $Python -m cog_core init
    if ($LASTEXITCODE -ne 0) { throw 'COG initialization failed.' }
    & $Python -m cog_core nexus
    exit $LASTEXITCODE
} finally { Pop-Location }
