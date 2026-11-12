# Database role contract rehearsal

This is a reviewable local proposal for issue #9, not an executed hosted grant plan. The synthetic fixture is [rehearse_database_roles.py](../archive/tests/rehearse_database_roles.py); [the dated receipt](evidence/DATABASE_ROLES_20261108.md) records its scope. The frozen input received independent review and the canonical isolation corrections received a further scoped review; final published-head review and exact-head CI remain required. Do not create provider roles or install these grants on the selected database on the strength of this local receipt.

The actual selected Neon database was observed on 2026-11-08 running PostgreSQL `18.6 (ac70818)`. Its `neondb_owner` login had `CREATEDB`, `CREATEROLE` and `BYPASSRLS`; no separate runtime, migration or backup login appeared in that catalog result. The public table count was zero. These observations do not establish all-schema emptiness, effective privileges of future identities, pooling compatibility or recovery acceptance. Live issue #9 retains the provider receipt.

## Canonical invocation and hosted staging proposal

Use `python -I -B archive/tests/run_database_role_rehearsal.py` with the explicit trusted bin directory, expected major, committed source and a fresh output path; see [the canonical receipt](evidence/STAGING_CANDIDATE_20261108.md). Do not invoke the underlying fixture directly from an ambient operator shell. The original input SHA-256 is `389ef4c1307b77c7039a4d0e2662d4a1a01f6325e1edfc4cba3152e449e89a3b`; canonical isolation and grant-actor corrections produce `c9040c22d1f009b62d62d00c444341a5dc4584c98d6eea233f08a93c6b488307` and 29 checks. Historical direct-script receipts below assume their recorded known-clean environments.

For the separately approved hosted setup, use `neondb` only on source branch `br-rapid-snow-bcykarsv` after verifying exact resource/database/owner and absence of unexpected roles, relations and user functions. Stop on a collision or incompatible managed-provider ownership; do not transfer system ownership. The operator/database owner creates purpose roles as NOLOGIN and applies only its database/schema grants below. The operator is not assumed to be a PostgreSQL superuser or a member of the purpose roles. Securely activate the migrator first; then authenticate as that exact migrator to set its own database-local function defaults before migrations/restore and to grant access to its own objects afterward. Activate runtime/backup only after those grants. LOGIN activation and credential setting are separate secure operator steps in [the execution request](STAGING_EXECUTION_REQUEST_20261108.md), not commands for the public console. Reapply database-local defaults before object creation independently on both restore targets. No grants are executed by this document.

```sql
CREATE ROLE psyche_migrator NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE psyche_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE psyche_backup NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
REVOKE ALL ON DATABASE neondb FROM PUBLIC;
GRANT CONNECT ON DATABASE neondb TO psyche_migrator, psyche_runtime, psyche_backup;
-- As database/schema owner, connected to this exact neondb:
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO psyche_migrator;
GRANT USAGE ON SCHEMA public TO psyche_runtime, psyche_backup;
```

After secure migrator activation, assert `current_user = psyche_migrator` and `current_database() = neondb` in its authenticated connection, then run its own default policy before migrations or restore. No administrative or inter-role membership is needed:

```sql
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
```

Run serialized reviewed migrations as the migrator, then issue the exact table/sequence grant block below in that same object-owner identity. The owner role's broad read/write memberships alone do not confer object grant authority. Inspect every resulting table/function owner and ACL, explicitly require the existing `archive_reject_append_only()` function to deny PUBLIC/runtime/backup EXECUTE and verify a fresh migration-owned probe function denies runtime/backup calls with SQLSTATE 42501. Revoke EXECUTE from PUBLIC/runtime/backup on that existing function if necessary under this approved policy; a changed default alone does not fix an old function ACL. Remove the probe before archive verification/backup. Do not grant role membership or use provider administrative access presets. Reject unexpected schemas/objects rather than silently expanding `ALL TABLES` scope. Runtime denial checks must cover DDL, role/database creation, SET ROLE, migration-history writes and immutable writes; backup must deny writes and DDL. Keep owner/migrator/backup secrets offline.

