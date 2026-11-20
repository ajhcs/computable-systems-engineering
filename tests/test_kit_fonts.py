"""Exact DejaVu bytes, real advances, reversible wrapping and stale-asset refusal."""
import base64
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier import kit_fonts as fonts


class KitFonts(unittest.TestCase):
    def test_manifest_metrics_and_embedded_fonts_pin_exact_bytes_and_notice(self):
        manifest = json.loads(fonts.manifest_bytes())
        metrics = json.loads(fonts.metrics_bytes())
        self.assertEqual(sha256(fonts.manifest_bytes()).hexdigest(), fonts.MANIFEST_SHA256)
        self.assertEqual(sha256(fonts.metrics_bytes()).hexdigest(), manifest['metrics']['sha256'])
        css = fonts.font_css()
        payloads = re.findall(r'url\(data:font/ttf;base64,([A-Za-z0-9+/=]+)\)', css)
        self.assertEqual(len(payloads), 4)
        for face, payload in zip(manifest['faces'], payloads):
            raw = base64.b64decode(payload)
            self.assertEqual(raw, (fonts.ASSETS / face['file']).read_bytes())
            self.assertEqual(sha256(raw).hexdigest(), face['sha256'])
            self.assertEqual(sha256((fonts.ASSETS / face['notice']).read_bytes()).hexdigest(), face['notice_sha256'])
            key = face['family'] + ':' + str(face['weight'])
            self.assertEqual(metrics['faces'][key]['font_sha256'], face['sha256'])
        self.assertIn('Bitstream', css)
        self.assertNotIn('https://', css.split('@font-face', 1)[1])

    def test_widths_match_true_type_hmtx_and_disable_kerning_ligatures(self):
        # A is glyph 36 in these exact pinned DejaVu fonts; use the source table,
        # independently of the stored metrics and the public measurement API.
        raw = (fonts.ASSETS / 'DejaVuSans.ttf').read_bytes()
        count = struct.unpack_from('>H', raw, 4)[0]
        tables = {tag: at for tag, _, at, _ in
                  (struct.unpack_from('>4sIII', raw, 12 + 16*i) for i in range(count))}
        advance_a = struct.unpack_from('>H', raw, tables[b'hmtx'] + 4*36)[0]
        units = struct.unpack_from('>H', raw, tables[b'head'] + 18)[0]
        self.assertEqual((advance_a, units), (1401, 2048))
        self.assertEqual(fonts.text_width('A', 24), 1401 * 24 / 2048)
        self.assertEqual(fonts.text_width('W', 24), 2025 * 24 / 2048)
        self.assertEqual(fonts.text_width('W', 24, weight=700), 2259 * 24 / 2048)
        for family in ('DejaVu Sans', 'DejaVu Sans Mono'):
            for weight in (400, 700):
                with self.subTest(family=family, weight=weight):
                    for value in ('AV', 'ffi', 'IF-201 · S2/B4'):
                        self.assertEqual(fonts.text_width(value, 24, family, weight),
                                         sum(fonts.text_width(c, 24, family, weight) for c in value))

    def test_mono_is_constant_width_including_middle_dot(self):
        for weight in (400, 700):
            self.assertEqual(fonts.text_width('Wi ·', 24, 'DejaVu Sans Mono', weight), 4 * 1233 * 24 / 2048)

    def test_wrapping_keeps_every_character_and_fits_measured_regions(self):
        for family in ('DejaVu Sans', 'DejaVu Sans Mono'):
            for weight in (400, 700):
                for value in ('Cooling loop', 'NOTE 01  Check seal. ', 'IF-201 · S2/B4', 'UnbrokenIdentifier1234'):
                    width = 100
                    lines = fonts.wrap_text(value, width, 24, family, weight)
                    self.assertEqual(''.join(lines), value)
                    self.assertTrue(all(fonts.text_width(line, 24, family, weight) <= width for line in lines))
        self.assertEqual(fonts.wrap_text('A B C', fonts.text_width('A B ', 24), 24), ['A B ', 'C'])

    def test_unqualified_text_and_invalid_measurement_requests_refused(self):
        for value in ('', '\n', 'A\tB', 'snowman \u2603', 'G\u0305', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                fonts.text_width(value, 24)
        for size in (0, -1, True, float('nan'), float('inf')):
            with self.subTest(size=size), self.assertRaises(ValueError):
                fonts.text_width('A', size)
        for family, weight in [('Arial', 400), ('DejaVu Sans', 500), ('DejaVu Sans', True), ({}, 400)]:
            with self.subTest(family=family, weight=weight), self.assertRaises(ValueError):
                fonts.text_width('A', 24, family, weight)
        for width in (0, -1, True, float('nan'), float('inf'), 1):
            with self.subTest(width=width), self.assertRaises(ValueError):
                fonts.wrap_text('W', width, 24)

    def test_changes_after_cached_read_refuse_font_metric_notice_and_manifest(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        for name, message in [('DejaVuSans.ttf', 'font digest'), ('metrics.json', 'metrics digest'),
                              ('DejaVu-COPYRIGHT.txt', 'notice digest'), ('manifest.json', 'manifest digest')]:
            with self.subTest(name=name), tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as d:
                target = Path(d) / 'fonts'
                shutil.copytree(fonts.ASSETS, target)
                with patch.object(fonts, 'ASSETS', target):
                    self.assertGreater(fonts.text_width('Cache first', 24), 0)
                    path = target / name
                    raw = path.read_bytes()
                    path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
                    with self.assertRaisesRegex(ValueError, message):
                        fonts.text_width('Read changed bytes', 24)

    def test_missing_asset_refused(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / '.tmp') as d, patch.object(fonts, 'ASSETS', Path(d)):
            with self.assertRaisesRegex(ValueError, 'Missing or unreadable'):
                fonts.font_css()


if __name__ == '__main__':
    unittest.main()
