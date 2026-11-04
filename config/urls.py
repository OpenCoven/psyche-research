from django.contrib.auth import views as auth
from django.urls import include, path

urlpatterns = [
    path('accounts/login/', auth.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth.LogoutView.as_view(), name='logout'),
    path('accounts/password/', auth.PasswordChangeView.as_view(success_url='/accounts/password/done/'), name='password_change'),
    path('accounts/password/done/', auth.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('', include('archive.urls')),
]
