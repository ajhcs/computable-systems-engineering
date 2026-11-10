"""Bounded font identity and static-export regressions, with opt-in real browser run."""
from pathlib import Path
import base64
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TEMP = ROOT / '.tmp'
TEMP.mkdir(exist_ok=True)
spec = importlib.util.spec_from_file_location('document_pdf', ROOT / 'scripts/check_document_pdf.py')
pdf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdf)


def font_bytes(family='Fixture Sans', ps='FixtureSans-Regular', weight=400):
    values = [(1, family), (6, ps)]
    strings = b''; records = b''
    for number, value in values:
        raw = value.encode('utf-16-be')
        records += struct.pack('>HHHHHH', 3, 1, 0x409, number, len(raw), len(strings))
        strings += raw
    names = struct.pack('>HHH', 0, len(values), 6 + len(records)) + records + strings
    os2 = struct.pack('>HHH', 0, 0, weight)
    offset = 12 + 16 * 2
    return (b'\0\1\0\0' + struct.pack('>HHHH', 2, 0, 0, 0) +
            struct.pack('>4sIII', b'name', 0, offset, len(names)) +
            struct.pack('>4sIII', b'OS/2', 0, offset + len(names), len(os2)) + names + os2)


class FontIdentity(unittest.TestCase):
    def test_actual_embedded_names_and_weight(self):
        identity = pdf.sfnt_identity(font_bytes(ps='Different-InternalName', weight=600))
        self.assertEqual(identity['postscript_names'], ['Different-InternalName'])
        self.assertEqual(identity['families'], ['Fixture Sans'])
        self.assertEqual(identity['weight'], 600)

    def test_compressed_or_out_of_bounds_font_cannot_pass(self):
        for raw in (b'wOF2' + bytes(48), font_bytes()[:50], b'not a font'):
            with self.subTest(raw=raw[:4]), self.assertRaises(ValueError):
                pdf.sfnt_identity(raw)

    def test_missing_pdf_dependency_is_unsupported(self):
        with mock.patch.dict(sys.modules, {'pymupdf': None, 'fitz': None}):
            result = pdf.inspect_pdf('unrun.pdf', {'status': 'pass', 'fonts': []})
        self.assertEqual(result['status'], 'unsupported')
        self.assertTrue(result['findings'])

    def test_unverified_profile_cannot_seed_pdf_success(self):
        result = pdf.inspect_pdf('unrun.pdf', {'status': 'fail', 'fonts': []})
        self.assertEqual(result['status'], 'error')


