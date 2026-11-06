# Reviewed release candidate qualification

Recorded 2026-11-05 America/Chicago. Application commit `fcd937a4da3e230c5329b09fbdb69b83181351d0`, tree `6dec7f78fdfd6e16238d15a78acf8a4592234825`. The release-candidate goal remains incomplete because current-source PostgreSQL/exact-head CI and the source-publication precondition are unverified. Pilot NO-GO; intake paused. This receipt establishes only the evidence explicitly described below.

## Inputs and ownership

[Source manifest](release-candidate-inputs-20261105.json) records merged main, drafts #16–#19, deployment guard, prior refresh/callback repairs, qualification base and branding snapshot. Candidate branch `candidate/release-qualification-20261105` was created in a separate sibling worktree from `96e808f42e20abc96d25471a118d81783a8d3545`. Branding commit `60a126434b7b16c236d189a9d0c2be440b9a1946` applies the existing patch to the newer stack. Its first three-way application returned exit 1 for the STAGING_ACCEPTANCE ownership-row conflict; resolution kept newer qualification text before current-state reconciliation. No original worktree, uncommitted branding edit or other owner's branch was changed.

[Remote receipt](release-remote-20261105.json) records fresh connected REST reads of main and every draft head/check. CLI REST failed with “error connecting to api.github.com”; the connected REST service supplied reads. Existing green runs remain tied to their older source. No source push, PR approval/merge, hosting mutation, deployment or new credential occurred.

## Findings, first failures and repair

Authentication reviewer `auth_review` reproduced P1 consumed-refresh reuse after an actual child process exit: the provider-side exchange was recorded, replacement saving happened inside the outer request transaction, and SQLite recovery restored the old consumed token. The isolated reproduction exited 1 with `externally_exchanged=synthetic-once-only` and `stored_after_crash=synthetic-once-only`. A separate downstream rollback regression likewise exchanged twice. A P2 synthetic real-RSA test reproduced two refreshes after a post-refresh JWKS outage, with statuses `[503, 503]` and retained authentication. The installed SDK itself verifies replacement JWTs, so that post-validation outage is a narrower failure window than the directly reproduced process-loss defect.

First-failure logs are retained privately under `var/release-qualification/psyche-auth-review-20261105-{crash-first-failure,rollback-first-failure,first-failure}.log`; their source copies remain under `/tmp`. No real provider or participant material was used. The new independent durability-test harness initially had two fixture errors (mock logout URL and finite monotonic values); the reviewer retained its first run and corrected both before relying on results. During main documentation preparation, an apply_patch delete/add of the same path was rejected before writing; direct file replacement then succeeded. The first Markdown link preflight then found broken relative links in moved status/release snapshots; their destinations were rebased without changing the preserved prose. These are harness/editing failures, not product acceptance.

The repair introduces `WorkOSCredential`, bound to the exact Django session, identity, client and local user. A durable atomic claim empties the consumable token before any SDK refresh exchange. Provider exchange runs outside a database transaction. Only the matching still-live claim with an active identity can receive the verified replacement. Ordinary session saves cannot rewrite this table, and downstream rollback cannot undo an earlier committed claim. Pending requests wait at most five seconds; a thirty-second abandoned claim is invalidated without restoring tokens. Expiry deletion uses a claim comparison; losing a race to finalization reloads the winner instead of logging it out. Late completion cannot resurrect logout, revocation or expiry.

Publication/recovery reviewer `publication_review` found an intermediate logout defect during the refactor: a legacy/malformed credential handle could raise before local logout, yielding 500 and retaining authentication. The final guard always clears the local session; missing/malformed-handle and copied-handle regressions pass. Migration 0006 does not rebuild publication tables. SQLite raw restoration explicitly deletes credentials before sessions; ORM restoration cascades credentials within its existing atomic boundary. Current-schema verification requires the new table/columns and migration. Legacy WorkOS sessions are not imported and require fresh sign-in.

## Exact application verification

