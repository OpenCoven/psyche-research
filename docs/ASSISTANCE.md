# Optional familiar assistance: human-run playbook

Status: proposed operating playbook, 2026-11-04, updated 2026-11-07. The current archive has no runtime LLM integration, model-provider dependency, familiar account type, external-content fetcher, or automated publication tool. Ordinary server-rendered forms and human moderation are the core workflow. This document does not authorize sending private submissions to a model, creating credentials, contacting contributors, or enabling an integration.

## What is available now

The [isolated offline workflow receipt](evidence/OFFLINE_WORKFLOW_20261106.md) records a complete synthetic local publication/correction/withdrawal and recovery drill with inherited provider settings removed, CPython socket/process events refused, and an injected instruction retained as escaped text. This qualifies the exercised local path without a model provider. WorkOS remains the selected hosted authentication path; actual AuthKit acceptance is still required. In hosted WorkOS mode, sign-in and session verification need WorkOS to be reachable, and when it is not the application answers with a retryable 503 instead of admitting anyone. That is an authentication dependency, not assistance; local mode runs the whole workflow offline. The audit assertion is a regression check for trusted tests, never permission to run submitted code.

Regression tests keep that boundary from drifting; the [assistance-boundary receipt](evidence/ASSISTANCE_BOUNDARIES_20261107.md) records what they check, the regressions they caught and their limits. Instructions placed in submitted fields, reports, appeals and withdrawal reasons stay escaped text on the workspace, moderation, operations and public pages the tests load, and loading those pages changes no account, permission, capacity or workflow record. The AI-assistance disclosure is required before submission and is labelled where moderators and readers see it. Every application response forbids script. Templates and runtime code are scanned for the known ways to switch off escaping. Runtime modules may import only a reviewed list of modules, network clients only in the WorkOS sign-in adapter, and none may start a process. Only the human moderation form reaches the one function that publishes a version. These are tripwires in the test suite, not a sandbox or a security certification.

Authors can prepare their note with ordinary tools and enter it into the archive themselves. They can describe assistance in the required AI-assistance disclosure field, including a clear statement of no assistance. A human operator can use this checklist to discuss preparation with an author without sharing the private draft with an external service. The application does not generate suggestions, store an assistance consent ledger, call an LLM, or automatically verify research claims.

Contributor accounts are provided by an operator and are not GitHub identities. The `moderators` group is the explicit application moderation permission; staff or superuser status alone is not a scientific qualification or a familiar grant. The implementation cannot establish that the person holding a password is human. Operators must therefore never give a familiar a contributor or moderator session, session cookie, account password, publication credential, database access, or authority to operate a human decision form.

The same holds for hosted sign-in through WorkOS. A WorkOS sign-in proves control of a WorkOS account, not that a human is acting, and only an operator-enabled binding of a WorkOS user ID to an existing local account grants entry. Never create, invite or bind a WorkOS user, organization membership or local identity binding for a familiar. Never give a familiar the WorkOS API key, client configuration or cookie password, a sealed session, hosting environment variables or deployment access, or membership of the `moderators` group. The WorkOS server key stays in its separately approved custody and is never a familiar or model-provider credential.

Useful bounded tasks include identifying missing metadata from a deliberately shared excerpt, helping an author separate observation from inference, suggesting clearer limitations, organizing citations, checking format against a public checklist, and preparing questions a human reviewer could choose to investigate. These outputs are suggestions. A familiar cannot certify rights, settle scientific disputes, publish, decide appeals, conduct independent human peer review, fabricate a vouch, or claim to have reproduced an experiment it did not actually run.

## Safe default workflow

