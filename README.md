# GitPulse

A repository observatory for maintainers and hiring reviewers: explainable merge
metrics, issue ages and a searchable activity table for **one public GitHub repository**.
Python collects the data; PostgreSQL owns persistence and metric calculations;
Next.js renders a responsive TypeScript dashboard.

The interface follows the JARVIS–TMC standard: IRIS **#7F00FF**, NVIDIA GREEN
**#76B900**, and VOID **#08070D**, with fine panel borders and lavender supporting
tones. Matrix Sans Regular supplies headings and metrics; Matrix Sans Video supplies
interface text. Both webfonts are bundled from the owner's supplied theme package,
self-hosted through Next.js and distributed with their SIL Open Font License and font log.
Brighter secondary text and clearer borders strengthen the dark theme. Neutral panels
pair IRIS and green accents together. Both charts have VOID plot backgrounds: IRIS
merge bars carry green edges, while green issue-age bars carry IRIS end caps.
Small explanatory/data labels are checked against a 7:1 contrast target.

![GitPulse dashboard with deterministic synthetic data](docs/dashboard.png)

## Run the demo

Prerequisite: Docker Desktop with Compose. From a clean clone/project root:

```powershell
git clone https://github.com/RussypherIOIIOI/RgitpulseR.git
cd RgitpulseR
docker compose up --build -d
```

Open **http://localhost:3017**. First startup applies the additive initial migration
to a dedicated PostgreSQL volume and imports 44 synthetic records. The web view is
read-only by default. Images/dependencies require network on first build; subsequent
demo loads use only bundled JSON and PostgreSQL, without GitHub or a token.
The database and app ports bind only to loopback. The Compose database password is
a public local-demo placeholder, not a production credential.

Explore the 12-week merge chart, the four issue-age buckets, then search `keyboard`
or `#12` and move between table pages. Metrics retain their full populations while
table filters change. Demo results: **7 hours median merge time**, **14 days median
open-issue age**, **20 open issues**, **15 merged PRs in the window**. The fixed
reference is October 12, 2026 at 12:00 UTC; the load timestamp records the actual seed.
`example/observatory`, authors and records are synthetic; their shaped source URLs
are examples, not claims that those records exist on GitHub.

```powershell
docker compose exec -T app python -m gitpulse.cli import
docker compose exec -T app python -m gitpulse.cli import
docker compose exec -T app python -m gitpulse.cli status
docker compose stop
```

The two imports retain **44** business keys and the same fixed-clock metrics.
Successful audit run IDs and load times change. `docker compose down` removes
containers/network while retaining the database volume. **Destructive reset:**
`docker compose down --volumes` permanently deletes this project's database volume;
use only after explicitly deciding to discard it. Never run resets on shared data.

## Manual refresh

CLI refresh works immediately. For the local web button, opt in before startup:

```powershell
$env:GITPULSE_REFRESH_ENABLED = 'true'
$env:GITPULSE_REFRESH_TOKEN = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
docker compose up -d
```

Keep the generated value private; enter it into **Maintainer controls → Maintainer
key**, then **Refresh dataset**. The key stays in memory, never local storage or the
URL. Requests require the key and an exact same-origin POST. Web refresh has a
60-second database cooldown; all entry points share the same database session lock.
A failed import leaves the prior dataset and last successful update intact.
Leave `GITPULSE_REFRESH_ENABLED=false` for public demos. See [API/storage](docs/api-and-schema.md).

## Local development

Use Node.js 24 LTS, Python 3.12+ and uv 0.10.10. Keep the project root as cwd.

```powershell
docker compose up -d --wait db
uv sync --frozen --extra dev
npm ci
$env:DATABASE_URL = 'postgresql://gitpulse:local-demo-only@127.0.0.1:55440/gitpulse_demo'
$env:GITPULSE_MODE = 'demo'
uv run gitpulse migrate
uv run gitpulse import
Copy-Item -LiteralPath .env.example -Destination .env.local
npm run dev
```

Next reads `.env.local`; Python CLI reads process environment. Neither is committed.
The migration command is explicit and transactional; apply only to the dedicated
database you have chosen. Do not run database migrations against unrelated JARVIS data.
Docker startup intentionally applies the same initial migration automatically.

## Live import

Use a **different database** from demo. For example, on this isolated local Compose DB:

```powershell
docker compose exec -T db createdb -U gitpulse gitpulse_live
$env:DATABASE_URL = 'postgresql://gitpulse:local-demo-only@127.0.0.1:55440/gitpulse_live'
$env:GITPULSE_MODE = 'live'
$env:GITPULSE_REPO = 'pallets/itsdangerous'
# Optional: set GITHUB_TOKEN privately to a read-only token.
uv run gitpulse migrate
uv run gitpulse import
uv run gitpulse status
```

Set those same database/mode/repository values in `.env.local` and restart `npm run dev`
to view live data. `pallets/itsdangerous` is a suggested bounded walkthrough target;
the optional real-network import must be verified when run. It was not imported
as part of the deterministic test suite. The API resolves and checks public visibility
and numeric repository identity, requests all states, filters PR representations from
issues and uses canonical PR IDs/`merged_at`. No arbitrary browser-selected targets.

Live imports are complete paginated REST collections, not atomic GitHub snapshots.
Defaults: 50 pages per endpoint, 10000 source records total, two bounded retries,
120-second HTTP budget. Any cap or failed page fails the whole attempt. Keep sources
modest. Without a token, GitHub's unauthenticated API quota can prevent repeated imports;
the client honors rate-limit headers and fails visibly when delay exceeds its budget.

## Architecture and correctness

