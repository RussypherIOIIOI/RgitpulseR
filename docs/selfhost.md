# ELMO self-host runbook

Updated 2026-11-08. Target: existing ELMO, read-only synthetic DEMO at
`https://gitpulse.tmcsolutions-org.net`, named Cloudflare tunnel `gitpulse-elmo`.
The URL is **live and publicly verified**; see [the release receipt](live-release.md).
Additional platform subscription:
**$0**; existing hardware, electricity, internet and domain costs remain. Owner:
Russ Meredith.

These cards remain a reference for future redeployment/recovery. The owner approved
the current ELMO deployment and public launch; cards 1–5 are complete for this
release. Do not rerun initialization or regenerate credentials on the existing
volume. Host settings/reboot and fresh-cluster production recovery were excluded
and require their own approved scope. Return no credentials, tokens or DSNs.

An app-only upgrade, with no schema, SQL or credential change, does not rerun these
cards. Build and label the image from the clean reviewed commit as in card 2. Then
change only `GITPULSE_IMAGE` in the existing `deploy/selfhost.env`, recreate only
`app`, and repeat card 4's checks. Card 2's env and secret steps refuse an existing
deployment by design. The November 8 TMC UI release followed this path; its
[receipt](live-release.md) has the exact command and the rollback image.

## 1. Approve the exact release

