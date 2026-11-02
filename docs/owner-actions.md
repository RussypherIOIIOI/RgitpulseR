# Owner actions: gated Render DEMO candidate

Prepared 2026-11-02. No steps below have been run against Render. No resource or
spending authorization is implied. Follow the numbered order; retain only nonsecret
receipts in the release evidence. The owner remains Russ Meredith. The environment
and account belong to the owner; no account identifiers or URLs are assumed.

## 1. Approve exact scope and bill before provisioning

Why owner required: host selection, account authorization and spending are owner
decisions. Blocks: all external actions in steps 2–5. Independent work while pending:
local builds, tests, documentation and release review can continue.

Prerequisites: final release commit and green CI, review of production-release.md
and deploy/render.yaml, a Render account with permission to provision in the chosen
workspace. Supply the final commit SHA, workspace name, Oregon region confirmation,
chosen $20/month operating ceiling (or explicit replacement), and approval for
one paid web instance plus one private paid PG18 instance, followed by **only**
migration 001 and synthetic fixture import. This approval covers no live GitHub data.
Confirm the currently quoted total in Render before clicking any paid create action.

Expected: a recorded scope/budget decision. Return: approval text, final SHA and
quoted base price, never billing details or credentials. Recovery: if scope, price,
workspace plan or region is wrong, stop before provisioning and revise the proposal.

## 2. Validate and provision the reviewed Blueprint

Why owner required: browser authentication grants the CLI account access and
provisioning creates paid resources. Blocks: account-aware validation and deployment.
Independent work: local JSON Schema validation and application checks can continue.

Prerequisites: step 1 approval, reviewed commit present on the connected Git remote,
Git provider access restricted to this repository, and explicit owner approval to
authorize the local CLI. The checksum-verified Render CLI v2.34.0 is already at
`artifacts/render-cli/render.exe`; do not install another copy. Local schema
validation passed, but running this CLI's Blueprint validator returned exactly
`no workspace specified and no default workspace set`. It has not validated the
selected account/workspace. In an owner PowerShell terminal run:

```powershell
Set-Location -LiteralPath 'C:\Users\david\.vscode\[personal_projects]\.ppp-gitpulse'
.\artifacts\render-cli\render.exe --version
.\artifacts\render-cli\render.exe login
# In the browser, verify the intended account and click Authorize CLI.
.\artifacts\render-cli\render.exe workspaces --output json
$renderWorkspaceId = Read-Host 'Approved workspace ID from the list'
.\artifacts\render-cli\render.exe workspace set $renderWorkspaceId
.\artifacts\render-cli\render.exe workspace current
.\artifacts\render-cli\render.exe blueprints validate deploy/render.yaml
```

The CLI login stores a token in its local configuration. Do not share that file or
browser authorization URL. Expected: the intended account/workspace selected and
validator exit 0; address failures before continuing. Return only CLI version,
workspace name/ID and validation result; never a token. Recovery: stop on login,
wrong-workspace, schema, plan or
resource-conflict errors; do not create a second copy as a workaround.