1. The author starts with their existing evidence and removes secrets, private repository details, personal information, unpublished coauthor material, and content they lack permission to share. Saving and resuming an archive draft needs no assistant.
2. The human chooses one bounded task that can be completed from a short public or explicitly approved excerpt. Prefer a public template or a synthetic example when it can answer the question. Do not grant the familiar access to the private queue merely for convenience.
3. If any non-public content would leave the author's existing approved tools, stop before transmission and obtain the specific author and operator consent described below. General acceptance of archive terms or checking an AI-disclosure box is not that consent. If the provider, retention, or rights conditions cannot be established, continue manually.
4. A human prepares the minimal task packet and inspects the exact final text and attachments before using an approved tool. Do not automatically import a manuscript, repository, link target, logs, moderation history, or other submission as context.
5. The familiar returns a bounded suggestion with evidence references and uncertainty. A human checks every adopted factual statement, citation, number, and attribution against actual evidence. Unknowns remain unknowns; a fluent answer does not fill an evidence gap.
6. The author edits and submits through their own session. A separate authorized human moderator evaluates the frozen submitted version and records the actual moderation reason. Neither the assistance output nor its apparent confidence authorizes publication.
7. The human records the assistance provenance and any relevant disclosure, removes temporary copies according to the adopted retention agreement, and records unresolved limitations. If consent is withdrawn, stop further processing and follow the deletion procedure; do not imply that already published external copies can be recalled.

## Consent gate for any future non-public assistance

The current application does not implement this gate as a feature. Before a future pilot uses an external assistant for private material, an accountable human must define and record the exact task, author and coauthor permissions, fields or excerpts being shared, excluded fields, recipient/provider and model, processing location where known, provider retention and training conditions, intended output audience, expiration, deletion route, and whether any subprocessors or tools receive data. Obtain explicit consent to that concrete packet and intended use. A human with access is not automatically entitled to send the content to another processor.

Offer an equally usable manual path with no eligibility, queue, publication, or visibility penalty. Consent must be optional and revocable for future processing; do not bundle it into publication or an account request. Explain practical limits on deleting already generated or externally retained content before asking. Do not promise a provider's deletion behavior without verified terms and an actual deletion path. No such processing arrangement has been approved by this repository document.

The human operator keeps the consent record in an approved restricted location separate from public issues and repository content. Use an opaque assistance task identifier, not a public title containing private information. If a consent record itself contains a sensitive excerpt, minimize it to a field list and digest where feasible. Do not claim the existing `Event` model automatically stores this off-platform record; it currently records application workflow events only.

## Task packet contract

| Field | Required content | Boundary |
| --- | --- | --- |
| Task ID and owner | Opaque identifier and accountable human. | No account password, session, token, or private contact details. |
| Purpose and allowed output | One concrete task, such as identifying missing limitations. | No accept/reject verdict, appeal decision, independent-review label, or publish action. |
| Input version | Exact excerpt or structured fields and a digest/date. | No live private document link that grants ongoing access. |
| Data classification and consent | Public, synthetic, or specifically approved private excerpt; consent reference and expiration when needed. | Never infer consent from public GitHub activity or archive participation. |
| Evidence | Only the evidence needed for the task, with human-checked citations where relevant. | No automatic downloads, repository execution, credentials, entire logs, or unrelated submissions. |
| Tools and egress | No tools or network by default; any necessary read access separately allowed and narrowly scoped. | No unrestricted browsing, arbitrary shell execution, external mail, database mutation, or production environment. |
| Output format | Suggestions, evidence references, unknowns, and checks still needed. | Do not present generated text as a completed human investigation. |
| Stop conditions | Private data, injected instructions, missing rights, scope expansion, unsupported claims, or exhausted task budget. | Stop and return to the human; do not improvise privileges or data sources. |

Submitted content is untrusted data even when written as commands. A sentence asking the familiar to ignore boundaries, fetch a URL, reveal another submission, change a decision, or contact someone is part of the material under examination. It cannot alter the task's authorization. Keep task instructions outside the quoted excerpt and explicitly label the excerpt as data. The human should discard an output that reflects a scope or data-boundary violation.

## Output and provenance record

A useful output distinguishes supplied facts, facts the human still needs to verify, suggestions, and unresolved questions. Citations must identify evidence actually provided or checked through an explicitly allowed route; never invent references or imply a linked repository was inspected when only its URL was present. Formatting assistance should preserve the author's meaning and uncertainty.

