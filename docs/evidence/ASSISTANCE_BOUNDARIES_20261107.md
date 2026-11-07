# Issue #7 assistance-boundary guards

Recorded 2026-11-07 for [issue #7](https://github.com/OpenCoven/psyche-research/issues/7) on branch `test/issue-7-assistance-boundaries-20261107`, based on main `3c097874d7a4eb6832239192ae3d50824aea8c5c` (tree `9c73f875ee3c5a0bbd5873db721e3b1f1eda3973`). It covers five things:

- a re-check of the issue's existing evidence on that main;
- new regression tests and the regressions they caught;
- a local rendered-browser check;
- an independent review and how each finding was resolved;
- commands, first failures and limits.

It is engineering evidence. It is not a security certification, scientific review, hosted or AuthKit acceptance, or founder adoption of the assistance playbook.

## What was re-checked on main

The issue's four criteria were already checked on the strength of the [offline workflow receipt](OFFLINE_WORKFLOW_20261106.md), [ASSISTANCE.md](../ASSISTANCE.md) and `test_reputation_and_runtime_model_providers_are_absent`. On main `3c09787` the full suite passed locally: 157 tests in 98.774 seconds, OK, ten PostgreSQL skips. A source and dependency inspection found the following:

- `requirements.txt` pins 18 packages, and none is an LLM or model-provider SDK.
- The network-capable packages are there for WorkOS: `httpx2`, `PyJWT` and `cryptography` are required by `workos`, and `httpcore2`, `anyio`, `h11`, `truststore` and `idna` come in under `httpx2`.
- `archive/workos_auth.py` is the only runtime module that imports a network client. It imports `workos` and `workos.session`, and uses `jwt.PyJWKClient` against `https://api.workos.com/sso/jwks/<client>`. When WorkOS is unreachable, sign-in, its callback and signed-in session verification answer with a retryable 503 rather than admitting anyone.
- No runtime module imports `subprocess`, `socket`, `urllib.request` or an HTTP library, and none calls `os.system`, `eval`, `exec` or `importlib`.
- `EMAIL_BACKEND` is Django's dummy backend, and `django.contrib.admin` is not installed.
- Templates contain no script element, event-handler attribute, `|safe` or `autoescape off`.
- Application responses carry `Content-Security-Policy: default-src 'none'; …` with no `script-src`.
- The AI-assistance disclosure must be non-blank before submission and is rendered under an "AI-assistance disclosure" heading on the frozen and published snapshot.
- Decisions are append-only rows with an `actor` foreign key, and `services.decide` is the only code that creates a `Version`.

## What the new tests add

`archive/tests/test_assistance_boundaries.py` turns those observations into six regression tests so later edits cannot quietly undo them:

| Test | Guarantee |
| --- | --- |
| `test_untrusted_text_is_inert_on_every_surface_and_reading_it_changes_nothing` | Instructions and markup are placed in every free-text submission field (including the change note), a report, an appeal and a withdrawal reason. They render as escaped text, with no raw `<script`, `<img src=x` or `onerror=` markup. Author pages checked: the dashboard and the draft, frozen and declined edit pages. Moderator pages checked: the queue, the moderation pages and operations. Public pages checked: archive, archive search, the work redirect and the version page before and after withdrawal. JSON exports are `application/json` with `nosniff` and the no-script policy. Loading those pages changes no row in any archive table, user, group or permission link. The only decisions are the human moderator's own, attributed to that account. |
| `test_assistance_disclosure_is_required_and_labelled_for_moderators_and_readers` | An empty or blank disclosure cannot be submitted and the draft stays a draft. The disclosure appears, escaped, under its heading on the moderator's page and the public version, and is stored exactly in the version snapshot. |
| `test_every_kind_of_application_response_keeps_the_no_script_policy` | A public page, a 404, a moderator page and a refused multipart upload all keep `default-src 'none'`, with no `script-src`, `script-src-elem`, `script-src-attr`, `worker-src` or `connect-src` and nothing `unsafe`. The same holds in WorkOS mode. |
| `test_runtime_imports_stay_on_the_reviewed_list_and_nothing_starts_processes` | Every runtime module (`archive/`, `config/`, `deploy/` and `manage.py`, excluding tests) may import only listed standard-library modules, Django, the project's own packages and `cryptography.fernet`. The Django mail, server, test, dynamic-import and safe-string modules are excluded. Only `archive/workos_auth.py` may import `workos` and `jwt`, and only `config/safe_logger.py` may import `gunicorn.glogging`. The scan also flags `from os import <process call>`, aliased `os` process calls, `getattr(os, …)`, `eval`, `exec`, `compile`, `__import__` and `__builtins__`. A per-file allowance fails if it is no longer used. |
| `test_only_the_human_moderation_form_reaches_publication` | `services.decide` is the only function that creates a `Version`. The moderation view is the only runtime caller of `decide`, and it keeps `@moderator_required`. The service keeps its human-moderator role check. |
| `test_templates_and_runtime_code_avoid_known_escaping_bypasses_and_script` | Autoescaping stays enabled. No template uses `\|safe`, `\|safeseq`, `autoescape off`, a script element, an event-handler attribute or a `javascript:` URL. No runtime module uses `mark_safe`, the safe-string classes, `html_safe`, `__html__`, `Template(` or `from_string`. No HTML response body is built from a variable or f-string unless its content type is not HTML. |

## Regressions the tests caught

A scratch copy of the branch received one regression at a time, and the new module ran after each one. All 31 were caught, and the unmodified control passed. Rows marked † came from the independent review or were added after it.

| Regression injected | Caught by |
| --- | --- |
| Disclosure rendered with `\|safe` | inert-surface, disclosure and escaping tests |
| `{% autoescape off %}` block on the moderator page | inert-surface and escaping tests |
| Disclosure section removed from the snapshot | disclosure test |
| Disclosure dropped from the fields required to submit | disclosure test |
| CSP widened with `script-src 'self' 'unsafe-inline'` | no-script policy test |
| `import urllib.request`, or `from urllib import request`, in `views.py` | import guard |
| `from httpx2 import Client` in `services.py` | import guard |
| `import subprocess` in the backup command | import guard |
| `import importlib` with `import_module(...)` in `views.py` | import guard |
| `mark_safe` imported in the template filters | import guard and escaping test |
| A script element in `base.html` | escaping and inert-surface tests |
| The moderation queue auto-publishing pending submissions on GET | inert-surface and publication-route tests |
| † A moderation page load adding the author to `moderators` | inert-surface test |
| † An operations page load marking open reports resolved | inert-surface test |
| † `from os import system`; an aliased `os` process call; `getattr(os, 'popen')` | import guard |
| † `from importlib import import_module`; `socketserver`; `_socket`; `wsgiref.simple_server` | import guard |
| † `django.core.mail.send_mail`; `from django.core import mail`; `django.utils.module_loading.import_string` | import guard |
| † A template filter returning a `str` subclass with `__html__`; `html_safe` | escaping test |
| † The error handler serving exception text as HTML | escaping test |
| † A management command calling `decide`; a second `Version.objects.create` path; `@moderator_required` removed from the moderation view | publication-route test |

## Rendered-browser check

Chrome for Testing headless shell 156.0.8078.4 was driven over the DevTools protocol from Node v24.22.0 against `manage.py runserver` on loopback, with a freshly migrated scratch SQLite database. The browser's host resolver mapped every host except 127.0.0.1 to "not found".

- **Fixture:** a synthetic author and moderator with random, never-printed passwords, and sessions created directly in the scratch database. One published and one pending submission carry the test module's payload in every free-text field, and a report and an appeal carry it too.
- **Pages loaded:** eleven in all. Moderator: the queue, two moderation pages and operations. Author: the dashboard and two edit pages. Public: home, archive, a script-bearing search and the version page.
- **Result:** every page returned 200 with the no-script policy. No page had a script element, an `img[src=x]`, an event-handler attribute or a page-level flag set by the payload. There was no dialog, no exception and no request to a non-loopback host. Content pages showed the payload as visible text, and the moderation, edit and version pages showed the "AI-assistance disclosure" heading.
- **Positive control:** a `data:` page without these headers, carrying the same kind of payload, tripped every detector: a dialog, a request to `https://example.invalid/`, a script element and the flag. So the clean result is not a blind harness.
- **Repeat:** the check passed again after the review fixes.

The harness is not in the repository or CI. It ran locally only, with script SHA-256 `c20b3b2516c4bcdddb71f3d286fe1bb54dd9609c66e9de1e0c8ef6684334b332` and fixture SHA-256 `912c035d4f101bf6b792f973460242e2e73062baab49ff7c509fc796a8a41841`. The mutation script's SHA-256 is `66ac5c5b71f8b1a9b19699f34f299f04fc1262dd20d78136ff3a8d9c8ca97aac`.

## Independent review

A separate agent reviewed the code and documentation without being given these conclusions, and modified nothing. It reported no blockers, five should-fix findings and four nits, each resolved as follows:

1. **State check too narrow.** It ignored accounts, groups, capacity and resolution fields, and the operations page load sat outside every comparison. Two mutations passed. Fix: the check now compares every archive row plus users, groups and permission links around each group of page loads, including operations.
2. **Denylist with gaps.** The network and process guard missed aliases, `from os import`, `socketserver`, `_socket`, `wsgiref`, Django mail and `import_string`. Fix: it is now an allowlist of exact imports with per-file allowances, plus alias-aware process-call checks. Every reported bypass is now caught.
3. **"Cannot switch off escaping" overclaimed.** A `__html__` filter, `html_safe`, `Template(` and HTML responses built from variables were missed. Fix: those patterns and an AST check of response content types were added, and ASSISTANCE.md now says the code is "scanned for the known ways".
4. **Wrong claim about PostgreSQL CI.** The first draft of this receipt said PostgreSQL execution was left to CI, but CI's PostgreSQL job runs only `test_postgres`, `test_input_limits` and `test_governance`. Fix: corrected below. The reviewer found no PostgreSQL-specific risk in the module.
5. **Unenforceable attribution claim.** "Assistance never authors a decision" cannot be enforced by the application. Fix: ASSISTANCE.md now says the playbook forbids it and the record shows the account, not whether a human acted.

The nits were handled as follows:

- The drill-scope and policies-page sentences were made exact.
- "Every response" became "every application response".
- The change note and withdrawal reason were added to the payload checks, and the home page dropped out of them.
- The test docstring now says extending an allowance is a reviewed change.

The reviewer also noted that criterion (a) holds only on the local-authentication path, so ASSISTANCE.md now records the hosted WorkOS dependency. It noted that nothing pinned publication to `decide`, which the publication-route test now does.

## Commands, environment and results

Environment: macOS (Darwin 27.2.0), Python 3.13.16, a fresh virtual environment installed with `pip install --require-hashes --no-deps -r requirements.txt`, SQLite with `LOCAL_DEVELOPMENT=1` and a random session-only secret. No model provider, provider key or private material was used. All accounts and text are synthetic.

| Step | Command | Result |
| --- | --- | --- |
| Main baseline | `manage.py test` on `3c09787` | 157 tests in 98.774 s, OK, ten PostgreSQL skips |
| First run of the first draft | `manage.py test archive.tests.test_assistance_boundaries -v 2` | 5 tests, 1 failure. The network guard compared full dotted names such as `workos.WorkOSClient` against module names, a test-authoring error that was fixed before review. |
| First draft mutation run | scratch copy, one regression at a time | 13 of 13 caught; control OK |
| Revised module after review | same command | 6 tests, OK |
| Revised mutation run | scratch copy, one regression at a time | 31 of 31 caught; control OK |
| Full suite on the branch | `manage.py test` | 163 tests in 50.886 s, OK, ten PostgreSQL skips (153 executed) |
| Django checks | `check --fail-level WARNING`; `makemigrations --check --dry-run` | no issues; no changes |
| First browser fixture | `manage.py shell` with the fixture | Refused with 429 by the fixed one-queued-submission-per-contributor rule, a fixture ordering error. Deciding the other submissions first fixed it. |
| Rendered check | headless Chromium as above, before and after the review fixes | 11 pages clean each time; positive control detected |

## Remaining limits

- **Static scans:** they are tripwires, not proofs. They read the repository's runtime modules only. They do not see code inside installed packages, the PostgreSQL connection Django opens from settings, the WorkOS SDK's own network use, or every conceivable dynamic trick. An allowance can be extended by a reviewed edit.
- **Headers versus browsers:** the CSP test checks application headers. The HTTPS redirect returned by Django's security middleware and platform-served static files are outside that middleware. The browser check shows enforcement in one Chromium build, without cross-browser coverage, and it did not submit decision forms.
- **Pages not rendered:** the withdraw, revision, report and sign-in pages are covered only by the template-wide escaping guard.
- **SQLite only:** the new module runs in CI's SQLite application job but not in its PostgreSQL job, and this slice does not change the workflow file.
- **Hosted dependency:** in hosted WorkOS mode, sign-in and session verification depend on WorkOS. Criterion (a)'s offline guarantee is for the local-authentication path.
- **Other gates:** ASSISTANCE.md remains a proposed playbook pending founder adoption. Actual AuthKit, hosted and human acceptance remain open under their existing gates.
- **Nothing outward-facing happened:** no deployment, credential, agreement, invitation, payment, merge or PR approval was performed.
