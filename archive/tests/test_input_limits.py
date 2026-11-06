"""Synthetic-only input boundaries across writing scripts and browser newlines."""
from unittest.mock import Mock, patch
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse

from archive import services
from archive.forms import SubmissionForm
from archive.middleware import BoundaryMiddleware
from archive.models import CONTENT_FIELDS, Submission, Version
from archive.tests.test_guarantees import Accounts, content


TEXT_FIELDS = tuple(name for name in CONTENT_FIELDS
                    if name not in ('kind', 'license', 'artifacts'))
SCRIPTS = ('x', 'é', 'ش', '界', 'あ', '한', '𐐀', '😀')


def at_limit(name, character):
    """Native maxlength counts a supplementary character as two UTF-16 units."""
    limit = Submission._meta.get_field(name).max_length
    return fill_units(limit, character)


def fill_units(limit, character):
    width = len(character.encode('utf-16-le')) // 2
    count, remainder = divmod(limit, width)
    return character * count + 'x' * remainder


def full_form(character):
    values = content(**{name: at_limit(name, character) for name in TEXT_FIELDS})
    # Eight valid links, 8,000 characters including seven line breaks.
    prefix = 'https://example.org/synthetic/'
    values['artifacts'] = '\n'.join(prefix + fill_units(length - len(prefix), character)
                                    for length in [1000] * 7 + [993])
    return values


class SubmissionCharacterBoundaries(SimpleTestCase):
    def test_every_text_field_accepts_each_script_at_limit_and_refuses_one_more(self):
        for character in SCRIPTS:
            for name in TEXT_FIELDS:
                with self.subTest(script=character, field=name):
                    values = {**content(), name: at_limit(name, character), 'revision': 0}
                    accepted = SubmissionForm(values)
                    self.assertTrue(accepted.is_valid(), accepted.errors.as_json())
                    refused = SubmissionForm({**values, name: values[name] + 'x'})
                    self.assertFalse(refused.is_valid())
                    self.assertIn(name, refused.errors)
                    self.assertIn('maxlength', accepted.fields[name].widget_attrs(
                        accepted.fields[name].widget))

    def test_textarea_newlines_count_once_before_length_validation(self):
        for name in TEXT_FIELDS:
            if name in ('title', 'byline'):
                continue
            limit = Submission._meta.get_field(name).max_length
            expected = 'x' * (limit - 2) + '\nx'
            for newline in ('\n', '\r\n', '\r'):
                with self.subTest(field=name, newline=repr(newline)):
                    values = {**content(), name: expected.replace('\n', newline), 'revision': 0}
                    accepted = SubmissionForm(values)
                    self.assertTrue(accepted.is_valid(), accepted.errors.as_json())
                    self.assertEqual(accepted.cleaned_data[name], expected)
                    refused = SubmissionForm({**values, name: values[name] + 'x'})
                    self.assertFalse(refused.is_valid())
                    self.assertIn(name, refused.errors)

    def test_artifact_field_limit_and_crlf_counting_match_the_other_fields(self):
        values = full_form('界')
        self.assertEqual(len(values['artifacts']), 8000)
        form = SubmissionForm({**values, 'artifacts': values['artifacts'].replace('\n', '\r\n'),
                               'revision': 0})
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(form.cleaned_data['artifacts'], values['artifacts'])
        refused = SubmissionForm({**values, 'artifacts': values['artifacts'] + 'x', 'revision': 0})
        self.assertFalse(refused.is_valid())
        self.assertIn('artifacts', refused.errors)


