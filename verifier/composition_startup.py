"""Initial-authoring session over the shared native builder and Git transaction.

No saved projection exists at revision zero. A recovered first receipt hands
off to the existing saved-model session instead of creating another editor.
"""
from copy import deepcopy
from http.server import ThreadingHTTPServer
import os
from pathlib import Path
import secrets
import stat
from threading import RLock

from .composition_edit import EditError, name_spelling
from .composition_initial import prepare, initialize, lookup, validate_request, validate_checked_request
from .composition_project import CompositionProject, request_digest
from .composition_session import CompositionSession, CompositionHandler
from .composition_view import identifier, render


class InitialCompositionSession:
    def __init__(self, project, project_id, root_element_id, view_id):
        for identity in (project_id, root_element_id):
            CompositionProject._request_id(identity)
        if project_id == root_element_id:
            raise EditError('identity', 'Initial engineering root and project identities must be distinct')
        identifier(view_id)
        self.project = project
        self.project_id = project_id
        self.root_element_id = root_element_id
        self.view_id = view_id
        self.lock = RLock()
        self.saved = CompositionSession(project, view_id)
        self.opened = False

    def _target(self):
        parent = os.open(self.project.repository.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            try:
                return os.stat(self.project.repository.name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                return None
        finally:
            os.close(parent)

    def _git_markers(self):
        for name in ('HEAD', 'objects', 'refs', 'config'):
            try:
                (self.project.repository/name).lstat()
                return True
            except FileNotFoundError:
                pass
        return False

    def _request(self, request, *, checked=False):
        request = validate_checked_request(request) if checked else validate_request(request)
        if (request['project_id'] != self.project_id or request['root_element_id'] != self.root_element_id
                or request['view_id'] != self.view_id):
            raise EditError('authorization', 'The initial request cannot replace this session project, root or view')
        return request

    def state(self):
        with self.lock:
            current = None
            target = 'unavailable'
            try:
                entry = self._target()
            except OSError:
                entry = False
            if entry is None:
                target = 'absent'
            elif entry is not False:
                target = 'unavailable'
                if stat.S_ISDIR(entry.st_mode):
                    try:
                        if not self._git_markers():
                            target = 'occupied'
                            return self._initial_state(target, current)
                        history = self.project.history()
                        if history[0]['project_id'] == self.project_id:
                            current = {key: history[0][key] for key in ('revision', 'commit')}
                            target = 'saved_project'
                        else:
                            target = 'occupied'
                    except (ValueError, OSError, TypeError, RecursionError):
                        pass  # Unavailable history is not an absent/empty target.
                else:
                    target = 'occupied'
            return self._initial_state(target, current)

    def _initial_state(self, target, current):
        return {'phase': 'initial', 'project_id': self.project_id,
                    'root_element_id': self.root_element_id, 'view_id': self.view_id,
                    'revision': 0, 'projection': None, 'current_saved': current,
                    'target_observation': target,
                    'claim': 'prospective_initial_session_not_a_saved_model_or_reserved_target'}

    def preview(self, request):
        with self.lock:
            request = self._request(request)
            entry = self._target()
            if entry is not None:
                if not stat.S_ISDIR(entry.st_mode) or not self._git_markers():
                    raise EditError('project_exists', 'The target is an occupied entry; it was preserved')
                if request['expected_bundle_sha256'] is not None:
                    result = lookup(self.project.repository, request)
                    if result['receipt'] is not None:
                        raise EditError('already_applied', 'Initial request already has a saved receipt; recover and open it')
                # Require readable history before calling an existing project a
                # definite competing creation. I/O failure remains uncertain.
                self.project.history()
                raise EditError('project_exists', 'The target already contains a saved project; retain this initial draft')
            document, checked = prepare(request)
            drawing = render(document, self.view_id)
            spelling = {key: name_spelling(request[key]) if request[key] is not None else None
                        for key in ('new_name', 'short_id', 'namespace_name')}
            return {'base_revision': 0, 'base_commit': None,
                    'request': checked, 'request_sha256': request_digest(checked),
                    'candidate_bundle_sha256': document.revision,
                    'candidate': document.inspect(), 'registry': deepcopy(document.registry),
                    'files': deepcopy(document.files), 'linked_records': deepcopy(document.linked_records),
                    'candidate_svg': drawing['svg'],
                    'source_spelling': spelling,
                    'claim': 'unsaved_initial_candidate_not_a_transaction_receipt'}

    def receipt(self, request):
        with self.lock:
            return lookup(self.project.repository, self._request(request, checked=True))

    def apply(self, request):
        with self.lock:
            try:
                request = self._request(request, checked=True)
            except EditError as exc:
                exc.definitive_refusal = True
                raise
            try:
                _, receipt = initialize(self.project.repository, request)
            except (ValueError, OSError, TypeError, RecursionError) as exc:
                # Every error after dispatch retains the exact request unless
                # this same path proves its refusal or recovers its receipt.
                if getattr(exc, 'code', None) in ('project_exists', 'request_reuse'):
                    exc.definitive_refusal = True
                    raise
                try:
                    result = lookup(self.project.repository, request)
                    receipt = result['receipt']
                except (ValueError, OSError, TypeError, RecursionError):
                    receipt = None
                if receipt is None:
                    raise EditError('outcome_unknown', 'Initial creation is unconfirmed; recover or retry the exact checked request') from exc
            return {'receipt': receipt, 'startup_state': self.state()}

    def open_saved(self, request):
        with self.lock:
            observed = self.receipt(request)
            if observed['receipt'] is None:
                raise EditError('not_observed', 'The initial receipt has not been observed; retain and recover its exact request')
            result = self.saved.page_state()
            self._saved_identity(result['state'])
            self.opened = True
            return {'initial_receipt': observed['receipt'], **result}

    def _saved_identity(self, state):
        projection = state['projection']
        roots = [node for node in projection['nodes'].values() if node['level'] == 0]
        if (projection['project_id'] != self.project_id or projection['id'] != self.view_id
                or len(roots) != 1 or roots[0]['element_id'] != self.root_element_id):
            raise EditError('authorization', 'The saved project, root or view no longer matches this initial session')

    def authorize_saved(self):
        with self.lock:
            if not self.opened:
                raise EditError('authorization', 'Recover and open the matching first receipt before using this saved session')
            if self.project.history()[0]['project_id'] != self.project_id:
                raise EditError('authorization', 'The saved target does not match this granted project')
            self._saved_identity(self.saved.state())


class InitialCompositionHTTPServer(ThreadingHTTPServer):
    """Same private loopback boundary; startup and saved routes stay distinct."""
    daemon_threads = True
    # Same-origin tab recovery requires restarting on the selected port after
    # the sole listener closes. SO_REUSEPORT remains disabled: a live listener
    # still prevents another server from binding this address/port.
    allow_reuse_address = True

    def __init__(self, project, project_id, root_element_id, view_id, port=0):
        self.initial = InitialCompositionSession(project, project_id, root_element_id, view_id)
        self.session = self.initial.saved
        self.access = secrets.token_urlsafe(32)
        self.csrf = secrets.token_urlsafe(32)
        self.cookie_name = 'cse_' + secrets.token_hex(8)
        super().__init__(('127.0.0.1', port), InitialCompositionHandler)
        self.origin = 'http://127.0.0.1:' + str(self.server_port)


class InitialCompositionHandler(CompositionHandler):
    def _saved_grant(self):
        self.server.initial.authorize_saved()

    def do_GET(self):
        try:
            self._boundary()
            if self.path in ('/start', '/initial.js'):
                name = 'composition-initial.html' if self.path == '/start' else 'composition-initial.js'
                kind = 'text/html; charset=utf-8' if self.path == '/start' else 'text/javascript; charset=utf-8'
                return self._send(200, (Path(__file__).resolve().parents[1]/'web'/name).read_bytes(), kind)
            if self.path == '/startup/state':
                if not self._authorized():
                    raise EditError('authorization', 'Open the private local session link')
                return self._send(200, {'state': self.server.initial.state(), 'csrf': self.server.csrf})
            if self._authorized() and self.path not in ('/', '/app.js', '/site-tools.js'):
                self._saved_grant()
        except (ValueError, OSError, TypeError, RecursionError) as exc:
            return self._error(exc)
        return super().do_GET()

    def do_POST(self):
        try:
            if self.path.startswith('/startup/'):
                self._boundary()
                if self.headers.get('Origin') != self.server.origin:
                    raise EditError('origin', 'A same-origin request is required')
                body = self._body()
                if not self._authorized() or not secrets.compare_digest(self.headers.get('X-CSE-CSRF', ''), self.server.csrf):
                    raise EditError('authorization', 'Invalid local session')
                if self.path == '/startup/preview':
                    return self._send(200, {'preview': self.server.initial.preview(body)})
                if self.path == '/startup/apply':
                    return self._send(200, self.server.initial.apply(body))
                if self.path == '/startup/receipt':
                    return self._send(200, self.server.initial.receipt(body))
                if self.path == '/startup/open':
                    return self._send(200, self.server.initial.open_saved(body))
                return self._send(404, {'error': {'code': 'not_found', 'detail': 'Unknown startup route'}})
            if self._authorized() and self.path.startswith('/api/'):
                self._saved_grant()
        except (ValueError, OSError, TypeError, RecursionError) as exc:
            return self._error(exc)
        return super().do_POST()
