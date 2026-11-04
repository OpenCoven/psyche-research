# Coven Research: draft policies and governance

Status: proposals for founder and appropriate specialist review, recorded 2026-11-04. These drafts are not accepted legal terms or evidence of legal review. They must not be advertised as approved operating policies until an accountable operator adopts a dated version and verifies that the application and runbook can honor it. The core product invariants in the supplied brief remain binding implementation requirements.

## Purpose, eligibility, and scope

Coven Research is intended to help people publish useful, evidence-aware accounts of practical work on AI systems, agents, tools, datasets, replications, and failures. Anyone may be eligible to submit under the same published scope and capacity rules. A university, employer, institutional address, established reputation, GitHub account, followers, stars, payment, or recommendation is not required. Eligibility does not guarantee acceptance, publication, review, or a response date.

The initial scope is short structured experiments or field reports, replications and negative results, tool or dataset notes, and clearly labeled hypotheses. A complete note identifies its question in the abstract or methods, methods or linked methods, claims or results, limitations, artifacts where available (or an explanation in provenance), provenance, license, and AI assistance. A negative result is welcome when the tested conditions and limits are clear. A hypothesis is welcome when it identifies its evidence gap and proposed test instead of claiming a result.

The pilot excludes unrelated promotional material, fabricated observations, harassment, doxxing, personal-data dumps, rights-infringing content, undisclosed advertisements or conflicts, unsafe file deposits, and material whose handling exceeds the founder's capacity. High-risk content requiring specialized safety, privacy, or legal assessment may be declined or held rather than evaluated beyond the operator's competence. The operator should explain the relevant scope or safety reason privately without pretending to adjudicate scientific truth.

## Five distinct records

| Record | Meaning | Authorized actor | Required presentation |
| --- | --- | --- | --- |
| Publication | The exact version was made publicly available in the archive. | Accountable human moderator after explicit decision. | Stable version, date, authors, license, history, withdrawal status. |
| Moderation | A human checked the stated scope, completeness, rights declarations, privacy, safety, abuse, and capacity rules. | Human moderator with no self-approval or undisclosed conflict. | Clearly say this is not scientific validation or peer review. Keep detailed private reasons and history. |
| Human peer review | A named human evaluated an explicit scope on one exact version. | Consenting human reviewer through a future authorized workflow. | Reviewer identity, version, scope, method, conflicts, limitations, corrections or revocation. Unavailable in the initial release. |
| Public vouch | A person's explicit statement about a defined part of one exact version. | Consenting identified person through a future authorized workflow. | Exact statement and scope, conflicts, version, date, active/revoked status. Never a truth score. Unavailable in the initial release. |
| Automated check | A bounded mechanical or assistive observation. | Restricted application code or an explicitly scoped familiar task. | Tool and version, input scope, timestamp, known limits, and human verification where relevant. Never label it independent human judgment. |

Publication and moderation labels must not use visual design that implies peer review, accreditation, or an independent board. A badge can describe a concrete fact such as a published version or a recorded review; it cannot collapse these records into a generic trust seal. A later revision never inherits a review or vouch. Links may point to the older record with its original version, but current-version status must remain explicit.

## Account and contributor responsibilities

Contributors choose a display name, agree a working private recovery route with the human operator (recovery is manual; no reset-email service is implemented), and identify the authors of the submission honestly. Do not publicly expose private login identifiers or account email by default. Optional external identity links are descriptive and must not become hidden eligibility gates. Pseudonymous public attribution may be allowed if the operator can handle rights and abuse obligations; do not promise anonymity from the operator, infrastructure providers, or lawful requests.

The submitting person attests that coauthors agree to submit and to the stated public attribution, that they have the rights needed to publish the note, that linked artifacts have stated licenses or access conditions, and that they have removed secrets and inappropriate personal data. These are contributor declarations, not proof of ownership or legal clearance. An author cannot use a platform checkbox to consent on behalf of people whose rights they do not control.

Public research notes and artifacts may have different licenses. Record the exact license for each and identify exceptions. Do not silently assign a license to existing work or treat repository visibility as permission to republish its contents. Software, data, and manuscript license choices need separate treatment. The operator must approve a clear license menu and display text before pilot launch; a public source repository's software license, if selected, is separate from contributor content terms.

