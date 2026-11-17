"""Real Git/process/race controls for the composition rename transaction."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Barrier
import unittest
from unittest.mock import patch
from uuid import uuid4, uuid5, UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import EditError
from verifier.composition_project import CompositionProject


PROJECT = '42d0daa7-6464-40cc-b5c8-10f2717f3495'
IMPORT = '0d538096-1d82-4419-822a-c167f46166b6'
FILES = {'types.sysml': '// 🛰 Keep exact Sensor prose.\r\npackage Types {\r\n'
         ' part def Sensor;\r\n part def Base { part <SENSOR> sensor [2] : Sensor; }\r\n'
         ' part def Assembly :> Base;\r\n}\r\n',
         'context.sysml': 'package Context { part current : Types::Assembly; }'}
SCOPE = {'version': 'configuration-1.0',
         'root': {'native_name': 'Context::current', 'type': 'Types::Assembly'},
         'selected_roles': {'SensorRole': {'parent': '$root', 'native_name': 'Types::Base::sensor',
                                         'type': 'Types::Sensor'}},
         'open_alternatives': [], 'connections': []}
LINKED = {
    'view.labels.json': {'kind': 'display_labels', 'text': json.dumps(
        {'version': 1, 'view': 'composition', 'title': 'Composition',
         'labels': [{'element': 'Types::Base::sensor', 'text': 'Sensor role'}]}, indent=2)},
    'scope.json': {'kind': 'retained_configuration', 'text': json.dumps(SCOPE, indent=2) + '\n'},
}


class ProjectTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / '.tmp')
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.project, self.initial = CompositionProject.create(
            self.work / 'project.git', FILES, project_id=PROJECT, request_id=IMPORT, linked_records=LINKED)
        self.identity = str(uuid5(UUID(PROJECT), 'Types::Base::sensor'))

    def request(self, name='detector', revision=1):
        return {'operation': 'rename', 'request_id': str(uuid4()), 'expected_revision': revision,
                'element_id': self.identity, 'new_name': name}

    def test_native_alias_qualified_and_short_references_survive_git_retry_reopen_and_restore(self):
        from tests.test_composition_edit import REFERENCE_SOURCE, REFERENCE_SCOPE
        from verifier.composition_view import render
        files = {'reference.sysml': REFERENCE_SOURCE, 'unrelated.sysml': '// exact 🛰\r\npackage Unrelated;\r\n'}
        records = {'scope.json': {'kind': 'retained_configuration', 'text': json.dumps(REFERENCE_SCOPE, indent=2)+'\n'},
                   'labels.json': {'kind': 'display_labels', 'text': json.dumps({'version': 1, 'view': 'PC_REFERENCE',
                       'title': 'Physical hierarchy', 'labels': [{'element': "ReferenceComposition::Outer::'Inner::device'",
                                                                'text': 'Original caption'}]})}}
        project, _ = CompositionProject.create(self.work/'references.git', files, project_id=PROJECT,
            request_id=str(uuid4()), linked_records=records)
        initial = project.snapshot()
        self.assertEqual(initial['document'].configuration_reviews[0]['report']['status'], 'pass')
        initial_svg = render(initial['document'], 'PC_REFERENCE')['svg']
        registry = initial['document'].registry
        ids = {value: key for key, value in registry.items()}
        for revision, old, new in [(1, 'ReferenceComposition::Outer', 'Platform'),
                (2, "ReferenceComposition::Outer::'Inner::device'", 'Module'),
                (3, "ReferenceComposition::'Sénsor::unit'", 'Detector')]:
            request = {'operation': 'rename', 'request_id': str(uuid4()), 'expected_revision': revision,
                       'element_id': ids[old], 'new_name': new}
            preview = project.preview(request)
            receipt = project.transact(request)
            self.assertEqual(project.transact(request), receipt)
            self.assertEqual(project.snapshot()['document'].files, preview['document'].files)
        saved = CompositionProject(project.repository).snapshot()
        document = saved['document']
        self.assertEqual(saved['revision'], 4)
        self.assertEqual(set(document.registry), set(registry))
        self.assertEqual(document.registry[ids["ReferenceComposition::Outer::'Inner::device'"]],
                         'ReferenceComposition::Platform::Module')
        self.assertEqual(document.linked_records['scope.json'], records['scope.json'])
        self.assertEqual(document.configuration_reviews[0]['report']['status'], 'fail')
        self.assertEqual(document.files['unrelated.sysml'], files['unrelated.sysml'])
        self.assertIn('part remote : Platform::Remote;', document.source)
        self.assertIn('part shortPath : O::I;', document.source)
        self.assertIn('part aliasShortRef : AS;', document.source)
        rendered = render(document, 'PC_REFERENCE')
        self.assertEqual(rendered['display_labels']['Inner'], 'Original caption')
        self.assertEqual(rendered['projection']['nodes']['Inner']['native']['name'], 'Module')
        stale = {**request, 'request_id': str(uuid4()), 'expected_revision': 2}
        with self.assertRaises(EditError):
            project.transact(stale)
        self.assertEqual(project.head(), saved['commit'])
        result = subprocess.run([sys.executable, '-B', 'scripts/composition_project.py', 'inspect',
                                 '--project', str(project.repository)], cwd=ROOT, capture_output=True, text=True, check=True)
        reopened = json.loads(result.stdout)
        self.assertEqual(reopened['revision'], 4)
        self.assertEqual(reopened['registry'], document.registry)
        restore = {'operation': 'restore', 'request_id': str(uuid4()), 'expected_revision': 4, 'target_revision': 1}
        receipt = project.transact(restore)
        self.assertEqual(receipt['revision'], 5)
        restored = CompositionProject(project.repository).snapshot()['document']
        self.assertEqual(restored.files, files)
        self.assertEqual(restored.registry, registry)
        self.assertEqual(restored.linked_records, records)
        self.assertEqual(render(restored, 'PC_REFERENCE')['svg'], initial_svg)

    def test_exact_sources_registry_and_findings_survive_a_fresh_process(self):
        code = '''import json,sys
from verifier.composition_project import CompositionProject
s=CompositionProject(sys.argv[1]).snapshot()
print(json.dumps({'revision':s['revision'],'files':s['document'].files,
                 'records':s['document'].linked_records,'inspect':s['document'].inspect()}))
'''
        result = subprocess.run([sys.executable, '-c', code, str(self.project.repository)],
                                cwd=ROOT, capture_output=True, text=True, check=True)
        saved = json.loads(result.stdout)
        self.assertEqual(saved['revision'], 1)
        self.assertEqual(saved['files'], FILES)
        self.assertEqual(saved['records'], LINKED)
        role = next(row for row in saved['inspect']['elements'] if row['element_id'] == self.identity)
        self.assertEqual(role['qualified_name'], 'Types::Base::sensor')
        self.assertEqual(saved['inspect']['configuration_reviews'][0]['report']['status'], 'pass')
        result = subprocess.run(['git', '--git-dir', str(self.project.repository), 'fsck', '--full'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rename_commits_linked_changes_together_without_migrating_scope(self):
        receipt = self.project.transact(self.request())
        snapshot = CompositionProject(self.project.repository).snapshot()
        document = snapshot['document']
        self.assertEqual(snapshot['revision'], 2)
        self.assertEqual(document.files['context.sysml'], FILES['context.sysml'])
        self.assertEqual(document.files['types.sysml'], FILES['types.sysml'].replace('<SENSOR> sensor', '<SENSOR> detector'))
        self.assertEqual(document.registry[self.identity], 'Types::Base::detector')
        self.assertEqual(document.linked_records['scope.json'], LINKED['scope.json'])
        self.assertEqual(document.linked_records['view.labels.json']['text'],
                         LINKED['view.labels.json']['text'].replace('Types::Base::sensor', 'Types::Base::detector'))
        self.assertEqual(document.configuration_reviews[0]['report']['status'], 'fail')
        self.assertEqual(receipt, snapshot['receipt'])
        self.assertEqual(receipt['parent_commit'], self.initial['commit'])
        raw = subprocess.check_output(['git', '--git-dir', str(self.project.repository),
                                       'show', receipt['commit'] + ':models/types.sysml'])
        self.assertEqual(raw, document.files['types.sysml'].encode('utf-8'))

    def test_lost_response_returns_original_receipt_without_reapplying(self):
        request = self.request()
        publish = self.project._publish
        def lose_response(commit, previous):
            publish(commit, previous)
            raise ConnectionError('Synthetic lost response after durable publication')
        with patch.object(self.project, '_publish', side_effect=lose_response):
            with self.assertRaises(ConnectionError):
                self.project.transact(request)
        saved = self.project.snapshot()['receipt']
        recovered = CompositionProject(self.project.repository).transact(request)
        self.assertEqual(recovered, saved)
        self.assertEqual(len(self.project.history()), 2)

    def test_failure_before_head_publication_leaves_old_state_and_retry_works(self):
        request = self.request()
        with patch.object(self.project, '_publish', side_effect=EditError('storage', 'Synthetic pre-publication failure')):
            with self.assertRaises(EditError):
                self.project.transact(request)
        self.assertEqual(self.project.head(), self.initial['commit'])
        self.assertEqual(self.project.snapshot()['document'].files, FILES)
        self.assertEqual(self.project.transact(request)['revision'], 2)

    def test_stale_request_and_reused_request_identity_do_not_overwrite(self):
        request = self.request()
        receipt = self.project.transact(request)
        for changed, expected in [(self.request('other'), 'stale_revision'),
                                  ({**request, 'new_name': 'other'}, 'request_reuse')]:
            with self.subTest(expected=expected), self.assertRaises(EditError) as error:
                self.project.transact(changed)
            self.assertEqual(error.exception.code, expected)
            self.assertEqual(self.project.head(), receipt['commit'])

    def test_undo_and_redo_are_new_monotonic_revisions_with_the_same_ids(self):
        rename = self.request()
        second = self.project.transact(rename)
        renamed = self.project.snapshot()['document']
        third = self.project.transact({'operation': 'restore', 'request_id': str(uuid4()),
                                      'expected_revision': 2, 'target_revision': 1})
        restored = self.project.snapshot()['document']
        self.assertEqual(third['revision'], 3)
        self.assertEqual(restored.files, FILES)
        self.assertEqual(restored.linked_records, LINKED)
        self.assertEqual(restored.registry[self.identity], 'Types::Base::sensor')
        self.assertEqual(restored.configuration_reviews[0]['report']['status'], 'pass')
        self.assertEqual(self.project.transact(rename), second)
        self.assertEqual(self.project.snapshot()['revision'], 3)
        fourth = self.project.transact({'operation': 'restore', 'request_id': str(uuid4()),
                                       'expected_revision': 3, 'target_revision': 2})
        self.assertEqual(fourth['revision'], 4)
        self.assertEqual(self.project.snapshot()['document'].files, renamed.files)
        self.assertEqual(self.project.snapshot()['document'].registry, renamed.registry)
        with self.assertRaises(EditError) as error:
            self.project.transact(self.request('stale', revision=1))
        self.assertEqual(error.exception.code, 'stale_revision')
        self.assertEqual([r['revision'] for r in self.project.history()], [4, 3, 2, 1])

    def race(self, requests):
        barrier = Barrier(2)
        def run(request):
            project = CompositionProject(self.project.repository)
            publish = project._publish
            def aligned(commit, previous):
                barrier.wait(timeout=30)
                return publish(commit, previous)
            with patch.object(project, '_publish', side_effect=aligned):
                try:
                    return project.transact(request)
                except EditError as exc:
                    return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, requests))

    def test_concurrent_different_edits_have_one_winner_and_one_explicit_conflict(self):
        requests = [self.request('alpha'), self.request('beta')]
        first, second = self.race(requests)
        self.assertEqual(sum(isinstance(r, dict) for r in (first, second)), 1)
        self.assertIn('stale_revision', (first, second))
        self.assertEqual(len(self.project.history()), 2)
        winner = first if isinstance(first, dict) else second
        self.assertEqual(self.project.head(), winner['commit'])
        winning_request = next(r for r in requests if r['request_id'] == winner['request_id'])
        self.assertEqual(self.project.snapshot()['document'].registry[self.identity],
                         'Types::Base::' + winning_request['new_name'])

    def test_concurrent_identical_requests_return_the_same_committed_receipt(self):
        request = self.request()
        first, second = self.race([request, deepcopy(request)])
        self.assertIsInstance(first, dict)
        self.assertEqual(first, second)
        self.assertEqual(len(self.project.history()), 2)

    def test_real_git_bundle_restores_sources_ids_and_history_in_another_directory(self):
        self.project.transact(self.request())
        bundle = self.work / 'portable.bundle'
        subprocess.run(['git', '--git-dir', str(self.project.repository), 'bundle', 'create',
                        str(bundle), '--all'], capture_output=True, check=True)
        target = self.work / 'restored.git'
        subprocess.run(['git', 'clone', '--bare', str(bundle), str(target)], capture_output=True, check=True)
        copy = CompositionProject(target)
        self.assertEqual(copy.head(), self.project.head())
        self.assertEqual(copy.snapshot()['document'].registry, self.project.snapshot()['document'].registry)
        self.assertEqual(copy.snapshot()['document'].files, self.project.snapshot()['document'].files)
        self.assertEqual(copy.history(), self.project.history())

    def test_corrupted_manifest_binding_cannot_be_read_as_valid_project_state(self):
        head = self.project.head()
        tree = self.project._tree(head)
        files = {name: self.project._blob(oid, 5_000_000) for name, oid in tree.items()}
        files['models/context.sysml'] += b'\n// changed without matching manifest\n'
        # Keep the history structurally valid so this isolates the source hash
        # check rather than failing first on an unrelated revision mismatch.
        state = json.loads(files['cse/state.json'])
        state['revision'] = 2
        state['receipt'].update(revision=2, operation='rename', parent_commit=head, request_id=str(uuid4()))
        files['cse/state.json'] = json.dumps(state).encode('utf-8')
        corrupt_tree = self.project._write_tree(files)
        corrupt_commit = self.project._git('commit-tree', corrupt_tree, '-p', head, data=b'Test corruption\n').stdout.decode().strip()
        self.project._publish(corrupt_commit, head)
        with self.assertRaises(EditError) as error:
            self.project.snapshot()
        self.assertEqual(error.exception.code, 'storage_integrity')
        self.assertIn('Source bytes and manifest disagree', str(error.exception))

    def test_extra_commit_without_a_new_revision_is_rejected_on_reopen(self):
        head = self.project.head()
        tree = self.project._git('rev-parse', head + '^{tree}').stdout.decode().strip()
        duplicate = self.project._git('commit-tree', tree, '-p', head, data=b'Test invalid revision\n').stdout.decode().strip()
        self.project._publish(duplicate, head)
        with self.assertRaises(EditError) as error:
            self.project.snapshot()
        self.assertEqual(error.exception.code, 'storage_integrity')

    def test_import_retry_returns_original_receipt_after_later_edits(self):
        self.project.transact(self.request())
        _, receipt = CompositionProject.create(self.project.repository, FILES, project_id=PROJECT,
                                               request_id=IMPORT, linked_records=LINKED)
        self.assertEqual(receipt, self.initial)
        self.assertEqual(self.project.snapshot()['revision'], 2)

    def test_unknown_and_malformed_operations_preserve_the_published_head(self):
        invalid = [{}, self.request() | {'extra': True}, self.request() | {'expected_revision': True},
                   self.request() | {'request_id': 'not-a-uuid'},
                   {'operation': 'restore', 'request_id': str(uuid4()), 'expected_revision': 1, 'target_revision': 0}]
        for request in invalid:
            with self.subTest(request=request), self.assertRaises(EditError):
                self.project.transact(request)
        self.assertEqual(self.project.head(), self.initial['commit'])

    def test_cli_uses_the_same_committed_state_and_idempotent_receipts(self):
        def cli(command, *args):
            process = subprocess.run([sys.executable, str(ROOT / 'scripts/composition_project.py'), command,
                                      '--project', str(self.project.repository), *args],
                                     cwd=ROOT, capture_output=True, text=True)
            return process.returncode, json.loads(process.stdout)
        request = self.request()
        path = self.work / 'request.json'
        path.write_text(json.dumps(request))
        code, saved = cli('apply', '--request', str(path))
        self.assertEqual(code, 0, saved)
        self.assertEqual(saved['receipt'], self.project.transact(request))
        code, inspected = cli('inspect')
        self.assertEqual(code, 0, inspected)
        self.assertEqual(inspected['revision'], 2)
        self.assertEqual(inspected['registry'][self.identity], 'Types::Base::detector')
        bundle = self.work / 'bundle.json'
        bundle.write_text(json.dumps({'version': 'cse-composition-bundle-1', 'models': FILES, 'linked_records': LINKED}))
        code, imported = cli('import', '--bundle', str(bundle), '--project-id', PROJECT, '--request-id', IMPORT)
        self.assertEqual(code, 0, imported)
        self.assertEqual(imported['receipt'], self.initial)
        code, history = cli('history')
        self.assertEqual(code, 0, history)
        self.assertEqual(history['history'], self.project.history())
        self.assertEqual(inspected['files'], self.project.snapshot()['document'].files)
        self.assertEqual(inspected['configuration_reviews'][0]['report']['status'], 'fail')
        code, history = cli('history')
        self.assertEqual(code, 0, history)
        self.assertEqual(history['history'], self.project.history())
        path.write_text(json.dumps(self.request('stale')))
        code, refused = cli('apply', '--request', str(path))
        self.assertEqual(code, 1)
        self.assertEqual(refused['error']['code'], 'stale_revision')
        self.assertEqual(self.project.head(), saved['receipt']['commit'])


class ImportRefusalTests(unittest.TestCase):
    def test_invalid_import_does_not_create_or_replace_a_project_directory(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as folder:
            target = Path(folder) / 'new.git'
            for models in ['not-a-file-map', {'a': 'package A;', 'a/b': 'package B;'}]:
                with self.subTest(models=models), self.assertRaises(EditError):
                    CompositionProject.create(target, models, project_id=PROJECT, request_id=IMPORT)
                self.assertFalse(target.exists())
            target.mkdir()
            sentinel = target / 'keep.txt'
            sentinel.write_text('Preserve existing files')
            with self.assertRaises(EditError):
                CompositionProject.create(target, FILES, project_id=PROJECT, request_id=IMPORT)
            self.assertEqual(sentinel.read_text(), 'Preserve existing files')


if __name__ == '__main__':
    unittest.main()
