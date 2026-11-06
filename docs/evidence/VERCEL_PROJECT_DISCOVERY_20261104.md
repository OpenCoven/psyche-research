# Existing Vercel project and manual deployment proposal

Recorded 2026-11-04 after the credential-approval continuation. This live read supersedes earlier statements that no archive Vercel project exists. It does not establish project-selection approval, a successful deployment, hosted application acceptance or a database. No Vercel configuration, environment variable, resource, protection setting or deployment was changed by this read-only discovery.

## Authoritative observations

The GitHub REST discussion timeline for draft PR #19 contained a Vercel bot failure report. Authenticated Vercel CLI 64.7.0 GET requests independently verified project `prj_KpONwA0jddpWRBIVQGt22FbZX7t2`, name `psyche-research`, under team `0xbuns`, linked to `OpenCoven/psyche-research` with production branch `main` and Django framework. The project was created at 20:19:44.879 UTC, before this discovery; its creation was not an action taken by this continuation. It has no configured environment variables. Its existing protection is `all_except_custom_domains`, not the proposed `all` setting. No credential values were requested for decryption, displayed or copied.

The deployment list contains two terminal errors. Production attempt `dpl_4x41N9e9HeSRQ4fVkrcCeMwdbkiU` used main d218b6bd2e72388fe00d928f465804c65e6ea306. Git-triggered preview `dpl_6TXwAa9r8pEVy9D7vjLZTGTPLaC6` used documentation head 2abdebcc31209782f3dccd23dfbe84f85d787612 from `fix/form-error-summary`. The latter confirms that the previous source publication triggered an automatic preview through the existing integration. Do not treat the earlier source-only intent as proof that no deployment attempt occurred.

Both attempts report `DJANGO_SETTINGS_FAILED`. Full preview build logs identify `django.core.exceptions.ImproperlyConfigured: Set DJANGO_SECRET_KEY to a random secret of at least 50 characters.` The existing startup guard is working; do not weaken it or supply a dummy hosted secret to make the build pass. The empty environment also does not satisfy the managed PostgreSQL, explicit-host, WorkOS or other hosted runtime contracts. GitHub Actions run 41909906944 passed the application/PostgreSQL checks on 2abdebcc; the Vercel build is a separate failed check.

| Actual URL | Anonymous HTTP observation | Limit |
| --- | --- | --- |
| `https://psyche-research-g4z0hpae3-0xbuns.vercel.app/` | 302 to `vercel.com/sso-api`; query omitted from this record. | Failed preview; server-level redirect only, no application/browser acceptance. |
| `https://psyche-research-7hjgao66h-0xbuns.vercel.app/` | 302 to `vercel.com/sso-api`; query omitted from this record. | Failed production attempt; not evidence of a working archive. |
| `https://psyche-research.vercel.app/` | 404; no redirect. | Registered project domain, with no ready application proved. |

The preview detail also records branch alias `psyche-research-git-fix-form-error-summary-0xbuns.vercel.app` with `aliasAssigned=false`. Its intended alias does not establish a reachable protected app. The project domain list has one verified platform domain and no additional entries. The scoped Neon marketplace installation list is empty; this says nothing about an unrelated external Neon account or its entitlements.

## Local reviewable guard

This unpublished branch proposes `git.deploymentEnabled=false` in vercel.json, as documented in [Vercel Git configuration](https://vercel.com/docs/project-configuration/git-configuration), checked 2026-11-04. It expresses the existing requirement that source pushes must not automatically deploy the application. Existing framework, installer and function configuration remain unchanged. The official [versioned deployment guide](https://vercel.com/kb/guide/can-you-deploy-based-on-tags-releases-on-vercel) describes disabling Git auto-deployment before an explicit CLI workflow; this proposal adds no CLI workflow, token or deployment action.

The guard is prepared locally on `fix/manual-deployment-gate` in the isolated psyche-research-vercel worktree, based on 2abdebcc31209782f3dccd23dfbe84f85d787612. It has not been pushed, applied to Vercel or exercised by the platform. The initial publication's behavior must not be assumed from the configuration documentation; resolve the existing Git integration and applicable authority before publishing it. Do not disable the integration, change project protection, alter credentials or retry deployment by inference. The existing PR #19 checkout and the shared branding worktree remain untouched by this proposal.

JSON parsing, exact comparison of every other manifest field against the base, Markdown paragraph/link checks and git diff checks are the local validation scope. No new application-suite or changed-head CI result is claimed for this unpublished configuration. Platform read-back and a deliberately approved publication/build exercise remain required before calling the guard effective.

## Concrete scope still to resolve

| Gate | Prepared choice or evidence | Required next input or proof |
| --- | --- | --- |
| Target | Existing `0xbuns/psyche-research` and actual URLs above. | Confirm Preview-only staging here or a separate staging project; project existence is not selection approval. |
| Git behavior | Automatic preview observed; local guard prepared. | Resolve authority and initial-publication behavior before any further source push or deployment retry. |
| Protection | Existing `all_except_custom_domains`; two generated URLs redirect anonymously. | Approve the exact target and configure/read back `all`, then test every actual URL form with a successful synthetic deployment. |
| Runtime environment | No variables configured; secret guard caused build failure. | Approved separate hosted secrets, explicit hosts and selected database role/endpoint; do not reuse local session secrets. |
| Database/recovery | Prior packet proposes Neon PostgreSQL 16 in US East with separate runtime/migration/backup identities and offline restore target; no scoped marketplace installation found. | Provider account/plan/region, actual entitlement/cost and authorization before provisioning or credential creation. |
| Operator and cost | Prior packet proposes seven-day synthetic rehearsal and USD 50 incremental monthly ceiling. | Named accountable operator, monitored contact, allowed testers/dates and accepted estimate/cap. |
| WorkOS and actual browser | Local credential-save approval is recorded, separate local session secrets exist, provider key/issuer remain absent; native service startup and browser host are unavailable. | Restore computer use, transfer only the approved existing staging key privately and verify real AuthKit; independent review and remaining browser sheet still required. |
| Acceptance | Local/CI and read-only platform observations are scoped above. | Hosted/provider/PITR/off-host recovery and human policy/accessibility/operating acceptance remain unrun. |

Private receipts are in the existing accessibility worktree's ignored mode-0700 `var/vercel-current-readonly/` directory, including sanitized project/deployment/domain metadata, build logs and anonymous HTTP receipts. Mode-0600 records omit secret values and authentication query strings from displayed summaries. Initial CLI requests failed DNS; command-scoped resolution of api.vercel.com from a current DNS-over-HTTPS answer restored reads while retaining ordinary TLS certificate/hostname verification. No machine-wide network settings changed. `vercel inspect --logs` returned exit 1 alongside the terminal failed-build log; that is not an active process or a successful deployment.

The full goal remains incomplete and pilot remains NO-GO. Keep intake paused. The pending consolidated non-secret scope question and computer-use reconnection request must be answered before dependent actions; local credential-save approval must not be requested again.
