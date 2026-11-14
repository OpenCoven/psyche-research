"""Public release entrypoint: refuse any archive settings override."""
import os
os.umask(0o077)
if os.environ.get('DJANGO_SETTINGS_MODULE', 'config.waitlist_settings') != 'config.waitlist_settings':
    raise RuntimeError('Public waitlist requires its isolated settings profile.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.waitlist_settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
