# PowerShell 7 / Windows. Run only for an approved new GitPulse deployment.
# Values stay in ACL-protected, ignored local files; never print their contents.
[CmdletBinding()]
param(
    [string]$OutputDirectory = '',
    [switch]$TunnelTokenOnly
)

$ErrorActionPreference = 'Stop'
if (-not $IsWindows) { throw 'Use PowerShell 7 on Windows for the ACL-protected secret setup.' }
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path (Split-Path -Parent $PSScriptRoot) 'artifacts\selfhost-secrets'
}
$secretDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
$databaseFiles = @('owner_password', 'reader_password', 'owner_database_url', 'reader_database_url')
$targetFiles = if ($TunnelTokenOnly) { @('cloudflared_token') } else { $databaseFiles }
foreach ($fileName in $targetFiles) {
    if (Test-Path -LiteralPath (Join-Path $secretDirectory $fileName)) {
        throw 'Secret file already exists. Stop; rotation needs a separately reviewed procedure.'
    }
}
if ($TunnelTokenOnly) {
    foreach ($fileName in $databaseFiles) {
        if (-not (Test-Path -LiteralPath (Join-Path $secretDirectory $fileName) -PathType Leaf)) {
            throw 'Prepare and verify the database secret set before adding the tunnel token.'
        }
    }
}
[System.IO.Directory]::CreateDirectory($secretDirectory) | Out-Null
$acl = [System.Security.AccessControl.DirectorySecurity]::new()
$acl.SetAccessRuleProtection($true, $false)
$inherit = [System.Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit'
$propagate = [System.Security.AccessControl.PropagationFlags]::None
$allow = [System.Security.AccessControl.AccessControlType]::Allow
$currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$systemSid = [System.Security.Principal.SecurityIdentifier]::new('S-1-5-18')
foreach ($sid in @($currentSid, $systemSid)) {
    $acl.AddAccessRule([System.Security.AccessControl.FileSystemAccessRule]::new(
        $sid, 'FullControl', $inherit, $propagate, $allow))
}
Set-Acl -LiteralPath $secretDirectory -AclObject $acl

function Write-NewSecret([string]$Name, [string]$Value) {
    $stream = [System.IO.File]::Open((Join-Path $secretDirectory $Name),
        [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None)
    try {
        $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Value)
        $stream.Write($bytes, 0, $bytes.Length)
    } finally { $stream.Dispose() }
}

if ($TunnelTokenOnly) {
    $secureToken = Read-Host 'Approved GitPulse Cloudflare tunnel token (hidden)' -AsSecureString
    try {
        $tokenValue = [System.Net.NetworkCredential]::new('', $secureToken).Password.Trim()
        if ($tokenValue.Length -lt 40 -or $tokenValue -match '\s') {
            throw 'Invalid tunnel token shape. Nothing was written.'
        }
        Write-NewSecret 'cloudflared_token' $tokenValue
    } finally {
        Remove-Variable tokenValue, secureToken -ErrorAction SilentlyContinue
    }
    Write-Output 'Tunnel token stored. No token value was printed.'
} else {
    $ownerPassword = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLowerInvariant()
    $readerPassword = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLowerInvariant()
    try {
        Write-NewSecret 'owner_password' $ownerPassword
        Write-NewSecret 'reader_password' $readerPassword
        Write-NewSecret 'owner_database_url' "postgresql://gitpulse_owner:${ownerPassword}@db:5432/gitpulse_demo"
        Write-NewSecret 'reader_database_url' "postgresql://gitpulse_reader:${readerPassword}@db:5432/gitpulse_demo"
    } finally {
        Remove-Variable ownerPassword, readerPassword -ErrorAction SilentlyContinue
    }
    Write-Output 'Created four database secret files. Values were not printed.'
}
Write-Output 'Preserve these files securely with the database backup; do not regenerate them for an existing volume.'
