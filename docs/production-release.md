# Public DEMO release candidate: ELMO

Prepared 2026-11-02. **Public deployment remains unverified.** The owner selected
existing ELMO hardware and `https://gitpulse.tmcsolutions-org.net`; this does not
establish a working URL or approve DNS/tunnel mutation. Final exact source/image
approval and [owner-run cards](selfhost.md) remain required. [Owner actions](owner-actions.md)
is the short approval index.

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
| Source reviewed before release | `1eee97dd6706db2c1dd8c493c011204aecb225ad` |
| Current review | [PR #1](https://github.com/RussypherIOIIOI/RgitpulseR/pull/1); resolve final head/checks before approval |
| Final approved deployment SHA | **Pending final commit and approval; do not substitute older candidate SHA** |
| CI for exact final SHA | **Pending**; [verification record](verification.md) separates observed earlier results |
| Image tag/config ID | **Pending final build**; record `gitpulse:selfhost-<12-character SHA>`, full image ID and source label |
| Registry digest | **Not claimed**; local config ID is not a registry manifest digest |
| ELMO container/volume and SQL/seed | **Pending owner-approved execution** |
| Tunnel ID and exact route | **Pending owner-approved Cloudflare action** |
| Public HTTPS/health/UI/read-only/privacy | **Unverified publicly** |
| Restart/reboot, backup/restore, rollback | **Pending operational checks** |

Earlier local/CI successes do not verify this final candidate or its public endpoint.
Use the final source/image receipt, reader checks, public browser checks and recovery
evidence before calling the release complete. Failure-injection browser tests run
only against isolated CI/test resources, never the public DEMO.

The previous paid Render architecture, prices, login/provisioning instructions and
`deploy/render.yaml` are **historical, unapproved proposal artifacts**, superseded
by this ELMO candidate.

## Primary references checked 2026-11-02

- [Cloudflare remote tunnel setup](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/): dashboard connector/routes.
- [Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/): startup after sign-in.
- [Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/): service-scoped file mounts.
- [Docker volume lifecycle](https://docs.docker.com/engine/storage/volumes/): persistence boundaries.
- [PostgreSQL pg_dump](https://www.postgresql.org/docs/18/app-pgdump.html) and [pg_restore](https://www.postgresql.org/docs/18/app-pgrestore.html): logical backup/recovery.
