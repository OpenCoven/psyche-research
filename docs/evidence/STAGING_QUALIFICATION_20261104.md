# Protected staging qualification continuation

Recorded 2026-11-04. The complete objective remains one exact revision demonstrated on authorized protected staging, measured provider and encrypted off-host recovery, and a founder GO/NO-GO packet with every human decision explicit. This continuation is incomplete and pilot remains NO-GO. Real intake stays paused. No hosting mutation, credential transfer, new identity, deployment, source publication or merge occurred.

## Ownership and source

This run read the user attachment, AGENTS.md, current status/decisions, the staging and WorkOS contracts, delivery epic #1 and operations/pilot issues #8/#9. Fresh GitHub REST reads confirm main d218b6bd2e72388fe00d928f465804c65e6ea306 and open draft stack #16 f7ebe30f3ec37dd032648ade8ffd121f0efc7d93, #17 86f564561b6851b0fb0f89f435cc777d70f6143c, #18 f9ae40780b3500e9235e76735345f442e5b91c0b, #19 2abdebcc31209782f3dccd23dfbe84f85d787612. Latest run 41909906944 remains completed/success on #19. That run does not cover the new local source.

The new isolated worktree is `/Users/buns/Documents/GitHub/OpenCoven/psyche-research-qualification`, branch `chore/staging-qualification-20261104`, based on unpublished deployment-guard commit dc06c0cbbf0620c857de25d142aaaf8ba0f84e16. The branding checkout and the accessibility, browser, Vercel and WorkOS worktrees were left untouched. The manual Git deployment guard is included locally through this base, but has not been published or verified effective on Vercel. Resolve actual Git behavior and applicable authority before source publication; Actions success does not establish deployment success.

## Review finding and repair

Review of the prior stack covered PKCE/browser state and callback consumption, JWT signature/issuer/client/subject validation, explicit local identity binding and role checks, encrypted server sessions, refresh/logout, migration/recovery clearing, public version notices and withdrawal suppression, and escaped error-summary navigation. The concrete new finding is a refresh race: two requests can load the same expired server session and exchange the same rotating refresh token. The second request can flush the first request's newly refreshed session. WorkOS documents refresh tokens as single-use in its [session token reference](https://workos.com/docs/reference/authkit/session-tokens), freshly read during this run. This source review and synthetic verification do not establish scientific peer review, security certification or live provider acceptance.

The first focused regression failed with `AssertionError: 2 != 1`, observing two exchanges instead of one. A separate concurrent full-middleware drill with the legacy Django session middleware fails with HTTP statuses `[503, 302]` and lost authentication. Those original failures remain in the private run receipts. The repaired drill passes with two authenticated responses, one refresh and the replacement session retained.

`WorkOSDatabaseSessionMiddleware` now locks the database session row before Django loads its session cache and holds the transaction through response saving. This serializes overlapping requests across application workers and prevents an older response overwriting rotated credentials. Local authentication keeps Django's ordinary session behavior. A lock/database operational failure returns a redacted retry response without claiming the underlying mutation was unsaved. Rotation is also saved before invoking a downstream view, because Django ordinarily omits session response saving on an HTTP 500; the dedicated regression proves a later server-error response does not replay the old token on the next request. No schema or role change was added.

The SQLite concurrency drill uses a fresh private temporary file, ordinary separate thread-local database connections and a bounded provider stub enforcing one use. It does not simulate PostgreSQL row locking or real WorkOS. The equivalent live PostgreSQL drill was added to the existing explicitly opted-in disposable-schema suite. That new test is unrun here: no PostgreSQL server/client or container runtime is available. Holding the session transaction through a request also needs independent review and actual PostgreSQL/pool contention measurement before hosted acceptance. Provider calls remain bounded and automatic exchange retries remain disabled. This is not crash-proof distributed token journaling or proof of recovery from a database outage after a provider consumes a token.

The new authentication/session repair has author verification only; an independent review of this changed source remains required before live use. The review of the pre-existing stack does not satisfy independent review of this run's own repair.

## Commands and results

Commands used `/Users/buns/Documents/GitHub/OpenCoven/psyche-research/.venv/bin/python` from the isolated qualification worktree, `LOCAL_DEVELOPMENT=1`, a private unused `DATABASE_PATH` under `var/qualification`, and no `DATABASE_URL`. The existing virtual environment is read for execution; its dependency state was not changed. [The machine-readable receipt](staging-qualification-20261104.json) records source hashes, commands, results, failures and unrun coverage. Raw logs are ignored private artifacts under `var/qualification`, not deployment inputs.

