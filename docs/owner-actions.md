# Owner actions: ELMO public DEMO

Prepared 2026-11-02. The owner selected existing ELMO hardware and
`gitpulse.tmcsolutions-org.net`. The active candidate requires **$0 additional
platform subscription**; existing domain, hardware, electricity and internet costs
remain. Hostname selection does not authorize production SQL, startup, tunnel or
DNS mutation. Final exact source/image approval remains pending.

The complete commands, dependencies, expected results, failure stops and nonsecret
receipts are in [the self-host runbook](selfhost.md). Execute cards in order:

| Card | Owner action and approval boundary | Blocks |
| --- | --- | --- |
| 1 | Approve final exact source SHA/image, ELMO resource scope, new protected credentials, dedicated volume, migration 001, reader SQL and 44 synthetic records | Production startup |
| 2 | Build approved image; create nonsecret env and ACL-protected secret files | Database connections |
| 3 | Start isolated PG18; explicitly migrate, seed and grant reader; start loopback app | Local acceptance |
| 4 | Verify health, reader privileges, synthetic metrics and restart persistence | Public promotion |
| 5 | Approve/create tunnel `gitpulse-elmo`, store token privately, route exact hostname to `http://app:3000` | Public HTTPS |
| 6 | Approve Docker sign-in startup and Windows power settings; verify reboot/login dependency | Operational acceptance |
| 7 | Approve isolated restore rehearsal; retain protected backups and recovery/rollback evidence | Recovery acceptance |

Owner access is needed because these pending actions create credentials and
persistent data, execute SQL, publish an endpoint or change host settings. These
gates follow the requested deployment scope and owner-controlled external actions.
Source review, isolated tests, documentation and CI can continue while pending.

Return only source/image IDs, CI links, container/volume names, tunnel ID, hostname,
status codes, metric/count comparisons, backup hash/time and durations. Never
return credentials, token-bearing connector commands, secret files or unrestricted
logs. Stop on any failed prerequisite, retain the redacted error and keep
publication disabled until corrected.

The earlier paid Render proposal is **historical, unapproved and inactive**.
`deploy/render.yaml` and its installer remain prior proposal artifacts. No Render
login, paid provisioning or billed recovery instance is required for this path.