## Pooled runtime timeouts

The application sends `-c statement_timeout=10000 -c lock_timeout=5000` as a startup option to direct endpoints. Neon's transaction pooler, selected by a `-pooler` suffix on the endpoint label, rejects the `options` startup parameter, and a session-level `SET` after connecting is not reliable under PgBouncer transaction pooling because later transactions can run on different server connections. For a pooled host the application therefore omits startup options and relies on database-local defaults for the runtime role, which PostgreSQL applies whenever the pooler starts a server connection for that role and database. As the operator that created the runtime role, connected to the exact application database, set them:

```sql
ALTER ROLE psyche_runtime IN DATABASE neondb SET statement_timeout = '10s';
ALTER ROLE psyche_runtime IN DATABASE neondb SET lock_timeout = '5s';
```

Roll out in this order: apply both defaults; recycle every pooled server connection for the runtime role and database so none predates them (for example by restarting the compute endpoint; the exact Neon recycling mechanism has not been verified); only then switch the runtime `DATABASE_URL` to the `-pooler` host. Repeat the first two steps after any change to these defaults, since PostgreSQL applies them only to server connections that start afterwards.

The guarantee rests on three conditions, not on an application check: the defaults are present on every server connection in the runtime role/database pool; nothing issues a session-level `SET` of these settings, because PgBouncer transaction mode does not reset session state between clients; and every pooled server connection started after the defaults were applied. The application issues no such `SET`, but the runtime role itself can run `ALTER ROLE CURRENT_USER IN DATABASE neondb SET statement_timeout = 0`, so the runtime credential's custody is part of this guarantee.

For each new connection without the startup timeouts the application runs a fail-closed canary: unless `pg_settings` reports both values in milliseconds from source `database user`, non-zero and at most 10 and 5 seconds, it closes the connection and the request receives a database error; `/health/` returns 503. Role-wide, database-wide and session values do not satisfy it. Under transaction pooling the canary samples only the server connection that serves its own query; later transactions in the same request can use other server connections. It detects absent or out-of-bounds defaults on the sampled connection but is not a per-transaction guarantee. Hosted acceptance must therefore sample `SHOW statement_timeout`, `SHOW lock_timeout` and their `pg_settings.source` across many separate requests through the pooler after connections recycle, and require 10s/5s or tighter from `database user` in every sample.

Migrations, dumps and restores keep using the direct endpoint with startup options. `archive/tests/test_postgres.py` verifies the role-in-database mechanism and the canary against local PostgreSQL in a disposable database without a pooler; the canonical role-rehearsal fixture does not yet set these defaults, and actual Neon pooler behavior remains unverified.

## Proposed separation

| Identity | Allowed purpose | Forbidden use |
| --- | --- | --- |
| Operator/owner | Explicit reviewed role/database setup and grants | Vercel application runtime or preview secrets |
| Migration | Own and migrate reviewed application schema; restore into an explicitly separate target | Application runtime, automatic build migrations or ordinary requests |
| Runtime | Application reads and necessary row writes; sequence use | DDL, role administration, migration-history writes, immutable-record updates/deletes or assuming migration identity |
| Backup | Read all application/auth/session data needed for a consistent dump | Writes, DDL or assuming migration identity |

All three application-purpose roles in the local model use `NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS` and have no role memberships. Hosted checks must inspect both flags and membership/inheritance, including provider-managed groups; flags alone are insufficient. The backup credential can read sensitive drafts and authentication records, so its custody and encrypted dump handling remain separate operational gates. A migration identity inherently owns sensitive schema objects and belongs only in the controlled runner.

