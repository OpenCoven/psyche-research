# WorkOS login and project setup

The user selected WorkOS for login and requested project creation on 2026-11-04. The Django integration is implemented on `feat/workos-login` in the isolated `psyche-research-workos` checkout; its base is the tested staging-documentation tree. The shared checkout's Psyche Research branding edits belong to another task and are untouched. Provider account authorization and real project creation remain pending. No fake client ID, API key or project is configured as working authentication.

## Login contract

Set `AUTH_PROVIDER=workos` to select AuthKit. In that mode the sign-in page contains one ordinary HTML form that starts WorkOS authentication; local password login and local password-change routes are unavailable. An incomplete configuration fails at startup rather than falling back to passwords. `AUTH_PROVIDER=local` preserves the existing local-development/operator-provisioned path; it is the default until real WorkOS configuration is supplied. Choosing a provider does not open intake or set `PILOT_APPROVED`.

The flow uses the official Python SDK 10.6.0, hash-pinned with its full transitive closure. A CSRF-protected POST creates a five-minute server-side state and PKCE verifier, stores only a random browser nonce in the Django session and redirects to the fixed WorkOS API origin. Pending attempts are bounded to 1,000 globally and one per browser nonce, with existing persistent anonymous rate limits. The callback locks and deletes the matching state before exchanging the authorization code, passes the verifier and disables automatic exchange retries. Replayed, expired, duplicate-parameter and other-browser callbacks do not reach the exchange endpoint.

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

## Create the project in the user's account

The official WorkOS CLI 0.24.0 is available through npm. `auth status` returned `authenticated:false`. An attempted dashboard-device login produced a user authorization request and then ended with `expired_token`; its code is no longer valid. No dashboard session, new WorkOS project/environment, provider user, API key, paid subscription or external message was created. The browser automation host also remained unavailable. The user must complete a fresh account sign-in before the agent can operate the account.

Use these commands without `--insecure-storage`; retain the system keyring. The team must be identified from the authenticated account before a write. These are the next actions, not commands already completed:

```sh
npx workos@0.24.0 --mode agent auth login
npx workos@0.24.0 whoami
npx workos@0.24.0 project list
npx workos@0.24.0 --mode agent project create 'Psyche Research' --no-production --yes
```

List existing projects first and reuse a matching project owned by the intended team; do not retry an ambiguous create response. CLI `project create` defaults to creating production as well, so `--no-production` is deliberate. The current request authorizes the login/project setup; it does not select a paid plan, accept a new legal agreement, grant unrelated account access or launch the archive. Stop for the applicable user action if those appear. Record the actual project/environment/application IDs and read them back before configuring credentials or callbacks. See [WorkOS projects](https://workos.com/docs/authkit/projects) and [CLI documentation](https://workos.com/docs/authkit/cli-installer).

Configure only the selected staging application's exact callback, an Initiate login URI at `/accounts/login/`, and an exact sign-out return URI at the application root. Keep public signup unavailable while pilot admission remains operator-controlled; no invitations or real users are needed to create the project. Configure local loopback callbacks only on staging. Keep production secrets and private participant records out of previews and this rehearsal. Actual hosted hostnames must come from the selected Vercel project before registering them; no domain or project ID has been invented.

The Vercel integration was offered because it exposes project creation, but installation/connection has not been confirmed. No Vercel project was created or linked. After access is available, inspect the current account/team and existing projects, create or reuse `psyche-research-staging` in the intended team, verify protection on all deployment URLs, then apply the real environment-specific configuration. Database provider/region/cost and actual deployment remain separate unresolved staging requirements in STAGING_ACCEPTANCE.md.

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