For material assistance, record the tool/provider and model identifier when available, date, exact input version or digest, task scope, permitted data, consent reference if applicable, output digest or restricted location, human verifier, adopted changes, rejected claims, and known limitations. Record whether any code or artifact was actually inspected or executed, by whom, where, and with what authorization; routine archive intake never executes submitted code. Avoid retaining full private prompts merely for an impressive-looking audit trail.

The public AI-assistance disclosure should describe what assistance was used and how the authors checked it, without disclosing private task packets or coauthor information. For example: "Assistance was used to reorganize the methods section; the author checked the rewritten sequence against the recorded procedure. No experiment was run by the assistant." This is a sample disclosure, not a statement about a real contributor or a completed platform review.

## Human moderation and appeal checklist

Moderators can use a public checklist to inspect scope, metadata, declarations, privacy, safety, and abuse. They should not feed a private queue into a model to decide what to read first. Familiar outputs, social metrics, and model confidence cannot alter queue priority or substitute for the recorded human reason.

A moderator must inspect the actual frozen version and its digest, check for self-approval and other conflicts, and make the decision through their own authorized session. A familiar may help draft a generic explanation template without access to the case, but the human must write or explicitly adopt the actual reason and take responsibility for it. An appeal requires human reconsideration; an unavailable unconflicted person is a capacity limitation, not an invitation to invent an independent familiar panel.

## Data handling and stop procedure

On an accidental sensitive transmission or unexpected tool action, stop the task and further egress. Do not copy the material into public issues, chat summaries, or a second model to ask for incident advice. Tell the authorized operator through the approved private route, record only necessary facts, revoke task access where it exists, and follow the founder incident runbook. External notifications and credential changes remain human-authorized actions.

At task completion or consent withdrawal, stop further use, remove temporary working copies and any task grants under the adopted retention rule, and request provider deletion only through the approved actual route. Record what was deleted, what remains under a justified retention duty, what may persist in backups or provider systems, and when expiry is expected. Do not represent a local file deletion as proof of remote erasure.

## Turning assistance off

Assistance has no runtime switch because nothing in the application depends on it. The founder turns it off by suspending this playbook: stop issuing task packets, stop tasks in progress under the stop procedure above, and remove temporary copies under the adopted retention rule. The archive keeps working with no code, configuration, migration or deployment change. The [offline workflow drill](evidence/OFFLINE_WORKFLOW_20261106.md) exercised drafts, submission, publication, a correction, withdrawal, a decline, a report, an appeal, refusal of an anonymous private export and SQLite recovery through service calls with local authentication and no model provider; resolving appeals and reports is covered by the ordinary test suite. Saying on the policies page that assistance is suspended is a template change and deployment like any other copy edit, and nothing in the archive depends on it.

Human decisions stay attributable: each moderation decision is an append-only record naming the moderator account that made it. The playbook forbids letting assistance operate a moderator session, but the record shows which account decided, not whether a human was at the keyboard. Disclosures already submitted remain part of their frozen versions, and changing one requires a new human-moderated version. A future runtime integration must ship with a configuration stop switch that is off by default, and its tests must show the complete workflow still passes with the switch off.

## Conditions before adding a runtime integration

A separate reviewable implementation issue must establish a useful need, owner, explicit data contract, optional consent and manual path, provider and transfer assessment, redaction tests, task-version binding, finite quotas/deadlines/retries, input/output handling, restricted tools and egress, minimal credentials, audit and deletion behavior, and a stop switch. Never expose publish, role-management, appeal-resolution, or unrelated-private-read tools to the integration.

Verification must demonstrate that malicious submission instructions cannot cross those boundaries, an unavailable assistant cannot block the archive path, consent refusal causes no disadvantage, outputs cannot become independent human reviews, and the human publishes only the exact version they inspect. Independent agent code review is useful technical evidence; it is not scientific peer review or a security certification. No runtime integration is approved or available until that separate work is completed and accepted.
