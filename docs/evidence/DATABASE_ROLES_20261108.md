# Synthetic database role rehearsal — 2026-11-08

Owned candidate: `test/issue-9-role-contract-20261108` in the isolated `psyche-research-role-contract` worktree, based on `bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4`. This candidate remains uncommitted and independently unreviewed. It changes a test fixture and documentation only; no application code, migration, provider role, credential, setting, deployment or intake was changed. The original checkout's dirty branding and other owners' worktrees were retained.

This receipt is historical. The [independent review response](DATABASE_ROLE_REVIEW_RESPONSE_20261108.md) supersedes it with the corrected 28-check fixture and cleanup result controls. The 22-check fixture SHA-256 `1858dd2bf27fac5867df80f8c0c90b7b1e24d7355cefdcfb74f77fb53370fc32` did not qualify its declared function hardening and could mislabel a cleanup-failure JSON receipt. Earlier hashes, commands and results describe those prior bytes; they are retained evidence rather than current-file fingerprints.

## Reproduction

Use an existing trusted PostgreSQL bin directory and a Python environment matching the archived source's requirements. The fixture accepts only a new private output path, an exact source SHA and expected PostgreSQL major 16 or 18; it starts its own fresh local server without TCP listeners, exports committed source with `git archive`, strips ambient provider configuration and records source/fixture/tool identities. It rejects optimized Python because its checks use assertions. It neither accepts a remote database URL nor provisions provider credentials.

```sh
/Users/buns/Documents/GitHub/OpenCoven/psyche-research-assistance/.venv/bin/python -B archive/tests/rehearse_database_roles.py \
  --pg-bin /Users/buns/Documents/GitHub/OpenCoven/psyche-research-qualification/var/postgres-qualification/install/bin \
  --expected-major 16 \
  --source-revision bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4 \
  --output /tmp/psyche-role-contract-reviewed-20261108-0935
```

The trusted existing tools are the prior qualification's source-built PostgreSQL 16.15 binaries; no package was installed for this slice. The environment matched all 18 pinned dependencies. The archive SHA-256 is `8afbf4dec06e8a4dca7743d11be2e8ef248d7e9be55201c1112ea8c2634a7927`. The final output directory retains `role-report.json`, exact grants embedded in the fixture, synthetic command logs, source export and private synthetic dump. Do not commit the dump or generated cluster.

## Coverage and limits

Final command exit was 0: all 20 checks passed, `first_failure` was null, `server_stopped` was true and final `pg_ctl status` exited 3. The tested fixture SHA-256 is `0ddcaf9d41650245df559be4136adb880a06b161dff578a38b282cf814fc23dc`; synthetic dump SHA-256 is `24202ecee2081d46edc8aa0d3307797f127f7412e180c64f019dde23e0d25ed7`. The JSON report has `provider_acceptance: false`, PostgreSQL server version `160015` and all four checked client/server tool versions `16.15`.

The 20 checks cover non-owner migration execution, absence of elevated role flags/memberships, a runtime publication/correction/report/withdrawal/private-draft/session/synthetic-credential workflow and archive verifier, ten runtime permission refusals, five backup permission refusals, a mode-0600 custom dump by the read-only backup role, and migration-role restore into a separate fresh database followed by runtime archive verification. Both synthetic databases end with two versions and paused intake. Synthetic WorkOS ORM records are inert; no actual sign-in, callback, network request or provider session was exercised.

Five additional negative controls passed: existing output was refused without changing its sentinel; a non-SHA revision was refused before output creation; a PostgreSQL 18 expectation rejected the available version-16 tools before initialization; optimized Python was refused; and a wrapper that deliberately reported startup failure after successfully starting the owned server produced the expected failure report and verified shutdown (`pg_ctl status` exit 3, no `postmaster.pid`). These controls are retained under `/var/folders/5b/njd1qhwx4h97r9lvy_wpf5lc0000gn/T/psyche-role-controls-5cp9kjat/controls.json`; the intentional fault is not a successful application rehearsal. Self-review identified and repaired cleanup after a failed/timed-out start, and made unverified cleanup fail the process. Independent review is still required.

Earlier qualification attempts had failed at local `initdb` because UID 501 could not be resolved. In this cycle `id -un` returned `buns` and fresh initialization succeeded; no signing or other environment blocker is presumed repaired from this observation. The final rehearsal's first-failure field and shutdown result are recorded in its JSON receipt. Full application CI, actual provider privileges, TLS/pooling, encrypted off-host restore, PITR/RPO/RTO, browser, human and operating acceptance were not run in this slice. The pilot remains NO-GO; real intake stays paused, `PILOT_APPROVED=0`, reviews/vouches unavailable and reputation disabled.

## PostgreSQL 18.6 continuation

The identical fixture and exact application source also passed all 20 checks on a private source-built PostgreSQL 18.6 server, with matching 18.6 dump/restore clients and all 18 dependency pins. [The structured receipt](database-roles-pg18-20261108.json) records server version `180006`, unchanged fixture/source fingerprints, `first_failure: null`, process exit 0 and verified shutdown (`server_stopped: true`, final status exit 3). Synthetic dump SHA-256 is `610c1d34c5536cbec1d7d0b991bad22601bbffc26dc9aa3d4ac317cb9e444b92`. It explicitly retains `provider_acceptance: false`.

