# Issue #22 input-bound qualification

Recorded 2026-11-06. This is an uncommitted, unpublished local slice on `fix/issue-22-script-fair-limits-20261106` in the isolated `psyche-research-input-limits` worktree, based on qualified PR #21 head `6966ea96f0018e26d91523ac361d74b54d43e0c3`, tree `9a20ec083272d4f6031ea4c1035ab7b7fa9f138c`. [Issue #22](https://github.com/OpenCoven/psyche-research/issues/22) was unassigned with no competing claim when work began; the planning comment records ownership. The original candidate, branding, moderation and governance worktrees remain untouched. The full goal remains active and incomplete; pilot NO-GO; real intake paused.

## Defect and resulting behavior

The former 96 KiB encoded-request cap refused valid multilingual forms before field validation. Native textarea values count a line break once, but submitted CRLF pairs counted twice in Django field validation. Supplementary characters also had inconsistent native-browser and server counts. These are different manifestations of a mismatch between the published field allowance, browser input and the encoded form boundary.

New submission saves normalize CRLF and CR to LF before form validation and storage, and enforce each field's existing native browser maxlength in UTF-16 units. A supplementary character such as 𐐀 or 😀 counts twice; combining sequences can consume multiple units. Each submission field now states its limit, and the editor and policies page explain the count. The model lengths, choices, upload refusal, forty-field cap, mutation-rate limits, account permissions, migration history and publication service code are unchanged.

The request cap is now 512 KiB, or 524,288 bytes. The ten text fields total 46,600 UTF-16 units. Each unit needs at most nine bytes when UTF-8 form encoding is percent escaped; serialized CRLF needs six bytes per logical line break. The worst text contribution is therefore 419,400 bytes, leaving 104,888 bytes for small field names, choices, CSRF and revision metadata. The largest exercised full synthetic form, with all fields including eight valid Unicode artifact URLs at their limits, is 417,840 encoded bytes. The cap still rejects over-limit Content-Length before form parsing or downstream work. It raises the global pre-parse allowance by 5.33 times, so independent abuse-bound review remains required; the change is not a hosted load qualification.

