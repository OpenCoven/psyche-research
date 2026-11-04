# WorkOS login and project setup

The user selected WorkOS for login and requested project creation on 2026-11-04, then completed account sign-in. The Django integration is implemented on `feat/workos-login` in the isolated `psyche-research-workos` checkout; its base is the tested staging-documentation tree. The shared checkout's Psyche Research branding edits belong to another task and are untouched. The real Psyche Research staging project now exists in the authenticated account, with its local callback, initiation and sign-out destinations verified. The user subsequently selected option 1 to approve saving this existing staging key and separate local session secrets in the previously specified ignored mode-0600 local store. The separate Django and Fernet secrets are generated there and their owner, file mode, distinct values and ignored status verified without displaying values. Its provider key remains absent because dashboard control is unavailable; exact issuer and real AuthKit sign-in remain unverified. This local approval must not be requested again and does not authorize hosted credentials, new provider keys, identity enrollment or deployment.

## Login contract

Set `AUTH_PROVIDER=workos` to select AuthKit. In that mode the sign-in page contains one ordinary HTML form that starts WorkOS authentication; local password login and local password-change routes are unavailable. An incomplete configuration fails at startup rather than falling back to passwords. `AUTH_PROVIDER=local` preserves the existing local-development/operator-provisioned path; it is the default until real WorkOS configuration is supplied. Choosing a provider does not open intake or set `PILOT_APPROVED`.

The flow uses the official Python SDK 10.6.0, hash-pinned with its full transitive closure. A CSRF-protected POST creates a five-minute server-side state and PKCE verifier, stores only a random browser nonce in the Django session and redirects to the fixed WorkOS API origin. The GET `/accounts/workos/initiate/` endpoint starts the same SDK-backed flow immediately for externally initiated AuthKit sign-in, without another button click. Both entry points have persistent rate limits. Pending attempts are bounded to 1,000 globally and one per browser nonce; capacity rejection occurs before creating a browser session. The callback locks and deletes the matching state before exchanging the authorization code, passes the verifier and disables automatic exchange retries. Replayed, expired, duplicate-parameter and other-browser callbacks do not reach the exchange endpoint.

The application verifies RS256 signatures against the configured client's HTTPS WorkOS JWKS, exact configured issuer, expiry, issued-at, subject, session ID and client ID. An explicit audience must match this client; ordinary first-party WorkOS session tokens can omit it. Impersonation and unverified email identities are rejected. The immutable provider subject and client ID must match an explicitly enabled `WorkOSIdentity` linked to an existing active local account. Email addresses, external roles and permissions cannot choose or create a local account or grant moderator access. A successful sign-in rotates the Django session key; a disabled binding or deactivated local account loses access on its next request.

Only an encrypted WorkOS session and minimal identity data are retained inside the existing private server-side Django session. Tokens are not returned to JavaScript, public cookies, logs or exports. The SDK refreshes expired access tokens without automatic retries; the replacement is verified again and cannot change the bound local subject. A signing-key outage while checking a current token returns a redacted 503 before a mutation and preserves the existing local session. Invalid sessions are cleared. A failed refresh requires fresh sign-in, since retrying a potentially consumed rotating refresh token is unsafe. Local authentication has an absolute eight-hour maximum even across refreshes. Provider-side revocation is enforced when the access token expires and refresh is denied; it is not an instantaneous webhook revocation feature. Local role and account checks still apply on every request.

Sign-out is a CSRF-protected POST that clears the local session before redirecting to WorkOS's session logout URL. Configure the provider sign-out redirect too. CSP permits the fixed WorkOS API origin for form redirects only when WorkOS mode is selected; scripts, arbitrary embedded content and submitted-link fetching remain disabled. Actual browser redirect/CSP/cookie behavior still needs live acceptance.

## Configuration and secrets

