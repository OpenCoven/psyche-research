from django.conf import settings
from django.core.exceptions import RequestDataTooBig, TooManyFieldsSent
from django.db import DatabaseError
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


def unavailable():
    response = HttpResponse('Registration is temporarily unavailable. Please try again later.', status=503)
    response['Retry-After'] = '60'
    return response


class PublicBoundary(MiddlewareMixin):
    def process_request(self, request):
        if request.method in {'POST', 'PUT', 'PATCH'}:
            try:
                size = int(request.META.get('CONTENT_LENGTH') or 0)
            except ValueError:
                size = -1
            if not 0 <= size <= settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
                return HttpResponse('Request is too large.', status=413)
            if request.content_type != 'application/x-www-form-urlencoded':
                return HttpResponse('Only text forms are accepted.', status=415)

    def process_exception(self, request, exception):
        if isinstance(exception, DatabaseError):
            return unavailable()
        if isinstance(exception, (RequestDataTooBig, TooManyFieldsSent)):
            return HttpResponse('Request is too large.', status=413)
        return None

    def process_response(self, request, response):
        response['Content-Security-Policy'] = "default-src 'none'; style-src 'self'; img-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'"
        response['Cache-Control'] = 'private, no-store'
        response['Referrer-Policy'] = 'no-referrer'
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response

