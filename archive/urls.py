from django.urls import path
from . import views
urlpatterns = [
    path('',views.home,name='home'),
    path('archive/',views.browse,name='archive'),
    path('policies/',views.policies,name='policies'),
    path('health/',views.health,name='health'),
    path('research/<uuid:work_id>/',views.latest,name='work'),
    path('research/<uuid:work_id>/v<int:number>/',views.version,name='version'),
    path('research/<uuid:work_id>/v<int:number>/export/',views.export_version,name='export_version'),
    path('research/<uuid:work_id>/report/',views.report,name='report'),
    path('workspace/',views.dashboard,name='dashboard'),
    path('workspace/new/',views.new_submission,name='new_submission'),
    path('workspace/<uuid:submission_id>/',views.edit,name='edit'),
    path('workspace/<uuid:submission_id>/export/',views.export_submission,name='export_submission'),
    path('workspace/<uuid:submission_id>/appeal/',views.appeal,name='appeal'),
    path('workspace/revision/<uuid:work_id>/',views.revision,name='revision'),
    path('workspace/withdraw/<uuid:work_id>/',views.withdraw,name='withdraw'),
    path('moderation/',views.queue,name='queue'),
    path('moderation/<uuid:submission_id>/',views.moderate,name='moderate'),
    path('moderation/appeals/<int:appeal_id>/',views.resolve_appeal,name='resolve_appeal'),
    path('operations/',views.operations,name='operations'),
    path('operations/reports/<uuid:report_id>/',views.report_resolve,name='report_resolve'),
]