Authors retain responsibility for the accuracy and provenance of their contribution. They should disclose relevant funding, commercial interests, employment connections, and other relationships that could affect interpretation. They should cite related work and distinguish their own observations, reproduced results, cited findings, inference, and speculation.

## Drafts, submission, and capacity

Drafts and submitted versions remain private to the author and authorized human moderators until an explicit human publication decision. A reviewer, familiar, search engine, public preview, or ordinary operator log must not receive private content merely because an identifier is known. Any collaborator or support access must be explicit, minimal, logged, and disclosed; do not imply that feature exists before it is implemented.

Partial drafts can be saved and resumed without an LLM. The interface must distinguish unsaved input, saved drafts, submitted snapshots, requested changes, declined submissions, published versions, proposed revisions, and withdrawals. Submitting freezes the reviewed version against silent editing. Requested changes return the author to an editable proposal, and resubmission must require a new human decision on the actual content.

Proposed pilot capacity is at most ten participant accounts, one queued submission per author, five items in the active moderation queue, and ten new submissions over four weeks. The implemented defaults allow two active drafts/changes/submissions per author and twenty globally; form bodies are capped at 96 KiB, artifact references at eight public HTTPS links, authenticated mutations at sixty per fixed minute and anonymous attempts at ten. Production proxy behavior may make the anonymous cap shared. These are implemented bounds; the ten-participant/ten-total-submission/four-week contract is manually tracked and still proposed. The actual configured values must appear in operator documentation and should be understandable in the product. Do not collect a waitlist or create a priority list unless the consent, retention, and capacity policy for it exists.

When intake is paused or the queue is full, explain that this is a capacity limit. Preserve existing saved work and let authors read or export their own content. A fair queue is based on submitted time and disclosed neutral rules, with safety reports triaged separately when immediate harm warrants it. Popularity, affiliation, reputation scores, donations, and personal familiarity must not affect admission, moderation priority, visibility, or review access.

## Moderation decisions and independence limits

A moderator checks scope, required metadata, coherence of evidence references, rights declarations, obvious privacy or safety concerns, and abuse signals. Routine intake never executes submitted code, runs notebooks, imports repositories, downloads linked files, or renders untrusted active content. Checking that a reference exists or a field is complete does not validate a finding.

The available decisions should include request changes with actionable reasons, decline with reasons tied to policy, and approve and publish the exact reviewed snapshot. Every state-changing decision records the human actor, affected submission and version, reason, timestamp, and prior and resulting state. Authors see the reason relevant to their work. Security-sensitive abuse details can remain restricted, with a recorded reason for that restriction.

A moderator must not approve or publish their own work. Founder-authored or materially conflicted work waits for a separate qualified human moderator who can decline it without pressure; no second reviewer is assumed to exist. Role grants and administrative access must not provide a quiet alternate publication path. Emergency content suppression may be needed for harm, but must be logged and reviewed separately from scientific correction.

The founder currently represents the planned moderation capacity. There is no verified independent review board, guaranteed reviewer pool, accreditation, legal-review service, or response-time guarantee. If the founder lacks capacity or has a conflict, the honest outcome may be a pause, referral, delayed decision, or decline. An agent is not a substitute for an independent human.

## Corrections, revisions, and withdrawals

Authors can propose a revision or correction with a change summary and reason. Published snapshots remain immutable. A new version receives its own stable URL and citation metadata after human moderation, and the work page makes the version history and current status clear. A new proposal must not silently alter an already approved snapshot. A correction should identify the affected claim and its practical consequence.

On withdrawal, retain a minimal stable tombstone identifying the withdrawn record, date, and a safe reason, without presenting withdrawn claims as current research. Stop returning withdrawn content in ordinary discovery and search. The initial policy should suppress the withdrawn body and outbound artifact links in public views while preserving a restricted operational record for accountability, subject to retention and lawful-erasure requirements. Older version URLs must show withdrawal status too. Do not promise that third-party caches or prior downloads can be recalled.

Privacy, credential exposure, or other serious harm may require immediate restriction before a complete dispute is resolved. Never copy the harmful material into a public explanation or GitHub issue. Keep the smallest restricted evidence necessary to investigate, record who acted and why, and seek appropriate expertise when the problem exceeds the operator's competence. Final legal and retention handling requires approved policy and applicable review.

