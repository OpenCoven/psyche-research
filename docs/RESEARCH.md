# Psyche Research: product research and proposed first release

Status: research and reversible implementation recommendation, recorded 2026-11-04. This document does not approve deployment, open intake, legal terms, a publication license, or launch. Implementation and test evidence belong in the project status and verification record; capabilities described here are requirements until demonstrated there.

## Evidence and assumptions

The initial local `OpenCoven/psyche-research` tree contained a single README and one initial commit. No charter or earlier discussion was present in that tree. The supplied project brief is the product authority for this work; it does not establish prior founder decisions, an independent governing body, available reviewers, funding, or scientific accreditation. A nearby `OpenCoven/research` checkout was present but contained no working-tree charter at its root; no private or unrelated materials have been imported here. If a charter is supplied later, reconcile it explicitly with this record.

The intended operator is one founder with bounded familiar assistance. Operator identity, jurisdiction, contact address, hosting region, budget, availability, and approved terms remain launch decisions. Assume an intentionally small pilot and ordinary web skills; do not assume an institutional account, domain, email service, DOI membership, paid plan, reviewer network, or external preservation agreement.

## What alternatives already provide

These are primary-source observations checked on 2026-11-04, not comparative performance evaluations. Policies change; recheck linked sources before making a public competitive claim.

