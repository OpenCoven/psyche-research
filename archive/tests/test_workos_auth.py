"""Synthetic AuthKit boundary tests: real signatures, local authority, no live provider."""
import base64
import hashlib
import io
import time
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, RequestFactory, TestCase, SimpleTestCase, override_settings
from django.http import HttpResponse
from django.utils import timezone
from workos import WorkOSClient
from workos.session import seal_session_from_auth_response, unseal_data

from archive.models import Event, Submission, WorkOSIdentity, WorkOSLoginAttempt, WorkOSCredential
from archive import workos_auth as auth

SYNTHETIC_SETTINGS = {
    'AUTH_PROVIDER': 'workos', 'WORKOS_API_KEY': 'sk_test_synthetic_only',
    'WORKOS_CLIENT_ID': 'client_synthetic',
    'WORKOS_REDIRECT_URI': 'http://testserver/accounts/workos/callback/',
    'WORKOS_ISSUER': 'https://api.workos.com/user_management/client_synthetic',
    'WORKOS_COOKIE_PASSWORD': base64.urlsafe_b64encode(b's' * 32).decode(),
}


@override_settings(**SYNTHETIC_SETTINGS)
class WorkOSAuthenticationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.author = get_user_model().objects.create_user('synthetic-workos-author',
            email='synthetic@example.invalid', password='synthetic-password-only')
        self.binding = WorkOSIdentity.objects.create(user=self.author,
            client_id='client_synthetic', subject='user_synthetic')
        self.api_patch = patch('archive.workos_auth.client')
        self.api = self.api_patch.start().return_value
        self.addCleanup(self.api_patch.stop)
        real = WorkOSClient(api_key='sk_test_synthetic_only', client_id='client_synthetic')
        self.api.user_management.get_authorization_url.side_effect = real.user_management.get_authorization_url
        self.api.user_management.get_logout_url.side_effect = real.user_management.get_logout_url
        self.keys_patch = patch('archive.workos_auth.jwks')
        self.keys = self.keys_patch.start().return_value
        self.keys.get_signing_key_from_jwt.return_value = SimpleNamespace(key=self.key.public_key())
        self.addCleanup(self.keys_patch.stop)
        self.api.user_management.authenticate_with_code.return_value = self.response()

    def token(self, **changes):
        claims = {'iss': SYNTHETIC_SETTINGS['WORKOS_ISSUER'], 'sub': 'user_synthetic',
            'sid': 'session_synthetic', 'client_id': 'client_synthetic',
            'iat': int(time.time()) - 5, 'exp': int(time.time()) + 300}
        claims.update(changes)
        return jwt.encode(claims, self.key, algorithm='RS256', headers={'kid': 'synthetic'})

    def response(self, **changes):
        data = {'user': SimpleNamespace(id='user_synthetic', email_verified=True),
            'access_token': self.token(), 'refresh_token': 'synthetic-refresh-token', 'impersonator': None}
        data.update(changes)
        return SimpleNamespace(**data)

    def begin(self, browser=None, next_path='/workspace/'):
        browser = browser or self.client
        response = browser.post('/accounts/workos/start/', urlencode({'next': next_path}), content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 302)
        return parse_qs(urlsplit(response['Location']).query)['state'][0]

    def finish(self, state, browser=None):
        return (browser or self.client).get('/accounts/workos/callback/', {'state': state, 'code': 'synthetic-code'})

    def sign_in(self):
        state = self.begin()
        self.assertEqual(self.finish(state).status_code, 302)

    def credential(self):
        return WorkOSCredential.objects.get(pk=self.client.session[auth.CREDENTIAL])

    def test_pkce_and_server_state_are_bound_to_browser_and_consumed_once(self):
        state = self.begin()
        attempt = WorkOSLoginAttempt.objects.get()
        args = self.api.user_management.get_authorization_url.call_args.kwargs
        challenge = base64.urlsafe_b64encode(hashlib.sha256(attempt.verifier.encode()).digest()).decode().rstrip('=')
        self.assertEqual(args['code_challenge_method'], 'S256')
        self.assertEqual(args['code_challenge'], challenge)
        self.assertEqual(attempt.state_hash, hashlib.sha256(state.encode()).hexdigest())
        self.assertEqual(self.finish(state, Client()).status_code, 400)
        self.api.user_management.authenticate_with_code.assert_not_called()
        self.assertEqual(self.finish(state).status_code, 302)
        self.assertFalse(WorkOSLoginAttempt.objects.exists())
        self.assertEqual(self.finish(state).status_code, 400)
        self.assertEqual(self.api.user_management.authenticate_with_code.call_count, 1)
        exchange = self.api.user_management.authenticate_with_code.call_args.kwargs
        self.assertEqual(exchange['code_verifier'], attempt.verifier)
        self.assertEqual(exchange['request_options']['max_retries'], 0)

    def test_expired_duplicate_and_superseded_callbacks_never_exchange(self):
        old = self.begin()
        new = self.begin()
        self.assertEqual(self.finish(old).status_code, 400)
        duplicate = self.client.get('/accounts/workos/callback/?' + urlencode([
            ('state', new), ('state', new), ('code', 'synthetic-code')]))
        self.assertEqual(duplicate.status_code, 400)
        WorkOSLoginAttempt.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.finish(new).status_code, 400)
        self.api.user_management.authenticate_with_code.assert_not_called()

    def test_no_email_linking_account_creation_or_external_role_escalation(self):
        self.binding.delete()
        before = get_user_model().objects.count()
        self.api.user_management.authenticate_with_code.return_value = self.response(
            user=SimpleNamespace(id='user_other', email_verified=True, email=self.author.email),
            access_token=self.token(sub='user_other', role='admin', permissions=['publish']))
        self.assertEqual(self.finish(self.begin()).status_code, 403)
        self.assertEqual(get_user_model().objects.count(), before)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(self.author.groups.exists())

    def test_signed_in_local_ownership_and_explicit_moderation_still_apply(self):
        self.sign_in()
        other = get_user_model().objects.create_user('synthetic-other')
        private = Submission.objects.create(author=other, title='SYNTHETIC PRIVATE SENTINEL')
        self.assertEqual(self.client.get('/workspace/').status_code, 200)
        denied = self.client.get(f'/workspace/{private.pk}/')
        self.assertEqual(denied.status_code, 404)
        self.assertNotContains(denied, private.title, status_code=404)
        self.assertEqual(self.client.get('/moderation/').status_code, 403)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.author.pk)
        sealed = self.credential().sealed
        self.assertNotIn('synthetic-refresh-token', sealed)
        data = unseal_data(sealed, SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])
        self.assertEqual(data['user'], {'id': 'user_synthetic', 'email_verified': True})

    def test_invalid_signature_issuer_client_subject_audience_or_impersonation_rejected(self):
        bad = [self.token(iss='https://attacker.invalid'), self.token(client_id='client_other'),
            self.token(sub='user_other'), self.token(aud='client_other'), self.token(act={'sub': 'operator'}),
            self.token(exp=int(time.time()) - 1),
            jwt.encode({'sub': 'user_synthetic'}, self.other_key, algorithm='RS256')]
        for token in bad:
            with self.subTest(token=token[:15]):
                browser = Client()
                self.api.user_management.authenticate_with_code.return_value = self.response(access_token=token)
                self.assertEqual(self.finish(self.begin(browser), browser).status_code, 503)
                self.assertNotIn('_auth_user_id', browser.session)

    def test_unverified_user_and_provider_impersonation_are_rejected(self):
        for response in [self.response(user=SimpleNamespace(id='user_synthetic', email_verified=False)),
                         self.response(impersonator={'email': 'synthetic@example.invalid'})]:
            self.api.user_management.authenticate_with_code.return_value = response
            self.assertEqual(self.finish(self.begin()).status_code, 503)
            self.assertNotIn('_auth_user_id', self.client.session)

    def test_session_fixation_legacy_password_session_and_local_password_route(self):
        state = self.begin()
        old_key = self.client.session.session_key
        self.assertEqual(self.finish(state).status_code, 302)
        self.assertNotEqual(old_key, self.client.session.session_key)
        legacy = Client()
        legacy.force_login(self.author)
        self.assertEqual(legacy.get('/workspace/').status_code, 302)
        self.assertNotIn('_auth_user_id', legacy.session)
        self.assertEqual(legacy.post('/accounts/login/', urlencode({'username': self.author.username,
            'password': 'synthetic-password-only'}), content_type='application/x-www-form-urlencoded').status_code, 405)
        self.assertEqual(legacy.get('/accounts/password/').status_code, 404)

    def test_safe_return_path_and_csrf_protection(self):
        browser = Client(enforce_csrf_checks=True)
        self.assertEqual(browser.post('/accounts/workos/start/', 'action=test', content_type='application/x-www-form-urlencoded').status_code, 403)
        page = browser.get('/accounts/login/?next=//attacker.invalid')
        self.assertContains(page, 'Continue to sign in')
        self.assertNotContains(page, 'name="password"')
        self.assertIn('https://api.workos.com', page['Content-Security-Policy'])
        token = browser.cookies['csrftoken'].value
        start = browser.post('/accounts/workos/start/', urlencode({'csrfmiddlewaretoken': token, 'next': '//attacker.invalid'}), content_type='application/x-www-form-urlencoded')
        state = parse_qs(urlsplit(start['Location']).query)['state'][0]
        self.assertEqual(self.finish(state, browser)['Location'], '/workspace/')
        self.assertEqual(browser.get('/accounts/logout/').status_code, 405)
        self.assertEqual(browser.post('/accounts/logout/', 'action=test', content_type='application/x-www-form-urlencoded').status_code, 403)
        token = browser.cookies['csrftoken'].value
        signed_out = browser.post('/accounts/logout/', urlencode({'csrfmiddlewaretoken': token}), content_type='application/x-www-form-urlencoded')
        self.assertEqual(urlsplit(signed_out['Location']).path, '/user_management/sessions/logout')
        self.assertNotIn('_auth_user_id', browser.session)

    @override_settings(ALLOWED_HOSTS=['testserver', 'other.example.invalid'])
    def test_sign_out_returns_only_to_the_configured_callback_origin(self):
        self.sign_in()
        hostile = 'https://attacker.invalid/'
        signed_out = self.client.post('/accounts/logout/?' + urlencode({'return_to': hostile, 'next': '//attacker.invalid'}),
            urlencode({'return_to': hostile, 'next': hostile, 'redirect_uri': hostile}),
            content_type='application/x-www-form-urlencoded', HTTP_HOST='other.example.invalid',
            HTTP_REFERER=hostile, HTTP_ORIGIN=hostile, HTTP_X_FORWARDED_HOST='attacker.invalid',
            HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(signed_out.status_code, 302)
        location = urlsplit(signed_out['Location'])
        self.assertEqual((location.scheme, location.netloc, location.path),
                         ('https', 'api.workos.com', '/user_management/sessions/logout'))
        self.assertEqual(parse_qs(location.query, strict_parsing=True),
                         {'session_id': ['session_synthetic'], 'return_to': ['http://testserver/']})
        self.api.user_management.get_logout_url.assert_called_once_with(
            session_id='session_synthetic', return_to='http://testserver/')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_sign_out_return_is_the_callback_origin_root_only(self):
        for callback, origin in [
                ('https://research.example.invalid/accounts/workos/callback/', 'https://research.example.invalid/'),
                ('https://research.example.invalid:8443/accounts/workos/callback/', 'https://research.example.invalid:8443/'),
                ('http://127.0.0.1:8011/accounts/workos/callback/', 'http://127.0.0.1:8011/'),
                ('http://[::1]:8011/accounts/workos/callback/', 'http://[::1]:8011/')]:
            with self.subTest(callback=callback), override_settings(WORKOS_REDIRECT_URI=callback):
                self.assertEqual(auth.logout_return_to(), origin)

    def test_sign_out_without_provider_session_stays_local(self):
        self.client.force_login(self.author)
        signed_out = self.client.post('/accounts/logout/', urlencode({'return_to': 'https://attacker.invalid/'}),
                                      content_type='application/x-www-form-urlencoded')
        self.assertEqual(signed_out['Location'], '/')
        self.api.user_management.get_logout_url.assert_not_called()

    def test_provider_failure_is_redacted_and_attempt_is_not_retried(self):
        self.api.user_management.authenticate_with_code.side_effect = RuntimeError('SYNTHETIC_SECRET private-token@example.invalid')
        state = self.begin()
        with self.assertLogs('archive.telemetry', level='INFO') as captured:
            result = self.finish(state)
        self.assertEqual(result.status_code, 503)
        self.assertNotIn('SYNTHETIC_SECRET', result.content.decode() + '\n'.join(captured.output))
        self.assertNotIn('synthetic-code', '\n'.join(captured.output))
        self.assertEqual(self.finish(state).status_code, 400)
        self.assertEqual(self.api.user_management.authenticate_with_code.call_count, 1)

    def test_signing_key_outage_blocks_mutation_without_destroying_valid_session(self):
        self.sign_in()
        self.keys.get_signing_key_from_jwt.side_effect = jwt.PyJWKClientConnectionError('synthetic outage')
        result = self.client.post('/workspace/new/', 'action=test', content_type='application/x-www-form-urlencoded')
        self.assertEqual(result.status_code, 503)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertFalse(Submission.objects.exists())

    def test_binding_disable_and_local_deactivation_take_effect_on_next_request(self):
        self.sign_in()
        self.binding.enabled = False
        self.binding.save()
        self.assertEqual(self.client.get('/workspace/').status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.binding.enabled = True
        self.binding.save()
        self.sign_in()
        self.author.is_active = False
        self.author.save()
        self.assertEqual(self.client.get('/workspace/').status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.author.is_active = True
        self.author.save()
        self.assertEqual(self.client.get('/workspace/').status_code, 302)

    def test_expired_access_token_refresh_checks_new_identity_and_retains_local_roles(self):
        self.sign_in()
        session = self.client.session
        credential = self.credential()
        credential.sealed = seal_session_from_auth_response(access_token=self.token(exp=int(time.time()) - 1),
            refresh_token='synthetic-old-refresh', user={'id': 'user_synthetic', 'email_verified': True},
            cookie_password=SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])
        credential.save(update_fields=['sealed'])
        refreshed = seal_session_from_auth_response(access_token=self.token(), refresh_token='synthetic-new-refresh',
            user={'id': 'user_synthetic', 'email_verified': True, 'email': 'synthetic-profile@example.invalid'},
            cookie_password=SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])
        self.api.user_management.load_sealed_session.return_value.refresh.return_value = SimpleNamespace(
            authenticated=True, sealed_session=refreshed)
        self.assertEqual(self.client.get('/workspace/').status_code, 200)
        data = unseal_data(self.credential().sealed, SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])
        self.assertEqual(data['refresh_token'], 'synthetic-new-refresh')
        self.assertNotIn('email', data['user'])
        self.assertFalse(self.author.groups.exists())

    def test_absolute_local_session_age_cannot_be_extended_by_refresh(self):
        self.sign_in()
        session = self.client.session
        credential = self.credential()
        credential.expires_at = timezone.now() - timedelta(seconds=1)
        credential.save(update_fields=['expires_at'])
        self.assertEqual(self.client.get('/workspace/').status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_overlapping_requests_do_not_reuse_a_consumed_refresh_token(self):
        """Two tabs can load the same expired session before either response saves it."""
        from django.contrib.sessions.backends.db import SessionStore

        self.sign_in()
        stored = self.client.session
        credential = self.credential()
        credential.sealed = seal_session_from_auth_response(
            access_token=self.token(exp=int(time.time()) - 1),
            refresh_token='synthetic-once-only-refresh',
            user={'id': 'user_synthetic', 'email_verified': True},
            cookie_password=SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])
        credential.save(update_fields=['sealed'])
        refreshed = seal_session_from_auth_response(
            access_token=self.token(), refresh_token='synthetic-replacement-refresh',
            user={'id': 'user_synthetic', 'email_verified': True},
            cookie_password=SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])
        refresh = self.api.user_management.load_sealed_session.return_value.refresh
        refresh.side_effect = [SimpleNamespace(authenticated=True, sealed_session=refreshed),
                               SimpleNamespace(authenticated=False)]
        requests = []
        for _ in range(2):
            request = RequestFactory().get('/workspace/')
            request.session = SessionStore(session_key=stored.session_key)
            dict(request.session.items())  # Both requests already cached the old token.
            request.user = self.author
            request.COOKIES['sessionid'] = stored.session_key
            requests.append(request)
        middleware = auth.WorkOSSessionMiddleware(lambda request: HttpResponse(status=200))
        from django.utils.module_loading import import_string
        middleware = import_string(settings.MIDDLEWARE[2])(middleware)
        for request in requests:
            self.assertEqual(middleware(request).status_code, 200)
        self.assertEqual(refresh.call_count, 1)
        self.assertTrue(Session.objects.filter(session_key=stored.session_key).exists())
        self.assertIn('_auth_user_id', requests[1].session)

    def test_refresh_survives_a_later_server_error_without_reusing_old_token(self):
        self.sign_in()
        session = self.client.session
        credential = self.credential()
        credential.sealed = seal_session_from_auth_response(
            access_token=self.token(exp=int(time.time()) - 1), refresh_token='synthetic-old-refresh',
            user={'id': 'user_synthetic', 'email_verified': True},
            cookie_password=SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])
        credential.save(update_fields=['sealed'])
        refreshed = seal_session_from_auth_response(
            access_token=self.token(), refresh_token='synthetic-new-refresh',
            user={'id': 'user_synthetic', 'email_verified': True},
            cookie_password=SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])
        refresh = self.api.user_management.load_sealed_session.return_value.refresh
        refresh.return_value = SimpleNamespace(authenticated=True, sealed_session=refreshed)
        # Use the real middleware around a failing view, including response saving.
        from archive.middleware import WorkOSDatabaseSessionMiddleware
        request = RequestFactory().get('/workspace/')
        request.COOKIES['sessionid'] = session.session_key
        request.user = self.author
        middleware = WorkOSDatabaseSessionMiddleware(
            auth.WorkOSSessionMiddleware(lambda request: HttpResponse(status=500)))
        self.assertEqual(middleware(request).status_code, 500)
        self.assertEqual(self.client.get('/workspace/').status_code, 200)
        self.assertEqual(refresh.call_count, 1)

    def test_malformed_return_paths_cannot_escape_or_crash_the_login_page(self):
        for value in ['//[', '//attacker.invalid/path', '/\\attacker.invalid', 'https://attacker.invalid', '/\nattacker']:
            self.assertEqual(auth.safe_next(value), '/workspace/')
        self.assertEqual(auth.safe_next('/workspace/?page=2'), '/workspace/?page=2')

    def test_external_initiation_starts_sdk_flow_without_button_and_completes_callback(self):
        response = self.client.get('/accounts/workos/initiate/', {'next':'//attacker.invalid'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response['Location']).hostname, 'api.workos.com')
        query = parse_qs(urlsplit(response['Location']).query)
        self.assertEqual(query['provider'], ['authkit'])
        self.assertEqual(query['redirect_uri'], [SYNTHETIC_SETTINGS['WORKOS_REDIRECT_URI']])
        self.assertEqual(self.finish(query['state'][0])['Location'], '/workspace/')

    def test_external_initiation_is_rate_limited_and_replaces_only_own_pending_state(self):
        for _ in range(10):
            self.assertEqual(self.client.get('/accounts/workos/initiate/').status_code, 302)
        self.assertEqual(self.client.get('/accounts/workos/initiate/').status_code, 429)
        self.assertEqual(WorkOSLoginAttempt.objects.count(), 1)

    def test_full_login_capacity_rejects_new_browser_without_creating_session(self):
        WorkOSLoginAttempt.objects.bulk_create([
            WorkOSLoginAttempt(state_hash=f'synthetic-state-{i}', browser_hash=f'synthetic-browser-{i}',
                verifier='synthetic-verifier', expires_at=timezone.now() + timedelta(minutes=5))
            for i in range(1000)
        ])
        response = self.client.get('/accounts/workos/initiate/')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(WorkOSLoginAttempt.objects.count(), 1000)
        self.assertEqual(Session.objects.count(), 0)
        self.assertNotIn('sessionid', response.cookies)
        self.api.user_management.get_authorization_url.assert_not_called()

    def test_expired_wrong_client_token_is_not_refreshed(self):
        self.sign_in()
        session = self.client.session
        credential = self.credential()
        credential.sealed = seal_session_from_auth_response(
            access_token=self.token(exp=int(time.time()) - 1, client_id='client_other'),
            refresh_token='synthetic-refresh', user={'id':'user_synthetic', 'email_verified':True},
            cookie_password=SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])
        credential.save(update_fields=['sealed'])
        self.assertEqual(self.client.get('/workspace/').status_code, 302)
        self.api.user_management.load_sealed_session.assert_not_called()

    def test_operator_link_is_audited_unique_and_does_not_grant_roles(self):
        self.binding.delete()
        out = io.StringIO()
        options = {'username': self.author.username, 'client_id': 'client_synthetic',
                   'subject': 'user_synthetic', 'reason': 'Synthetic operator binding', 'stdout': out}
        call_command('link_workos_identity', **options)
        self.assertTrue(Event.objects.filter(kind='workos_identity_linked').exists())
        self.assertFalse(self.author.groups.exists())
        with self.assertRaises(CommandError):
            call_command('link_workos_identity', **{**options, 'subject': 'user_other'})
        call_command('link_workos_identity', **options, disable=True)
        self.assertFalse(WorkOSIdentity.objects.get(user=self.author).enabled)
        self.assertTrue(Event.objects.filter(kind='workos_identity_disabled').exists())