| Setting | Value and handling |
| --- | --- |
| `AUTH_PROVIDER` | `workos` in the configured environment; `local` for the existing offline development path. |
| `WORKOS_API_KEY` | Secret environment-scoped server key from the selected staging application. Never expose it to the browser or place it in an issue, source, CLI argument or public build log. |
| `WORKOS_CLIENT_ID` | Exact application client ID from the new project's staging environment. Bind identities to this ID, not just to a user ID shared across applications. |
| `WORKOS_REDIRECT_URI` | Exact allowed callback ending in `/accounts/workos/callback/`. Use HTTPS when hosted. HTTP is accepted only for explicit local development on localhost or loopback. No wildcard callback. |
| `WORKOS_ISSUER` | Exact issuer for this environment's access tokens, from its verified configuration. WorkOS documents multiple issuer forms and trailing-slash differences; do not infer or normalize the value. |
| `WORKOS_COOKIE_PASSWORD` | Separate secret Fernet key: URL-safe base64 encoding of 32 random bytes, as required by the pinned Python SDK. Generate through `cryptography.fernet.Fernet.generate_key()` into an approved secret store, not chat or shell output. Never reuse the Django key or share it with production. |
| `DJANGO_SECRET_KEY`, database and allowed hosts | Existing production contract in VERCEL.md. WorkOS keys do not replace the Django session/CSRF secret or authorize another host/database. |

The API base URL and JWKS origin are fixed to `https://api.workos.com`; an ambient SDK base-URL variable cannot redirect credentials. SDK HTTP and JWKS operations have five-second timeouts. All provider exceptions are redacted in responses and application telemetry. Separately verify that hosting access/error logs omit callback query strings; application route-only telemetry does not configure a provider's own logs.