In [Render Dashboard](https://dashboard.render.com), choose **New > Blueprint**,
connect the repository, select the approved branch, and set Blueprint path to
`deploy/render.yaml`. Review the two new resources and current prices. Confirm the
private PG allow list, single instance, maintenance mode, disabled auto-deploy and
Node-only Docker command in the preview. Only then click **Deploy Blueprint**.
Disable automatic Blueprint sync in its settings so a future push cannot change
maintenance/security settings without review. Its source branch is inherited by
the web service; do not race a push between approval and first build.

Expected: private database Available and successful Docker image build. The first
web deploy may fail its schema health check until step 3; retain maintenance mode.
Return: database/service IDs (nonsecret), selected source commit/build ID, resource
states and redacted errors. Recovery: build failure means fix the source and obtain
review for the replacement SHA; do not run the job against an unreviewed build.
If the built commit differs from approval, stop. No credentials are entered into
the Blueprint: DATABASE_URL is injected from the database. Confirm web Environment
shows demo/refresh false, and that GitHub/refresh token variables are absent.

## 3. Run the separately approved migration and seed job

Why owner required: this executes approved SQL and publishes the synthetic dataset;
API-key creation grants external account access. Blocks: schema readiness and public
promotion. Independent work: review migration, fixture and job command locally.

Prerequisites: step 1 explicit SQL/seed approval, dedicated empty GitPulse database,
step 2 successful build of the exact approved SHA. Inspect migrations/001_initial.sql
before proceeding; the three tables/two indexes/function are itemized in the release
document. Confirm no real data or unrelated schema is present using provider tooling.
Use Render Account Settings > API Keys to create a temporary owner key. Enter it
at the hidden prompt below in **PowerShell 7**; never paste it into chat, a file,
source code or a command argument. The CLI/container inherits its private DSN from
Render; it must not be copied to the local terminal.

```powershell
$serviceId = Read-Host 'Approved Render web service ID (srv-...)'
if ($serviceId -notmatch '^srv-[a-z0-9]+$') { throw 'Invalid service ID' }
$renderSecret = Read-Host 'Temporary Render API key' -AsSecureString
try {
    $jobBody = @{
        startCommand = 'sh -c "python -m gitpulse.cli migrate && python -m gitpulse.cli import && python -m gitpulse.cli status"'
    } | ConvertTo-Json -Compress
    $job = Invoke-RestMethod -Method Post -Uri "https://api.render.com/v1/services/$serviceId/jobs" `
        -Authentication Bearer -Token $renderSecret -ContentType 'application/json' -Body $jobBody
    $job | Select-Object id, serviceId, createdAt
} finally {
    Remove-Variable renderSecret -ErrorAction SilentlyContinue
}
```

Do not retry POST after a timeout until checking **service > One-off Jobs** for an
already-created job. Expected: job completes once, exits 0, logs contain
`{"status": "schema ready", "version": 1}`, import success, and status reports
DEMO `example/observatory`, the fixture reference time and nonempty data. Return:
job ID, exit status and sanitized counts/reference time. Keep raw private errors
out of chat. A job uses the latest successful build, so confirm it belongs to the
approved build before execution. If the first-deploy job is refused, stop; report
that exact error. Do not switch the web CMD to migrate. After successful job review,
revoke the temporary API key from Account Settings > API Keys > menu > Revoke.

Recovery: failure stops promotion. Inspect sanitized logs; migration is transactional
and import publication is transactional, but audit attempts may persist. Do not drop
objects or reseed a different dataset. Retry only after identifying the cause and
confirming the target/source are unchanged and the approved command remains valid.

## 4. Promote and observe the actual HTTPS workflow

Why owner required: promotion publishes the service and the restart below changes
a running process. Obtain explicit approval for both. Blocks: public acceptance and
restart-persistence evidence. Independent work: finish local browser and API checks.

Prerequisites: successful step 3, correct synthetic status, current resource privacy
and environment checks. In web service > **Manual Deploy**, select **Deploy a
specific commit** with the approved SHA; wait for its health check to pass. Keep
auto-deploy disabled. Change `maintenanceMode.enabled` to `false` in the reviewed
Blueprint, commit that one approved promotion change through the normal review
flow, then manually sync the Blueprint. Confirm sync only changes maintenance mode
and does not change source/build/settings. This explicit gate exposes public traffic.
If a sync would create/reconfigure resources, stop and review its diff first.

Expected: service **Deploys** page shows the approved deployment with Live badge.
Copy the actual Render-assigned HTTPS URL from its service page (do not guess).
Run from PowerShell 7, substituting it at the prompt:

```powershell
$demoOrigin = (Read-Host 'Actual HTTPS origin, without trailing slash').TrimEnd('/')
if ($demoOrigin -notmatch '^https://[a-zA-Z0-9.-]+$') { throw 'HTTPS origin required' }
$ready = Invoke-WebRequest "$demoOrigin/api/health" -SkipHttpErrorCheck
$refresh = Invoke-WebRequest "$demoOrigin/api/refresh" -Method Post -SkipHttpErrorCheck
$foreignRefresh = Invoke-WebRequest "$demoOrigin/api/refresh" -Method Post `
    -Headers @{ Origin = 'https://unrelated.example' } -SkipHttpErrorCheck
$ready.StatusCode
$ready.Content
$refresh.StatusCode
$foreignRefresh.StatusCode
```

Expected: health 200 `{"status":"ready"}`, both refresh probes 403, including the
unrelated Origin. Do not send a refresh token. In a browser verify DEMO
and synthetic provenance; metrics, charts, search/type/state/sort/pagination;
reload preserves results; empty/invalid search recovery; keyboard focus and mobile
layout; font and both chart colors; no refresh credential field or active refresh
action. Inspect browser requests for mixed content or secret exposure. Check the
provider DB External Access remains disabled and CPU/memory/disk/restart metrics.
Return only actual public URL, Live build/source SHA, statuses and findings.

