# Issue #22 reviewed qualification candidate

Recorded 2026-11-06. This is the continued, uncommitted candidate in `psyche-research-input-limits` on `fix/issue-22-script-fair-limits-20261106`, based on PR #21 head `6966ea96f0018e26d91523ac361d74b54d43e0c3`. It reconciles the published PR #23 governance source at `8877646ea4b950b19e8434da11c8fb994de61005` without editing that owner's worktree or the unpublished alternative. The earlier [input qualification](INPUT_LIMITS_20261106.md) and [original structured receipt](input-limits-verification-20261106.json) remain historical, including their first failures. This receipt supersedes their pending-review/global-allowance descriptions. Pilot NO-GO; intake remains paused.

## Result and boundary

Valid submissions can use every advertised field allowance across writing scripts. Server validation matches browser maxlength in UTF-16 units and normalizes new CRLF/CR input to LF. Supplementary characters count twice and line breaks once. No existing manuscript, frozen snapshot, version or digest is rewritten. Legacy drafts remain readable/exportable on refusal; a legacy frozen CRLF retry can conflict without changing its frozen content or later publication digest.

The absolute pre-parse ceiling and Django parser limit are 512 KiB. After authentication, exact URL resolution permits that allowance only for editor POSTs; other form requests, including anonymous requests, retain 96 KiB. The primary user/IP bucket is charged before CSRF or body parsing, and login's username bucket is charged only after that primary check. CSRF validation remains required. The hard forty-field and no-upload safeguards remain. The scoped allowance resolves the review's anonymous/global-budget finding; charging before parsing resolves its exhausted-principal finding, including login.

The candidate incorporates PR #23's contributor-facing capacity/admission/wind-down changes and tests. Three source reconciliation conflicts were resolved: forms retains both the authored normalization validators and governance's artifact-link constant; STATUS preserves both owners' evidence narratives; policies retains the newer governance structure with the candidate's Psyche Research branding. The capacity partial, view context, policies, D011/D012 and tests now agree on request scope and counts. These changes adopt no human policy or operating commitment. Other owners' branches and worktrees are preserved.

## First failures and checks

The four new real-middleware regression tests initially ran in 1.587 seconds with eleven failing subcases: oversized non-editor/anonymous requests reached CSRF instead of 413, exhausted principals were not rejected before parsing, and an unresolved route returned 404 rather than the intended smaller-bound refusal. After the boundary repair all fifteen input-limit tests passed. The first combined 43-test input/governance/HTTP run then failed one assertion because the reconciled sidebar omitted the existing submission-limit link; the link was restored rather than weakening the assertion. The final full suite covers that correction.

| Check | Exact evidence | Result and scope |
| --- | --- | --- |
| Full combined suite | `manage.py test --verbosity 2`; `var/issue22-review-full-suite.log` | 157 discovered, 38.335 seconds, OK with ten explicit PostgreSQL skips; 147 executed. |
| Fresh migrations | `manage.py migrate --noinput` against `var/issue22-review-synthetic.sqlite3` | Exit 0; synthetic isolated data only. |
| Drift, settings and verifier | `manage.py makemigrations --check --dry-run`; `manage.py check --fail-level WARNING`; `manage.py verify_archive` | All exit 0. |
| Dependencies | `python -m pip check` with the verified Django 6.1.2/asgiref overlays | Exit 0; existing eighteen pins retained. |
| Production settings | `manage.py check --deploy --fail-level WARNING` | Exit 0 with an ephemeral test-only secret and `research.example.invalid`. |
| Static collection and whitespace | `manage.py collectstatic --noinput`; `git diff --check` | Both exit 0. |
| Independent abuse-bound review | Eight real-WSGI probes with valid CSRF cookies; saved source replay in `var/issue22-independent-review/final_probes.py` | Eight passed in 2.886 seconds; no unresolved scoped finding. |
| Final candidate browser | Playwright Chromium headless-shell 1248 with sandbox enabled | Startup failed with SIGTRAP before a page existed. Browser/native count and rendered acceptance remain unrun on this candidate. |
| Exact-source PostgreSQL CI | Prepared workflow runs `archive.tests.test_postgres archive.tests.test_input_limits archive.tests.test_governance` | Not published or run. PR #21's ten live PostgreSQL tests and PR #23's green CI cover their inputs only. |

