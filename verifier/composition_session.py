"""Loopback development transport for one saved physical-composition view.

This adapter exercises direct interaction against the existing Git transactions.
It does not implement hosted account authorization or either application host.
"""
from copy import deepcopy
from hashlib import sha256
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
from threading import RLock
from urllib.parse import urlsplit, parse_qs

from .composition_data_tools import CompositionDataTools, catalog_read
from .composition_edit import EditError
from .composition_project import CompositionProject, request_digest
from .composition_records import strict_json
from .composition_view import DEFAULT_FRAME_STYLE, appearance_palette, artifact_files, companion, identifier, render, view_key_master_sha256
from .composition_source import files as source_files

ROOT = Path(__file__).resolve().parents[1]
MAX_BODY = 1_000_000
DEFINITE_REFUSALS = frozenset(('stale_revision', 'request_reuse', 'input', 'request_id',
    'name', 'identity', 'name_collision', 'multiplicity', 'element_kind', 'reference_form', 'unresolved_reference',
    'semantic_delta', 'reference_delta', 'overlapping_edits', 'linked_records',
    'source_span', 'native_diagnostics', 'reconciliation', 'presentation_conflict', 'file_name',
    'owner', 'same_owner', 'ownership_cycle', 'composition_transition', 'checked_candidate', 'reference_limit',
    'native_delta', 'explicit_effects', 'owned_members', 'view_unavailable',
    'artwork_role', 'artwork_key', 'stale_catalog', 'stale_palette'))
_REMOVAL_OPERATIONS = frozenset(('delete', 'remove_occurrence'))
ARTIFACT_TYPES = {'view.svg': 'image/svg+xml', 'view.json': 'application/json'}


