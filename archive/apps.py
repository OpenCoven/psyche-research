from django.apps import AppConfig

class ArchiveConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'archive'

    def ready(self):
        from django.db.backends.signals import connection_created
        from config.database import verify_session_timeouts
        connection_created.connect(verify_session_timeouts, dispatch_uid='archive.verify_session_timeouts')
