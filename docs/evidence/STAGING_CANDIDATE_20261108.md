# Canonical staging candidate qualification

This candidate combines PostgreSQL 16/18 qualification from draft PR #34, the native private moderation contract from draft PR #36 and the frozen independently reviewed role-contract input. [The input manifest](STAGING_INPUTS_20261108.json) pins original heads/patches and the 12-file role snapshot. Final exact-head CI, artifact identities and final review are recorded in the canonical draft PR's qualification receipt; until those exist this document is preparation evidence, not a passing delivery claim.

The frozen role fixture is SHA-256 `389ef4c1307b77c7039a4d0e2662d4a1a01f6325e1edfc4cba3152e449e89a3b`. Independent review of the combined candidate found ambient parent libpq settings could redirect an explicit socket connection, then identified child passfile/user-site and interpreter-startup gaps. The canonical-only correction removes inherited PG settings, forces parent/child to a private empty mode-0600 regular configuration file, disables child user-site imports and invokes the supported allowlisted launcher under `-I -B`. HOME is preserved. Grant, restore, denial and cleanup assertions from the frozen input remain intact; one environment-policy check brings the rehearsal to 29 checks. Original owner bytes and branches remain unchanged.

## Local results and exact scope

| Check | Result |
| --- | --- |
| Application suite | 169 discovered / 159 executed / ten dedicated PostgreSQL skips; exit 0; isolated SQLite and sanitized environment |
| Restricted-role PostgreSQL 16.15 | 29 checks, 18 pins matched, first failure null, shutdown verified/status 3 |
| Restricted-role PostgreSQL 18.6 | Same 29 checks and cleanup result |
| Fixture identity for both final local runs | `9b33339f8c0d012b2fce71f5766c3c020140f4b15bfb9184ccdf842cddbee39d` |
| Archived application source | Main `bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4`, archive SHA-256 `8afbf4dec06e8a4dca7743d11be2e8ef248d7e9be55201c1112ea8c2634a7927`; these local runs do not qualify the future published head |
| Cleanup/environment unit controls | Six passing tests, including cleanup-report failure, first-failure preservation and historical-mutant rejection |
| Workflow and whitespace | actionlint and git diff --check pass |
| Local Docker and combined native browser | Docker unavailable locally; combined container/native execution requires exact-head hosted CI |

Reproduce using trusted installed dependencies/tools and a new output directory for each run:

```sh
python -I -B archive/tests/run_database_role_rehearsal.py --pg-bin /TRUSTED/POSTGRES16/bin --expected-major 16 --source-revision EXACT_COMMITTED_SHA --output var/role-pg16-UNIQUE
python -I -B archive/tests/run_database_role_rehearsal.py --pg-bin /TRUSTED/POSTGRES18/bin --expected-major 18 --source-revision EXACT_COMMITTED_SHA --output var/role-pg18-UNIQUE
python -m unittest archive.tests.test_database_role_cleanup archive.tests.test_database_role_environment -v
actionlint .github/workflows/verify.yml
git diff --check
```

The supported launcher uses an OS environment allowlist and execs the fixture with isolated Python before imports. The hosted matrix builds an allowlisted two-file context using the official PostgreSQL 16/18 Debian trixie images and hash-pinned Python dependencies, runs as the unprivileged postgres identity with read-only source and no container network, poisons ambient PG/provider inputs, and uploads only the structured role-report.json. Dumps, databases, logs and session/private data are excluded. Unit controls run in the ordinary application job as well. The dedicated role job archives the actual PR head, not the historical main baseline.

## First failures and review limits

The initial snapshot-doc patch check failed before mutation when invoked in the old default checkout; explicit workdir and a three-way STATUS merge preserved both inputs. Initial actionlint rejected mkdir -p/-m and a sudo/redirection pattern; install -d and an explicit owner/mode copy resolved both. Launcher-only trial receipts passed 28 checks but warned about /dev/null passfiles; the final private regular-file policy removed those warnings. The reviewer's initial unittest command used an unsupported --verbosity argument and exited 2 before executing tests; corrected -v passed. A resumed control command used the uninstalled bare python executable and exited 127 before tests; the explicit python3 invocation is the corrective command. No earlier failed/superseded run is relabeled as final qualification.

The independent canonical_review agent compared the frozen-to-canonical delta and ran all six controls, finding no further scoped code defect after the isolation fixes. Final published-head/documentation review remains a separate completion gate. It did not run PostgreSQL, a container, native browser or provider checks; root-owned evidence covers local PostgreSQL. Agent review is not scientific peer review or security certification.

Actual read-only provider evidence and the priced execution request are in [NEON_CONTRACT_20261108.md](../NEON_CONTRACT_20261108.md) and [STAGING_EXECUTION_REQUEST_20261108.md](../STAGING_EXECUTION_REQUEST_20261108.md). No provider writes, deployment, new persistent credential, spending or intake activation occurred. Full pilot remains NO-GO.
