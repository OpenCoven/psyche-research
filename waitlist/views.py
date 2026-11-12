from django.conf import settings
from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods
from .forms import RegistrationForm
from .middleware import unavailable
from .services import register


def context(**kwargs):
    return {'operator': settings.WAITLIST_OPERATOR or 'Operator pending launch approval',
            'contact': settings.WAITLIST_CONTACT, 'retention_days': settings.WAITLIST_RETENTION_DAYS, **kwargs}


@require_http_methods(['GET', 'HEAD', 'POST'])
def home(request):
    form = RegistrationForm(request.POST if request.method == 'POST' else None)
    status = 200
    message = ''
    errors = None
    if request.method == 'POST':
        if form.is_valid():
            try:
                result = register(form.cleaned_data)
            except DatabaseError:
                result = 'busy'
            if result == 'accepted':
                return redirect('waitlist_confirmation')
            status = 429 if result == 'limited' else 503
            message = ('Too many attempts. Please try again tomorrow.' if result == 'limited' else
                       'Registration is temporarily unavailable. Please try again later.')
        else:
            status = 400
        # Keep private input out of rendered responses, even on validation failure.
        errors = form.errors
        form = RegistrationForm()
    response = render(request, 'waitlist/home.html', context(form=form, message=message, errors=errors), status=status)
    if status in {429, 503}:
        response['Retry-After'] = '86400' if status == 429 else '60'
    return response


@require_GET
def confirmation(request):
    return render(request, 'waitlist/confirmation.html')


@require_GET
def privacy(request):
    return render(request, 'waitlist/privacy.html', context())


@require_GET
def health(request):
    return HttpResponse('ok', content_type='text/plain')


def not_found(request, exception):
    return HttpResponse('Page not found.', status=404)


def server_error(request):
    return HttpResponse('Temporarily unavailable.', status=500)