See the [WorkOS Python guide](https://workos.com/docs/authkit/vanilla/python), [official Python SDK](https://github.com/workos/workos-python), [session token reference](https://workos.com/docs/reference/authkit/session-tokens) and [token validation guidance](https://workos.com/blog/verify-workos-access-tokens-in-your-own-api), checked 2026-11-04. The pinned installed SDK's sealing API requires a Fernet key even though some general framework examples describe an arbitrary cookie password. Tests exercise the pinned implementation and real RSA signatures.

## Verified staging project

After the earlier device authorization expired, the user completed account sign-in. Official CLI 0.24.0 `whoami` verified team `Val` (`team_01JSV5TKHJECJTSRMFSF04AEQC`) and organization `org_01JSV5TKEPBHV5WA9Q1ZKFMJ7N`. Project listing found no Psyche project. A single `project create 'Psyche Research' --no-production --yes --json` created this staging-only project, then project listing, environment-scoped `whoami` and the signed-in dashboard independently read back its identifiers. The existing SlopOS CLI profile and its credentials were not repointed or reused.

| Resource | Verified value |
| --- | --- |
| Project | `project_01M6KVC1HJRRSX2H4WZQ86KM10`, Psyche Research |
| Staging environment | `environment_01M6KVC1JEV7TSP86SZ6ZZJ7MF`, sandbox; no production environment |
| Default application | `app_01M6KVC22RHQBPBRA217AWPKC6`, dashboard default name Val's Application |
| Client ID | `client_01M6KVC1Y1QA30MA8F86ADXQ7W` |
| AuthKit domain | `sure-tranquility-41-staging.authkit.app` |
| Default callback | `http://127.0.0.1:8011/accounts/workos/callback/` |
| Initiate login URI | `http://127.0.0.1:8011/accounts/workos/initiate/` |
| Default sign-out return | `http://127.0.0.1:8011/` |

The CLI reported both URI lists empty before mutation. Each replacement list was dry-run first, applied with the exact environment ID, then read back. The initiation setting is not exposed by this CLI version or its REST catalog; it was saved through the signed-in dashboard and reopened to verify the exact value. No CORS entry is needed for this server-rendered redirect flow. The project's automatically available server key remains masked and has not been copied, rotated or used by this application. No provider user, paid plan, invitation, agreement, role grant or production resource was created by this continuation.

These are read-only resumption commands; do not create the project again. Retain the system keyring and use explicit environment scoping:

```sh
WORKOS_MODE=agent npx workos@0.24.0 whoami --environment-id environment_01M6KVC1JEV7TSP86SZ6ZZJ7MF --json
WORKOS_MODE=agent npx workos@0.24.0 authkit redirect-uris list --environment-id environment_01M6KVC1JEV7TSP86SZ6ZZJ7MF --json
WORKOS_MODE=agent npx workos@0.24.0 authkit logout-uris list --environment-id environment_01M6KVC1JEV7TSP86SZ6ZZJ7MF --json
```

The first local receipt writer failed after creation returned because `Path.open` does not support `opener`; creation was not retried. A read-only list recovered the exact project identity before further changes. The writer now uses exclusive mode-0600 files in an ignored mode-0700 directory and redacts credential fields before displaying output. Private raw receipts remain under `var/workos-account/`; their non-secret results and this first failure are recorded in [the implementation evidence](evidence/WORKOS_IMPLEMENTATION.md). See [WorkOS projects](https://workos.com/docs/authkit/projects) and [CLI documentation](https://workos.com/docs/authkit/cli-installer).

Next, restore computer-use access, transfer the selected existing staging server key privately into the approved local store without replacing its generated secrets, verify the exact token issuer, and exercise real sign-in/sign-out and external initiation before claiming provider acceptance. Fresh native inventory now fails service startup and the browser host is unavailable. Scoped CLI whoami still confirms the exact staging environment/client; CLI 0.24.0 and its REST catalog do not expose retrieval of this existing server key. Do not create a replacement key or switch an unrelated profile to get past this access failure. WorkOS account creation still cannot enroll someone into the archive: only an explicitly enabled local identity binding permits entry. Keep loopback callbacks on staging and keep production secrets and private participant records out of this rehearsal. Actual hosted hostnames must come from the selected Vercel project before registering them; no hosted domain or project ID has been invented. Preserve existing URI lists when adding that host, and do not replace a default or remove an entry without its applicable authorization.

Read-only Vercel CLI discovery subsequently verified bunsdev and owner access to the proposed 0xbuns team on its existing Pro plan. No archive project was created or linked. A new dedicated psyche-research-staging project remains a proposal; do not reuse the unrelated existing Node research project by inference. Resolve the team, provider/region/roles/recovery target, audience/window, operator/contact and cap in STAGING_ACCEPTANCE.md before the applicable provisioning and deployment authorization. Verify protection on every actual deployment URL before loading synthetic records. Local WorkOS credential approval does not authorize Vercel or database credentials.

## Link an existing local account

An operator verifies the WorkOS user ID against the intended person through the approved account channel, then links that immutable ID to an existing local user. The command creates no person, changes no password, and grants no group, staff or superuser permission. It refuses reassignment of an existing local binding and duplicate provider subjects. The reason and exact binding are recorded in private append-only audit history.

```sh
python manage.py link_workos_identity \
  --username EXISTING_LOCAL_USERNAME \
  --client-id VERIFIED_STAGING_CLIENT_ID \
  --subject VERIFIED_WORKOS_USER_ID \
  --reason 'Approved account binding reference'
```

To revoke that binding, repeat the exact identifiers with `--disable`. Re-enabling or moving an identity requires a separately reviewed operator change rather than a silent email match. Existing moderator grants still use the established explicit local procedure and do not transfer from WorkOS claims. Do not grant a role merely to make a login test pass.

## Migration, recovery and acceptance

Migration `0005_workos_identity_login_attempt` creates the identity and short-lived login-attempt tables without accounts, credentials, role grants or open intake. Rehearse it on the isolated staging database before any hosted rollout; builds still must not run migrations. Backups must include identity links and encrypted server sessions. Restore preparation now clears pending WorkOS attempts as well as Django sessions and rate buckets, preserves identity links, pauses intake and appends the recovery event atomically. Reconcile identity disablements, account deactivations, WorkOS session revocations and compromised encryption/API keys since the snapshot before any cutover. Reversing migration 0005 deletes provider bindings and pending attempts; it is not a lossless rollback. Prefer forward repair and an approved isolated restore.

Local evidence and first failures are in [the WorkOS implementation receipt](evidence/WORKOS_IMPLEMENTATION.md). Fixture tests do not establish a real WorkOS project, successful provider sign-in, browser accessibility, Vercel deployment or founder pilot acceptance. Independent sensitive-code review remains required before live use. Keep real intake paused and record live AuthKit sign-in/sign-out, session expiry/revocation, wrong-issuer/client rejection, actual CSP/cookies/proxy/log behavior and provider access separately when the account and hosting environment are available.
