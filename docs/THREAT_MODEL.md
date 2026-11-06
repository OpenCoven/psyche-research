# Psyche Research threat model

Status: proposed pilot model, recorded 2026-11-04. This document is a review checklist, not a security certification. Implementation and test evidence belong in the project status and verification record; a control described here is not automatically implemented.

## Scope and ownership

The proposed first release is one server-rendered Django application, a relational database on one operator-controlled host, and deliberately bounded intake. It stores structured manuscript text and links rather than accepting manuscript file uploads, executing submitted code, crawling repositories, or rendering fetched previews. The core path must operate without a model provider or familiar.

The neighboring `OpenCoven/research` checkout is a separate researcher workspace with agent research, source, and media contracts. It is not evidence of an approved archive charter. Narrow local inspection of its Markdown and `coven-docs/content` found no archive charter or prior publication decisions. Earlier discussions remain unverified. `coven-docs/content/docs/guide/ecosystem.mdx` establishes that the implementing repository owns its facts and experimental integrations remain labeled until release evidence exists. This archive therefore owns its publication facts and must not inherit review, runtime authority, retention, or security claims from neighboring products.

## Assets and actors

| Asset or actor | Trust and permitted access |
| --- | --- |
| Anonymous reader | Public, approved versions and explicit withdrawal/correction notices only; no draft identifiers, queue metadata, account directory, or author contact details. |
| Contributor | Own drafts, own submitted snapshots, moderation explanations addressed to them, revision requests, and appeal requests; cannot mutate another contributor's work or publish. |
| Human moderator | Private queue and necessary decision evidence; may request changes, reject, publish an exact eligible version, or record a withdrawal. A moderator cannot approve their own work. |
| Operator | Deployment, accounts, backups, incident recovery, intake pause, and documented exceptional administrative actions; not an invisible scientific review board. |
| Familiar or model output | Untrusted assistance. No standing application account, session cookie, database connection, production secret, publication authority, or unrestricted private corpus access. |
| Database and backups | Confidential manuscripts, contact/account data, sessions, audit events, decisions, and publication snapshots. Backups carry the same confidentiality requirements as the database. |
| Submitted text, URLs, repositories, and future files | Attacker-controlled input, including content submitted by a previously trusted contributor or returned by a model. |

One founder can hold several operational roles. The application still must preserve actor identity, version identity, conflict disclosure, and self-approval prevention. Giving the founder a moderator role does not create an independent reviewer.

## Boundaries and required controls

| Boundary | Credible attack or failure | Required control | Evidence required before a hosted pilot |
| --- | --- | --- | --- |
| Anonymous to authenticated views | Guessed UUID/ID exposes a private title, manuscript, or appeal. | Resolve through actor-scoped queries; fail closed with non-revealing errors; no public drafts or previews. | Cross-account and anonymous route matrix, including export, history, errors, and search. |
| Contributor to moderator | Role input, hidden form field, direct POST, or forged object owner publishes work. | Authorization at every mutation, trusted server-side owner assignment, CSRF, no mass assignment, least-privilege roles. | Direct request tests with contributor, unrelated contributor, inactive account, moderator, and superuser. |
| Moderator to own work | Moderator or operator self-publishes through an alternate route. | Server-side author/actor conflict rejection on every publication route; no generic admin mutation that bypasses the workflow. | Role combinations and admin bypass attempts fail without creating public content. |
| Draft to decision | Author edits after review; stale tab approves different content. | Freeze the submitted snapshot or bind decisions to revision/digest; allow edits only through an explicit state transition; transactionally reject stale decisions. | Stale submission/decision tests and persisted snapshot comparisons. |
| Concurrent mutations | Duplicate POST, interrupted response, or competing moderator creates duplicate publication or overfills queue. | Database constraints, transactions, idempotent transitions, bounded retry behavior, explicit stale-state errors. Single-host SQLite must serialize writes safely; a process-local lock alone is insufficient. | Duplicate/retry tests, concurrent capacity tests against the actual supported database, and no partial state on failure. |
| Private to public | Query, template, sitemap, feed, export, debug log, cache, or storage route leaks pending material. | Dedicated public query filtered by accepted publication records; public rendering reads immutable approved snapshot; no debug in production; no manuscript/contact bodies in logs; private responses prevent shared caching. | Sentinel tests across every public route, cache-header checks, redacted error/log inspection. |
| Untrusted text to browser | Stored XSS through HTML, Markdown, SVG, names, titles, or error echo. | Default HTML escaping, no unsafe rich-text rendering, restrictive CSP, no inline event handlers, safe content type, `nosniff`, no user-supplied HTML marked safe. | Malicious text fixtures render escaped and do not execute in actual browser QA. |
| Untrusted text to database/commands | SQL, template, shell, or prompt injection. | Parameterized ORM, no template execution, no shell interpolation, no routine code execution, no model-directed tools. | Injection fixtures remain inert; static review finds no dynamic execution path. |
| URL to network/browser | SSRF, metadata service access, credentials in URLs, `javascript:` links, IDN ambiguity, redirects, malicious external page. | Bounded HTTPS links, reject credentials and control characters, no automatic server fetch, no previews, safe external-link attributes and clear external-link treatment. Validation is not proof that a remote site is safe. | Reject unsafe schemes/userinfo/local IP literals; prove submission and rendering perform no network fetch. DNS rebinding is irrelevant only while the no-fetch invariant holds. |
| Upload boundary | Multipart upload fills disk or supplies active content. | File uploads are unavailable in the first release; reject file-bearing requests, cap request bodies at proxy and app, do not create public media endpoints. | Multipart/oversize requests rejected with no stored file; deployed proxy limit verified. Future uploads require an independent storage/scan/preview review. |
| Internet to session | Credential stuffing, fixation, CSRF, cookie theft, open redirects. | Framework password hashing and session rotation, POST-only logout, CSRF, bounded login attempts, secure/HttpOnly/SameSite cookies, HTTPS, host allowlist, safe redirect handling. | Session and redirect tests; deployment checks; HTTPS/browser cookie inspection. |
| Intake to capacity | Spam, Sybil accounts, unbounded drafts, giant submissions, abuse-report flood, repeated appeals. | Operator-mediated account invitations without prestige screening; explicit queue/draft/text limits; persistent rate limits; bounded appeals/reporting; intake pause checked at write time. | Exact boundary tests, account crossover tests, concurrent tests, pause behavior, restart persistence of limits. |
| New version to endorsement | Revision inherits a review/vouch for an earlier manuscript. | Phase reviews/vouches out of first release; do not display availability claims or endorsement UI. Before enabling, store exact publication version, scope, actor, conflict disclosure, status, and revocation history. | No implemented feature silently labels moderation as peer review; future version-bound tests before release. |
| Reputation to decisions | Stars/followers/votes bias admission, queue position, discovery, or visibility. | Keep any later experiment isolated from production workflow and sorting. Default disabled; no reputation fields in admission/publication queries or public ranking. | Architecture/import/query review and input perturbation tests showing identical admission, queue, browse/search results, and visibility. |
| Familiar to authority | Manuscript prompt injection exfiltrates other submissions or causes publication. | No agent integration in the first release. Any future assistance accepts explicitly selected, minimized material and returns a labeled suggestion to a human; no publication credentials or autonomous appeals. | Core end-to-end path succeeds with no model keys/network; future agent sandbox and output provenance tests. |
| Backup to recovery | Inconsistent SQLite copy, lost WAL, leaked backup, restore overwrites live records, tampered backup. | Online database backup API or offline quiesced backup; integrity check; restrictive file permissions; encrypted off-host storage before pilot; restore into an empty target; explicit operator cutover. | Restore drill with private draft, account, audit history, approved version, correction, and withdrawal; record hashes and restore duration. |
| Deployment to users | Debug mode, untrusted proxy headers, wrong secrets, stale build, broad database permissions. | Fail-closed environment configuration, checked secret strength, HTTPS and host/proxy configuration, pinned dependencies, least-privilege process, reviewed migrations, exact revision evidence. | Production-system checks, dependency audit, staging rehearsal, migration/rollback evidence, operator approval. |