Prove persistence across an explicitly approved **application restart**, not only
a browser reload. Open the paid web service's Dashboard **Shell** and run this
read-only snapshot command. The local SSH-key setup in step 5 is only needed for
the later terminal-based recovery rehearsal:

```sh
python - <<'PY'
import asyncio, json, os
import asyncpg

async def snapshot():
    db = await asyncpg.connect(os.environ['DATABASE_URL'], timeout=10, command_timeout=10)
    try:
        async with db.transaction(readonly=True):
            data = json.loads(await db.fetchval('SELECT gitpulse_dashboard()'))
            print(json.dumps({key: data[key] for key in ('dataset', 'total', 'metrics')}, sort_keys=True))
    finally:
        await db.close()

asyncio.run(snapshot())
PY
```

Record this nonsecret synthetic result. It includes dataset repository/mode/runId,
`asOf`, `lastSuccess`, total and all metrics; never print the environment or DSN.
In the authenticated local owner terminal run (supply the recorded actual service ID):

```powershell
$restartServiceId = Read-Host 'Approved web service ID to restart (srv-...)'
if ($restartServiceId -notmatch '^srv-[a-z0-9]+$') { throw 'Invalid service ID' }
.\artifacts\render-cli\render.exe workspace current
.\artifacts\render-cli\render.exe restart $restartServiceId
```

Confirm the current workspace and target before the restart. Wait for health 200,
reopen Dashboard Shell and repeat the exact read-only snapshot command. Expected:
dataset identity/runId, `asOf`, `lastSuccess`, total and every metric equal the
before-restart receipt; reload the browser and repeat both refresh 403 probes.
Node-only startup must not create a new import run or change lastSuccess. Return
restart time/status and before/after comparison, not private environment values.
If the comparison changes unexpectedly, stop acceptance and investigate startup
and target configuration; do not reseed to make results agree.

Recovery: any failed check means re-enable maintenance via reviewed Blueprint sync,
retain logs and stop claiming release complete. Fix and re-check an approved build.
No health bypass, auto migration or refresh enablement is permitted.

## 5. Backup, restore rehearsal and rollback receipt

Why owner required: registering an SSH key changes account access; recovery and
ephemeral shells create additional billed resources; rollback changes production.
Obtain explicit approval for public-key registration, ephemeral shell charges and
the temporary recovery database within the approved ceiling before each applies.
Blocks: remote persistence/recovery evidence and rollback execution. Independent
work: review backup instructions and prepare comparisons without account changes.

Prerequisites for terminal access: step 2 CLI login and verified current workspace,
paid web service with a successful deploy, and the reviewed Dockerfile creates
`/home/gitpulse/.ssh` owned by `gitpulse` with mode `0700` (Render's non-root Docker
SSH prerequisite). Verify that build contains this directory before connecting.
In the owner terminal repeat `.\artifacts\render-cli\render.exe workspace current`.
Use an existing suitable SSH key if available; never display or upload its private
file. To create a dedicated key only when needed, use a new path and refuse overwrite:

```powershell
$renderKeyPath = Join-Path $env:USERPROFILE '.ssh\gitpulse_render_ed25519'
if ((Test-Path -LiteralPath $renderKeyPath) -or (Test-Path -LiteralPath "$renderKeyPath.pub")) {
    throw 'Key path already exists; reuse an approved key or choose a different new path'
}
ssh-keygen -t ed25519 -f $renderKeyPath -C 'gitpulse-render-owner'
# Set a passphrase at the interactive prompt. Copy only the .pub file:
Get-Content -Raw -LiteralPath "$renderKeyPath.pub" | Set-Clipboard
```

