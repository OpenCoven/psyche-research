# Coherent release candidate — 2026-11-11

This candidate combines main `302bbe93452e6e9cc5e6714b5fb9498f7f9e1721` (merged UI #39) with staging source `5150063afbd0316642ac7ca2cbeb4a24cbf8595f` (#38), including canonical qualification `212b622f6b02357a166d81f2e51ed723bb7d0667` (#37). The merge preserves both histories without conflicts. Existing drafts #34/#36/#37/#38 and their owners remain intact. This is source preparation and qualification; no merge, deployment, provider mutation or pilot activation is authorized.

The application models, services, authorization views, forms, migrations and dependency pins match main. Main's seven UI files match exactly, including the new readability stylesheet and the WorkOS form's CSRF-protected action. The integrated changes retain verify-full TLS with OS certificate roots, fail-closed pooled-timeout checks, builder-debug refusal, explicit canonical same-origin logout return, and exact-origin AuthKit CSP. Hosted database endpoint mode and role defaults are unchanged. Browser evidence now fingerprints the new stylesheet and changed UI templates as well as the existing contract sources, so old UI fingerprints cannot stand in for this candidate.

## Qualification and requirement matrix

Exact revision/tree, commands, first failures, final check links, artifact integrity and independent review must be recorded in the candidate draft PR and private execution handoff after qualification. The tests below are required; this document does not claim a passing result before they execute.

| Requirement | Required candidate evidence | Scope limit |
| --- | --- | --- |
| One owned coherent candidate and provenance | Merge ancestry includes exact main, #37 and #38; main UI byte comparison; exact revision/tree and private ownership ledger | Existing drafts and dirty branding retained |
| Application/auth/configuration guarantees | Documented full application suite, configuration tests, system/deployment checks and migration drift | SQLite is local evidence only |
| PostgreSQL 16 and 18 | Exact-head service-container tests on both majors, including concurrency and recovery | No hosted endpoint or pooling change |
| Restricted database roles and immutable records | Exact-head 16/18 disposable role containers and metadata receipts; all checks and shutdown verified | Does not certify actual provider role behavior |
| Multilingual input, reflow, focus and contrast | Exact-head input contract, synthetic screenshots, measurements and independent database postcondition | Human accessibility remains outstanding |
| Moderation/privacy boundaries | Exact-head moderation contract, five isolated contexts, private/public assertions and independent database postcondition | Moderation is not scientific validation |
| WorkOS redirect chain | Exact-head loopback-only application/CSP browser contract accepts configured origin and refuses unlisted origin | No live provider authentication by this candidate |
| Safe source publication and draft delivery | Fresh Vercel Git disconnection/disabled deployment options, disabled manifest, owned branch and one draft PR | No deployment or merge authority |
| Independent engineering review | Fresh review of combined candidate and sensitive boundaries, findings resolved or explicitly retained | Not PR approval, scientific review or security certification |
| Interruption safety | Private commands/logs/first failures, artifact hashes, coverage, ownership, unresolved gates and single next action | Private execution receipts excluded from source/upload |

## Separate deployed-source acceptance

Private reviewed v3 receipts record passing normal hosted signed-in and signed-out phases on deployed source `5150063afbd0316642ac7ca2cbeb4a24cbf8595f`, at 2026-11-11T02:15Z and 02:19Z respectively. Those receipts qualify their original deployment and verifier scope only; they do not qualify this combined candidate. External initiation, browser cookie observations, visible logout-hop/landing/workspace-denial confirmation, actual expiry enforcement, rehearsal-end binding revocation/denial and conditional setting restoration remain separate outstanding acceptance gates. Completed binding, recovery and rollout operations must not be replayed.

Keep `PILOT_APPROVED=0`, intake paused, reviews/vouches unavailable and reputation disabled. Human accessibility, policy and operating acceptance remain open. The original staging deadline is **2026-11-16T09:03:38Z**; this candidate neither restarts nor extends it. No pilot GO is implied.
