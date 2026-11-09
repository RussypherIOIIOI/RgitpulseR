# Verification record

## TMC brand UI release — November 8, 2026

The merged TMC redesign (`main` at `67a74478b8b0fe480c81939640c3382b188a1aa0`)
replaced the running app image on ELMO. PRs #1–#3 are merged. This supersedes the
running-source and merge-status statements in the dated sections below.
[Full receipt](live-release.md).

- **CI:** the [push CI](https://github.com/RussypherIOIIOI/RgitpulseR/actions/runs/42519456852)
  for that exact SHA passed `verify` and `selfhost`.
- **HTTP:** private and public health and root returned 200, an unknown path returned
  404, and same/foreign-origin refresh POSTs returned 403.
- **Reader and data:** reader identity is unchanged. Row count, import runs and
  `gitpulse_dashboard()` output were byte-identical before and after the swap.
- **Browser:** public read-only checks gave **2 passed, 1 deselected** in 17.42
  seconds. [Desktop capture](public-dashboard.png).

## Public ELMO release — November 3, 2026

The approved deployment is live at [gitpulse.tmcsolutions-org.net](https://gitpulse.tmcsolutions-org.net/).
This dated update supersedes the pending deployment/DNS statements in the
historical sections below. [Full live receipt and limitations](live-release.md).

- Public root and health returned 200 with normal TLS validation; same/foreign
  Origin POST refresh returned 403. An external Exa fetch retrieved the public
  dashboard and expected synthetic metrics.
- Public read-only browser checks: **2 passed, 1 deselected** in 10.75 seconds;
  failure-injection/manual-refresh test excluded from production. Fonts, paired
  IRIS/green charts, VOID plots, computed contrast, keyboard operation, mobile
  overflow, search and pagination passed.
- App-only restart preserved run `b7ae66db-c787-4ce6-aade-47d0c7816fe5`, load
  `2026-11-03T17:27:00.498459+00:00`, two import runs, 44 rows and exact metrics
  **7h / 14d / 20 / 15**. No seed/import was invoked by the restart verification.
- Actual reader connection, denied writes, private database/no host port and
  loopback app binding were verified on ELMO. Connector readiness returned 200
  with four connections. No native PostgreSQL/JARVIS settings were changed.
- Exact operator-source `510535304dfb671b5c30a5465107bdd06034b5b0` passed
  [push CI](https://github.com/RussypherIOIIOI/RgitpulseR/actions/runs/41687858818)
  and [PR CI](https://github.com/RussypherIOIIOI/RgitpulseR/actions/runs/41687866846):
  50 Python/PostgreSQL tests, three isolated browser tests, two TypeScript tests,
  lint/type/build, zero Python/npm runtime audit findings and disposable selfhost
  isolation/restart/recovery contract. Running app source remains approved dca6823;
  later helper/document changes do not imply the running image was rebuilt.
- A protected on-ELMO baseline dump exists. No host reboot, pre-login Docker
  recovery, off-host backup, fresh-cluster recovery or production rollback was
  executed. No automatic monitoring/backup task was installed. Main merge excluded.

## Historical ELMO selfhost candidate — November 2, 2026

The owner declined additional hosting subscriptions, confirmed always-on hardware,
and selected `gitpulse.tmcsolutions-org.net`. The active candidate is now
`deploy/selfhost.compose.yaml`; the earlier paid Render package below is historical,
unapproved and superseded. **No production database, public tunnel or DNS route has
been created.** The selected hostname currently returns DNS name does not exist.

Observed local verification of the actual selfhost package:

- Built the Node/Python image including `start-selfhost.sh`. Pulled pinned
  cloudflared 2026.10.7 and verified its version and `--token-file` support without
  network access from the version/help containers.
- `python scripts/verify-selfhost.py --image gitpulse:selfhost-verify` passed against
  a uniquely named disposable Docker project: private PG18 without host ports,
  loopback-only app, missing-secret rejection, zero implicit schema writes before
  explicit migration/seed, exact **44 / 7h / 14d / 20 / 15** fixture results,
  reader SELECT access with persistent write/CREATE rejection, 403 refresh with
  same/foreign Origin, identical restart snapshot and same-cluster backup/restore.
- Reader-role SQL repeated safely and rejected four independently induced unsafe
  cases: owned table, schema CREATE, PUBLIC UPDATE, and column-level UPDATE. These
  mutations were isolated test fixtures and were removed. No public tunnel started.
  The script removed only its own disposable containers/network/volume.
- Windows PowerShell secret generation produced current-user/SYSTEM-only protected
  directory ACLs, distinct random credentials, ignored file paths and refusal to
  overwrite. A non-root container read the ACL-protected DSN mount without printing
  its value. No production credential files or actual tunnel token were created.
- Compose validation, PowerShell parsing, Ruff lint/format and diff checks passed.
  Independent review's reader-ownership/CREATE finding was corrected; final source
  and operator-document review reported no remaining must-fix findings.

CI adds a separate `selfhost` job that builds the image and executes the same
disposable runtime/recovery contract, alongside the existing 41 PostgreSQL/Python,
3 browser and 2 TypeScript checks and runtime audit gates. Final exact-source CI and
image provenance are recorded in the ignored `artifacts/elmo-release-approval.md`
after publication; [PR #1](https://github.com/RussypherIOIIOI/RgitpulseR/pull/1) is the
authoritative candidate head/checks view. Earlier green CI does not prove this new
job until it actually passes.

Public HTTPS/UI, actual Cloudflare account/route, production SQL/seed, host reboot
and pre-login Docker recovery, fresh-cluster restoration and operational availability
remain unverified. [Owner cards](selfhost.md) distinguish each pending gate. Existing
ELMO power/internet/domain costs remain; the proposal adds no platform subscription.

## Release hardening — November 2, 2026

This section supersedes the historical dependency/CI/production-browser caveats
below. Public deployment remains unverified; no production resources were created.

- Clean local/remote base: `1eee97dd6706db2c1dd8c493c011204aecb225ad`.
  [Its hosted CI passed](https://github.com/RussypherIOIIOI/RgitpulseR/actions/runs/38938786757):
  41 Python/PostgreSQL tests, 3 production-server browser tests, 2 TypeScript tests,
  lint, type checks and build. The earlier production-refresh policy blocker was
  subsequently covered by those CI browser tests.
- Patched certifi from 2026.7.22 to 2026.10.23, regenerated hashes with uv 0.10.10,
  and added pinned pip-audit 2.10.1 plus lock/export consistency checks to CI.
  Baseline audit failed; patched Python runtime audit returned zero findings.
  npm runtime audit also returned zero findings. Full npm audit retains 16 moderate
  development entries from one minimatch advisory; see [security evidence](release-security.md).
- Fresh real PostgreSQL 18 tests: **41 passed, 3 browser tests deselected**, no
  integration skips. Fresh browser tests against the rebuilt production Docker
  server: **3 passed**. Tests cover fonts, paired chart colors, sampled contrast,
  keyboard access, responsive layout, search/pagination, refresh authorization,
  cooldown, real failed writes, last-good preservation and recovery.
- TypeScript tests **2 passed**; Ruff lint/format, TypeScript check, frontend lint,
  local production build and Docker build passed. Local Node is 25.9.0; Docker/CI
  use the pinned Node 24 runtime. Build warned about an unrelated parent-directory
  lockfile; the Docker build context stays inside this repository.
- Disposable resources use Compose project `gitpulse-release-20261102`, PostgreSQL
  loopback port 55441, application port 3018, separate test/CLI/browser databases.
  Fresh approved schema/seed startup produced 44 records and metrics **7h / 14d /
  20 open issues / 15 window merges**. Image runtime readback: certifi 2026.10.23.
  Local image config ID:
  `sha256:361af791651cad45921bd4b0e7d9a8be84c9c472cb1a6d698b6333b859cf68c9`.
  This local image is not a remotely published registry artifact.
- The final image includes the Render Docker SSH prerequisite: non-root UID 10001,
  `/home/gitpulse/.ssh` mode 0700 owned by gitpulse. A second isolated database
  verified Node-only startup leaves **zero public tables**, returns health 503,
  and performs no implicit initialization. Explicit approved migration/seed then
  returned health 200, 44 rows and the expected metrics. Refresh returned 403 both
  without credentials and with an unrelated Origin. An app restart preserved the
  exact dataset identity, reference/load time, metrics, counts and single audit run.
  Two read-only browser checks passed again against this final image.
- Render Blueprint passed the current official JSON Schema. The checksum-verified
  local Render CLI 2.34.0 could not run account-aware validation: `no workspace
  specified and no default workspace set`. Account/workspace validation is pending.
  Independent package review found two operational gaps; both were corrected and
  the targeted rereview reported no remaining must-fix findings.
- GitHub deployment records and the connected Vercel project list were empty.
  No compatible existing host/account access was discovered. Proposed Render
  configuration, costs, owner gates and operations are documented separately.
  Patched application candidate `f8b3555c7beb9b03624c53cb75ec4c01854b8bc8`
  [passed hosted CI](https://github.com/RussypherIOIIOI/RgitpulseR/actions/runs/41521390933)
  including the new Python audit gate, 41 PostgreSQL/Python tests and all 3 browser
  tests. [Release PR #1](https://github.com/RussypherIOIIOI/RgitpulseR/pull/1) contains
  the current candidate; its exact final head/CI are also recorded in the local
  `artifacts/portfolio-release-receipt.md` after publication.

The historical records below retain their original dates and evidence scope.

## JARVIS–TMC theme update — October 16, 2026

Applied the owner's exact IRIS #7F00FF, NVIDIA GREEN #76B900 and VOID #08070D,
plus supporting panel/text tones from the supplied reference. Matrix Sans Regular
and Matrix Sans Video WOFF2 files are copied from the owner's theme package and
self-hosted by Next.js; OFL and FONTLOG are retained in source and runtime image.
Regular supplies headings/metrics, Video supplies interface text. The old Segoe UI,
Georgia, light surfaces and blue/amber chart palette have been replaced.

Observed: the theme regression failed on the prior light UI, then passed against the
rebuilt Docker application. Checks cover actual computed anchor colors, downloaded
font faces (no failed font responses), sampled foreground/background contrast of
at least 4.5:1, visible keyboard focus and no document overflow at 390px. Existing
browser search/pagination/empty-state checks also passed, with no uncaught page errors.
Desktop 1440px and mobile 390px screenshots were visually inspected. These checks
are scoped evidence, not a full assistive-technology accessibility certification.

`npm test` (2 tests), `npm run check`, `npm run lint`, local production build,
Docker build and Python test-file lint passed. The running container's image digest
was verified against the newly built image, and the existing in-app browser was
reloaded. Only the app container was replaced, with a temporary ignored Compose
command override that starts Node directly; no migrations or reimports were run.
API, database, refresh authorization and metric behavior are unchanged.

The README screenshot is updated; additional desktop/mobile/overview captures are
in ignored `artifacts/`. The October 15 backend verification below remains historical.

### Contrast refinement — October 16, 2026

At the owner's request, brightened supporting text, raised purple panel surfaces,
strengthened control/panel borders and table row separation, and introduced dark
green surfaces with pale-green accents. NVIDIA GREEN now also accents active
navigation, repository identity, issue panels, table headings, count badges and
pagination. Exact IRIS/NVIDIA GREEN/VOID anchors and Matrix Sans remain intact.

The strengthened browser test first failed on the previous card note (about 5.6:1),
then passed with at least 7:1 for sampled small explanatory/data labels. Other sampled
text/control pairs retain a 4.5:1 minimum. Both browser tests passed (theme/keyboard/
fonts/contrast plus desktop/mobile search/pagination/empty states); TypeScript tests,
type checks, lint, local production build and Docker build passed. The app-only
container was replaced and the user's browser reloaded; no migrations or imports.
Updated desktop/mobile/overview screenshots and README preview were captured.

### Paired-color correction — October 16, 2026

The owner rejected separate purple-on-purple and green-on-green chart treatments.
The current design supersedes those earlier refinements: neutral panel surfaces,
VOID plotting areas and tracks, and both exact colors within each chart. Merge bars
use IRIS fills with NVIDIA GREEN edges; issue-age bars use NVIDIA GREEN fills with
IRIS end caps. Card rules and repository borders also pair both colors. Colors do
not encode additional populations or categories. Browser assertions cover the
actual plot background and both foreground colors in each chart, in addition to
the existing text-contrast, font-loading, keyboard and responsive checks.
The updated color regression failed against the previous treatment and passed
against the rebuilt app. Both scoped browser checks passed, as did lint, type checks,
TypeScript tests, and local/Docker production builds. The running image was verified,
the owner's tab refreshed, and the README screenshot updated. No data changes.

## Initial MVP evidence

This records observed local evidence, not a deployed GitHub release.

| Check | Observed result |
| --- | --- |
| Recovered baseline | Reproduced 20 passed / 1 failed; corrected the inconsistent closed-PR fixture without weakening validation |
| Python contracts + real PostgreSQL | 41 passed, browser checks deselected; no skipped PostgreSQL checks with dedicated test DSNs |
| TypeScript security/input tests | 2 passed |
| Type checking | `npm run check` passed |
| Frontend lint | `npm run lint` passed |
| Python lint/format | Ruff check and format check passed |
| Local production build | `npm run build` passed; dynamic overview, health and refresh routes |
| Docker image | Built pinned Node/Python bases with production-only Node dependencies, non-root runtime |
| Empty-database clean start | New `gitpulse_clean` project/volume; approved migration and seed succeeded, health returned ready, 44 rows and expected demo metrics |
| Browser overview | Desktop and mobile; search, pagination, empty results, stable metrics and no uncaught browser errors passed in development and packaged Docker production |
| Browser manual refresh | Development server: success, denied key, cooldown, injected real write failure, preserved last-success timestamp and successful recovery passed |
| Production refresh repeat | A separate host Node test-server launch on port 3019 was rejected by automatic approval review with only `blocked by policy`; that repeat was not executed |
| Production npm audit | Zero findings |
| Development npm audit | Five high-severity transitive findings through the unpatched braces <=3.0.3 advisory; ESLint 9.39.5 is deprecated but matches the Next plugin peer ranges |
| Windows batch script | PowerShell parser verification; immediate run correctly rejected by cooldown, later one-shot execution succeeded and wrote the same 44 entities |
| Hosted GitHub CI | Workflow written and action refs verified; not pushed or executed on GitHub |
| Live GitHub import | Opt-in; not executed against the network in this deterministic run |
| Recurring task | Installer and enable/disable/status commands supplied; no task installed |

The golden PostgreSQL fixture returned median merge time **4 hours**, median issue
age **24 days**, **4** open issues and exactly **[1,1,1,1]** age buckets. The repeat
import compares full business fields/keys plus fixed-reference metrics. The rollback
test fails on the second database update and verifies identical prior rows and
published metadata. Independent connections prove the lock rejects overlap during
fetch. Other cases cover source changes/reopening/merging, older versions, empty
repositories, historical rows missing from the new collection, UTC Monday/year and
age bucket boundaries, literal search and table-only filtering, timeout/rate limits,
malformed JSON, page caps/later-page failures, and credential-safe error/navigation.

## Reproduce browser checks

Use a **dedicated** `gitpulse_browser` database. Never point these tests at an owner's
dataset: they intentionally install a failure trigger and adjust test run timestamps.
The trigger is disabled in a finally block; test records are retained for inspection.

```powershell
docker compose exec -T db createdb -U gitpulse gitpulse_browser
$env:DATABASE_URL = 'postgresql://gitpulse:local-demo-only@127.0.0.1:55440/gitpulse_browser'
$env:GITPULSE_MODE = 'demo'
uv run gitpulse migrate
uv run gitpulse import
$env:GITPULSE_REFRESH_ENABLED = 'true'
$env:GITPULSE_REFRESH_TOKEN = 'test-only-maintainer-key-0123456789-abcdef'
$env:GITPULSE_ORIGIN = 'http://localhost:3017'
# Ensure .env.local does not point to another database; process environment wins.
npm run dev
```

In a second terminal, from the same project root:

```powershell
$env:GITPULSE_BROWSER_URL = 'http://localhost:3017'
$env:TEST_BROWSER_DATABASE_URL = 'postgresql://gitpulse:local-demo-only@127.0.0.1:55440/gitpulse_browser'
$env:GITPULSE_REFRESH_TOKEN = 'test-only-maintainer-key-0123456789-abcdef'
uv run --extra dev pytest tests/test_browser.py -q
```

That key is a public test fixture, never a deployment secret. Windows tests use
installed Edge. On Linux install Chromium with `uv run playwright install --with-deps
chromium`. Screenshots are captured in ignored `artifacts/`. The README shows the
public deployment capture `docs/public-dashboard.png`; `docs/dashboard.png` is the
original October 16 local capture, kept for history. Tests explicitly wait for the new
publication timestamp after a successful refresh, avoiding a race with router refresh.

## Supported evidence boundaries

Local success does not prove a GitHub CI run or live deployment. The initial local
verification predates repository publication. The publication target is
`RussypherIOIIOI/RgitpulseR`; its existing initial history and GPLv3 license are retained.
CI outcomes and deployment must be verified separately from a successful Git push.
Live source size/rate-limit behavior must be checked for the maintainer's chosen
repository. A multi-request REST read can change during collection. Dependencies
and their advisory status may change after this dated verification.
