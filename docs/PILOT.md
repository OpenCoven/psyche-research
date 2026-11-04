# Coven Research: bounded pilot and onboarding drafts

Status: proposed pilot plan and copy, recorded 2026-11-04. Current decision is **NO-GO for invitations, real submissions, deployment, and public launch** until the gates below are evidenced and an accountable founder explicitly authorizes the concrete pilot. Drafting this plan does not send invitations, create participants, approve policies, provision hosting, or claim the service is live.

## Proposed pilot contract

Run a four-week pilot with at most ten consenting participants, ten submitted notes in total, one queued note per person, and five items in the active moderation queue. Admit people by the disclosed subject and capacity rules, without an affiliation, social-following, payment, or reputation requirement. Invite a mix of independent builders, maintainers, replication authors, and academically affiliated practitioners only when outreach is explicitly authorized. A deliberately small sample tests usability and workload; it does not establish broad demand or representative fairness.

The proposed founder schedule is two 45-minute moderation sessions per week, one 30-minute weekly operations and metrics check, and a separately recorded reserve for reports or incidents. There is no guaranteed response time or emergency coverage. If this schedule cannot be accepted in practice, lower the intake cap before opening it. A report queue must have a known monitored route; do not promise that a weekly check is adequate for emergencies.

The first pilot exercises research-note publication only. Human peer reviews and vouches remain a next-milestone feature with no implied reviewer availability. Anyone offering scientific feedback during the pilot should understand that ordinary feedback is not a platform-certified peer review or a blanket endorsement. Do not display manufactured reviews, collaborators, research records, or popularity data to make a small archive look established.

## Go/no-go evidence

| Gate | Required evidence | Decision owner |
| --- | --- | --- |
| Accountable operations | Named founder, working monitored contact, real weekly availability, accepted participant and queue limits, hosting region and cost cap. | Founder. |
| Policy adoption | Dated scope, moderation, correction, withdrawal, appeals, retention, privacy and content-license choices reviewed and accepted; no unapproved legal claims. | Founder with appropriate specialist input where needed. |
| Product path | A saved partial draft can be resumed; full submission reaches a private human queue; changes can be requested; an exact accepted version publishes; corrections and withdrawal work. | Implementation owner plus independent technical reviewer. |
| Authorization and privacy | Negative tests cover anonymous and cross-account access, moderators, self-approval, raw identifiers, search, exports, logs, and state transitions; no unresolved critical findings. | Independent technical reviewer; not a scientific peer review or security certification. |
| Capacity and abuse | Actual configured caps, rates, pause behavior, report and appeal handling demonstrated; no role escalation or hidden priority score. | Implementation owner and founder. |
| Safe input | Untrusted text stays escaped; uploads are rejected if unsupported; no automatic fetches, previews, repository execution, or runtime agent access to private intake. | Implementation owner plus independent technical reviewer. |
| Accessible experience | Keyboard path, focus and errors, zoom/reflow, meaningful labels, contrast, responsive pages, and a screen-reader pass on the actual rendered client; limitations recorded and resolved or accepted with a justified pilot accommodation. | Founder and usability reviewer. |
| Recovery | Consistent backup restored into a fresh environment; private/public boundaries, version history, moderation record, and export verified; operator can follow the runbook. | Operator. |
| Deployment | Explicit approval of target, audience, version, credentials, and cost; hardened production configuration and migration/rollback plan; hosted smoke evidence on the actual version. | Founder. |
| Invitation and consent | Explicit authorization to contact the selected recipients, accurate final copy, clear pilot status, approved contact and participant privacy terms. | Founder. |

An incomplete gate is NO-GO for the affected activity. A locally passing test suite is evidence about tested behavior; it does not establish hosting, real email delivery, legal readiness, production recovery, or human accessibility acceptance. Keep planned, implemented, tested, independently reviewed, deployed, and human-accepted states separate in the project status.

## Pause and stop criteria

Pause new intake immediately for a credible private-data exposure, unexplained authorization bypass, unsafe public content that cannot be promptly contained, missing or untested backups, unknown operator access, an unmonitored reporting route, or founder unavailability without cover. Preserve existing authors' read and export access when safe. Emergency restriction of compromised access can take precedence over convenience, with a recorded reason and recovery plan.

