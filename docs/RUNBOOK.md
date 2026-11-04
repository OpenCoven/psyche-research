# Founder runbook

Status: reviewable operating candidate, 2026-11-04. This runbook does not adopt policies or authorize provisioning, deployment, new persistent credentials, external messages, payments, legal agreements or a public launch. Read [STATUS.md](STATUS.md), [DECISIONS.md](DECISIONS.md), [POLICIES.md](POLICIES.md), [PILOT.md](PILOT.md), [THREAT_MODEL.md](THREAT_MODEL.md) and [RELEASE.md](RELEASE.md) before operating. One founder is the proposed operator; there is no independent board or guaranteed reviewer pool. The user selected Vercel; [VERCEL.md](VERCEL.md) is the primary hosted packet. SQLite file commands and nginx/Gunicorn procedures below apply only to local or alternative persistent-host operation, not managed PostgreSQL recovery.

## Before any real intake

Record an accountable human operator, monitored public contact and private recovery contact; approved dates, subject scope, privacy/content-license terms and retention choices; real hosting region, domain/TLS, service account, persistent disk, cost cap and available hours; exact source/deployment revision; independently reviewed configuration; tested encrypted off-host backups; actual-client keyboard/zoom/contrast/screen-reader acceptance; and an explicit go/no-go. Use the pilot matrix. No placeholder contact or hostname is a working route. Keep intake paused if any gate is missing. PILOT_APPROVED is an operator attestation after this record, not a substitute for acceptance.

The proposed pilot is four weeks, ten consenting participants, ten new submissions total, five queued at once, one queued per author, two active records per author and twenty globally. The application enforces queue/active bounds and the production approval flag; the founder manually records participant count, ten-total submissions, dates and schedule. No account is selected through affiliation, social popularity, payment, recommendations or a reputation score.

## Start of every operating session

Inspect the exact running revision, health, aggregate error counts, queue age, unresolved reports/appeals, available disk, last successful backup and last restore drill. Confirm the operator is available and no incident or takeover invalidates prior acceptance. Read current issues and status before changing code. Run a fresh backup with the currently deployed release before migrations. Keep a confidential operator decision log; never paste manuscripts, account details, secrets or report bodies into public GitHub issues.

Visit /operations/ as the explicit human moderator to see configured caps, oldest submitted timestamp, active draft/queue/publication counts, pending appeals and bounded reports. The queue is ordered by submitted time. Safety reports may need urgent action separate from routine queue order; neither social score nor familiarity is a priority rule. Count missing moderation time as unknown, not zero.

The proposed schedule is two 45-minute moderation sessions and one 30-minute operations/metrics session per week, with a separately agreed incident reserve. Track actual minutes per submission, author-help request, appeal, report and recovery. There is no response-time promise. Pause at five queued, oldest queue item over fourteen days, unavailable operator, unmonitored report route, unknown backups, or weekly effort above three hours for two weeks. Lower caps rather than erase records to make metrics improve.

## Human account and role procedures

There is no email provider, public signup or automatic identity verification. After separately approved onboarding and a verified private contact route, the human operator runs provision_contributor in a private terminal, supplies the initial password through getpass and shares it through the approved private channel. Do not use a shell argument, issue, chat log or committed file for passwords. The contributor changes it after sign-in. Public byline is separate from private login and may be pseudonymous if the adopted policy supports it. Do not require a GitHub account or institutional email.

```sh
.venv/bin/python manage.py provision_contributor CONTRIBUTOR_LOGIN
.venv/bin/python manage.py set_moderator MODERATOR_LOGIN --reason 'Approved human moderator assignment; decision reference'
.venv/bin/python manage.py set_moderator MODERATOR_LOGIN --revoke --reason 'Access revocation; decision reference'
```

These are examples for the human operator, not actions already performed. Role grants expand private access and require their own approval. Staff/superuser status confers no publication permission. There is no generic admin editing surface. Never give an automated familiar a human session, moderator account, database file or production credential.