## Publication and withdrawal invariants

A submission being complete does not make it public. Moderation checks completeness, rights, privacy, safety, and abuse; it does not establish scientific validity. Publication records must identify the human actor, exact source snapshot, decision, and publication time. Public pages must explain these distinctions without implying independent review.

A published snapshot is immutable through ordinary author and moderator editing. A correction or revision creates a new version with a reason and clear relationship to earlier versions. Public history must not leak private moderation notes or draft revisions. Stable version URLs and downloadable citation metadata identify the exact version; current-version links explain when a newer version exists.

A withdrawal has a reason, actor, time, scope, and visible tombstone. A safety/privacy withdrawal must suppress unsafe body content from every public version, search, export, preview, cache, and future feed; preserving a citation is not a reason to keep harmful material accessible. The operator documents cache purge limits and any exceptional legal retention. Withdrawal is distinct from rejection and must not silently destroy the decision history.

## Retention, logging, and incident posture

Collect only account details and manuscript metadata necessary for the bounded pilot. Do not require GitHub, affiliation, employer, followers, stars, payment, or public legal-name disclosure. A moderator should see contact data only when needed for operating the submission. Public authorship fields must be explicitly contributor supplied and previewed before publication.

Request logs should use route names, status, duration, and opaque correlation identifiers. Avoid raw URL queries, manuscript text, contact details, passwords, authorization values, session cookies, and appeal/report bodies. Aggregate queue age, error counts, and moderation effort are useful; public analytics must not fingerprint readers. Any hosting or error-monitoring provider needs a reviewed data boundary before private intake.

Published research is intended to remain citable; private drafts, rejected submissions, appeals, sessions, logs, and backup generations need separate retention policies. The operator must document the policy actually implemented, how exports and erasure requests work, what remains in rotating backups, and the date of eventual expiry. A stated retention period is not implemented until the purge/export path is tested.

On suspected leakage or authorization bypass, pause intake and publication, restrict affected serving routes, preserve minimal confidential incident evidence, rotate exposed credentials if any, assess affected people, and restore service only after targeted regression tests and operator review. Notification or external communication requires a human decision and must not be delegated autonomously to a familiar.

## Unverified gates and residual risks

This plan does not establish a hosted environment, domain, TLS, persistent secrets, operator identity verification, legal approval, reviewer pool, independent appeal decision maker, monitoring provider, encrypted off-site backups, penetration test, accessibility conformance, or production recovery. Those require current evidence and, where applicable, explicit approval.

Invite-based intake limits exposure but does not prove participants are honest or protect against compromised accounts. Link-only artifacts reduce archive storage risk but can rot or change and do not preserve reproducibility; contributors should use an existing durable repository and cite a version/commit/checksum where possible. An archive without DOIs must honestly offer stable application URLs and citation exports rather than promise DOI registration.

Single-host SQLite is a proposed low-capacity pilot choice. It needs actual write-contention and backup evidence and an explicit migration threshold; a successful local happy path is insufficient. A host or database operator can read private material, and privileged database access can bypass application audit constraints. Do not describe application audit events as tamper-proof.