Pause intake if the active queue reaches five items, the oldest queued item exceeds 14 days, total weekly founder effort exceeds three hours for two weeks, or unresolved appeal/report handling exceeds available competence or time. These are proposed thresholds, not response guarantees. Do not erase queue items to make metrics look healthy; lower capacity, explain delays, or wind down transparently.

End the pilot early if the core archive path cannot be made private and safe, participants do not understand publication versus review after explanation, or the founder cannot sustain even the reduced operating schedule. A smaller useful archive or an export-and-close outcome can be successful learning. Do not continue collecting sensitive work merely to reach a volume target.

## Measurement and feedback

Collect the smallest aggregate measures useful for a decision. Avoid third-party tracking, manuscript-body analytics, social-score collection, demographic profiling without a justified approved study, or tracking people across services. The founder can maintain an access-controlled pilot worksheet with consented participant feedback and publish only a safe aggregate summary.

| Measure | How to record it | Proposed useful signal |
| --- | --- | --- |
| Time to first saved draft and complete submission | Consented timed usability sessions or voluntary estimates, including assistance time and interruptions. | Most participants can save a draft unaided and understand what remains; median completion time for a prepared note is at most 30 minutes. |
| Abandonment and submission friction | Ask what prevented completion; count draft resumptions and unresolved form errors without copying private text. | No repeated preventable loss of work; fields have a clear purpose. |
| Queue age | Submitted and decision timestamps; report median and oldest item, including pauses. | Queue remains within founder capacity; 14-day pause threshold is respected. |
| Founder effort | Minutes spent on moderation, author help, reports, appeals, operations, and interruptions. | Median handling stays near or below 30 minutes per note, with a sustainable weekly total. |
| Usefulness and return behavior | Ask for a concrete reuse, citation, attempted replication, design decision, or voluntary return; record a count with consent. | At least three participants can identify a concrete use beyond publishing their own page; this is exploratory, not a market proof. |
| Reviewer interest | Count consenting expressions of interest and actual volunteered scope/time, separately from reviews completed. | Enough real commitment to justify a later review milestone; no review pool claimed from a sign-up count. |
| Corrections | Count proposed and completed corrections, time to visible status, and whether a reader found the history clear. | Corrections are usable and discoverable; a high or low count alone is not a quality score. |
| Accessibility barriers | Participant-reported issues and actual keyboard, zoom, reflow, and assistive-technology findings. | No unresolved barrier preventing the core task; documented accommodations where appropriate. |
| Abuse and safety burden | Restricted report counts, broad category, handling time, escalation, and unresolved state. | Safe triage within capacity; never optimize away reports or publish sensitive evidence. |
| Cost and recovery | Actual hosting/backups/communications invoices or logs, plus restoration time and result. | Costs within the founder-approved cap and recovery possible by the operator. |

Ask contributors: Which existing document did you start from? Which fields helped or duplicated work? Did any claim become clearer or more limited? Could you tell whether a save succeeded? Could you resume after interruption? Did you know what would become public? Did the eligibility and capacity rules feel understandable? What would make you return or choose an existing archive instead?

Ask readers: Can you identify the exact version, claim, methods, limitations, license, and artifacts? What does the moderation label mean? Was anything mistaken for peer review? Could you find a correction or withdrawal? Did this page change a real decision or help reproduce a result? What accessibility or comprehension barrier did you encounter?

Ask the founder: Which decision required expertise you did not have? How much effort was invisible in the queue count? Were capacity rules actually fair? Did private data appear where it should not? Which task could be simplified without replacing human judgment? Would a smaller scope, existing community, or orderly close serve people better?

## Four-week operating sequence

Week 0 is preparation only: complete go/no-go evidence; rehearse with clearly marked local synthetic fixtures; restore backups; verify public empty states; inspect final copy; approve policies, deployment and specific outreach separately. No fake research or endorsements should appear in a public archive or preview.

Week 1 starts only after authorization: onboard two or three participants, observe draft save/resume and private submission, handle the first item manually, and confirm authors understand the publication boundary. Keep intake paused between cohorts if a product guarantee is uncertain.

Week 2 expands only within caps: invite the remaining approved participants in small batches, record total author and founder effort, and test a correction or withdrawal only with the author's informed consent. A synthetic rehearsal is preferable when a real public change would create confusion.

Week 3 concentrates on reader value, accessible use, unresolved reports, and whether the founder schedule holds. Gather reviewer interest without claiming a review service. Address the highest-impact friction before adding features.

