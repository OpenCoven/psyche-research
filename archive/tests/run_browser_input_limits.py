"""Run the exact-source browser contract against a disposable synthetic database."""
import json
import hashlib
import os
from pathlib import Path
import socket
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main():
    with tempfile.TemporaryDirectory(prefix='psyche-browser-contract-') as temporary:
        scratch = Path(temporary)
        # Refuse inherited serving/provider configuration; all data is synthetic.
        for name in list(os.environ):
            if name.startswith(('DATABASE_', 'DJANGO_', 'WORKOS_', 'VERCEL', 'POSTGRES_')):
                os.environ.pop(name)
        os.environ.update(LOCAL_DEVELOPMENT='1', PILOT_APPROVED='0', AUTH_PROVIDER='local',
                          DATABASE_PATH=str(scratch / 'synthetic.sqlite3'), DJANGO_SETTINGS_MODULE='config.settings')
        import django
        django.setup()
        from django.contrib.auth import get_user_model
        from django.core.management import call_command
        from django.test import Client
        from archive import services
        from archive.models import Capacity, Submission, Version
        call_command('migrate', verbosity=0, interactive=False)
        author = get_user_model().objects.create_user('synthetic-browser-author')
        submission = services.create_submission(author)
        client = Client()
        client.force_login(author)
        with socket.socket() as available:
            available.bind(('127.0.0.1', 0))
            port = available.getsockname()[1]
        origin = f'http://127.0.0.1:{port}'
        # Only a fixed synthetic-image/measurement allowlist is uploaded by CI.
        # Session configuration, database and server logs stay in private scratch.
        review_directory = ROOT / 'var/browser-review'
        # Refuse stale bundles rather than mixing images from different executions.
        review_directory.mkdir(parents=True, mode=0o700, exist_ok=False)
        from archive.tests.browser_fonts import font_environment
        source = {
            'sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'tree': subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT, text=True).strip(),
            'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)),
            'font_environment': font_environment(),
            'files': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
                'static/archive/site.css', 'archive/tests/browser_input_limits.mjs',
                'archive/tests/browser_review.mjs', 'archive/tests/run_browser_input_limits.py',
                'archive/tests/browser_fonts.py',
                '.github/workflows/verify.yml')},
        }
        fixture = scratch / 'fixture.json'
        fixture.write_text(json.dumps({'origin': origin, 'editor': f'/workspace/{submission.pk}/',
            'review_directory': str(review_directory), 'source': source,
            'cookie': {'name': 'sessionid', 'value': client.cookies['sessionid'].value}}))
        fixture.chmod(0o600)
        with (scratch / 'server.log').open('w') as log:
            server = subprocess.Popen([sys.executable, 'manage.py', 'runserver', '--insecure', '--noreload',
                                       f'127.0.0.1:{port}'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            try:
                for _ in range(100):
                    if server.poll() is not None:
                        raise RuntimeError('Synthetic browser server exited before readiness')
                    try:
                        with urllib.request.urlopen(origin + '/health/', timeout=1) as response:
                            if response.status == 200:
                                break
                    except (urllib.error.URLError, TimeoutError):
                        time.sleep(0.1)
                else:
                    raise RuntimeError('Synthetic browser server did not become ready')
                node = subprocess.Popen(['node', str(ROOT / 'archive/tests/browser_input_limits.mjs'), str(fixture)],
                                        cwd=ROOT, start_new_session=True)
                try:
                    result = node.wait(timeout=90)
                    if result:
                        raise subprocess.CalledProcessError(result, 'native browser input contract')
                finally:
                    # The new session contains this probe's Node/Chromium processes only.
                    # On timeout, kill the whole group before removing its private scratch data.
                    try:
                        os.killpg(node.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        node.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        pass
                    try:
                        os.killpg(node.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    node.wait(timeout=5)
                submission.refresh_from_db()
                assert submission.revision == 2 and submission.state == Submission.State.DRAFT
                assert submission.title == 'SYNTHETIC-' + 'x' * 190
                assert submission.methods == '界' * 9998 + '\nX' and len(submission.artifacts) == 8000
                for name in ('title', 'byline', 'abstract', 'claims', 'limitations', 'provenance', 'ai_disclosure', 'change_note'):
                    assert len(getattr(submission, name)) == Submission._meta.get_field(name).max_length
                assert not Capacity.objects.get(pk=1).intake_open and not Version.objects.exists()
                report_path = review_directory / 'report.json'
                report = json.loads(report_path.read_text())
                report['server_verified'] = True
                report['server_postcondition'] = {'revision': 2, 'intake': 'paused', 'public_versions': 0}
                report_path.write_text(json.dumps(report, indent=2) + '\n')
                print(json.dumps({'server_revision': 2, 'all_field_limits_saved': True,
                    'stored_newlines': 'LF', 'intake': 'paused', 'public_versions': 0}))
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)


if __name__ == '__main__':
    main()