@unittest.skipUnless(shutil.which('node'), 'Node is optional outside document rendering')
class RendererContract(unittest.TestCase):
    def test_output_escape_symlink_and_runtime_are_refused(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            project = Path(directory)
            (project / 'escape').symlink_to(project.parent, target_is_directory=True)
            script = 'const r=require(process.argv[1]);try{r.newOutputPath(process.argv[2],process.argv[3]);process.exitCode=0;}catch(e){process.stdout.write(e.message);process.exitCode=1;}'
            for destination in ('../outside', 'escape/outside', str(ROOT / '.tmp/plugin-write')):
                run = subprocess.run(['node', '-e', script, str(ROOT / 'scripts/render_technical_document.cjs'), str(project), destination], text=True, capture_output=True)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn('outside the plugin runtime', run.stdout)

    def test_missing_arguments_returns_structured_error(self):
        run = subprocess.run(['node', str(ROOT / 'scripts/render_technical_document.cjs'), 'render'], text=True, capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(json.loads(run.stdout)['status'], 'error')

    def test_font_css_embeds_supplied_bytes_without_filename_inference(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            font = Path(directory) / 'misleading-name.ttf'
            font.write_bytes(font_bytes())
            preflight = {'fonts': [{'id': 'body', 'family': 'Fixture Sans', 'weight': 400,
                                    'resolved_path': str(font)}], 'profile': {'palette': {'ink': '#123456'},
                         'typography': {'body': {'font': 'body', 'size_pt': 11, 'selectors': ['p']}}}}
            script = 'const r=require(process.argv[1]);process.stdout.write(r.profileCSS(JSON.parse(process.argv[2])));'
            run = subprocess.run(['node', '-e', script, str(ROOT / 'scripts/render_technical_document.cjs'), json.dumps(preflight)], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn(base64.b64encode(font.read_bytes()).decode(), run.stdout)
            self.assertIn('font-family:"Fixture Sans"', run.stdout)
            self.assertNotIn('misleading-name', run.stdout)


@unittest.skipUnless(os.environ.get('CSE_RUN_DOCUMENT_BROWSER') == '1', 'opt-in existing Chromium/PyMuPDF toolchain')
class BrowserExport(unittest.TestCase):
    def test_selected_fonts_svg_graphics_and_hidden_asset_rejection(self):
        test_temp = ROOT.parent / '.cse-document-render-tests'
        test_temp.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=test_temp) as directory:
            project = Path(directory)
            profile = {'version': 'cse.visual-profile/1', 'id': 'synthetic', 'revision': '1',
                       'authority': {'kind': 'project', 'source': 'Synthetic test choice'},
                       'fonts': [{'id': 'body', 'family': 'IBM Plex Sans', 'weight': 400,
                                  'path': 'runtime:examples/ecosystem-diagram-reference/fonts/IBMPlexSans-Regular.woff2',
                                  'postscript_name': 'IBMPlexSans'},
                                 {'id': 'heading', 'family': 'IBM Plex Sans', 'weight': 600,
                                  'path': 'runtime:examples/ecosystem-diagram-reference/fonts/IBMPlexSans-SemiBold.woff2',
                                  'postscript_name': 'IBMPlexSans-SmBld'}],
                       'typography': {'body': {'font': 'body', 'size_pt': 11, 'selectors': ['body','text']},
                                      'heading': {'font': 'heading', 'size_pt': 16, 'selectors': ['h1']}},
                       'palette': {'ink': '#111111'},
                       'assets': [{'id': 'comp-process', 'kind': 'svg', 'role': 'illustration',
                                   'path': 'runtime:assets/engineering-library/components/comp-process.svg',
                                   'source': 'CSE synthetic illustration', 'license': 'MIT', 'adaptations': []},
                                  {'id': 'art', 'kind': 'image', 'role': 'editorial-art', 'path': 'art.png',
                                   'source': 'Synthetic test pixels', 'license': 'CC0', 'adaptations': []}]}
            def chunk(kind, data):
                return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
            (project / 'art.png').write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\x00\x20\x60\x80\x80\xa0\x40' * 2)) + chunk(b'IEND', b''))
            (project / 'profile.json').write_text(json.dumps(profile))
            source = '<!doctype html><html><head><style>@page{size:A4;margin:12mm}.page{width:160mm}svg{width:30mm;height:30mm}img{width:20mm;height:20mm}</style></head><body><div class="page"><h1>Test document</h1><p>Accepted wording remains.</p><div data-cse-asset="comp-process"></div><img data-cse-asset="art" alt="Synthetic test pixels"></div></body></html>'
            html = project / 'source.html'; html.write_text(source)
            svg = '<svg xmlns="http://www.w3.org/2000/svg" width="560" height="180" viewBox="0 0 560 180"><g data-cse-asset="comp-process" transform="translate(216 4)"/><text x="18" y="158">Supplied records → Review → Coded summary</text></svg>'
            (project / 'flow.svg').write_text(svg)
            command = ['node', str(ROOT / 'scripts/render_technical_document.cjs'), 'render', '--root', str(project),
                       '--profile', 'profile.json', '--html', 'source.html', '--svg', 'flow.svg', '--output-dir', 'good', '--python', sys.executable]
            run = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            result = json.loads((project / 'good/render-receipt.json').read_text())
            self.assertEqual(result['status'], 'pass')
            self.assertTrue(result['font_probes'])
            self.assertTrue(all(p['font_matches_selection'] for p in result['font_probes']))
            self.assertTrue(result['assets'][0]['geometry_preserved'])
            self.assertTrue(result['assets'][1]['images'][0]['loaded'])
            self.assertEqual(result['pdf']['postscript_names'], ['IBMPlexSans', 'IBMPlexSans-SmBld'])
            self.assertEqual(result['pdf']['weights'], [400, 600])
            self.assertTrue(any(p['artifact'] == 'figure-1.svg' for p in result['font_probes']))
            self.assertEqual((project / 'flow.svg').read_text(), svg)
            self.assertEqual(html.read_text(), source)
            # Retained output is never replaced, even by an otherwise valid retry.
            run = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            # A native master hidden by layout cannot count as delivered reuse.
            html.write_text(source.replace('data-cse-asset="comp-process"', 'style="display:none" data-cse-asset="comp-process"'))
            command[command.index('good')] = 'hidden'
            run = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            result = json.loads((project / 'hidden/render-receipt.json').read_text())
            self.assertFalse(result['checks']['selected_vectors_visible'])
            html.write_text(source.replace('data-cse-asset="comp-process"', 'style="position:absolute;left:2000px" data-cse-asset="comp-process"'))
            command[command.index('hidden')] = 'offpage'
            run = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            result = json.loads((project / 'offpage/render-receipt.json').read_text())
            self.assertFalse(result['checks']['selected_vectors_visible'])


if __name__ == '__main__':
    unittest.main()