Week 4 stops new pilot intake, resolves or clearly hands off pending submissions and appeals, offers authors export, records safe aggregate findings, and makes a written continue/reduce/pause/close decision. Do not silently convert a time-bounded pilot into an indefinite service.

## Contributor onboarding draft

Welcome to Coven Research, a proposed small archive for practical research on AI systems and agents. You can contribute without an institutional affiliation, a popular repository, or a payment. We are testing whether clear accounts of experiments, replications, negative results, tools, datasets, and carefully labeled ideas help other people do better work.

Start with a concrete question and the work you already have. Save a draft with a working title and summary, then add who did the work, how it was done, what happened or what you claim, what remains uncertain, and where the relevant artifacts and exact versions can be found. Cite related work, record provenance and licenses, and disclose how AI assistance was used and checked. A linked method is fine when the note still explains what a reader needs to understand the claim.

Remove tokens, private repositories, personal data, confidential logs, and material you do not have permission to publish. Do not upload or ask the archive to run code. Use a durable artifact host when appropriate, include a commit, release, dataset version, or DOI, and make access conditions clear. A public repository is not automatically licensed for copying.

Your saved draft stays private to you and authorized human moderators until publication. Submission is a request for a scope, completeness, rights, privacy, safety, and abuse check. The moderator may ask for changes, decline with reasons, or publish the exact reviewed version. That is not scientific peer review or a promise that your findings are correct. Capacity is limited, and no response time is guaranteed.

Before agreeing to publish, check the exact public attribution, content, license, and artifact links. After publication, use a new version or correction rather than silently changing the research record. You can request withdrawal or appeal a decision through the real routes listed in the deployed service. If you plan to submit to another venue, check that venue's rules first. The pilot contact and policy links must be filled with approved, monitored destinations before this copy is used.

## Reviewer onboarding draft for the next milestone

Human review is not available in the initial pilot. This guidance is preparation for a later workflow and is not a request to review or a claim that reviewers have been recruited.

Choose a bounded scope you can competently assess on one exact version. State what you examined, how you examined it, what you did not test, your relevant expertise, conflicts, and uncertainty. A code read, a reproduced experiment, a methods critique, and a statistical analysis are different contributions. Do not imply you performed a task you only asked an agent to describe.

Tell the moderator about collaboration, employment, financial, supervisory, family, personal, or other relevant relationships. Decline if you cannot make the required independent judgment or lack time. You can disclose a qualified perspective without calling it an independent review. Do not access private content outside your explicit task or copy it into an external model service without permission.

Be specific, constructive, and evidence-limited. Distinguish a blocking concern from a suggestion, and explain how an author could address it. Do not execute untrusted software on your ordinary machine as part of routine archive intake; any later reproduction work requires its own safe plan. AI tools may assist organization only under the disclosed workflow; your actual judgment and verification remain your responsibility.

Before publication, explicitly consent to the precise review text, public identity, version, scope, and conflicts. Correct or revoke a statement when evidence changes. A revision does not inherit your review; you must assess and explicitly adopt a new statement for the new version. Credit is for the work you actually performed, without a promise of academic recognition or platform status.

## FAQ draft

**Who may submit?** Anyone whose work fits the stated scope and the same capacity rules. Affiliation, employer, GitHub popularity, followers, reputation, and payment are not prerequisites.

**Is every complete submission published?** No. A human can request changes, decline material outside scope or handling capacity, restrict harmful content, or pause intake. Reasons and a private appeal route should be available.

**Does publication mean peer review or scientific validation?** No. Publication records availability. Moderation checks the disclosed operational criteria. Human peer review and scoped vouches are separate later workflows and unavailable in the initial pilot.

**Are negative results or replications welcome?** Yes, when the conditions, evidence, limitations, and relationship to earlier work are clear. Novelty and favorable results are not prerequisites.

**Do I need a formal paper or GitHub account?** The proposed format is a short structured note with artifact links where relevant. A conventional paper and external identity links are optional. The actual account route must be verified in the deployed product.

**Can I use AI assistance?** Yes, with an honest description of where it was used and how you checked the work. An AI tool cannot act as an independent human reviewer, author, moderator, or appeal decision maker. The archive path does not require an LLM.

