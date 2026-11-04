"""Gunicorn errors may contain raw URLs/headers. Preserve severity, omit request content and traces."""
import json
import logging
from gunicorn.glogging import Logger

class ConstantServerEvent(logging.Filter):
    def filter(self,record):
        record.msg=json.dumps({'event':'wsgi_server','level':record.levelname},separators=(',',':'))
        record.args=()
        record.exc_info=None
        record.exc_text=None
        record.stack_info=None
        return True

class SafeGunicornLogger(Logger):
    def setup(self,cfg):
        for target in (self.error_log,self.access_log):
            if not any(isinstance(f,ConstantServerEvent) for f in target.filters):
                target.addFilter(ConstantServerEvent())
        super().setup(cfg)
