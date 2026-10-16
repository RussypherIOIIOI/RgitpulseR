# Metric contract

All canonical calculations live in `gitpulse_dashboard` in the PostgreSQL migration.
The frontend only rounds values for display. Every response is one SQL statement and
uses one published run. Table filters never change the metric populations.

Let **A** be the published dataset reference time. Live: completion of all REST reads.
Demo: **2026-10-12 12:00:00 UTC**, fixed in the bundled synthetic fixture.
Let **S** be Monday 00:00 UTC of A's week minus 11 weeks. The merge window is **[S,A)**.
The current UTC calendar week is partial. No historical event reconstruction is implied.

| Metric | Exact definition | Empty population |
| --- | --- | --- |
| Median merge time | `percentile_cont(0.5)` of `(merged_at-created_at)` in fractional hours; true PRs with `merged_at >= S AND merged_at < A`. Includes bots. | SQL null; UI says No merged pull requests |
| Median open-issue age | `percentile_cont(0.5)` of `(A-created_at)` in fractional days for true issues open in the published snapshot, over all imported history. | SQL null; UI says No open issues |
| Open issues | Count of that open-issue population. | 0 |
| Age distribution | Days in `[0,7)`, `[7,30)`, `[30,90)`, `[90,infinity)`. | Four zeros |
| Weekly merged PRs | Count once per canonical PR by UTC Monday week of `merged_at` within `[S,A)`; all 12 weeks returned, zero-filled and chronological. | Twelve zeros |

Age starts at creation, including reopened issues. Closed-unmerged PRs are excluded
from merge metrics. Negative durations, future source timestamps, naive timestamps,
identity conflicts, invalid state/timestamp combinations, and conflicting equal
source versions fail the entire refresh. Nullable/deleted authors are valid.
Optional source fields outside this small model are ignored; no metrics depend on them.

The golden PostgreSQL test uses PR durations `[1,3,5,7]` hours and open-issue ages
`[2,8,40,100]` days. Exact results: **4 hours**, **24 days**, **4 open issues**, age
counts **[1,1,1,1]**. Tests also cover odd medians, empty data, Monday/year boundaries,
the excluded upper bound A, bucket edges, and zero-merge weeks.

GitHub REST pagination is not an atomic snapshot. Issues or PRs can change while
pages are collected. GitPulse validates the collected records and describes them as
approximately current at A. It does not fabricate missing pages or infer deletion
from absence. Missing historical rows remain stored but are outside the latest
publication. These three signals are not a universal repository health score.
