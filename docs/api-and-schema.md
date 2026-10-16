# API and storage

`GET /` renders server-side PostgreSQL data. Parameters: `q` (up to 200 characters),
`type` (issue/pr/empty), `state` (open/closed/merged/empty), `sort` (updated/created),
`page` (integer 1–100000). Duplicate/invalid parameters show a resettable error.
Pages past the available range clamp to the final page; pages contain 10 records.
Search is literal, case-insensitive title/author/number containment. Ordering is
descending source timestamp, then descending issue/PR number. SQL is parameterized.

`GET /api/health`: 200 `{ "status": "ready" }` when the schema is readable, including
a database with no published import; 503 for unavailable/mismatched storage.

`POST /api/refresh`: no configurable target or body. Defaults to disabled (403).
Enable server configuration and supply `Authorization: Bearer <maintainer-key>`.
The server checks an exact `Origin` against `GITPULSE_ORIGIN` and a constant-time
key comparison (minimum 32 characters). Keys are entered into a password field,
kept only in client memory, and sent only in the request header. No cookies/login
system. Use TLS for remote access. 200 means publication completed; 409 means the
database lock/cooldown rejected the import; 503 means the importer failed. Unsupported
GET returns 405. Requests never accept a repository, executable, shell argument or DSN.

The self-hosted Node process invokes the fixed Python module with shell disabled,
a whitelisted environment, a 160-second child deadline and an 8 KiB output bound.
Python has a 150-second total deadline; HTTP collection is bounded to 120 seconds,
15 seconds per request, two retries, 50 pages per endpoint, and 10000 total source
records (issue-endpoint PR representations also consume the protective cap).
Web refresh has a database-backed 60-second cooldown. CLI and daily batch share
the same session advisory lock through collection, validation and commit.

## Migration 001

Apply only to a dedicated GitPulse database. Initial migration adds three tables,
two indexes and a stable SQL function. The CLI applies it transactionally with a
separate advisory migration lock; repeating an already complete initial migration
is a no-op. A partial or unrelated schema fails visibly. This MVP has one schema
version; future changes require new explicit migrations.

* `import_runs`: UUID, mode/repository, status, start/end/reference timestamps,
  fetched/written counts and a sanitized error summary. Running attempts abandoned
  by a killed process are marked failed when the next importer acquires the lock.
* `repositories`: singleton dataset identity, numeric GitHub repository ID, mode,
  source name and last-successful-run FK. Different modes/targets require different
  databases/volumes; a mode/target mismatch fails before network collection.
* `work_items`: PK `(repository_id,number)`, unique `(repository_id,kind,source_id)`,
  kind/title/nullable author/state/source URL, UTC timestamps, last-seen-run FK.
  Checks enforce positive identities and consistent state/timestamp ordering.

Business writes, success-run metadata and the published pointer commit in one
transaction. Audit creation/failure recording happen separately. A write failure
rolls back every business change while preserving the previous pointer and success
timestamp. Older source versions cannot overwrite newer rows. Equal-version
conflicts fail explicitly. Retained records absent from the latest import are not
presented as current and are not interpreted as confirmed GitHub deletions.

No database error, raw HTTP body, token or stack trace is returned to visitors.
CLI failures are nonzero (3 for busy/cooldown; 1 for other errors); successful output
is small JSON. Connection errors have generic summaries. Loss of the database itself
can prevent recording a failed attempt; it cannot publish a successful one.
