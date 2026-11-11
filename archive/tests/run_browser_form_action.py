"""Exact-source browser contract: the WorkOS sign-in form's redirect chain under the application's own CSP.

Browsers apply CSP form-action to every redirect of a form-submitted navigation. The sign-in button POSTs to the
app, which redirects to https://api.workos.com, which redirects to the environment's hosted AuthKit origin. This
contract runs the real application in WorkOS mode on loopback and lets Chromium resolve api.workos.com and two
synthetic AuthKit hosts to a local HTTPS mock through --host-resolver-rules, trusting only that mock's key. Every
other hostname is mapped to NOTFOUND and proxies are disabled, so no browser request can reach WorkOS or any other
real service. It requires that the configured AuthKit origin completes the chain
and that an unlisted origin is still refused, so the directive stays enforced rather than removed.
"""
import base64
import datetime
import hashlib
import http.server
import json
import os
from pathlib import Path
import signal
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
AUTHKIT = 'synthetic-authkit.example.invalid'
UNLISTED = 'unlisted-authkit.example.invalid'
CLIENT_ID = 'client_synthetic'


def free_port():
    with socket.socket() as available:
        available.bind(('127.0.0.1', 0))
        return available.getsockname()[1]


def mock_certificate(directory):
    """A one-hour self-signed key for the three mapped hosts; Chromium trusts only its SPKI hash."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'synthetic loopback mock')])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
                   .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=5))
                   .not_valid_after(now + datetime.timedelta(hours=1))
                   .add_extension(x509.SubjectAlternativeName(
                       [x509.DNSName(host) for host in ('api.workos.com', AUTHKIT, UNLISTED)]), critical=False)
                   .sign(key, hashes.SHA256()))
    cert_path, key_path = directory / 'mock-cert.pem', directory / 'mock-key.pem'
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                           serialization.NoEncryption()))
    key_path.chmod(0o600)
    spki = key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return cert_path, key_path, base64.b64encode(hashlib.sha256(spki).digest()).decode()


def mock_server(cert_path, key_path, authkit_target, callback, hits):
    """api.workos.com: check the authorize request's shape, then redirect to authkit_target. AuthKit hosts: 200."""
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            host = (self.headers.get('Host') or '').split(':')[0]
            url = urllib.parse.urlsplit(self.path)
            if url.path == '/favicon.ico':  # browser housekeeping, not part of the navigation chain
                self.send_response(404)
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            if host == 'api.workos.com' and url.path == '/user_management/authorize':
                query = urllib.parse.parse_qs(url.query)
                hits.append({'host': host, 'path': url.path,
                             'shape_ok': query.get('client_id') == [CLIENT_ID] and query.get('redirect_uri') == [callback]
                             and query.get('provider') == ['authkit'] and query.get('code_challenge_method') == ['S256']
                             and len(query.get('state', [''])[0]) >= 32})
                self.send_response(302)
                self.send_header('Location', f'https://{authkit_target}/sign-in')
                self.send_header('Content-Length', '0')
                self.end_headers()
            elif host in (AUTHKIT, UNLISTED):
                hits.append({'host': host, 'path': url.path})
                body = b'<!doctype html><title>SYNTHETIC AUTHKIT</title><p>SYNTHETIC AUTHKIT</p>'
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                hits.append({'host': host, 'path': url.path, 'unexpected': True})
                self.send_response(404)
                self.send_header('Content-Length', '0')
                self.end_headers()

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def run_node(fixture):
    node = subprocess.Popen(['node', str(ROOT / 'archive/tests/browser_form_action.mjs'), str(fixture)], cwd=ROOT,
                            start_new_session=True, stdout=subprocess.PIPE, text=True)
    try:
        output, _ = node.communicate(timeout=120)
        if node.returncode:
            raise subprocess.CalledProcessError(node.returncode, 'browser form-action contract')
        return json.loads(output.strip().splitlines()[-1])
    finally:
        # The new session holds this probe's Node/Chromium processes only.
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(node.pid, sig)
            except ProcessLookupError:
                break
            time.sleep(0.5)


