# Public DEMO release: ELMO

Updated 2026-11-03. **Approved and publicly verified:**
[gitpulse.tmcsolutions-org.net](https://gitpulse.tmcsolutions-org.net/).
The owner explicitly approved ELMO deployment and public launch, including the
dedicated database, credentials, additive SQL, synthetic seed and exact tunnel
route. See [the dated live receipt](live-release.md) for source/image provenance,
executed checks and operational limits. [Owner-run cards](selfhost.md) remain the
recovery/redeployment reference; [owner actions](owner-actions.md) separates
completed deployment from optional, still unapproved host/recovery changes.

The active implementation is [`deploy/selfhost.compose.yaml`](../deploy/selfhost.compose.yaml),
with a nonsecret [env template](../deploy/selfhost.env.example), explicit
[reader-role SQL](../deploy/selfhost-reader.sql), a
[service-specific secret loader](../scripts/start-selfhost.sh), and
[Windows credential preparation](../scripts/prepare-selfhost-secrets.ps1).

## Scope and architecture

Only bundled synthetic `example/observatory` data is published. No GitHub token,
live ingestion, visitor accounts, web refresh, scheduler or new paid subscription
is included. Retain DEMO provenance, Matrix Sans, IRIS `#7F00FF` and NVIDIA GREEN
`#76B900`.

A dedicated PostgreSQL 18 container owns a new named Docker volume on a private
backend network. It publishes **no database port** and does not use or modify
ELMO's native PostgreSQL/JARVIS services. The app publishes only `127.0.0.1:3017`,
starts Node without automatic migration/import, and receives only a reader DSN
file. The `operations` profile provides explicit one-shot owner CLI jobs with a
separate owner DSN. The `public` profile connector joins the frontend network;
Cloudflare tunnel `gitpulse-elmo` routes only the approved HTTPS hostname to
`http://app:3000`. No router forwarding or public PG listener is needed.

New random credentials reside in ignored ACL-protected host files, mounted as
service-scoped Compose secrets. File mounts are not an encryption-at-rest guarantee.
Tunnel-token entry is a separate hidden prompt after approval, never a command
argument. Reader grants allow SELECT on the three tables and EXECUTE on the
existing dashboard function; smoke checks must confirm no reader write privileges.

App/database limits are each 1 CPU / 512 MB; tunnel is 0.5 CPU / 256 MB. Node
old-space is 320 MB; existing pool size four, connection timeout five seconds and
statement timeout ten seconds remain. Logs rotate at three 10 MB files per service.
These are configured bounds, not measured capacity or an SLA. Host/VM disk growth
is owner-managed; there is no storage autoscale or automatic plan increase.

Additional platform subscription: **$0** using existing Docker/Cloudflare access,
hardware and domain. Existing power/internet/domain costs remain. Confirm account
permissions, applicable product terms and no-cost availability; stop if a paid
product is proposed. Docker Desktop sign-in, Windows sleep/reboots, power and home
internet affect availability. Unattended pre-login recovery is not established.

## Exact SQL and data boundary

Existing [`migrations/001_initial.sql`](../migrations/001_initial.sql) creates
`import_runs`, `repositories`, `work_items`, indexes `work_items_published` and
`import_runs_started`, constraints, and stable SQL function
`gitpulse_dashboard(text,text,text,integer,text)`. The CLI applies it under a
transactional advisory lock. Existing-schema detection is not a full schema diff;
unexpected schemas require investigation.

New [`selfhost-reader.sql`](../deploy/selfhost-reader.sql) creates the login
`gitpulse_reader` if absent, refuses elevated privileges/memberships, and grants
CONNECT, schema USAGE, SELECT and dashboard EXECUTE. It does not rotate existing
credentials. The app never receives the owner DSN. Review both SQL files before
execution; this is additional explicit privilege SQL beyond migration 001.

An explicitly invoked DEMO import publishes 44 synthetic work items and the
successful dataset pointer transactionally. Expected metrics: **7 hours median
merge time, 14 days median issue age, 20 open issues, 15 merged PRs in the window**,
reference `2026-10-12T12:00:00Z`. No real GitHub data is approved.

## Release evidence

| Item | Current state / required receipt |
| --- | --- |
| Running application source | `67a74478b8b0fe480c81939640c3382b188a1aa0` on `main` (TMC brand UI, November 8); previously `dca6823f4567c0a5caa1c286e5d20f5ed409ace0` |
| Current review | PRs #1–#3 merged into `main`; [push CI](https://github.com/RussypherIOIIOI/RgitpulseR/actions/runs/42519456852) succeeded for the running SHA |
| Operator helper source | `510535304dfb671b5c30a5465107bdd06034b5b0`; token parser and ACL checks, no app changes |
| Exact helper-source CI | [Push](https://github.com/RussypherIOIIOI/RgitpulseR/actions/runs/41687858818) and [PR](https://github.com/RussypherIOIIOI/RgitpulseR/actions/runs/41687866846) succeeded |
| Actual running local image ID | `sha256:b547f4d66831c67c717024039401ccae98e89e337f13c075832c0beda201f05c`; rollback target `sha256:cf9f02b20d806d0013f9bb1dd2cebef72aa679a6de0efb4750e5b918b23393a6` (November 3); details in [receipt](live-release.md) |
| Registry digest | **Not claimed**; local config ID is not a registry manifest digest |
| ELMO container/volume and SQL/seed | Running; 44 synthetic rows, dedicated volume, reader-only app |
| Tunnel ID and exact route | `d2100870-8492-4f08-b99c-c6cdb0c6aa37`; approved hostname to `http://app:3000`, four ready connections |
| Public HTTPS/health/UI/read-only/privacy | HTTP 200 root/health; same/foreign-origin refresh 403; two read-only browser tests and external page fetch passed; HTTP and browser checks rerun after the November 8 image swap |
| Restart/reboot, backup/restore, rollback | App restart preserved snapshot; November 8 image swap left the dataset byte-identical; protected local dump exists; isolated same-cluster recovery passed. Host reboot, off-host/fresh-cluster recovery and production rollback remain unverified |

Public deployment evidence is recorded separately from local/CI results in the
[live receipt](live-release.md). Failure-injection browser tests run only against
isolated CI/test resources, never the public DEMO.

The previous paid Render architecture, prices, login/provisioning instructions and
`deploy/render.yaml` are **historical, unapproved proposal artifacts**, superseded
by this ELMO candidate.

## Primary references checked 2026-11-02

- [Cloudflare remote tunnel setup](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/): dashboard connector/routes.
- [Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/): startup after sign-in.
- [Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/): service-scoped file mounts.
- [Docker volume lifecycle](https://docs.docker.com/engine/storage/volumes/): persistence boundaries.
- [PostgreSQL pg_dump](https://www.postgresql.org/docs/18/app-pgdump.html) and [pg_restore](https://www.postgresql.org/docs/18/app-pgrestore.html): logical backup/recovery.