class SubmissionSaveBoundaries(Accounts, TestCase):
    def setUp(self):
        self.accounts()
        # These tests save private drafts while intake is paused.
        self.capacity.intake_open = False
        self.capacity.save()
        self.client.force_login(self.author)

    def test_whole_form_at_all_field_limits_saves_for_every_script(self):
        submission = self.draft()
        for character in SCRIPTS:
            with self.subTest(script=character):
                values = full_form(character)
                data = {**values, 'revision': submission.revision, 'action': 'save',
                        'csrfmiddlewaretoken': 'x' * 64}
                # Browser submission serializes textarea line endings as CRLF.
                data = {key: value.replace('\n', '\r\n') if isinstance(value, str) else value
                        for key, value in data.items()}
                body = urlencode(data)
                if character == '界':
                    self.assertGreater(len(body), 96 * 1024)
                self.assertLessEqual(len(body), settings.DATA_UPLOAD_MAX_MEMORY_SIZE)
                response = self.client.post(reverse('edit', args=[submission.pk]), body,
                                            content_type='application/x-www-form-urlencoded')
                self.assertEqual(response.status_code, 302)
                submission.refresh_from_db()
                for name in CONTENT_FIELDS:
                    self.assertEqual(getattr(submission, name), values[name])
                self.assertEqual(submission.state, Submission.State.DRAFT)
                self.assertFalse(self.capacity.intake_open)

    def test_overlong_fields_reach_validation_without_mutating_the_draft(self):
        submission = self.draft()
        for character in SCRIPTS:
            with self.subTest(script=character):
                data = {**content(methods=at_limit('methods', character) + 'x'),
                        'revision': submission.revision, 'action': 'save'}
                response = self.client.post(reverse('edit', args=[submission.pk]), urlencode(data),
                                            content_type='application/x-www-form-urlencoded')
                self.assertEqual(response.status_code, 400)
                self.assertIn('methods', response.context['form'].errors)
                self.assertContains(response, 'href="#id_methods"', status_code=400)
                submission.refresh_from_db()
                self.assertEqual(submission.methods, '')
                self.assertEqual(submission.revision, 0)

    def test_draft_and_policy_pages_explain_the_actual_limits(self):
        submission = self.draft()
        response = self.client.get(reverse('edit', args=[submission.pk]))
        self.assertContains(response, 'At most 10,000 characters.')
        self.assertContains(response, 'a line break counts once')
        self.assertContains(response, '512 KiB')
        policy = self.client.get(reverse('policies'))
        self.assertContains(policy, '512 KiB')
        self.assertContains(policy, 'in any writing script')
        self.assertContains(policy, 'href="#submission-limits"')

    def test_direct_service_save_normalizes_newlines_and_does_not_bypass_field_limit(self):
        submission = self.draft()
        values = content(methods='x' * 9998 + '\r\nx')
        services.save_submission(self.author, submission.pk, values, submission.revision)
        submission.refresh_from_db()
        self.assertEqual(submission.methods, 'x' * 9998 + '\nx')
        with self.assertRaises(services.WorkflowError):
            services.save_submission(self.author, submission.pk,
                                     content(methods='𐐀' * 5000 + 'x'), submission.revision)
        submission.refresh_from_db()
        self.assertEqual(submission.revision, 1)

    def test_legacy_supplementary_draft_remains_readable_and_exportable_on_refusal(self):
        values = content(methods='𐐀' * 6000)
        submission = Submission.objects.create(author=self.author, **values)
        self.assertEqual(self.client.get(reverse('edit', args=[submission.pk])).status_code, 200)
        exported = self.client.get(reverse('export_submission', args=[submission.pk]))
        self.assertEqual(exported.status_code, 200)
        self.assertEqual(exported.json()['research']['methods'], values['methods'])
        response = self.client.post(reverse('edit', args=[submission.pk]),
                                    urlencode({**values, 'revision': 0, 'action': 'save'}),
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 400)
        submission.refresh_from_db()
        self.assertEqual(submission.methods, values['methods'])
        self.assertEqual(submission.revision, 0)

    def test_legacy_frozen_crlf_retry_conflicts_without_rewriting_publication(self):
        values = content(methods='SYNTHETIC pre-upgrade\r\nsecond line')
        snapshot = {name: values[name] for name in CONTENT_FIELDS}
        original_digest = services.digest(snapshot)
        submission = Submission.objects.create(author=self.author, **values,
            revision=1, state=Submission.State.SUBMITTED,
            frozen_snapshot=snapshot, digest=original_digest)
        response = self.client.post(reverse('edit', args=[submission.pk]),
                                    urlencode({**values, 'revision': 0, 'action': 'submit'}),
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 409)
        submission.refresh_from_db()
        self.assertEqual(submission.frozen_snapshot, snapshot)
        self.assertEqual(submission.digest, original_digest)
        self.assertFalse(Version.objects.exists())
        services.decide(self.moderator, submission.pk, 'publish',
                        'SYNTHETIC legacy exact-version preservation', 1,
                        conflicts='None; synthetic fixture')
        version = Version.objects.get(submission=submission)
        self.assertEqual(version.snapshot, snapshot)
        self.assertEqual(version.digest, original_digest)


