"""Loopback development transport for one saved physical-composition view.

This adapter exercises direct interaction against the existing Git transactions.
It does not implement hosted account authorization or either application host.
"""
from copy import deepcopy
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
from threading import RLock
from urllib.parse import urlsplit, parse_qs

from .composition_edit import EditError
from .composition_project import CompositionProject
from .composition_records import strict_json
from .composition_view import artifact_files, render

ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 1_000_000
DEFINITE_REFUSALS = frozenset(('stale_revision', 'request_reuse', 'input', 'request_id',
    'name', 'identity', 'name_collision', 'multiplicity', 'element_kind', 'reference_form', 'unresolved_reference',
    'semantic_delta', 'reference_delta', 'overlapping_edits', 'linked_records',
    'source_span', 'native_diagnostics', 'reconciliation', 'presentation_conflict', 'file_name'))


class CompositionSession:
    def __init__(self, project, view_id):
        self.project = project
        self.view_id = view_id
        self.lock = RLock()
        self.cache = None

    def _refresh(self):
        if self.cache is None or self.cache['state']['commit'] != self.project.head():
            snapshot = self.project.snapshot()
            drawing = render(snapshot['document'], self.view_id)
            files = artifact_files(snapshot, self.view_id)
            state = {'revision': snapshot['revision'], 'commit': snapshot['commit'],
                     'projection': drawing['projection'], 'layout': drawing['layout'],
                     'display_title': drawing['display_title'], 'display_labels': drawing['display_labels'],
                     'configuration_reviews': deepcopy(snapshot['document'].configuration_reviews),
                     'reconciliation': deepcopy(snapshot['document'].reconciliation),
                     'history': [{key: row[key] for key in ('revision', 'operation', 'restored_from_revision')}
                                 for row in self.project.history()],
                     'claim': 'local_saved_project_not_hosted_or_application_qualified'}
            self.cache = {'state': state, 'files': files}
        return self.cache

    def state(self):
        with self.lock:
            return deepcopy(self._refresh()['state'])

    def inspect_page(self, *, expected_revision, expected_bundle_sha256, origin, offset, limit):
        from .composition_inspection import page
        with self.lock:
            if type(expected_revision) is not int or expected_revision < 1 or not isinstance(expected_bundle_sha256, str):
                raise EditError('input', 'Inspection needs an explicit saved revision and bundle digest')
            state = self._refresh()['state']
            if expected_revision != state['revision']:
                raise EditError('stale_revision', 'The saved project changed before inspection')
            return {'revision': state['revision'], 'commit': state['commit'],
                    'inspection_page': page(state['projection']['inspection'], origin=origin,
                        offset=offset, limit=limit, expected_bundle_sha256=expected_bundle_sha256)}

    def file(self, name):
        with self.lock:
            return self._refresh()['files'][name]

    def page_state(self):
        with self.lock:
            cache = self._refresh()
            return {'state': deepcopy(cache['state']), 'view_html': cache['files']['index.html'].decode('utf-8')}

    def preview(self, request):
        with self.lock:
            if isinstance(request, dict) and request.get('operation') in ('create_definition', 'create_usage') and request.get('view_id') != self.view_id:
                raise EditError('input', 'Creation must use this session view')
            candidate = self.project.preview(request)
            document = candidate.pop('document')
            drawing = render(document, self.view_id)
            if request.get('operation') in ('create_definition', 'create_usage'):
                if request['view_id'] != self.view_id:
                    raise EditError('input', 'Creation must use this session view')
                candidate['candidate_svg'] = drawing['svg']
                candidate['created_element'] = next((node for node in drawing['projection']['nodes'].values()
                    if node['element_id'] == request['element_id']),
                    drawing['projection']['inspection']['occurrences']['decl:'+request['element_id']])
            return {**candidate, 'candidate_bundle_sha256': document.revision,
                    'configuration_reviews': deepcopy(document.configuration_reviews),
                    'reconciliation': deepcopy(document.reconciliation),
                    'claim': 'unsaved_candidate_not_a_transaction_receipt'}

    def apply(self, request):
        with self.lock:
            try:
                request = self.project._validate_request(request)
            except EditError as exc:
                exc.definitive_refusal = True
                raise
            try:
                try:
                    self.preview(request)
                except EditError as exc:
                    if exc.code != 'already_applied':
                        raise
                except ValueError as exc:
                    raise EditError('presentation_conflict', str(exc)) from exc
                receipt = self.project.transact(request)
            except (ValueError, OSError, TypeError, RecursionError) as exc:
                # Preliminary reads during a retry can also fail. Their
                # failure says nothing about the earlier publication outcome.
                history_read, lookup_completed = False, False
                try:
                    history = self.project.history()
                    history_read = True
                    receipt = self.project._retry(history, request)
                    lookup_completed = True
                except (ValueError, OSError, TypeError, RecursionError) as lookup_error:
                    if history_read and getattr(lookup_error, 'code', None) == 'request_reuse':
                        lookup_error.definitive_refusal = True
                        raise
                    receipt = None
                if receipt is None:
                    if lookup_completed and getattr(exc, 'code', None) in DEFINITE_REFUSALS:
                        exc.definitive_refusal = True
                        raise
                    raise EditError('outcome_unknown', 'Save outcome is unconfirmed; retry the exact request ID and values') from exc
            # Publication is already durable. Rendering a following read must
            # not turn that acknowledgement into a mutation refusal.
            try:
                return {'receipt': receipt, 'state': self.state()}
            except (ValueError, OSError, TypeError, RecursionError) as exc:
                return {'receipt': receipt, 'state': None,
                        'refresh_error': {'code': getattr(exc, 'code', 'refresh'), 'detail': str(exc)}}


class CompositionHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, project, view_id, port=0):
        self.session = CompositionSession(project, view_id)
        self.session.state()  # Refuse an unavailable native view before listening.
        self.access = secrets.token_urlsafe(32)
        self.csrf = secrets.token_urlsafe(32)
        self.cookie_name = 'cse_' + secrets.token_hex(8)
        super().__init__(('127.0.0.1', port), CompositionHandler)
        self.origin = 'http://127.0.0.1:' + str(self.server_port)


class CompositionHandler(BaseHTTPRequestHandler):
    server_version = 'CSE-local'

    def log_message(self, *_):
        pass  # No request bodies, model names or session credentials in logs.

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def _send(self, status, body, kind='application/json; charset=utf-8', *, cookie=False):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=True, allow_nan=False).encode('utf-8')
        self.send_response(status)
        for name, value in {
            'Content-Type': kind, 'Content-Length': str(len(body)), 'Cache-Control': 'no-store',
            'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src data:; img-src 'self' data:; connect-src 'self'; frame-src 'self'; frame-ancestors 'self'; base-uri 'none'; form-action 'self'",
        }.items():
            self.send_header(name, value)
        if cookie:
            self.send_header('Set-Cookie', self.server.cookie_name + '=' + self.server.access + '; Path=/; HttpOnly; SameSite=Strict')
        self.end_headers()
        self.wfile.write(body)

    def _boundary(self):
        if self.headers.get('Host') != self.server.origin.removeprefix('http://'):
            raise EditError('origin', 'Use the exact loopback server origin')
        origin = self.headers.get('Origin')
        if origin is not None and origin != self.server.origin:
            raise EditError('origin', 'Cross-origin access is refused')

    def _authorized(self):
        raw = self.headers.get('Cookie', '')
        if len(raw) > 8192:
            return False
        try:
            cookies = SimpleCookie(raw)
            value = cookies.get(self.server.cookie_name)
            return value is not None and secrets.compare_digest(value.value, self.server.access)
        except Exception:
            return False

    def _body(self):
        length = self.headers.get('Content-Length', '')
        if (self.headers.get('Transfer-Encoding') is not None or not length.isdigit()
                or not 1 <= int(length) <= MAX_BODY
                or self.headers.get_content_type() != 'application/json'):
            raise EditError('input', 'Supply one bounded JSON request')
        raw = self.rfile.read(int(length))
        if len(raw) != int(length):
            raise EditError('input', 'Incomplete request body')
        value = strict_json(raw.decode('utf-8'))
        if not isinstance(value, dict):
            raise EditError('input', 'Expected a JSON object')
        return value

    def _error(self, exc):
        code = getattr(exc, 'code', 'input')
        status = 503 if code == 'outcome_unknown' else 409 if code in ('stale_revision', 'request_reuse', 'already_applied') else 403 if code in ('origin', 'authorization') else 400
        self._send(status, {'error': {'code': code, 'detail': str(exc),
                                    'definitive_refusal': getattr(exc, 'definitive_refusal', False) is True}})

    def do_GET(self):
        try:
            self._boundary()
            if self.path in ('/', '/app.js', '/site-tools.js'):
                name = {'/': 'composition-workbench.html', '/app.js': 'composition-workbench.js',
                        '/site-tools.js': 'composition-site-tools.js'}[self.path]
                kind = 'text/html; charset=utf-8' if self.path == '/' else 'text/javascript; charset=utf-8'
                return self._send(200, (ROOT/'web'/name).read_bytes(), kind)
            if not self._authorized():
                raise EditError('authorization', 'Open the private local session link')
            if self.path == '/api/state':
                return self._send(200, {**self.server.session.page_state(), 'csrf': self.server.csrf})
            if self.path == '/api/head':
                return self._send(200, {'commit': self.server.session.project.head()})
            files = {'/view': ('index.html', 'text/html; charset=utf-8'),
                     '/view.svg': ('view.svg', 'image/svg+xml'), '/view.json': ('view.json', 'application/json; charset=utf-8')}
            route = urlsplit(self.path)
            if route.path in files:
                query = parse_qs(route.query, strict_parsing=True)
                with self.server.session.lock:
                    cache = self.server.session._refresh()
                    if query and query != {'commit': [cache['state']['commit']]}:
                        raise EditError('stale_revision', 'Requested drawing revision is no longer current; refresh the project')
                    name, kind = files[route.path]
                    return self._send(200, cache['files'][name], kind)
            return self._send(404, {'error': {'code': 'not_found', 'detail': 'Unknown route'}})
        except (ValueError, OSError, TypeError, RecursionError) as exc:
            self._error(exc)

    def do_POST(self):
        try:
            self._boundary()
            if self.headers.get('Origin') != self.server.origin:
                raise EditError('origin', 'A same-origin request is required')
            body = self._body()
            if self.path == '/session':
                if set(body) != {'access'} or not isinstance(body['access'], str) or not secrets.compare_digest(body['access'], self.server.access):
                    raise EditError('authorization', 'Invalid local session link')
                return self._send(200, {'connected': True}, cookie=True)
            if not self._authorized() or not secrets.compare_digest(self.headers.get('X-CSE-CSRF', ''), self.server.csrf):
                raise EditError('authorization', 'Invalid local session')
            if self.path == '/api/preview':
                return self._send(200, {'preview': self.server.session.preview(body)})
            if self.path == '/api/apply':
                return self._send(200, self.server.session.apply(body))
            if self.path == '/api/receipt':
                return self._send(200, self.server.session.project.lookup_receipt(body))
            if self.path == '/api/inspection':
                if set(body) != {'expected_revision', 'expected_bundle_sha256', 'origin', 'offset', 'limit'}:
                    raise EditError('input', 'Supply exactly the inspection snapshot and page fields')
                return self._send(200, self.server.session.inspect_page(**body))
            return self._send(404, {'error': {'code': 'not_found', 'detail': 'Unknown route'}})
        except (ValueError, OSError, TypeError, RecursionError) as exc:
            self._error(exc)
