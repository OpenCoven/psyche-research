"""Synthetic concurrent-session drill, only called inside isolated test databases."""
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db import connections
from django.test import Client, override_settings
from django.utils import timezone
from datetime import timedelta

from archive import workos_auth as auth
from archive.models import WorkOSIdentity, WorkOSCredential


def run_callback_commit_boundary():
    """An independent connection must see state consumption before code exchange."""
    from types import SimpleNamespace
    from urllib.parse import parse_qs, urlsplit
    from cryptography.hazmat.primitives.asymmetric import rsa
    from workos import WorkOSClient
    from archive.tests.test_workos_auth import SYNTHETIC_SETTINGS
    import jwt

    user = get_user_model().objects.create_user('synthetic-callback-commit')
    WorkOSIdentity.objects.create(user=user, client_id='client_synthetic', subject='user_synthetic')
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode({'iss': SYNTHETIC_SETTINGS['WORKOS_ISSUER'], 'sub': 'user_synthetic',
        'sid': 'session_synthetic', 'client_id': 'client_synthetic',
        'iat': int(time.time()) - 5, 'exp': int(time.time()) + 300}, key, algorithm='RS256')
    response = SimpleNamespace(user=SimpleNamespace(id='user_synthetic', email_verified=True),
        access_token=token, refresh_token='synthetic-refresh', impersonator=None)
    counts = []

    def exchange(**kwargs):
        probe = connections['default'].copy(alias='synthetic-commit-probe')
        try:
            with probe.cursor() as cursor:
                cursor.execute('SELECT count(*) FROM archive_workosloginattempt')
                counts.append(cursor.fetchone()[0])
        finally:
            probe.close()
        assert counts[-1] == 0, 'Callback consumption was not committed before provider exchange'
        return response

    with override_settings(**SYNTHETIC_SETTINGS), patch('archive.workos_auth.client') as factory, \
            patch('archive.workos_auth.jwks') as keys:
        real = WorkOSClient(api_key='sk_test_synthetic_only', client_id='client_synthetic')
        factory.return_value.user_management.get_authorization_url.side_effect = real.user_management.get_authorization_url
        factory.return_value.user_management.authenticate_with_code.side_effect = exchange
        keys.return_value.get_signing_key_from_jwt.return_value = SimpleNamespace(key=key.public_key())
        browser = Client()
        started = browser.post('/accounts/workos/start/', 'next=%2Fworkspace%2F',
                               content_type='application/x-www-form-urlencoded')
        assert started.status_code == 302
        state = parse_qs(urlsplit(started['Location']).query)['state'][0]
        finished = browser.get('/accounts/workos/callback/', {'state': state, 'code': 'synthetic-code'})
        assert counts == [0], 'Independent connection observed unconsumed callback state: ' + repr(counts)
        assert finished.status_code == 302, finished.status_code