| Alternative | Verified capability | Implication for Psyche Research |
| --- | --- | --- |
| arXiv | arXiv distinguishes moderation from peer review, operates an endorsement process, and retains version history. See [moderation](https://info.arxiv.org/help/moderation/index.html), [endorsement](https://info.arxiv.org/help/endorsement.html), and [version availability](https://info.arxiv.org/help/versions.html). | Do not claim to have invented preprints, versioning, or the moderation/review distinction. Psyche can choose open eligibility without copying endorsement requirements. |
| Zenodo | Users can deposit varied research objects; published records receive DOIs, and versions have separate records. Published metadata is public, including when files are restricted. See [about records](https://help.zenodo.org/docs/deposit/about-records/). | Recommend durable artifact deposits there when appropriate. A published restricted-file record is not private intake. Psyche must keep drafts private in its own workflow. |
| Zenodo communities | Communities can accept or decline submissions, including unpublished records; acceptance can publish the record. See [review submissions](https://help.zenodo.org/docs/communities/review-submissions/). | A curated overlay is feasible without building a new large-file preservation service. Human acceptance and public publication must remain an explicit boundary. |
| OpenReview | The platform supports configurable review forms and visibility, submission tracking, discussion, conflict information, and an API. See [about OpenReview](https://openreview.net/about) and [submission reader controls](https://docs.openreview.net/how-to-guides/workflow/how-to-change-who-can-access-submissions-after-the-deadline). | Review infrastructure is an existing capability. Running it still requires people, policies, conflict handling, and capacity; software does not supply independent reviewers. |
| JOSS | JOSS offers external human review of research software and a concise software paper, with a defined scope and review process. Its current author guidance requires AI-use disclosure. See [about JOSS](https://joss.theoj.org/about) and [submission guidance](https://joss.readthedocs.io/en/latest/submitting.html). | Direct suitable software authors toward an established journal when that fits their needs. Psyche's initial notes are not equivalent to JOSS acceptance or peer review. |
| PREreview | PREreview combines a review platform, training, and collaborative reviewing activities. See [about PREreview](https://prereview.org/about). | Reviewer learning, recognition, and inclusion already have active communities. Psyche should learn from and link to them without promising a comparable network. |
| Hugging Face Hub | Repository discussions and pull requests support collaboration around models, datasets, and Spaces. See [Hub collaboration documentation](https://huggingface.co/docs/hub/repositories-pull-requests-discussions). | Practitioners already discuss artifacts where they build. Psyche must add useful synthesis and bounded claims rather than duplicate a repository discussion thread. |

## Approach comparison

| Approach | Smallest useful version | Founder burden | Main limits | Recommendation |
| --- | --- | --- | --- | --- |
| Overlay on existing repositories and archives | A structured research note, stable Psyche version URL, citation metadata, links to immutable artifact versions, private intake, and human scope moderation. | Moderate editorial effort; small application and metadata storage; external hosts retain artifact burden. | External links and retention can fail; Psyche cannot guarantee third-party preservation; artifact hosts have their own policies. | Start here. Build a narrow curated overlay, with local structured content sufficient to understand the claim and limitations. |
| Curated publication | Commissioned or selected essays with editorial revision and a regular issue cadence. | High per-article editing, author recruitment, fact checking, and schedule pressure. | Can privilege founder interests, become a bottleneck, and imply editorial expertise beyond actual capacity. | Borrow clear editorial guidance, avoid a promised issue cadence or novelty contest. |
| Independently hosted archive | Own file deposits, file processing, storage quotas, identifiers, preservation, takedowns, search, and long-term recovery. | Highest security, privacy, legal, storage, and continuity burden. | Malware, unsafe previews, personal data, preservation expectations, and migration cost exceed a small first pilot. | Defer file custody and archival guarantees until demonstrated need and funded operational capacity exist. |

The proposed first release is a curated practitioner research overlay, implemented as a small modular monolith. It preserves each published Psyche note and its metadata while linking to author-controlled artifact versions. This meets the archive reading and citation path without accepting arbitrary files or becoming a scientific journal. The recommendation is an operational judgment based on one-founder capacity, not evidence that this approach will attract contributors.

## Who it serves and why they would return

Contributors are independent AI builders, applied researchers, maintainers, replication authors, and practitioners who have a concrete question, evidence or an explicit evidence gap, and a useful account of what happened. Academic authors are welcome on the same terms. Affiliation, employer, followers, stars, prior publication, payment, and social endorsement are never eligibility requirements. Realistic capacity limits apply to everyone through the same disclosed rules.

Readers are builders choosing an implementation approach, researchers looking for reproducible observations, maintainers diagnosing failures, and reviewers deciding whether to inspect a bounded claim. A useful page should answer: what was attempted, on which version and environment, what evidence supports the claim, what failed, what is unknown, and how to cite or reproduce it safely.

The first formats are an experiment or field report, replication or negative result, tool or dataset note, and a clearly marked hypothesis or position note. A hypothesis must separate existing evidence from proposed tests; it must not masquerade as an observed result. The format is a short accessible structured note, with linked methods permitted when the summary still identifies the procedure, environment, and relevant artifact version. A conventional paper is welcome but is not mandatory.

Author incentives are a stable versioned account, clear attribution, reusable citation metadata, an easier route from repository work to a coherent research record, and visible corrections. Reviewer incentives, when that later workflow is available, are a named, scoped contribution and a reusable review record. Neither recognition nor publication is a promise of academic credit, indexing, peer-review recognition, employment benefit, or favorable review.

Academic compatibility means exportable citations, optional ORCID or external identifiers, explicit licenses and artifact versions, related-work references, and a clear label that archive publication alone is not peer review. Authors must check their intended venue's prior-publication, anonymity, copyright, and preprint rules themselves. Psyche cannot promise that a particular conference or journal will accept work already posted here, and should not mirror another venue's private submission or review record.

Return visits are a hypothesis: readers may value a small chronological stream of useful practitioner results, replications, corrections, and concrete failure reports. The first release should provide browsing and plain text search with a stable deterministic order. A digest, subscriptions, recommendations, popularity ranking, and automated feeds are later choices requiring real demand, consent where needed, and operational support.

## Lean release boundary

The coherent first release includes a public introduction and honest labels; account-based private draft creation and resumption; required title, authors, summary, research format, question within abstract/methods, methods or methods link, claims or results, limitations, artifact references where available or a provenance explanation of their absence, provenance, license, and AI-assistance disclosure; human private moderation; explicit changes-requested and decline paths; human publication of an exact approved version; stable readable version pages and citation metadata; browse and search of published versions only; proposed revisions and corrections; withdrawal tombstones; abuse reporting; private appeals; intake pause and limits; and backup, restore, export, monitoring, and runbooks.

Exclusions are arbitrary file uploads, remote fetches, link previews, code execution, PDF compilation, agent-triggered publication, payment, DOI minting, public discussion threads, review matching, metrics-based rank, reputation scoring in product decisions, and guaranteed preservation of external artifacts. Optional human peer reviews and version-bound scoped vouches belong in the next milestone after the publication boundary is proven; the UI must say they are unavailable until implemented and reviewed.

A first-use draft should ask for only the title and a recognizable working summary, save partial input safely, and clearly mark what remains before submission. Require full metadata at submission, not at the first keystroke. Make saving explicit and acknowledge completion; avoid claiming unsaved text is durable. A conflict on an older editing session must preserve the user's input and offer a safe reconciliation path instead of silently overwriting a newer draft. This is a requirement to verify, not a claim that the current implementation already does so.

## Architecture recommendation

Prefer a maintained server-rendered framework, one relational database, ordinary migrations, explicit domain services for state transitions, and a small permission surface. Django is a reasonable reversible choice because authentication, forms, escaping, CSRF protection, database migrations, and an administrative foundation are available in one maintained stack. Use the maintained version selected and locked by the implementation, not an unpinned suggestion in this document. Private operational records must stay outside public indexes and exports.

For a single-host bounded pilot, SQLite with tested online backup and explicit transaction handling is a reasonable starting database if concurrent capacity behavior is tested against its actual locking semantics. Move to PostgreSQL before multiple application hosts or workloads require it. Do not claim that development database tests prove production concurrency. Ordinary private filesystem storage can hold operator-generated backups and exports outside the public web root; author artifacts remain links. Object storage becomes necessary only when file custody is deliberately added, with private buckets, controlled downloads, quotas, scanning, retention, and restored-state tests.

Do not add a queue, worker network, microservices, vector search, or an agent orchestration layer to the first slice. Operator-scheduled bounded maintenance is enough until a measured operation needs background work. If jobs are later introduced, every job needs a finite input and deadline, bounded retry policy, idempotency, least-privilege credentials, observable failure, and a way to stop it. No background job may cross the human publication boundary.

## Threat model and controls to prove

| Threat | Required control | Evidence needed |
| --- | --- | --- |
| Private drafts leak through IDs, search, previews, logs, or exports | Object-level authorization; one public published-version projection; no submitted body in public logs or telemetry; no public draft previews. | Anonymous and cross-account tests for every detail and list route, error path, search, export, log, and template; manual rendered check. |
| Account or role compromise | Framework sessions and CSRF; safe redirects; password controls; secure deployment cookies; explicit role grants; session termination; no self-approval. | Permission matrix and negative tests; production configuration check; operator access drill. |
| Stored XSS or injection | Render user content as escaped text; validate bounded URL fields; parameterized queries; avoid raw HTML and executable Markdown. | Malicious fixtures in all user text fields, search terms, and URLs; inspect rendered output and response headers. |
| SSRF or code execution | Do not fetch submitted links, render external previews, import repositories, run notebooks, execute code, or process uploaded files in routine intake. | Tests that link validation has no network side effects and file requests are rejected; dependency and source review. |
| Sybil spam, queue exhaustion, or burst traffic | Neutral account and global limits, serialized capacity checks, request/body bounds, intake pause, rate limits, and abuse reporting. | Boundary, concurrent request, retry, pause, and recovery tests on the deployed database and proxy. |
| Mutable artifacts or stale endorsement | Save exact publication snapshots; require artifact revision identifiers where available; bind future reviews and vouches to one version and scope. | State-transition and stale-edit tests; future endorsement revocation and non-inheritance tests. |
| Coercion, conflicts, and founder discretion | Written reasons, private decision history, appeals with recusal limits disclosed, no silent deletion, explicit scope. | Operator walk-through and independently reviewed permission logic; no claim of independent review board. |
| Data loss or operator absence | Tested consistent backups, integrity checks, private export, recovery instructions, pause and wind-down plan. | Restore into a fresh database, recover a private and a public record, verify privacy and hashes, document actual elapsed time. |
| Prompt injection through submissions | No runtime agent access to private intake by default; sanitized opt-in tasks only; no publish or appeal credentials. | Inspect task payloads and credential/network boundaries; core path verified with no LLM. |

## Costs, sustainability, and unresolved risks

The likely dominant pilot cost is human moderation and correspondence, followed by hosting, backups, domain/TLS operations, transactional email if adopted, monitoring, incident response, and eventual specialist policy or legal advice. Large artifacts and LLM inference are intentionally excluded from the critical path. No pricing estimate here is a vendor quote. Founder approval of an actual monthly cash cap is required before provisioning; log real spend and effort rather than present an unsupported cheap-hosting claim.

The founder may lack domain expertise to assess a technical claim, and moderation does not repair that gap. The publication label must therefore remain modest. A small curated archive can still amplify weak claims, unsafe advice, or biased selection; explicit limits, evidence requirements, reasoned decisions, corrections, and willingness to pause reduce but do not eliminate those risks. Outside expertise remains a separate voluntary activity with disclosed scope.

External artifact links may disappear or change. Require immutable identifiers or archived releases where available, display the recorded version and access context, and never imply Psyche has verified or preserved all linked content. Authors may have conflicting coauthor, employer, dataset, privacy, or venue obligations. A checklist records their declaration; it does not amount to legal clearance.

## Decision ledger

| ID | Decision or proposal | State | Revisit trigger |
| --- | --- | --- | --- |
| D1 | Start with a curated practitioner overlay rather than own arbitrary artifact storage. | Recommended reversible implementation default. | Pilot cannot convey evidence with linked artifacts, or an approved funded preservation plan exists. |
| D2 | Accept people on disclosed scope and capacity rules, without prestige or popularity requirements. | Required product invariant. | Never replace with reputation-based eligibility. |
| D3 | Use a small server-rendered modular monolith and ordinary relational storage. | Recommended reversible implementation default; selected stack recorded in project status. | Measured operational need, not fashion or familiarity alone. |
| D4 | Defer human peer reviews and vouches to the next milestone; label them unavailable. | Recommended phasing permitted by the brief. | Publication privacy, versioning, and operations pass; real reviewer commitments exist. |
| D5 | Keep reputation research opt-in, isolated, disabled by default, and unable to affect product decisions. | Required product invariant. | Any proposal to use it in admission, access, ranking, visibility, or priority must be rejected. |
| D6 | Start with no runtime LLM requirement and no familiar publication authority. | Required product invariant. | Assistive tasks have consent, a bounded data contract, and a demonstrated need. |
| D7 | Run a bounded pilot only after explicit go/no-go. | Proposed operating decision; requires founder approval before invitations or launch. | Gates in the pilot plan pass and operator accepts the concrete pilot plan. |

## Hypotheses and disconfirming evidence

H1: a structured practitioner note reduces the work of turning an experiment into a reusable research account. Measure author time, abandoned drafts, and requested help; reject or redesign if the form merely duplicates existing documentation or forces unsupported claims.

H2: readers return for replications, limitations, and corrections around agent work. Measure useful follow-up actions and repeat voluntary use in the pilot; traffic, stars, and account count are insufficient evidence.

H3: one founder can moderate the selected scope in a bounded weekly budget. Measure total handling and appeal effort per submission; reduce scope or pause when the budget is exceeded rather than mask backlog with automation.

H4: authors and academics find a versioned record useful alongside existing repositories and venues. Ask about actual citation, reuse, and venue conflicts; a survey answer alone is weaker than a cited or reused note.

H5: optional scoped reviews will add value after the archive is usable. Test only with explicit reviewer consent and real availability in the next milestone; do not manufacture reviews to make the archive appear active.

H6: any reputation signal might help study bias or gaming. This is a research question, never a publication feature justification. A null result, harmful bias, inadequate consent, re-identification risk, or absence of a meaningful study design is a reason not to run the experiment.
