# Pilot candidate and acceptance audit

Status: local implementation candidate, **NO-GO for deployment, invitations, real intake and launch**. User-selected target: Vercel with managed PostgreSQL. This packet is reviewable preparation, not deployment approval. No real participant, paper, review, vouch, reputation score, production credential, provider project or legal agreement has been fabricated or created. Read [STATUS.md](STATUS.md) for exact current checks and delivery state.

## Requirement-to-evidence audit

| Requirement | Current authoritative evidence | Acceptance state |
| --- | --- | --- |
| Inspect actual repository, ownership and overlap | Initial6f6914b local/remote tree, permissions, branches/issues/PRs/runs checks in STATUS; neighboring research workspace left untouched | Verified at discovery; refresh before publication/merge |
| Research alternatives and compare three approaches | RESEARCH.md primary-source comparison with dates, DECISIONS D001/D002/D007 | Draft recommendation; no unsupported superiority claim |
| Contributors/readers/formats/incentives/academic compatibility | RESEARCH.md, PILOT.md positioning, onboarding, FAQ and unsent invitation | Drafted; demand/reuse and venue compatibility remain hypotheses |
| Governance, policies, architecture, threat, costs/risks | POLICIES.md, DECISIONS.md, THREAT_MODEL.md, RUNBOOK.md, VERCEL.md | Drafts implemented; human adoption, real cost cap/contact missing |
| Highest-priority epic and dependency-linked implementation issues | GitHub#1–#11, plan.json and STATUS acyclic map | Created and every URL fetched; native milestone/label mutations unavailable |
| Each issue complete and resumable | Every child body includes outcome/scope/dependencies/criteria/guidance/security/tests/evidence/recovery/effort and two prompts | Verified after creation; maintain as evidence advances |
| Open eligibility, bounded capacity and honest labels | Forms, services, policies and public templates; no GitHub/payment/social fields; explicit finite limits | Locally tested; operator scheduling/adoption pending |
| Save/resume/submit complete private research | SubmissionForm, save_submission, optimistic revision, canonical frozen JSON/digest and owner export; guarantee tests | Implemented and locally tested; actual-client interrupted workflow pending |
| Role authorization and self-approval prevention | Explicit moderator group, service checks, no generic admin; direct cross-account/role/superuser tests | Locally tested; real account/role procedure requires authorized human |
| Human decisions, history, pause, conflicts and appeals | Frozen digest/revision-bound Decision, required conflict declaration, append-only records, Capacity controls, exact-decision Appeal and discovery UI | Locally tested; non-self conflict recusal is a human control, no independent panel promised |
| Versioned public publication/search/citation | Version/work URLs, canonical immutable snapshots, chronological latest-only discovery/search, JSON metadata, escaped plain text | Locally tested; stable domain/host and long-term operation unverified |
| Revisions/corrections/withdrawal | New moderated versions and change notes, all-version tombstones, no body in browse/search/public exports; regression tests | Locally tested including representative restore; external copies cannot be recalled |
| Optional human reviews/vouches | Issue#10 explicitly next milestone, public UI says unavailable, no endorsement store | Deliberately phased; version/scope/conflicts/revocation tests required before enablement |
| Familiar assistance and core without LLM | ASSISTANCE.md, no runtime provider/key/fetch/execution dependency, offline test workflow and inert injection fixtures | Implemented boundary/playbook; no autonomous assistance integration |
| Optional isolated reputation experiment | REPUTATION.md protocol, issue#11, no collection/score/product joins, input perturbation and query review | Disabled/unimplemented; separate opt-in shadow approval before any data collection |
| Upload/XSS/injection/SSRF/privacy boundaries | Text-only form boundary, 96KiB/per-field limits, multipart rejection, bounded HTTPS validation/no-fetch, ORM/escaping/CSP, sentinel route/export/log tests | Locally tested; actual proxy/body/log/cookie behavior unverified |
| Abuse, rates, capacity, concurrency and retries | Bounded reports/appeals, persistent rate buckets, service capacity locks, idempotent exact retries, real-file queue/publication races | SQLite tested; dedicated PostgreSQL races require actual live CI/backend evidence |
| Database, migration safety, backup/restore | Hash-pinned deps/migrations, six guards, historical-data roundtrip, bounded consistent snapshot and representative isolated restore tests | SQLite verified; PostgreSQL provider backup/PITR/restore not proven by SQLite |
| Vercel-target durable persistence | DATABASE_URL/verify-full/CA/timeouts/pooling contract, native WSGI manifest, no ephemeralSQLite fallback, vendor PostgreSQL guards and live tests | Implemented candidate; actual provider/region/roles/pooling/TLS/build pending |
| Observability and operations | Health, private aggregate metrics, safe route/status telemetry, constant Gunicorn errors, pause/account/role commands, RUNBOOK | Locally tested; real monitoring/rotation/operator response unverified |
| Accessible/responsive rendered client | Semantic templates, labels/error states/skip link/focus CSS, compiler and28 actual server-rendered route checks | Actual browser/mobile/keyboard/zoom/contrast/screen reader unrun: computer-use host unavailable |
| Retention/export/recovery/wind-down | Owner/public exports, explicit retention proposal and manual-maintenance limitation, session expiry/restore revocation, operator cutover/withdrawal reconciliation, wind-down plan | Policy/tool scope documented; private erasure/audit redaction procedure unexercised and gates real intake |
| Independent sensitive-code review | Separate agent tests and reviews found/fixed auth/version/appeal/migration/recovery/log/PG rate races; current review evidence in STATUS | Agent review, not human scientific peer review/security certification; latest backend/host still needs scoped acceptance |
| Founder pilot plan/metrics/go-no-go | PILOT.md four-week10 participants/10 submissions proposal, capped queue/time, feedback and pause/stop measures | Drafted; founder adoption and actual participant acceptance missing |
| Reviewable release and deployment approval | Repository source/CI/configuration packet; eventual draft PR and exact head recorded in STATUS | No merge/deploy/launch authorized; approve a concrete target/revision/audience/cost only after gates |

## Local validation contract

Run the README commands from a clean checkout with Python 3.13 and hash-verified requirements. The test suite uses clearly labeled synthetic records in isolated files/schemas, never public archive seeds. SQLite mode explicitly skips dedicated PostgreSQL tests rather than implying backend proof. The PostgreSQL CI job creates an ephemeral test_ database, opts into disposable schema tests and never accesses a participant database. Successful CI must be associated with the exact PR head; a synthetic merge is not delivery proof.

An actual Vercel build and protected preview require an approved project and separate nonproduction database/environment. Keep private participant content out of all builds, static output, preview credentials, fixture bundles and logs. Native Django static collection is only for checked repository CSS/assets; no runtime data belongs there. Do not connect production DB secrets to every PR preview or migrate shared databases during a build.

## Remaining decisions and required permissions

The user supplied Vercel as the target. The actual project/domain, managed PostgreSQL provider/region and role/backup arrangement, monitored operator contact, monthly cash cap, founder schedule, policy/content-license/retention adoption, actual-client accessibility acceptance and any specialist review are not supplied or accepted. Prepare these concretely, then seek the corresponding authorization. Do not treat a hosting preference as permission to provision credentials, accept terms, spend, deploy, launch, approve a PR or send invitations.

The immediate engineering gate is current-head PostgreSQL CI and any resulting repair. The external acceptance gates are actual browser access, approved protected staging target/provider, restored-provider drill and human operating acceptance. A passing local/CI result leaves these unverified. Keep the thread goal active while required scope remains; use the status record to resume without duplicating completed work.
