"""Fresh-file process-loss probe; deliberately crashes only its synthetic child."""
import os
from pathlib import Path
import subprocess
import sys
from datetime import timedelta
from unittest.mock import patch


def run_crash_probe():
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.test import Client, RequestFactory, override_settings
    from django.utils import timezone
    from archive import workos_auth as auth
    from archive.models import WorkOSCredential, WorkOSIdentity
    call_command('migrate', verbosity=0)
    user = get_user_model().objects.create_user('synthetic-crash-author')
    identity = WorkOSIdentity.objects.create(user=user, client_id='client_synthetic', subject='user_synthetic')
    browser = Client()
    browser.force_login(user)
    session = browser.session
    credential = WorkOSCredential.objects.create(session_id=session.session_key, identity=identity,
        sealed='synthetic-once-only', provider_session_id='session_synthetic',
        expires_at=timezone.now() + timedelta(hours=8))
    session[auth.CREDENTIAL] = str(credential.pk)
    session.save()
    child = r'''
import os,django
from pathlib import Path
django.setup()
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory,override_settings
from archive import workos_auth as auth
request=RequestFactory().get('/workspace/')
request.user=get_user_model().objects.get(username='synthetic-crash-author')
request.session=SessionStore(session_key=os.environ['SYNTHETIC_SESSION_KEY'])
def exchange(sealed,consume):
    assert sealed=='synthetic-once-only'
    consume()
    with Path(os.environ['SYNTHETIC_EXCHANGE_LOG']).open('w') as f:
        f.write('provider consumed old credential');f.flush();os.fsync(f.fileno())
    os._exit(17)
auth.check_session=exchange
with override_settings(AUTH_PROVIDER='workos',WORKOS_CLIENT_ID='client_synthetic'):
    auth.authenticate_session(request)
'''
    result = subprocess.run([sys.executable,'-c',child],
        env={**os.environ,'SYNTHETIC_SESSION_KEY':session.session_key},
        capture_output=True,text=True,timeout=20)
    assert result.returncode == 17, (result.returncode, result.stdout, result.stderr)
    assert Path(os.environ['SYNTHETIC_EXCHANGE_LOG']).read_text() == 'provider consumed old credential'
    credential.refresh_from_db()
    assert credential.claim is not None and credential.sealed == ''
    from django.contrib.sessions.backends.db import SessionStore
    request = RequestFactory().get('/workspace/')
    request.user = user
    request.session = SessionStore(session_key=session.session_key)
    with override_settings(AUTH_PROVIDER='workos',WORKOS_CLIENT_ID='client_synthetic'), \
            patch('archive.workos_auth.check_session') as check, \
            patch('archive.workos_auth.time.monotonic',side_effect=[0,6]):
        try:
            auth.authenticate_session(request)
        except auth.RefreshBusy:
            pass
        else:
            raise AssertionError('Claim was unexpectedly reusable after process loss')
        check.assert_not_called()
    print('Committed empty claim survived process loss; old credential was not exchanged again')