def run_session_overlap():
    user = get_user_model().objects.create_user('synthetic-refresh-race')
    WorkOSIdentity.objects.create(user=user, client_id='client_synthetic', subject='user_synthetic')
    browser = Client()
    browser.force_login(user)
    stored = browser.session
    credential = WorkOSCredential.objects.create(session_id=stored.session_key,
        identity=WorkOSIdentity.objects.get(user=user), sealed='synthetic-once-only-token',
        provider_session_id='session_synthetic', expires_at=timezone.now()+timedelta(hours=8))
    stored[auth.CREDENTIAL] = str(credential.pk)
    stored.save()
    key = stored.session_key
    config = dict(connections.databases['default'])
    entered, release, second_started, second_finished = Event(), Event(), Event(), Event()
    counter_lock = Lock()
    calls = []

    def check(sealed, consume_refresh):
        if sealed == 'synthetic-once-only-token':
            consume_refresh()
            with counter_lock:
                calls.append(sealed)
                if len(calls) > 1:
                    raise auth.InvalidLogin()
            entered.set()
            assert release.wait(10), 'The test did not release the first refresh'
        else:
            assert sealed == 'synthetic-replacement-token'
        return 'synthetic-replacement-token', {'sub': 'user_synthetic', 'sid': 'session_synthetic'}

    def request(second=False):
        # Preserve the disposable PostgreSQL search_path in thread-local connections.
        connections.databases['default'] = dict(config)
        try:
            client = Client()
            client.cookies['sessionid'] = key
            if second:
                second_started.set()
            return client.get('/workspace/').status_code
        finally:
            if second:
                second_finished.set()
            connections.close_all()

    with override_settings(AUTH_PROVIDER='workos', WORKOS_CLIENT_ID='client_synthetic'), \
            patch('archive.workos_auth.check_session', side_effect=check), \
            ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(request)
        try:
            assert entered.wait(10), 'The first request never reached refresh'
            second = pool.submit(request, True)
            assert second_started.wait(10), 'The second request did not start'
            # The old middleware completes the second request against the old token.
            # The fixed middleware waits on the real database session lock instead.
            second_finished.wait(0.5)
        finally:
            release.set()
        statuses = [first.result(timeout=15), second.result(timeout=15)]
    assert statuses == [200, 200], 'Overlapping requests lost authenticated access: ' + repr(statuses)
    assert len(calls) == 1, 'A one-use refresh token was exchanged more than once'
    row = Session.objects.get(session_key=key)
    credential.refresh_from_db()
    assert credential.sealed == 'synthetic-replacement-token'
    assert auth.SESSION_DATA not in row.get_decoded()


def run_durable_refresh_boundary():
    """Real independent commits, view rollback and stale saves on either backend."""
    from django.contrib.sessions.backends.db import SessionStore
    from django.db import transaction
    from django.http import HttpResponse
    from archive.middleware import WorkOSDatabaseSessionMiddleware
    from django.test import RequestFactory

    user = get_user_model().objects.create_user('synthetic-refresh-durability')
    identity = WorkOSIdentity.objects.create(user=user, client_id='client_synthetic', subject='user_synthetic')
    browser = Client()
    browser.force_login(user)
    stored = browser.session
    credential = WorkOSCredential.objects.create(session_id=stored.session_key, identity=identity,
        sealed='synthetic-old-token', provider_session_id='session_synthetic',
        expires_at=timezone.now()+timedelta(hours=8))
    stored[auth.CREDENTIAL] = str(credential.pk)
    stored.save()
    stale = SessionStore(session_key=stored.session_key)
    dict(stale.items())
    exchanges = []

    def check(sealed, consume):
        if sealed == 'synthetic-old-token':
            consume()
            probe = connections['default'].copy(alias='synthetic-refresh-commit-probe')
            try:
                with probe.cursor() as cursor:
                    cursor.execute('SELECT sealed, claim FROM archive_workoscredential WHERE session_id=%s',
                                   [stored.session_key])
                    persisted = cursor.fetchone()
                assert persisted[0] == '' and persisted[1], 'Provider exchange preceded durable consumption'
            finally:
                probe.close()
            exchanges.append(sealed)
        else:
            assert sealed == 'synthetic-replacement-token'
        return 'synthetic-replacement-token', {'sub': 'user_synthetic', 'sid': 'session_synthetic'}

    def failing_view(request):
        with transaction.atomic():
            get_user_model().objects.create_user('synthetic-rolled-back-user')
            transaction.set_rollback(True)
        return HttpResponse(status=500)

    with override_settings(AUTH_PROVIDER='workos', WORKOS_CLIENT_ID='client_synthetic'), \
            patch('archive.workos_auth.check_session', side_effect=check):
        request = RequestFactory().get('/workspace/')
        request.COOKIES['sessionid'] = stored.session_key
        request.user = user
        middleware = WorkOSDatabaseSessionMiddleware(auth.WorkOSSessionMiddleware(failing_view))
        assert middleware(request).status_code == 500
        assert not get_user_model().objects.filter(username='synthetic-rolled-back-user').exists()
        stale['synthetic'] = 'stale ordinary response'
        stale.save()
        assert browser.get('/workspace/').status_code == 200
    credential.refresh_from_db()
    assert credential.sealed == 'synthetic-replacement-token' and credential.claim is None
    assert exchanges == ['synthetic-old-token'], 'Consumed credential was exchanged again'