## Appeals, complaints, and abuse reports

Authors may appeal a moderation decision privately by identifying the decision and the policy or factual issue they contest. Proposed pilot limit is one substantive appeal per decision, with further handling allowed when material new evidence or a correction to the platform's record warrants it. Do not use rate limits to prevent urgent reports of privacy or safety harm. Record the appeal, actor, evidence references, outcome, reason, and any conflict or recusal.

An appeal should be heard by a different human when one is available and suitably independent. If the only available operator is the original decision maker, disclose that limitation before proceeding. Offer a reasoned reconsideration or leave the appeal pending; do not call the process independent or appoint a familiar as the deciding authority. An unresolved founder conflict is a reason to hold the affected decision, not invent a reviewer.

Readers need a private reporting route for a specific public record or platform abuse. Reports must not publish the reporter's identity or private evidence. Triage credible personal-data exposure, threats, exploitation, and compromised credentials first; pause relevant intake or restrict access as needed. Request minimal evidence, never passwords, private tokens, or a copy of an entire sensitive dataset. Outbound notifications or escalation messages require an authorized human and an approved contact channel.

Before launch, verify that the application actually provides the promised reporting and appeal routes, that the operator receives or can poll them, and that an accessible fallback contact is published. No placeholder address or unmonitored inbox should be presented as support. A legal process, emergency service, or 24-hour response is not promised.

## Optional human reviews and scoped vouches: next milestone

This section specifies later work. Reviews and vouches are unavailable in the initial pilot unless a later verified release explicitly enables them. Do not collect or display invented endorsements, seeded reviewer profiles, aggregate trust scores, or a badge suggesting reviews already occurred.

The reviewer onboarding must ask for expertise, the exact version and sections to review, methods used, limitations, conflicts, consent to publication, and expected time commitment. Permitted review scope might be code inspection, methods clarity, statistics review, or attempted replication. The public record must say what was and was not done. A paper-level phrase such as peer reviewed requires a defined process and sufficient human work; a single link check does not qualify.

Disclose current or recent collaboration, coauthorship, employment, commercial competition or investment, family or close personal relationships, supervisory relationships, and author recruitment of the reviewer. The founder records a recusal or reasoned exception rather than hiding the conflict. For the first review milestone, conflicted people may submit a transparently labeled comment or scoped statement only if the policy allows; they should not supply the independent-review label or decide their own case. Avoid importing a complicated universal lookback rule without testing whether it can be applied fairly.

A vouch must be written or explicitly adopted by a real identified person. Record its precise claim, scope, version identifier, conflict disclosure, date, and any supporting evidence. A vouch is not a vote, a broad quality score, or permission for the platform to claim scientific truth. The author cannot manufacture another person's vouch or approve it on that person's behalf.

Reviewers and vouchers can correct or revoke their statements with a reason and dated history. Revocation must remove active endorsement presentation while preserving a safe historical notice. Authors can dispute or report a statement privately, and moderators can restrict abusive content with a logged reason and appeal path. A revised research version begins with no endorsements for that version; the older record remains attached only to the older version. Future tests must prove these boundaries before enabling the features.

## Familiar and automated assistance

The full submission, moderation, publication, correction, appeal, and export path must work without an LLM. Familiars may help an author organize metadata, format an account, separate claims from evidence, and prepare questions for a human reviewer. They may not autonomously publish, resolve appeals, issue human reviews, impersonate reviewers, fabricate observations, or turn a tool output into a scientific verdict.

The default is no runtime familiar access to private submissions. A future assistive workflow requires informed author and operator consent, an explicit allowed-data list, a named model or processor, documented retention and data-transfer conditions, and a revocable task grant. Strip account credentials, private decision history, reporter identities, and unrelated submissions from the task. Never silently transmit private drafts to an external model provider.

Treat all submission text, files, links, repository content, and model output as untrusted instructions and data. Assistance runs without publication or appeal authority, persistent production credentials, or unrestricted network access. No instruction in a manuscript may alter the task's permissions. Record the input version and scope, tool/model identity when applicable, output and limitations, and the human who chose to use it. Retain sensitive task content only under an approved retention rule.