Manual account recovery requires confirming the existing agreed recovery route and identity without public disclosure. Use Django's interactive changepassword only after that verification, notify through the already approved channel, and revoke compromised access as needed. A changed password invalidates sessions on their next authentication check; on suspected theft stop service or use a reviewed session revocation procedure. Do not guess identity from repository popularity. If identity cannot be verified, pause the account and escalate to the human owner. No self-service recovery or communication service is implemented.

## Moderation checklist and decision

Read only the assigned private submission and its exact frozen revision/digest. Never run notebooks, scripts, repositories, attached instructions or agent output. Do not fetch remote previews through the application. If a human chooses to inspect external artifacts, use a separately assessed safe environment and permissions; a public link is not proof of license or safety. State what was actually inspected.

Check subject scope, metadata completeness, methods/claims/limitations clarity, artifact access/provenance/versions, contributor consent and rights declarations, privacy, unsafe disclosure and abuse. Treat negative results and replications neutrally. Disclose conflicts in the required decision field or explicitly state None. Do not approve your own work, including with an operator/superuser account. Founder-authored or materially conflicted work must wait for another qualified human or remain unpublished; do not invent a reviewer.

Choose request changes with actionable reasons, decline with a reason within scope/capacity, or publish the exact submitted snapshot. The decision and conflict declaration are private to the author and moderators. Moderation does not test scientific truth and must not be described as peer review. Before publishing, check the public byline and license as the contributor supplied them and remind the author to consider other venues' preprint/anonymity rules. Do not promise academic acceptance, indexing or a DOI.

An identical retry after an interrupted response does not create another submission/publication. A stale save or decision returns a conflict; reload saved state, preserve the submitted form text privately, and reconcile before retrying. The application does not autosave. A database busy response has Retry-After; reload to check whether the prior operation succeeded instead of issuing a new action with modified content blindly.

## Corrections, withdrawal, reports and appeals

An author proposes a later version from the public record, supplies a change note, and submits it for a new exact-version decision. Earlier published content stays fixed. Human reviews and vouches are unavailable; the next milestone must bind actor/scope/conflict/consent/revocation to one version and never transfer endorsement to a correction. The current archive contains no endorsement or reputation store.

An author or moderator can immediately withdraw a whole work through the confirmation page. Use a short safe public reason that does not repeat private data. Every version becomes a tombstone and public HTML/search/JSON omits the manuscript; account owners/moderators still have restricted records. External downloads/caches may persist. For suspected serious exposure, stop public serving as well as pausing intake; no blanket automatic content purge or CDN recall is implemented.

Reports are anonymous text without a collected contact address. Triage them in /operations/ and record a bounded private resolution. Ten unresolved reports per work and one hundred globally bound storage; sixty authenticated or ten anonymous mutations per fixed minute bound attempts. When a report cap is full, the approved operator contact is the fallback; that contact must exist before pilot. If the current proxy makes all anonymous requests appear loopback, the anonymous rate cap is shared across visitors; validate usability and never enable arbitrary forwarded-header trust to fix it.

Appeals are private and bound to a specific recorded decision. One open appeal per submission, one per exact decision and at most three per submission are implemented; further exceptional review needs the human operator. A moderator cannot resolve their own appeal. Respond with reasons; reopening cannot overwrite a newer decision or exceed active capacity. If the original founder reconsiders a decision, disclose that it is reconsideration by the same person, not independent appeal review. If an unconflicted competent person is required but unavailable, pause and state that limit rather than use a familiar as an independent judge.

## Pause, incidents and observability

```sh
.venv/bin/python manage.py pause_intake --reason 'Specific operating or safety reason'
```

This only pauses new submissions for moderation; saved drafts and public pages remain available. Use /operations/ to change limits or reopen only after current acceptance, capacity and incident checks. For a credible leak, compromised account, malicious public material or unknown backup/access state, pause intake immediately, restrict affected serving routes or stop the WSGI service, preserve minimal confidential evidence, contain exposure, identify affected records, repair and run targeted regressions, and get human incident acceptance before restoring access. External notifications, credential rotations or legal escalation need the applicable human decision and authorization.