**Will Coven store or run my software and datasets?** The first release links to artifacts and records their versions. It does not accept arbitrary file deposits, run submitted code, or guarantee third-party preservation. Use a suitable durable repository where appropriate.

**Will my draft be public?** It must remain private until an explicit human publication decision. Private intake is distinct from a published external archive record; do not link confidential material merely because a form field accepts a URL.

**Can I correct or withdraw work?** The intended workflow is a new moderated version or a withdrawal tombstone with clear history. Public copies already downloaded or cached elsewhere may remain. Exact privacy and retention behavior must be approved and implemented before launch.

**Do you mint DOIs or guarantee indexing?** No such capability or arrangement is verified. Stable version URLs and citation metadata are the first-release goal. You may link an existing DOI from a suitable artifact host without suggesting it certifies Coven's moderation.

**Is a reputation score used?** No. Any future reputation study must be optional, isolated, disabled by default, and unable to affect admission, review access, ranking, visibility, priority, or moderation. It cannot measure scientific truth.

**Why might an academic participate?** A clear versioned account of a replication, tool, or practical result may support reuse and citation alongside existing venues. Check your own venue, anonymity, rights, and institutional rules; academic recognition or acceptance elsewhere is not promised.

**Who operates this?** The proposed operating model is one founder with limited familiar assistance. No independent board, guaranteed reviewer pool, accreditation, legal-review service, or response-time guarantee is claimed. The actual accountable operator and monitored contact must be published before pilot opening.

## Landing-page copy draft

**Practical AI work, recorded clearly.**

Coven Research is being built as a small archive for useful accounts of AI experiments, replications, tools, datasets, negative results, and evidence-aware ideas. Start with the work you did, show the evidence you have, and say where it stops.

You do not need an institution, a popular repository, a following, or a payment to be eligible. Intake is bounded and human moderated for scope, completeness, rights, privacy, safety, and abuse. Publication is not scientific peer review or a guarantee that a claim is correct.

The goal is a readable, versioned research record that connects practical work to methods, artifacts, limitations, and corrections. Human reviews and vouches are separate future features. There is no reputation-based admission or ranking.

**Pilot preparation.** Real submissions and invitations will begin only after the founder approves the pilot and its operating gates. Until then, the archive should show an honest empty state and accurate implementation status. Replace this status with the actual verified release state when authorized; do not imply that this draft has already launched.

## Invitation draft: do not send without authorization

Subject: Invitation to a small Coven Research pilot

I am preparing a small pilot for Coven Research, a versioned archive for practical work on AI systems and agents. I would value your help testing whether a short structured account makes an experiment, replication, tool, dataset, negative result, or carefully framed idea more useful to other people.

The proposed pilot runs for four weeks with at most ten participants and ten submissions. You can take part without an institution, a popular GitHub project, or a payment. A human moderator checks scope, completeness, rights, privacy, safety, and abuse; publication is not scientific peer review. Human reviews and vouches are not available in this first pilot.

I am a practitioner building this around the work people do with agents and AI systems. That gives me a concrete perspective on documenting experiments and limitations, not universal research expertise. I will keep intake small, record corrections, and ask for help or pause when a decision exceeds my capacity.

If you choose to participate, I would ask you to prepare one note from work you can safely share and give feedback on saving a draft, submitting, understanding the labels, and reading someone else's record. Participation is voluntary, there is no response-time guarantee, and you can ask about export or withdrawal before publishing. I will not use social metrics to prioritize your work.

The approved service link, actual dates, monitored contact, and adopted privacy and content terms must be inserted and checked before sending this invitation. No outreach is authorized by this draft. An academic contributor should check their intended venue's policies before publishing; participation does not promise academic credit, indexing, or future acceptance.

## Pilot completion decision template

Record the actual version and deployment, pilot dates and scope, participant consent route, submitted and completed counts, unresolved items, author time, founder time, queue age, concrete reader uses, accessibility findings, report and appeal burden, actual cost, correction handling, and restored-backup result. Separate observations from inference and publish only safe aggregates.

Choose one outcome: continue at the same cap, continue at a lower cap with named repairs, pause for specific gates, or wind down with export and public status notices. Record the decision owner, reasons, risks, budget and availability for the next period, outstanding participant obligations, and the next review date. No continuing operation, public launch, outreach, or new spending should be inferred from an optimistic pilot narrative.
