"""Exact-source waitlist browser acceptance, isolated synthetic data and loopback only."""
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def main():
    os.umask(0o077)
    report_dir = ROOT / 'var/waitlist-browser-review'
    report_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {'ok': False, 'server_stopped': False}
    with tempfile.TemporaryDirectory(prefix='psyche-waitlist-browser-') as temporary:
        scratch = Path(temporary).resolve()
        # An explicit environment allowlist prevents serving/provider settings from entering the fixture.
        task_env = {key: value for key, value in os.environ.items()
                    if key in {'PATH', 'HOME', 'TMPDIR', 'TMP', 'TEMP', 'LANG', 'LC_ALL', 'SYSTEMROOT'}}
        task_env.update(LOCAL_DEVELOPMENT='1', PILOT_APPROVED='0', AUTH_PROVIDER='local',
                        DATABASE_PATH=str(scratch / 'synthetic.sqlite3'),
                        DJANGO_SETTINGS_MODULE='config.waitlist_settings', WAITLIST_COLLECTION_ENABLED='1',
                        WAITLIST_OPERATOR='Synthetic test operator', WAITLIST_CONTACT='operator@example.invalid')
        os.environ.clear()
        os.environ.update(task_env)
        sys.path.insert(0, str(ROOT))
        import django
        django.setup()
        from django.conf import settings
        from django.core.management import call_command
        from waitlist.models import CollectionState, Registration
        if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3' or settings.DATABASE_PATH != scratch / 'synthetic.sqlite3':
            raise RuntimeError('Disposable browser database identity mismatch.')
        call_command('migrate', verbosity=0, interactive=False)
        CollectionState.objects.filter(pk=1).update(paused=False)
        with socket.socket() as available:
            available.bind(('127.0.0.1', 0))
            port = available.getsockname()[1]
        origin = f'http://127.0.0.1:{port}'
        names = subprocess.check_output(['git', 'ls-files', 'waitlist', 'templates/waitlist', 'static/waitlist',
            'config/waitlist_settings.py', 'config/waitlist_wsgi.py', 'config/settings.py', 'config/database.py',
            'requirements.txt', '.python-version', '.github/workflows/verify.yml', 'archive/tests/browser_process.mjs'], cwd=ROOT, text=True).splitlines()
        report['source'] = {'sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'tree': subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT, text=True).strip(),
            'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)),
            'files': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}}
        if report['source']['dirty']:
            raise RuntimeError('Browser evidence requires committed clean source.')
        server = None
        try:
            with (scratch / 'server.log').open('w') as log:
                server = subprocess.Popen([sys.executable, 'manage.py', 'runserver', '--insecure', '--noreload',
                    f'127.0.0.1:{port}'], cwd=ROOT, env=task_env, stdout=log, stderr=subprocess.STDOUT)
                for attempt in range(100):
                    if server.poll() is not None:
                        raise RuntimeError('Owned browser server exited before readiness.')
                    try:
                        with urllib.request.urlopen(origin + '/health/', timeout=1) as response:
                            if response.status == 200:
                                break
                    except (urllib.error.URLError, TimeoutError):
                        time.sleep(0.1)
                else:
                    raise RuntimeError('Owned browser server did not become ready.')
                for phase in ('flow', 'paused'):
                    if phase == 'paused':
                        CollectionState.objects.filter(pk=1).update(paused=True)
                    fixture = scratch / f'{phase}.json'
                    fixture.write_text(json.dumps({'origin': origin, 'phase': phase, 'review_directory': str(report_dir)}))
                    node = subprocess.Popen(['node', str(ROOT / 'waitlist/tests/browser_waitlist.mjs'), str(fixture)],
                        cwd=ROOT, env=task_env, start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    try:
                        output, errors = node.communicate(timeout=150)
                        if node.returncode:
                            raise RuntimeError('Owned browser contract failed: ' + errors[-5000:])
                        report[phase] = json.loads(output.strip().splitlines()[-1])
                    finally:
                        # This newly created process group contains only the owned Node/Chromium fixture.
                        for sig in (signal.SIGTERM, signal.SIGKILL):
                            try:
                                os.killpg(node.pid, sig)
                            except ProcessLookupError:
                                break
                            time.sleep(0.2)
                rows = list(Registration.objects.values('email', 'name', 'interest'))
                if rows != [{'email': 'browser-check@example.invalid', 'name': 'Synthetic browser fixture', 'interest': 'reader'}]:
                    raise RuntimeError('Duplicate, pause or registration database postcondition failed.')
                if not CollectionState.objects.get(pk=1).paused or CollectionState.objects.get(pk=1).retained_count != 1:
                    raise RuntimeError('Collection postcondition failed.')
                report['postcondition'] = {'registrations': 1, 'duplicate_unchanged': True, 'paused': True,
                                           'archive_or_accounts_installed': 'archive' in settings.INSTALLED_APPS or 'django.contrib.auth' in settings.INSTALLED_APPS}
                if report['postcondition']['archive_or_accounts_installed']:
                    raise RuntimeError('Private archive/account surface unexpectedly installed.')
                report['ok'] = True
        except BaseException as error:
            report['first_failure'] = str(error)
            raise
        finally:
            if server is not None:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=10)
                with socket.socket() as probe:
                    report['server_stopped'] = server.poll() is not None and probe.connect_ex(('127.0.0.1', port)) != 0
            report['ok'] = report['ok'] and report['server_stopped']
            (report_dir / 'report.json').write_text(json.dumps(report, indent=2))
            if not report['server_stopped']:
                raise RuntimeError('Owned browser server shutdown is unverified.')
    print(json.dumps({'ok': report['ok'], 'source': report['source']['sha'], 'server_stopped': report['server_stopped']}))


if __name__ == '__main__':
    main()
