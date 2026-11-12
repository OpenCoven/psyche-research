"""Isolated public deployment. Never use the archive's tables or credentials."""
from .settings import *  # Reuse secret, TLS, debug, host and PostgreSQL guards.
from django.core.validators import validate_email

if PILOT_APPROVED:
    raise ImproperlyConfigured('The public waitlist requires PILOT_APPROVED=0.')
if AUTH_PROVIDER != 'local' or WORKOS_API_KEY or WORKOS_COOKIE_PASSWORD:
    raise ImproperlyConfigured('The public waitlist must not receive WorkOS credentials.')
INSTALLED_APPS = ['django.contrib.contenttypes', 'django.contrib.staticfiles', 'waitlist.apps.WaitlistConfig']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'waitlist.middleware.PublicBoundary',
              'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
              'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'waitlist.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates',
              'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
              'OPTIONS': {'context_processors': ['django.template.context_processors.request']}}]
DATA_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 8
WAITLIST_COLLECTION_ENABLED = os.environ.get('WAITLIST_COLLECTION_ENABLED') == '1'
WAITLIST_OPERATOR = os.environ.get('WAITLIST_OPERATOR', '')
WAITLIST_CONTACT = os.environ.get('WAITLIST_CONTACT', '')
WAITLIST_PRIVACY_VERSION = '2026-11-11'
WAITLIST_CAPACITY = 1000
WAITLIST_RETENTION_DAYS = 90
WAITLIST_OPERATOR_MODE = os.environ.get('WAITLIST_OPERATOR_MODE') == '1'
if not LOCAL_DEVELOPMENT:
    try:
        validate_email(WAITLIST_CONTACT)
        db = DATABASES['default']
        if (not WAITLIST_OPERATOR.strip() or db['ENGINE'] != 'django.db.backends.postgresql'
            or db['NAME'] != 'psyche_waitlist_20261111'
            or db['USER'] not in {'psyche_waitlist_runtime', 'psyche_waitlist_operator', 'psyche_waitlist_migrator'}
            or (ON_VERCEL and (db['USER'] != 'psyche_waitlist_runtime' or WAITLIST_OPERATOR_MODE))):
            raise ValueError()
    except Exception:
        raise ImproperlyConfigured('Public waitlist requires an adopted operator/contact and isolated PostgreSQL database and purpose role. Values are not logged.') from None
LOGGING['loggers']['waitlist'] = {'handlers': ['null'], 'propagate': False}