class HardRequestBoundaries(SimpleTestCase):
    def test_body_above_hard_limit_is_refused_before_form_parsing_or_downstream_work(self):
        downstream = Mock(return_value=HttpResponse('synthetic accepted request'))
        boundary = BoundaryMiddleware(downstream)
        factory = RequestFactory()
        for size, status in ((settings.DATA_UPLOAD_MAX_MEMORY_SIZE, 200),
                             (settings.DATA_UPLOAD_MAX_MEMORY_SIZE + 1, 413)):
            with self.subTest(size=size):
                downstream.reset_mock()
                request = factory.post('/workspace/synthetic/', 'x=1',
                                       content_type='application/x-www-form-urlencoded',
                                       CONTENT_LENGTH=str(size))
                with patch.object(type(request), '_load_post_and_files',
                                  side_effect=AssertionError('Form parsing reached')):
                    response = boundary(request)
                self.assertEqual(response.status_code, status)
                self.assertEqual(downstream.call_count, 1 if status == 200 else 0)

    def test_multipart_is_refused_before_form_parsing(self):
        downstream = Mock()
        request = RequestFactory().post('/workspace/synthetic/', {'synthetic': 'fileless multipart'})
        with patch.object(type(request), '_load_post_and_files',
                          side_effect=AssertionError('Form parsing reached')):
            response = BoundaryMiddleware(downstream)(request)
        self.assertEqual(response.status_code, 415)
        downstream.assert_not_called()


class PreParseAbuseBoundaries(Accounts, TestCase):
    def setUp(self):
        self.accounts()
        self.submission = self.draft()
        self.client = Client(enforce_csrf_checks=True)

    def test_larger_allowance_is_only_for_authenticated_editor_posts(self):
        body = 'methods=' + 'x' * (96 * 1024)
        for signed_in in (False, True):
            if signed_in:
                self.client.force_login(self.author)
            paths = [reverse('login'), reverse('operations'), reverse('new_submission'),
                     '/workspace/not-an-editor/']
            if not signed_in:
                paths.append(reverse('edit', args=[self.submission.pk]))
            for path in paths:
                with self.subTest(signed_in=signed_in, path=path):
                    with patch.object(WSGIRequest, '_load_post_and_files',
                                      side_effect=AssertionError('oversized request parsed')):
                        response = self.client.post(path, body,
                            content_type='application/x-www-form-urlencoded')
                    self.assertEqual(response.status_code, 413)

    def test_exhausted_principal_is_rejected_before_csrf_or_login_body_parsing(self):
        for signed_in, limit, route in ((False, 10, 'login'), (True, 60, 'edit')):
            with self.subTest(signed_in=signed_in):
                self.client = Client(enforce_csrf_checks=True)
                if signed_in:
                    self.client.force_login(self.author)
                path = reverse(route, args=[self.submission.pk] if signed_in else [])
                with patch('archive.middleware.time.time', return_value=1700000000):
                    # Invalid CSRF still consumes the principal's parse budget.
                    for _ in range(limit):
                        response = self.client.post(path, 'synthetic=1',
                            content_type='application/x-www-form-urlencoded')
                        self.assertEqual(response.status_code, 403)
                    with patch.object(WSGIRequest, '_load_post_and_files',
                                      side_effect=AssertionError('rate-exhausted request parsed')):
                        response = self.client.post(path, 'synthetic=1',
                            content_type='application/x-www-form-urlencoded')
                self.assertEqual(response.status_code, 429)
                self.assertEqual(response.headers['Retry-After'], '60')

    def test_authenticated_editor_can_save_full_multilingual_form_with_real_csrf(self):
        self.client.force_login(self.author)
        path = reverse('edit', args=[self.submission.pk])
        self.client.get(path)
        token = self.client.cookies['csrftoken'].value
        data = {**full_form('界'), 'revision': 0, 'action': 'save',
                'csrfmiddlewaretoken': token}
        response = self.client.post(path, urlencode(data),
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.methods, at_limit('methods', '界'))

    def test_authenticated_editor_still_requires_csrf(self):
        self.client.force_login(self.author)
        path = reverse('edit', args=[self.submission.pk])
        response = self.client.post(path, urlencode({**full_form('界'), 'revision': 0, 'action': 'save'}),
                                    content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 403)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.revision, 0)