[Neon's role documentation](https://neon.com/docs/manage/roles), checked 2026-11-08, says Console/API-created roles receive `neon_superuser` membership, as do default CLI-created roles; SQL-created roles instead require selective grants. The documented CLI access presets are not this custom immutable-table contract. Any later approved execution should use reviewed SQL for these custom identities and verify effective memberships afterward, rather than create an administrative Console role and assume the displayed flags make it restricted. No provider role-creation method was exercised in this slice.

## Exact local grant sequence

The fixture creates fresh synthetic roles and databases in its own private UNIX-socket cluster. These names and passwordless local authentication are test-only. A hosted operator must first approve actual identifiers, credential delivery, managed-provider compatibility and the exact separate target; do not paste this block into a provider console as an execution instruction. Apply schema grants and ALTER DEFAULT PRIVILEGES while connected to the exact application database, verifying current_database() first. Default privileges are local to that database; applying them in postgres does not change the application database. Repeat the policy separately in each newly created restore database before pg_restore creates functions. A default-policy change does not revoke privileges on functions that already exist; inspect their effective ACLs and repair them under the approved plan.

```sql
CREATE ROLE psyche_migrator LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE psyche_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
CREATE ROLE psyche_backup LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
REVOKE ALL ON DATABASE synthetic_role_contract FROM PUBLIC;
GRANT CONNECT ON DATABASE synthetic_role_contract TO psyche_migrator, psyche_runtime, psyche_backup;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO psyche_migrator;
GRANT USAGE ON SCHEMA public TO psyche_runtime, psyche_backup;
-- Reconnect as psyche_migrator in this exact database before object creation:
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
```

Run the reviewed migrations as `psyche_migrator`, then that object-owner identity applies the following grants. The local fixture also now uses the migrator for its own defaults and object grants; earlier frozen receipts used a synthetic superuser for those administrative calls and do not prove hosted operator authority. They cover the current committed schema, including application-managed auth/session/control tables; this is a trusted application-server identity, not per-participant database authorization. Application authorization remains mandatory. No automatic future-table grants are installed: each schema change requires review and a deliberate grant refresh. Functions added later need an explicit execution policy.

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO psyche_runtime;
REVOKE INSERT, UPDATE, DELETE ON django_migrations FROM psyche_runtime;
REVOKE UPDATE, DELETE ON archive_version, archive_decision, archive_event FROM psyche_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO psyche_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO psyche_backup;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO psyche_backup;
```

Restore with compatible `pg_restore --no-owner --no-acl --exit-on-error --single-transaction` as the migration role into a newly created, explicitly isolated database. Reapply the reviewed database/schema/data grants for that target; omitted source ACLs do not recreate them. The isolated offline preparation runner can then use the runtime role's necessary row privileges to invoke `prepare_restored_archive` with `RECOVERY_MODE=isolated-restore`, no `VERCEL`, and explicit expected target identifiers. The fixture now verifies wrong-target refusal without row changes and successful session/credential/attempt/rate removal, intake pause and one audit event, while every other restored row and every source row remains unchanged. This does not establish a full hosted recovery drill or authorize serving restored data. Follow [VERCEL.md](VERCEL.md) for credential rotation, post-snapshot access/withdrawal reconciliation, private sentinel checks and the recovery acceptance gate.

## Required provider acceptance

The frozen fixture passed 28 checks locally on PostgreSQL 16.15 and 18.6; the canonical isolated-launcher version passes 29 checks on both. These are different fixture identities and historical receipts are not evidence for the changed isolation policy. Before approving hosted grants, independently review the proposal and verify the actual restricted identities, effective memberships, schema ownership and denied-DDL behavior against the approved Neon target. Separately verify direct and pooled endpoints with `verify-full` TLS, compatible PostgreSQL 18 dump/restore clients, the seven-day recovery setting, encrypted off-host custody, a separate restore target and measured RPO/RTO. Verify that the existing append-only function has the migration owner and no PUBLIC/runtime/backup EXECUTE, then create a harmless migration-owned probe function and require runtime and backup calls to fail with SQLSTATE 42501 in both the source and restore databases. Remove the probe before taking or verifying the archive. Local PostgreSQL over a private socket proves none of these provider properties. Retain actual WorkOS, inherited hosting-team access, policy and human operating acceptance as separate gates; intake stays paused and the pilot stays NO-GO.
