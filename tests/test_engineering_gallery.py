"""Reproduce the public synthetic case and refuse stale or mistyped companions."""
import copy
from contextlib import contextmanager
import importlib.util
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'examples/engineering-gallery/water-sampling'
sys.path.insert(0, str(ROOT))
from verifier.sysml import JAR, CLASSES
spec = importlib.util.spec_from_file_location('engineering_gallery_case', CASE / 'build.py')
gallery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gallery)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        self.targets.extend(value for key, value in attrs if key in ('href', 'src') and value)


class GalleryTests(unittest.TestCase):
    @contextmanager
    def copied_case(self):
        temporary = ROOT / '.tmp'
        temporary.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary, prefix='gallery-control-') as name:
            target = Path(name) / 'case'
            shutil.copytree(CASE, target, ignore=shutil.ignore_patterns('__pycache__'))
            for name in ('README.md', 'index.html'):
                shutil.copy2(CASE.parent / name, target.parent / name)
            with patch.object(gallery, 'HERE', target):
                yield target

    def test_source_edits_refuse_before_rebuilding(self):
        with self.copied_case() as case, patch.object(gallery, 'build') as build:
            path = case / 'evidence-pass.json'
            path.write_bytes(path.read_bytes() + b' ')
            with self.assertRaisesRegex(ValueError, 'Source or engine changed'):
                gallery.check()
            build.assert_not_called()

    def test_generated_changes_deletion_and_addition_refuse_before_rebuilding(self):
        for mutation in ('diagram', 'delete', 'add'):
            with self.subTest(mutation=mutation), self.copied_case() as case, patch.object(gallery, 'build') as build:
                output = case / 'generated'
                if mutation == 'diagram':
                    path = output / 'overview.svg'
                    path.write_bytes(path.read_bytes() + b'<!-- changed -->')
                elif mutation == 'delete':
                    (output / 'native-pass.json').unlink()
                else:
                    (output / 'unlisted.json').write_text('{}', encoding='utf-8')
                with self.assertRaises(ValueError):
                    gallery.check()
                build.assert_not_called()

    def test_allocation_references_and_part_kinds_are_checked(self):
        inventory = json.loads((CASE / 'generated/shape-concept.json').read_text())['inventory']
        ledger = json.loads((CASE / 'semantic-ledger.json').read_text())
        gallery.check_allocations(inventory, ledger)
        for mutation in ('performer', 'function', 'type'):
            broken = copy.deepcopy(ledger)
            if mutation == 'type':
                broken['native_part_usages']['WaterSampling::station'] = 'Operator'
            else:
                broken['documentary_allocations'][0][mutation] = 'UnknownReference'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                gallery.check_allocations(inventory, broken)

    def test_documentation_and_gallery_links_resolve(self):
        paths = [ROOT / 'README.md', ROOT / 'docs/capability-completion.md', ROOT / 'docs/gallery-method.md']
        paths += sorted((ROOT / 'examples/engineering-gallery').rglob('*.md'))
        paths += sorted((ROOT / 'examples/engineering-gallery').rglob('*.html'))
        checked = 0
        for path in paths:
            content = path.read_text(encoding='utf-8')
            if path.suffix == '.html':
                parser = Links()
                parser.feed(content)
                targets = parser.targets
            else:
                targets = re.findall(r'\[[^\]]*\]\(([^)]+)\)', content)
            for target in targets:
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                resolved = (path.parent / unquote(url.path)).resolve()
                with self.subTest(source=str(path.relative_to(ROOT)), target=target):
                    self.assertTrue(resolved.is_relative_to(ROOT), 'Local link escaped repository')
                    self.assertTrue(resolved.exists(), 'Broken local artifact link')
                checked += 1
        self.assertGreater(checked, 40)

    @unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(),
                         'Install the pinned SysML parser')
    def test_actual_gallery_rebuild_and_positive_negative_outcomes(self):
        temporary = ROOT / '.tmp'
        temporary.mkdir(exist_ok=True)
        environment = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
                           PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(temporary),
                           TMP=str(temporary), TEMP=str(temporary))
        result = subprocess.run([sys.executable, '-B', str(CASE / 'build.py'), '--check'],
                                cwd=ROOT, env=environment, capture_output=True,
                                text=True, encoding='utf-8', timeout=600)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS synthetic gallery freshness', result.stdout)


if __name__ == '__main__':
    unittest.main()
