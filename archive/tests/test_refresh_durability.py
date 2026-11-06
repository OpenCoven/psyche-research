"""Synthetic durability regressions; no provider, production data or credentials."""
import os
from itertools import count
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.db import OperationalError, connections, transaction
from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TransactionTestCase, override_settings
from django.utils import timezone
from workos import WorkOSClient
from workos.session import seal_session_from_auth_response, unseal_data

from archive import workos_auth as auth
from archive.middleware import WorkOSDatabaseSessionMiddleware
from archive.models import WorkOSCredential, WorkOSIdentity
from archive.tests.test_workos_auth import SYNTHETIC_SETTINGS


@override_settings(**SYNTHETIC_SETTINGS)
class RefreshDurabilityTests(TransactionTestCase):
    """Real commits remain outside ordinary request/view transactions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.author = get_user_model().objects.create_user('synthetic-durable-author')
        self.identity = WorkOSIdentity.objects.create(user=self.author,
            client_id='client_synthetic', subject='user_synthetic')
        self.browser = Client()
        self.browser.force_login(self.author)
        self.session = self.browser.session
        self.expired = self.token(exp=int(time.time()) - 1)
        self.fresh = self.token()
        self.old = self.sealed(self.expired, 'synthetic-once-only-refresh')
        self.replacement = self.sealed(self.fresh, 'synthetic-replacement-refresh')
        self.credential = WorkOSCredential.objects.create(session_id=self.session.session_key,
            identity=self.identity, sealed=self.old, provider_session_id='session_synthetic',
            expires_at=timezone.now() + timedelta(hours=8))
        self.session[auth.CREDENTIAL] = str(self.credential.pk)
        self.session.save()
        self.api_patch = patch('archive.workos_auth.client')
        self.api = self.api_patch.start().return_value
        self.addCleanup(self.api_patch.stop)
        sdk = WorkOSClient(api_key='sk_test_synthetic_only', client_id='client_synthetic')
        self.api.user_management.get_logout_url.side_effect = sdk.user_management.get_logout_url
        self.refresh = self.api.user_management.load_sealed_session.return_value.refresh
        self.refresh.return_value = SimpleNamespace(authenticated=True, sealed_session=self.replacement)
        self.keys_patch = patch('archive.workos_auth.jwks')
        self.keys = self.keys_patch.start().return_value
        self.keys.get_signing_key_from_jwt.return_value = SimpleNamespace(key=self.key.public_key())
        self.addCleanup(self.keys_patch.stop)

    def token(self, **changes):
        claims = {'iss': SYNTHETIC_SETTINGS['WORKOS_ISSUER'], 'sub': 'user_synthetic',
            'sid': 'session_synthetic', 'client_id': 'client_synthetic',
            'iat': int(time.time()) - 5, 'exp': int(time.time()) + 300}
        claims.update(changes)
        return jwt.encode(claims, self.key, algorithm='RS256', headers={'kid':'synthetic'})

    def sealed(self, token, refresh):
        return seal_session_from_auth_response(access_token=token, refresh_token=refresh,
            user={'id':'user_synthetic','email_verified':True},
            cookie_password=SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])

    def request(self, path='/workspace/'):
        request = RequestFactory().get(path)
        request.user = self.author
        request.COOKIES['sessionid'] = self.session.session_key
        request.session = SessionStore(session_key=self.session.session_key)
        return request

    def test_committed_claim_contains_no_old_token_before_provider_exchange(self):
        observed = []
        def exchange():
            probe = connections['default'].copy(alias='synthetic-durable-probe')
            try:
                with probe.cursor() as cursor:
                    cursor.execute('SELECT sealed, claim FROM archive_workoscredential WHERE session_id=%s',
                        [self.session.session_key])
                    observed.append(cursor.fetchone())
            finally:
                probe.close()
            self.assertEqual(observed[0][0], '')
            self.assertTrue(observed[0][1])
            return SimpleNamespace(authenticated=True, sealed_session=self.replacement)
        self.refresh.side_effect = exchange
        auth.authenticate_session(self.request())
        self.assertEqual(len(observed), 1)
        self.credential.refresh_from_db()
        self.assertIsNone(self.credential.claim)
        self.assertEqual(unseal_data(self.credential.sealed,
            SYNTHETIC_SETTINGS['WORKOS_COOKIE_PASSWORD'])['refresh_token'], 'synthetic-replacement-refresh')

    def test_downstream_database_rollback_cannot_restore_consumed_credentials(self):
        def failing_view(request):
            try:
                with transaction.atomic():
                    get_user_model().objects.create_user('synthetic-must-rollback')
                    raise OperationalError('synthetic downstream transaction failure')
            except OperationalError:
                return HttpResponse(status=503)
        middleware = WorkOSDatabaseSessionMiddleware(auth.WorkOSSessionMiddleware(failing_view))
        self.assertEqual(middleware(self.request()).status_code, 503)
        self.assertFalse(get_user_model().objects.filter(username='synthetic-must-rollback').exists())
        auth.authenticate_session(self.request())
        self.assertEqual(self.refresh.call_count, 1)
        self.credential.refresh_from_db()
        self.assertNotEqual(self.credential.sealed, self.old)

    def test_post_refresh_signing_key_outage_never_reuses_consumed_refresh(self):
        def key(token):
            if token == self.fresh:
                raise jwt.PyJWKClientConnectionError('synthetic outage after provider exchange')
            return SimpleNamespace(key=self.key.public_key())
        self.keys.get_signing_key_from_jwt.side_effect = key
        statuses = [self.browser.get('/workspace/').status_code for _ in range(2)]
        self.assertEqual(statuses, [503, 302])
        self.assertEqual(self.refresh.call_count, 1)
        self.assertFalse(WorkOSCredential.objects.filter(pk=self.credential.pk).exists())
        self.assertNotIn('_auth_user_id', self.browser.session)

    def test_stale_ordinary_session_save_cannot_overwrite_rotated_credentials(self):
        stale = SessionStore(session_key=self.session.session_key)
        dict(stale.items())
        auth.authenticate_session(self.request())
        rotated = WorkOSCredential.objects.get(pk=self.credential.pk).sealed
        stale['synthetic_ordinary_field'] = 'preserve ordinary session behavior'
        stale.save()
        auth.authenticate_session(self.request())
        self.assertEqual(WorkOSCredential.objects.get(pk=self.credential.pk).sealed, rotated)
        self.assertEqual(self.refresh.call_count, 1)
        self.assertNotIn(auth.SESSION_DATA, Session.objects.get(session_key=self.session.session_key).get_decoded())

    def test_pending_request_returns_busy_without_deleting_winning_claim(self):
        claim = uuid.uuid4()
        WorkOSCredential.objects.filter(pk=self.credential.pk).update(sealed='', claim=claim, claimed_at=timezone.now())
        with patch('archive.workos_auth.time.monotonic', side_effect=count(0, 6)):
            result = self.browser.get('/workspace/')
        self.assertEqual(result.status_code, 503)
        row = WorkOSCredential.objects.get(pk=self.credential.pk)
        self.assertEqual(row.claim, claim)
        self.assertEqual(row.sealed, '')
        self.assertTrue(Session.objects.filter(session_key=self.session.session_key).exists())
        self.refresh.assert_not_called()
        WorkOSCredential.objects.filter(pk=row.pk, claim=claim).update(sealed=self.replacement, claim=None, claimed_at=None)
        self.assertEqual(self.browser.get('/workspace/').status_code, 200)
        self.refresh.assert_not_called()

    def test_expired_claim_clears_local_login_and_cannot_block_fresh_login(self):
        WorkOSCredential.objects.filter(pk=self.credential.pk).update(sealed='', claim=uuid.uuid4(),
            claimed_at=timezone.now()-timedelta(seconds=31))
        self.assertEqual(self.browser.get('/workspace/').status_code, 302)
        self.assertFalse(WorkOSCredential.objects.filter(pk=self.credential.pk).exists())
        self.assertNotIn('_auth_user_id', self.browser.session)
        self.assertEqual(self.browser.get('/accounts/login/').status_code, 200)
        self.refresh.assert_not_called()

    def test_legacy_and_malformed_handles_still_allow_local_logout(self):
        for value in (None, 'malformed'):
            browser = Client()
            browser.force_login(self.author)
            session = browser.session
            if value is not None:
                session[auth.CREDENTIAL] = value
                session.save()
            self.assertEqual(browser.post('/accounts/logout/', 'action=logout',
                content_type='application/x-www-form-urlencoded').status_code, 302)
            self.assertNotIn('_auth_user_id', browser.session)

    def test_copied_credential_handle_cannot_authenticate_another_session(self):
        browser = Client()
        browser.force_login(self.author)
        session = browser.session
        session[auth.CREDENTIAL] = str(self.credential.pk)
        session.save()
        self.assertEqual(browser.get('/workspace/').status_code, 302)
        self.assertNotIn('_auth_user_id', browser.session)
        self.assertTrue(WorkOSCredential.objects.filter(pk=self.credential.pk).exists())
        self.refresh.assert_not_called()

    def test_outer_transaction_is_refused_before_any_provider_exchange(self):
        with transaction.atomic():
            with self.assertRaises(RuntimeError):
                auth.authenticate_session(self.request())
        self.refresh.assert_not_called()
        self.credential.refresh_from_db()
        self.assertEqual(self.credential.sealed, self.old)
        self.assertIsNone(self.credential.claim)

    def test_logout_during_exchange_cannot_be_resurrected_by_finalization(self):
        def exchange():
            # Exercise the actual logout path while the first request is in flight.
            other = Client()
            other.cookies['sessionid'] = self.session.session_key
            self.assertEqual(other.post('/accounts/logout/', 'action=logout',
                content_type='application/x-www-form-urlencoded').status_code, 302)
            self.assertFalse(WorkOSCredential.objects.filter(pk=self.credential.pk).exists())
            return SimpleNamespace(authenticated=True, sealed_session=self.replacement)
        self.refresh.side_effect = exchange
        self.assertEqual(self.browser.get('/workspace/').status_code, 302)
        self.assertFalse(WorkOSCredential.objects.filter(pk=self.credential.pk).exists())
        self.assertFalse(Session.objects.filter(session_key=self.session.session_key).exists())
        self.assertEqual(self.refresh.call_count, 1)

    def test_identity_revocation_during_exchange_cannot_restore_access(self):
        def exchange():
            WorkOSIdentity.objects.filter(pk=self.identity.pk).update(enabled=False)
            return SimpleNamespace(authenticated=True, sealed_session=self.replacement)
        self.refresh.side_effect = exchange
        self.assertEqual(self.browser.get('/workspace/').status_code, 302)
        self.assertFalse(WorkOSCredential.objects.filter(pk=self.credential.pk).exists())
        self.assertEqual(self.refresh.call_count, 1)
        WorkOSIdentity.objects.filter(pk=self.identity.pk).update(enabled=True)
        self.assertEqual(self.browser.get('/workspace/').status_code, 302)
        self.assertEqual(self.refresh.call_count, 1)

    def test_abandoned_claim_expires_without_reusing_old_credentials(self):
        WorkOSCredential.objects.filter(pk=self.credential.pk).update(sealed='', claim=uuid.uuid4(),
            claimed_at=timezone.now() - timedelta(seconds=31))
        self.assertEqual(self.browser.get('/workspace/').status_code, 302)
        self.assertFalse(WorkOSCredential.objects.filter(pk=self.credential.pk).exists())
        self.assertNotIn('_auth_user_id', self.browser.session)
        self.assertEqual(self.browser.get('/accounts/login/').status_code, 200)
        self.refresh.assert_not_called()


    def test_expiry_delete_that_loses_to_finalization_reloads_winner(self):
        WorkOSCredential.objects.filter(pk=self.credential.pk).update(sealed='', claim=uuid.uuid4(),
            claimed_at=timezone.now() - timedelta(seconds=31))
        def finalizer_wins(queryset):
            self.assertIs(queryset.model, WorkOSCredential)
            WorkOSCredential.objects.filter(pk=self.credential.pk).update(
                sealed=self.replacement, claim=None, claimed_at=None)
            return 0, {}
        with patch('django.db.models.query.QuerySet.delete', autospec=True, side_effect=finalizer_wins) as delete:
            auth.authenticate_session(self.request())
        self.assertEqual(delete.call_count, 1)
        self.assertTrue(WorkOSCredential.objects.filter(pk=self.credential.pk).exists())
        self.refresh.assert_not_called()


    def test_late_finalizer_cannot_resurrect_an_expired_claim(self):
        def exchange():
            WorkOSCredential.objects.filter(pk=self.credential.pk).update(
                claimed_at=timezone.now() - timedelta(seconds=31))
            other = Client()
            other.cookies['sessionid'] = self.session.session_key
            self.assertEqual(other.get('/workspace/').status_code, 302)
            return SimpleNamespace(authenticated=True, sealed_session=self.replacement)
        self.refresh.side_effect = exchange
        self.assertEqual(self.browser.get('/workspace/').status_code, 302)
        self.assertFalse(WorkOSCredential.objects.filter(pk=self.credential.pk).exists())
        self.assertEqual(self.refresh.call_count, 1)



class RefreshProcessCrashTests(SimpleTestCase):
    def test_process_loss_after_exchange_retains_no_consumable_refresh(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix='psyche-refresh-crash-') as directory:
            env = {**os.environ, 'LOCAL_DEVELOPMENT':'1', 'DJANGO_SETTINGS_MODULE':'config.settings',
                'DATABASE_PATH':str(Path(directory) / 'synthetic.sqlite3'),
                'SYNTHETIC_EXCHANGE_LOG':str(Path(directory) / 'exchange.txt')}
            env.pop('DATABASE_URL', None)
            result = subprocess.run([sys.executable, '-c',
                'from archive.tests.refresh_crash_fixture import run_crash_probe; run_crash_probe()'],
                cwd=root, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Committed empty claim survived process loss; old credential was not exchanged again', result.stdout)
