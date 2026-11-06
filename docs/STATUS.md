# Psyche Research status and resumption record

Updated 2026-11-05 (America/Chicago). **Release candidate incomplete; pilot NO-GO; real intake paused.** This goal prepares one reviewed engineering candidate for an explicit integration decision. Merge, hosting changes, deployment, new persistent credentials, spending, agreements, outreach and launch remain outside authorization.

## Candidate and ownership

Owned worktree: `/Users/buns/Documents/GitHub/OpenCoven/psyche-research-candidate`, branch `candidate/release-qualification-20261105`. Application revision `fcd937a4da3e230c5329b09fbdb69b83181351d0`, tree `6dec7f78fdfd6e16238d15a78acf8a4592234825`, includes drafts #16–#19, local deployment/callback repairs and branding. Later documentation commits must preserve its application hashes. [Input manifest](evidence/release-candidate-inputs-20261105.json) records source SHA/tree identities and the branding patch hash. Original worktrees and uncommitted edits were preserved; the three-way branding conflict retained the newer staging ownership text before reconciliation.

Fresh GitHub REST reads confirmed main `d218b6bd2e72388fe00d928f465804c65e6ea306` and open draft stack #16 `f7ebe30` → #17 `86f5645` → #18 `f9ae407` → #19 `2abdebcc`. Their Actions runs remain terminal success; #19's Vercel status is failure. They do not cover this candidate. No source was pushed, PR approved/merged or hosting resource changed. [Previous status](evidence/STATUS_CANDIDATE_INPUT_20261105.md) and [previous release audit](evidence/RELEASE_CANDIDATE_INPUT_20261105.md) preserve superseded narrative. Existing evidence remains historical truth.

## Repair and review

Independent authentication review reproduced consumed-refresh reuse after actual process loss and after a synthetic post-refresh signing-key outage. The prior outer request transaction rolled back replacement-token persistence on process loss. Migration `0006_durable_workos_credential` adds token authority outside ordinary Django session saves. Its durable claim clears the old token before provider exchange; finalization requires the same live claim and enabled identity. Downstream views run outside that transaction. Pending requests wait at most five seconds; dead claims expire after thirty seconds without restoring a token. Stale saves, logout, revocation and restore cannot resurrect credentials. Legacy WorkOS sessions require fresh sign-in; builds never run migrations.

Independent authentication and publication/recovery reviewers examined the final application revision with no unresolved scoped findings. Review also found and verified correction of an intermediate legacy/malformed-handle logout defect. Agent review is neither scientific peer review nor security certification. [Qualification receipt](evidence/RELEASE_CANDIDATE_20261105.md) records first failures, exact commands, reviewer scope and limitations.

## Current evidence

| Gate | Evidence | State |
| --- | --- | --- |
| Full application suite | Application revision: 126 tests in 24.803s, nine explicit PostgreSQL skips, 117 executed. | Pass within application/SQLite scope. |
| Fresh migrations, drift, system/deploy settings, archive verifier, static collection, dependency consistency | Seven checks on isolated local data, with an ephemeral test-only deployment key; structured commands and log hashes in receipt. | Pass. |
| Independent authentication review | 39 authentication/durability tests in 4.699s plus one real-file durable commit/rollback drill in 1.389s, no skips. | No unresolved scoped finding. |
| Independent publication/privacy/recovery review | Final revision: eight recovery/migration tests in 1.565s and two logout/copied-handle tests in 0.149s, no skips; source-unchanged raw/ORM restore probe. | No unresolved scoped finding. |
| Live PostgreSQL concurrency and logical recovery | Nine dedicated tests prepared, including durable refresh and credential restoration cleanup. | Unrun on candidate. UID 501 unresolved; no supported local runtime. Existing Docker CI supplies required PostgreSQL 16 service/clients. |
| Rendered final candidate | Fresh computer-use inventory: zero apps/browsers, native startup failure, browser host unavailable. | Blocked; no final-candidate focus/narrow/zoom/contrast/screenshots. Prior Safari observations remain revision-specific history. |
| Actual WorkOS | Existing staging setup and local credential-save approval preserved in WORKOS.md. | Live flows and exact issuer unverified. No provider key transferred by this task. |
| Source publication and exact-head CI | Earlier Vercel Git link attempted automatic previews; local guard remains unexercised. Current Vercel API reads reject expired access; CLI reports fetch failed. | Blocked pending trusted-host access renewal and applicable Git-link control/publication authorization. |
| Hosted/provider/human acceptance | STAGING_ACCEPTANCE.md and PILOT.md define separate gates. | Unverified; no launch or intake authority inferred. |

## Exact next action and authority

Resolve the publication precondition before any push. The concrete proposal is to disconnect only Vercel project `0xbuns/psyche-research` (`prj_KpONwA0jddpWRBIVQGt22FbZX7t2`, team `team_VLpvr923t3nLPeaUaLxABctM`) from `OpenCoven/psyche-research`; verify the Git link is absent and retain deployment inventory; publish the exact reviewed candidate as a branch/draft PR; run and inspect exact-head Actions. This project-level change requires applicable separate authorization and trusted-host Vercel authentication renewal. Do not reconnect Git, deploy or alter other projects, secrets, protection, domains or existing deployments. A local `git.deploymentEnabled=false` file does not prove platform behavior.

After authorized safe publication, require current application CI and all nine PostgreSQL tests without skips, including concurrency, guards and logical recovery. Preserve first failures and repair findings before recommending integration. If a supported isolated runtime becomes available independently, run the unchanged dedicated suite there; never point destructive fixtures at serving data or bypass OS identity checks. Restore browser access for available final-candidate checks; human accessibility remains separate.

This release-candidate goal remains active and incomplete. Source consolidation, reproduced defects, durable repair, independent review and new evidence constitute progress; this is not a no-progress blocker audit. An older protected-staging goal's blocked status does not carry over to this goal. Preserve the approved local WorkOS secret-store scope without asking again. Reviews/vouches remain unavailable, reputation disabled and real intake paused.
