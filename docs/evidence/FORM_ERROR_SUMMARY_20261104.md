# Form error navigation audit

Recorded 2026-11-04. Requirement A22 explicitly calls for an error summary linking fields. The shared form partial showed inline errors and separate non-field alerts but had no linked summary. This reviewable correction is isolated on `fix/form-error-summary` in `/Users/buns/Documents/GitHub/OpenCoven/psyche-research-accessibility`, based on browser PR #18 head f9ae40780b3500e9235e76735345f442e5b91c0b, tree b1cee77a4137e36ab39bfab4fbc2bf9a857f65d3. The branding, WorkOS and prior browser worktrees were left untouched. No migration, service, authorization, publication or persistent credential changed.

The shared partial now puts a named error alert before the controls. Each visible field error links to that bound field's actual label target, including prefixed controls and checkboxes. Non-field and hidden-state errors remain visible without unusable links. Inline errors keep Django's error IDs, invalid-state attributes and descriptions; their redundant alert roles were removed. Django escaping remains enabled for labels, errors and retained values. No script, automatic focus behavior or browser acceptance is claimed.

## Commands and first failures

Commands ran in the isolated accessibility worktree using the existing hash-pinned Python 3.13.16 environment. Logs are ignored local artifacts in its mode-0700 `var` directory, not participant data or public fixtures.

| Command | Result and receipt |
| --- | --- |
| `.venv/bin/python manage.py test archive.tests.test_form_rendering --verbosity 1` | First harness invocation omitted the documented local environment flag and failed startup on the secret-key guard; `var/error-summary-first.log` preserves it. No guard was weakened and no credential was created. |
| `LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py test archive.tests.test_form_rendering --verbosity 1` before the repair | Two tests ran; one failed because the named linked summary was absent. Original output is `var/error-summary-regression-first.log`. |
| Same focused command after the repair | Two tests passed in 0.003 seconds; `var/error-summary-repaired.log`. Checks cover actual prefixed targets, checkbox targets, hidden-state errors, non-field errors, escaping, invalid attributes, and absence of the summary on unbound/valid forms. |
| `LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py test --verbosity 1` | 104 tests in 15.172 seconds, OK with seven explicit dedicated-PostgreSQL skips, 97 executed; `var/error-summary-full.log`. The additional real submission endpoint regression verifies HTTP 400, links to missing evidence/confirmation controls, retained escaped input, private cache policy and unchanged stored draft/revision/publication state. |
| `LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py check --fail-level WARNING` | No issues. |
| `LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py makemigrations --check --dry-run` | No changes detected. |
| `git diff --check` | Passed before publication. |

A file lookup also referenced nonexistent `.github/workflows/ci.yml` and exited 2; the README supplied the correct documented local commands. This discovery failure is separate from the startup failure and missing-summary regression. Changed-head CI must be associated with the eventual exact PR head and read back separately; local skips do not establish PostgreSQL acceptance.

## Remaining gates and resumption

Fresh browser inventory still reports an unavailable browser host. Fresh Safari and Dia native bindings both fail with `cgWindowNotFound`; a Google Chrome binding reports `Invalid app`. This continuation therefore cannot verify rendered summary appearance, link activation/focus, keyboard-only flow, exact narrow width, zoom overflow, measured contrast or screen-reader announcements. The previous actual-browser receipt remains scoped to its recorded source. A22 and human accessibility acceptance remain partial.

The real WorkOS project and source implementation already exist; runtime credential-save confirmation remains unanswered, so no key was transferred and no real provider identity was enrolled. The proposed protected Vercel/managed PostgreSQL target, provider recovery and off-host recovery still require the resolved scope and their applicable authorization. Independent sensitive-code review, human policies and operating acceptance remain separate. No provisioning, deployment, merge, PR approval, invitation or real intake occurred; pilot remains NO-GO.

Resume by restoring browser access and exercising the changed invalid form, answering the pending exact local credential-save request if real AuthKit verification is desired, and resolving the named staging target/operator/cost decisions in STAGING_ACCEPTANCE.md before provisioning. Preserve the first-failure logs and verify the live PR head/checks before further delivery.
