# Coven Research status and resumption record

Updated 2026-11-04. **Pilot NO-GO.** The user selected Vercel, with managed PostgreSQL required for durable hosted data. No Vercel project/domain, provider/region, monitored operator contact, spending cap, policy adoption, new persistent credentials, deployment or outreach has been authorized. [Draft PR #12](https://github.com/OpenCoven/psyche-research/pull/12) is open and unmerged; main remains the initial 6f6914b8aebf42075947731c6f7a57b4ba34fd91. Refresh the current PR head and checks before using any earlier evidence.

## Verified checkpoint and current work

Checkpoint 1cc4ac30bae305b393eb5e2bc10bbcd325c81de4 has tree 9a93808be4eebe7bf5836c77ab7d1390e54b69cf. [Exact-head CI run 41830970609](https://github.com/OpenCoven/psyche-research/actions/runs/41830970609) passed both jobs: 71 tests found in the SQLite job, 66 executed and five dedicated PostgreSQL skips; PostgreSQL 16.15 executed those five live tests with no skips. Checkout logs confirm the exact SHA. These prove their tested scope, not Vercel deployment, provider recovery or human accessibility acceptance.

The implemented path includes private resumable drafts, optimistic saves, frozen exact-content submissions, bounded queues/rates, explicit moderator permissions and conflicts, self-approval prevention, append-only publication/decision/audit records, search/citations, new correction versions, whole-work withdrawal tombstones, private reports/appeals and exports. No runtime LLM, submitted-code execution, remote fetching, file uploads, reputation signals, fabricated research or human endorsements are present. Reviews/vouches are unavailable in the first pilot. Read [DECISIONS.md](DECISIONS.md) for architecture and trust boundaries.

Current recovery slice adds an offline-only `prepare_restored_archive` command with exact expected host/port/database and connected-database checks, explicit recovery-mode opt-in, Vercel-serving refusal, atomic verification/session revocation/rate reset/intake pause/audit, redacted failures and no serving cutover. Six local guard/rollback tests passed, with independent agent review. The consolidated local command `LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py test --verbosity 1` ran 78 tests in 14.688 seconds, OK with six explicit PostgreSQL-backend skips (72 executed). System checks and migration drift checks passed. This does not claim the new PostgreSQL logical-recovery test ran locally. The PostgreSQL CI suite now requires a representative custom-format dump/restore into a newly created disposable test database, restored private/public/history/withdrawal assertions, recovery preparation, and proof that the source is unchanged. Follow the current-head CI result before claiming this slice accepted. SQLite restore evidence does not substitute for this check, and a CI logical dump does not establish provider PITR or encrypted off-host recovery.

## Milestones and dependencies

| Issue | Outcome | Milestone | Depends on | State |
| --- | --- | --- | --- | --- |
| [#1](https://github.com/OpenCoven/psyche-research/issues/1) | Delivery epic | All | Child evidence | Open |
| [#2](https://github.com/OpenCoven/psyche-research/issues/2) | Research, governance, decisions | M0 | None | Drafted; human adoption pending |
| [#3](https://github.com/OpenCoven/psyche-research/issues/3) | Foundation, CI, database | M0 | #2 engineering recommendation | Local and PostgreSQL CI pass at checkpoint; actual Vercel build pending |
| [#4](https://github.com/OpenCoven/psyche-research/issues/4) | Identity/private intake | M1 | #3 | Implemented; tested within stated scope |
| [#5](https://github.com/OpenCoven/psyche-research/issues/5) | Human moderation/appeals | M1 | #4 | Implemented; tested within stated scope |
| [#6](https://github.com/OpenCoven/psyche-research/issues/6) | Publication/corrections/withdrawal | M1 | #5 | Implemented; tested within stated scope |
| [#7](https://github.com/OpenCoven/psyche-research/issues/7) | Familiar boundaries | M2 | #5 | Playbook and no-runtime boundary implemented |
| [#8](https://github.com/OpenCoven/psyche-research/issues/8) | Operations/accessibility/recovery | M2 | #6 | PostgreSQL logical recovery slice; browser/provider acceptance outstanding |
| [#9](https://github.com/OpenCoven/psyche-research/issues/9) | Pilot/onboarding/release packet | M2 | #2,#6,#7,#8 | Draft packet; NO-GO |
| [#10](https://github.com/OpenCoven/psyche-research/issues/10) | Optional human reviews/vouches | M3 | #6,#9 | Deferred and unavailable |
| [#11](https://github.com/OpenCoven/psyche-research/issues/11) | Isolated reputation research | M3 | #9 | Protocol only; collection/scoring disabled |

Critical path: #2 → #3 → #4 → #5 → #6 → #8 → #9. The graph is acyclic; #9 does not depend on #10/#11. Shared migrations and overlapping service edits have one owner. Policy research, bounded independent test work and code review may proceed in parallel. Every implementation issue contains scope, dependencies, observable criteria, security/tests/evidence/recovery, effort and self-contained goal/resumption prompts. [plan.json](plan.json) is the planning snapshot; live issue bodies and current CI are authoritative for later evidence. Native GitHub milestone/label creation is unavailable through the current connector, so milestone/priority data is explicit in the issues and this map.

## Remaining gates and exact next action

Complete and independently review the PostgreSQL logical recovery slice, push it to PR #12, follow all checks to terminal and update issues with the exact head/result. Then use [VERCEL.md](VERCEL.md) and [RELEASE.md](RELEASE.md) to prepare a concrete protected staging approval once the real team/project, provider/region/roles, domain, monitored contact and spending cap are known. Do not create resources, credentials, accept agreements, approve/merge the PR, deploy, send invitations or open intake by inference.

The browser service was rechecked during this cycle and still reports no available browsers/apps, a browser-host failure and native startup failure. Actual rendered desktop/mobile, keyboard, zoom, contrast and screen-reader acceptance remain unrun. Vercel CLI 64.7.0 is installed, but a read-only lookup of psyche-research failed with “fetch failed,” including a session-only hostname-resolution attempt; no project ownership or authentication state was inferred from that error. No Vercel project was linked or created.

Actual hosted build/TLS/proxy/cookies/cache/logs, provider pooling/role restrictions, encrypted off-host restore/PITR, post-snapshot safety/access reconciliation, human retention/policy/license adoption and founder operating acceptance remain required. Recovery preparation does not stop other serving processes or reconcile restored passwords, moderator grants, takedowns or erasures; keep the candidate offline until those are reviewed. The full goal remains active.

## Evidence history and ownership

[Initial implementation history](evidence/IMPLEMENTATION_HISTORY.md) preserves exact first failures, harness corrections, sensitive-code findings, migration/recovery/logging repairs, commands and intermediate counts. [Initial CI receipt](evidence/ci-41830343693.json) is historical; the linked exact-head checkpoint is stronger later evidence. Synthetic fixtures remain confined to tests. Agent code review is not scientific peer review or security certification.

Discovery found only a README at the initial commit, no issues/PRs/runs and one unprotected branch; the authenticated GitHub connector had admin/push/triage permissions. The neighboring OpenCoven/research workspace had retained work and was left untouched; no earlier archive charter was found in the narrow documentation search. GitHub writes use the connector because CLI credentials are unavailable; public Git fetch works with command-scoped hostname resolution. No machine-wide DNS or credential settings were changed. Preserve ownership and recheck live state rather than using this discovery snapshot as current permission evidence.

## Issue #2 governance slice (2026-11-06)

Branch `docs/issue-2-governance-20261106` from main `b46613f` makes admission, founder capacity, accessibility and wind-down explicit for contributors. The public policies page states that pilot accounts are invitation-only and renders the effective intake state, configured limits and per-field character limits from the running application; POLICIES.md gains matching draft sections, RUNBOOK.md the closure steps, and DECISIONS.md D011 the founder operating model and the reconstructed seven product principles. The uneven per-save size allowance across writing scripts is tracked in [issue #22](https://github.com/OpenCoven/psyche-research/issues/22). [The governance review](evidence/GOVERNANCE_REVIEW_20261106.md) holds the policy-by-principle inspection, the dated primary-source recheck, commands, first failures, independent review and limits. Automated headless Chromium rendering at `61aefbd` found no reflow overflow from 320 to 1280 CSS px, AA text contrast and a correct heading, landmark, keyboard and in-page link order for the new section; human assistive-technology and cross-browser acceptance remain unrun. Founder confirmation of the principles and adoption of the policies remain human gates; issue #2 stays open and the pilot remains NO-GO.