class CompositionSession:
    def __init__(self, project, view_id):
        self.project = project
        self.view_id = view_id
        self.lock = RLock()
        self.cache = None
        self.prepared = None
        self.alternate_views = {}

    def for_view(self, view_id):
        if view_id is None or view_id == self.view_id:
            return self
        identifier(view_id)
        with self.lock:
            if view_id not in self.alternate_views:
                if len(self.alternate_views) >= 128:
                    self.alternate_views.pop(next(iter(self.alternate_views)))
                self.alternate_views[view_id] = CompositionSession(self.project, view_id)
            return self.alternate_views[view_id]

    def _refresh(self):
        if self.cache is None or self.cache['state']['commit'] != self.project.head():
            snapshot = self.project.snapshot()
            document = snapshot['document']
            from .composition_inspection import project as inspect
            from .composition_removal_views import physical_view_ids
            available = physical_view_ids(document)
            drawing = render(document, self.view_id) if self.view_id in available else None
            files = artifact_files(snapshot, self.view_id) if drawing else {}
            hashes = json.loads(files['manifest.json'])['files'] if files else {}
            projection = drawing['projection'] if drawing else {
                'id': self.view_id, 'project_id': document.project_id, 'bundle_sha256': document.revision,
                'mode': None, 'nodes': {}, 'edges': {}, 'inspection': inspect(document, self.view_id, {}),
                'claim': 'saved_project_without_the_requested_physical_view',
            }
            _, appearance = companion(document, 'composition_appearance', self.view_id) if drawing else (None, None)
            _, label_record = companion(document, 'display_labels', self.view_id) if drawing else (None, None)
            aliases = {row['element']: row['text'] for row in label_record['labels']} if label_record else {}
            state = {'revision': snapshot['revision'], 'commit': snapshot['commit'],
                     'artifact_hashes': {kind: hashes[kind] for kind in ARTIFACT_TYPES if kind in hashes},
                     'view_available': drawing is not None, 'available_views': available,
                     'projection': projection, 'layout': drawing['layout'] if drawing else None,
                     'display_title': drawing['display_title'] if drawing else None,
                     'display_labels': drawing['display_labels'] if drawing else {},
                     'display_aliases': {key: aliases[node['element']] for key, node in projection['nodes'].items()
                                         if node['element'] in aliases},
                     'frame_masters': {
                         row['node']: {'component_id': row['template'],
                                       'svg_sha256': drawing['kit_usage']['components'][row['template']]}
                         for row in drawing['kit_usage']['adaptations'] if 'node' in row
                     } if drawing else {},
                     'frame_styles': appearance['nodes'] if appearance else {
                         key: DEFAULT_FRAME_STYLE.copy() for key in projection['nodes']
                     },
                     'connector_styles': {
                         key: appearance['edges'].get(key, 'N100') if appearance else 'N100'
                         for key in projection['edges']
                     },
                     'appearance_palette': appearance_palette() if drawing else None,
                     'view_key': {'view_id': self.view_id, 'master_sha256': view_key_master_sha256(),
                                  'legend': appearance['legend'] if appearance else []} if drawing else None,
                     'configuration_reviews': deepcopy(snapshot['document'].configuration_reviews),
                     'reconciliation': deepcopy(snapshot['document'].reconciliation),
                     'model_sources': source_files(snapshot['document']),
                     'history': [{key: row[key] for key in ('revision', 'operation', 'restored_from_revision')}
                                 for row in self.project._history(snapshot['commit'])],
                     'claim': 'local_saved_project_not_hosted_or_application_qualified'}
            self.cache = {'state': state, 'files': files, 'document': snapshot['document']}
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
            files = self._refresh()['files']
            if name not in files:
                raise EditError('view_unavailable', 'The requested saved view is unavailable')
            return files[name]

    def read_artifact(self, payload):
        if (not isinstance(payload, dict)
                or set(payload) != {'kind', 'revision', 'commit', 'bundle_sha256', 'expected_sha256'}
                or not isinstance(payload['kind'], str) or payload['kind'] not in ARTIFACT_TYPES
                or type(payload['revision']) is not int):
            raise EditError('input', 'Choose a saved SVG or JSON artifact and its exact revision')
        with self.lock:
            cache = self._refresh()
            state, kind = cache['state'], payload['kind']
            projection = state['projection']
            if (payload['commit'] != state['commit'] or payload['revision'] != state['revision']
                    or payload['bundle_sha256'] != projection['bundle_sha256']):
                raise EditError('stale_revision', 'Refresh the saved physical view before exporting')
            if kind not in cache['files']:
                raise EditError('view_unavailable', 'The requested saved view is unavailable')
            digest = state['artifact_hashes'][kind]
            if digest != payload['expected_sha256']:
                raise EditError('artifact_changed', 'The saved artifact differs from the rendered view; refresh before exporting')
            raw = cache['files'][kind]
            return {**payload, 'project_id': projection['project_id'], 'view_id': projection['id'],
                    'media_type': ARTIFACT_TYPES[kind], 'sha256': digest,
                    'bytes': len(raw), 'text': raw.decode('utf-8')}

    def ownership_context(self, *, element_id, expected_revision, expected_bundle_sha256, offset, limit, view_id):
        from .composition_ownership import destinations
        from .composition_ownership_views import consequences
        with self.lock:
            cache = self._refresh()
            state, document = cache['state'], cache['document']
            if (type(expected_revision) is not int or not isinstance(expected_bundle_sha256, str)
                    or type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100
                    or not isinstance(element_id, str) or view_id is not None and not isinstance(view_id, str)):
                raise EditError('input', 'Ownership context needs a captured target/revision/bundle and bounded destination page')
            if expected_revision != state['revision'] or expected_bundle_sha256 != document.revision:
                raise EditError('stale_revision', 'Project changed before ownership context inspection')
            impacts, choices = consequences(document, element_id), destinations(document)
            if offset > len(choices):
                raise EditError('input', 'Ownership destination offset exceeds its inventory')
            selected = next((row for row in impacts if row['view_id'] == view_id), None)
            if view_id is not None and selected is None:
                raise EditError('input', 'Requested ownership view is not affected by this captured declaration')
            return {'project_id': document.project_id, 'element_id': element_id,
                    'revision': state['revision'], 'commit': state['commit'], 'bundle_sha256': document.revision,
                    'destinations': choices[offset:offset+limit], 'total_destinations': len(choices),
                    'next_offset': offset+limit if offset+limit < len(choices) else None,
                    'affected_views': [{key: value for key, value in row.items() if key != 'current_layout'} for row in impacts],
                    'view_detail': {**selected, 'projection': render(document, view_id)['projection']} if selected else None}

    def preview_view(self, request, view_id):
        with self.lock:
            if (not isinstance(request, dict) or request.get('operation') not in _REMOVAL_OPERATIONS | {'reparent'}
                    or request.get('checked_bundle_sha256') is None or not isinstance(view_id, str)
                    or view_id not in {row.get('view_id') for row in request.get('view_effects', []) if isinstance(row, dict)}):
                raise EditError('input', 'Choose one affected view from the exact checked request')
            candidate = self._prepared_candidate(request)
            closed = any(effect['view_id'] == view_id and effect.get('action') == 'close_view'
                         for effect in request['view_effects'])
            drawing = None if closed else render(candidate['document'], view_id)
            return {'view_id': view_id, 'candidate_svg': drawing['svg'] if drawing else None,
                    **({'closed': True} if closed else {}),
                    'candidate_bundle_sha256': candidate['document'].revision,
                    'base_revision': candidate['base_revision'], 'request_sha256': candidate['request_sha256'],
                    'claim': 'one_unsaved_checked_view_not_a_transaction_receipt'}

    def _prepared_candidate(self, request):
        request = self.project._validate_request(request)
        head, digest = self.project.head(), request_digest(request)
        if self.prepared and self.prepared['base_commit'] == head and self.prepared['request_sha256'] == digest:
            return self.prepared
        candidate = self.project.preview(request)
        self.prepared = candidate
        return candidate

    def read_source(self, *, expected_revision, expected_bundle_sha256, request, file, offset, limit):
        from .composition_source import chunk
        with self.lock:
            saved = self._refresh()
            state, document = saved['state'], saved['document']
            if (type(expected_revision) is not int or not isinstance(expected_bundle_sha256, str)
                    or request is not None and not isinstance(request, dict)):
                raise EditError('input', 'Source inspection needs its captured revision/bundle and optional exact candidate request')
            if expected_revision != state['revision'] or expected_bundle_sha256 != document.revision:
                raise EditError('stale_revision', 'Project changed before source inspection')
            digest = None
            if request is not None:
                candidate = self._prepared_candidate(request)
                document, digest = candidate['document'], candidate['request_sha256']
            return {**chunk(document, file, offset, limit), 'revision': state['revision'],
                    'base_commit': state['commit'], 'snapshot': 'candidate' if request is not None else 'saved',
                    'request_sha256': digest}

    def page_state(self):
        with self.lock:
            cache = self._refresh()
            return {'state': deepcopy(cache['state']), 'view_html': cache['files']['index.html'].decode('utf-8') if cache['files'] else None}

    def preview(self, request):
        with self.lock:
            if isinstance(request, dict) and request.get('operation') in ('create_definition', 'create_usage') and request.get('view_id') != self.view_id:
                raise EditError('input', 'Creation must use this session view')
            if isinstance(request, dict) and request.get('operation') in ('set_frame_master', 'set_connector_style', 'set_view_key', 'set_display_alias') and request.get('view_id') != self.view_id:
                raise EditError('input', 'The appearance edit must use this session view')
            if isinstance(request, dict) and request.get('operation') == 'set_layout' and (
                    not isinstance(request.get('layout'), dict) or request['layout'].get('view') != self.view_id):
                raise EditError('input', 'The layout edit must use this session view')
            prepared = self._prepared_candidate(request)
            document = prepared['document']
            candidate = {key: deepcopy(value) for key, value in prepared.items() if key != 'document'}
            removal = request.get('operation') in _REMOVAL_OPERATIONS
            closed = removal and any(row['view_id'] == self.view_id and row['action'] == 'close_view'
                                     for row in request['view_effects'])
            from .composition_removal_views import physical_view_ids
            available = physical_view_ids(document)
            if self.view_id in available:
                drawing = render(document, self.view_id)
            elif removal or request['operation'] == 'restore':
                drawing = None
            else:
                raise EditError('view_unavailable', 'Open a saved physical view before editing it')
            if request['operation'] == 'restore':
                candidate['candidate_available_views'] = available
                candidate['candidate_svg'] = drawing['svg'] if drawing else None
            if removal:
                candidate['candidate_svg'] = drawing['svg'] if drawing else None
                candidate['affected_views'] = {row['view_id']: {
                    'view_effect': deepcopy(row),
                    'candidate_svg_sha256': sha256(render(document, row['view_id'])['svg'].encode()).hexdigest()
                                            if row['action'] != 'close_view' else None,
                } for row in request['view_effects']}
                candidate['current_view_closed'] = closed
            if request.get('operation') in ('create_definition', 'create_usage'):
                if request['view_id'] != self.view_id:
                    raise EditError('input', 'Creation must use this session view')
                candidate['candidate_svg'] = drawing['svg']
                candidate['created_element'] = next((node for node in drawing['projection']['nodes'].values()
                    if node['element_id'] == request['element_id']),
                    drawing['projection']['inspection']['occurrences']['decl:'+request['element_id']])
            if request.get('operation') in ('set_types', 'reparent'):
                candidate['candidate_svg'] = drawing['svg']
                candidate['edited_element'] = drawing['projection']['inspection']['occurrences']['decl:'+request['element_id']]
            if request.get('operation') == 'set_layout':
                candidate['candidate_svg'] = drawing['svg']
                candidate['candidate_layout'] = drawing['layout']
            if request.get('operation') == 'set_frame_master':
                candidate['candidate_svg'] = drawing['svg']
                candidate['frame_artwork'] = {key: request[key] for key in ('view_id', 'node_id', 'element_id', 'component_id', 'catalog_sha256', 'svg_sha256')}
                _, appearance = companion(document, 'composition_appearance', self.view_id)
                style = appearance['nodes'][request['node_id']]
                candidate['frame_style'] = {key: style[key] for key in ('fill', 'stroke', 'text', 'align')}
            if request.get('operation') == 'set_connector_style':
                candidate['candidate_svg'] = drawing['svg']
                candidate['connector_style'] = {key: request[key] for key in ('view_id', 'edge_id', 'source_id', 'target_id', 'swatch', 'palette_sha256')}
            if request.get('operation') == 'set_view_key':
                candidate['candidate_svg'] = drawing['svg']
                candidate['view_key'] = {key: request[key] for key in ('view_id', 'master_sha256', 'legend')}
            if request.get('operation') == 'set_display_alias':
                candidate['candidate_svg'] = drawing['svg']
                candidate['display_alias'] = {key: request[key] for key in ('view_id', 'node_id', 'element_id', 'alias')}
            if request.get('operation') == 'reparent':
                candidate['ownership_change'] = deepcopy(document.ownership_change)
                candidate['affected_views'] = {effect['view_id']: {
                    'candidate_svg_sha256': sha256(render(document, effect['view_id'])['svg'].encode()).hexdigest(),
                    'view_effect': deepcopy(effect)} for effect in request['view_effects']}
            if 'candidate_svg' in candidate:
                svg = candidate['candidate_svg']
                candidate['candidate_svg_sha256'] = sha256(svg.encode()).hexdigest() if svg else None
            return {**candidate, 'candidate_bundle_sha256': document.revision,
                    'candidate_model_sources': source_files(document),
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
                if request['operation'] in _REMOVAL_OPERATIONS and any(
                    effect['view_id'] == self.view_id and effect['action'] == 'close_view'
                    for effect in request['view_effects']
                ):
                    from .composition_removal_views import physical_view_ids
                    snapshot = self.project.snapshot()
                    available = physical_view_ids(snapshot['document'])
                    if self.view_id not in available:
                        return {'receipt': receipt, 'state': None, 'view_closed': {
                            'view_id': self.view_id, 'available_views': available,
                            'commit': snapshot['commit'], 'revision': snapshot['revision'],
                        }}
                return {'receipt': receipt, 'state': self.state()}
            except (ValueError, OSError, TypeError, RecursionError) as exc:
                return {'receipt': receipt, 'state': None,
                        'refresh_error': {'code': getattr(exc, 'code', 'refresh'), 'detail': str(exc)}}


class CompositionHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, project, view_id, port=0):
        self.session = CompositionSession(project, view_id)
        identifier(view_id)
        self.session.state()  # Qualify saved project access before listening.
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

    def _saved_session(self, artifact_view=None):
        return self.server.session.for_view(artifact_view if artifact_view is not None else
                                            self.headers.get('X-CSE-View'))

    def do_GET(self):
        try:
            self._boundary()
            if self.path in ('/', '/app.js', '/site-tools.js', '/artifact-bytes.mjs'):
                name = {'/': 'composition-workbench.html', '/app.js': 'composition-workbench.js',
                        '/site-tools.js': 'composition-site-tools.js',
                        '/artifact-bytes.mjs': 'composition-artifact-bytes.mjs'}[self.path]
                kind = 'text/html; charset=utf-8' if self.path == '/' else 'text/javascript; charset=utf-8'
                return self._send(200, (ROOT/'web'/name).read_bytes(), kind)
            if not self._authorized():
                raise EditError('authorization', 'Open the private local session link')
            if self.path == '/api/state':
                return self._send(200, {**self._saved_session().page_state(), 'csrf': self.server.csrf})
            if self.path == '/api/head':
                return self._send(200, {'commit': self.server.session.project.head()})
            files = {'/view': ('index.html', 'text/html; charset=utf-8'),
                     '/view.svg': ('view.svg', 'image/svg+xml'), '/view.json': ('view.json', 'application/json; charset=utf-8')}
            route = urlsplit(self.path)
            if route.path in files:
                # Python 3.10 rejects an empty string in strict query parsing.
                query = parse_qs(route.query, strict_parsing=True) if route.query else {}
                requested = query.pop('view', None)
                if requested is not None and len(requested) != 1:
                    raise EditError('input', 'Choose one saved view ID')
                session = self._saved_session(requested[0] if requested else None)
                with session.lock:
                    cache = session._refresh()
                    if query and query != {'commit': [cache['state']['commit']]}:
                        raise EditError('stale_revision', 'Requested drawing revision is no longer current; refresh the project')
                    name, kind = files[route.path]
                    if name not in cache['files']:
                        raise EditError('view_unavailable', 'The requested saved view is unavailable')
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
            if self.path == '/api/catalog-search':
                return self._send(200, catalog_read('catalog_search', body))
            if self.path == '/api/catalog-inspect':
                return self._send(200, catalog_read('catalog_inspect', body))
            if self.path == '/api/catalog-selection':
                return self._send(200, catalog_read('catalog_selection', body))
            if self.path == '/api/preview':
                return self._send(200, {'preview': self._saved_session().preview(body)})
            if self.path == '/api/apply':
                return self._send(200, self._saved_session().apply(body))
            if self.path == '/api/receipt':
                return self._send(200, self.server.session.project.lookup_receipt(body))
            if self.path == '/api/artifact':
                return self._send(200, self._saved_session().read_artifact(body))
            if self.path == '/api/inspection':
                if set(body) != {'expected_revision', 'expected_bundle_sha256', 'origin', 'offset', 'limit'}:
                    raise EditError('input', 'Supply exactly the inspection snapshot and page fields')
                return self._send(200, self._saved_session().inspect_page(**body))
            if self.path == '/api/ownership-context':
                if set(body) != {'element_id', 'expected_revision', 'expected_bundle_sha256', 'offset', 'limit', 'view_id'}:
                    raise EditError('input', 'Supply exactly the ownership target/snapshot, destination page and selected affected view')
                return self._send(200, self._saved_session().ownership_context(**body))
            if self.path == '/api/removal-context':
                return self._send(200, self.server.session.project.removal_context(body))
            if self.path == '/api/preview-view':
                if set(body) != {'request', 'view_id'}:
                    raise EditError('input', 'Supply exactly the checked request and one affected view')
                return self._send(200, self._saved_session().preview_view(body['request'], body['view_id']))
            if self.path == '/api/source':
                if set(body) != {'expected_revision', 'expected_bundle_sha256', 'request', 'file', 'offset', 'limit'}:
                    raise EditError('input', 'Supply exactly the source snapshot, optional checked request, file and bounded page')
                return self._send(200, self._saved_session().read_source(**body))
            if self.path == '/api/retained-review':
                if set(body) != {'revision', 'bundle_sha256', 'file', 'scope_sha256', 'offset', 'limit'}:
                    raise EditError('input', 'Supply exactly the saved snapshot, retained scope and page fields')
                session = self.server.session
                project_id = session.state()['projection']['project_id']
                reader = CompositionDataTools(lambda granted_id: session.project if granted_id == project_id else None)
                return self._send(200, reader.retained_review(project_id, **body))
            return self._send(404, {'error': {'code': 'not_found', 'detail': 'Unknown route'}})
        except (ValueError, OSError, TypeError, RecursionError) as exc:
            self._error(exc)
