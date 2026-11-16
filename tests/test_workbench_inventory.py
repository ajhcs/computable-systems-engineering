"""Preservation inventory must capture dirty bytes and avoid following links."""
from hashlib import sha256
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workbench_inventory', ROOT / 'scripts/workbench_inventory.py')
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def test_captures_dirty_tracked_untracked_and_symlink_without_following(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'model.sysml').write_text('package Original;')
            subprocess.run(['git', '-C', str(root), 'add', 'model.sysml'], check=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Test',
                            '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false',
                            'commit', '-qm', 'Synthetic baseline'], check=True)
            (root / 'model.sysml').write_text('package Dirty;')
            (root / 'scope.json').write_text('{"explicit":"untracked"}')
            (root / 'outside').symlink_to('/nonexistent/private-source')
            result = inventory.capture(root)
            files = {f['path']: f for f in result['files']}
            self.assertEqual(files['model.sysml']['sha256'], sha256(b'package Dirty;').hexdigest())
            self.assertIn('scope.json', files)
            self.assertEqual(files['outside'], {'path': 'outside', 'symlink': '/nonexistent/private-source'})
            self.assertIn(' M model.sysml', result['status'])
            self.assertEqual((root / 'model.sysml').read_text(), 'package Dirty;')

    def test_dynamic_arguments_stay_explicit_and_tools_are_inventoried(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as directory:
            path = Path(directory) / 'entrypoint.py'
            path.write_text("p.add_argument('command', choices=COMMANDS)\n@server.tool(annotations=READ)\ndef inspect(): pass\n")
            rows = inventory.declarations(path)
            self.assertEqual(rows[0]['choices_source'], 'COMMANDS')
            self.assertEqual(rows[1]['name'], 'inspect')


if __name__ == '__main__':
    unittest.main()
