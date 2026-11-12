# Public waitlist implementation plan

> Execute locally with the executing-plans and test-driven-development skills; obtain independent whole-branch review before launch.

**Goal:** Complete the attached public website and waitlist brief through an approved Vercel launch, hosted controlled registration, operator observation, deletion and rollback.

**Spec:** `/Users/buns/.codex/attachments/bbcb3843-3b25-4bf6-8960-20a8541ffc1e/pasted-text-1.txt`.

**Architecture:** Reuse qualified PR #40 source as foundation in an isolated worktree. Add an isolated Django waitlist settings/URL configuration and app; production contains only waitlist tables and uses a separate managed PostgreSQL project with distinct runtime, operator and migration roles. The public runtime has no account, archive, submission or operator routes. Operators use offline management commands with a separate role and private files.

**Decisions:** A separate Django deployment reuses existing framework/TLS safeguards without deploying an archive surface. A third-party form would add a processor and weaker control of storage; a second frontend framework would duplicate the established deployment. Use a quiet editorial design, responsive cards and a simple server-rendered form with no JavaScript dependency, analytics, remote fonts or outbound email. These are implementation choices under the user's safe-preparation instruction. Production launch, credentials, costs and policy adoption require the final concrete request.

## Global constraints

Keep PILOT_APPROVED=0, research intake paused, reviews/vouches unavailable and reputation disabled. Preserve all owner worktrees, synthetic staging protection and automatic-deployment disablement. Collect only email, reader/researcher/both interest, optional name and consent/version/time. Never collect manuscripts, uploads or research material. Return the same confirmation for new and existing addresses and never publish contact data or status.

## Review focus

Concurrent duplicate and capacity races; address harvesting through responses and logs; runtime escalation to export/delete; accidental archive routes or staging credentials; pause/failure/rollback preserving private records.

### Task 1: Isolated collection and privacy

- [ ] Write failing HTTP tests for registration, unchanged duplicates, consent/validation, disabled collection, size/files/CSRF, generic errors and absence of archive/operator routes.
- [ ] Add `waitlist` models, migration, form, services, middleware, views, isolated settings/URLs and templates; database-serialized capacity and global/per-address abuse budgets, default pause and no reflected values in success/error responses.
- [ ] Verify focused tests and migration drift. Exercise concurrency on disposable PostgreSQL.

### Task 2: Operators and durable access boundaries

- [ ] Write failing tests for restrictive export permissions, safe spreadsheet text, deletion without argv email, pause/resume and retention cleanup.
- [ ] Implement offline operator commands plus exact PostgreSQL role grants and production database identity checks; runtime cannot read name/interest, export, delete or change pause.
- [ ] Propose 90-day retention, 1,000 registrations, 30 attempts/minute, 200/day and three per address/day. Export expires under the same retention/deletion obligations. Delete data through the operator workflow; document backup erasure limits and routine purge scheduling.

### Task 3: Qualification and launch packet

- [ ] Review personal-data handling, authorization and storage independently; fix material findings with regression tests.
- [ ] Run complete archive suite and isolated waitlist suite, PostgreSQL concurrency/role denial/failure tests and real desktop/mobile/keyboard browser checks; retain exact source and receipts.
- [ ] Prepare a concrete launch request naming exact revision, new Vercel project/hostname, isolated Neon project/database/roles, credentials, operator/contact, privacy notice, proposed USD 25 incremental monthly cap and pause/rollback. Refresh actual provider plans/access before requesting approval.
- [ ] After applicable approval, provision only approved resources, migrate serially, deploy manually, verify anonymous HTTPS/route boundaries, identify one controlled registration privately in hosted storage/operator export, delete it, exercise pause/rollback and restore approved collection state. Preserve receipts and report human acceptance separately.

## Evidence ledger

Initial main refresh: c3a75d9 merges #37 after PR #40's base; PR #40 head 4ec5e41 has eleven terminal successful checks. Isolated worktree starts at that qualified head; original checkout has 28 owner branding edits. Protected synthetic rehearsal source 5150063 and its existing receipts remain separate. No production authorization is inferred from those receipts.
