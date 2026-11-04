"""Deployment candidate only. Requires separately approved loopback-only nginx/TLS host."""
bind='127.0.0.1:8010'
workers=1
worker_class='sync'
threads=1
timeout=30
graceful_timeout=30
limit_request_line=4094
limit_request_fields=40
limit_request_field_size=4094
umask=0o077
# nginx must overwrite X-Forwarded-Proto, and the listener must never bind a public interface.
forwarded_allow_ips='127.0.0.1'
secure_scheme_headers={'X-FORWARDED-PROTO':'https'}
# No raw URL, query, body, cookie, username or IP access log. Health and aggregate ops are separate.
accesslog=None
errorlog='-'
loglevel='warning'
capture_output=False
# Gunicorn's default malformed-request/exception logs may contain URIs, headers and tracebacks.
logger_class='config.safe_logger.SafeGunicornLogger'
