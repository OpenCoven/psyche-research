# Release candidate integration audit

**Incomplete engineering qualification; pilot NO-GO.** Reviewed application revision: `fcd937a4da3e230c5329b09fbdb69b83181351d0`, tree `6dec7f78fdfd6e16238d15a78acf8a4592234825`, branch `candidate/release-qualification-20261105`. [STATUS.md](STATUS.md) is the current resumption record. [Qualification evidence](evidence/RELEASE_CANDIDATE_20261105.md) maps every goal requirement to evidence; [the previous audit](evidence/RELEASE_CANDIDATE_INPUT_20261105.md) remains historical.

The candidate consolidates drafts #16–#19, local deployment/callback repairs and Psyche Research branding. Independent review found consumed-refresh reuse after process loss and post-refresh validation failure. The repair durably consumes tokens before provider exchange and keeps token authority outside ordinary session saves. Migration 0006 adds the credential table without rebuilding publication history. Legacy WorkOS sessions require fresh sign-in; reversing 0006 discards credential state and is not a session-preserving rollback.

The full local suite passed 126 tests in 24.803s with nine PostgreSQL skips (117 executed), including actual child-process loss, real-file concurrency, independent commit observation, stale saves, expiry/finalization races, logout and restore cleanup. Fresh migration, drift, system/deploy settings, archive verification, static collection and dependency checks passed. Independent scoped reviewers have no unresolved findings. This evidence does not establish PostgreSQL, real AuthKit, rendered browser, hosted or human acceptance.

## Integration recommendation

Keep the candidate local until Vercel Git deployment behavior and publication authority are resolved. Renew trusted-host Vercel access, then obtain authorization for the exact project-only Git disconnect and branch/draft publication described in STATUS. Verify the absent link before publishing and retain the manual deployment guard. Run exact-head application and all nine live PostgreSQL tests on the supported CI runtime, inspect execution and repair findings before recommending merge. No current-candidate PostgreSQL or hosted CI result exists.

Final-candidate rendered checks remain blocked by the unavailable computer-use host. Keep keyboard, narrow/zoom/contrast and human screen-reader acceptance distinct from historical Safari, HTTP and template checks. WorkOS provider login remains unverified; the prior local credential-save approval remains valid and authorizes neither new keys nor hosted credentials.

Source integration, protected staging, provider/off-host recovery, human policy/license/retention adoption, accountable operation and pilot activation retain separate evidence and authorization gates. Keep real intake paused. Publication and moderation imply no scientific validation; reviews/vouches are unavailable and reputation has no product influence.
