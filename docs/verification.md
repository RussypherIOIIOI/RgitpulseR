# Verification record — October 15, 2026

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
chromium`. Screenshots are captured in ignored `artifacts/`; the README includes a
real captured image in `docs/dashboard.png`. Tests explicitly wait for the new
publication timestamp after a successful refresh, avoiding a race with router refresh.

## Supported evidence boundaries

Local success does not prove a GitHub CI run or live deployment. The initial local
verification predates repository publication. The publication target is
`RussypherIOIIOI/RgitpulseR`; its existing initial history and GPLv3 license are retained.
CI outcomes and deployment must be verified separately from a successful Git push.
Live source size/rate-limit behavior must be checked for the maintainer's chosen
repository. A multi-request REST read can change during collection. Dependencies
and their advisory status may change after this dated verification.
