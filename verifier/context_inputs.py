"""Parse captured model bytes without reopening their original paths.

This is local snapshot and provenance handling, not a protected execution
boundary. The caller separately checks whether its original inputs drifted.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import tempfile

from .foundation import Invalid, read_regular
from .sysml import CACHE
from .workflow import _model_digest, _model_label

MODEL_BYTE_CAP = 5_000_000


def parse_captured(captured, files, model_digest, *, parser):
    """Parse a ``capture_model_inputs`` result and restore original provenance.

    The explicit parser receives private snapshot paths. Its reported digest
    must identify those snapshots; multi-file digests also include their paths.
    Snapshot failures raise an input error, while native parser failures retain
    their findings and diagnostics with original source labels.
    """
    if (type(captured) not in (list, tuple) or not 1 <= len(captured) <= 128
            or type(files) not in (list, tuple) or len(files) != len(captured)):
        raise Invalid('Expected one bounded captured model set and matching file provenance')
    files = deepcopy(list(files))
    total = 0
    for capture, entry in zip(captured, files):
        if (type(capture) not in (list, tuple) or len(capture) != 2
                or type(capture[1]) is not bytes
                or type(entry) is not dict or set(entry) != {'path', 'sha256'}
                or type(entry['path']) is not str or not entry['path']):
            raise Invalid('Malformed captured model bytes or file provenance')
        raw = capture[1]
        total += len(raw)
        if total > MODEL_BYTE_CAP:
            raise Invalid('Combined captured SysML model exceeds 5 MB')
        if sha256(raw).hexdigest() != entry['sha256']:
            raise Invalid('Captured model bytes differ from file provenance')
    if (len({entry['path'] for entry in files}) != len(files)
            or _model_digest(files) != model_digest):
        raise Invalid('Captured model aggregate identity differs from file provenance')

    directory = CACHE / 'context-scratch'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.is_symlink():
        raise Invalid('Context scratch directory must not be a symlink')
    with tempfile.TemporaryDirectory(prefix='context-', dir=directory) as temporary:
        snapshots, snapshot_files, source_map = [], [], {}
        for index, (capture, entry) in enumerate(zip(captured, files)):
            snapshot = Path(temporary) / f'{index:03d}.sysml'
            snapshot.write_bytes(capture[1])
            snapshot.chmod(0o600)
            snapshots.append(snapshot)
            label = _model_label(snapshot)
            snapshot_files.append({'path': label, 'sha256': entry['sha256']})
            source_map[label] = entry['path']
        native = parser(snapshots[0] if len(snapshots) == 1 else snapshots,
                        syntax_only=True, kind=None)
        if type(native) is not dict or native.get('model_sha256') != _model_digest(snapshot_files):
            raise Invalid('Parsed native snapshot revision differs from captured inputs')
        if any(read_regular(snapshot, MODEL_BYTE_CAP) != capture[1]
               for snapshot, capture in zip(snapshots, captured)):
            raise Invalid('Native snapshot bytes changed during parsing')

    native = deepcopy(native)
    native['snapshot_sha256'] = native['model_sha256']
    native['model_sha256'] = model_digest
    native['model_files'] = files
    records = [item for group in native.get('inventory', {}).values() for item in group]
    records.extend(native.get('findings', []))
    records.extend(native.get('parser_issues', []))
    for item in records:
        if item.get('source') in source_map:
            item['source'] = source_map[item['source']]
    return native
