# Psyche Research

A bounded research publication for practical work with AI systems: experiments, replications, negative results, tools, datasets and evidence-supported ideas. Eligibility does not depend on affiliation, popularity, GitHub or payment. Publication follows human moderation for scope, completeness, rights, privacy, safety and abuse; it is not scientific peer review.

**Pilot preparation, not launched.** This repository implements the local archive path. Intake defaults paused. Policies are drafts; hosted operation, actual-browser accessibility, operator ownership and pilot acceptance remain gates. Human scientific reviews and vouches are unavailable; reputation research is disabled and unimplemented. No real research, users or endorsements are seeded.

## Start here

Read [project status](docs/STATUS.md), [decisions](docs/DECISIONS.md), [founder runbook](docs/RUNBOOK.md) and the [delivery epic](https://github.com/OpenCoven/psyche-research/issues/1). The current state and remaining gates are in those records, not implied by an attractive interface or a passing unit test.

## Local development

WorkOS login is selected by the user. See [WorkOS setup](docs/WORKOS.md) for the implemented AuthKit flow, verified staging project and login destinations, required server-side configuration and existing-account identity linking. Local development below retains `AUTH_PROVIDER=local` until the real staging server key and exact issuer are privately configured; real provider sign-in remains unverified.

Use Python 3.13. The dependency file pins hashes; normal installation requires package-registry network access. Runtime core workflows require no network service or model provider. The commands below create only an empty local database; they create no participant accounts and no research fixtures.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.txt
mkdir -m 700 -p var
LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py migrate --noinput
LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py runserver --insecure 127.0.0.1:8010
```

Open http://127.0.0.1:8010. The loopback development server uses the explicit local-only key and insecure local cookies; never expose LOCAL_DEVELOPMENT=1 to a network or use runserver for hosting. `--insecure` serves repository CSS while DEBUG remains false. Files and SQLite data stay in ignored var, outside static paths.

## Verify

```sh
LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py check --fail-level WARNING
LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py makemigrations --check --dry-run
LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py test --verbosity 2
LOCAL_DEVELOPMENT=1 .venv/bin/python manage.py collectstatic --noinput
```

Tests create clearly labeled synthetic fixtures only in isolated databases. They cover authorization and private-data boundaries, frozen snapshots, exact moderation decisions, self-approval prevention, append-only records, concurrent capacity/publication, safe retries, corrections/withdrawals, appeals, abuse/rates, rejected uploads, escaped content, production settings, safe logs, migrations and representative backup restoration. They do not prove deployed TLS, browser accessibility, scientific accuracy or legal acceptance. See [verification plan](docs/VERIFICATION_PLAN.md) and [release evidence](docs/RELEASE.md).

## Operating boundaries

This is one Django application with server-rendered text forms, explicit service transitions and framework sessions/CSRF. The user-selected Vercel target uses managed PostgreSQL for durable data; SQLite remains the local development backend. See the [Vercel packet](docs/VERCEL.md) for environment, preview-isolation, migration, provider recovery and deployment gates. Author artifacts remain bounded public HTTPS references; the application never fetches links, accepts files, executes research code, generates remote previews or invokes an LLM. Private drafts do not enter public pages, search or metadata exports. Publication snapshots, decisions and audit events are append-only through application and database triggers; a privileged host owner can still bypass them.

Contributor provisioning and moderator role commands are human operator procedures documented in the runbook. Do not use them to create real credentials without approval. There is no public signup, email delivery, password reset email or generic admin site. Manual recovery, moderator conflicts and limited founder availability require a real monitored operator before intake opens.

Vercel configuration at the root and alternative-host examples under deploy are reviewable candidates. No resource or project is provisioned; alternative-host domains/paths are deliberately invalid placeholders. They do not deploy anything. A real deployment needs a reviewed target, TLS/proxy configuration, private persistent storage, backed-up secret handling, encrypted off-host backups, cost/availability acceptance, policy adoption and explicit authorization. Never point a web server at the repository root or var.
