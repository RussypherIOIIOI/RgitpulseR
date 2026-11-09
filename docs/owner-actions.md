# Owner actions: ELMO public DEMO

Updated 2026-11-08. **Deployment and public launch complete:**
[live demo](https://gitpulse.tmcsolutions-org.net/) and [verified receipt](live-release.md).
On November 8 the owner had the merged TMC brand UI deployed. That was an app-only
image upgrade from `main` at `67a74478b8b0fe480c81939640c3382b188a1aa0`, with no
database, credential or tunnel change; see its receipt.
The owner approved existing ELMO hardware and
`gitpulse.tmcsolutions-org.net`. The active candidate requires **$0 additional
platform subscription**; existing domain, hardware, electricity and internet costs
remain. Cards 1–5 below were approved and completed for this release. They are
retained as redeployment reference, not tasks to repeat on the existing volume.
No further token entry is needed.

The complete commands, dependencies, expected results, failure stops and nonsecret
receipts are in [the self-host runbook](selfhost.md). Future redeployments follow
the cards in order; current status and limits are in the live receipt:

| Card | Owner action and approval boundary | Blocks |
| --- | --- | --- |
| 1 | Approve final exact source SHA/image, ELMO resource scope, new protected credentials, dedicated volume, migration 001, reader SQL and 44 synthetic records | Production startup |
| 2 | Build approved image; create nonsecret env and ACL-protected secret files | Database connections |
| 3 | Start isolated PG18; explicitly migrate, seed and grant reader; start loopback app | Local acceptance |
| 4 | Verify health, reader privileges, synthetic metrics and restart persistence | Public promotion |
| 5 | Approve/create tunnel `gitpulse-elmo`, store token privately, route exact hostname to `http://app:3000` | Public HTTPS |
| 6 | Approve Docker sign-in startup and Windows power settings; verify reboot/login dependency | Operational acceptance |
| 7 | Approve isolated restore rehearsal; retain protected backups and recovery/rollback evidence | Recovery acceptance |

Remaining owner decisions concern host startup/reboot verification, protected
off-host backup and fresh-cluster recovery. These were excluded from this launch;
no recurring jobs or host settings were changed. Card 7's local baseline backup
exists and isolated test recovery passed; production recovery remains unverified.
The November 3 launch excluded the main merge. PRs #1–#3 have since merged, and the
November 8 release runs `main`. No action is required to view the public demo. Use the live receipt's health/recovery commands after host changes.

Return only source/image IDs, CI links, container/volume names, tunnel ID, hostname,
status codes, metric/count comparisons, backup hash/time and durations. Never
return credentials, token-bearing connector commands, secret files or unrestricted
logs. Stop on any failed prerequisite, retain the redacted error and keep
publication disabled until corrected.

The earlier paid Render proposal is **historical, unapproved and inactive**.
`deploy/render.yaml` and its installer remain prior proposal artifacts. No Render
login, paid provisioning or billed recovery instance is required for this path.