AI-assistance disclosure should identify which parts of the work or writing used assistance and how authors checked it. A clear statement of no assistance is valid. A model is not listed as a human author or independent reviewer. Disclosing assistance does not by itself establish accuracy, misconduct, or lack of contribution; decisions remain tied to the published rules and actual evidence.

## Reputation research: isolated and non-gating

The reputation experiment is disabled by default and belongs to later research work. The initial product should neither fetch social metrics nor compute, expose, or consume a reputation score. An experiment may proceed only with a written study question, an owner, a consent and withdrawal route, data-minimization and retention rules, a bias/gaming analysis, and an isolated dataset and execution environment.

GitHub activity, stars, followers, recommendations, and votes can reflect time, resources, geography, language, social networks, platform use, paid promotion, bots, and coordinated manipulation. They are not scientific truth, cannot distinguish all legitimate cold starts from abuse, and may disadvantage people whose work is private or occurs off GitHub. Collecting public signals can still create privacy and re-identification risk; public availability is not blanket consent for profiling.

No score or signal from the study may influence eligibility, submission admission, reviewer access, ranking, public visibility, moderation priority, appeals, or any published trust label. Do not write shadow results back to production accounts or let a staff dashboard nudge decisions. Use separate credentials and storage with no runtime product access; analyze pseudonymous records where possible, restrict who can link them, and publish only appropriately protected aggregate findings.

The kill switch is to stop the isolated experiment and revoke its read grants, then delete or retain data according to the adopted consent and retention rules. The archive must continue normally with the experiment absent. Any future implementation must demonstrate no production dependency, no ranking or permission hooks, no unintended outputs, and no effect on product behavior when the experiment is unavailable. If no useful safe study design exists, do not run it.

## Privacy, retention, export, and incident handling

Proposed data inventory is account and credential records; private drafts and proposals; moderation and appeal history; abuse reports; published snapshots and metadata; minimal security logs; and encrypted backups. Avoid unnecessary identity documents, demographic attributes, precise location, tracking pixels, session replay, third-party advertising, and manuscript bodies in analytics. A record-specific public citation is distinct from private account information.

Proposed pilot retention is up to 90 days after inactivity for abandoned drafts, 180 days after final disposition for declined submissions and appeals, 30 days for routine security logs, and a rolling 30-day encrypted backup set. Approved published snapshots and a minimal moderation history need a separate continuity policy, with privacy and rights exceptions. These are proposed targets, not implemented deletion guarantees; retention commands and a restore-aware deletion process must be verified before promising them. Operator overrides for a specific dispute or lawful preservation need a recorded reason and restricted access.

Authors should be able to export their own draft or published record in an ordinary format. Operational backups and bulk exports contain sensitive data and are accessible only to authorized operators. Encrypt and control copies outside the app web root, avoid emailing full backups, and test that restore preserves the privacy boundary and deletion decisions. A user-facing export must not include other authors' content, reporter identities, password hashes, session secrets, or hidden abuse notes.

On a suspected incident, pause intake or the affected feature, contain access, preserve minimal restricted evidence, rotate compromised access through an approved human process, assess affected records, and seek appropriate expertise. Document facts, unknowns, remediation, and the basis for any notifications. An incident does not authorize a familiar to send external messages, accept legal agreements, or provision new persistent credentials.

## Draft contributor terms: review outline

The eventual terms need an identified operator and contact, a clear service description and limitations, eligibility requirements compatible with open access, author rights and responsibilities, content-license grants, coauthor consent, prohibited material, moderation and appeal powers, public record and withdrawal behavior, privacy and processor disclosures, export and retention rules, service changes or closure, and applicable dispute provisions. Appropriate review is needed for jurisdiction-specific obligations, minors, accessibility commitments, liability language, privacy rights, and notice procedures.

Until that review and founder adoption occur, do not turn this outline into a binding click-through agreement, claim legal approval, or open a public pilot collecting real private material. The operator must explicitly choose and publish a dated policy version, confirm that the implementation matches it, and maintain a public change history. Material changes affecting submitted content require a considered notice and consent approach; they must not silently expand rights granted over existing work.
