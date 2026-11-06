# Isolated local workflow and recovery qualification

Recorded 2026-11-06 for issues #3, #7 and #8, based on integrated main `a292928e395abe70c31aef03a5d6333f874fe3cf`, tree `6b727d1ff02fca4345e262cea2243aa123bb1251`. This candidate changes operational tests and acceptance records only; production application, authentication, storage and migration bytes are unchanged. Current main CI is green, while this changed test source needs its own exact-head qualification. Live epic #1 and the relevant issues retain the later canonical delivery receipt.

## Reproduced gap and bounded repair

The existing operational drill inherited the caller's process environment and selected a local database only through DATABASE_PATH. In settings, DATABASE_URL takes precedence; inherited Vercel/provider flags could also change or block the intended fixture. A baseline probe supplied only dummy Vercel/database configuration and reproduced the production-settings refusal before migration. No real key, provider endpoint or database was used. This establishes configuration inheritance, not evidence that a real serving database was modified.

Local drill subprocesses now inherit an explicit interpreter/OS environment allowlist, then set local authentication, PILOT_APPROVED=0, config.settings and their freshly allocated SQLite path. The representative recovery drill always supplies poisoned dummy hosted/database/provider/secret/host values, so the actual workflow exercises isolation rather than merely comparing a filtering helper's output. The child requires SQLite and the exact canonical temporary path before migration. The production-settings checks keep their explicit fail-closed/ephemeral-key/host cases in a separate temporary path, without ambient provider configuration. Other owners' Python installations are reused read-only; no package or global environment is changed.

The complete representative fixture and restored-app inspection run with a CPython audit assertion refusing socket/DNS and child-process events. Safe probes confirm the assertion actually refuses DNS resolution, socket creation and a child launch before continuing. This is a trusted regression fixture, not an operating-system sandbox for hostile code. Python documents this limitation in [sys.addaudithook](https://docs.python.org/3.13/library/sys.html#sys.addaudithook) and lists the relevant [audit events](https://docs.python.org/3.13/library/audit_events.html). Submitted instructions are never executed. A synthetic instruction/script string is stored as manuscript text, survives the restore and must remain escaped in the rendered version.

Existing coverage remains: fresh and reverse/reapplied migrations, historical publication/append-only guards, exact publication digests, separately moderated corrections, all-version withdrawal, private drafts/decisions/appeals/reports, consistent mode-0600 backup/restore, revoked restored sessions/credentials, paused intake, corrupt-schema refusal and restored public/private route behavior. There is no LLM dependency or model-provider key. Real AuthKit authentication, managed PostgreSQL/provider PITR, encrypted off-host retrieval and human acceptance remain separate gates.

## Local execution and first failures

The task used CPython 3.13.16 from the existing repository interpreter with the previously verified Django-main/asgiref package overlays; all 18 installed requirements were compared with the current pins and matched, including Django 6.1.2, asgiref 3.13.0 and WorkOS 10.6.0. The controller supplied an explicit local temporary database and no private provider values. Exact test command:

```sh
python manage.py test archive.tests.test_operations --verbosity 2
```

The first changed-source run passed five of six tests and failed the new pre-migration path assertion because macOS spells the same temporary directory through `/var` and `/private/var`. Comparing both resolved paths repairs that assertion while preserving exact-target equality. The corrected run executed all six tests in 4.492 seconds, OK with no skips; Django reported no system-check issues. `python3 -m py_compile archive/tests/test_operations.py` and `git diff --check` passed. Restricted raw baseline/first/final logs are retained under ignored task-local var storage; only these synthetic summaries are published.

The locally tested operational-test source SHA-256 is `6ba2a9ef8d6e0f9c11904ee015e8dd64771b1683e7fcd76eaa9d7c8e3f7442fb`. This local CPython/SQLite execution does not qualify PostgreSQL, hosted access, actual WorkOS sign-in, off-host recovery, legal adoption, real browser zoom/device/screen-reader or operating acceptance. The source-publication/integration path must inspect exact-head CI and keep those gates open. No resource, credential, agreement, payment, deployment, intake opening or cleanup occurred.
