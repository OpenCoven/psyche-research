import json
from urllib.parse import urlencode
from django.contrib.auth import get_user_model
from django.test import TestCase
from archive import services

class SafeTelemetry(TestCase):
    def test_private_payload_query_and_account_never_enter_request_log(self):
        user=get_user_model().objects.create_user('SYNTHETIC-private-identity',password='synthetic-password-test-123')
        self.client.force_login(user)
        row=services.create_submission(user)
        with self.assertLogs('archive.telemetry',level='INFO') as captured:
            response=self.client.post('/workspace/'+str(row.id)+'/?private=SECRET_QUERY_SENTINEL',urlencode({
                'revision':0,'title':'SECRET_MANUSCRIPT_SENTINEL','kind':'report','action':'save'}),content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code,302)
        raw=' '.join(captured.output)
        for marker in ['SECRET_QUERY_SENTINEL','SECRET_MANUSCRIPT_SENTINEL','SYNTHETIC-private-identity',str(row.id),'sessionid','csrfmiddlewaretoken']:
            self.assertNotIn(marker,raw)
        event=json.loads(captured.records[-1].getMessage())
        self.assertEqual(set(event),{'request_id','route','method','status','duration_ms'})
        self.assertEqual(event['route'],'edit')
        self.assertEqual(response['X-Request-ID'],event['request_id'])

    def test_wsgi_request_errors_omit_headers_uris_and_tracebacks(self):
        from gunicorn.config import Config
        from config.safe_logger import SafeGunicornLogger
        logger=SafeGunicornLogger(Config())
        with self.assertLogs('gunicorn.error',level='DEBUG') as captured:
            logger.warning('Invalid header %s','SECRET_HEADER_SENTINEL')
            try:
                raise RuntimeError('SECRET_TRACE_SENTINEL')
            except RuntimeError:
                logger.exception('Error handling request %s','/private/?SECRET_URI_SENTINEL')
        for record in captured.records:
            self.assertEqual(set(json.loads(record.getMessage())),{'event','level'})
            self.assertIsNone(record.exc_info)
            self.assertIsNone(record.exc_text)
        raw=' '.join(captured.output)
        for marker in ['SECRET_HEADER_SENTINEL','SECRET_TRACE_SENTINEL','SECRET_URI_SENTINEL','Traceback']:
            self.assertNotIn(marker,raw)

    def test_artifact_links_are_validated_escaped_external_references_without_fetch(self):
        from django.template import Template,Context
        from archive.templatetags.research import artifact_links
        self.assertEqual(artifact_links('javascript:alert(1)'),[])
        self.assertEqual(artifact_links('https://example.org/"><script>'),[])
        self.assertEqual(artifact_links('https://example.org/synthetic'),['https://example.org/synthetic'])
        html=Template('{% include "archive/_snapshot.html" %}').render(Context({'snapshot':{'artifacts':'https://example.org/synthetic'}}))
        self.assertIn('href="https://example.org/synthetic"',html)
        self.assertIn('rel="noreferrer noopener nofollow"',html)
