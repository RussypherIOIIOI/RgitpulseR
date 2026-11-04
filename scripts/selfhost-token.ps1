# Shared parser for private owner entry. Never execute or print the pasted text.
function ConvertFrom-CloudflareTunnelEntry {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Entry)
    $text = $Entry.Trim()
    if ($text -match '^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$') {
        throw 'That is the Tunnel ID. Use the copy icon beside Run tunnel with Docker.'
    }
    if ($text -match '[*•]') {
        throw 'This is masked placeholder text. Use the connector command copy icon.'
    }
    $candidate = if ($text -match '(?:^|\s)--token(?:\s*=\s*|\s+)(\S+)') {
        $Matches[1].Trim([char[]]@([char]34, [char]39))
    } else { $text }
    if ($candidate -notmatch '^[A-Za-z0-9_+/=-]{40,}$') {
        throw 'No valid tunnel token found. Nothing was written.'
    }
    try {
        $encoded = $candidate.Replace('-', '+').Replace('_', '/')
        $encoded += '=' * ((4 - $encoded.Length % 4) % 4)
        $payload = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded)) | ConvertFrom-Json -ErrorAction Stop
        $tunnelId = [guid]::Empty
        if (-not $payload.a -or -not $payload.s -or -not [guid]::TryParse([string]$payload.t, [ref]$tunnelId)) {
            throw 'Invalid structure'
        }
    } catch {
        throw 'No valid Cloudflare tunnel token found. Nothing was written.'
    }
    return $candidate
}
