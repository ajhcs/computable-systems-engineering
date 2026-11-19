"""One native physical root and its original-kit view, before any saved revision.

This builder does not publish storage, infer retained configuration or establish
engineering acceptance. Every application adapter must use this same boundary.
"""
from copy import deepcopy
import ctypes
import errno
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
from uuid import UUID

from .composition_edit import CompositionDocument, EditError, name_spelling, validate_name
from .composition_records import embedded_json
from .composition_view import ID, render
from . import composition_fonts as kit_fonts


OPERATION = 'initialize_physical_project'
FIELDS = {'operation', 'request_id', 'project_id', 'expected_revision',
          'root_element_id', 'root_kind', 'new_name', 'short_id',
          'namespace_name', 'view_id', 'expected_bundle_sha256'}


def validate_request(request):
    """Validate the retained typed intent without invoking the source generator.

    An exact receipt retry must not regenerate sources using a newer generator.
    """
    if not isinstance(request, dict) or set(request) != FIELDS or request.get('operation') != OPERATION:
        raise EditError('input', 'Supply the complete typed initial physical-project request')
    for key in ('project_id', 'request_id', 'root_element_id'):
        value = request[key]
        try:
            if not isinstance(value, str) or str(UUID(value)) != value:
                raise ValueError('Noncanonical UUID')
        except (ValueError, AttributeError) as exc:
            raise EditError('identity', 'Initial project, request and root identities must be canonical UUIDs') from exc
    if request['root_element_id'] in (request['project_id'], request['request_id']):
        raise EditError('identity', 'Use a distinct prospective engineering root UUID')
    if type(request['expected_revision']) is not int or request['expected_revision'] != 0:
        raise EditError('stale_revision', 'Initial creation requires expected revision zero')
    if not isinstance(request['root_kind'], str) or request['root_kind'] not in ('definition', 'usage'):
        raise EditError('input', 'Choose a native part definition or namespace/package-owned part usage')
    validate_name(request['new_name'])
    for key in ('short_id', 'namespace_name'):
        if request[key] is not None:
            validate_name(request[key])
    if not isinstance(request['view_id'], str) or not ID.fullmatch(request['view_id']):
        raise EditError('input', 'Supply the granted physical view identity')
    digest = request['expected_bundle_sha256']
    if digest is not None and (not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest)):
        raise EditError('input', 'Use null before preview or the exact checked candidate bundle digest')
    return deepcopy(request)