/health/ checks database/singleton availability and returns status only. Application JSON logs contain opaque request ID, route name, method, response status and duration. They omit raw paths/queries, accounts, IPs, headers, bodies, passwords, cookies, reports and private text. Use status/duration counts and request IDs to locate an operating window, then reproduce with synthetic input in an isolated environment; do not enable body/traceback capture in production. The privacy regression inspects a private save containing manuscript, query and account sentinels. Configure host log rotation before pilot: proposed maximum ten MiB per file, two generations and seven-day retention. No external telemetry provider or uptime service is provisioned.

Check process liveness, disk, database size and health outside the public application with operator-owned monitoring. Investigate sustained 5xx, repeated database-busy 503, rate-limit spikes or failed health. Stop intake before database size reaches forty-eight MiB or private disk free space becomes uncertain; snapshot/recovery refuses databases above sixty-four MiB to keep this pilot operation bounded. Audit events grow with saves and do not auto-expire, so this manual size check is required. A larger archive needs a reviewed retention/storage/recovery change. No guarantee of automated alerting exists yet.

## Backup and restore

Backups contain private submissions, account hashes, sessions, decisions, reports and audit. They are never public web assets. Use a private operator-owned mode-0700 directory outside every static/document root, with encrypted disk and approved encrypted off-host copies. Snapshot files are mode 0600. A default proposal is daily snapshots while active, seven daily generations and four weekly generations, plus a pre-migration snapshot; approve actual retention and verify encrypted copies before intake. No cloud storage or encryption key has been provisioned by this work.

```sh
.venv/bin/python manage.py backup_archive /APPROVED_PRIVATE_DIRECTORY/snapshot-UNIQUE.sqlite3
.venv/bin/python manage.py restore_archive /APPROVED_PRIVATE_DIRECTORY/snapshot-UNIQUE.sqlite3 /APPROVED_PRIVATE_DIRECTORY/restored-UNIQUE.sqlite3
```

Use new unique filenames; the commands refuse existing files and symlinks. SQLite's online backup creates a consistent bounded in-memory snapshot, then writes through a held exclusive/no-follow file descriptor, verifies current tables/columns/migrations/triggers/digests/foreign keys, fsyncs file and private parent, and reports SHA-256. Store that hash in the separate confidential backup ledger and compare it before any restore; an integrity check alone does not authenticate a backup. The private parent must be owned by the current operator and mode 0700. The host operator remains trusted.

Restore produces a separate verified candidate, clears sessions/rate buckets, pauses intake and appends a recovery event. It never switches the running service. Keep the candidate offline. Record source revision/migration/hash, backup time, recovery-point data-loss interval and duration. Reconcile all withdrawals, safety/privacy takedowns, account deactivations and moderator revocations since the snapshot against the confidential operator log before any serving cutover. An older valid snapshot can otherwise resurrect withdrawn content or access. Also reconcile post-snapshot submitted work and tell affected contributors only through separately approved communication.

With the candidate configuration, run checks, migration-state inspection and a private/public/withdrawal/export smoke test; compare exact publication digests and decision history, and verify sessions are gone and intake paused. Shut down the writer before an approved cutover, retain the old DB and backup, use a controlled configuration/path switch, then test the actual host before reopening intake. Never copy a live SQLite DB file without its transaction state, overwrite the running database during a drill, or change database paths while a process is running.

The automated drill uses fresh isolated files with a partial private draft, private decision/appeal/report, published v1/v2, a second visible publication, withdrawal tombstones, accounts, audit and sessions. It verifies restored reader/owner boundaries, exact digests, session invalidation and pause. Schema corruption, disabled triggers, missing auth junctions, unsafe destinations, symlinks and migration upgrade/reversal are regressions. This is local recovery evidence; real encrypted off-host retrieval, hardware failure and actual operator cutover remain acceptance gates.

## Retention, privacy requests and export