```mermaid
flowchart LR
  G[GitHub REST / bundled demo] --> P[Python: collect and validate]
  C[Maintainer CLI] --> P
  W[Protected web POST] -->|fixed CLI; no shell| P
  T[Optional daily Windows task] -->|same CLI| P
  P -->|session lock; atomic publication| D[(PostgreSQL)]
  D -->|one SQL snapshot; canonical metrics| N[Next.js server components]
  N --> V[Charts and paginated activity]
```

Database-enforced keys prevent duplicates. Newer source records update existing
entities; older versions cannot overwrite them; equal-version conflicts fail.
The per-database lock spans HTTP collection through commit without holding an open
transaction during HTTP. Publication writes and the successful-run pointer commit
together. Failed fetches/writes preserve prior published data and record a sanitized
failed attempt. Missing historical records stay stored but are outside the latest
publication. [Exact metric definitions](docs/metrics.md) · [Schema/API](docs/api-and-schema.md)
· [Decisions and implementation plan](docs/implementation-plan.md).

## Tests and evidence

```powershell
docker compose exec -T db createdb -U gitpulse gitpulse_test
docker compose exec -T db createdb -U gitpulse gitpulse_cli
$env:TEST_DATABASE_URL = 'postgresql://gitpulse:local-demo-only@127.0.0.1:55440/gitpulse_test'
$env:TEST_CLI_DATABASE_URL = 'postgresql://gitpulse:local-demo-only@127.0.0.1:55440/gitpulse_cli'
uv run --frozen --extra dev pytest -m 'not browser' -q
uv run ruff check src tests
uv run ruff format --check src tests
npm test
npm run check
npm run lint
npm run build
npm audit --omit=dev
```

Create each database once; `createdb` fails if it already exists. Integration tests
use fresh named schemas and retain them for inspection; use a disposable test database,
not a production database. Without test DSNs, those tests explicitly skip. Browser
tests use Playwright (Edge on Windows, installed Chromium on Linux). They require a
separate `gitpulse_browser` database and a server configured for it. See
[verification evidence and reproduction](docs/verification.md). CI runs deterministic
HTTP fixtures, real PostgreSQL integration, browser refresh checks, type checks, lint
and production build. CI is not a deployment and never accesses a live database.

The golden fixture proves **4 hours / 24 days / 4 issues / [1,1,1,1] age buckets**.
The rollback test fails on the second actual business update; the previous rows and
published pointer remain identical. Two database connections prove overlapping
entry points cannot publish competing imports.

## Configuration

| Variable | Meaning |
| --- | --- |
| `DATABASE_URL` | Server-only PostgreSQL DSN; required for CLI and dashboard |
| `GITPULSE_MODE` | `demo` (default) or `live`; never mixed in a database |
| `GITPULSE_REPO` | One fixed public owner/repo for live imports |
| `GITHUB_TOKEN` | Optional read-only GitHub token; server-side only |
| `GITPULSE_REFRESH_ENABLED` | Exactly `true` opts into the web refresh button/endpoint |
| `GITPULSE_REFRESH_TOKEN` | Maintainer secret, at least 32 characters |
| `GITPULSE_ORIGIN` | Exact browser origin; Compose defaults to `http://localhost:3017` |
| `GITPULSE_PYTHON` | Trusted server-side Python executable; defaults to the local venv |
| `TEST_DATABASE_URL`, `TEST_CLI_DATABASE_URL` | Disposable PostgreSQL integration/CLI databases |
| `GITPULSE_BROWSER_URL`, `TEST_BROWSER_DATABASE_URL` | Browser test server and isolated database |
| `PLAYWRIGHT_CHANNEL` | Optional browser override; platform defaults documented above |

Never place secrets in `NEXT_PUBLIC_*`, URLs, command arguments, source control or
screenshots. Docker image build excludes `.env*`. Production image runs as a non-root
user and omits frontend development dependencies. The supported runtime is a persistent
self-hosted Node/Python process with PostgreSQL, not serverless Next.js.

## Scheduling and deliberate limits

An optional **09:00 America/Denver** Windows daily task invokes the same CLI after
the manual workflow passes. Enable, disable, timing/retries and operating requirements
are in [scheduling.md](docs/scheduling.md). No recurring job is installed automatically.

No streaming, webhooks, multiple repositories, universal health score, AI features,
Kafka, Kubernetes or login platform. Next steps: revisit unpatched development-tool
advisories, add reviewed schema version 2 when needed, and measure import limits on
the intended live source before considering incremental ingestion.

## Versions and references

Direct versions are pinned in `pyproject.toml`/`package.json`, with `uv.lock`, a hashed
Docker Python requirements export and `package-lock.json`. Python 3.12.13, httpx 0.28.1,
asyncpg 0.31.0, Next.js 16.4.1, React 19.3.1, TypeScript 6.0.3, pg 8.23.1;
Docker bases pin observed Node 24, Python 3.12 and PostgreSQL 18 image digests.
ESLint 9.39.5 matches the current Next config plugin peer ranges; that ESLint line is
deprecated upstream. Five dev-tool audit findings trace to an unpatched `braces`
advisory. Production dependency audit: zero findings on October 15, 2026.

Official references checked October 15, 2026: [GitHub issues](https://docs.github.com/en/rest/issues/issues),
[PR endpoints](https://docs.github.com/en/rest/pulls/pulls),
[REST practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api),
[PostgreSQL ordered-set aggregates](https://www.postgresql.org/docs/current/functions-aggregate.html),
and the installed Next.js 16.4.1 App Router guides (`node_modules/next/dist/docs`).
Context7 was used to cross-check async `searchParams` and server-component data access.
