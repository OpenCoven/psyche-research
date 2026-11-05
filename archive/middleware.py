import hashlib
import hmac
import time
import json
import logging
import uuid
from datetime import timedelta
from django.conf import settings
from django.db import transaction, OperationalError
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.core.exceptions import RequestDataTooBig, TooManyFieldsSent
from django.utils import timezone
from .models import RateBucket


class WorkOSDatabaseSessionMiddleware(SessionMiddleware):
    """Serialize session loading, token rotation and response saving across workers."""

    def __call__(self, request):
        key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, '')
        if settings.AUTH_PROVIDER != 'workos' or not key or len(key) > 40:
            return super().__call__(request)
        try:
            with transaction.atomic():
                # Lock before SessionMiddleware loads its cache. Keep the lock until
                # process_response saves, so an older response cannot restore old tokens.
                Session.objects.select_for_update().filter(session_key=key).first()
                return super().__call__(request)
        except OperationalError:
            return HttpResponse('Sign-in is temporarily busy. Retry shortly; reload to confirm whether your change was saved.',
                                status=503, headers={'Retry-After': '5'})

class BoundaryMiddleware:
    def __init__(self,get_response):
        self.get_response=get_response
    def process_exception(self,request,exception):
        if isinstance(exception,OperationalError):
            result=HttpResponse('Intake is busy. Retry shortly; reload to confirm whether your change was saved.',status=503)
            result['Retry-After']='5'
            return result
        return None
    def __call__(self,request):
        started=time.monotonic()
        request_id=uuid.uuid4().hex
        response=None
        if request.method in ['POST','PUT','PATCH']:
            try:
                size=int(request.META.get('CONTENT_LENGTH') or 0)
            except ValueError:
                size=-1
            if size < 0 or size > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
                response=HttpResponse('Request body exceeds the intake limit.',status=413)
            elif request.content_type != 'application/x-www-form-urlencoded':
                response=HttpResponse('Only text form submissions are accepted. File uploads are unavailable.',status=415)
        try:
            response=response or self.get_response(request)
        except (RequestDataTooBig,TooManyFieldsSent):
            response=HttpResponse('Request exceeds the intake limit.',status=413)
        form_action = "'self' https://api.workos.com" if settings.AUTH_PROVIDER == 'workos' else "'self'"
        response['Content-Security-Policy']=f"default-src 'none'; style-src 'self'; img-src 'self'; form-action {form_action}; base-uri 'none'; frame-ancestors 'none'"
        response['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        # Keep paths and OAuth query strings private without making browser POST Origin null.
        response['Referrer-Policy']='strict-origin'
        response['Cache-Control']='private, no-store'
        if not (request.path == '/' or request.path.startswith('/research/') or request.path in ['/archive/','/policies/','/health/']):
            response['X-Robots-Tag']='noindex, nofollow'
        response['X-Request-ID']=request_id
        match=getattr(request,'resolver_match',None)
        logging.getLogger('archive.telemetry').info(json.dumps({
            'request_id':request_id,'route':match.view_name if match else 'unmatched',
            'method':request.method if request.method in ['GET','POST','HEAD','PUT','PATCH','DELETE','OPTIONS'] else 'OTHER',
            'status':response.status_code,'duration_ms':round((time.monotonic()-started)*1000)},separators=(',',':')))
        return response

class WriteLimitMiddleware:
    def __init__(self,get_response):
        self.get_response=get_response
    def __call__(self,request):
        return self.get_response(request)
    def process_view(self,request,view_func,view_args,view_kwargs):
        external_login = (settings.AUTH_PROVIDER == 'workos' and request.method == 'GET'
                          and request.path == '/accounts/workos/initiate/')
        if request.method != 'POST' and not external_login:
            return None
        now=timezone.now()
        # Never trust user-supplied X-Forwarded-For. A deployment proxy needs explicit separate review.
        principal='user:'+str(request.user.pk) if request.user.is_authenticated else 'ip:'+request.META.get('REMOTE_ADDR','unknown')
        principals=[(principal,60 if request.user.is_authenticated else 10)]
        if request.path == '/accounts/login/':
            principals.append(('login:'+request.POST.get('username','')[:150].casefold(),10))
        try:
            with transaction.atomic():
                for principal,limit in principals:
                    raw=f'{int(time.time())//60}:{principal}'.encode()
                    key=hmac.new(settings.SECRET_KEY.encode(),raw,hashlib.sha256).hexdigest()
                    bucket,_=RateBucket.objects.select_for_update().get_or_create(key=key,defaults={'expires_at':now+timedelta(minutes=2)})
                    if bucket.count>=limit:
                        result=HttpResponse('Too many attempts. Please retry in one minute.',status=429)
                        result['Retry-After']='60'
                        return result
                    bucket.count+=1
                    bucket.save(update_fields=['count'])
                RateBucket.objects.filter(expires_at__lt=now).delete()
        except OperationalError:
            result=HttpResponse('Intake is busy. Retry shortly; do not assume your change was saved.',status=503)
            result['Retry-After']='5'
            return result
        return None