def document_for(request):
    """Serialize native names, parse the whole bundle and check exact root facts."""
    request = validate_request(request)
    try:
        for key in ('new_name', 'short_id', 'namespace_name'):
            if request[key] is not None:
                kit_fonts.require_supported_text(request[key])
    except ValueError as exc:
        raise EditError('presentation_conflict', str(exc)) from exc
    name = name_spelling(request['new_name'])
    package = name_spelling(request['namespace_name']) if request['namespace_name'] is not None else None
    short = name_spelling(request['short_id']) if request['short_id'] is not None else None
    qualified = (package['qualified_segment'] + '::' if package else '') + name['qualified_segment']
    declaration = ('part def ' if request['root_kind'] == 'definition' else 'part ')
    if short:
        declaration += '<' + short['source_token'] + '> '
    declaration += name['source_token'] + ';\n'
    model = ('package ' + package['source_token'] + ' {\n' + declaration + '}\n') if package else declaration
    # The existing view contract requires package ownership. It never creates a
    # physical owner or rewrites a global root into a model package.
    metadata = 'CSE_Views_' + request['project_id'].replace('-', '')
    reserved = {request['namespace_name']} if package else {request['new_name'], request['short_id']}
    base, suffix = metadata, 0
    while metadata in reserved:
        suffix += 1
        metadata = base + '_' + str(suffix)
    occurrence = 'N' + request['root_element_id'].replace('-', '')
    view = {'views': [{'id': request['view_id'], 'kind': 'physical_composition',
                      'mode': 'definitions' if request['root_kind'] == 'definition' else 'usages',
                      'nodes': [{'id': occurrence, 'element': qualified,
                                 'parent': None, 'level': 0, 'edge': None}]}]}
    views = ('package ' + name_spelling(metadata)['source_token'] + ' {\n'
             ' doc cseViews /* CSE-VIEWS/1.1\n' + embedded_json(view, indent=2) + '\n*/\n}\n')
    document = CompositionDocument({'model.sysml': model, 'views.sysml': views},
        project_id=request['project_id'], registry={request['root_element_id']: qualified})
    rows = document.inspect()['elements']
    expected_kind = 'part_definitions' if request['root_kind'] == 'definition' else 'parts'
    if (len(rows) != 1 or rows[0]['kind'] != expected_kind
            or rows[0]['element_id'] != request['root_element_id']
            or rows[0]['name'] != request['new_name'] or rows[0].get('id') != request['short_id']
            or rows[0]['qualified_name'] != qualified
            or rows[0].get('owner') != (package['qualified_segment'] if package else None)
            or rows[0].get('owner_kind') != ('Package' if package else 'Namespace')
            or rows[0].get('is_variation') is not False
            or rows[0]['source_location']['file'] != 'model.sysml'
            or document.configuration_reviews or document.linked_records):
        raise EditError('native_correspondence', 'Native initial root differs from the requested declaration')
    native = rows[0]
    if request['root_kind'] == 'usage':
        if (native.get('is_composite') is not False or native.get('nested') is not False
                or native.get('types') != [] or native.get('redefines') != [] or native.get('subsets') != []
                or native.get('multiplicity') != {'status': 'default', 'lower': 1, 'upper': 1}
                or native.get('has_native_value') is not False
                or native.get('has_non_typing_specialization') is not False):
            raise EditError('native_correspondence', 'Native root usage differs from untyped default 1..1 with no physical owner')
    elif native.get('supertypes') != [] or native.get('has_specialization') is not False:
        raise EditError('native_correspondence', 'Native root definition unexpectedly specializes another type')
    try:
        drawing = render(document, request['view_id'])
    except ValueError as exc:
        raise EditError('presentation_conflict', str(exc)) from exc
    projection = drawing['projection']
    if set(projection['nodes']) != {occurrence} or projection['edges']:
        raise EditError('native_correspondence', 'Initial physical view must contain exactly the requested root and no ownership edge')
    if request['expected_bundle_sha256'] is not None and document.revision != request['expected_bundle_sha256']:
        raise EditError('candidate_changed', 'Initial source differs from the checked candidate; retain the draft and preview again')
    return document


def prepare(request):
    """Bind the candidate's exact bytes to the request used for first save."""
    request = validate_request(request)
    document = document_for(request)
    request['expected_bundle_sha256'] = document.revision
    return document, request


def validate_checked_request(request):
    request = validate_request(request)
    if request['expected_bundle_sha256'] is None:
        raise EditError('preview_required', 'Preview the initial model and retain its checked bundle digest before creating or recovering it')
    return request


