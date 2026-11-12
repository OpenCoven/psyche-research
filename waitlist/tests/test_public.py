from unittest.mock import patch
from django.conf import settings
from django.db import OperationalError
from django.test import Client, TestCase, override_settings
from waitlist.models import AddressBudget, CollectionState, Registration


@override_settings(WAITLIST_COLLECTION_ENABLED=True)
class PublicWaitlistTests(TestCase):
    def setUp(self):
        CollectionState.objects.update_or_create(pk=1, defaults={'paused': False})
        self.data = {'email': 'Private.Person@example.net', 'name': 'Private Person', 'interest': 'reader', 'consent': 'on'}

    def submit(self, **changes):
        from urllib.parse import urlencode
        return self.client.post('/', urlencode(self.data | changes), content_type='application/x-www-form-urlencoded')

    def test_home_offers_waitlist_without_accounts(self):
        response = self.client.get('/')
        self.assertContains(response, 'Join the waitlist')
        self.assertNotContains(response, 'Sign in')
        self.assertNotContains(response, '/accounts/')

    def test_new_registration_is_private_and_does_not_create_account(self):
        response = self.submit()
        self.assertRedirects(response, '/confirmation/')
        row = Registration.objects.get()
        self.assertEqual((row.email, row.name, row.interest, row.privacy_version),
                         ('private.person@example.net', 'Private Person', 'reader', '2026-11-11'))
        self.assertEqual(CollectionState.objects.get().retained_count, 1)
        self.assertEqual(settings.INSTALLED_APPS, ['django.contrib.contenttypes', 'django.contrib.staticfiles', 'waitlist.apps.WaitlistConfig'])
        page = self.client.get('/confirmation/?email=private.person@example.net')
        self.assertNotContains(page, row.email)
        self.assertEqual(page['Cache-Control'], 'private, no-store')

    def test_duplicate_does_not_overwrite_and_has_identical_public_result(self):
        first = self.submit()
        second = self.submit(email='PRIVATE.PERSON@example.net', name='Attacker', interest='both')
        self.assertEqual((first.status_code, first.url, first.content), (second.status_code, second.url, second.content))
        self.assertEqual(Registration.objects.count(), 1)
        self.assertEqual(Registration.objects.get().name, 'Private Person')

    def test_validation_and_consent_never_store_or_reflect_private_values(self):
        for changes in [{'consent': ''}, {'interest': 'manuscript'}, {'email': 'private-malformed'},
                        {'name': 'x' * 101}, {'name': 'private\x00name'}]:
            with self.subTest(changes=changes):
                result = self.submit(**changes)
                self.assertEqual(result.status_code, 400)
                self.assertNotContains(result, 'Private.Person', status_code=400)
                self.assertContains(result, 'Check these details', status_code=400)
        self.assertFalse(Registration.objects.exists())

    def test_global_and_address_budgets_do_not_depend_on_membership(self):
        for _ in range(3):
            self.assertEqual(self.submit().status_code, 302)
        self.assertEqual(self.submit().status_code, 429)
        CollectionState.objects.update(minute_attempts=30)
        self.assertEqual(self.submit(email='new@example.net').status_code, 429)
        for bucket in AddressBudget.objects.values():
            self.assertNotIn('example', str(bucket))

    def test_honeypot_consumes_budget_without_registration(self):
        self.assertEqual(self.submit(website='bot').status_code, 302)
        self.assertFalse(Registration.objects.exists())
        self.assertEqual(CollectionState.objects.get().minute_attempts, 1)

    def test_pause_and_capacity_refuse_new_and_duplicate_equally(self):
        self.submit()
        for field in ['paused', 'retained_count']:
            CollectionState.objects.update(paused=False, retained_count=0)
            CollectionState.objects.update(**{field: True if field == 'paused' else 1000})
            self.assertEqual(self.submit().status_code, 503)
            self.assertEqual(self.submit(email='new@example.net').status_code, 503)
        self.assertEqual(Registration.objects.count(), 1)

    @override_settings(WAITLIST_COLLECTION_ENABLED=False)
    def test_environment_pause_overrides_database_resume(self):
        self.assertEqual(self.submit().status_code, 503)
        self.assertFalse(Registration.objects.exists())

    def test_database_failure_is_safe_and_no_false_confirmation(self):
        with patch('waitlist.services.CollectionState.objects.select_for_update', side_effect=OperationalError('private@example.net password')):
            response = self.submit()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b'private@example.net', response.content)
        self.assertNotIn(b'password', response.content)

    def test_csrf_upload_and_body_size_controls(self):
        from urllib.parse import urlencode
        self.assertEqual(Client(enforce_csrf_checks=True).post('/', urlencode(self.data), content_type='application/x-www-form-urlencoded').status_code, 403)
        self.assertEqual(self.client.post('/', self.data).status_code, 415)
        self.assertEqual(self.client.post('/', 'x' * 8193, content_type='application/x-www-form-urlencoded').status_code, 413)
        self.assertEqual(self.client.post('/', '&'.join(f'f{i}=x' for i in range(9)), content_type='application/x-www-form-urlencoded').status_code, 413)
        self.assertFalse(Registration.objects.exists())

    def test_public_routes_cannot_reach_archive_or_operator_tools(self):
        for route in ['/accounts/login/', '/accounts/workos/callback/', '/archive/', '/research/1/', '/dashboard/',
                      '/operations/', '/admin/', '/waitlist/export/', '/waitlist/delete/', '/static/private.json']:
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 404)
                self.assertEqual(self.client.post(route, 'x=y', content_type='application/x-www-form-urlencoded').status_code, 404)

    def test_confirmation_and_privacy_do_not_query_database(self):
        with self.assertNumQueries(0):
            self.assertEqual(self.client.get('/confirmation/').status_code, 200)
            self.assertEqual(self.client.get('/privacy/').status_code, 200)
