# Vercel hosting candidate and approval packet

## Canonical staging candidate — 2026-11-08

The combined staging candidate and its current evidence are tracked in [STAGING_REQUIREMENTS_20261108.md](STAGING_REQUIREMENTS_20261108.md), [the qualification receipt](evidence/STAGING_CANDIDATE_20261108.md), [the actual Neon dossier](NEON_CONTRACT_20261108.md) and [the consolidated execution request](STAGING_EXECUTION_REQUEST_20261108.md). Main remains `bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4`; PR #34/#36 are separate drafts. Canonical source publication is explicitly authorized; earlier publication holds below do not apply to this owned candidate. Final combined-head CI, artifact verification and published-head review are completion gates recorded in its draft PR.

The selected Neon resource already exists and read-only SQL verifies PostgreSQL 18.6, administrative owner membership and one-day history. No restricted application identity or seven-day history is qualified. The legacy pooler flag is deprecated, so it does not prove pooling is unavailable. Actual WorkOS exchanges now validate and correctly reject the unbound founder with 403; account enrollment, completed app login/logout, protected hosting, provider/off-host recovery and human/policy acceptance remain separate. No provider write, secret transfer, deployment, spending or intake activation is included. Full pilot stays NO-GO with `PILOT_APPROVED=0`, paused intake, unavailable reviews/vouches and disabled reputation.

The dated material below is retained historical evidence. Use the linked current matrix for superseded source, resource-absence, credential-absence, missing-choice and execution-authority statements; earlier passing revisions do not qualify this candidate's changed head.

Status: hosting target selected by the user; deployment, project creation, database provisioning, purchases, new persistent credentials, real intake, invitations, and launch remain unapproved. Updated 2026-11-06: the user selected existing `0xbuns/psyche-research` for protected synthetic staging only. Its ID is `prj_KpONwA0jddpWRBIVQGt22FbZX7t2`; the selection is not deployment or resource-execution approval. This packet keeps the existing Django application and its server-rendered workflow. It does not authorize a platform rewrite or claim a Vercel deployment exists.

[STAGING_ACCEPTANCE.md](STAGING_ACCEPTANCE.md) supplies the current source/CI checkpoint, a concrete but unapproved staging proposal, provider/protection recommendations, execution sheets, cost/recovery objectives and missing target/operator decisions. Use it to resolve the actual identifiers and prepare one consolidated staging request; this document remains the environment and operational contract.

## Target architecture