def _fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_tree(path):
    """Flush every created Git file and directory, including init metadata."""
    for child in path.iterdir():
        mode = child.lstat().st_mode
        if stat.S_ISDIR(mode):
            _fsync_tree(child)
        elif stat.S_ISREG(mode):
            fd = os.open(child, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        else:
            raise EditError('storage', 'Initial staging contains an unexpected nonregular Git entry')
    _fsync_directory(path)


def _rename_noreplace(source, destination):
    """Qualified Linux atomic directory publication; never replace an entry.

    os.rename can replace an unrelated empty directory. Do not silently fall
    back to it, an existence check plus rename, or cross-filesystem copying.
    """
    try:
        function = ctypes.CDLL(None, use_errno=True).renameat2
    except (OSError, AttributeError) as exc:
        raise EditError('storage_unsupported', 'Atomic no-replace project publication is unavailable') from exc
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    if function(-100, os.fsencode(source), -100, os.fsencode(destination), 1):
        code = ctypes.get_errno()
        if code == errno.EEXIST:
            raise FileExistsError(code, os.strerror(code), str(destination))
        if code in (errno.ENOSYS, errno.EINVAL, errno.ENOTSUP, errno.EXDEV):
            raise EditError('storage_unsupported', 'The selected filesystem does not support atomic no-replace publication')
        raise OSError(code, os.strerror(code), str(destination))


def _existing_receipt(project, request):
    if not project.repository.is_dir() or project.repository.is_symlink():
        raise EditError('project_exists', 'Selected project target already exists; it was preserved')
    has_git_marker = False
    for name in ('HEAD', 'objects', 'refs', 'config'):
        try:
            (project.repository/name).lstat()
            has_git_marker = True
            break
        except FileNotFoundError:
            pass
    if not has_git_marker:
        raise EditError('project_exists', 'Selected target is an unrelated directory; it was preserved')
    history = project.history()  # Unreadable/corrupt/timeout remains unconfirmed.
    receipt = project._retry(history, request)
    if receipt is None:
        raise EditError('project_exists', 'Selected project belongs to another creation request; it was preserved')
    _verify_initial_receipt(project, receipt, request)
    # A previous process may have published the name and died or failed during
    # the parent flush. Visible matching objects alone cannot acknowledge it.
    _fsync_directory(project.repository.parent)
    return receipt


def _verify_initial_receipt(project, receipt, request):
    """Read the immutable checked bytes without rerunning a source generator.

    Metadata/history visibility alone does not establish source availability.
    This is storage verification, not a new native or engineering verdict.
    """
    state, tree = project._metadata(receipt['commit'])
    if (state['revision'] != 1 or state['project_id'] != request['project_id']
            or state['receipt']['request_sha256'] != receipt['request_sha256']
            or set(state['models']) != {'model.sysml', 'views.sysml'} or state['linked_records']
            or set(state['registry']) != {request['root_element_id']}
            or not isinstance(state['registry'][request['root_element_id']], str)):
        raise EditError('storage_integrity', 'Initial receipt and committed model bindings disagree')
    manifest = []
    total = 0
    for name, item in sorted(state['models'].items()):
        raw = project._blob(tree['models/' + name], 5_000_000)
        total += len(raw)
        try:
            raw.decode('utf-8')
        except UnicodeError as exc:
            raise EditError('storage_integrity', 'Initial source is not UTF-8') from exc
        digest = sha256(raw).hexdigest()
        if digest != item['sha256'] or total > 5_000_000:
            raise EditError('storage_integrity', 'Initial source bytes and manifest disagree')
        manifest.append({'path': name, 'sha256': digest})
    digest = sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if digest != receipt['bundle_sha256'] or digest != request['expected_bundle_sha256']:
        raise EditError('storage_integrity', 'Initial stored bundle differs from the checked candidate')


def lookup(repository, request):
    """Observe an exact initial receipt or an unreserved revision-zero absence."""
    from .composition_project import CompositionProject, request_digest
    request = validate_checked_request(request)
    project = CompositionProject(repository)
    parent = os.open(project.repository.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        try:
            os.stat(project.repository.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return {'observed_commit': None, 'observed_revision': 0,
                    'request_sha256': request_digest(request), 'receipt': None}
    finally:
        os.close(parent)
    if not project.repository.is_dir() or project.repository.is_symlink():
        raise EditError('project_exists', 'Selected target already exists; it was preserved')
    history = project.history()
    if history[0]['project_id'] != request['project_id']:
        raise EditError('project_exists', 'Selected target belongs to another project')
    receipt = project._retry(history, request)
    if receipt is not None:
        _verify_initial_receipt(project, receipt, request)
        _fsync_directory(project.repository.parent)
    return {'observed_commit': history[0]['commit'], 'observed_revision': history[0]['revision'],
            'request_sha256': request_digest(request), 'receipt': receipt}


def initialize(repository, request):
    """Atomically publish exactly one initial native project, or recover it.

    `repository` is a trusted operator-selected location. It is not a filename
    supplied by an untrusted application caller. Its parent must already exist.
    """
    from .composition_project import CompositionProject
    request = validate_checked_request(request)
    project = CompositionProject(repository)
    _fsync_directory(project.repository.parent)  # Preflight before any staging/publication.
    if os.path.lexists(project.repository):
        return project, _existing_receipt(project, request)
    document = document_for(request)
    if not project.repository.parent.is_dir():
        raise EditError('storage', 'Select an existing trusted parent directory for the new project')
    staging = Path(tempfile.mkdtemp(prefix='.cse-initial-', dir=project.repository.parent))
    attempt = CompositionProject(staging)
    published = False
    try:
        attempt._git('init', '--bare', '--object-format=sha1', '--initial-branch=main', str(staging))
        receipt = attempt._commit(document, request, 1, None)
        _verify_initial_receipt(attempt, receipt, request)
        _fsync_tree(staging)
        try:
            _rename_noreplace(staging, project.repository)
        except FileExistsError:
            return project, _existing_receipt(project, request)
        published = True
        _fsync_directory(project.repository.parent)
        return project, receipt
    finally:
        # Only this call's private, unpublished staging directory is removable.
        # A killed process can leave its attempt for inspection; no glob scan,
        # adoption, rollback or deletion of authoritative/user storage occurs.
        if not published and staging.exists():
            shutil.rmtree(staging)