def main():
    with tempfile.TemporaryDirectory(prefix='psyche-form-action-contract-') as temporary:
        scratch = Path(temporary)
        # Refuse inherited serving/provider configuration; all data and keys are synthetic and disposable.
        for name in list(os.environ):
            if name.startswith(('DATABASE_', 'DJANGO_', 'WORKOS_', 'VERCEL', 'POSTGRES_', 'AUTH_')):
                os.environ.pop(name)
        port = free_port()
        origin = f'http://127.0.0.1:{port}'
        callback = origin + '/accounts/workos/callback/'
        from cryptography.fernet import Fernet
        os.environ.update(LOCAL_DEVELOPMENT='1', PILOT_APPROVED='0', AUTH_PROVIDER='workos',
                          DATABASE_PATH=str(scratch / 'synthetic.sqlite3'), DJANGO_SETTINGS_MODULE='config.settings',
                          WORKOS_API_KEY='sk_test_synthetic_only', WORKOS_CLIENT_ID=CLIENT_ID,
                          WORKOS_REDIRECT_URI=callback, WORKOS_ISSUER='https://api.workos.com/user_management/' + CLIENT_ID,
                          WORKOS_COOKIE_PASSWORD=Fernet.generate_key().decode(),
                          WORKOS_AUTHKIT_ORIGIN='HTTPS://' + AUTHKIT.upper() + ':443/')
        subprocess.run([sys.executable, 'manage.py', 'migrate', '--verbosity', '0'], cwd=ROOT, check=True, timeout=120)
        cert_path, key_path, spki = mock_certificate(scratch)
        hits = {'listed': [], 'unlisted': []}
        mocks = {'listed': mock_server(cert_path, key_path, AUTHKIT, callback, hits['listed']),
                 'unlisted': mock_server(cert_path, key_path, UNLISTED, callback, hits['unlisted'])}
        with (scratch / 'server.log').open('w') as log:
            server = subprocess.Popen([sys.executable, 'manage.py', 'runserver', '--insecure', '--noreload',
                                       f'127.0.0.1:{port}'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            try:
                for _ in range(100):
                    if server.poll() is not None:
                        raise RuntimeError('Synthetic WorkOS-mode server exited before readiness')
                    try:
                        with urllib.request.urlopen(origin + '/health/', timeout=1) as response:
                            if response.status == 200:
                                break
                    except (urllib.error.URLError, TimeoutError):
                        time.sleep(0.1)
                else:
                    raise RuntimeError('Synthetic WorkOS-mode server did not become ready')
                with urllib.request.urlopen(origin + '/accounts/login/', timeout=5) as response:
                    policy = response.headers['Content-Security-Policy']
                expected = f"form-action 'self' https://api.workos.com https://{AUTHKIT};"
                assert expected in policy, 'login page CSP does not list the canonical configured AuthKit origin'
                assert UNLISTED not in policy
                results = {}
                for case, mock in mocks.items():
                    fixture = scratch / f'fixture-{case}.json'
                    mock_port = mock.server_address[1]
                    rules = [f'MAP {host} 127.0.0.1:{mock_port}' for host in ('api.workos.com', AUTHKIT, UNLISTED)]
                    rules += ['MAP * ~NOTFOUND', 'EXCLUDE 127.0.0.1']
                    fixture.write_text(json.dumps({'origin': origin, 'spki': spki, 'host_rules': ', '.join(rules)}))
                    fixture.chmod(0o600)
                    results[case] = run_node(fixture)
                listed, unlisted = results['listed'], results['unlisted']
                # Configured origin: the whole chain completes on hosted AuthKit with no CSP refusal.
                assert [h['host'] for h in hits['listed']] == ['api.workos.com', AUTHKIT], hits['listed']
                assert hits['listed'][0]['shape_ok'], 'authorize request lost client, callback, PKCE or state'
                assert listed['final'] == f'https://{AUTHKIT}/sign-in' and listed['title'] == 'SYNTHETIC AUTHKIT', listed
                assert not listed['csp_refusals'], listed
                # Unlisted origin: the first hop is allowed, the second is refused and the page stays put.
                assert [h['host'] for h in hits['unlisted']] == ['api.workos.com'], hits['unlisted']
                assert hits['unlisted'][0]['shape_ok']
                assert unlisted['final'] == origin + '/accounts/login/', unlisted
                assert any('form-action' in text for text in unlisted['csp_refusals']), unlisted
                print(json.dumps({'login_csp_lists_configured_authkit_origin': True,
                                  'listed_chain': [h['host'] for h in hits['listed']], 'listed_final': listed['final'],
                                  'unlisted_chain': [h['host'] for h in hits['unlisted']],
                                  'unlisted_final_path': urllib.parse.urlsplit(unlisted['final']).path,
                                  'unlisted_refused_by_form_action': True, 'browser': listed['browser']}))
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)
                for mock in mocks.values():
                    mock.shutdown()
                    mock.server_close()


if __name__ == '__main__':
    main()
