# Optional reputation research: isolated shadow protocol

Status: later research proposal, disabled and unimplemented, 2026-11-04. The current archive does not collect GitHub activity, followers, stars, recommendations, votes, or a reputation score. There is no scoring model, reputation database, data collector, study participant set, or public score. This protocol does not authorize collection, outreach, profiling, provisioning, or a production experiment.

## Non-negotiable boundary

No reputation or study signal may decide or influence eligibility, account access, submission admission, human review access, moderation priority, appeals, ranking, public visibility, discovery order, or any trust label. The rule includes indirect influence through a moderator dashboard, notification order, badges, account annotations, recommendations, or private hints. A score is not a measure of scientific truth, expertise in every domain, or research quality.

The production archive must continue normally if the study, its files, and its owners are absent. There must be no production import, database join, foreign key, API dependency, shared credential, callback, event consumer, feature flag carrying scores, or write-back route to the application. The current product's chronological discovery and neutral capacity/permission rules remain the only relevant behavior. Even a promising study result cannot authorize relaxing this boundary.

## Research question and first stage

The first useful question is whether proposed social proxies are too easy to game or too dependent on unequal opportunity to justify further study. Begin with synthetic data only, clearly labeled and kept out of public archive records. A study can compare intentionally varied fixture profiles with identical underlying evidence: a new account, an established account, a private-work contributor, an account active on another host, and manipulated stars or recommendations. These are invented test conditions, never real people or claims about actual groups.

Before any analysis, preregister the exact question, proposed formula or signal transformations, fixture-generation rules, comparison groups, missing-data behavior, intended sensitivity checks, stopping rules, owner, output audience, and limitations. No formula is selected here. Do not define a target labeled "scientific truth," use moderation acceptance as scientific ground truth, or train on decisions whose unfairness is the subject being examined.

Try to falsify the usefulness of the proxy by varying stars, followers, contribution frequency, account age, recommendation networks, and visible work while holding the evidence constant. Measure how much a hypothetical score changes, whether sparse data turns into a penalty, and whether removing a manipulable signal changes conclusions. A large unstable difference for equivalent evidence is evidence against that proxy; it is not a reason to prioritize one profile in the archive.

Publish a useful null or adverse finding if appropriate, with the fixture design and limitations. There is no requirement to invent a scoring product to justify this research. If the synthetic stage already shows the experiment lacks a defensible purpose, stop before collecting human data.

## Human-data stage: a separate approval gate

A real-data study requires a new reviewable plan and explicit founder approval, a named research owner, a justified question that synthetic data cannot answer, an appropriate ethics/privacy assessment, a cash and time budget, and an approved consent and retention process. An archive account, a public profile, or a public repository is not consent to profiling. Contacting potential participants also requires explicit outreach authorization.

Participation must be genuinely optional. Declining, withdrawing, having no GitHub account, doing private work, using another platform, or leaving a metric blank must have no effect on archive treatment or reviewer access. The consent text must state the exact fields, source, purpose, storage location, who can see them, study duration, outputs, deletion route, and practical limits on retracting already released aggregate analysis. Do not publish the names of people who decline or withdraw.

Use participant-supplied snapshots of the minimal agreed public fields when feasible. A future collection tool needs its own source, rate, terms, credential, and security review; no scraper or token is authorized here. Do not collect follower identities, social graphs, private repository activity, contacts, emails, employer lists, manuscript contents, moderation notes, appeals, reports, sessions, passwords, tokens, or precise location. Do not infer protected or sensitive traits from names, profiles, language, or network patterns.

If a study truly requires demographic or other sensitive attributes to evaluate bias, that is a separate higher-sensitivity protocol with a compelling question, suitable review, specific consent, restricted access, careful disclosure control, and a deletion plan. The ordinary pilot does not collect them. A convenience sample of public platform users cannot establish fairness for people it excludes.

## Isolation and data contract

| Element | Proposed handling | Prohibited connection |
| --- | --- | --- |
| Study workspace | Separate directory or system with an approved owner and access list; no public web serving. | No production runtime mount or shared archive database. |
| Study identifier | Random study-only identifier. | No production account ID, author ID, work ID, or persistent score annotation. |
| Identity mapping | Only if necessary for consent withdrawal; separate restricted file held by the human owner and promptly expired. | No evaluator access to identities merely to improve predictions. |
| Consent record | Restricted owner record with agreed fields, purpose, date, expiry, withdrawal route. | No upload to public GitHub issues or research pages. |
| Input snapshot | Minimal participant-agreed data with source and time, or synthetic fixture clearly labeled. | No live feed or private archive read credential. |
| Analysis | Offline bounded run with no network by default; pinned code and logged configuration. | No production API calls, writes, queue actions, or publication tools. |
| Outputs | Restricted aggregates with disclosure review before sharing. | No per-person score, leaderboard, admission hint, badge, or recommendation. |

Pseudonymization is not anonymization. Public metric combinations, timestamps, rare activity patterns, and small groups can re-identify a person. Minimize precision, avoid publishing row-level records, suppress or combine sparse cells, and assess whether even an aggregate could identify someone. No universal cell-size threshold is claimed adequate here; the approved study must justify its own disclosure rule. If a useful result cannot be released safely, do not release the sensitive data.

