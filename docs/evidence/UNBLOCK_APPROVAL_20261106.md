# Scoped unblock authorization and access

Recorded 2026-11-06. The user explicitly selected “Authorize scoped disconnect and draft PR” in response to the request to disconnect Git only for Vercel project `0xbuns/psyche-research`, verify the link is absent, then commit/push the prepared moderation candidate and open a draft PR for PostgreSQL CI. Scope excludes merge, deployment, Git reconnect, secret changes and changes to other projects. This authorization persists; it must not be requested again because a tool or connection fails.

The candidate remains the exact 78-file [tested source manifest](moderation-verification-20261106.json), aggregate SHA-256 `cf997e88e91c2c2237a15d712c623e24b74b3d518ad5262ec8191bbcba993325`. All source hashes were freshly rechecked after authorization and match. The prior full suite remains 132 tests in 33.925s, ten explicit PostgreSQL skips, 122 executed. No source change warrants repeating it. This continuation prepares a local commit of the existing moderation test/dependency/evidence slice and current authorization record; remote source publication remains conditional on verified Git disconnection.

## Newly observed access

Native app inventory briefly recovered while the browser-tab connector remained unavailable. Dia's existing Vercel session was signed in as `bunsdev`. Actual settings navigation confirmed project `psyche-research` in team `0xBuns`, project ID `prj_KpONwA0jddpWRBIVQGt22FbZX7t2`, at `https://vercel.com/0xbuns/psyche-research/settings/general`. Git settings at `https://vercel.com/0xbuns/psyche-research/settings/git` showed Connected Git Repository `OpenCoven/psyche-research` and a Disconnect button. No setting was changed.

The deployment list exposed these six rows, all displayed as Error. This records the observed rows and does not claim an unfiltered or complete platform inventory.

| Deployment | Commit | Displayed target |
| --- | --- | --- |
| `H8sixebGei1qn8EdCKD8MgotLCpg` | `6121857` | Preview, Dependabot Django branch |
| `5kQThspH62hTSSZhJbENXzeyz8AL` | `14df694` | Production, main |
| `BjtiGcyEGpGjsz61Tkejmi5UdLCG` | `ee0543f` | Preview, Dependabot asgiref branch |
| `9dy4waT9uoBdTr9d9Tto72e2zFAZ` | `5abaf33` | Production, main |
| `6TXwAa9r8pEVy9D7vjLZTGTPLaC6` | `2abdebc` | Preview, form-error branch |
| `4x41N9e9HeSRQ4fVkrcCeMwdbkiU` | `d218b6b` | Production, main |

After approval, two attempts to select Dia and a fresh native inventory each timed out at thirty seconds and reset the CUA kernel. No Disconnect click or other project mutation occurred. The CUA part ended with that observed service failure. Read-only Vercel CLI project GET again exited 1 with `Error: fetch failed`. Therefore the live Git link cannot be treated as disconnected. A successful earlier dashboard read is not proof of the subsequent mutation.

The normal local account lookup still fails for UID 501, and Docker/Podman/Colima/Lima/initdb/pg_ctl remain absent. The prepared GitHub PostgreSQL CI route avoids requiring a local identity workaround. Native browser acceptance is potentially available once the native service stabilizes, but no new candidate rendering acceptance was executed during this access discovery.

## Exact next step

Use the existing approval to disconnect only the verified project's Git link once native control returns, then verify Git settings show no connected repository and retain existing deployment records. If the user performs that same approved step manually, inspect its actual resulting state before publishing. Then publish the prepared current source to a new branch/draft PR, require exact-head application CI and all ten live PostgreSQL tests without skips, and record the outcomes. No Git reconnect, merge, deployment or launch is authorized. Keep real intake paused and preserve all other worktrees.
