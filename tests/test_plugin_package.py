"""Committed-source packaging excludes active edits and preserves exact payload bytes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from package_plugin import build
from package_chatgpt import package as chatgpt_package
from zipfile import ZipFile


class PluginPackageTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.tmp')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'source'
        self.repo.mkdir()
        self.command('init', '-q')
        self.command('config', 'user.email', 'fixture@example.invalid')
        self.command('config', 'user.name', 'Synthetic Fixture')
        identity = {'name': 'computable-systems-engineering', 'version': '0.2.0-test'}
        self.write('plugin.json', json.dumps(identity))
        self.write('.codex-plugin/plugin.json', json.dumps(identity))
        for number in range(11):
            self.write(f'skills/fixture-{number}/SKILL.md', '---\nname: fixture\n---\n')
        self.write('docs/guide.md', 'Committed wording.\n')
        self.write('assets/master.svg', '<svg/>\n')
        self.write('prototypes/repair_reuse.py', 'def retained_helper(): return 42\n')
        self.write('.agents/skills/fixture-alias', 'Repository-only alias')
        self.write('.github/workflows/check.yml', 'Source-only CI')
        self.write('.gitignore', 'private/\n')
        self.command('add', '.')
        self.command('commit', '-qm', 'Synthetic package fixture')

    def command(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_exact_commit_ignores_dirty_staged_untracked_and_ignored_content(self):
        commit = self.command('rev-parse', 'HEAD')
        self.write('docs/guide.md', 'Existing engineer draft.\n')
        self.command('add', 'docs/guide.md')
        self.write('assets/untracked.svg', '<private/>')
        self.write('private/notes.txt', 'private input')
        before = self.command('status', '--porcelain')
        receipt = build(self.repo, commit, self.base / 'package')
        payload = self.base / 'package/plugins/computable-systems-engineering'
        self.assertEqual((payload / 'docs/guide.md').read_text(), 'Committed wording.\n')
        self.assertFalse((payload / 'assets/untracked.svg').exists())
        self.assertFalse((payload / 'private').exists())
        self.assertFalse((payload / '.agents').exists())
        self.assertFalse((payload / '.github').exists())
        self.assertEqual((payload / 'prototypes/repair_reuse.py').read_text(),
                         'def retained_helper(): return 42\n')
        self.assertEqual(receipt['commit'], commit)
        self.assertEqual(len(receipt['skills']), 11)
        self.assertEqual(self.command('status', '--porcelain'), before)

    def test_two_builds_have_identical_payload_inventories_and_receipts(self):
        first = build(self.repo, 'HEAD', self.base / 'one')
        second = build(self.repo, 'HEAD', self.base / 'two')
        self.assertEqual(first, second)
        self.assertEqual((self.base / 'one/source-receipt.json').read_bytes(),
                         (self.base / 'two/source-receipt.json').read_bytes())

    def test_existing_output_and_output_inside_source_are_refused(self):
        existing = self.base / 'existing'
        existing.mkdir()
        marker = existing / 'retain.txt'
        marker.write_text('Preserve this.')
        for destination in (existing, self.repo / 'new-output'):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                build(self.repo, 'HEAD', destination)
        self.assertEqual(marker.read_text(), 'Preserve this.')

    def test_manifest_disagreement_cannot_produce_success(self):
        self.write('plugin.json', json.dumps({'name': 'computable-systems-engineering', 'version': 'different'}))
        self.command('add', 'plugin.json')
        self.command('commit', '-qm', 'Mismatched synthetic metadata')
        with self.assertRaisesRegex(ValueError, 'identities differ'):
            build(self.repo, 'HEAD', self.base / 'mismatch')
        self.assertFalse((self.base / 'mismatch/source-receipt.json').exists())

    def test_escaping_symlink_is_refused(self):
        (self.repo / 'assets/external').symlink_to('../../outside')
        self.command('add', 'assets/external')
        self.command('commit', '-qm', 'Unsafe fixture link')
        with self.assertRaisesRegex(ValueError, 'Nonportable symlink'):
            build(self.repo, 'HEAD', self.base / 'escaping')

    def test_hosted_zip_has_root_manifests_remote_tools_and_exact_committed_skills(self):
        portable = json.loads((self.repo / 'plugin.json').read_text())
        portable['extensions'] = {'com.openai': {'requires_local_executor': True,
                                                'interface': {'displayName': 'Synthetic CSE'}}}
        self.write('plugin.json', json.dumps(portable))
        self.command('add', 'plugin.json')
        self.command('commit', '-qm', 'Synthetic portable presentation metadata')
        self.write('docs/guide.md', 'Private uncommitted input must stay excluded.')
        first = chatgpt_package(self.repo, 'HEAD', self.base / 'hosted-one')
        second = chatgpt_package(self.repo, 'HEAD', self.base / 'hosted-two')
        self.assertEqual(first['zip_sha256'], second['zip_sha256'])
        with ZipFile(self.base / 'hosted-one' / first['zip']) as archive:
            data = json.loads(archive.read('plugin.json'))
            native = json.loads(archive.read('.codex-plugin/plugin.json'))
            extension = data['extensions']['com.openai']
            self.assertFalse(extension['requires_local_executor'])
            self.assertFalse(native['requires_local_executor'])
            self.assertEqual(extension['interface'], native['interface'])
            self.assertEqual(len(extension['review']['test_cases']['positive']), 5)
            self.assertEqual(len(extension['review']['test_cases']['negative']), 3)
            self.assertNotIn('demo_recording_url', extension['review'])
            self.assertTrue(json.loads(archive.read('mcp.json'))['mcpServers']['cse']['url'].endswith('/mcp'))
            self.assertEqual(archive.read('docs/guide.md').decode(), 'Committed wording.\n')
            self.assertEqual(sum(name.endswith('/SKILL.md') for name in archive.namelist()), 11)
        self.assertIn('Real demo recording URL', first['required_before_submission'])


if __name__ == '__main__':
    unittest.main()
