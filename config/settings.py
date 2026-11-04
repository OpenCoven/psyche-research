"""Fail-closed Django settings. Vercel requires managed PostgreSQL; SQLite is a local option."""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_DEVELOPMENT = os.environ.get('LOCAL_DEVELOPMENT') == '1'
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if LOCAL_DEVELOPMENT and not SECRET_KEY:
    SECRET_KEY = 'local-development-only-never-a-deployment-key-coven-research'
if len(SECRET_KEY) < 50 or (not LOCAL_DEVELOPMENT and SECRET_KEY.startswith('local-development-only-')):
    raise ImproperlyConfigured('Set DJANGO_SECRET_KEY to a random secret of at least 50 characters.')
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') if h.strip()]
if LOCAL_DEVELOPMENT:
    ALLOWED_HOSTS = ALLOWED_HOSTS or ['localhost', '127.0.0.1', '[::1]', 'testserver']
if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured('Set explicit DJANGO_ALLOWED_HOSTS; wildcard hosts are forbidden.')
PILOT_APPROVED = os.environ.get('PILOT_APPROVED') == '1'
DATABASE_PATH = Path(os.environ.get('DATABASE_PATH', BASE_DIR / 'var' / 'archive.sqlite3')).resolve()
DATABASE_URL=os.environ.get('DATABASE_URL','')
ON_VERCEL=os.environ.get('VERCEL')=='1'
if ON_VERCEL and (LOCAL_DEVELOPMENT or not DATABASE_URL):
    raise ImproperlyConfigured('Vercel requires production settings and persistent PostgreSQL DATABASE_URL; local SQLite is not a hosted database.')
if DATABASE_URL:
    from .database import postgres_config
    DATABASES={'default':postgres_config(DATABASE_URL,local=LOCAL_DEVELOPMENT)}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': DATABASE_PATH,
        'OPTIONS': {'timeout': 15, 'transaction_mode': 'IMMEDIATE'}}}
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.messages', 'django.contrib.staticfiles', 'archive']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'archive.middleware.BoundaryMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'archive.middleware.WriteLimitMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages',
    'archive.context_processors.roles']}}]
WSGI_APPLICATION = 'config.wsgi.application'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_SECURE = not LOCAL_DEVELOPMENT
CSRF_COOKIE_SECURE = not LOCAL_DEVELOPMENT
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SECURE_SSL_REDIRECT = not LOCAL_DEVELOPMENT
SECURE_HSTS_SECONDS = 31536000 if not LOCAL_DEVELOPMENT else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'no-referrer'
X_FRAME_OPTIONS = 'DENY'
# TLS terminates in WSGI or a separately reviewed trusted proxy. Never trust forwarded headers by default.
DATA_UPLOAD_MAX_MEMORY_SIZE = 96 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 40
FILE_UPLOAD_MAX_MEMORY_SIZE = 0
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
# No body/query/error traceback is logged by the application in production.
LOGGING = {'version': 1, 'disable_existing_loggers': False,
    'handlers': {'null': {'class': 'logging.NullHandler'}, 'safe_stream': {'class': 'logging.StreamHandler'}},
    'loggers': {'archive.telemetry': {'handlers': ['safe_stream'], 'level': 'INFO', 'propagate': False},
                'django.request': {'handlers': ['null'], 'propagate': False},
                'django.security': {'handlers': ['null'], 'propagate': False}}}
