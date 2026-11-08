# Issue #5 native moderation browser contract

Prepared on current main `bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4`, tree `a22d3141c32a7c72b75a20280c7bda0dc127a90f`, on the owned branch `test/issue-5-browser-workflow-20261106`. This five-file test/workflow/evidence slice changes no production application, migration, template, stylesheet or dependency bytes. Other owners' source and worktrees are retained. The full goal is active and incomplete; pilot NO-GO, real intake paused, reviews/vouches unavailable and reputation disabled.

## Contract

The existing Chrome job covers public/contributor pages and draft input. The added job exercises the private human moderation path using a newly migrated disposable SQLite database, synthetic local identities and five separate Chromium contexts: anonymous, author, unrelated staff/superuser without the explicit moderator role, moderator, and a moderator/superuser with their own queued work. These are preauthenticated test sessions, not live WorkOS sign-in.

`run_browser_moderation.py` strips ambient database/Django/WorkOS/Vercel/PostgreSQL settings before importing Django, verifies default paused intake, creates four clearly synthetic submissions in private temporary storage and returns intake to paused before browser execution. The native driver uses an isolated browser profile, no sandbox-disabling flag and interception that refuses page HTTP(S) requests outside the exact loopback origin. Synthetic session configuration, database and server logs stay outside the artifact allowlist. Processes have bounded execution and task-owned cleanup.

The workflow checks role/private-record boundaries, superuser self-decision refusal, scientific-review disclosures, request changes, keyboard edit/save during pause, paused and finite-queue refusals, resubmission, decline, stale-decision refusal, appeal/response/reopening, exact publication and an identical lost-response retry. Anonymous HTML/JSON must expose only the final exact synthetic claims and no private decision/appeal markers. The separate database postcondition verifies every snapshot field/digest, three actor/revision/time/conflict/reason-bound decisions, audit events, a linked resolved appeal, no decisions for denied identities, one exact temporary synthetic version, two remaining queued records, an incomplete saved draft and paused intake.

Rendered checks cover queue, decision and operations pages at 1440, 390 and 320 CSS pixels, plus declined-author, resolved-appeal, paused-draft, public-version and linked-decision-error states. They verify reflow, landmarks, native error-link focus and reduced-motion styles and reuse the integrated computed-contrast/screenshot module. Only synthetic PNGs and report.json/index.html/README.md may be uploaded, for seven days. Capture completion, contrast status and persisted-state verification remain separate fields. Actual browser zoom, screen-reader/device/human operating acceptance remains unrun.

## First published native execution

