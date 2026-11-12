# Selected Neon contract: read-only inspection

This dossier records actual inspection of existing project `noisy-snow-11090716`; it is not provider acceptance or execution authority. The [sanitized receipt](evidence/staging-neon-contract-20261108.json) identifies observation time, API/catalog scope and limitations. No password or connection string was retrieved. The authenticated MCP server remains `readonly=true`; no alternative interface was used for writes.

## Resource and database identity

| Property | Verified observation |
| --- | --- |
| Marketplace resource | `store_3SQQeILRV76itKkX`, already created on 2026-11-06; do not create again |
| Neon project / organization | `noisy-snow-11090716` / `org-broad-bonus-12722634` |
| Name / plan / region | `psyche-research-synthetic-20261106` / Launch `launch_v3` / `aws-us-east-1` |
| Source branch / compute | `br-rapid-snow-bcykarsv` (`main`) / `ep-dry-dream-bcyl2d48` |
| Actual SQL server | PostgreSQL `18.6 (ac70818)`; API major 18 |
| Database / owner / inspected session | `neondb` / `neondb_owner` / `neondb_owner` |
| Public schema owner | `pg_database_owner` |
| Filtered relation count | Zero outside system schemas for ordinary/partitioned tables, views, materialized views, sequences and foreign tables; not proof of absence of every object type |
| Endpoint sizing | Minimum = maximum 1 CU; API timeout 0 denotes project/provider default, not a measured always-on compute |
| History | 86,400 seconds (one day); selected seven days not configured |
| Snapshots / snapshot schedule | Empty list / empty schedule at inspection; PITR history is a separate facility |
| Network posture | Empty IP allowlist; public connections not blocked; no claim of founder-only infrastructure access |
| Read-only SQL scope | Metadata-only catalog SELECT; `transaction_read_only=on`; no application content |

The SQL session's owner has CREATEDB, CREATEROLE, REPLICATION and BYPASSRLS, is not a PostgreSQL superuser, and has effective membership including `neon_superuser`, `pg_read_all_data`, `pg_write_all_data` and `pg_database_owner`. Provider login roles `cloud_admin` and `neon_service` are also visible. No restricted runtime/migration/backup login was present in that result. The owner credential is unsuitable for application runtime. A displayed NOSUPERUSER flag does not negate administrative membership; [the proposed SQL-created role contract](DATABASE_ROLES.md) requires effective-membership and denial checks.

## Endpoint, TLS and pooling contract

The direct host is `ep-dry-dream-bcyl2d48.c-16.us-east-1.aws.neon.tech`; the API also returns pooled host `ep-dry-dream-bcyl2d48-pooler.c-16.us-east-1.aws.neon.tech`. No credential is included here. Current [Neon API documentation](https://neon.com/docs/reference/api/endpoints/update-project-endpoint) marks both `pooler_enabled` and `pooler_mode` deprecated: pooling is selected through the `-pooler` hostname. The returned legacy `pooler_enabled=false` is not evidence that pooling is disabled, and no flag change is proposed. This corrects the initial goal's provisional observation.

The prior independent owner continuation recorded certificate-chain and hostname verification on both public endpoints using PostgreSQL SSLRequest: TLS 1.3 / TLS_AES_256_GCM_SHA384, certificate expiry 2027-01-20. Startup options reached SASL authentication without credentials or SQL. These are transport/pre-authentication observations, not authenticated driver, transaction-pool, runtime-role or recovery acceptance; [issue #9](https://github.com/OpenCoven/psyche-research/issues/9) retains their provenance. An MCP backend `pg_stat_ssl.ssl=false` observation concerns a different connection leg and does not contradict external endpoint TLS.

The existing Django parser requires production `sslmode=verify-full`, system/explicit trusted CA roots, no persistent Django connections (`CONN_MAX_AGE=0`), disabled psycopg prepared statements and bounded connect/statement/lock timeouts. Its PostgreSQL startup options and real application transactions still need authenticated tests on both direct and pooled endpoints. Use direct connections for serialized migration, dump and restore; qualify the pooled runtime separately before selecting it. Do not relax TLS or suppress failed compatibility checks.

## Query history and consumption

The earlier native-console query was submitted once and showed Connecting before the page changed. A later owner inspected History and found its text but no verified result. Its outcome remains unverified; it was not blindly replayed. Later native and MCP catalog reads were distinct completed statements. This dossier's new metadata SELECT does not retroactively qualify the old execution.

The daily project consumption response for November 1–9 contains 2,620 CU-seconds, 1,916,574 root byte-month, 230,589 instant-restore byte-month and 59,705 network bytes. The current period is November 1–December 1. Current-day data can lag; missing metric entries do not prove zero, and this is neither an invoice nor total account cost. At the [current Launch compute rate](https://neon.com/pricing) of USD 0.106/CU-hour, the returned compute component is approximately USD 0.0771 before other charges, tax or account adjustments. The [execution worksheet](STAGING_EXECUTION_REQUEST_20261108.md) reserves future usage and requires billing readback before spending.

Actual restricted-role provisioning/grants, seven-day history, authenticated direct/pool behavior, provider timestamp recovery, encrypted off-host retrieval and measured RPO/RTO remain unrun. Keep intake paused and pilot NO-GO.
