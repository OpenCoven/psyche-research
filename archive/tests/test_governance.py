"""Contributor-facing governance guarantees for issue #2. Every account and manuscript here is a synthetic fixture."""
import re
from pathlib import Path
from unittest.mock import patch

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import OperationalError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from archive import services
from archive.forms import MAX_ARTIFACT_LINKS, validate_artifacts
from archive.models import CONTENT_FIELDS, Capacity, Submission
from archive.views import PUBLIC_FIELD_LIMITS
from archive.tests.test_guarantees import Accounts, content

ROOT = Path(settings.BASE_DIR)


def capacity_section(response):
    html = response.content.decode()
    match = re.search(r'<section id="capacity".*?</section>', html, re.S)
    assert match, 'The policies page must contain the founder capacity section.'
    return match.group(0)


@override_settings(PILOT_APPROVED=True)
class FounderCapacityDisclosure(Accounts, TestCase):
    def setUp(self):
        self.accounts()

    def test_policies_page_publishes_configured_limits_and_follows_audited_changes(self):
        current = services.configure(self.moderator, {'intake_open': False, 'queue_limit': 3, 'per_author_limit': 1, 'draft_limit': 7},
                                     Capacity.objects.get(pk=1).revision, 'Synthetic capacity reduction for a disclosure test.')
        response = self.client.get(reverse('policies'))
        self.assertContains(response, '<a href="#capacity">What one founder can sustain</a>', html=True)
        section = capacity_section(response)
        for expected in (
            'Intake is currently paused.', 'A new submission is accepted only while fewer than 3 items across the whole archive are awaiting a human decision.',
            'One submitted item at a time.', 'only while you have fewer than 1 active item,', 'fewer than 7 active items in total.',
            f'You can add up to {MAX_ARTIFACT_LINKS} public HTTPS artifact links.', f'Each signed-in editor save is limited to {settings.SUBMISSION_FORM_MAX_BYTES // 1024} KiB',
            'enough to use all the listed field limits in any writing script',
            f'are limited to {settings.DEFAULT_FORM_MAX_BYTES // 1024} KiB.',
            'They are capacity limits, not response times.', 'the only planned moderator', 'not yet accepted for a live pilot',
            'when the moderation queue is full', 'is a founder commitment, not a software control.',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, section)
        # Every free-text content field must be listed; kind and license are choices, not free text.
        self.assertEqual({name for name, _ in PUBLIC_FIELD_LIMITS}, set(CONTENT_FIELDS) - {'kind', 'license'})
        self.assertIn('a line break counts once', section)
        self.assertIn('<li>Methods or linked methods: 10,000 characters</li>', section)
        for name, label in PUBLIC_FIELD_LIMITS:
            with self.subTest(field=name):
                self.assertIn(f'<li>{label}: {Submission._meta.get_field(name).max_length:,} characters</li>', section)
        services.configure(self.moderator, {'intake_open': True, 'queue_limit': 4}, current.revision, 'Synthetic reopening for a disclosure test.')
        section = capacity_section(self.client.get(reverse('policies')))
        self.assertIn('Intake is currently open to scheduled pilot contributors.', section)
        self.assertIn('fewer than 4 items across the whole archive', section)
        self.assertNotIn('fewer than 3 items', section)

    def test_public_intake_status_matches_whether_a_submission_is_accepted(self):
        # Reviewer reproduction: intake_open alone must not be advertised as open when pilot approval is absent.
        for index, (intake_open, approved) in enumerate(((True, False), (True, True), (False, True), (False, False))):
            with self.subTest(intake_open=intake_open, approved=approved), override_settings(LOCAL_DEVELOPMENT=False, PILOT_APPROVED=approved):
                Capacity.objects.filter(pk=1).update(intake_open=intake_open)
                page = capacity_section(self.client.get(reverse('policies')))
                home = self.client.get(reverse('home')).content.decode()
                author = get_user_model().objects.create_user(f'synthetic-gate-author-{index}', password='synthetic-password-12345')
                draft = services.create_submission(author)
                try:
                    services.save_submission(author, draft.pk, content(), draft.revision, submit=True)
                    accepted = True
                except services.WorkflowError:
                    accepted = False
                self.assertEqual(accepted, intake_open and approved)
                self.assertEqual('Intake is currently open' in page, accepted)
                self.assertEqual('Intake is open' in home, accepted)

    def test_public_pages_describe_paused_intake_when_capacity_cannot_be_read(self):
        Capacity.objects.all().delete()
        for name in ('policies', 'home'):
            with self.subTest(missing_row=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'Intake is open')
        section = capacity_section(self.client.get(reverse('policies')))
        self.assertIn('Intake is currently paused. The configured limits cannot be read right now', section)
        self.assertNotIn('<dl', section)
        with patch.object(Capacity.objects, 'get', side_effect=OperationalError('synthetic outage')):
            response = self.client.get(reverse('policies'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pause or wind-down')

    def test_authors_can_export_their_own_work_while_intake_is_paused(self):
        submission = self.draft()
        services.save_submission(self.author, submission.pk, content(title='SYNTHETIC paused-export draft'), submission.revision)
        Capacity.objects.filter(pk=1).update(intake_open=False)
        self.client.force_login(self.author)
        response = self.client.get(reverse('export_submission', args=[submission.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['research']['title'], 'SYNTHETIC paused-export draft')

    def test_public_capacity_disclosure_does_not_vary_with_private_activity(self):
        before = self.client.get(reverse('policies')).content
        secret = 'SYNTHETIC-PRIVATE-CAPACITY-SENTINEL-4c19e'
        self.submitted(data=content(title=secret, abstract=secret))
        self.draft(self.other)
        after = self.client.get(reverse('policies'))
        self.assertNotContains(after, secret)
        # Queue occupancy and private record counts are never rendered; only configured limits change the page.
        self.assertEqual(before, after.content)

    def test_policies_page_keeps_open_eligibility_and_distinct_trust_records(self):
        response = self.client.get(reverse('policies'))
        html = response.content.decode()
        self.assertIn('University affiliation, employer prestige, GitHub activity, popularity, followers, reputation, and payment are not prerequisites.', html)
        self.assertIn('It is not scientific validation or peer review.', html)
        self.assertEqual(html.count('Not available in this release.'), 2, 'Human peer reviews and public vouches must both be labelled unavailable.')
        self.assertIn('They do not establish the truth, originality, reproducibility, or safety of a finding.', html)
        self.assertIn('Familiars have no autonomous publication or appeal authority.', html)
        self.assertIn('A score cannot decide publication, access, visibility, discovery order, or moderation priority.', html)
        self.assertIn('There is no public sign-up, request form or waitlist yet.', html)
        # Response times, boards and accreditation may appear only inside this explicit negation.
        self.assertIn('There is no verified independent review board, reviewer pool, accreditation, legal review, or guaranteed response time.', html)
        for overclaim in ('peer-reviewed', 'peer reviewed by', 'certified', 'accredited', 'we guarantee', 'wcag conformant', 'fully accessible'):
            with self.subTest(overclaim=overclaim):
                self.assertNotIn(overclaim, html.lower())
        self.assertIsNone(re.search(r'\b(?:within|in under|in less than|no later than)\s+\d+\s+(?:business\s+)?(?:hours?|days?|weeks?)\b', html, re.I))

    def test_wind_down_copy_promises_export_and_no_private_transfer_or_successor(self):
        html = self.client.get(reverse('policies')).content.decode()
        section = re.search(r'<section id="winddown".*?</section>', html, re.S).group(0)
        for expected in ('where it is safe, authors keep access', 'defined period to export their records', 'An emergency closure for harm could shorten that period',
                         'Private material is not handed to another operator without consent;', 'disclosures required by law',
                         'No successor operator, permanent hosting or preservation guarantee is promised', 'draft commitments pending founder adoption'):
            with self.subTest(expected=expected):
                self.assertIn(expected, section)


class GovernanceRecordContracts(SimpleTestCase):
    def test_stated_submission_bounds_match_enforced_validation_and_settings(self):
        links = [f'https://example.org/synthetic-artifact-{n}' for n in range(MAX_ARTIFACT_LINKS + 1)]
        self.assertEqual(validate_artifacts('\n'.join(links[:-1])).count('\n'), MAX_ARTIFACT_LINKS - 1)
        with self.assertRaises(ValidationError):
            validate_artifacts('\n'.join(links))
        kib = settings.DATA_UPLOAD_MAX_MEMORY_SIZE // 1024
        policies = (ROOT / 'docs' / 'POLICIES.md').read_text()
        self.assertIn(f'{kib} KiB', policies)
        self.assertIn('eight public HTTPS links', policies)
        self.assertEqual(MAX_ARTIFACT_LINKS, 8)

    def test_policy_drafts_cover_every_required_governance_topic(self):
        text = (ROOT / 'docs' / 'POLICIES.md').read_text()
        headings = re.findall(r'^## (.+)$', text, re.M)
        for required in ('Account and contributor responsibilities', 'Moderation decisions and independence limits', 'Corrections, revisions, and withdrawals',
                         'Appeals, complaints, and abuse reports', 'Privacy, retention, export, and incident handling', 'Pilot accounts and admission',
                         'What the founder can sustain', 'Accessibility', 'Pause, closure, and wind-down'):
            with self.subTest(heading=required):
                self.assertIn(required, headings)
        # Commitments added for issue #2; each names a behaviour the runbook and implementation must honour.
        for sentence in ('There is no public sign-up, request form or waitlist', 'Pending submissions are not judged on their merits during a closure.',
                         'The proposed export period is at least 30 days where that is safe and feasible',
                         'deletion at closure means destroying the database and its provider backups',
                         'Any static record or successor handoff must be built only from the public published-version set',
                         'That is a target, not a conformance claim.', 'is a founder commitment, not a software control.'):
            with self.subTest(sentence=sentence):
                self.assertIn(sentence, text)
        runbook = (ROOT / 'docs' / 'RUNBOOK.md').read_text()
        self.assertIn('Return each pending submission unpublished with a requested-changes decision', runbook)

    def test_reputation_and_runtime_model_providers_are_absent(self):
        forbidden_fields = {'reputation', 'score', 'followers', 'stars', 'votes', 'karma', 'rank', 'trust_score'}
        models = list(apps.get_app_config('archive').get_models()) + [get_user_model()]
        for model in models:
            with self.subTest(model=model.__name__):
                self.assertFalse(forbidden_fields.intersection(field.name for field in model._meta.get_fields()))
        providers = {'openai', 'anthropic', 'ai', 'langchain', 'litellm', 'cohere', 'mistralai', 'google-generativeai', 'google-genai', 'transformers', 'ollama'}
        pinned = {line.split('==')[0].strip().lower() for line in (ROOT / 'requirements.txt').read_text().splitlines() if '==' in line and not line.lstrip().startswith('#')}
        self.assertFalse(providers.intersection(pinned))
        pattern = re.compile(r'^\s*(?:from|import)\s+(openai|anthropic|langchain\w*|litellm|cohere|mistralai|transformers|ollama)\b', re.M)
        for path in list((ROOT / 'archive').rglob('*.py')) + list((ROOT / 'config').rglob('*.py')):
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertIsNone(pattern.search(path.read_text()))
