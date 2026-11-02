# Production DEMO release candidate

Prepared 2026-11-02. **Deployment has not occurred.** No host, workspace, billing
approval, production database, image digest, domain or production URL is established.
The inspected Vercel project list was empty and GitHub deployments returned `[]`;
neither observation proves that no independently managed hosting exists.

The candidate is a public, read-only synthetic portfolio DEMO: no user accounts,
real repository ingestion, GitHub token, web refresh, cron or background importer.
The bundled `example/observatory` fixture is synthetic. Keep DEMO labels and fixture
provenance visible. The established Matrix Sans font and paired IRIS `#7F00FF` /
NVIDIA GREEN `#76B900` design remain application requirements.

## Chosen candidate architecture (awaiting owner selection)

One paid Render Docker web service and one paid PostgreSQL 18 database in Oregon.
This fits the existing Node 24 / Python 3.12 image without splitting the application.
Render manages HTTPS; its private network connects the services. PostgreSQL owns
persistent data; the web filesystem is disposable. No web disk is needed.

[`deploy/render.yaml`](../deploy/render.yaml) is the actual candidate Blueprint.
It starts **only Node**, overrides the Dockerfile's automatic migrate/seed CMD,
disables auto deploys/previews, and initially enables maintenance mode. It contains
no pre-deploy or initial-deploy SQL hook. Creating the Blueprint still provisions
paid resources and attempts the initial deploy; `autoDeployTrigger: off` does not
prevent that first attempt. Only apply it after the owner gate in owner-actions.

Initial health can fail on an empty database. After a successful image build,
an explicitly approved one-off job performs migration and synthetic seeding using
that build. Render documents jobs using the latest successful **build** artifact;
first-deploy bootstrap on this account remains unverified. If Render refuses the
job, stop and retain maintenance mode; do not add an automatic migration hook.

## Bounds and security

Web: one instance, 0.5 CPU, 512 MB RAM, V8 old-space bound 320 MB (other process
memory also counts). PostgreSQL: 0.1 CPU, 256 MB RAM, 1 GB disk, no storage autoscale.
The existing Node pool caps at four connections with 5-second connection and
10-second statement timeouts. CLI jobs have the existing 150-second deadline.
These are proposed resource bounds, not measured hosted capacity or an SLA.
Monitor memory/restarts, disk, connection count, health and latency after deployment.
No silent plan increase is authorized if these bounds prove insufficient.

`DATABASE_URL` is injected from the database; never print or paste it into chat.
The database external IP allow list is empty. Confirm this in the provider console.
Do not add `GITHUB_TOKEN`, `GITPULSE_REFRESH_TOKEN` or any `NEXT_PUBLIC_*` secret.
`GITPULSE_REFRESH_ENABLED=false` enforces visitor read-only behavior and must remain
false. The provider-created database role also supports the approved CLI writes;
this configuration does **not** claim a SELECT-only database role. A dedicated
reader role would require a separately reviewed privilege change, outside this
no-new-SQL release. Restrict provider account access, enable MFA, and keep the API
key used for the one-off job in the owner's terminal only; revoke it afterward.

## Cost proposal, not approval

Official Render sources checked 2026-11-02 list $7/month for the 512 MB web service,
$6/month for the 256 MB paid database and $0.30/GB/month database storage. Proposed
steady base: **$13.30/month USD** on a $0 Hobby workspace with 1 GB database storage.
Taxes, bandwidth/build overages, brief one-off jobs, recovery databases and optional
domains are additional. Request an owner-selected **$20/month operating ceiling**;
this is a human approval threshold, not a provider-enforced hard spending cap.
Before provisioning confirm the console quote and workspace suitability for the
LLC's intended usage. If a paid workspace is needed, re-price and obtain approval.
An unapproved or exceeded quote blocks provisioning; do not substitute Free PG.

Pricing evidence: [official pricing](https://render.com/pricing),
[official cost breakdown](https://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses),
[official service price comparison](https://render.com/articles/render-vs-netlify).
The pricing page body did not render its complete price tables in the text browser;
indexed official pricing supplied the $6 database rate. Console confirmation is
still mandatory before spending.

## Exact migration and publication scope

Only existing [`migrations/001_initial.sql`](../migrations/001_initial.sql) is used.
It creates `import_runs`, `repositories`, `work_items`; indexes
`work_items_published` and `import_runs_started`; and stable SQL function
`gitpulse_dashboard(text,text,text,integer,text)` (default arguments permit `()`).
Primary/unique/check constraints and FKs are defined in that file. There are no
new SQL files, destructive migrations or schema changes in this package.
The CLI applies migration transactionally under a migration advisory lock. Its
existing-schema detection is limited; inspect the dedicated target and do not
treat a no-op as a comprehensive schema diff. Partial/unrelated schemas require
investigation, never manual table deletion to force the CLI through.

`python -m gitpulse.cli import` in DEMO mode reads the packaged fixture and publishes
the business writes and dataset pointer in one transaction. A failed import must
leave the previous successful snapshot; check job failure before attempting any
retry. No network GitHub credentials are required. See [API/schema](api-and-schema.md).

## Provenance and evidence to fill at release

| Evidence | Current value / required release value |
| --- | --- |
| Source inspected before edits | `1eee97dd6706db2c1dd8c493c011204aecb225ad` |
| Final reviewed release commit | **TBD after all authorized work and checks** |
| CI run for that exact commit | **TBD** |
| Candidate hosted build/deploy ID | **TBD, no resource created** |
| Hosted image digest, if exposed | **TBD; record build ID + exact source SHA if provider does not expose digest** |
| Previous known-good deploy ID/source SHA | **TBD; first release has no previous deployed version** |
| Migration/seed job ID and exit status | **TBD** |
| HTTPS URL, health/UI/refresh checks | **TBD** |
| Backup and isolated recovery rehearsal | **TBD** |

Local preparation observed: checksum-verified Render CLI v2.34.0 is available at
`artifacts/render-cli/render.exe`. Official Render JSON Schema validation passed.
The actual CLI validation stopped with `no workspace specified and no default
workspace set`; owner login, CLI authorization and workspace selection are required
before account-aware validation. These observations establish no hosted readiness.

Never replace these with guessed IDs or URLs. Source build provenance does not
prove a registry digest. Run the exact-commit validation and operator steps in
[owner-actions.md](owner-actions.md). Production acceptance requires observed
health 200, correct synthetic UI after reload, refresh 403, HTTPS, database privacy,
and recorded rollback/recovery evidence. Local or schema validation is insufficient.

## Official provider behavior checked 2026-11-02

* [Blueprint fields and schema](https://render.com/docs/blueprint-spec): configuration reference.
* [Compute plan IDs](https://render.com/docs/compute-plans): current resource names.
* [Blueprint setup](https://render.com/docs/infrastructure-as-code): review before Deploy Blueprint.
* [One-off jobs](https://render.com/docs/one-off-jobs): build/config snapshot and billing.
* [API authentication](https://render.com/docs/api): owner API key setup/revocation.
* [CLI validation](https://render.com/docs/cli-reference): `render blueprints validate`.
* [CLI login/workspace setup](https://render.com/docs/cli): local account authorization.
* [SSH access/setup](https://render.com/docs/ssh): public-key registration, Docker prerequisites and ephemeral billing.
* [Managed TLS](https://render.com/docs/tls): host-provided certificates.
* [Database recovery](https://render.com/docs/postgresql-backups): recovery/export operations.
* [Current Deploys UI](https://render.com/blog/deploys-page): Live badge and rollback.
