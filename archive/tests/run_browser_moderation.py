"""Exercise human moderation in native Chromium against disposable synthetic data."""
import argparse
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
sys.path.insert(0, str(ROOT))


def prepare(scratch, review):
    # Settings must be isolated before importing Django or any application module.
    assert 'django.conf' not in sys.modules, 'Run this fixture in its own interpreter'
    for name in list(os.environ):
        if name.startswith(('DATABASE_', 'DJANGO_', 'WORKOS_', 'VERCEL', 'POSTGRES_')):
            os.environ.pop(name)
    os.environ.update(LOCAL_DEVELOPMENT='1', PILOT_APPROVED='0', AUTH_PROVIDER='local',
                      DATABASE_PATH=str(scratch / 'synthetic.sqlite3'), DJANGO_SETTINGS_MODULE='config.settings')
    import django
    django.setup()
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from django.core.management import call_command
    from django.test import Client
    from archive import services
    from archive.models import Capacity, Submission
    call_command('migrate', verbosity=0, interactive=False)
    assert not Capacity.objects.get(pk=1).intake_open
    actors = {name: get_user_model().objects.create_user('synthetic-browser-' + name)
              for name in ('author', 'other', 'moderator', 'self')}
    group, _ = Group.objects.get_or_create(name='moderators')
    for name in ('moderator', 'self'):
        actors[name].groups.add(group)
    for name in ('other', 'self'):
        actors[name].is_staff = actors[name].is_superuser = True
        actors[name].save()
    config = Capacity.objects.get(pk=1)
    services.configure(actors['moderator'], {'intake_open': True}, config.revision,
                       'SYNTHETIC isolated fixture setup only')
    content = dict(title='SYNTHETIC moderation workflow fixture', byline='Synthetic Contributor', kind='report',
                   abstract='SYNTHETIC test only; no research claim.', methods='SYNTHETIC inert procedure.',
                   claims='SYNTHETIC initial frozen claims.', limitations='SYNTHETIC fixture only.',
                   artifacts='', provenance='SYNTHETIC generated test data.', license='CC0-1.0',
                   ai_disclosure='SYNTHETIC automated fixture; no scientific review.', change_note='',
                   rights_confirmed=True, privacy_confirmed=True)
    rows = {}
    for name in ('author', 'other', 'self'):
        row = services.create_submission(actors[name])
        services.save_submission(actors[name], row.pk,
            {**content, 'title': content['title'] + ' ' + name}, row.revision, submit=True)
        row.refresh_from_db()
        rows[name] = row
    draft = services.create_submission(actors['author'])
    config.refresh_from_db()
    services.configure(actors['moderator'], {'intake_open': False}, config.revision,
                       'SYNTHETIC fixture prepared; intake paused')
    cookies = {}
    for name, actor in actors.items():
        client = Client()
        client.force_login(actor)
        cookies[name] = client.cookies['sessionid'].value
    with socket.socket() as available:
        available.bind(('127.0.0.1', 0))
        port = available.getsockname()[1]
    files = ['archive/tests/run_browser_moderation.py', 'archive/tests/browser_moderation.mjs',
             'archive/tests/browser_review.mjs', 'archive/views.py', 'archive/services.py',
             'archive/forms.py', 'archive/models.py', 'static/archive/site.css', '.github/workflows/verify.yml']
    files += sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'templates').rglob('*.html'))
    fixture = {'origin': f'http://127.0.0.1:{port}', 'cookies': cookies,
               'submissions': {name: str(row.pk) for name, row in rows.items()}, 'draft': str(draft.pk),
               'review_directory': str(review), 'source': {
                   'sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                   'tree': subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT, text=True).strip(),
                   'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)),
                   'files': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}}
    return fixture, actors, rows, draft


