"""Bounded consistent SQLite snapshots. Restores never replace a live file or follow a leaf symlink."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
from django.apps import apps
from django.db.migrations.loader import MigrationLoader

MAX_SNAPSHOT_BYTES=64 * 1024 * 1024
REQUIRED_TRIGGERS={f'archive_{table}_no_{action}' for table in ('version','decision','event') for action in ('update','delete')}

def verify(connection):
    size=connection.execute('PRAGMA page_count').fetchone()[0]*connection.execute('PRAGMA page_size').fetchone()[0]
    if size>MAX_SNAPSHOT_BYTES:
        raise ValueError('Database exceeds the 64 MiB pilot recovery bound; use a separately reviewed recovery plan.')
    if connection.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:
        raise ValueError('Database integrity check failed.')
    if connection.execute('PRAGMA foreign_key_check').fetchall():
        raise ValueError('Database foreign-key check failed.')
    tables={x[0] for x in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'django_migrations' not in tables:
        raise ValueError('Migration history is missing.')
    for model in apps.get_models(include_auto_created=True):
        if model._meta.managed:
            name=model._meta.db_table
            if name not in tables:
                raise ValueError('Required application table is missing: '+name)
            columns={x[1] for x in connection.execute('PRAGMA table_info("'+name+'")')}
            if not {field.column for field in model._meta.local_concrete_fields}<=columns:
                raise ValueError('Required application columns are missing: '+name)
    required=set(MigrationLoader(None).graph.leaf_nodes())
    applied=set(connection.execute('SELECT app,name FROM django_migrations'))
    if not required<=applied:
        raise ValueError('Backup schema is not at the current migration version.')
    triggers=dict(connection.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger'"))
    if not REQUIRED_TRIGGERS<=triggers.keys():
        raise ValueError('Publication/audit immutability triggers are missing.')
    for name in REQUIRED_TRIGGERS:
        action=name.rsplit('_',1)[1]
        table=name.rsplit('_no_',1)[0]
        sql=' '.join(triggers[name].lower().split())
        expected=f"create trigger {name} before {action} on {table} begin select raise(abort, 'append-only record'); end"
        if sql.rstrip(';')!=expected:
            raise ValueError('Publication/audit trigger definition does not match the contract.')
    if connection.execute('SELECT count(*) FROM archive_capacity WHERE id=1').fetchone()[0]!=1:
        raise ValueError('Capacity singleton is missing.')
    for encoded,expected in connection.execute('SELECT snapshot,digest FROM archive_version'):
        snapshot=json.loads(encoded)
        actual=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        if actual!=expected:
            raise ValueError('Published content digest mismatch.')

def copy_database(source,destination,restore=False):
    source=Path(source).resolve(strict=True)
    # Preserve the final component so O_EXCL rejects even a dangling destination symlink.
    requested=Path(os.path.abspath(destination))
    parent=requested.parent.resolve(strict=True)
    if source==parent/requested.name:
        raise ValueError('Source and destination must differ.')
    parent_fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    created=None
    try:
        info=os.fstat(parent_fd)
        if info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)&0o077:
            raise ValueError('Destination directory must be owned by this operator and mode 0700.')
        try:
            os.stat(requested.name,dir_fd=parent_fd,follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError('Destination already exists, including symlinks.')
        # Build a bounded consistent snapshot in memory; SQLite never opens the destination path.
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as origin, sqlite3.connect(':memory:') as target:
            verify(origin)
            origin.backup(target)
            verify(target)
            if restore:
                target.execute('DELETE FROM archive_workoscredential')
                target.execute('DELETE FROM django_session')
                target.execute('DELETE FROM archive_ratebucket')
                target.execute('DELETE FROM archive_workosloginattempt')
                target.execute('UPDATE archive_capacity SET intake_open=0,revision=revision+1 WHERE id=1')
                target.execute("INSERT INTO archive_event (kind,target,details,created_at,actor_id) VALUES ('restored_paused','capacity','{}',strftime('%Y-%m-%d %H:%M:%f','now'),NULL)")
                target.commit()
                verify(target)
            payload=target.serialize()
            if len(payload)>MAX_SNAPSHOT_BYTES:
                raise ValueError('Snapshot exceeds pilot recovery bound.')
        fd=os.open(requested.name,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600,dir_fd=parent_fd)
        created=os.fstat(fd)
        with os.fdopen(fd,'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        current=os.stat(requested.name,dir_fd=parent_fd,follow_symlinks=False)
        if (current.st_dev,current.st_ino)!=(created.st_dev,created.st_ino):
            raise ValueError('Destination changed during snapshot creation.')
        os.fsync(parent_fd)
        return hashlib.sha256(payload).hexdigest()
    except Exception:
        if created:
            try:
                current=os.stat(requested.name,dir_fd=parent_fd,follow_symlinks=False)
                if (current.st_dev,current.st_ino)==(created.st_dev,created.st_ino):
                    os.unlink(requested.name,dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        raise
    finally:
        os.close(parent_fd)
