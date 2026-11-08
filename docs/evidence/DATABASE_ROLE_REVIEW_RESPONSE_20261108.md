# Database-role independent review response — 2026-11-08

The owner adopted two independent P2 findings against fixture SHA-256 `1858dd2bf27fac5867df80f8c0c90b7b1e24d7355cefdcfb74f77fb53370fc32`. The [cleanup review](https://github.com/OpenCoven/psyche-research/issues/9#issuecomment-6719959829) and the function-ACL review in [issue #9](https://github.com/OpenCoven/psyche-research/issues/9) cover the original candidate. The response remains an uncommitted test/documentation candidate based on exact application source `bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4`; no application code or migration changed. [Independent follow-up](https://github.com/OpenCoven/psyche-research/issues/9#issuecomment-6726183561) confirms the combined response with no further scoped finding. Source-publication approval and changed-source CI remain pending. Agent review is engineering evidence, not scientific peer review, PR approval or certification.

## Function ACL scope

The original fixture revoked default function EXECUTE while connected to `postgres`. PostgreSQL applies defaults only in the current database, so that did not harden functions created in either application database. All original 22 checks passed despite PUBLIC/runtime/backup EXECUTE on the append-only trigger function. No privilege escalation or data-reading exploit was demonstrated; the function is trigger-only and raises an error. The earlier passing receipts do not qualify the declared hardening.

The adopted independent patch moves the revocation into `schema_grants(database)` before migrations and before restore. Both targets now require the append-only function to be migration-owned with no PUBLIC, runtime or backup EXECUTE. A harmless newly created migration-owned function must also reject runtime and backup invocation with SQLSTATE 42501 in each database; the probe is removed before dump/verification. The role proposal now explains database-local scope and why default changes do not repair existing function ACLs. The reviewed patch SHA-256 is `3d6a65af68bb948106217642a46cdda8e65e9f09823701f5f418834964b1b1da`.

Owner verification inspected the independent actual JSON reports: the source-policy omission control failed at the source ACL assertion, and the restore-only omission control passed source checks before failing at the restored ACL assertion. Both reported failed status and verified stopped servers. The independent corrected fixture passed 28 checks on both PostgreSQL versions. Removing only the four-line cleanup response from the final owner file reproduces that independently tested fixture hash `e31364e8893eddab46331578f42a5dc977760212d3ff31e48bb9a3226ca01797`; the reviewer files were not changed or rerun.

## Cleanup receipt consistency

The original process correctly raised on unverified shutdown but could serialize `status=passed` and `first_failure=null`. The owner adopted the reviewed correction before serialization: set failed status and supply a cleanup failure only when no earlier failure exists. The nonzero process behavior remains intact.

Four owner controls execute the AST-extracted actual final cleanup block with mocked subprocesses only: successful cleanup stays passed, failed cleanup becomes failed and raises, an earlier failure survives failed cleanup, and removing the correction reproduces the defect and is rejected. No server is started by these mocked controls. [Their structured receipt](database-role-cleanup-controls-20261108.json) retains the exact tested fixture identity and scope. Live positive runs separately verify actual server shutdown.

## Combined qualification

The follow-up reviewer independently reran the actual revised owner fixture at SHA-256 `389ef4c1307b77c7039a4d0e2662d4a1a01f6325e1edfc4cba3152e449e89a3b` on PostgreSQL 16.15 and 18.6: all 28 checks passed in both runs, all 18 dependency pins matched, first failure was null and server shutdown verified with final status exit 3. Three independent controls of the actual cleanup block also passed. The reviewer inspected the six added function-ACL checks, confirmed the P2 cleanup finding resolved on these exact bytes and reported no further scoped finding. The owner rechecked that the current fixture hash matches that reviewed identity; the documentation-only reconciliation did not change it. This closes the local scoped review, without claiming CI, provider or operating acceptance.

Final fixture SHA-256: `389ef4c1307b77c7039a4d0e2662d4a1a01f6325e1edfc4cba3152e449e89a3b`. The same final bytes passed all 28 checks on PostgreSQL 16.15 and 18.6, process exit 0, `first_failure=null`, server stopped and final status exit 3. Both runs matched all 18 dependency pins and application archive SHA-256 `8afbf4dec06e8a4dca7743d11be2e8ef248d7e9be55201c1112ea8c2634a7927`. Current receipts are [PostgreSQL 16](database-role-reviewed-pg16-20261108.json) and [PostgreSQL 18](database-role-reviewed-pg18-20261108.json), including exact synthetic dump digests. The prior CLI/startup controls were not repeated; their source identity and scope remain historical.

Commands use the same interpreter, trusted version-specific bins and exact source SHA recorded in the earlier receipt, with fresh output directories:

```sh
PYTHON -B archive/tests/rehearse_database_roles.py --pg-bin PG16_BIN --expected-major 16 --source-revision bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4 --output /tmp/psyche-reviewed-role-final16-20261108-1000
PYTHON -B archive/tests/rehearse_database_roles.py --pg-bin PG18_BIN --expected-major 18 --source-revision bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4 --output /tmp/psyche-reviewed-role-final18-20261108-1000
```

The exact private invocation scripts and cleanup controls remain in the owner scratch evidence. These are local synthetic checks over private UNIX sockets without TLS; both JSON reports explicitly set `provider_acceptance=false`. No provider identity, credential, setting, schema, deployment, real participant or intake changed. Do not rerun the earlier unverified native metadata query before inspecting its history. Existing account-binding, metered history, hosting-access, actual provider/recovery, WorkOS, policy and human acceptance gates remain separate. Keep real intake paused, `PILOT_APPROVED=0`, reviews/vouches unavailable, reputation disabled and pilot NO-GO.