The shared existing interpreter is `/Users/buns/Documents/GitHub/OpenCoven/psyche-research/.venv/bin/python`. All fixtures are synthetic and isolated. The application command on the committed revision was `LOCAL_DEVELOPMENT=1 DATABASE_PATH="$PWD/var/release-qualification/unused.sqlite3" /Users/buns/Documents/GitHub/OpenCoven/psyche-research/.venv/bin/python manage.py test --verbosity 2`. It exited 0: **126 tests in 24.803 seconds, nine explicit PostgreSQL skips, 117 executed**. Raw output is private `var/release-qualification/final-application.log`; its hash and application source hashes are in [the structured verification](release-candidate-verification-20261105.json).

| Check on application revision | Result |
| --- | --- |
| Full suite above | 126 tests, nine dedicated PostgreSQL skips, 117 executed; pass. |
| Focused new durability and operations checks before application commit | 21 tests in 5.266s, no skips; included again in committed full suite. |
| `manage.py migrate --noinput` against a fresh isolated SQLite file | Pass, including 0006. |
| `manage.py makemigrations --check --dry-run` | Pass, no changes detected. |
| `manage.py check --fail-level WARNING` | Pass. |
| `manage.py verify_archive` | Pass on fresh migrated isolated database. |
| `manage.py collectstatic --noinput` | Pass; collected files inspected as repository CSS only. |
| `python -m pip check` | Pass; no broken requirements. |
| `manage.py check --deploy --fail-level WARNING` | Pass with LOCAL_DEVELOPMENT=0, fresh ephemeral test-only key and research.example.invalid; no hosted credential created. |

The earlier branded baseline ran 109 tests in 20.839s with eight PostgreSQL skips. An intermediate refactor run ran 109 in 18.775s with eight skips. These are superseded local checkpoints, not evidence of later source.

## Independent final-source review

Authentication reviewer used a clean detached checkout of `fcd937a` and ran `LOCAL_DEVELOPMENT=1 <interpreter> manage.py test archive.tests.test_refresh_durability archive.tests.test_workos_auth archive.tests.test_operations.OperationalDrill.test_workos_callback_consumption_commits_before_provider_exchange archive.tests.test_operations.OperationalDrill.test_overlapping_workos_requests_preserve_rotated_session_in_real_file_database --verbosity 1`: **39 tests in 4.699s, no skips**. The separate `archive.tests.test_operations.OperationalDrill.test_refresh_claim_commits_before_exchange_and_survives_view_rollback` passed in 1.389s with no skips. The reviewer examined callback commitment, binding recheck, claim expiry/CAS, outer-transaction refusal, real process loss, stale saves, logout/revocation and migration; no unresolved scoped finding remains. Private logs: `/tmp/psyche-auth-final-fcd937a-tests.log` and `/tmp/psyche-auth-final-fcd937a-real-commit.log`.

Publication/recovery reviewer ran `manage.py test archive.tests.test_restore_preparation archive.tests.test_operations.OperationalDrill.test_fresh_migrations_representative_restore_and_corruption_refusal archive.tests.test_operations.OperationalDrill.test_upgrade_with_existing_published_record_preserves_content_and_triggers --verbosity 1`: **eight tests in 1.565s, no skips**, plus legacy/malformed logout and copied-handle isolation: **two tests in 0.149s, no skips**. A separate private fixture verified raw and ORM restored credential/session/attempt/rate removal, identity preservation, paused intake, foreign-key integrity and unchanged source SHA-256. Its first noncanonical temporary expected-path argument was correctly rejected and rerun with the resolved path. Final source and diffs were reviewed with no unresolved scoped finding. Earlier 67 publication/privacy/form tests passed before the credential repair; current full-suite evidence above covers the final revision.

These are agent engineering reviews of synthetic local behavior. They are not scientific peer review, a security certification or provider/browser/human acceptance.

## Environment and publication gates

Runtime reviewer `runtime_review` freshly observed effective UID 501 unresolved by `pwd.getpwuid`, absent supported Docker/Podman/Lima/Colima/PostgreSQL executables and no connected cloud/container execution surface. Process enumeration failed because sysmond was unavailable; this does not establish process absence. The prior verified PostgreSQL source build remains historical; its first initdb failure is preserved and no OS identity shim, account change, upstream patch or weaker test was substituted. The dedicated logical restore test intentionally requires the real PostgreSQL 16 Docker service and matching container clients supplied by the existing CI workflow.

