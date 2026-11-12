"""Offline operator workflow. Never provide this role to the public runtime."""
import hashlib
import hmac
import json
import os
import stat
import fcntl
import tempfile
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import DatabaseError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from waitlist.models import AddressBudget, CollectionState, Erasure, Registration


def private_path(raw):
    if not raw:
        raise CommandError('An absolute private path is required.')
    path = Path(raw)
    if not path.is_absolute() or path.is_symlink() or path.resolve().is_relative_to(settings.BASE_DIR):
        raise CommandError('Use a private path outside the repository.')
    parent = path.parent.stat()
    if parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) & 0o077:
        raise CommandError('The private parent directory must be owned by you and mode 0700.')
    return path


def private_read(raw, max_bytes=1024 * 1024):
    path = private_path(raw)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'r') as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > max_bytes):
            raise CommandError('Input must be your mode-0600 bounded regular file.')
        return stream.read()


def address_key(email):
    return hmac.new(settings.SECRET_KEY.encode(), ('erasure:' + email).encode(), hashlib.sha256).hexdigest()


def ledger_erasure(raw, key, expires):
    path = private_path(raw)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise CommandError('Ledger must be your mode-0600 regular file.')
        stream.write(json.dumps({'key': key, 'expires_at': expires.isoformat()}, separators=(',', ':')) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def ledger_lock(raw):
    path = private_path(raw)
    fd = os.open(str(path) + '.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise CommandError('Ledger lock must be your private regular file.')
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield


def read_ledger(raw):
    entries = [json.loads(line) for line in private_read(raw).splitlines() if line]
    for entry in entries:
        expires = parse_datetime(entry.get('expires_at', ''))
        key = entry.get('key', '')
        if (len(key) != 64 or any(c not in '0123456789abcdef' for c in key)
            or expires is None or timezone.is_naive(expires)):
            raise CommandError('Invalid private recovery ledger.')
    return entries


def compact_ledger(raw, now):
    path = private_path(raw)
    entries = [entry for entry in read_ledger(raw) if parse_datetime(entry['expires_at']) > now]
    fd, temporary = tempfile.mkstemp(prefix='.erasure-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            for entry in entries:
                stream.write(json.dumps(entry, separators=(',', ':')) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Command(BaseCommand):
    help = 'Offline waitlist status, pause/resume, private JSON export, verified-request deletion and expiry/recovery cleanup.'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['status', 'pause', 'resume', 'export', 'delete', 'purge', 'reconcile'])
        parser.add_argument('--output')
        parser.add_argument('--email-file')
        parser.add_argument('--ledger')

    def handle(self, *args, **options):
        if not settings.WAITLIST_OPERATOR_MODE or settings.ON_VERCEL:
            raise CommandError('Offline operator mode is required; serving runtimes cannot run operator commands.')
        try:
            if options['action'] in {'delete', 'purge', 'reconcile'}:
                with ledger_lock(options['ledger']):
                    self.operate(options)
                    compact_ledger(options['ledger'], timezone.now())
            else:
                self.operate(options)
        except (OSError, ValueError, UnicodeError, DatabaseError, ValidationError):
            raise CommandError('Operation failed. Private values are not logged; inspect the private target before retrying.') from None

    def operate(self, options):
        action = options['action']
        now = timezone.now()
        if action == 'export':
            path = private_path(options['output'])
            # JSON avoids spreadsheet formula interpretation. Never send to stdout.
            with transaction.atomic():
                CollectionState.objects.select_for_update().get(pk=1)
                rows = list(Registration.objects.order_by('id').values('email', 'name', 'interest', 'privacy_version', 'created_at'))
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, 'w') as stream:
                    json.dump(rows, stream, default=str, ensure_ascii=False)
                    stream.flush()
                    os.fsync(stream.fileno())
            self.stdout.write('Private JSON export saved. It has the same retention and deletion obligations as the database.')
            return
        if action == 'delete':
            email = private_read(options['email_file'], 512).strip().casefold()
            validate_email(email)
            key = address_key(email)
            expires = now + timedelta(days=8)
            # Persist recovery suppression outside the database BEFORE deleting.
            ledger_erasure(options['ledger'], key, expires)
        if action == 'reconcile':
            entries = read_ledger(options['ledger'])
        if action == 'purge':
            # Refuse malformed/missing recovery data before database changes.
            read_ledger(options['ledger'])
        with transaction.atomic():
            state = CollectionState.objects.select_for_update().get(pk=1)
            if action == 'status':
                self.stdout.write(json.dumps({'paused': state.paused, 'environment_enabled': settings.WAITLIST_COLLECTION_ENABLED,
                    'retained': state.retained_count, 'capacity': settings.WAITLIST_CAPACITY}))
                return
            if action in {'pause', 'resume'}:
                if action == 'resume' and not settings.WAITLIST_COLLECTION_ENABLED:
                    raise CommandError('Environment collection switch is disabled.')
                state.paused = action == 'pause'
                state.save(update_fields=['paused'])
            elif action == 'delete':
                Erasure.objects.update_or_create(key=key, defaults={'expires_at': expires})
                Registration.objects.filter(email=email).delete()
            elif action in {'purge', 'reconcile'}:
                if action == 'reconcile':
                    if not state.paused:
                        raise CommandError('Recovery reconciliation requires collection paused.')
                    for entry in entries:
                        if parse_datetime(entry['expires_at']) > now:
                            Erasure.objects.update_or_create(key=entry['key'], defaults={'expires_at': parse_datetime(entry['expires_at'])})
                    keys = set(Erasure.objects.filter(expires_at__gt=now).values_list('key', flat=True))
                    for pk, address in Registration.objects.values_list('pk', 'email'):
                        if address_key(address) in keys:
                            Registration.objects.filter(pk=pk).delete()
                Registration.objects.filter(created_at__lte=now - timedelta(days=settings.WAITLIST_RETENTION_DAYS)).delete()
                AddressBudget.objects.filter(expires_at__lte=now).delete()
                Erasure.objects.filter(expires_at__lte=now).delete()
            if action in {'delete', 'purge', 'reconcile'}:
                state.retained_count = Registration.objects.count()
                state.save(update_fields=['retained_count'])
        self.stdout.write('Operation complete. No private values are printed.')
