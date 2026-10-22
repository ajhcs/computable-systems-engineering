"""Reproduce source-bound README previews and keep their reader links usable."""
from html.parser import HTMLParser
import importlib.util
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'examples/readme-showcase'
sys.path.insert(0, str(ROOT))
from verifier.sysml import JAR, CLASSES
spec = importlib.util.spec_from_file_location('readme_showcase', HERE / 'build.py')
showcase = importlib.util.module_from_spec(spec)
spec.loader.exec_module(showcase)


class Targets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        self.links.extend(value for key, value in attrs if key in ('href', 'src') and value)
        self.ids.update(value for key, value in attrs if key == 'id' and value)


class ReadmeShowcaseTests(unittest.TestCase):
    @unittest.skipUnless(JAR.is_file() and (CLASSES / 'SysmlBridge.class').is_file(),
                         'Install the pinned SysML parser')
    def test_actual_source_recomputation_and_fresh_preview_comparison(self):
        temporary = ROOT / '.tmp'
        temporary.mkdir(exist_ok=True)
        env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
                   PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(temporary),
                   TMP=str(temporary), TEMP=str(temporary))
        result = subprocess.run([sys.executable, '-B', str(HERE / 'build.py'), '--check'],
                                cwd=ROOT, env=env, capture_output=True, text=True,
                                encoding='utf-8', timeout=600)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_altered_missing_and_unlisted_preview_files_refuse_before_computation(self):
        temporary = ROOT / '.tmp'
        temporary.mkdir(exist_ok=True)
        for mutation in ('svg', 'png', 'delete', 'add'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(dir=temporary) as name:
                output = Path(name) / 'generated'
                shutil.copytree(HERE / 'generated', output)
                if mutation in ('svg', 'png'):
                    path = next(output.glob('*.' + mutation))
                    path.write_bytes(path.read_bytes() + b'altered')
                elif mutation == 'delete':
                    next(output.glob('*.svg')).unlink()
                else:
                    (output / 'unlisted.txt').write_text('unexpected', encoding='utf-8')
                with patch.object(showcase, 'acquire') as acquire, self.assertRaises(ValueError):
                    showcase.check(output)
                acquire.assert_not_called()

    def test_embedded_images_and_relative_reader_links_resolve(self):
        readme = ROOT / 'README.md'
        text = readme.read_text(encoding='utf-8')
        images = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)
        previews = [target for target in images if target.startswith('examples/readme-showcase/')]
        self.assertEqual(len(previews), 8)
        self.assertEqual(len(set(previews)), 8)
        self.assertIn('examples/engineering-gallery/water-sampling/generated/overview.png', images)
        for target in previews:
            data = (ROOT / target).read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            width, height = struct.unpack('>II', data[16:24])
            self.assertEqual(width, 800)
            self.assertGreater(height, 200)
        files = [readme, HERE / 'README.md', HERE / 'generated/index.html']
        checked = 0
        for path in files:
            source = path.read_text(encoding='utf-8')
            if path.suffix == '.html':
                parser = Targets()
                parser.feed(source)
                targets = parser.links
            else:
                targets = re.findall(r'\]\(([^)]+)\)', source)
            for target in targets:
                url = urlsplit(target)
                if url.scheme or url.netloc or not (url.path or url.fragment):
                    continue
                resolved = (path.parent / unquote(url.path)).resolve() if url.path else path.resolve()
                with self.subTest(source=str(path.relative_to(ROOT)), target=target):
                    self.assertTrue(resolved.is_relative_to(ROOT), 'Reader link escaped repository')
                    self.assertTrue(resolved.exists(), 'Missing reader target')
                    if url.fragment and resolved.suffix in ('.md', '.html'):
                        body = resolved.read_text(encoding='utf-8')
                        if resolved.suffix == '.html':
                            parser = Targets()
                            parser.feed(body)
                            anchors = parser.ids
                        else:
                            anchors = set()
                            counts = {}
                            for title in re.findall(r'^#{1,6} (.+)$', body, re.M):
                                slug = re.sub(r'[^\w -]', '', title.lower()).replace(' ', '-')
                                count = counts.get(slug, 0)
                                counts[slug] = count + 1
                                anchors.add(slug + (f'-{count}' if count else ''))
                        self.assertIn(unquote(url.fragment), anchors, 'Missing reader anchor')
                checked += 1
        self.assertGreater(checked, 60)


if __name__ == '__main__':
    unittest.main()
