# Daily batch (optional, Windows)

Added after the manual browser refresh, idempotency and failure/recovery checks
passed. No recurring task is installed automatically. The mechanism is Windows
Task Scheduler invoking `scripts/daily-import.ps1`, which runs the same Python CLI
inside the running Compose app. No second ingestion implementation or laptop
database access from GitHub Actions is assumed.

Prerequisites: Docker Desktop running, Compose app already started, PowerShell 7,
and Windows timezone `Mountain Standard Time` (America/Denver, including DST).
The installer fails visibly for a different timezone. Run from the project root:

```powershell
pwsh -NoProfile -File scripts/daily-schedule.ps1 -Action Enable
pwsh -NoProfile -File scripts/daily-schedule.ps1 -Action Status
pwsh -NoProfile -File scripts/daily-schedule.ps1 -Action Disable
```

The daily trigger is **09:00 America/Denver**. Task Scheduler may delay execution
while the machine sleeps, Docker is stopped or the user session is unavailable.
StartWhenAvailable allows a missed run to start later. The default task runs in the
registering user's interactive context; a logged-out machine is not a dependable
server. It retries failed tasks at most twice, five minutes apart, with a five-minute
task deadline. MultipleInstances IgnoreNew and the PostgreSQL lock reject overlap;
the CLI still performs its bounded HTTP retries and preserves the previous dataset.

Run the job manually without installing a schedule:

```powershell
pwsh -NoProfile -File scripts/daily-import.ps1
```

The container's configured mode, repository and server-side credentials are reused.
For live operation, configure a separate persistent live database and the app's
environment first. Do not put tokens in task arguments. A demo schedule only reloads
synthetic fixtures and never makes their reference time look like a GitHub update.
Inspect `gitpulse status`, the dashboard audit state and Task Scheduler's last result.