[MDN's maxlength reference](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/maxlength) was fetched on 2026-11-06 and confirms native limits use UTF-16 units. [The HTML textarea specification](https://html.spec.whatwg.org/multipage/form-elements.html#the-textarea-element), fetched the same day, defines the API value used by maxlength with normalized LF line endings. The regression implementation follows those contracts. Documentation and HTTP/form tests do not replace actual rendered-browser acceptance.

Existing stored drafts, frozen snapshots and published digests are not rewritten. New saves use the normalized representation. A legacy draft saved through a direct client with more supplementary characters than its browser allowed remains readable/exportable but must fit the native limit to save again. A retry of a submission frozen before this normalization change receives a controlled conflict if its old CRLF snapshot differs from the normalized retry; the regression verifies no duplicate version and subsequent moderator publication preserves the original snapshot and digest. Review these compatibility limits before integration.

## First failures and runtime

The first exploratory test invocation accidentally used the shared Django 5.2.19 environment. Its `var/input-limits-first.log` is retained but is not candidate qualification evidence. The runner was corrected to the existing read-only, hash-verified Django 6.1.2 and asgiref 3.13.0 package overlays; all eighteen requirement versions were verified. Shared virtualenv packages and other owners' overlays were not modified.

On the correct Django 6.1.2 runtime, the first seven-test regression run failed in 0.837 seconds with 41 failing subcases and one error: valid multilingual forms returned 413; an ASCII form with eight CRLF-separated links returned 400; textarea CRLF limits failed; lone CR remained unnormalized; supplementary-character overlimits were accepted; direct service save of a valid CRLF boundary failed. The exact first log is `var/input-limits-django612-first.log`. After the initial repair, seven tests passed in 0.940 seconds. The final expanded tests include valid full-form saves, one-unit-over field refusal with unchanged drafts, displayed limits, no-parse 413 and multipart 415 behavior. Two final compatibility cases prove that a legacy supplementary-character draft remains readable/exportable without mutation on refusal, and that a legacy frozen CRLF retry conflicts while later publication preserves the exact old snapshot/digest. The full suite was rerun after those additions; its earlier 141-test pass remains in the structured history.

## Executed checks

All qualified child processes use `/Users/buns/Documents/GitHub/OpenCoven/psyche-research/.venv/bin/python` with `PYTHONPATH=/Users/buns/Documents/GitHub/OpenCoven/psyche-research-django-main/var/django-main/packages:/Users/buns/Documents/GitHub/OpenCoven/psyche-research-main-refresh/var/main-refresh/packages`, `LOCAL_DEVELOPMENT=1`, `PILOT_APPROVED=0` and an isolated synthetic database in this worktree's ignored `var/`. The structured receipt records exact argument arrays, paths, source hashes, durations and log hashes. The production check uses a separate ephemeral test-only secret and `research.example.invalid`; no secret value is recorded or persisted.

| Check | Result |
| --- | --- |
| `manage.py test archive.tests.test_input_limits archive.tests.test_guarantees.HTTPBoundaryGuarantees --verbosity 1` | 27 tests in 12.362s, no skips, exit 0. |
| `manage.py test --verbosity 2` | 143 discovered in 31.905s, ten explicit PostgreSQL skips, 133 executed, exit 0. |
| `manage.py migrate --noinput` on a fresh isolated database | Exit 0. |
| `manage.py makemigrations --check --dry-run` | No migration changes, exit 0. |
| `manage.py check --fail-level WARNING` | Exit 0. |
| `manage.py verify_archive` | Exit 0. |
| `python -m pip check` with the same overlays | Exit 0; all eighteen pinned versions match. |
| `manage.py check --deploy --fail-level WARNING` with an ephemeral test-only secret | Exit 0. |
| `manage.py collectstatic --noinput` | Exit 0. |
| `git diff --check` | Exit 0. |

The eleven new tests cover ASCII, accented Latin, Arabic, Chinese, Japanese, Korean, Deseret and emoji. Each free-text field is checked at its native limit and one unit above. LF, CRLF and CR are checked at and above textarea limits. Valid artifact URLs exercise the 8,000-unit aggregate field. Real HTTP/form/service writes verify stored values, preserved revision on refusal, private error links and saving with intake paused. Hard-bound and multipart probes assert downstream work and form parsing are not reached on refusal.

The PostgreSQL CI job is prepared to execute `archive.tests.test_input_limits` alongside the ten existing live PostgreSQL guarantees. That workflow has not run for this uncommitted source. Base PR #21's successful CI is evidence for the base only. Local SQLite tests do not prove PostgreSQL, provider pooling, PITR, off-host recovery, actual browser or human acceptance.

## Identity, review and continuation

[The structured receipt](input-limits-verification-20261106.json) hashes eighty application, template, static, test, workflow and dependency files. Its source-manifest SHA-256 is `ef18d676121a9897c937193bbaaf8b37413e8dca1485f454f4f3cec6f6183a41`. This identifies an uncommitted source set, not a Git revision or CI-qualified release. The first logs and synthetic databases remain private and ignored; no research or participant material was used.

Independent review is pending. The implementation author's inspection is not an independent review, scientific peer review or security certification. The session prohibits spawning agents without an explicit request; no reviewer agent was started. The independent governance branch `2c759a3` has newer policy/capacity copy that must be reconciled by its owner before integration; this slice does not copy or overwrite it. No service edits or migrations overlap that work.

Resume by verifying this source manifest and current ownership, obtaining independent review of the cap/count/normalization and legacy-draft behavior, addressing findings, then obtaining any required source-publication authority and following exact-head application/PostgreSQL CI to terminal. Do not reuse the earlier snapshot-only publication authorization for unrelated source. Actual browser/AuthKit, named protected staging/provider/roles/recovery/off-host scope, operator/contact/audience/window/cap, deployment authorization and human acceptance remain separate unmet parts of the original full goal. Keep intake paused, reviews/vouches unavailable and reputation disabled.