For an existing approved key, copy only its `.pub` file with `Get-Content -Raw
-LiteralPath '<actual-public-key-path.pub>' | Set-Clipboard`. In Render **Account
Settings > SSH Public Keys > + Add SSH Public Key**, enter an owner-recognizable
name, paste the public key, and select **Add SSH Public Key**. Clear the clipboard
afterward with `Set-Clipboard -Value ''`. Keep the private key local. Use the
approved private-key path explicitly with SSH `-i`; compare the first-connection
host fingerprint to the official regional fingerprint in
[Render SSH documentation](https://render.com/docs/ssh#public-key-fingerprints).
On mismatch stop; never bypass host verification. If access is denied, verify the
registered public key, selected account and image ownership; do not weaken modes.

Prerequisites: owner approval for a temporary recovery database and its additional
cost, healthy seeded primary, all identifiers recorded. Database > **Recovery >
Create export** produces a logical backup. Download the completed export to an
owner-controlled protected backup folder; record creation time/hash without sharing
the archive. In an owner PowerShell terminal calculate the exact export hash:

```powershell
$backupArchive = Read-Host 'Absolute path of the downloaded .dir.tar.gz backup'
Get-FileHash -LiteralPath $backupArchive -Algorithm SHA256 | Select-Object Algorithm, Hash
```

Expected: a 64-hex SHA256 hash; return hash and export creation time only. If the
download is missing or incomplete, retry the download before recording a receipt.
Weekly exports and a three-day PITR window on Hobby are the proposed
DEMO recovery plan; the owner must assign a weekly reminder. No scheduler is
installed. Desired recovery objectives: at most seven days of synthetic configuration
evidence loss with export fallback and four-hour owner response; these are targets,
not measured guarantees.

For an isolated rehearsal, database > **Recovery > Point-in-Time Recovery > Restore
Database**, select a seeded time within the available window and at least ten minutes
old, give the new database a distinct rehearsal name, copy existing settings, and
click **Start Recovery**. Wait for Available; confirm its external IP allow list is
still empty. Do not switch the production web DSN. From the authenticated owner
terminal, run the following after checking the approved account/workspace and key:

```powershell
$recoveryServiceId = Read-Host 'Approved web service ID (srv-...)'
$approvedPrivateKey = Read-Host 'Absolute path of the approved local SSH private key'
.\artifacts\render-cli\render.exe workspace current
.\artifacts\render-cli\render.exe ssh $recoveryServiceId --ephemeral -- -i $approvedPrivateKey -o IdentitiesOnly=yes
```

This creates a billed isolated shell from the service artifact without its startup
command; it does not migrate or seed. Stay within the approved operating ceiling;
if a recovery instance or shell would exceed it, stop for revised budget approval.
Disconnect immediately after verification; ephemeral instances bill at the service
rate until disconnect (provider maximum 24 hours). In that remote shell run:

```sh
python - <<'PY'
import asyncio, getpass, json
import asyncpg

async def inspect():
    url = getpass.getpass('Recovery instance INTERNAL URL (hidden): ')
    db = await asyncpg.connect(url, timeout=10, command_timeout=10)
    try:
        async with db.transaction(readonly=True):
            snapshot = json.loads(await db.fetchval('SELECT gitpulse_dashboard()'))
            print(json.dumps({key: snapshot[key] for key in ('dataset', 'metrics', 'total')}))
    finally:
        await db.close()

asyncio.run(inspect())
PY
```

Copy the recovery instance's Internal Database URL from its Info page into the
hidden remote-shell prompt only; never print it or share it in the receipt. Exit
the ephemeral shell when finished. Verify DEMO identity/counts/reference match the
primary receipt. If tooling
cannot reach the private restored instance, keep production unchanged and report
the exact access limitation; do not open `0.0.0.0/0`. Return restore ID, duration,
count comparison and recovery result. Rehearsal is incomplete until observed.

For real recovery only, separately approve switching web DATABASE_URL to the
validated recovery instance using a reviewed Blueprint `fromDatabase` update and
manual sync/deploy; keep the old instance until health/UI checks pass. Recovery
creates another billed database. After recording results, explicitly approve deletion
of the **rehearsal ID only** to stop its cost. Never delete the primary as cleanup.

For application rollback, prerequisite is an identified previous successful compatible
deploy artifact. Web > **Deploys** > select that deploy > **Rollback**; confirm its
source SHA and Live badge, Node-only command, maintenance setting, refresh false,
private DSN and health/UI results. Leave auto-deploy off. Rollback does not undo SQL,
seeding, environment changes or data loss. First release has no previous live build:
its immediate recovery is maintenance mode plus a reviewed corrected deployment.
Do not reverse migration 001 by dropping tables.

Return a nonsecret release receipt: approved SHA/CI URL, provider build/deploy/job
IDs, actual HTTPS origin, privacy and refresh checks, backup timestamp/hash,
restoration comparison/duration and rollback target. Missing evidence remains
explicitly unverified. If stopping the project, disconnect/remove Blueprint management
before separately approved resource deletion so a later sync cannot recreate bills.
