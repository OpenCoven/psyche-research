"""AuthKit authentication composed with local ownership and human moderator authority."""
import base64
import hashlib
import secrets
import time
from datetime import timedelta
from functools import lru_cache
from urllib.parse import urlsplit

import jwt
from django.conf import settings
from django.contrib.auth import login, logout, views as django_auth
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from workos import WorkOSClient
from workos.session import seal_session_from_auth_response, unseal_data

from .models import Capacity, WorkOSIdentity, WorkOSLoginAttempt

SESSION_DATA = 'workos_session'
SESSION_SUBJECT = 'workos_subject'
SESSION_ID = 'workos_session_id'
SESSION_STARTED = 'workos_session_started'
BROWSER_NONCE = 'workos_browser_nonce'


class InvalidLogin(Exception):
    pass


def client():
    # Do not let an ambient SDK base-URL override receive authentication material.
    return WorkOSClient(api_key=settings.WORKOS_API_KEY, client_id=settings.WORKOS_CLIENT_ID,
                        base_url='https://api.workos.com/', request_timeout=5,
                        jwt_issuer=settings.WORKOS_ISSUER, max_retries=0)


@lru_cache(maxsize=8)
def jwks(client_id):
    return jwt.PyJWKClient(f'https://api.workos.com/sso/jwks/{client_id}', timeout=5,
                           lifespan=300, cache_keys=False)


def token_claims(token, *, allow_expired=False):
    if not isinstance(token, str) or len(token) > 32768:
        raise InvalidLogin()
    try:
        key = jwks(settings.WORKOS_CLIENT_ID).get_signing_key_from_jwt(token)
    except jwt.PyJWKClientConnectionError:
        raise
    except jwt.PyJWKClientError:
        raise InvalidLogin() from None
    claims = jwt.decode(token, key.key, algorithms=['RS256'], issuer=settings.WORKOS_ISSUER,
                        options={'require': ['exp', 'iat', 'iss', 'sub', 'sid', 'client_id'],
                                 'verify_aud': False, 'verify_exp': not allow_expired})
    if (claims['client_id'] != settings.WORKOS_CLIENT_ID or claims.get('act')
        or not isinstance(claims['sub'], str) or not claims['sub'].startswith('user_')
        or not isinstance(claims['sid'], str) or not claims['sid'].startswith('session_')):
        raise InvalidLogin()
    # First-party session tokens normally omit aud. Bind an explicit audience too.
    audience = claims.get('aud')
    if audience is not None and audience != settings.WORKOS_CLIENT_ID and audience != [settings.WORKOS_CLIENT_ID]:
        raise InvalidLogin()
    return claims


def seal(response):
    if response.impersonator or not response.user.email_verified:
        raise InvalidLogin()
    claims = token_claims(response.access_token)
    if claims['sub'] != response.user.id:
        raise InvalidLogin()
    sealed = seal_session_from_auth_response(
        access_token=response.access_token, refresh_token=response.refresh_token,
        user={'id': response.user.id, 'email_verified': True},
        cookie_password=settings.WORKOS_COOKIE_PASSWORD)
    return sealed, claims


def check_session(sealed):
    try:
        data = unseal_data(sealed, settings.WORKOS_COOKIE_PASSWORD)
    except Exception:
        raise InvalidLogin() from None
    try:
        claims = token_claims(data['access_token'])
    except jwt.ExpiredSignatureError:
        token_claims(data['access_token'], allow_expired=True)
        session = client().user_management.load_sealed_session(
            session_data=sealed, cookie_password=settings.WORKOS_COOKIE_PASSWORD)
        session.jwks = jwks(settings.WORKOS_CLIENT_ID)
        result = session.refresh()
        if not result.authenticated:
            raise InvalidLogin()
        data = unseal_data(result.sealed_session, settings.WORKOS_COOKIE_PASSWORD)
        claims = token_claims(data['access_token'])
        # Keep provider profile/contact fields out of the persisted session.
        sealed = seal_session_from_auth_response(
            access_token=data['access_token'], refresh_token=data['refresh_token'],
            user={'id': (data.get('user') or {}).get('id'),
                  'email_verified': (data.get('user') or {}).get('email_verified')},
            impersonator=data.get('impersonator'), cookie_password=settings.WORKOS_COOKIE_PASSWORD)
    user = data.get('user') or {}
    if data.get('impersonator') or user.get('id') != claims['sub'] or user.get('email_verified') is not True:
        raise InvalidLogin()
    return sealed, claims


def safe_next(value):
    if not isinstance(value, str) or len(value) > 2048 or '\\' in value or any(ord(c) < 32 for c in value):
        return '/workspace/'
    if not value.startswith('/') or value.startswith('//'):
        return '/workspace/'
    try:
        parsed = urlsplit(value)
    except ValueError:
        return '/workspace/'
    if parsed.scheme or parsed.netloc:
        return '/workspace/'
    return value


def unavailable():
    response = HttpResponse('Sign-in is temporarily unavailable. Retry shortly; your saved work is unchanged.', status=503)
    response['Retry-After'] = '30'
    return response


def login_view(request):
    if settings.AUTH_PROVIDER != 'workos':
        return django_auth.LoginView.as_view()(request)
    if request.method != 'GET':
        return HttpResponse(status=405, headers={'Allow': 'GET'})
    return render(request, 'registration/workos_login.html', {'next': safe_next(request.GET.get('next', '/workspace/'))})


@require_POST
def start(request):
    return begin_login(request, request.POST.get('next', '/workspace/'))


