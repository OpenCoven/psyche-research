from django.urls import include, path
from archive import workos_auth

urlpatterns = [
    path('accounts/login/', workos_auth.login_view, name='login'),
    path('accounts/logout/', workos_auth.logout_view, name='logout'),
    path('accounts/workos/start/', workos_auth.start, name='workos_start'),
    path('accounts/workos/initiate/', workos_auth.initiate, name='workos_initiate'),
    path('accounts/workos/callback/', workos_auth.callback, name='workos_callback'),
    path('accounts/password/', workos_auth.password_change, name='password_change'),
    path('accounts/password/done/', workos_auth.password_change_done, name='password_change_done'),
    path('', include('archive.urls')),
]
