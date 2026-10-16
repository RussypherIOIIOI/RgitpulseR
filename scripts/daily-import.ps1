$ErrorActionPreference = 'Stop'
$gitpulseRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $gitpulseRoot
try {
    & docker compose exec -T app python -m gitpulse.cli import --cooldown 60
    if ($LASTEXITCODE -ne 0) { throw "GitPulse daily import failed with exit code $LASTEXITCODE" }
}
finally { Pop-Location }
