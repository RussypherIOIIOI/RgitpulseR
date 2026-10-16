# GitPulse execution plan

Workspace: the maintainer's existing GitPulse portfolio checkout. Preserve local
handoff prompts and the original recovery checkout outside the published source.

1. Reproduce and repair the inconsistent closed-PR test fixture.
2. Test PostgreSQL persistence, atomic publication, locking and fixed-clock SQL metrics.
3. Build a deterministic offline demo and bounded Python CLI.
4. Build the responsive Next.js dashboard and protected refresh bridge; test in a browser.
5. After manual refresh passes, document one daily Windows Task Scheduler batch.
6. Run Python tests/lint, TypeScript checks/lint, production build, clean-start smoke.

Initial migration: `migrations/001_initial.sql`, three new tables, two indexes and one
read function; no existing table/data changes. Execute only after owner approval,
against a new isolated local GitPulse database. Never touch JARVIS databases.

Design (updated October 16, 2026 to the owner's JARVIS–TMC standard): VOID #08070D
canvas, neutral #16151D panels, exact IRIS #7F00FF actions/merge bars, and exact NVIDIA GREEN
#76B900 issue bars/ready states. Contrast variations derived from the reference:
IRIS SOFT #D5B9FF, text #FAF8FF, secondary #DCD3EA, muted #C3B9D4, green-tinted
surfaces #0F0E14 and pale green #C7F28A. Green also accents navigation, repository
identity, count badges, table headings and pagination. Stronger borders, restrained corner markers,
and square controls follow the supplied command-center reference. Matrix Sans Regular
supplies headings/metrics; Matrix Sans Video supplies readable interface text. Fonts
are bundled locally with OFL/FONTLOG. Left-aligned content; summary above paired
charts and a full-width activity table. Keep charts and source freshness prominent;
no synthetic health score or ornamental animation. This replaces the original navy,
white, cobalt, amber, Segoe UI and Georgia proposal.

Owner correction: IRIS and NVIDIA GREEN must be paired within the same panels and
charts. Chart plot/track backgrounds are neutral VOID, never purple behind purple
marks or green behind green marks. Merge bars combine IRIS fill and NVIDIA edges;
issue-age bars combine NVIDIA fill and IRIS end caps. Both are one population per
chart; the two mark colors do not imply extra data categories.

Consequential choices: one dataset per database; demo/live require distinct databases.
Session advisory lock covers fetch through commit, without an HTTP-spanning transaction.
SQL owns all metrics and returns one coherent JSON snapshot. Self-hosted Node invokes
Python without a shell. Public mode is read-only; opt-in local refresh requires a
maintainer bearer secret plus exact Origin verification and database cooldown.