[Draft PR #36](https://github.com/OpenCoven/psyche-research/pull/36) first published exact source `7419846da627321fb0b2a3c845d3ab93494e4b74`, tree `0caea3c1818b128ff1c053e8208f035d2c3e6098`. All five remote blobs and the tree matched the staged source, and the exact unsigned commit bytes were independently reconstructed before moving only the owned local branch to that commit. The working tree was clean. No GitHub merge, deployment or credential change occurred.

[Run 42442146450](https://github.com/OpenCoven/psyche-research/actions/runs/42442146450), native moderation job 128613433131, reached Chromium and failed at the first adversarial POST helper with `Renderer expression failed`. That helper used page-context fetch; the application's no-connect CSP forbids that request path. The raw terminal log and the three-file incomplete artifact 13601941663 (ZIP SHA-256 `b910e6ef0824554cbcc69ef0b7a4d613d53e952fe431cddad41e5a337478786a`) are retained. No screenshot or complete workflow result is claimed from this attempt.

The driver now makes adversarial POSTs through a native same-origin form with the real CSRF token and waits for its response document. Public JSON is loaded by navigation and read through DevTools response capture, rather than page fetch. It also records the main-frame request identifier/MIME type and value-free renderer exception classes. CSP, CSRF, role/refusal checks and all workflow/database/contrast assertions remain intact. No application header or other production source changes. Syntax/diff checks pass; the corrected source requires its own exact-head execution.

## Current-source baseline

Main integrates assistance-boundary PR #35. [Run 42441312642](https://github.com/OpenCoven/psyche-research/actions/runs/42441312642) is terminal success on exact SHA `bb2c47ea2584118f7ffd9e53d8189b585c0a8ad4`; all checkout logs confirm it. Application job 128610931587 ran 163 tests in 135.112 seconds, ten dedicated PostgreSQL skips, 153 executed. PostgreSQL job 128610931600 ran all 35 tests in 42.181 seconds without skips, including the moderation pause/competing-decision race. Browser job 128610931476 passed eighteen page/viewport states, 21 linked-error keyboard activations, 37 screenshot states, zero failed/unmeasured contrast cases and its separate revision-two/paused-intake/zero-publications postcondition. CodeQL is separately successful. None of these results qualifies the new browser harness before its own exact-head CI executes.

PR #34 remains another owner's draft at `81a8ad08dac7ad97683248342c0c489e24bdd838`. Its PostgreSQL 18 results do not qualify main or this candidate. Its exact workflow patch passed a dry `git apply --check` against the candidate without application or integration. The latest maintenance CLI collection failed remote transport; the connected REST refresh supplies all issue/PR/ruleset/run and head check/status collections. Raw inventories retain all 25 worktrees. No cleanup or owner release is inferred.

## Local validation and first failures

| Command or check | Actual result and scope |
| --- | --- |
| Existing Python runtime / package-pin comparison | Python 3.13.16; all eighteen installed versions match unchanged requirements. |
| `python archive/tests/run_browser_moderation.py --prepare-only` | Passed: four synthetic submissions, paused intake and zero publications. Browser checks unrun. |
| CSRF-enforced HTTP rehearsal using the preparation/postcondition helpers | Full decision/appeal/capacity sequence and exact database postcondition passed. First attempt used Django Client's default multipart encoding and correctly received 415; corrected to the actual URL-encoded form contract. No safeguard changed. |
| `LOCAL_DEVELOPMENT=1 DATABASE_PATH=… python manage.py test archive.tests.test_moderation archive.tests.test_form_rendering --verbosity 2` | Seven tests in 2.159 seconds, OK, no skips, on original base 3c09787. Current-main CI above covers these unchanged tests. |
| `node --test archive/tests/browser_review.test.mjs` | Three contrast-reference tests passed, no skips. |
| Rendered-form target review before/after an appeal | Four cases passed. The original broad submit selector also reached header logout; scoped primary-form selectors now identify exactly one decision/capacity control, and the keyboard helper rejects ambiguity. This is HTTP/HTML evidence, not native rendering. |
| `node --check archive/tests/browser_moderation.mjs`; `python3 -m py_compile archive/tests/run_browser_moderation.py`; `git diff --check` | Passed. |

All raw local scripts/logs and source manifests remain under ignored `var/moderation-audit/`. Prior source, status and blocked-audit narratives were copied with verified hashes before preparing this publication receipt; their first failures remain preserved. The owned branch was fast-forwarded from 3c09787 to current main only after backing up all five candidate files. The exact moderation status patch was reapplied, preserving the assistance owner's new section. No other worktree was changed and no new local commit was needed for that fast-forward.

## Local browser startup limits

| Probe | Actual terminal result |
| --- | --- |
| Raw CDP Chromium 156 and matching Playwright 1.64.1 with explicit Chromium sandbox | SIGTRAP before page creation; first logs retained in the earlier moderation owner's receipt. |
| Matching Chromium 149 / Playwright 1.61.1 | SIGTRAP, fatal sandbox initialization input/output error (5). |
| Matching WebKit 27.2 / Playwright 1.64.1 | Child abort trap 6; launcher exit 134, no page. |
| Playwright 1.63.0 default launch from terminal | SIGTRAP, fatal Mach-port bootstrap error 141. Its default sandbox-disabling flag is explicitly recorded; this was a synthetic runtime diagnostic only. |
| Supported persistent JavaScript executor, explicit sandbox | SIGTRAP, sandbox initialization error (5). The installed CommonJS client required the supported createRequire loader after two ESM import failures, before any browser launch. |
| Same supported executor, installed Playwright defaults | SIGTRAP, Mach-port bootstrap error 141. Actual default launch flags are recorded. |
| Fresh task-owned Chromium 156 with loopback DevTools port, host resolver denying other hosts, and a clean private profile | PID 37465 exited SIGTRAP before DevTools readiness, fatal Mach-port bootstrap error 141. This diagnostic's sandbox-disabling flag is recorded; it did not change the prepared CI contract. |

No application page, screenshot or native moderation result is claimed from these failed probes. The successful assistance-owner receipt's exact harness hash was verified and its port connection method inspected read-only; its existing browser was never attached or stopped. The port-mode diagnostic tested a supported connection difference and failed independently. UID 501 remains unresolved and native/browser services and local container runtimes were unavailable on the last checks. No identity or host-bootstrap workaround was introduced. The new native moderation workflow must execute on its published exact source; retain its first actual result and resolve findings without dropping assertions.

## Publication authority and remaining gates

The user authorized scoped Vercel Git disconnection, moderation-candidate commit/push and a draft PR, then explicitly authorized isolated headless checks. That authority persists for this test-only continuation of the same moderation objective; it excludes merge and deployment. The earlier continuation incorrectly treated source approval as exhausted by one snapshot and raised an unnecessary second request. That interpretation is superseded; no further approval is required for this bounded source/draft-PR/CI step. No authority for a separately governed action is inferred.

Fresh authenticated official project-only Vercel GETs confirm a null Git link, zero environment entries, unchanged protection and the same seven historical terminal ERROR deployments before publication. The prepared five-file source is published in draft PR #36 under the existing approval. Inspect the corrected native job and allowlisted artifact, verify actual persisted postconditions, retain first failures and qualify the changed source before any integration recommendation. No new independent review of this test-only harness is claimed; existing sensitive production-code reviews retain their original scope. Actual WorkOS, protected hosted/provider/off-host recovery, policy adoption and human accessibility/operating acceptance remain separate, and dependency #4/issue #5 stay open until their full evidence is complete.
