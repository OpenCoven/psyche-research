# Issue #2 governance review and evidence

Recorded 2026-11-06 for [issue #2](https://github.com/OpenCoven/psyche-research/issues/2) on branch `docs/issue-2-governance-20261106`, based on main `b46613f`. This record inspects every draft policy against the seven product principles, rechecks the primary sources and their dates, records the contributor-facing admission, capacity, accessibility and wind-down slice, and preserves commands, first failures, independent review and limits. It is engineering and drafting evidence. It is not legal review, scientific peer review, security certification, founder adoption or pilot approval.

## What changed

The public policies page now explains who may submit during the pilot: eligibility is open, but accounts are created only for invited participants, with no public sign-up, request form or waitlist, and that invitation-only admission is a recorded fairness limit. A new "What one founder can sustain" section renders the effective intake state, the configured queue, per-contributor and archive-wide active-work limits and each field's character limit from the running application, describes the fixed one-queued-item rule, the 96 KiB encoded request limit and its uneven cost for non-Latin scripts, and separates enforced limits from the proposed founder schedule, manually tracked pilot totals and pause triggers. It renders configured limits only; queue occupancy and private record counts are never shown. If the capacity row cannot be read, the home and policies pages describe intake as paused instead of failing. The home page's open or paused status now uses the same effective intake check, which also requires pilot approval. The page's wind-down copy describes the export period with its safety and emergency qualifiers, return of pending work unpublished, retention, a minimal static record of published versions, no handover of private material without consent and no successor guarantee.

[POLICIES.md](../POLICIES.md) gains four draft sections: "Pilot accounts and admission", "What the founder can sustain", "Accessibility" and "Pause, closure, and wind-down". Before this change, wind-down existed only as an operator procedure in the runbook and pilot plan, so the policy drafts did not cover it as the issue requires, and no policy made an accessibility commitment. [RUNBOOK.md](../RUNBOOK.md) gains the matching closure steps and [PILOT.md](../PILOT.md) clarifies week-four handling. [DECISIONS.md](../DECISIONS.md) D011 records the founder operating model, assumptions, exclusions, cost drivers, approval boundaries, new proposals and the reconstructed seven principles. `archive/services.py` gains a pure `intake_accepting` helper that mirrors the two existing submission gates without changing them. `archive/tests/test_governance.py` adds ten tests. A follow-up commit groups the digits of each field's character limit, for example 10,000 rather than 10000, after the rendered page was inspected. [Issue #22](https://github.com/OpenCoven/psyche-research/issues/22) tracks the uneven per-save size allowance.

## The seven product principles

The issue asks implementers to preserve "the seven product principles in the epic", but neither the epic body, the planning snapshot nor the repository enumerates them; the original brief is not in the repository. D011 folds nine candidates from the epic outcome and scope, issue #2 and the working instructions into a working list: P1 accessible; P2 open eligibility; P3 bounded founder capacity; P4 private intake; P5 human moderation with distinct trust records, including non-gating reputation; P6 stable versioned publication; and P7 optional assistance and safe input. Founder confirmation of this list is a human acceptance item.

## Policy inspection against the principles

Each cell records whether the section implements the principle (✓), implements it with a recorded limitation (◐) or is neutral (·). Sections were read in full on 2026-11-06 after the review fixes.

| Policy section | P1 | P2 | P3 | P4 | P5 | P6 | P7 | Inspection note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Purpose, eligibility, and scope | · | ✓ | ✓ | · | ✓ | · | ✓ | Content-based exclusions, including material beyond founder capacity, apply equally to everyone; fabricated observations and unsafe file deposits are excluded. |
| Five distinct records | · | · | · | · | ✓ | ✓ | ✓ | Forbids a generic trust seal; a revision never inherits a review or vouch; automated checks are never labelled human judgment. |
| Account and contributor responsibilities | ◐ | ✓ | · | ✓ | · | · | · | External identity links must not become hidden gates; login identifiers stay private. Account recovery is manual through the operator, a usability limit until an approved contact exists. |
| Drafts, submission, and capacity | · | ✓ | ✓ | ✓ | ✓ | · | ✓ | Popularity, affiliation, reputation, donations and familiarity must not affect admission; saving works without an LLM. Required configured values to be understandable in the product, which the page section now provides. |
| Moderation decisions and independence limits | · | · | ✓ | ✓ | ✓ | · | ✓ | Routine intake never executes code or downloads links; conflicted work is held rather than invented reviewers. |
| Corrections, revisions, and withdrawals | · | · | · | ✓ | · | ✓ | · | Snapshots stay immutable; tombstones suppress withdrawn bodies; harmful material is never copied into public explanations. |
| Appeals, complaints, and abuse reports | · | · | ✓ | ✓ | · | · | ✓ | No response time; reporter identity stays private; a familiar cannot decide an appeal. |
| Optional human reviews and scoped vouches | · | · | · | · | ✓ | ✓ | · | Unavailable in the first pilot; version-bound with revocation; no seeded or aggregate endorsements. |
| Familiar and automated assistance | · | · | · | ✓ | ✓ | · | ✓ | No runtime access to private submissions by default; no publication or appeal authority; submission text is untrusted. |
| Reputation research | · | ✓ | · | ✓ | ✓ | · | · | Disabled, isolated, non-gating, with a kill switch and no write-back to production. |
| Privacy, retention, export, and incident handling | · | · | · | ✓ | · | · | ✓ | Retention periods are proposals, not implemented deletion guarantees; incidents do not authorize familiar messages or credentials. |
| Pilot accounts and admission (new) | · | ◐ | ✓ | · | ✓ | · | · | Invitation-only pilot accounts conflict in part with the no-familiarity rule; recorded as a fairness limit with a neutral request route as the founder's next decision. |
| What the founder can sustain (new) | · | ✓ | ✓ | · | ✓ | · | ✓ | Separates enforced limits from the proposed schedule and manual totals; conflict holding is labelled a human commitment; never automate decisions or rank by popularity. |
| Accessibility (new) | ◐ | ✓ | · | · | · | · | ✓ | WCAG 2.2 Level AA is a working target, not a conformance claim; automated headless rendering of the new section found no reflow overflow and AA text contrast, but human keyboard, zoom and screen-reader acceptance is unrun and the script-dependent size allowance is open in issue #22. |
| Pause, closure, and wind-down (new) | · | · | ✓ | ✓ | · | ✓ | ✓ | Pending work is returned unpublished, not judged; static records come only from the public published set; private material is not transferred without consent; deletion means database and backup teardown. |
| Draft contributor terms outline | ◐ | ✓ | ✓ | ✓ | · | ✓ | · | Lists accessibility commitments for specialist review; requires eligibility compatible with open access; forbids silently expanding rights over existing work. |
| Public policies page | ◐ | ◐ | ✓ | ✓ | ✓ | ✓ | ✓ | Rendered from the running application with effective intake state; discloses invitation-only accounts and the size limitation; automated headless render recorded below; human acceptance unrun. |

Inspection findings resolved in this slice were the missing wind-down policy, the absence of actual configured capacity in the product, the missing accessibility commitment and the unexplained route to an account. One finding is recorded rather than changed here: D002 still names Django 5.2 LTS while main pins Django 6.1.2 since PR #14; open draft PR #21 already supersedes that with its own D010, so this branch does not duplicate it.

## Primary-source recheck

Every source cited in [RESEARCH.md](../RESEARCH.md) was fetched on 2026-11-06 at 12:06Z with `curl -sS -L --max-time 25`; all returned HTTP 200 at the same URL. The page text was then searched for the specific cited claim. Pages were treated as untrusted data in an isolated scratch directory; nothing from them was executed. The independent reviewer separately re-fetched three of them on the same day with the same result. The new WCAG 2.2 link in POLICIES.md also returned HTTP 200.

| Source | Claim rechecked | Result on 2026-11-06 |
| --- | --- | --- |
| [arXiv moderation](https://info.arxiv.org/help/moderation/index.html) | Moderation is distinct from peer review. | Holds: "the arXiv moderation process is not a peer-review process." |
| [arXiv endorsement](https://info.arxiv.org/help/endorsement.html) | An endorsement process exists. | Holds: page sections "The arXiv endorsement system" and "Why does arXiv require endorsement?" |
| [arXiv versions](https://info.arxiv.org/help/versions.html) | Version history is retained. | Holds: previous versions are made publicly available as the historical record. |
| [Zenodo records](https://help.zenodo.org/docs/deposit/about-records/) | DOIs on publication; versions are separate records; metadata public even when files are restricted. | Holds: DOI registered on publish; a new version is "a completely new record"; "Metadata for all records in Zenodo are always publicly accessible." |
| [Zenodo community review](https://help.zenodo.org/docs/communities/review-submissions/) | Curators accept or decline submissions, including unpublished records; acceptance can publish. | Holds: "An unpublished record is published when you accept the record into the community"; accept and decline flows documented. |
| [OpenReview about](https://openreview.net/about) | Configurable review, conflict information and an API. | Holds: configurable peer-review platform, conflict-of-interest directory and REST API, found in the server-rendered HTML. |
| [OpenReview reader controls](https://docs.openreview.net/how-to-guides/workflow/how-to-change-who-can-access-submissions-after-the-deadline) | Submission visibility is configurable. | Holds: "Submission Readers" settings change who can read submissions. |
| [JOSS about](https://joss.theoj.org/about) | External human review of research software. | Holds: "a formal peer review process". |
| [JOSS submitting](https://joss.readthedocs.io/en/latest/submitting.html) | AI-use disclosure is required. | Holds: generative AI use "must be disclosed in an 'AI usage disclosure' statement". The page now also lists pre-review screening criteria; the RESEARCH conclusion is unchanged. |
| [PREreview about](https://prereview.org/about) | Review platform with training and community activities. | Holds: review requests, clubs and trainings are linked. |
| [Hugging Face Hub collaboration](https://huggingface.co/docs/hub/repositories-pull-requests-discussions) | Repository discussions and pull requests. | Holds: "Pull requests and Discussions" documentation. |

The differentiation hypotheses H1–H6 in RESEARCH.md remain untested; the recheck confirms only that the cited alternatives still provide the capabilities RESEARCH.md attributes to them. Recheck again before any public competitive claim.

## Acceptance criteria evidence

| Criterion | Evidence | State |
| --- | --- | --- |
| Primary-source comparisons identify existing capabilities and untested differentiation hypotheses. | RESEARCH.md comparison table and H1–H6; eleven of eleven sources rechecked above. | Drafted and rechecked; hypotheses untested by design. |
| ADR recommends a smallest sustainable approach and records assumptions, exclusions, cost drivers and approval boundaries. | D001 approach and D011 assumptions, exclusions, ordered cost drivers, approval gates and new proposals. | Drafted; founder adoption pending. |
| Policy drafts cover rights, privacy, abuse, conflict, appeals, correction, withdrawal, retention and wind-down. | POLICIES.md sections in the table above, including the new admission, capacity, accessibility and wind-down sections; RUNBOOK.md closure steps; `test_policy_drafts_cover_every_required_governance_topic`. | Drafted; not adopted; no legal review. |
| Reputation is optional, disabled or shadow-only and cannot gate decisions; LLM use is optional with no publication authority. | D005, POLICIES.md reputation and assistance sections, REPUTATION.md, ASSISTANCE.md; existing `test_reputation_inputs_do_not_change_public_order_or_admission`, `test_form_never_accepts_identity_state_or_reputation_fields` and moderator-only publication tests; new `test_reputation_and_runtime_model_providers_are_absent`. | Met within tested scope. |

Human gates that remain open: founder confirmation of the seven principles; adoption of dated policy, terms, content-license, retention, admission, accessibility and wind-down choices, including the proposed 30-day export period and a neutral request route; an accountable operator, monitored contact and cost cap; specialist review of the private-material transfer commitment and other jurisdiction-specific obligations; and a decision on issue #22 before real intake. Issue #2 stays open with its needs-acceptance status until those are recorded.

## Independent review

A separate agent reviewed the uncommitted change read-only against the issue criteria, the epic, AGENTS.md and the enforcing code, and reproduced its findings with synthetic probes in a scratch copy. It reported two blockers, nine should-fix items and eleven nits; it confirmed the enforced limit mapping, paused-intake behaviour, export availability, privacy of the page and schedule consistency. Resolutions:

| Finding | Severity | Resolution |
| --- | --- | --- |
| "96 KiB per save" was false: limits are per field in characters, and the encoded request cap costs non-Latin scripts up to nine bytes per character. | Blocker | Page renders each field's character limit from the model and describes the 96 KiB encoded cap and its script cost; uneven allowance filed as [issue #22](https://github.com/OpenCoven/psyche-research/issues/22). |
| D011 and POLICIES.md said contributors see "the values the code enforces". | Blocker | Narrowed to configured limits, effective intake state and per-field limits; fixed-in-code rules described as such. |
| Page said "open" when intake was switched on without pilot approval. | Should-fix | `services.intake_accepting` mirrors both gates; home and policies use it; `test_public_intake_status_matches_whether_a_submission_is_accepted` covers all four combinations. |
| "At most N awaiting" described occupancy that can exceed a lowered limit. | Should-fix | Reworded as admission rules ("accepted only while fewer than N…") for all three limits. |
| D011 omitted accessibility and safe input. | Should-fix | D011 names the nine candidates and folds them into seven, with accessibility as P1; new Accessibility policy section. |
| Open eligibility had no stated route to an account. | Should-fix | Page and new "Pilot accounts and admission" section state invitation-only accounts, no sign-up or waitlist, and the fairness limit. |
| Page wind-down copy dropped "where safe" and emergency shortening. | Should-fix | Both qualifiers added to the page. |
| Runbook lacked the procedure the policy points to. | Should-fix | RUNBOOK.md closure steps added. |
| STATUS and this record cited evidence not yet written. | Should-fix | This section and the final results below were written before commit. |
| No test for the intake gate mismatch. | Should-fix | Added, and mutation-checked. |
| Keyword-coverage test was vacuous. | Should-fix | Replaced with checks for the specific new commitments and the runbook step. |
| Conflict holding presented as if enforced; founder submissions would block a slot. | Nit | Labelled a human commitment; draft recommends the founder not submit during the pilot. |
| Closure deletion needs database and backup teardown. | Nit | Stated in POLICIES.md and RUNBOOK.md. |
| Static record or successor handoff could carry withdrawn snapshots. | Nit | Must be built only from the public published-version set; removed records identified by stable identifier. |
| "Never transferred" conflicts with processors and lawful requests. | Nit | Reworded; processors and legal disclosures left to adopted privacy terms; specialist review flagged. |
| Policies page returned 500 without the capacity row or database. | Nit | Fallback to paused intake without limits; tested for a missing row and a synthetic database error. |
| Copy tests were narrow; no paused-export test. | Nit | Added a response-time promise pattern, conformance overclaims and `test_authors_can_export_their_own_work_while_intake_is_paused`. |
| DECISIONS.md header date and ordering against PR #21. | Nit | Left unchanged to avoid a merge conflict with PR #21, which inserts D008–D010 directly below the header; D011 is dated and appended. |
| PILOT.md "hands off pending submissions" was ambiguous. | Nit | Reworded to decide or return unpublished and to refer open appeals. |
| "Queue full" pause trigger was missing. | Nit | Added to the page and POLICIES.md. |
| Inspection table was too generous. | Nit | Rebuilt above with recorded limitations. |
| The principles are inferred. | Nit | Founder-confirmation gate kept. |

## Independent re-check

The same reviewer re-checked every claimed resolution against the files and code, read-only and without fetching. It found 18 findings fully resolved, findings 9, 15 and 16 partly resolved, and accepted the deferral of finding 18. It raised six new low-severity items. All were addressed before commit:

| Re-check item | Resolution |
| --- | --- |
| Finding 9: this record cited the re-check before it existed. | This section. |
| Finding 15: the page's handover sentence lacked the processor and legal-disclosure qualifier. | Qualifier added to the page; the policy keeps the specialist-review flag. |
| Finding 16: the fallback said published records stay available, which is false during a database outage. | Removed; the fallback now says only that intake should be treated as closed. |
| PILOT.md selected invitees partly by academic affiliation, contradicting "never by affiliation". | Reworded to seek varied practice backgrounds without requiring or selecting on affiliation. |
| POLICIES.md's familiarity rule read as unconditional beside the admission section. | Cross-reference to the recorded pilot tension added. |
| Field character counts: the server counts a submitted line break as two characters while browser `maxlength` counts one; punctuation and line breaks cost extra bytes; artifact links have an 8,000-character total. | Verified with a form-validation probe (text counted as 7,503 characters by the browser rule is refused as 10,002 by the server); the page states the line-break rule, the byte cost and the artifact total; issue #22 scope and criteria extended. |
| Issue #22 named `WriteLimitMiddleware` instead of `BoundaryMiddleware`. | Issue body corrected and re-read. |
| The field-limit test iterated its own list. | It now asserts the list equals every free-text content field. |
| "Start or reopen work" implied authors reopen declined work; home omitted invitation-only accounts. | Reworded to "start a new draft or revision"; home adds that pilot accounts are by invitation. |

The reviewer confirmed privacy of the new view, consistency of the wind-down and schedule numbers across documents, the 88-test result and one-line prose paragraphs.

## Commands, environment and results

Environment: macOS (Darwin 27.2.0), Homebrew Python 3.13, a fresh `.venv` installed with `python -m pip install --require-hashes -r requirements.txt` (Django 6.1.2, `pip check` clean), SQLite local backend with `LOCAL_DEVELOPMENT=1`. PostgreSQL was not run locally; its tests are the six explicit skips and run in CI.

| Step | Command | Result |
| --- | --- | --- |
| Baseline on unmodified main `b46613f` | `LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py test --verbosity 1` | 78 tests, OK, six PostgreSQL skips (72 executed), 39.7 s wall. |
| First run of new tests | `LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py test archive.tests.test_governance --verbosity 2` | 7 tests, 4 failures. Three were the expected policy gap: headings "What the founder can sustain" and "Pause, closure, and wind-down" and the topic "wind-down" were absent from POLICIES.md. One was a test defect: the overclaim check matched the page's own negation "or guaranteed response time", so it was replaced by an assertion that the explicit negation sentence is present. |
| After policy sections | same command | 7 tests, OK. |
| First mutation checks in a scratch copy | six injected regressions, then the unmutated control | All six caught: rendering live queue occupancy, hard-coding the queue limit, raising the enforced link limit without updating policy text, removing the wind-down heading, advertising vouches as available and adding a reputation model field. Control OK. |
| After review and re-check fixes | same governance command | 10 tests, OK. |
| Second mutation checks | three injected regressions, then the control | All caught: deriving "open" from the switch alone, removing the capacity fallback and restoring occupancy wording. Control OK. |
| Full suite after review fixes, and again after re-check fixes | `LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py test --verbosity 1` | 88 tests in 37.7 s, then 88 tests in 35.4 s, each OK with six PostgreSQL skips (82 executed). |
| Django checks | `check --fail-level WARNING`; `makemigrations --check --dry-run`; `collectstatic --noinput`; production `check --deploy --fail-level WARNING` with an ephemeral test-only key and `research.example.invalid` | No issues; no migrations; static collected; deploy check exit 0. |
| Local HTTP render | `runserver --insecure --noreload` on a free loopback port against a freshly migrated empty database, then `curl` of `/` and `/policies/` | Both HTTP 200; capacity section showed paused intake, fewer than 5, one, fewer than 2, fewer than 20, every field limit, 8 links and the 96 KiB note; eligibility copy showed invitation-only accounts. Server stopped afterwards. |
| Digit-grouping follow-up at `61aefbd` | governance tests; the same mutation approach, removing the grouping; full suite; `check`; `makemigrations --check --dry-run` | 10 tests OK; the mutation was caught by the new formatted-value assertion and the control restored; 88 tests in 31.6 s, OK, six PostgreSQL skips; no issues; no migrations. |
| Encoding arithmetic | `urllib.parse.urlencode` of synthetic characters | ASCII 1, accented Latin and Arabic 6, Chinese, Japanese or Korean 9 encoded bytes per character; 10,000 CJK characters in one field encode to 90,008 bytes. |
| Prose format | scratch checker for mid-paragraph breaks, trailing double-space breaks and HTML breaks, self-tested on a bad sample | Every touched Markdown file and the issue #22 body: zero problems. |
| Vercel publication precondition, read-only | `vercel api /v9/projects/prj_KpONwA0jddpWRBIVQGt22FbZX7t2?teamId=team_VLpvr923t3nLPeaUaLxABctM --method GET` with CLI 65.12.1, then the team `repoUrl` project filter | `link` is null and Git `createDeployments` is disabled; no project in that team is linked to this repository. The Vercel connector returned 404 for the same project, so the CLI read is the evidence. Other teams were not rechecked. |

## Automated browser rendering

Rendered on 2026-11-06 with the Chrome for Testing headless shell 156.0.8078.4, driven over the DevTools protocol by a scratch Node 24 script, against commit `61aefbd` served by `runserver --insecure --noreload` on a free loopback port with a freshly migrated empty SQLite database and default capacity. Nothing outside 127.0.0.1 was contacted. The scripts and screenshots stay in the agent's scratch directory and are not committed. The browser and server were started and stopped by process ID.

| Check | Method | Result |
| --- | --- | --- |
| Reflow | Viewports 1280, 640 (the CSS width of 200% zoom at 1280), 390 (phone) and 320 (the CSS width of 400% zoom at 1280) CSS px; document `scrollWidth` against `clientWidth`, and any element of the eligibility, capacity or wind-down sections extending past the viewport | No horizontal overflow and no overflowing element at any width. |
| Text contrast | Computed colour against the nearest opaque background for ten selectors in the new and changed sections | Lowest 5.64:1 (definition text, 14.1 px); notice 7.63:1; links 7.92:1; body text and headings 14.23:1. All are at least 4.5:1. |
| Headings and landmarks | Chromium accessibility tree | One h1. "What one founder can sustain" is an h2 between "Human decisions and finite capacity" and "Rights and privacy", with h3s "Size of a submission" and "When limits are reached". The section is exposed as a region named by its heading. |
| Keyboard order | 40 synthetic Tab presses from the top of the page | Skip link, header links, the issue #22 link in the new section, then the eleven on-this-page links including "What one founder can sustain", the sidebar sign-in and the footer, each with a solid 3 px focus outline. The order follows the visual reading order: content column, then sidebar. |
| In-page link | From a fresh load, the "What one founder can sustain" link activated by synthetic click at 1280 px and by Enter at 1280 and 390 px, polling every 250 ms | Hash `#capacity`; in all three cases the section settles 32 px below the viewport top, the stylesheet's 2 rem scroll padding, within 0.75 s. A measurement inside the main script, taken after the Tab traversal, reported the section out of view; it did not reproduce in the isolated probe, which is the recorded result. |
| Visual inspection | Section screenshots at all four widths, inspected by the agent | The notice, definitions, limit list and paragraphs render legibly with no clipped or overlapping text. This inspection prompted the digit-grouping fix; at `901aa51`, before it, the same overflow, contrast, heading and focus checks gave identical results. |

This is automated rendering in one engine. It is not a human keyboard, zoom, screen-reader or cross-browser test, and it does not exercise the forms. In-page links use the site's existing smooth scrolling, which has no reduced-motion override; that site-wide style is outside this slice.

## Remaining limits

Human keyboard, zoom, screen-reader and cross-browser acceptance of the new sections remain unrun; the built-in browser cannot reach a loopback server started by the agent. The sections reuse existing styles and add no script or form. Exact-head CI and PostgreSQL execution are recorded in the pull request. Hosted, human and legal acceptance are unchanged and remain gates. No deployment, credential, agreement, invitation, payment, merge or PR approval was performed.
