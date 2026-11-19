"""Keep the walkthrough tied to saved SVG masters, exact fonts and notation."""
from hashlib import sha256
import json
import re
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'s': 'http://www.w3.org/2000/svg'}


class KitTests(unittest.TestCase):
    def setUp(self):
        self.html = (ROOT / 'docs/workbench/composition-walkthrough.html').read_text()
        self.svg = ET.fromstring(re.search(r'<svg\b[\s\S]*?</svg>', self.html).group())
        self.usage = json.loads((ROOT / 'docs/workbench/composition-kit-usage.json').read_text())

    def test_saved_master_is_pinned_and_actual_uses_retain_its_treatments(self):
        component = self.usage['components'][0]
        source = ROOT / component['path']
        self.assertEqual(sha256(source.read_bytes()).hexdigest(), component['sha256'])
        master = ET.parse(source).getroot()
        expected = [{k: v for k, v in e.attrib.items() if k != 'href'}
                    for e in master.findall('s:g/s:use', NS)]
        groups = self.svg.findall('s:g', NS)
        self.assertEqual(len(groups), 2)
        for group in groups:
            self.assertEqual(group.get('data-component'), component['id'])
            self.assertEqual(group.get('data-source-sha256'), component['sha256'])
            actual = [{k: v for k, v in e.attrib.items() if k != 'href'}
                      for e in group.findall('s:use', NS)]
            self.assertEqual(actual, expected)
            self.assertTrue(group.get('data-model-element'))

    def test_exact_font_files_notices_and_usage_manifest(self):
        path = ROOT / self.usage['font_manifest']
        self.assertEqual(sha256(path.read_bytes()).hexdigest(), self.usage['font_manifest_sha256'])
        manifest = json.loads(path.read_text())
        for face in manifest['faces']:
            for name, expected in [(face['file'], face['sha256']), (face['notice'], face['notice_sha256'])]:
                self.assertEqual(sha256((path.parent / name).read_bytes()).hexdigest(), expected)
            self.assertIn(face['file'], self.html)
        for text in self.svg.findall('.//s:text', NS):
            self.assertIn(text.get('font-family'), ('DejaVu Sans', 'DejaVu Sans Mono'))
        self.assertNotIn('Rectangle Plain White', ''.join(self.svg.itertext()))

    def test_proposed_ownership_route_is_unarrowed_and_readable(self):
        paths = self.svg.findall('s:path', NS)
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].get('data-relation'), 'native-declaration-ownership')
        self.assertEqual(paths[0].get('d'), 'M360 138 V244')
        self.assertFalse(self.svg.findall('.//s:marker', NS))
        self.assertFalse(self.svg.findall('.//s:polygon', NS))
        self.assertIn('Scroll horizontally', self.html)
        self.assertIn('proposed projection', self.html)
        self.assertIn('selected configuration not evaluated', self.html)

    def test_multiline_label_uses_saved_minimum_baseline_spacing(self):
        tokens = json.loads((ROOT / 'assets/engineering-library/tokens/typography-spec.json').read_text())
        step = int(re.search(r"setAttribute\('dy',i\?'(\d+)'", self.html).group(1))
        label = self.svg.find(".//s:text[@id='roleLabel']", NS)
        self.assertGreaterEqual(step / int(label.get('font-size')),
                                tokens['multiline_baseline_spacing_em_min'])


if __name__ == '__main__':
    unittest.main()