class WorkOSConfigurationTests(SimpleTestCase):
    def test_activation_requires_complete_valid_configuration_without_echoing_secrets(self):
        import os
        import subprocess
        import sys
        env = {**os.environ, **SYNTHETIC_SETTINGS, 'LOCAL_DEVELOPMENT': '1',
               'DJANGO_ALLOWED_HOSTS': 'testserver', 'DJANGO_SETTINGS_MODULE': 'config.settings'}
        for changes in [{'WORKOS_COOKIE_PASSWORD': 'SYNTHETIC_PRIVATE_BAD_KEY'},
                        {'WORKOS_API_KEY': ''}, {'WORKOS_ISSUER': ''},
                        {'WORKOS_REDIRECT_URI': 'https://SYNTHETIC_PRIVATE_BAD_HOST.invalid/accounts/workos/callback/'},
                        {'WORKOS_REDIRECT_URI': 'http://testserver/accounts/workos/callback/'},
                        {'WORKOS_REDIRECT_URI': 'https://testserver:bad/accounts/workos/callback/'}]:
            result = subprocess.run([sys.executable, '-c', 'import config.settings'],
                env={**env, **changes}, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('WorkOS requires', result.stderr)
            self.assertNotIn('SYNTHETIC_PRIVATE', result.stderr)
        valid = {**env, 'WORKOS_REDIRECT_URI': 'https://testserver/accounts/workos/callback/'}
        result = subprocess.run([sys.executable, '-c', 'import config.settings'], env=valid,
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
