# Download a pinned official CLI into ignored local artifacts; no account access.
# Run with PowerShell 7 on Windows. Does not change PATH or log in.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
if (-not $IsWindows) { throw 'This helper supports PowerShell 7 on Windows only.' }
$architecture = switch ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture) {
    'X64' { 'amd64' }
    'Arm64' { 'arm64' }
    default { throw 'Unsupported Windows architecture.' }
}
$cliVersion = '2.34.0'
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$cliDirectory = Join-Path $projectRoot 'artifacts\render-cli'
[System.IO.Directory]::CreateDirectory($cliDirectory) | Out-Null
$archiveName = "cli_${cliVersion}_windows_${architecture}.zip"
$releaseUrl = "https://github.com/render-oss/cli/releases/download/v$cliVersion"
$archivePath = Join-Path $cliDirectory $archiveName
$checksumPath = Join-Path $cliDirectory 'SHA256SUMS'
Invoke-WebRequest -Uri "$releaseUrl/$archiveName" -OutFile $archivePath
Invoke-WebRequest -Uri "$releaseUrl/cli_${cliVersion}_SHA256SUMS" -OutFile $checksumPath
$checksumRows = @(Get-Content -LiteralPath $checksumPath | Where-Object {
    ($_ -split '\s+')[-1] -eq $archiveName
})
if ($checksumRows.Count -ne 1) { throw 'Expected exactly one official archive checksum.' }
$expectedHash = ($checksumRows[0] -split '\s+')[0]
$actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
if ($expectedHash -notmatch '^[a-fA-F0-9]{64}$' -or $expectedHash -ne $actualHash) {
    throw 'Render CLI checksum mismatch; downloaded code was not executed.'
}
# .NET handles literal bracket-containing paths unlike Expand-Archive internals.
[System.IO.Compression.ZipFile]::ExtractToDirectory($archivePath, $cliDirectory, $true)
$cliExecutable = Join-Path $cliDirectory 'render.exe'
if (-not (Test-Path -LiteralPath $cliExecutable -PathType Leaf)) {
    throw 'Official archive did not contain render.exe.'
}
& $cliExecutable --version
if ($LASTEXITCODE -ne 0) { throw 'Render CLI version check failed.' }
Write-Output "Verified official archive SHA256: $actualHash"