Authors can export their submission, decision explanations and appeal responses from their private workspace. Public versions have separate metadata exports; withdrawn versions export tombstone metadata only. No public account directory or contact address is exposed. Account identity and private exports must be protected independently of public byline. Do not promise erasure of publicly downloaded material.

The proposed policy distinguishes private drafts/declines, published records, confidential decision/audit records, reports, sessions, operator logs and backup generations. Exact periods need founder/specialist adoption before collection. Expired sessions can be removed with the framework clearsessions command; rate buckets expire and are cleaned on subsequent writes. Private draft deletion, identity erasure, audit redaction and legal holds are not automated features. Immutability triggers intentionally block ordinary deletion of publication/decision/audit records. Handle a requested erasure through a separately reviewed, backed-up operator maintenance plan that reconciles rights, safety, retained evidence and backup expiry; do not claim that accepting a request has already purged every copy.

Keep the intake gate closed until the approved retention commitments can be honored by an exercised manual procedure or a tested tool. If a request cannot be met, state the actual limitation to the human owner before collecting more data. Never run ad-hoc destructive SQL or disable triggers during normal moderation. A future retention issue must specify redaction versus deletion, publication tombstones, audit minimization, legal holds, backup expiry and restore reapplication; it is not silently solved by this runbook.

## Costs and weekly decision

Record actual host, domain, backup, monitoring, email if later adopted, incident/specialist spend and operator minutes. No hosting spend or vendor quote is established; no payment or provider agreement is accepted. Runtime model and artifact-storage charges are excluded by design, not a promise of zero operating cost. Use the requested actual monthly cap once approved; reduce scope or pause before exceeding it. Count unpaid founder effort honestly.

Weekly review the pilot measures: completion time, interruptions/stale saves, oldest/median queue age, moderation effort, corrections, report/appeal burden, accessibility barriers, concrete reuse/return visits and actual costs. Reviewer participation is unavailable for this release; record consenting interest only after authorized outreach, never fabricate a review count. Treat a small sample as exploratory. Publish only safe aggregate findings through an approved communication path.

## Deployment, rollback and wind-down

The selected Vercel target requires an approved managed PostgreSQL provider and region, separate runtime/migration roles, verified TLS, isolated previews, serialized operator-run migrations, provider backup/PITR and a separate-target restore drill. Do not run SQLite backup helpers there, embed migrations in the build, share production credentials with previews, or infer that Vercel rollback reverses database writes. No Vercel project, hosted database, domain or cost cap has been approved. Review [VERCEL.md](VERCEL.md) and record actual host/log/proxy/connection-pool behavior before acceptance.

Deploy examples are candidates, not an applied service. Use one non-root application user, private persistent DB and secret environment, collected static files only, loopback Gunicorn and an explicitly reviewed nginx TLS front end. nginx must overwrite scheme headers and never serve var or repository source. Gunicorn trusts only loopback scheme normalization; Django does not accept arbitrary proxy headers. Check actual host/proxy request limits, cookie security, bad Host rejection, log redaction, invalid HTTP/TLS, error rates, file permissions and restart persistence. Run check --deploy with production settings and record the exact head actually served. Do not use the local development key or LOCAL_DEVELOPMENT outside loopback.

Every migration needs a pre-migration snapshot and schema/data compatibility review. Tested migrations 0002→0004→0002→0004 preserve existing publication content and all six append-only triggers, but reverse removal of newly added conflict/appeal metadata can discard that metadata. Prefer forward repair or restore the matching release with a verified database snapshot; do not call schema reversal a lossless rollback. Published stable IDs and withdrawal status must survive. A new incompatible release needs its own restore drill.

If the founder cannot sustain the service, pause intake, inventory pending decisions/reports/appeals and obligations, prepare an unsent notice for approval, offer a defined export window through approved contacts, stop new collection, and agree whether a minimal static tombstone/citation record can be maintained. Document retention/deletion and backup expiry, off-host access/key ownership, outstanding privacy/safety actions and costs. Do not disappear behind a green test result, silently delete citations or imply a successor operator exists.