Fresh Vercel CLI 64.7.0 read-only project/deployment requests terminated with “fetch failed.” A command-scoped DNS retry retained normal TLS verification; the API was reachable but rejected the existing expired access token with forbidden/invalidToken on both reads. No token or refresh token was printed or modified. Therefore the earlier project/link/protection/deployment observations are historical, not freshly confirmed current. The local `git.deploymentEnabled=false` matches [documented Git configuration](https://vercel.com/docs/project-configuration/git-configuration), but is unpublished and unexercised. [Git settings](https://vercel.com/docs/project-configuration/git-settings) and [CLI Git documentation](https://vercel.com/docs/cli/git) describe project Git disconnection; installed help confirms the project/scope flags.

The concrete approval proposal, after final documentation freeze, is to renew trusted-host Vercel access and authorize disconnecting only `0xbuns/psyche-research` (`prj_KpONwA0jddpWRBIVQGt22FbZX7t2`) from `OpenCoven/psyche-research`, verify the link is absent via project API and retain deployment inventory, then publish the exact reviewed candidate as a branch/draft PR and run exact-head Actions. No reconnect, deployment, other project change, secret/environment/protection/domain change or existing deployment deletion is included. Applicable separate hosting/publication authority is missing. This is a prepared request, not an executed action.

Fresh computer-use inventory returned zero apps/browsers, native startup failure and browser host unavailable; the CUA session was concluded with that observed blocker. Final-candidate screenshots, focus, narrow viewport, zoom and contrast are unrun. Earlier Safari evidence remains bound to its original sources; no HTTP/template check substitutes. Existing WorkOS local credential-save approval is preserved; no key transfer or live identity/provider flow was performed. Human screen-reader, policy and operating decisions remain separate.

## Requirement-to-evidence matrix

| Goal requirement | Authoritative evidence | Disposition |
| --- | --- | --- |
| Read goal, instructions, STATUS/DECISIONS, epic/issues and live PR/checks | Attachment read; source/remote manifests and private initial reads. | Verified. |
| Isolated candidate; source provenance; preserve other ownership | Candidate branch from 96e808f; branding patch hash and source SHA/trees; original worktrees unmodified by this task. | Verified locally. |
| Reconcile every requested slice and visible brand | Ancestor stack plus branding commit and fcd937a repair; current STATUS/RELEASE/WORKOS/DECISIONS/STAGING records. | Implemented; final docs/hash audit follows. |
| Separate independent authentication and publication/privacy/recovery review | Final-revision reviewer results above; reproduced findings and repaired regressions. | Verified within scoped local review; no unresolved scoped finding. |
| Callback commit before exchange; no rotating-token reuse or stale overwrite | Independent connection probes, real-file overlapping clients, actual process exit, rollback, stale saves, expiry/logout/revocation races. | Local pass; PostgreSQL still unrun. |
| Full application, migration/system/production checks and static collection | Structured verification and exact-source full suite. | Pass within stated local scope. |
| Dedicated live PostgreSQL including concurrency and logical recovery | Nine tests prepared; CI runtime defined; no current-source execution. | Missing required evidence; incomplete. |
| Available final-candidate rendered checks; separate human acceptance | Fresh CUA service failure and historical revision-specific browser receipt. | Blocked; human acceptance unrun. |
| Resolve Vercel automatic deployment before source publication | Local guard, historical auto-preview failure, expired access evidence, concrete project-only disconnect proposal. | Incomplete; no source published. |
| Preserve credential approval and avoid unauthorized operations | No secret-store change or approval repeat; no remote mutation, push, merge, provisioning or deployment. | Observed task boundary. |
| Clean committed candidate, requirement matrix, integration recommendation, current status | Application committed; this receipt/STATUS/RELEASE and final documentation commit. | Local deliverables prepared; full goal remains incomplete. |

Resume through the exact publication precondition and supported current-source PostgreSQL execution. Continue safe independent work if new access appears; do not treat another document, older green CI or a nominal NO-GO as completion.