## Bias, gaming, and cold starts

| Risk | What to examine | Decision consequence |
| --- | --- | --- |
| Bought or coordinated stars/followers | Perturb counts and model coordinated inflation in synthetic fixtures. | Report proxy instability; do not build a higher social threshold. |
| Recommendation rings and reciprocal votes | Compare independent statements with coordinated synthetic networks. | Do not interpret agreement counts as independent evidence or scientific consensus. |
| Activity farming | Vary commit frequency, trivial contributions, mirrored repositories, and bot activity without changing underlying work. | Visible activity is not a valid substitute for contribution assessment. |
| Unequal time, resources, and platform access | Examine missingness and selection mechanisms without inventing sensitive attributes. | Do not treat low visible activity as low ability or trustworthiness. |
| Private or non-GitHub work | Include absent-profile and off-platform conditions. | Missing social data must not become a product disadvantage. |
| Account age and cold starts | Compare identical evidence for new and established synthetic accounts. | No probationary visibility penalty, waiting-time advantage, or endorsement prerequisite. |
| Popularity feedback | Model prior visibility increasing metrics and later visibility again. | A self-reinforcing loop is a confound, not evidence of merit. |
| Conflicted human labels | Inspect whether evaluators know identities or prior scores; keep decisions from becoming unexamined ground truth. | Findings must disclose label limits and avoid circular claims. |
| Privacy and re-identification | Assess rare combinations, small samples, identity mappings, and output joins. | Stop or reduce collection when disclosure risk exceeds the value of the question. |

Do not claim these tests establish demographic fairness, identify every Sybil account, or distinguish all real contributors from abuse. A person can be credible with no platform history, and a popular account can be compromised or wrong. Abuse controls in the archive should continue to examine actual behavior, rights, privacy, safety, capacity, and evidence under published rules, independent of study proxies.

## Provenance and results record

For each approved run, record the study protocol version, owner, code revision, input classification and digest, consent coverage, field list, collection time, missing-data handling, transformations, configuration, dependencies, output digest, failures, excluded records with reasons, sensitivity checks, and limitations. Store no secret values or raw identifying data in ordinary run logs. Separate preregistered analysis from later exploration to avoid presenting a selected positive result as a planned test.

A result should say exactly which synthetic or consenting sample was studied, what the study observed, what cannot be inferred, and how gaming, selection, confounding, missingness, and uncertainty affect interpretation. A correlation does not establish merit or cause. A successful isolated computation is not evidence that the score can safely enter archive decisions; that use remains prohibited.

## Kill switch, withdrawal, and deletion

The default kill switch is absence: no study process runs and the archive has no study dependency. For any approved later run, the human owner must be able to stop the specific job, disable scheduled collection, revoke study-only access, disconnect data sources, and quarantine outputs immediately. Stopping the study must not pause archive publication, alter discovery, or lock contributor accounts.

Proposed retention for a small human-data study is no more than 30 days for raw identifiable snapshots and the identity mapping, and 90 days for pseudonymous analysis inputs, with the actual consented schedule approved before collection. These are proposals, not implemented deletion promises. Keep only reviewed aggregate results or clearly synthetic fixtures longer when justified and disclosed. Do not quietly extend retention to rescue an interesting analysis.

On withdrawal, stop future collection and exclude the participant from future analysis. The owner identifies and deletes the relevant raw, mapped, derived, and cached records where feasible; regenerates unreleased aggregates; records which already released results cannot practically be recalled; and follows the adopted backup-expiry procedure. Record completion without retaining the deleted profile as proof. A restriction on the identity mapping is not deletion of the underlying data.

If there are backups, the study plan must specify access, expiry, restored-state exclusion of deleted records, and verification of the deletion schedule. Do not claim immediate deletion from all copies when a backup retention window remains. A future worker needs bounded retries and a tested stop path so a failed collector cannot continue after withdrawal.

## Acceptance before any human-data run

1. An independent technical reviewer inspects the exact study code and confirms there is no production import, schema, API, credential, mount, write-back, or public score dependency. This is code review, not a scientific peer review or security certification.
2. Run production product tests with the study workspace absent, inaccessible, malformed, and containing extreme hypothetical values; admission, permissions, queue ordering, public discovery, and visibility must remain identical. No production test should need a real social account or profile.
3. Prove the collection and analysis limits, consent refusal path, withdrawal exclusion, deletion, backup expiry, and stop switch in synthetic drills. Inspect the final serialized outputs for identity and sensitive-data leakage.
4. Record approvals and unresolved limitations, then obtain explicit authorization for the exact human-data collection. Until that step, use synthetic material only and keep the study disabled.

## Current evidence and limits

Source inspection on 2026-11-04 found no reputation fields in the archive models or form field list, no score in the publication/capacity permission services, and discovery ordered by published time and ID. The tests include attempted reputation inputs and order checks; actual terminal results belong in the verification record. This inspection is bounded to the current local tree and must be repeated after changes. No human-data study, collection, scoring performance, bias finding, or deletion drill is claimed to have occurred.
