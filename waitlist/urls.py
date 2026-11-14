from django.urls import path
from . import views

urlpatterns = [path('', views.home, name='waitlist_home'),
               path('confirmation/', views.confirmation, name='waitlist_confirmation'),
               path('privacy/', views.privacy, name='waitlist_privacy'),
               path('health/', views.health, name='waitlist_health')]
handler404 = 'waitlist.views.not_found'
handler500 = 'waitlist.views.server_error'
