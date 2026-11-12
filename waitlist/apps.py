from django.apps import AppConfig
from django.db.backends.signals import connection_created
from config.database import verify_session_timeouts


class WaitlistConfig(AppConfig):
    name = 'waitlist'

    def ready(self):
        connection_created.connect(verify_session_timeouts, dispatch_uid='waitlist-timeout-check')