| Command or drill | Result |
| --- | --- |
| Baseline `manage.py test --verbosity 2` | 104 tests in 31.838 seconds, OK with seven PostgreSQL skips; 97 executed. |
| Initial focused overlapping-request regression | Expected failure: two refresh exchanges instead of one. |
| Focused AuthKit module after repair | 22 tests in 2.742 seconds, no skips, passed. |
| Full-middleware concurrent drill with legacy session middleware | Expected failure: `[503, 302]`; session access lost. |
| `test_overlapping_workos_requests_preserve_rotated_session_in_real_file_database` after repair | One test in 1.553 seconds, passed. |
| Final `manage.py test --verbosity 2` | 108 tests in 27.849 seconds, OK with eight explicit PostgreSQL skips; 100 executed. Includes the real-file concurrency and downstream-500 rotation regressions. |
| `manage.py makemigrations --check --dry-run` | Passed; no changes detected. |
| `manage.py check --fail-level WARNING` | Passed. |
| `python -m pip check` | Passed; no broken requirements. |
| `manage.py check --deploy --fail-level WARNING` | Passed with an ephemeral test-only key and reserved invalid hostname; no hosted credential created. |
| `vercel api /v9/projects/prj_KpONwA0jddpWRBIVQGt22FbZX7t2?teamId=team_VLpvr923t3nLPeaUaLxABctM --method GET --raw` | Exit 1, `fetch failed`; no remote project change or absence inferred. |

## Completion audit and next actions

| Original requirement | Current evidence | Remaining action |
| --- | --- | --- |
| One reviewed candidate; preserve ownership | Isolated branch, live stack/source refresh, prior-stack review and reproduced refresh finding with local repair. | Independently review the repair; run its PostgreSQL gate and exact-head hosted CI after publication is authorized and Git deployment behavior is resolved. |
| Prevent unintended Git deployment | Existing unpublished `git.deploymentEnabled=false` configuration matches freshly read [Vercel documentation](https://vercel.com/docs/project-configuration/git-configuration). | Resolve authority and initial-publication behavior, then platform read-back/exercise; no platform effectiveness claimed. |
| Live WorkOS login and account isolation | Existing staging project and URL setup are recorded in WORKOS.md; local authorization/isolation tests pass. | Browser access, private transfer of the already approved existing staging key, exact issuer and actual sign-in/sign-out/external-initiation checks. Do not request the same local credential-save approval again or create another provider key. |
| Keyboard, narrow layout, zoom, error focus and contrast | Historical Safari results remain limited to their recorded revisions; current synthetic form tests pass. | Fresh native inventory returned no apps/browsers, native startup failure and unavailable browser host. Current rendered checks are blocked, with no new screenshot or accessibility result. Human screen-reader acceptance remains separate. |
| Resolve and authorize staging scope | Existing project discovery and provider/region/cost proposal are preserved; consolidated non-secret scope questions were asked in this thread. | Await selection of existing versus separate project and actual provider/account/region/recovery target, operator/contact, audience/window and total cap. Then present the resolved resource/credential/deployment request. No placeholder scope is approval-ready. |
| Protected hosted workflow | Existing execution sheet and synthetic workflow tests. | Actual authorized protected deployment, unauthenticated denial on every hostname, runtime-role/pooling/TLS/log tests and full workflow. Any synthetic submission window needs its separate explicit bounded scope; no real intake. |
| Provider recovery and unchanged source | Earlier exact-head CI logical recovery evidence, separately scoped from this local repair. | Actual selected-provider separate-target recovery, post-snapshot safety/access reconciliation and measured loss/time with source unchanged. |
| Encrypted off-host restoration | Prepared execution contract only. | Approved storage/encryption/key owner and separate target, encrypted export/retrieval/restore with measured result. |
| Founder decision and human acceptance | NO-GO with explicit unresolved gates. | Human policy/license/retention, accessibility, operating coverage and final dated founder decision on the evidenced candidate. |

The browser and external-scope blockers are freshly verified in this first goal turn. This turn made concrete progress through independent inspection of prior work, an observed defect, a local repair and regression evidence. The full objective remains active and incomplete. Resume with independent review and new-head PostgreSQL verification when possible, continue any safe preparation, and incorporate the pending scope answers before dependent hosted actions. Do not turn local greens into hosted, recovery or human acceptance.
