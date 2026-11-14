# User-local staged source installer. No administrator, service, or Hermes reconfiguration.
[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [ValidateSet('Status','Install','Activate','Launch')][string]$Action = 'Status',
    [ValidatePattern('^[0-9a-fA-F]{40}$')][string]$Commit,
    [switch]$WithDesktopExtras,
    [switch]$WithDocumentParsers
)
$ErrorActionPreference = 'Stop'
$Source = Split-Path -Parent $PSScriptRoot
$AppRoot = Join-Path $env:LOCALAPPDATA 'COG-Nexus-App'
$Releases = Join-Path $AppRoot 'releases'
$Pointer = Join-Path $AppRoot 'current.json'
function Assert-Ordinary([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        $Item = Get-Item -LiteralPath $Path -Force
        if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Refusing redirected application path: $Path"
        }
    }
}
function Invoke-Checked([string]$Exe, [string[]]$Arguments) {
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" }
}
function Get-Release([string]$Sha) {
    if ($Sha -notmatch '^[0-9a-f]{40}$') { throw 'Invalid release commit.' }
    $Path = Join-Path $Releases $Sha
    Assert-Ordinary $Path
    $Path
}
function Test-Release([string]$Sha) {
    $Path = Get-Release $Sha
    $Marker = Join-Path $Path 'release.json'
    Assert-Ordinary $Marker
    if (!(Test-Path -LiteralPath $Marker -PathType Leaf)) { throw 'Release is not marked ready.' }
    $Info = Get-Content -LiteralPath $Marker -Raw | ConvertFrom-Json
    if ($Info.commit -cne $Sha) { throw 'Release marker mismatch.' }
    $Python = Join-Path $Path '.venv\Scripts\python.exe'
    if (!(Test-Path -LiteralPath $Python -PathType Leaf)) { throw 'Release Python missing.' }
    Push-Location -LiteralPath $Path
    try { Invoke-Checked $Python @('-m','cog_core','validate') }
    finally { Pop-Location }
}
function Set-Active([string]$Sha) {
    Assert-Ordinary $Pointer
    $Temp = Join-Path $AppRoot ([Guid]::NewGuid().ToString('N') + '.tmp')
    @{commit=$Sha} | ConvertTo-Json -Compress | Set-Content -LiteralPath $Temp -Encoding UTF8
    try {
        if (Test-Path -LiteralPath $Pointer) {
            [IO.File]::Replace($Temp,$Pointer,$null)
        } else { [IO.File]::Move($Temp,$Pointer) }
    } finally {
        if (Test-Path -LiteralPath $Temp) { Remove-Item -LiteralPath $Temp -Force }
    }
}
Assert-Ordinary $AppRoot
Assert-Ordinary $Releases
Assert-Ordinary $Pointer
if ($Action -eq 'Status') {
    if (Test-Path -LiteralPath $Pointer) { Get-Content -LiteralPath $Pointer -Raw }
    else { Write-Output 'No activated COG Nexus release.' }
    return
}
if ($Action -eq 'Launch') {
    if (!(Test-Path -LiteralPath $Pointer)) { throw 'Install and activate a release first.' }
    $Active = (Get-Content -LiteralPath $Pointer -Raw | ConvertFrom-Json).commit
    $Path = Get-Release $Active
    Test-Release $Active
    Push-Location -LiteralPath $Path
    try { Invoke-Checked (Join-Path $Path '.venv\Scripts\python.exe') @('-m','cog_core','nexus') }
    finally { Pop-Location }
    return
}
if (!$Commit) { throw 'Specify the exact reviewed Git commit SHA with -Commit.' }
$Commit = $Commit.ToLowerInvariant()
if ($Action -eq 'Activate') {
    if ($PSCmdlet.ShouldProcess($Commit,'Validate and activate existing release')) {
        Test-Release $Commit
        Set-Active $Commit
    }
    return
}
if (!$PSCmdlet.ShouldProcess($Commit,'Install reviewed source as a new user-local release')) { return }
$Resolved = (& git -C $Source rev-parse --verify "$Commit^{commit}").Trim()
if ($LASTEXITCODE -ne 0 -or $Resolved -cne $Commit) { throw 'Reviewed commit is not present in this checkout.' }
New-Item -ItemType Directory -Path $AppRoot,$Releases -Force | Out-Null
Assert-Ordinary $AppRoot
Assert-Ordinary $Releases
$Destination = Get-Release $Commit
if (Test-Path -LiteralPath $Destination) { throw 'Release already exists. Activate it or inspect the incomplete installation manually.' }
$Archive = Join-Path $AppRoot ([Guid]::NewGuid().ToString('N') + '.zip')
try {
    # Only tracked files at the selected commit; never copy untracked vaults or credentials.
    Invoke-Checked 'git' @('-C',$Source,'archive','--format=zip',"--output=$Archive",$Commit)
    # Refuse existing destination; create venv at the final path.
    New-Item -ItemType Directory -Path $Destination | Out-Null
    Expand-Archive -LiteralPath $Archive -DestinationPath $Destination
    Push-Location -LiteralPath $Destination
    try {
        Invoke-Checked 'py' @('-3.12','-m','venv','.venv')
        $Python = Join-Path $Destination '.venv\Scripts\python.exe'
        $Args = @('-m','pip','install','-r','requirements-nexus.txt','-r','requirements-mcp.txt','-r','requirements-backup.txt')
        if ($WithDesktopExtras) { $Args += @('-r','requirements-nexus-desktop.txt') }
        if ($WithDocumentParsers) { $Args += @('-r','requirements-ingest.txt') }
        Invoke-Checked $Python $Args
        Invoke-Checked $Python @('-m','cog_core','validate')
        Invoke-Checked $Python @('-m','compileall','-q','cog_core')
        # No vault initialization or migration during installation.
        @{commit=$Commit; installed=(Get-Date).ToUniversalTime().ToString('o')} |
            ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $Destination 'release.json') -Encoding UTF8
    } finally { Pop-Location }
    Test-Release $Commit
    Set-Active $Commit
    Write-Output "Activated $Commit. Previous releases and private COG data are preserved."
} finally {
    if (Test-Path -LiteralPath $Archive) { Remove-Item -LiteralPath $Archive -Force }
}