@require_GET
def initiate(request):
    """AuthKit's externally initiated flow must redirect without another button click."""
    return begin_login(request, request.GET.get('next', '/workspace/'))


def begin_login(request, next_path):
    if settings.AUTH_PROVIDER != 'workos':
        raise Http404()
    if request.user.is_authenticated:
        return redirect('dashboard')
    nonce = request.session.get(BROWSER_NONCE) or secrets.token_urlsafe(32)
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    browser_hash = hashlib.sha256(nonce.encode()).hexdigest()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    with transaction.atomic():
        Capacity.objects.select_for_update().get(pk=1)
        WorkOSLoginAttempt.objects.filter(browser_hash=browser_hash).delete()
        WorkOSLoginAttempt.objects.filter(expires_at__lt=timezone.now()).delete()
        if WorkOSLoginAttempt.objects.count() >= 1000:
            return HttpResponse('Sign-in is busy. Retry in five minutes.', status=429, headers={'Retry-After': '300'})
        WorkOSLoginAttempt.objects.create(state_hash=hashlib.sha256(state.encode()).hexdigest(),
            browser_hash=browser_hash, verifier=verifier, next_path=safe_next(next_path),
            expires_at=timezone.now() + timedelta(minutes=5))
    request.session[BROWSER_NONCE] = nonce
    request.session.cycle_key()
    try:
        url = client().user_management.get_authorization_url(provider='authkit',
            redirect_uri=settings.WORKOS_REDIRECT_URI, state=state,
            code_challenge_method='S256', code_challenge=challenge, screen_hint='sign-in')
    except Exception:
        return unavailable()
    return redirect(url)


@require_GET
def callback(request):
    if settings.AUTH_PROVIDER != 'workos':
        raise Http404()
    state, code = request.GET.get('state', ''), request.GET.get('code', '')
    nonce = request.session.get(BROWSER_NONCE, '')
    if (len(request.GET.getlist('state')) != 1 or len(request.GET.getlist('code')) != 1
        or not state or len(state) > 256 or not code or len(code) > 4096 or not nonce or request.GET.get('error')):
        return HttpResponse('Sign-in could not be completed. Start again from the sign-in page.', status=400)
    with transaction.atomic():
        attempt = WorkOSLoginAttempt.objects.select_for_update().filter(
            state_hash=hashlib.sha256(state.encode()).hexdigest(),
            browser_hash=hashlib.sha256(nonce.encode()).hexdigest(), expires_at__gt=timezone.now()).first()
        if not attempt:
            return HttpResponse('Sign-in could not be completed. Start again from the sign-in page.', status=400)
        verifier, next_path = attempt.verifier, attempt.next_path
        attempt.delete()
    try:
        response = client().user_management.authenticate_with_code(
            code=code, code_verifier=verifier, request_options={'timeout': 5, 'max_retries': 0})
        sealed, claims = seal(response)
    except Exception:
        return unavailable()
    identity = WorkOSIdentity.objects.select_related('user').filter(
        client_id=settings.WORKOS_CLIENT_ID, subject=claims['sub'], enabled=True, user__is_active=True).first()
    if not identity:
        return HttpResponse('This sign-in is not linked to an active pilot account. Contact your operator through your established channel.', status=403)
    login(request, identity.user, backend='django.contrib.auth.backends.ModelBackend')
    request.session[SESSION_DATA] = sealed
    request.session[SESSION_SUBJECT] = claims['sub']
    request.session[SESSION_ID] = claims['sid']
    request.session[SESSION_STARTED] = time.time()
    request.session.pop(BROWSER_NONCE, None)
    return redirect(safe_next(next_path))


@require_POST
def logout_view(request):
    if settings.AUTH_PROVIDER != 'workos':
        return django_auth.LogoutView.as_view()(request)
    session_id = request.session.get(SESSION_ID)
    logout(request)
    if isinstance(session_id, str) and session_id.startswith('session_'):
        return redirect(client().user_management.get_logout_url(session_id=session_id))
    return redirect('home')


def password_change(request):
    if settings.AUTH_PROVIDER == 'workos':
        raise Http404()
    return django_auth.PasswordChangeView.as_view(success_url='/accounts/password/done/')(request)


def password_change_done(request):
    if settings.AUTH_PROVIDER == 'workos':
        raise Http404()
    return django_auth.PasswordChangeDoneView.as_view()(request)


class WorkOSSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.AUTH_PROVIDER == 'workos' and not request.user.is_authenticated and request.session.get('_auth_user_id'):
            # A deactivated local account must not regain an old session on reactivation.
            logout(request)
        if settings.AUTH_PROVIDER == 'workos' and request.user.is_authenticated and request.path != '/accounts/logout/':
            started = request.session.get(SESSION_STARTED)
            bound = WorkOSIdentity.objects.filter(user=request.user, client_id=settings.WORKOS_CLIENT_ID,
                subject=request.session.get(SESSION_SUBJECT, ''), enabled=True).exists()
            if not bound or not isinstance(started, (int, float)) or time.time() - started > settings.SESSION_COOKIE_AGE:
                logout(request)
            else:
                try:
                    sealed, claims = check_session(request.session.get(SESSION_DATA, ''))
                    if claims['sub'] != request.session.get(SESSION_SUBJECT):
                        raise InvalidLogin()
                    if sealed != request.session.get(SESSION_DATA):
                        request.session[SESSION_DATA] = sealed
                    request.session[SESSION_ID] = claims['sid']
                except (InvalidLogin, jwt.InvalidTokenError, ValueError, KeyError, TypeError):
                    logout(request)
                except Exception:
                    return unavailable()
        return self.get_response(request)