**Why owner needed:** new secrets, persistent data, SQL, host resources and public
exposure. **Dependencies:** the final reviewed release commit and green required CI
checks for that exact SHA. The November 3 launch used the head of
[PR #1](https://github.com/RussypherIOIIOI/RgitpulseR/pull/1); the November 8 upgrade
used `main` after PRs #1–#3 merged. Also: inspect Compose, migration 001,
reader-role SQL and secret generator. The current approved SHA/image are recorded
in [the live receipt](live-release.md); a future release needs its own exact receipt.

Before cards 2–4 approve: ELMO only; project `gitpulse-public`; new dedicated PG18
container/`gitpulse-public_postgres_data` volume; four ignored ACL-protected files
(`owner_password`, `reader_password`, `owner_database_url`, `reader_database_url`);
existing migration 001 (three tables, two indexes, dashboard function); new explicit
reader-role/grant SQL; 44 synthetic records; reader-only Node app on loopback 3017.
No native PG/JARVIS changes, public DB port, scheduler, live import or paid product.
Record exact full source SHA and final image config ID before production startup.

Separately approve card 5: tunnel `gitpulse-elmo`, protected token file and only
`gitpulse.tmcsolutions-org.net` → `http://app:3000`. Cards 6–7 require approved host
settings/reboot and isolated restore writes. Preserve unrelated domain records.

**Expected / return:** explicit approval scope, full SHA/CI URL, final image receipt
and $0 additional subscription decision. **Stop:** red CI, source/image mismatch,
existing unexpected volume, port conflict, added billing or uncertain zone/account.

## 2. Prepare image and protected files

**Why owner needed:** creates deployment artifacts/credentials. **Dependencies:**
card 1 approval, PowerShell 7, Git, running Docker Desktop Linux engine, free disk
and memory, no listener on loopback 3017. Commands use the actual checkout; keep
this cwd for every card. Native Docker failures must stop the card:

```powershell
Set-Location -LiteralPath 'C:\Users\david\.vscode\[personal_projects]\.ppp-gitpulse'
$ErrorActionPreference = 'Stop'
function Invoke-ReleaseDocker {
    & docker @args
    if ($LASTEXITCODE -ne 0) { throw 'Docker command failed; stop this card.' }
}
Invoke-ReleaseDocker version
Invoke-ReleaseDocker compose version
git status --short
$releaseSha = (git rev-parse HEAD).Trim()
$approvedSha = Read-Host 'Approved full source SHA from the release receipt'
if ($releaseSha -ne $approvedSha -or $releaseSha -notmatch '^[a-f0-9]{40}$') { throw 'Wrong reviewed checkout' }
if (git status --porcelain) { throw 'Use the clean reviewed checkout' }
$releaseImage = 'gitpulse:selfhost-' + $releaseSha.Substring(0, 12)
Invoke-ReleaseDocker build --label "org.opencontainers.image.revision=$releaseSha" -t $releaseImage .
Invoke-ReleaseDocker image inspect $releaseImage --format '{{.Id}} {{index .Config.Labels "org.opencontainers.image.revision"}}'
$releaseImageId = (Invoke-ReleaseDocker image inspect $releaseImage --format '{{.Id}}').Trim()
if ($releaseImageId -notmatch '^sha256:[a-f0-9]{64}$') { throw 'Expected full local image ID' }
if (Test-Path -LiteralPath 'deploy/selfhost.env') { throw 'Existing deployment env requires review' }
$selfhostConfig = (Get-Content -LiteralPath 'deploy/selfhost.env.example' -Raw).Replace('gitpulse:selfhost-REPLACE_WITH_REVIEWED_COMMIT', $releaseImageId)
[IO.File]::WriteAllText((Join-Path (Get-Location) 'deploy/selfhost.env'), $selfhostConfig)
& './scripts/prepare-selfhost-secrets.ps1'
$composeArgs = @('--env-file', 'deploy/selfhost.env', '-f', 'deploy/selfhost.compose.yaml', '-p', 'gitpulse-public')
Invoke-ReleaseDocker compose @composeArgs config --quiet
Get-ChildItem -LiteralPath 'artifacts/selfhost-secrets' | Select-Object Name, Length
Get-Acl -LiteralPath 'artifacts/selfhost-secrets' | Select-Object Owner, AccessToString
git check-ignore deploy/selfhost.env artifacts/selfhost-secrets/owner_password artifacts/selfhost-secrets/reader_password artifacts/selfhost-secrets/owner_database_url artifacts/selfhost-secrets/reader_database_url
```

This builds locally without registry publication and pins the env to the full local
image ID. Record the ID and revision label; the convenient build tag alone is movable.
The current agent-prepared approval receipt supplies the built image ID. If a future
clean-clone build produces a different ID, obtain
that remaining exact-image approval before startup. Recheck the ID before upgrades.

The generator creates four random credential files without printing values and
restricts directory ACLs to current Windows identity and SYSTEM. It refuses existing
files. Compose secrets are mounted host files, **not encrypted-at-rest storage**.
Keep a protected copy with backups; an existing volume needs its original secrets.
Do not print file contents, use shell tracing, expose process environments or pass
credentials as arguments. The startup loader reads only its service-specific DSN
file into process environment; the app does not receive owner credentials.

**Expected / return:** image ID/label, four filenames/nonzero lengths, ACL principals,
ignored status and Compose exit 0. **Stop:** incorrect ACL, missing ignore rule,
partial/existing secret set or wrong build. Do not regenerate for an existing volume;
rotation is a separate reviewed operation. No tunnel token is needed yet.

## 3. Create dedicated PG18, explicitly migrate and seed

**Why owner needed:** starts production containers, creates persistent storage and
executes SQL/publication. **Dependencies:** approved image ID and card 2. Use the
same PowerShell 7 session. If reopened, repeat only cwd/function/`$composeArgs`
definitions; do not rerun credential creation.

Inspect first:

```powershell
Invoke-ReleaseDocker compose @composeArgs ps -a
docker volume inspect gitpulse-public_postgres_data
# For first deployment, "no such volume" is expected; an existing volume needs review.
Get-NetTCPConnection -LocalPort 3017 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, OwningProcess
```

After confirming a new dedicated volume and free port:

```powershell
Invoke-ReleaseDocker compose @composeArgs up -d --wait db
Invoke-ReleaseDocker compose @composeArgs --profile operations run --rm bootstrap python -m gitpulse.cli migrate
Invoke-ReleaseDocker compose @composeArgs --profile operations run --rm bootstrap python -m gitpulse.cli import
Invoke-ReleaseDocker compose @composeArgs exec -T db sh -c 'export GITPULSE_READER_PASSWORD="$(cat /run/secrets/reader_password)"; exec psql -X -q -v ON_ERROR_STOP=1 -U gitpulse_owner -d gitpulse_demo -f /opt/gitpulse/selfhost-reader.sql'
Invoke-ReleaseDocker compose @composeArgs up -d --wait app
Invoke-ReleaseDocker compose @composeArgs ps
```

Each mutation stops on failure. `bootstrap` is an explicit operations-profile job
with owner DSN; normal app startup runs Node only with reader DSN. The existing CLI
migration check is not a complete schema diff. Never use root `docker compose up`
in place of this file/project: root Compose is the local demo with different
startup/security behavior.

**Expected / return:** schema ready/version 1, import success, 44 synthetic items,
reader SQL exit 0 and healthy database/app; no connector started. **Stop:** any SQL,
seed or health failure. Keep publication disabled, retain sanitized errors and
investigate; do not drop tables/delete volumes or retry unexplained partial failure.

## 4. Verify privately and restart the app

**Why owner needed:** exercises deployment and a bounded restart. **Dependencies:**
healthy services and approved synthetic seed. Nonsecret HTTP/privilege checks:

```powershell
$localBase = 'http://127.0.0.1:3017'
(Invoke-WebRequest "$localBase/api/health").StatusCode
(Invoke-WebRequest "$localBase/").StatusCode
(Invoke-WebRequest "$localBase/api/refresh" -Method Post -Headers @{Origin='https://gitpulse.tmcsolutions-org.net'} -SkipHttpErrorCheck).StatusCode
(Invoke-WebRequest "$localBase/api/refresh" -Method Post -Headers @{Origin='https://unrelated.invalid'} -SkipHttpErrorCheck).StatusCode
Invoke-ReleaseDocker compose @composeArgs exec -T db psql -X -v ON_ERROR_STOP=1 -U gitpulse_owner -d gitpulse_demo -c "SELECT count(*) AS synthetic_rows FROM work_items; SELECT rolname, rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls FROM pg_roles WHERE rolname='gitpulse_reader'; SELECT has_table_privilege('gitpulse_reader','work_items','SELECT') AS can_read, has_table_privilege('gitpulse_reader','work_items','INSERT') AS can_insert, has_table_privilege('gitpulse_reader','work_items','UPDATE') AS can_update, has_table_privilege('gitpulse_reader','work_items','DELETE') AS can_delete;"
Invoke-ReleaseDocker compose @composeArgs exec -T app sh scripts/start-selfhost.sh node -e 'const {Pool}=require("pg"); const p=new Pool({connectionString:process.env.DATABASE_URL}); p.query("SELECT current_user, current_database()").then(r=>console.log(JSON.stringify(r.rows))).catch(()=>{console.error("Reader connection check failed");process.exitCode=1}).finally(()=>p.end())'
Invoke-ReleaseDocker compose @composeArgs exec -T db psql -X -v ON_ERROR_STOP=1 -U gitpulse_owner -d gitpulse_demo -c 'SELECT gitpulse_dashboard();'
Invoke-ReleaseDocker compose @composeArgs port app 3000
Invoke-ReleaseDocker compose @composeArgs ps db
Invoke-ReleaseDocker compose @composeArgs restart app
Invoke-ReleaseDocker compose @composeArgs up -d --wait app
(Invoke-WebRequest "$localBase/api/health").StatusCode
Invoke-ReleaseDocker compose @composeArgs exec -T db psql -X -v ON_ERROR_STOP=1 -U gitpulse_owner -d gitpulse_demo -c 'SELECT gitpulse_dashboard();'
```

Compare dataset identity, reference, last-success run and counts before/after restart;
startup must not import again. Recheck app image ID against card 2. Browser checks:
**7h / 14d / 20 open issues / 15 window merges**, DEMO identity, 44 total work items,
search `keyboard` and `#12`, pagination, keyboard focus, mobile layout, fonts and both
chart colors. Reload and confirm persisted results. Database must have no published
port; app must report `127.0.0.1:3017`.

**Expected / return:** HTTP 200/200/403/403, count 44, reader connection identifies
`gitpulse_reader` / `gitpulse_demo`, can_read true and writes false, all elevation
flags false, stable dataset after restart, browser results.
**Stop:** writable reader, wrong identity, restart reseeding or exposed DB/host port.
Keep public profile stopped. CI's three browser tests include isolated failure
injection; never run those against the public deployment.

## 5. Publish only the approved Cloudflare hostname

**Why owner needed:** authenticated account access, secret creation, DNS/route
mutation and public exposure. **Dependencies:** card 4 passes, explicit tunnel/DNS
approval, existing Cloudflare account/zone access and no conflicting `gitpulse`
record. Confirm no additional subscription; stop if offered a paid product.
No zone-wide API token, router forwarding or native cloudflared service is needed.

In [Cloudflare Dashboard](https://dash.cloudflare.com) choose **Networking > Tunnels > Create a tunnel**, select
the cloudflared connector when prompted and name it **gitpulse-elmo**. Choose **Docker** for the connector.
Its example command contains a token: do not execute it or save it to history,
a file, screenshot or chat. Use its copy icon, then paste the whole copied Docker
command (or just its token) into this hidden prompt. Both private entry points
share a parser that extracts only a structurally valid token and never executes
the pasted text:

```powershell
& './scripts/prepare-selfhost-secrets.ps1' -TunnelTokenOnly
Set-Clipboard -Value ''
Get-Item -LiteralPath 'artifacts/selfhost-secrets/cloudflared_token' | Select-Object Name, Length
git check-ignore artifacts/selfhost-secrets/cloudflared_token
Invoke-ReleaseDocker compose @composeArgs --profile public up -d tunnel
Invoke-ReleaseDocker compose @composeArgs ps
```

Create the connector first without a published hostname. The script requires the
four DB secret files and refuses token overwrite. If prompting fails, correct the
issue without printing values. Wait for the approved connector to be healthy.

Then open its **Routes > Add route > Published application**. Set subdomain
**gitpulse**, domain **tmcsolutions-org.net**, leave path empty and service URL
**http://app:3000**. Review exact host/destination before saving. Check for existing
conflicting DNS first; do not delete records without reviewing their purpose.
No wildcard, extra hostname or private-network route is authorized.

```powershell
$publicBase = 'https://gitpulse.tmcsolutions-org.net'
Resolve-DnsName gitpulse.tmcsolutions-org.net
(Invoke-WebRequest "$publicBase/api/health").StatusCode
(Invoke-WebRequest "$publicBase/").StatusCode
(Invoke-WebRequest "$publicBase/api/refresh" -Method Post -Headers @{Origin=$publicBase} -SkipHttpErrorCheck).StatusCode
(Invoke-WebRequest "$publicBase/api/refresh" -Method Post -Headers @{Origin='https://unrelated.invalid'} -SkipHttpErrorCheck).StatusCode
```

Use an external connection/browser to check valid HTTPS, DEMO metrics/counts,
reload persistence, responsive/keyboard/search/pagination behavior and read-only
controls. Healthy tunnel status alone does not prove the app works.

**Expected / return:** tunnel name/ID (never token), exact route/DNS results, HTTP
200/200/403/403 and public browser evidence. **Stop:** wrong account/zone, extra bill,
DNS conflict, TLS/redirect, 502/1033, health or dataset failure. Disable ingress:

```powershell
Invoke-ReleaseDocker compose @composeArgs --profile public stop tunnel
```

This preserves app/data. Review route corrections with owner; do not open DB/router
ports as a workaround. Inspect logs locally and share only redacted errors.

## 6. Verify Windows availability and operating ownership

**Why owner needed:** power/startup settings and reboot affect ELMO/other workloads.
**Dependencies:** approved maintenance window, nonsecret baseline receipt. Compose
`unless-stopped` applies after Docker starts; it does not prove pre-login startup.

Docker Desktop **Settings > General > Start Docker Desktop when you sign in to
your computer**: enable and apply after approval. In Windows Settings search
**sleep**, open this machine's power/sleep controls, and set plugged-in system
sleep to **Never** if approved. Record actual labels/prior values; Windows versions
vary. Display-off can remain. Do not enable automatic Windows login or weaken
security controls. Restart policies do not prevent power/internet/update outages.

At the approved time reboot ELMO. Observe endpoint availability before sign-in;
sign in, wait for Docker running and repeat private/public checks. Record reboot,
sign-in dependency, recovery duration, service states and unchanged dataset identity.
If unattended pre-login startup is required but fails, mark it unmet rather than
claiming continuous availability because ELMO normally remains powered.

Owner monitoring is manual; no monitor/reminder/scheduled task is installed. Check
public health/UI after changes and reboots. Local operational commands:

```powershell
Invoke-ReleaseDocker compose @composeArgs ps
Invoke-ReleaseDocker compose @composeArgs logs --tail 50 app db tunnel
Invoke-ReleaseDocker stats --no-stream
Invoke-ReleaseDocker system df
```

Review logs locally before sharing. Investigate unhealthy status, repeated restarts,
resource pressure and near-full host/VM disk. Owner response: disable ingress if
unsafe, check Docker/power/internet and use card 7. Limits are not load-test evidence.
**Expected / return:** settings changed, reboot/login dependency and recovery time,
healthy services and stable identity. **Stop:** impact on other workloads or unmet
availability requirement; record the limitation.

## 7. Backup, isolated restore and rollback

**Why owner needed:** backup writes and a new rehearsal database; real recovery
changes running behavior. **Dependencies:** approved healthy release, protected
existing backup directory, disk space and approved isolated restore scope. Keep a
secure copy of env/database secret files and tunnel recovery information with the
backup. Do not upload/commit credentials or claim ACLs encrypt them. Use existing
owner-approved protected off-ELMO storage when available. A volume is not a backup.

Dump custom format inside the DB container, then copy with Docker (no PowerShell
binary redirection):

```powershell
$backupStamp = Get-Date -Format 'yyyyMMddTHHmmss'
$backupName = "gitpulse-$backupStamp.dump"
$backupDirectory = Read-Host 'Existing absolute protected backup folder path'
if (-not [IO.Path]::IsPathRooted($backupDirectory) -or -not (Test-Path -LiteralPath $backupDirectory -PathType Container)) { throw 'Use existing protected absolute directory' }
$backupPath = Join-Path $backupDirectory $backupName
if (Test-Path -LiteralPath $backupPath) { throw 'Backup target exists' }
Invoke-ReleaseDocker compose @composeArgs exec -T db pg_dump -U gitpulse_owner -d gitpulse_demo -Fc -f "/tmp/$backupName"
Invoke-ReleaseDocker compose @composeArgs cp "db:/tmp/$backupName" $backupPath
Get-Item -LiteralPath $backupPath | Select-Object Name, Length, LastWriteTimeUtc
Get-FileHash -LiteralPath $backupPath -Algorithm SHA256 | Select-Object Algorithm, Hash
Invoke-ReleaseDocker compose @composeArgs exec -T db pg_restore --list "/tmp/$backupName"
```

Separately approved rehearsal: create a unique database in this **dedicated
container only**, retaining existing cluster roles. Never change the app DSN:

```powershell
$restoreDatabase = 'gitpulse_restore_' + (Get-Date -Format 'yyyyMMddHHmmss')
Invoke-ReleaseDocker compose @composeArgs exec -T db createdb -U gitpulse_owner $restoreDatabase
Invoke-ReleaseDocker compose @composeArgs exec -T db pg_restore -U gitpulse_owner --exit-on-error --no-owner -d $restoreDatabase "/tmp/$backupName"
Invoke-ReleaseDocker compose @composeArgs exec -T db psql -X -v ON_ERROR_STOP=1 -U gitpulse_owner -d $restoreDatabase -c 'BEGIN READ ONLY; SELECT count(*) AS restored_rows FROM work_items; SELECT gitpulse_dashboard(); COMMIT;'
```

Compare restored/primary dataset/run identity, reference, metrics, counts and
business keys; record duration. An archive list alone does not prove recovery.
No cleanup is automatic; retain rehearsal/archive pending exact named deletion
approval. Never seed/import the restore database or switch the app DSN.

This same-cluster rehearsal does not prove fresh-cluster disaster recovery. `pg_dump`
does not preserve role passwords. A fresh-cluster recovery requires the protected
original secret set, explicit initialization of the dedicated cluster, restore into
`gitpulse_demo` using `--no-owner --no-acl`, and separately reviewed execution of
`deploy/selfhost-reader.sql` before reader-app checks. Do not improvise a production
DSN switch; prepare/approve a concrete recovery plan first. Fresh-cluster recovery
remains unverified until actually rehearsed.

Suggested owner-run objective: weekly protected dumps and before approved changes,
up to seven days of evidence loss and a four-hour owner response target. These are
targets, not tested guarantees. No recurring backup job is installed.

App rollback: stop ingress, review a previously recorded compatible image config
ID/tag, edit only `GITPULSE_IMAGE` in `deploy/selfhost.env`, verify ID/source label,
then recreate app and test before reopening:

```powershell
Invoke-ReleaseDocker compose @composeArgs --profile public stop tunnel
# Owner reviews env image against the recorded compatible rollback image receipt.
Invoke-ReleaseDocker compose @composeArgs up -d --wait --force-recreate app
# Repeat card 4; only after acceptance:
Invoke-ReleaseDocker compose @composeArgs --profile public up -d tunnel
```

First public release has no previous public known-good image: keep ingress stopped
and use an approved correction when rollback lacks a validated target. App rollback
does not reverse SQL/data loss. Do not drop migration tables, remove the primary
volume or run `down --volumes` as a shortcut.

**Expected / return:** backup time/size/hash, rehearsal DB name, matching identity/
metrics/keys/counts, measured duration and rollback receipt or explicit limitation.
**Stop:** dump/restore failure, mismatch, no disk or missing secret backup; preserve
healthy primary and sanitized errors.

## References and completion receipt

Official behavior checked 2026-11-02:
[Cloudflare remote tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/),
[Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/),
[Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/),
[volume persistence](https://docs.docker.com/engine/storage/volumes/),
[PostgreSQL 18 pg_dump](https://www.postgresql.org/docs/18/app-pgdump.html) and
[pg_restore](https://www.postgresql.org/docs/18/app-pgrestore.html).

Record full approved SHA/CI URL, image tag/config ID/revision label, ELMO project/
container/volume names, SQL/seed results, reader privilege results, tunnel ID/route,
actual public health/UI results, restart/reboot identity/login dependency, backup
hash/time, restore comparison/duration and rollback target. Mark missing evidence
**unverified**. A build or healthy connector alone does not complete this release.