def verify(actors, rows, draft):
    from archive import services
    from archive.models import Appeal, Capacity, Decision, Event, Submission, Version
    row = rows['author']
    expected = {**row.payload(), 'claims': 'SYNTHETIC final frozen claims after appeal.'}
    row.refresh_from_db()
    decisions = list(Decision.objects.filter(submission=row).order_by('created_at', 'pk'))
    assert [(d.action, d.revision) for d in decisions] == [('changes', 1), ('decline', 4), ('publish', 7)]
    assert all(d.actor == actors['moderator'] and d.created_at and d.conflicts == 'None; SYNTHETIC fixture'
               and d.reason == 'SYNTHETIC PRIVATE ' + d.action for d in decisions)
    assert row.state == Submission.State.PUBLISHED and row.revision == 8
    version = Version.objects.get(submission=row)
    assert Version.objects.count() == 1
    assert version.snapshot == row.payload() == row.frozen_snapshot == expected
    assert version.snapshot['claims'] == 'SYNTHETIC final frozen claims after appeal.'
    assert version.digest == row.digest == decisions[-1].digest == services.digest(version.snapshot)
    assert len({d.digest for d in decisions}) == 3
    appeal = Appeal.objects.get(submission=row)
    assert appeal.decision == decisions[1] and appeal.author == actors['author']
    assert appeal.reason == 'SYNTHETIC PRIVATE appeal' and appeal.response == 'SYNTHETIC PRIVATE response'
    assert appeal.resolved_by == actors['moderator'] and appeal.created_at and appeal.resolved_at
    for name in ('other', 'self'):
        rows[name].refresh_from_db()
        assert rows[name].state == Submission.State.SUBMITTED and rows[name].revision == 1
        assert not Decision.objects.filter(submission=rows[name]).exists()
    draft.refresh_from_db()
    assert draft.state == Submission.State.DRAFT and draft.revision == 1
    assert draft.title == 'SYNTHETIC saved while paused' and not draft.abstract
    config = Capacity.objects.get(pk=1)
    assert not config.intake_open and config.queue_limit == 3
    assert Submission.objects.filter(state=Submission.State.SUBMITTED).count() == 2
    for decision in decisions:
        audit = Event.objects.get(kind='moderation_' + decision.action, target=str(row.pk))
        assert audit.actor == actors['moderator']
        assert audit.details == {'digest': decision.digest, 'revision': decision.revision}
    return {'decisions': 3, 'appeals_resolved': 1, 'exact_public_versions': 1,
            'published_revision': 8, 'paused_draft_revision': 1, 'intake': 'paused',
            'remaining_queue': 2, 'queue_limit': 3, 'self_and_unrelated_decisions': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true', help='Verify isolated setup only; no browser claim')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='psyche-moderation-contract-') as temporary:
        scratch = Path(temporary)
        review = ROOT / 'var/moderation-browser-review'
        fixture, actors, rows, draft = prepare(scratch, review)
        if args.prepare_only:
            from archive.models import Capacity, Submission, Version
            assert Submission.objects.count() == 4 and not Version.objects.exists()
            assert not Capacity.objects.get(pk=1).intake_open
            print(json.dumps({'fixture_preparation': 'passed', 'submissions': 4,
                              'intake': 'paused', 'browser_checks': 'unrun'}))
            return
        review.mkdir(parents=True, mode=0o700, exist_ok=False)
        config = scratch / 'fixture.json'
        config.write_text(json.dumps(fixture))
        config.chmod(0o600)
        port = fixture['origin'].rsplit(':', 1)[1]
        with (scratch / 'server.log').open('w') as log:
            server = subprocess.Popen([sys.executable, 'manage.py', 'runserver', '--insecure', '--noreload',
                                       f'127.0.0.1:{port}'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            try:
                for _ in range(100):
                    if server.poll() is not None:
                        raise RuntimeError('Synthetic server exited before readiness')
                    try:
                        with urllib.request.urlopen(fixture['origin'] + '/health/', timeout=1) as response:
                            if response.status == 200:
                                break
                    except (urllib.error.URLError, TimeoutError):
                        time.sleep(0.1)
                else:
                    raise RuntimeError('Synthetic server did not become ready')
                node = subprocess.Popen(['node', str(ROOT / 'archive/tests/browser_moderation.mjs'), str(config)],
                                        cwd=ROOT, start_new_session=True)
                try:
                    result = node.wait(timeout=180)
                    if result:
                        raise subprocess.CalledProcessError(result, 'native moderation contract')
                finally:
                    for sig in (signal.SIGTERM, signal.SIGKILL):
                        try:
                            os.killpg(node.pid, sig)
                        except ProcessLookupError:
                            pass
                        try:
                            node.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            pass
                    node.wait(timeout=5)
                postcondition = verify(actors, rows, draft)
                report_path = review / 'report.json'
                report = json.loads(report_path.read_text())
                report.update(server_verified=True, server_postcondition=postcondition)
                report_path.write_text(json.dumps(report, indent=2) + '\n')
                print(json.dumps({'server_postcondition': postcondition}))
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)


if __name__ == '__main__':
    main()
