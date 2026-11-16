"""Local Git transaction reference for the physical-composition capability.

Only inspect, rename and restoration of this capability's snapshots are admitted.
The bare repository is a trusted server-side location, never a client filename.
This is not the Cloudflare coordinator or an authenticated application adapter.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from uuid import UUID

from .composition_edit import CompositionDocument, EditError, project_name
from .core import _pairs


REF = 'refs/heads/main'
OID = re.compile(r'[0-9a-f]{40}\Z')
MAX_HISTORY = 10_000


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def request_digest(request):
    return sha256(encoded(request)).hexdigest()


def json_object(raw):
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
        if not isinstance(value, dict):
            raise ValueError('Expected object')
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise EditError('storage_integrity', 'Invalid project metadata') from exc


class CompositionProject:
    """One immutable commit per successful operation; one atomic published head."""

    def __init__(self, repository):
        self.repository = Path(repository).absolute()

    def _git(self, *args, data=None, check=True):
        # Do not inherit an unrelated checkout/index/config injection. No hooks,
        # replacement objects, external diff, shell command or model code runs.
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
                   GIT_AUTHOR_NAME='CSE local project store',
                   GIT_AUTHOR_EMAIL='cse-local@invalid',
                   GIT_COMMITTER_NAME='CSE local project store',
                   GIT_COMMITTER_EMAIL='cse-local@invalid', LC_ALL='C')
        try:
            result = subprocess.run(
                ['git', '--no-replace-objects', '--git-dir', str(self.repository),
                 '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
                 '-c', 'core.fsync=all', '-c', 'core.fsyncMethod=fsync',
                 *args], input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, timeout=20)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise EditError('storage', 'Git operation unavailable or timed out') from exc
        if check and result.returncode:
            raise EditError('storage', result.stderr.decode('utf-8', errors='replace')[:1000])
        return result

    def head(self):
        result = self._git('rev-parse', '--verify', REF, check=False)
        value = result.stdout.decode().strip()
        if result.returncode or not OID.fullmatch(value):
            raise EditError('storage', 'Project has no readable published head')
        return value

    def _blob(self, oid, cap):
        if not isinstance(oid, str) or not OID.fullmatch(oid):
            raise EditError('storage_integrity', 'Invalid object identity')
        size = self._git('cat-file', '-s', oid).stdout.strip()
        if not size.isdigit() or int(size) > cap:
            raise EditError('storage_integrity', 'Project object exceeds its limit')
        raw = self._git('cat-file', 'blob', oid).stdout
        if len(raw) != int(size):
            raise EditError('storage_integrity', 'Object size mismatch')
        return raw

    def _tree(self, commit):
        if not OID.fullmatch(commit):
            raise EditError('storage_integrity', 'Invalid commit identity')
        result = {}
        for entry in self._git('ls-tree', '-r', '-z', commit).stdout.split(b'\0'):
            if not entry:
                continue
            header, name = entry.split(b'\t', 1)
            mode, kind, oid = header.decode().split(' ')
            name = name.decode('utf-8')
            if mode != '100644' or kind != 'blob' or name in result:
                raise EditError('storage_integrity', 'Unexpected project tree entry')
            result[name] = oid
        return result

    def _metadata(self, commit):
        tree = self._tree(commit)
        if 'cse/state.json' not in tree:
            raise EditError('storage_integrity', 'Project manifest missing')
        state = json_object(self._blob(tree['cse/state.json'], 2_000_000))
        if (set(state) != {'version', 'project_id', 'revision', 'models', 'linked_records', 'registry', 'receipt'}
                or state['version'] != 'cse-composition-project-1'
                or type(state['revision']) is not int or not 1 <= state['revision'] <= MAX_HISTORY
                or not isinstance(state['models'], dict) or not isinstance(state['linked_records'], dict)
                or not 1 <= len(state['models']) + len(state['linked_records']) <= 128
                or not state['models'] or not isinstance(state['registry'], dict)
                or not isinstance(state['receipt'], dict)):
            raise EditError('storage_integrity', 'Invalid project state')
        try:
            UUID(state['project_id'])
        except (ValueError, TypeError, AttributeError) as exc:
            raise EditError('storage_integrity', 'Invalid project identity') from exc
        expected = {'cse/state.json'}
        for group, folder in [('models', 'models'), ('linked_records', 'linked')]:
            for name, item in state[group].items():
                project_name(name)
                fields = {'sha256'} if group == 'models' else {'sha256', 'kind'}
                if (not isinstance(item, dict) or set(item) != fields
                        or not isinstance(item['sha256'], str)
                        or not re.fullmatch('[0-9a-f]{64}', item['sha256'])):
                    raise EditError('storage_integrity', 'Invalid file manifest')
                expected.add(folder + '/' + name)
        if set(tree) != expected:
            raise EditError('storage_integrity', 'Project tree and manifest disagree')
        receipt = state['receipt']
        if (set(receipt) != {'project_id', 'request_id', 'request_sha256', 'revision', 'operation',
                             'bundle_sha256', 'parent_commit', 'restored_from_revision', 'storage'}
                or receipt.get('revision') != state['revision'] or receipt.get('project_id') != state['project_id']
                or receipt.get('storage') != 'local_git_fsync'
                or receipt.get('operation') not in ('import', 'rename', 'restore')
                or not re.fullmatch('[0-9a-f]{64}', str(receipt.get('request_sha256')))
                or not re.fullmatch('[0-9a-f]{64}', str(receipt.get('bundle_sha256')))
                or receipt.get('parent_commit') is not None and not OID.fullmatch(str(receipt['parent_commit']))):
            raise EditError('storage_integrity', 'Receipt and state disagree')
        self._request_id(receipt['request_id'])
        if (receipt['operation'] == 'import') != (state['revision'] == 1):
            raise EditError('storage_integrity', 'Import is not the initial revision')
        restored = receipt['restored_from_revision']
        if ((receipt['operation'] == 'restore' and (type(restored) is not int or not 1 <= restored < state['revision']))
                or receipt['operation'] != 'restore' and restored is not None):
            raise EditError('storage_integrity', 'Invalid restoration receipt')
        return state, tree

    def _load(self, commit):
        state, tree = self._metadata(commit)
        files, linked = {}, {}
        for group, folder, target in [('models', 'models', files), ('linked_records', 'linked', linked)]:
            for name, item in state[group].items():
                raw = self._blob(tree[folder + '/' + name], 5_000_000)
                if sha256(raw).hexdigest() != item['sha256']:
                    raise EditError('storage_integrity', 'Source bytes and manifest disagree')
                try:
                    text = raw.decode('utf-8')
                except UnicodeError as exc:
                    raise EditError('storage_integrity', 'Invalid UTF-8 project file') from exc
                target[name] = text if group == 'models' else {'kind': item['kind'], 'text': text}
        document = CompositionDocument(files, project_id=state['project_id'],
                                       registry=state['registry'], linked_records=linked)
        if document.revision != state['receipt'].get('bundle_sha256'):
            raise EditError('storage_integrity', 'Project bundle digest disagrees')
        return state, document

    def snapshot(self):
        commit = self.head()
        self._history(commit)
        state, document = self._load(commit)
        return {'commit': commit, 'revision': state['revision'], 'document': document,
                'receipt': {**deepcopy(state['receipt']), 'commit': commit}}

    def _history(self, head):
        commits = self._git('rev-list', '--first-parent', '--max-count=' + str(MAX_HISTORY + 1), head).stdout.decode().splitlines()
        if not 1 <= len(commits) <= MAX_HISTORY:
            raise EditError('storage_integrity', 'Project history exceeds its current limit')
        result = []
        project = None
        for revision, commit in zip(range(len(commits), 0, -1), commits):
            state, _ = self._metadata(commit)
            project = project or state['project_id']
            if (state['revision'] != revision or state['project_id'] != project
                    or state['receipt'].get('parent_commit') != (commits[len(commits)-revision+1] if revision > 1 else None)):
                raise EditError('storage_integrity', 'Non-monotonic or disconnected project history')
            result.append({**deepcopy(state['receipt']), 'commit': commit})
        return result

    def history(self):
        return self._history(self.head())

    def _retry(self, history, request):
        digest = request_digest(request)
        matches = [row for row in history if row['request_id'] == request['request_id']]
        if len(matches) > 1:
            raise EditError('storage_integrity', 'Duplicate request in published history')
        if matches:
            if matches[0]['request_sha256'] != digest:
                raise EditError('request_reuse', 'Request ID already belongs to a different operation')
            return matches[0]
        return None

    def _write_tree(self, files):
        root = {}
        for name, raw in sorted(files.items()):
            node = root
            parts = name.split('/')
            for part in parts[:-1]:
                node = node.setdefault(part, {})
                if not isinstance(node, dict):
                    raise EditError('file_name', 'A file path is also used as a directory')
            if parts[-1] in node:
                raise EditError('file_name', 'A file path is also used as a directory')
            node[parts[-1]] = self._git('hash-object', '-w', '--stdin', data=raw).stdout.strip()

        def tree(node):
            rows = []
            for name, value in sorted(node.items()):
                header = b'040000 tree ' + tree(value) if isinstance(value, dict) else b'100644 blob ' + value
                rows.append(header + b'\t' + name.encode('utf-8') + b'\0')
            return self._git('mktree', '-z', data=b''.join(rows)).stdout.strip()
        return tree(root).decode()

    def _publish(self, commit, previous):
        result = self._git('update-ref', '-m', 'CSE composition transaction', REF, commit,
                           previous or '0' * 40, check=False)
        if result.returncode:
            # A concurrent winner is a conflict; other failures stay errors.
            if self.head() != previous:
                raise EditError('stale_revision', 'Another project operation committed first')
            raise EditError('storage', 'Project head was not published')

    def _commit(self, document, request, revision, previous, restored_from=None):
        receipt = {'project_id': document.project_id, 'request_id': request['request_id'],
                   'request_sha256': request_digest(request), 'revision': revision,
                   'operation': request['operation'], 'bundle_sha256': document.revision,
                   'parent_commit': previous, 'restored_from_revision': restored_from,
                   'storage': 'local_git_fsync'}
        state = {'version': 'cse-composition-project-1', 'project_id': document.project_id,
                 'revision': revision, 'models': {}, 'linked_records': {},
                 'registry': document.registry, 'receipt': receipt}
        files = {}
        for name, text in document.files.items():
            raw = text.encode('utf-8')
            files['models/' + name] = raw
            state['models'][name] = {'sha256': sha256(raw).hexdigest()}
        for name, record in document.linked_records.items():
            raw = record['text'].encode('utf-8')
            files['linked/' + name] = raw
            state['linked_records'][name] = {'kind': record['kind'], 'sha256': sha256(raw).hexdigest()}
        raw = encoded(state)
        if len(raw) > 2_000_000:
            raise EditError('input', 'Project metadata exceeds its current 2 MB limit')
        files['cse/state.json'] = raw
        tree = self._write_tree(files)
        args = ['commit-tree', tree]
        if previous:
            args += ['-p', previous]
        commit = self._git(*args, data=('CSE composition ' + request['operation'] + '\n').encode()).stdout.decode().strip()
        self._publish(commit, previous)
        return {**receipt, 'commit': commit}

    @staticmethod
    def _request_id(value):
        try:
            if not isinstance(value, str) or str(UUID(value)) != value:
                raise ValueError('Noncanonical UUID')
        except (ValueError, AttributeError) as exc:
            raise EditError('request_id', 'Use a canonical request UUID') from exc

    @classmethod
    def create(cls, repository, models, *, project_id, request_id, linked_records=None):
        cls._request_id(request_id)
        cls._request_id(project_id)
        if not isinstance(models, dict) or linked_records is not None and not isinstance(linked_records, dict):
            raise EditError('input', 'Project import requires explicit model and linked-record maps')
        request = {'operation': 'import', 'request_id': request_id, 'project_id': project_id,
                   'models': models, 'linked_records': linked_records or {}}
        project = cls(repository)
        if project.repository.exists():
            receipt = project._retry(project.history(), request)
            if receipt:
                return project, receipt
            raise EditError('project_exists', 'Selected project location already exists')
        document = CompositionDocument(models, project_id=project_id, linked_records=linked_records)
        for names in (document.files, document.linked_records):
            for name in names:
                if any('/'.join(name.split('/')[:i]) in names for i in range(1, len(name.split('/')))):
                    raise EditError('file_name', 'A file path is also used as a directory')
        project.repository.mkdir(mode=0o700, parents=True, exist_ok=False)
        project._git('init', '--bare', '--object-format=sha1', '--initial-branch=main', str(project.repository))
        # Make the new directory entry durable before the first published head.
        fd = os.open(project.repository.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        return project, project._commit(document, request, 1, None)

    def transact(self, request):
        if not isinstance(request, dict):
            raise EditError('input', 'Supply a typed composition operation')
        common = {'operation', 'request_id', 'expected_revision'}
        fields = {'rename': {'element_id', 'new_name'}, 'restore': {'target_revision'}}
        operation = request.get('operation')
        if not isinstance(operation, str) or operation not in fields or set(request) != common | fields[operation]:
            raise EditError('input', 'Unknown composition operation or fields')
        self._request_id(request['request_id'])
        if type(request['expected_revision']) is not int or not 1 <= request['expected_revision'] < MAX_HISTORY:
            raise EditError('input', 'Expected revision is outside the current history limit')
        if operation == 'rename' and (not isinstance(request['element_id'], str) or not isinstance(request['new_name'], str)):
            raise EditError('input', 'Rename requires an element UUID and a declared name')
        if operation == 'restore' and type(request['target_revision']) is not int:
            raise EditError('input', 'Restore requires an integer revision')
        previous = self.head()
        history = self._history(previous)
        retried = self._retry(history, request)
        if retried:
            return retried
        state, document = self._load(previous)
        if state['revision'] != request['expected_revision']:
            raise EditError('stale_revision', 'Project changed; inspect current state before preparing another operation')
        restored = None
        if operation == 'rename':
            document = document.rename(request['element_id'], request['new_name'],
                                       expected_source_sha256=document.revision)
        else:
            restored = request['target_revision']
            if type(restored) is not int or not 1 <= restored <= state['revision']:
                raise EditError('input', 'Restore must select a published revision of this project')
            target = next(row for row in history if row['revision'] == restored)
            _, document = self._load(target['commit'])
        try:
            return self._commit(document, request, state['revision'] + 1, previous, restored)
        except EditError as exc:
            if exc.code == 'stale_revision':
                retried = self._retry(self.history(), request)
                if retried:
                    return retried
            raise
