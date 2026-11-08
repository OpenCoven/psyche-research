"""Start the reviewed local fixture with a sanitized parent libpq environment."""

import os
from pathlib import Path
import sys


FIXTURE = Path(__file__).with_name('rehearse_database_roles.py')
OS_VARIABLES = {'PATH', 'HOME', 'TMPDIR', 'LANG', 'USER', 'LOGNAME', 'TZ'}


def sanitized_environment(environment):
    clean = {key: value for key, value in environment.items()
             if key in OS_VARIABLES or key.startswith('LC_')}
    clean.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                 PGPASSFILE=os.devnull, PGSERVICEFILE=os.devnull)
    return clean


def main():
    # Isolated mode also excludes ambient Python paths/user packages in the fixture.
    os.execve(sys.executable, [sys.executable, '-I', '-B', str(FIXTURE), *sys.argv[1:]],
              sanitized_environment(os.environ))


if __name__ == '__main__':
    main()
