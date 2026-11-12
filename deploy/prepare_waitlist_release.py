"""Create a public-only upload from a committed revision; no provider operations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


def prepare(revision, destination):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Use an exact full commit revision.')
    root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
    destination = Path(destination)
    if not destination.is_absolute() or destination.exists() or destination.resolve().is_relative_to(root):
        raise ValueError('Destination must be a new absolute directory outside the repository.')
    source_files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', revision], text=True).splitlines()
    mapping = {}
    fixed = {'manage.py', 'requirements.txt', 'config/__init__.py', 'config/settings.py',
             'config/database.py', 'config/waitlist_settings.py', 'config/waitlist_wsgi.py'}
    for name in source_files:
        if (name in fixed or name.startswith(('templates/waitlist/', 'static/waitlist/'))
            or (name.startswith('waitlist/') and not name.startswith(('waitlist/tests/', 'waitlist/management/')))):
            mapping[name] = name
    mapping['vercel.json'] = 'vercel.waitlist.json'
    mapping['pyproject.toml'] = 'deploy/waitlist-pyproject.toml'
    destination.mkdir(mode=0o700)
    receipt = {'revision': revision, 'files': {}}
    for output, source in sorted(mapping.items()):
        data = subprocess.check_output(['git', 'show', f'{revision}:{source}'])
        path = destination / output
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        receipt['files'][output] = {'source': source, 'sha256': hashlib.sha256(data).hexdigest()}
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--receipt', required=True)
    options = parser.parse_args()
    receipt_path = Path(options.receipt)
    fd = os.open(receipt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(prepare(options.revision, options.output), stream, indent=2)
    print('Public-only release prepared; no deployment or credentials.')
