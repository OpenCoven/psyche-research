"""Parse only the supported PostgreSQL connection contract; never echo connection material."""
import os
from urllib.parse import urlsplit,parse_qs,unquote
from django.core.exceptions import ImproperlyConfigured

STATEMENT_TIMEOUT_MS=10000
LOCK_TIMEOUT_MS=5000
STARTUP_TIMEOUTS=f'-c statement_timeout={STATEMENT_TIMEOUT_MS} -c lock_timeout={LOCK_TIMEOUT_MS}'

# psycopg-binary wheels bundle OpenSSL with a private OPENSSLDIR, so libpq's
# sslrootcert=system can load no roots on Vercel. Prefer the runtime's OS bundle:
# Amazon Linux (Vercel), Debian/Ubuntu, then macOS/Alpine.
CA_BUNDLES=('/etc/pki/tls/certs/ca-bundle.crt','/etc/ssl/certs/ca-certificates.crt','/etc/ssl/cert.pem')

def root_certificates():
    """An explicit PGSSLROOTCERT wins; otherwise the first readable OS bundle, else libpq's system store."""
    explicit=os.environ.get('PGSSLROOTCERT','')
    if explicit:
        return explicit
    for path in CA_BUNDLES:
        if os.path.isfile(path) and os.access(path,os.R_OK):
            return path
    return 'system'

def pooled_host(hostname):
    """Neon selects its transaction pooler by a -pooler suffix on the endpoint label."""
    return hostname.split('.',1)[0].endswith('-pooler')

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
        options={'sslmode':mode,'connect_timeout':10,'prepare_threshold':None}
        if not pooled_host(parsed.hostname):
            # The pooler rejects the options startup parameter. Pooled sessions must
            # instead prove role-in-database defaults on connect (verify_session_timeouts).
            options['options']=STARTUP_TIMEOUTS
        if mode=='verify-full':
            options['sslrootcert']=root_certificates()
        return {'ENGINE':'django.db.backends.postgresql','NAME':unquote(parsed.path.lstrip('/')),
            'USER':unquote(parsed.username),'PASSWORD':unquote(parsed.password or ''),'HOST':parsed.hostname,
            'PORT':parsed.port or 5432,'CONN_MAX_AGE':0,'OPTIONS':options}
    except (ValueError,UnicodeError):
        raise ImproperlyConfigured('DATABASE_URL must be a PostgreSQL URL with a database, user, host and only an approved sslmode query; production requires verify-full. Connection material is not logged.') from None

def timeouts_pinned_at_startup(options):
    """True only when the startup options' final values are exactly the reviewed timeouts."""
    tokens=str(options.get('options','')).split()
    pinned={}
    for flag,value in zip(tokens,tokens[1:]):
        if flag=='-c':
            name,_,setting=value.partition('=')
            pinned[name]=setting
    return (pinned.get('statement_timeout')==str(STATEMENT_TIMEOUT_MS)
            and pinned.get('lock_timeout')==str(LOCK_TIMEOUT_MS))

SESSION_TIMEOUTS_SQL="SELECT name,setting,unit,source FROM pg_settings WHERE name IN ('statement_timeout','lock_timeout')"

def session_timeouts_within_bounds(rows):
    """Both timeouts must come from a role-in-database default and be non-zero within bounds."""
    found={row[0]:row[1:] for row in rows}
    for name,bound in (('statement_timeout',STATEMENT_TIMEOUT_MS),('lock_timeout',LOCK_TIMEOUT_MS)):
        setting,unit,source=found.get(name,(None,None,None))
        if unit!='ms' or source!='database user' or not str(setting).isdigit() or not 0<int(setting)<=bound:
            return False
    return True

def verify_session_timeouts(sender,connection,**kwargs):
    """connection_created receiver. Under transaction pooling a session SET is unreliable,
    so a session whose startup packet did not pin the timeouts must already carry them."""
    if connection.vendor!='postgresql' or timeouts_pinned_at_startup(connection.settings_dict.get('OPTIONS') or {}):
        return
    from django.db import OperationalError
    try:
        with connection.cursor() as cursor:
            cursor.execute(SESSION_TIMEOUTS_SQL)
            rows=cursor.fetchall()
        if not session_timeouts_within_bounds(rows):
            raise OperationalError('PostgreSQL session timeouts are unverified: pooled connections require the runtime role-in-database statement_timeout and lock_timeout defaults in docs/DATABASE_ROLES.md. Connection material is not logged.')
    except BaseException:
        # Never leave an unverified session open for a caller that catches the error.
        connection.close()
        raise