Qualified application commands use `/Users/buns/Documents/GitHub/OpenCoven/psyche-research/.venv/bin/python`, `PYTHONPATH=/Users/buns/Documents/GitHub/OpenCoven/psyche-research-django-main/var/django-main/packages:/Users/buns/Documents/GitHub/OpenCoven/psyche-research-main-refresh/var/main-refresh/packages`, `LOCAL_DEVELOPMENT=1`, `PILOT_APPROVED=0` and isolated synthetic database paths. The production check substitutes only local development, an ephemeral secret and the invalid example host. The runner strips inherited authentication/database/hosting configuration before starting its checks. [The reviewed structured receipt](input-limits-review-verification-20261106.json) preserves exact argument arrays, timings and source/log hashes. The ignored runner is `var/run_issue22_review_qualification.py`; no participant material was used.

## Independent review

A separately delegated reviewer first reproduced the defects with three synthetic probes: anonymous 110,125-byte login reached parsing, and exhausted login/editor requests parsed before returning 429. The historical receipt explicitly distinguishes structured transcription from an unavailable original raw log. The reviewer then independently tested the repaired real WSGI middleware chain with valid CSRF cookies: anonymous oversized login/editor and authenticated oversized operations requests returned 413 with zero parses; exhausted login/editor requests returned 429 with zero parses; an editor above the absolute ceiling returned 413 with zero parses; a wrong-token editor request returned 403 without changing the draft; and a 417,799-byte CJK form serialized with CRLF saved successfully. Review also inspected normalization, legacy digest preservation and governance reconciliation. Final D011/accessibility corrections were verified. Agent review is not scientific peer review or security certification.

Saved review artifacts are under ignored `var/issue22-independent-review/`: original reproduction source/receipt, final source/receipt/log, and provenance README. The final receipt SHA-256 is `f9849ea93eb4fcf765751726e123bfa4879af0a951ab99503af3d2bee3ffb4d2`. It supplies the exact environment/argv and source hashes; the probe is piped to the recorded Python stdin command. The reviewed forms, middleware, settings, services, views, input/governance tests and policy partial match those recorded hashes.

## Requirement audit and continuation

| Requirement | Authoritative evidence | State |
| --- | --- | --- |
| Every field at CJK limits saves; ASCII, accented Latin, Arabic, Japanese, Korean, Deseret and emoji boundaries | `SubmissionCharacterBoundaries` and `SubmissionSaveBoundaries` in `test_input_limits.py`; full suite | Local pass. |
| Hard oversized requests refused before parsing | `HardRequestBoundaries`, `PreParseAbuseBoundaries`, independent real-WSGI probes | Local pass. |
| Browser/server newline and supplementary-character count contract | Field tests plus native maxlength attributes, policy copy and normalized storage assertions | Server/HTML contract passes; final native-browser execution remains unrun. |
| Legacy drafts and frozen publications preserved | Legacy export/refusal and CRLF retry/publication tests | Local pass. |
| Actual policy copy and governance agree | `test_governance.py`, policy/editor assertions, D011/D012 source review | Local pass. |
| Independent abuse review and findings resolved | Separate reviewer, eight persisted-source probes and exact source hashes | Pass within recorded scope. |
| Full applicable suite and exact-candidate PostgreSQL CI | 157-test local run; prepared PostgreSQL workflow | Local pass; exact-candidate CI pending publication authority. |
| Reviewable publication candidate and safe handoff | Current diff, source manifest, this receipt and STATUS | Prepared locally; no commit, source publication, PR approval/merge or deployment by this continuation. |

Next, obtain the missing issue-22 source-delivery authority for a local commit, new branch and draft PR carrying this reviewed combined candidate, then verify the exact published head and all applicable application/PostgreSQL jobs to terminal. Earlier moderation-only publication authority is not reused for this new diff. Recheck live main, PR #21/#23 heads, the candidate fingerprints, owners and Vercel Git-disable state immediately before publication. Preserve current PR owners; do not merge or close their PRs by inference. Restore supported browser execution for final native field-count/encoding checks. Keep actual AuthKit, protected staging/provider recovery, policy adoption and human accessibility/operating acceptance separate; no real intake or launch follows from source qualification.

Resume by reading the current goal, AGENTS, STATUS, DECISIONS, issue #22/comments and PR #21/#23; inspect the reviewed source/receipt and continue the remaining publication/CI/browser gates. Do not recreate the original implementation, repeat unchanged passing tests without a new concern, or substitute older checks for this candidate's missing evidence.
