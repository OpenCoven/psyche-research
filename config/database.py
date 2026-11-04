"""Parse only the supported PostgreSQL connection contract; never echo connection material."""
import os
from urllib.parse import urlsplit,parse_qs,unquote
from django.core.exceptions import ImproperlyConfigured

def postgres_config(url,local=False):
    try:
        parsed=urlsplit(url)
        query=parse_qs(parsed.query,keep_blank_values=True,strict_parsing=True)
        if (parsed.scheme not in ['postgres','postgresql'] or not parsed.hostname or not parsed.username or
            not parsed.path.strip('/') or parsed.fragment or set(query)-{'sslmode'} or
            any(len(value)!=1 for value in query.values())):
            raise ValueError()
        mode=query.get('sslmode',['verify-full'])[0]
        if mode not in (['disable','require','verify-full'] if local else ['verify-full']):
            raise ValueError()
        options={'sslmode':mode,'connect_timeout':10,'options':'-c statement_timeout=10000 -c lock_timeout=5000',
                 'prepare_threshold':None}
        if mode=='verify-full':
            options['sslrootcert']=os.environ.get('PGSSLROOTCERT','system')
        return {'ENGINE':'django.db.backends.postgresql','NAME':unquote(parsed.path.lstrip('/')),
            'USER':unquote(parsed.username),'PASSWORD':unquote(parsed.password or ''),'HOST':parsed.hostname,
            'PORT':parsed.port or 5432,'CONN_MAX_AGE':0,'OPTIONS':options}
    except (ValueError,UnicodeError):
        raise ImproperlyConfigured('DATABASE_URL must be a PostgreSQL URL with a database, user, host and only an approved sslmode query; production requires verify-full. Connection material is not logged.') from None