Use the repository's `manage.py`, `config.wsgi.application`, templates, static files, domain services, and migrations. The Vercel-specific entrypoint is `config.wsgi:application` in `[tool.vercel]`; no frontend framework or service split is needed. Vercel's current Django guide describes `manage.py` detection, WSGI entrypoint discovery, automatic static collection, and environment-based database configuration. See [Vercel Django documentation](https://vercel.com/docs/frameworks/full-stack/django), checked 2026-11-04. These documented capabilities are not evidence that this repository's build has passed on Vercel.

Hosted state must live in an approved managed PostgreSQL database. SQLite remains a local development and isolated test option only; it must not become a Vercel persistence strategy or a silent fallback when the hosted database variable is missing. Do not place an SQLite database, private export, backup, submitted content, or mutable operational state in a deployment bundle or static directory. Author artifacts remain external references; arbitrary uploads and remote previews stay unavailable.

Keep the founder workflow unchanged: contributor accounts supplied by an operator, private drafts and frozen submitted snapshots, explicit `moderators` group, human decisions, immutable published versions, moderated corrections, withdrawal tombstones, private reports and appeals, and finite intake. PostgreSQL and Vercel must preserve those guarantees rather than merely render the landing page.

## Candidate details still requiring approval

| Item | Concrete proposal | Current decision/evidence |
| --- | --- | --- |
| Source and application | `OpenCoven/psyche-research`, reviewed Django release revision recorded in the delivery evidence. | Repository is known; exact deployable revision must be frozen and verified. |
| Hosting platform | Vercel native Django/Python deployment. | User-selected target; no project or deployment approval inferred. |
| Team and project | A founder-owned Vercel team/project with a known access list and production branch. | Existing `0xbuns/psyche-research` is user-selected and verified by read-only CLI. Git link is null; automatic Git deployments stay disabled. Confirm billing/audience and authorize the exact execution scope separately. |
| Public domain | One explicitly approved canonical domain, with any preview hosts separately scoped. | Existing platform domain is `psyche-research.vercel.app`. All Deployments protection and the exact generated/alias allowlist need execution approval and actual verification; no custom DNS is selected. |
| Database | Managed PostgreSQL with TLS hostname verification, supported version, bounded connections, backups and a tested recovery route. | Provider, account, plan and credentials unselected; do not choose, purchase, or create them without approval. |
| Region | One approved application region close to the approved database region, subject to privacy/residency requirements. | No region or residency commitment selected. |
| Preview | Isolated protected preview with synthetic data and a separate PostgreSQL database and secrets. | No preview resource exists or is approved by this document. |
| Migrations | Reviewed one-off operator run from the exact release using a separate migration role. | Runner, approver and maintenance window unknown. |
| Backups | Provider recovery plus a verified logical export/restore route into a separate target, with encrypted restricted copies and expiry. | No hosted backup, PITR entitlement, restoration target, RPO or RTO verified. |
| Operator and contact | Named founder with actual monitoring schedule, escalation route and safe public contact. | Contact, real availability and any cover not approved. |
| Spending | Founder-approved monthly ceiling, billing owner and alert/pause thresholds covering hosting and database separately. | No monetary cap or vendor cost estimate approved. |
| Pilot activation | Approved policies and gates, then a separate human decision to enable the bounded pilot. | `PILOT_APPROVED=0`, intake closed, NO-GO. |

No free-tier, workload capacity, regional availability, backup retention, support, compliance, or price claim is made here. Before choosing resources, obtain current primary provider details for the exact plan and region, record the estimate and who pays, and obtain approval of that concrete scope. Relevant cost drivers are function execution, request and data transfer, build usage, database compute/storage/connections, backup/PITR and restore targets, monitoring retention, and operator time.

## Environment contract

Set project-specific configuration in the approved Vercel environment controls, with secrets restricted to the intended environment and authorized people. Production, Preview, and Development must have different database and session secrets. Vercel documents environment scopes and notes that changes apply to new deployments; inspect both scope and deployed revision when rotating. See [Vercel environment variables](https://vercel.com/docs/environment-variables), checked 2026-11-04. Do not pull production variables into repository `.env` files, log them, paste them into issues, or commit an exported environment.

The table was checked against the current local `config/settings.py` and `config/database.py` on 2026-11-04 and must be checked again at the exact release revision. It records expected values, never real secret values. Platform-provided variables are not substitutes for deployment authorization.

| Variable | Hosted production value | Preview/development boundary | Secret and handling |
| --- | --- | --- | --- |
| `DJANGO_SECRET_KEY` | Independently generated random value of at least 50 characters; never the development fallback. | Different value for every approved environment; do not share production sessions with previews. | Secret; provision and rotate only through approved controls. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated explicit canonical hostname(s), without scheme, path or wildcard. | Only the exact approved preview hostname(s) for that environment. | Configuration; never accept an arbitrary request host or wildcard to make a build pass. |
| `DATABASE_URL` | PostgreSQL URL with approved runtime role, database and hostname; the only permitted query key is `sslmode`, set to `verify-full`. | Preview uses a different database/role and the same hosted TLS requirement. A disposable local PostgreSQL CI service may disable TLS only with explicit local development mode. | Secret; percent-encode URL credentials, never echo the URL on parse or connection failure. |
| `LOCAL_DEVELOPMENT` | Absent or `0`. | Must also be absent or `0` on Vercel previews. `1` is for local tools and disposable tests only. | Configuration; never enable local shortcuts on a hosted target. |
| `PILOT_APPROVED` | `0` until a recorded founder go/no-go approves the exact pilot. | `0` on ordinary hosted previews. A separately approved synthetic rehearsal must not enable real intake. | Configuration; an environment value is not itself evidence of founder approval. |
| `VERCEL` | Platform-provided `1` on actual Vercel deployment. | Use platform value only on actual Vercel previews; do not spoof it on an unrelated proxy. | Platform configuration; selects the reviewed hosting boundary, not publication authority. |
| `DATABASE_PATH` | Unset and unused. | May identify a private local SQLite file only outside Vercel when local development is explicit. | Local path; must not point hosted writes at ephemeral files. |
| `PGSSLROOTCERT` | Normally unset when the approved provider chains to the runtime's verified system trust; otherwise an approved accessible CA-bundle path. | Preview must independently validate its database certificate chain. | Trust configuration, not a database credential; no weakening of `verify-full` to hide certificate failure. |

The PostgreSQL settings use `connect_timeout=10`, a 10-second statement timeout, a 5-second lock timeout, `CONN_MAX_AGE=0`, and `prepare_threshold=None` for the selected driver. The default root-certificate setting is `system`, with the approved `PGSSLROOTCERT` path override described above. These are code settings, not additional supported URL query parameters. Do not append arbitrary pool, timeout, CA, or driver arguments to `DATABASE_URL`; the parser deliberately accepts only the stated query key. A provider requiring other connection configuration needs a reviewed code change and tests rather than a silent bypass.

TLS must validate both the certificate chain and the database hostname. PostgreSQL's `verify-full` mode performs those checks; a provider-specific CA may be necessary. See [PostgreSQL client SSL verification](https://www.postgresql.org/docs/current/libpq-ssl.html), checked 2026-11-04. Verify that the pinned driver/libpq and the actual Vercel runtime support the configured trust mode, and test a wrong-host or untrusted-certificate rejection. A connection that happens to succeed does not prove the intended validation was active.

## Database region, pooling, and roles

Select the database provider and region only after founder approval of privacy, cost, recovery, and operational terms. The application region should be deliberately configured near that database rather than scattered across regions by habit. Record the actual function and database regions, latency, residency implications, and any failover behavior. Vercel documents configurable function regions; this is not a promise that a particular region or plan is available. See [Vercel function region configuration](https://vercel.com/docs/functions/configuring-functions/region), checked 2026-11-04.

Use a provider-supported pooled runtime endpoint when appropriate for the approved workload, and a direct endpoint for controlled migrations and recovery where the provider requires it. Record pool mode, maximum connections, startup-option support, idle and request limits, and what happens under exhaustion. Django documents request connection lifetime and transaction-pooling caveats; our zero persistent lifetime is an application choice, not proof that any vendor pool is compatible. See [Django 5.2 database guidance](https://docs.djangoproject.com/en/5.2/ref/databases/), checked 2026-11-04.

Test the actual endpoint with the chosen timeouts, prepared-statement setting, transaction boundaries and locking. If a pool rejects startup parameters, session behavior, or the runtime configuration, stop and resolve the provider-specific contract explicitly. Do not remove timeouts, certificate verification, or atomic capacity controls merely to obtain a successful connection. Measure bounded bursts and recovery after idle connections and temporary outages before trusting a connection limit.

Use a dedicated migration role with only the ownership/DDL needed to apply reviewed migrations and a separate runtime role with only necessary application table/sequence operations. The runtime must not create roles, grant privileges, own the database, or perform ordinary schema migrations. An approved backup role needs access sufficient for a complete backup and its own restricted handling. Confirm the provider actually supports the proposed role separation; a plan that only exposes a privileged owner credential leaves this gate unresolved.

Do not make a migration credential a Vercel build variable, application runtime secret, branch-preview secret, or general CI credential. Account provisioning and moderator grants remain explicit audited operator actions; neither initial migrations nor a deployment should silently create real participants, moderators, public research, or endorsements. Keep intake closed while establishing the environment.

## Build and migration sequence

No deployment or provisioning command in this section has been executed by this document. After the target and resources are explicitly approved, use the exact reviewed source revision and dependency lock/hashes. Confirm the Python version supported by the deployed runtime and selected driver, and retain build logs with secrets and content redacted.

Vercel's automatic Django/static build should collect only application-owned static files. Do not put `migrate`, fixtures, account provisioning, database resets, intake opening, provider provisioning, or any publication action in `pyproject.toml`, a Vercel build command, import-time code, or request startup. A branch push or repeated preview build must not write a production schema. Production build code is privileged by the secrets it can read; only trusted reviewed source may receive production configuration.

For each release needing schema changes, the human operator takes a verified backup, rehearses the migrations on a separate database with appropriate synthetic fixtures or an authorized restricted copy, and reviews the migration plan and backward compatibility. The actual one-off runner receives the migration role through an approved secret channel, checks the intended host/database using non-secret identifiers, and runs the following against the approved target only:

```sh
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py check --deploy --fail-level WARNING
```

Record the exact source revision, applied migration IDs, command exits, first failures, retries, duration and operator. Never print the connection URL to prove the target. Switch the serving application only after migration compatibility and the rollback plan are established, then run the actual hosted smoke path with intake closed. A successful build is not evidence that a database migration or human publication succeeded.

The one-off runner's `DATABASE_URL` uses the migration role and is not copied into the runtime environment. The serving deployment receives the runtime URL only. If configuration checks cannot import without the correct database contract, supply approved environment configuration to that runner; do not enable `LOCAL_DEVELOPMENT=1` as a hosted workaround.

## Preview isolation

Every hosted preview needs a separate approved database or a demonstrably isolated provider branch with separate credentials, no production private material, and no production migration role. Do not restore production drafts, decisions, appeals, reports, contacts, session records, or backups into a public preview. Use clearly labeled synthetic fixtures in a restricted rehearsal, and never make fabricated research appear to be real public archive activity.

Protect preview access and verify the actual protection scope, exact URL, team permissions, share/bypass mechanisms and any automation access. Vercel offers deployment protection settings, but this packet does not assume an entitlement or claim that a created preview is private by default. See [Vercel deployment protection](https://vercel.com/docs/deployment-protection), checked 2026-11-04. Application authentication and ownership checks remain necessary even when a platform gate exists.

Do not inject production variables into all non-production branches, forks or untrusted preview builds. Confirm integration-created variables have the intended environment scope before connecting any database integration. The same restriction applies to branch-specific overrides and later secret rotations. Delete temporary preview data/resources under the approved lifecycle plan after the rehearsal, without deleting retained evidence or a resource another owner is using.

## PostgreSQL backup and recovery gate

The repository's SQLite `backup_archive` and `restore_archive` commands are local SQLite tools. Their passing tests, digests, or restored files do not prove hosted PostgreSQL recovery. Do not run them against a hosted PostgreSQL URL or copy a Vercel filesystem as a database backup.

Before real intake, select and verify the provider's actual backup/PITR entitlement, retention, encryption and access controls, region, restore target options, failure alerts, deletion handling and charges. Record a founder-approved recovery-point objective and recovery-time objective, then measure them in a restore drill. A dashboard saying backups are enabled is insufficient evidence that the operator can restore the right data privately.

Maintain a tested logical export route where supported. PostgreSQL documents `pg_dump` as a consistent logical snapshot and `pg_restore` for archive formats. See [PostgreSQL SQL dump documentation](https://www.postgresql.org/docs/current/backup-dump.html), checked 2026-11-04. Choose compatible client/server versions and approved privileges, protect the resulting dump as private data, and include schema, migration records, auth, sessions if retained, submissions, versions, decisions, events, appeals, reports and capacity state in verification.

Use an approved runner whose libpq connection variables or secret service configuration are injected without placing a URL/password in command arguments, source files, chat or logs. The following commands illustrate the intended operation; the operator must select the source connection for the dump and then a different, fresh approved restore target before the restore. The path is a placeholder, and no target is created by this example.

```sh
umask 077
pg_dump --format=custom --no-owner --no-acl --file /approved/private/path/archive.dump
pg_restore --list /approved/private/path/archive.dump
pg_restore --exit-on-error --single-transaction --no-owner --no-acl --dbname archive_restore_drill /approved/private/path/archive.dump
```

Re-establish intended ownership and grants on the restore target through the approved role setup, since the sample deliberately omits source ownership/ACL replay. Validate counts and foreign keys, exact snapshot digests, migration state, account/role behavior, private sentinel exclusion, queue limits, published histories, pending corrections, appeals and withdrawal suppression. Never point a restore drill at the serving database or treat an in-place destructive test as necessary evidence. Confirm that restored sessions, deleted records, restricted data and old credentials are handled according to the adopted recovery and retention policies.

After restoring to the explicitly approved separate target, keep every serving process disconnected. The offline runner can use `prepare_restored_archive` only with `RECOVERY_MODE=isolated-restore`, `VERCEL` absent, and explicit expected host, port and database identifiers matching the approved endpoint. It also checks PostgreSQL's connected database name. These identifiers express intended isolation; they do not stop a live process or prove the operator chose the correct resource. The command verifies the archive and atomically revokes sessions, clears rate buckets, pauses intake and records an operator-reason event. Verification or audit failure rolls back its changes and emits a redacted error. It does not restore data, change a serving target, repair role grants, or certify safety.

```sh
RECOVERY_MODE=isolated-restore python manage.py prepare_restored_archive \
  --expected-host APPROVED_RESTORE_HOST \
  --expected-port 5432 \
  --expected-database APPROVED_RESTORE_DATABASE \
  --reason 'Approved isolated recovery drill reference'
```

Keep connection credentials in the approved runner's environment or secret service, never in those arguments or logs. Reconcile every withdrawal, privacy/erasure decision, account deactivation, password compromise and moderator revocation since the snapshot against the current confidential operator record before any cutover. Restored data can resurrect access or unsafe content even when every digest and schema check passes. The CI logical-recovery test uses only synthetic records, a dedicated test database and a new generated restore database; it proves the exercised dump/restore path, not a managed provider's backup service, PITR, encryption or real operating access.

Logical dumps do not establish point-in-time recovery. PostgreSQL's continuous-archiving procedure relies on a base backup and the necessary WAL history; provider PITR must be tested through the provider's documented mechanism. See [PostgreSQL continuous archiving and PITR](https://www.postgresql.org/docs/current/continuous-archiving.html), checked 2026-11-04. If the selected plan lacks PITR, document the actual backup window and obtain acceptance of that limitation; do not advertise PITR from a successful `pg_dump` round trip.

A practical drill restores into a separate approved database, opens it only through an isolated application, verifies private/public behavior, records elapsed time and data-loss boundary, and proves the operator can recover access without relying on a lost serving function. Keep a restricted encrypted off-host copy if that is part of the accepted plan, verify its recoverability and expiry, and record remaining gaps. No hosted drill is claimed here.

## Hosted verification and rollback

Run actual production-configuration checks, clean migrations and migration rehearsal, PostgreSQL product and concurrency tests, backup restoration, and an independent technical review at the release revision. Re-run product guarantees against the hosted preview and actual database/pool, including final-slot races, duplicate decisions, correction races and withdrawal reads. A SQLite suite or mocked URL parser cannot prove PostgreSQL locking or serverless retry behavior.

Verify HTTPS without redirect loops, canonical and hostile host handling, trusted proxy assumptions, secure/HTTP-only session cookies, CSRF origin behavior, login/logout, request/body and field limits, actual client rate-limit behavior through Vercel, no shared caching of private pages, security headers, static-file delivery, safe errors and redacted logs. Do not trust arbitrary `X-Forwarded-For` input to fix anonymous throttling. Confirm how the real platform supplies client identity and record any additional reviewed change required.

Observe the actually rendered current browser at desktop and narrow widths. Exercise saved draft resumption, stale-edit error recovery, queue moderation, publication, correction and withdrawal with clearly labeled isolated synthetic data, then remove that data from any environment intended for real intake. Complete the human keyboard and screen-reader acceptance specified in the pilot plan; automated checks alone are insufficient.

For rollback, pause intake first and assess schema compatibility. Reverting a Vercel application deployment does not undo migrations or recover lost data. Prefer a previous compatible application revision when safe; otherwise use the approved backup or provider recovery route to a separate target and explicitly account for writes since the recovery point. A human authorizes any data switch, destructive replacement, secret rotation, DNS change or service shutdown, with preserved incident and recovery evidence.

## Approval and prerequisite checklist

- [ ] Verify the current repository/branch/revision, ownership, open work, CI terminal results and independent technical findings; freeze a concrete deployment candidate.
- [ ] Verify the founder-owned Vercel team/project, access list, plan, billing owner, build/production branch behavior, exact domain and allowed hosts; obtain approval before creating or connecting resources.
- [ ] Approve a specific managed PostgreSQL provider, version, region, endpoint/pool mode, role capabilities, recovery features and cash cap; obtain approval before purchase or credential creation.
- [ ] Approve app/database regions, privacy/residency and processor terms, monitored operator contact, actual founder schedule and fallback route.
- [ ] Provision separate runtime, migration, backup and preview access only through approved mechanisms; verify TLS chain/hostname, timeout/pool compatibility and secret scopes without exposing values.
- [ ] Ensure every preview is protected, isolated and synthetic, production secrets stay out of previews/untrusted builds, and builds perform no migrations or production data writes.
- [ ] Rehearse clean and upgrade migrations, PostgreSQL state and concurrency guarantees, provider backup/export and restoration into a separate target; record actual failures, fixes and recovery limits.
- [ ] Verify hosted proxy/session/CSRF/host/rate/cache behavior, monitoring without content leaks, rendered responsive UI and human accessibility acceptance.
- [ ] Adopt dated policies and content-license choices; confirm retention/deletion behavior and a real monitored report/appeal contact.
- [ ] Present exact target, audience, source revision, domain, resource plan, costs, secrets/roles, remaining risks, verification and rollback as the concrete deployment approval request. Hosting preference alone does not satisfy it.
- [ ] After explicit deployment approval, keep `PILOT_APPROVED=0` and intake closed while verifying the deployed result. Record separate founder go/no-go before real intake, and separate outreach authorization before invitations.

Until every required gate has evidence and the applicable human decisions are recorded, the honest state is a locally prepared candidate for Vercel with hosted operation and pilot activation unverified. Continue safe implementation, local PostgreSQL testing, review and issue maintenance without implying permission to deploy or open the archive.