The source archive came from [the official PostgreSQL 18.6 release directory](https://ftp.postgresql.org/pub/source/v18.6/). Its SHA-256 matched the separately downloaded published checksum: `555610c24d53e4316da5b7d3fc25c279d96856d5e0e23ee308c328c5fa881d9f`. No system package, service, PATH or credential was installed. Configure used a private `--prefix` with `--without-icu --without-readline --without-zlib --without-openssl --without-lz4 --without-zstd`; `make -j4` and `make install` both exited 0. The private build deliberately has no TLS and must not be used for hosted connection acceptance.

The first configure attempt ran before the extraction session had reported completion and exited 1 with a missing `src/template/darwin`; its log was retained as `configure-first-failure.log`. After the original extraction session completed with exit 0, an archive inventory found all 7,284 regular files present. The subsequent configure, build and installation completed with exits 0. No extraction or download was restarted because of an observation timeout. The private scratch build and logs remain under the `psyche-pg18-build-jl2zqb5z` temporary directory.

```sh
/Users/buns/Documents/GitHub/OpenCoven/psyche-research-assistance/.venv/bin/python -B archive/tests/rehearse_database_roles.py \
  --pg-bin /var/folders/5b/njd1qhwx4h97r9lvy_wpf5lc0000gn/T/psyche-pg18-build-jl2zqb5z/install/bin \
  --expected-major 18 \
  --source-revision bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4 \
  --output /tmp/psyche-role-contract-pg18-20261108-0940
```

The PostgreSQL 18 result closes the local major-version rehearsal gap only. Managed Neon privilege inheritance, actual endpoints/TLS/pooling and provider/off-host recovery remain unexecuted; neither this test nor the documentation review is independent review of the new candidate. Current [Neon role documentation](https://neon.com/docs/manage/roles) confirms the Console/API administrative membership distinction now recorded in the role proposal; no new role was provisioned.

## Restricted recovery continuation

The earlier fixture stopped after restore and archive verification. Existing application recovery tests exercised offline preparation using a broader database identity, so they did not establish compatibility with this new role/grant proposal. The final fixture now restores in one transaction as the migration role, then runs the existing `prepare_restored_archive` command as the restricted runtime role against only its fresh restore database. Application and migration source remain unchanged.

Only the synthetic restored copy is seeded with open intake and one active rate bucket; the source remains paused. Before preparation the restored copy also has exactly one session, sealed synthetic WorkOS credential and pending login attempt. A mismatched expected database exits 1 with the expected target-refusal message and no changes to any public table. Correct explicit identifiers allow preparation: all four transient record types disappear, intake closes, capacity revision increases by one, other capacity fields remain unchanged and exactly one actorless `restored_paused` event records the exact synthetic reason/scope. Every historical event and every row of every other public table remains identical. Every source public-table row remains identical, and the final runtime archive verifier passes. This verifies the exercised row-state contract; it does not claim provider session revocation, sequence equality, rollback under every failure, hosted isolation or post-snapshot access reconciliation.

Final PostgreSQL 16.15 and 18.6 commands both exited 0 with 22 checks, no first failure and verified shutdown (status exit 3). Both JSON reports retain `provider_acceptance: false`, the same application archive hash and all 18 matching dependency pins. The final fixture SHA-256 is `1858dd2bf27fac5867df80f8c0c90b7b1e24d7355cefdcfb74f77fb53370fc32`. The two structured receipts are [PostgreSQL 16](database-role-recovery-pg16-20261108.json) and [PostgreSQL 18](database-role-recovery-pg18-20261108.json); they retain each synthetic dump's exact digest. The earlier cleanup/CLI failure controls were not rerun because their paths were unchanged; their older fixture identity remains explicit above. Independent review and changed-source CI remain outstanding.

```sh
/Users/buns/Documents/GitHub/OpenCoven/psyche-research-assistance/.venv/bin/python -B archive/tests/rehearse_database_roles.py \
  --pg-bin /Users/buns/Documents/GitHub/OpenCoven/psyche-research-qualification/var/postgres-qualification/install/bin \
  --expected-major 16 \
  --source-revision bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4 \
  --output /tmp/psyche-role-recovery-final16-20261108-0947
/Users/buns/Documents/GitHub/OpenCoven/psyche-research-assistance/.venv/bin/python -B archive/tests/rehearse_database_roles.py \
  --pg-bin /var/folders/5b/njd1qhwx4h97r9lvy_wpf5lc0000gn/T/psyche-pg18-build-jl2zqb5z/install/bin \
  --expected-major 18 \
  --source-revision bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4 \
  --output /tmp/psyche-role-recovery-final18-20261108-0947
```

The complete metadata audit in `var/agent-maintenance/role-recovery-20261108.json` reconfirms unchanged main, twelve open issues, the two existing draft PR heads with eight successful checks each, and 26 retained worktrees. No source publication, integration, provider operation, actual WorkOS or human acceptance occurred. The local candidate does not resolve those external gates; full goal remains incomplete and pilot NO-GO.

## Provider observation hold

A subsequent native Safari read again reached the existing selected Neon settings page without changing a setting. The CLI still exited 1 with the default profile unsigned in, and no Neon/Vercel connector was callable. The blank SQL editor accepted one `BEGIN READ ONLY` catalog transaction selecting session membership, database/schema ownership and non-system table count; the final text was inspected and Run invoked once. The console reached Connecting, but before a terminal result was observed Safari switched to a separate AuthKit page. Further UI input stopped. The transaction's outcome remains unverified; no result, membership finding or zero-table claim is inferred, and no second execution was attempted. The editor may retain this non-secret metadata query in its history. No mutation or credential operation was requested by the transaction. Resume by inspecting that existing query's terminal history through a stable operator interface before considering another execution; preserve the earlier completed provider query as the latest verified SQL result.
