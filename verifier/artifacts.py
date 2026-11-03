"""Bounded freshness receipts for declared files; no generator or model code runs."""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re

from .core import ID, _pairs
from .foundation import read_regular

VERSION = 'artifact-bundle-1.0'
LIMITS = {'record_bytes': 262144, 'files': 128, 'file_bytes': 33554432,
          'total_bytes': 134217728, 'path_characters': 512}
CLAIM = 'declared_file_freshness_only'
HASH = re.compile(r'^[0-9a-f]{64}$')


class Invalid(ValueError):
    pass


def load(path):
    raw = read_regular(path, LIMITS['record_bytes'])
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(Invalid('Nonfinite JSON value')))
    except (UnicodeError, RecursionError) as exc:
        raise Invalid('Invalid UTF-8 or excessive JSON nesting') from exc
    return value, sha256(raw).hexdigest()


def _object(value, fields, where):
    if type(value) is not dict or set(value) != set(fields):
        raise Invalid(where + ' needs exactly the documented fields')


def _hash(value):
    if type(value) is not str or not HASH.fullmatch(value):
        raise Invalid('Expected a lowercase SHA-256 digest')


def validate_plan(plan):
    _object(plan, ('version', 'id', 'revision', 'inputs', 'outputs'), 'plan')
    if plan['version'] != VERSION:
        raise Invalid('Unsupported artifact plan version')
    if type(plan['id']) is not str or not ID.fullmatch(plan['id']):
        raise Invalid('Plan needs an engineering identifier')
    if type(plan['revision']) is not str or not 1 <= len(plan['revision'].strip()) <= 128:
        raise Invalid('Plan needs a bounded revision')
    paths, ids = set(), set()
    for group in ('inputs', 'outputs'):
        entries = plan[group]
        if type(entries) is not dict or not 1 <= len(entries) <= LIMITS['files']:
            raise Invalid(group + ' needs a nonempty bounded ID-to-path map')
        for key, path in entries.items():
            if type(key) is not str or not ID.fullmatch(key) or key in ids:
                raise Invalid('File IDs must be valid and unique across the plan')
            ids.add(key)
            if (type(path) is not str or not 1 <= len(path) <= LIMITS['path_characters'] or
                    any(ord(c) < 32 for c in path) or '\\' in path or ':' in path):
                raise Invalid('Use a bounded relative POSIX path')
            parts = PurePosixPath(path)
            if parts.is_absolute() or '..' in parts.parts or path != parts.as_posix() or path == '.':
                raise Invalid('Paths must be relative, normalized and within the project root')
            if path in paths:
                raise Invalid('An input/output path must occur only once')
            paths.add(path)
    if len(paths) > LIMITS['files']:
        raise Invalid('Plan exceeds total file limit')


def _path(root, name):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise Invalid('Artifact root must be a directory')
    target = root
    for part in PurePosixPath(name).parts:
        target = target / part
        if target.is_symlink():
            raise Invalid('Symlink artifact paths are unsupported: ' + name)
    return target


def snapshot(root, entries):
    result, total = {}, 0
    for key, name in sorted(entries.items()):
        path = _path(root, name)
        before = path.stat()
        raw = read_regular(path, LIMITS['file_bytes'])
        after = _path(root, name).stat()
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if identity(before) != identity(after):
            raise Invalid('File changed while reading: ' + name)
        if not raw:
            raise Invalid('Artifact files must be nonempty: ' + name)
        total += len(raw)
        if total > LIMITS['total_bytes']:
            raise Invalid('Artifacts exceed total byte limit')
        result[key] = {'path': name, 'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)}
    return result


def _receipt(plan, digest, phase, inputs, outputs):
    return {'version': VERSION, 'phase': phase, 'claim_scope': CLAIM,
            'id': plan['id'], 'revision': plan['revision'], 'plan_sha256': digest,
            'inputs': inputs, 'outputs': outputs}


def begin(root, plan, plan_sha256):
    """Capture sources before generation. Declared outputs must not yet exist."""
    validate_plan(plan)
    _hash(plan_sha256)
    inputs = snapshot(root, plan['inputs'])
    for name in plan['outputs'].values():
        if _path(root, name).exists():
            raise Invalid('Output already exists; use a fresh run path: ' + name)
    return _receipt(plan, plan_sha256, 'started', inputs, {})


def _validate_receipt(plan, plan_sha256, receipt, phase):
    _hash(plan_sha256)
    _object(receipt, ('version', 'phase', 'claim_scope', 'id', 'revision',
                      'plan_sha256', 'inputs', 'outputs'), 'receipt')
    if any(receipt[key] != value for key, value in
           {'version': VERSION, 'phase': phase, 'claim_scope': CLAIM, 'id': plan['id'],
            'revision': plan['revision'], 'plan_sha256': plan_sha256}.items()):
        raise Invalid('Receipt identity, phase or retained plan does not match')
    for group in ('inputs', 'outputs'):
        expected = {} if group == 'outputs' and phase == 'started' else plan[group]
        actual = receipt[group]
        if type(actual) is not dict or set(actual) != set(expected):
            raise Invalid('Receipt omits or adds declared ' + group)
        for key, entry in actual.items():
            _object(entry, ('path', 'sha256', 'bytes'), 'file receipt')
            _hash(entry['sha256'])
            if (entry['path'] != expected[key] or type(entry['bytes']) is not int or
                    not 1 <= entry['bytes'] <= LIMITS['file_bytes']):
                raise Invalid('File receipt path or byte count does not match the contract')


def finish(root, plan, plan_sha256, started):
    """Bind newly produced outputs only when the captured sources still match."""
    validate_plan(plan)
    _validate_receipt(plan, plan_sha256, started, 'started')
    inputs = snapshot(root, plan['inputs'])
    if inputs != started['inputs']:
        raise Invalid('Source changed since generation began')
    outputs = snapshot(root, plan['outputs'])
    if sum(x['bytes'] for x in (*inputs.values(), *outputs.values())) > LIMITS['total_bytes']:
        raise Invalid('Artifacts exceed total byte limit')
    if snapshot(root, plan['inputs']) != inputs:
        raise Invalid('Source changed while capturing outputs')
    return _receipt(plan, plan_sha256, 'complete', inputs, outputs)


def check(root, plan, plan_sha256, receipt):
    """Read-only freshness check against the separately retained file scope."""
    validate_plan(plan)
    _validate_receipt(plan, plan_sha256, receipt, 'complete')
    for group in ('inputs', 'outputs'):
        if snapshot(root, plan[group]) != receipt[group]:
            raise Invalid('Stale or altered artifact ' + group)
    if sum(x['bytes'] for group in ('inputs', 'outputs') for x in receipt[group].values()) > LIMITS['total_bytes']:
        raise Invalid('Artifacts exceed total byte limit')
    if snapshot(root, plan['inputs']) != receipt['inputs']:
        raise Invalid('Source changed while checking outputs')
    return {'status': 'pass', 'version': VERSION, 'claim_scope': CLAIM,
            'plan_sha256': plan_sha256, 'checked_inputs': sorted(plan['inputs']),
            'checked_outputs': sorted(plan['outputs'])}
