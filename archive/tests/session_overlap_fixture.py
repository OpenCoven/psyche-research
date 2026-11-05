"""Synthetic concurrent-session drill, only called inside isolated test databases."""
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.db import connections
from django.test import Client, override_settings

from archive import workos_auth as auth
from archive.models import WorkOSIdentity


def run_session_overlap():
    user = get_user_model().objects.create_user('synthetic-refresh-race')
    WorkOSIdentity.objects.create(user=user, client_id='client_synthetic', subject='user_synthetic')
    browser = Client()
    browser.force_login(user)
    stored = browser.session
    stored.update({auth.SESSION_DATA: 'synthetic-once-only-token',
                   auth.SESSION_SUBJECT: 'user_synthetic', auth.SESSION_ID: 'session_synthetic',
                   auth.SESSION_STARTED: time.time()})
    stored.save()
    key = stored.session_key
    config = dict(connections.databases['default'])
    entered, release, second_started, second_finished = Event(), Event(), Event(), Event()
    counter_lock = Lock()
    calls = []

    def check(sealed):
        if sealed == 'synthetic-once-only-token':
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
    assert row.get_decoded()[auth.SESSION_DATA] == 'synthetic-replacement-token'

