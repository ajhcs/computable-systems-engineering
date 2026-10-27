#!/usr/bin/env python3
"""Negative controls for the source-safe reference packaging screen."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check_reference_release import check


def chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)


def png(metadata=None):
    data = b'\x89PNG\r\n\x1a\n'
    data += chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    if metadata is not None:
        data += chunk(b'iTXt', b'plantuml\0\x01\x00\0\0' + zlib.compress(metadata.encode()))
    return data + chunk(b'IDAT', zlib.compress(b'\0\xff\xff\xff')) + chunk(b'IEND', b'')


class ReferenceReleaseTests(unittest.TestCase):
    def setUp(self):
        (ROOT / '.tmp').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / '.tmp')
        self.root = Path(self.temp.name)
        self.pack = self.root / 'examples/engineering-reference'
        self.pack.mkdir(parents=True)
        self.addCleanup(self.temp.cleanup)

    def test_bounded_derivatives_and_reviewed_png_metadata_can_pass(self):
        (self.pack / 'facts.json').write_text(json.dumps({'source': 'public model', 'count': 3}))
        (self.pack / 'diagram.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>Three selected parts</text></svg>')
        (self.pack / 'diagram.png').write_bytes(png('@startuml\nA --> B\n@enduml'))
        self.assertEqual(check(self.root)['files_checked'], 3)

    def test_released_reference_package_is_screened(self):
        self.assertGreater(check(ROOT)['files_checked'], 0)

    def test_raw_xml_and_source_archives_are_rejected(self):
        for filename in ('source.xml', 'model.mdzip', 'source.zip', 'article.pdf'):
            path = self.pack / filename
            path.write_bytes(b'test')
            with self.subTest(filename=filename), self.assertRaisesRegex(ValueError, 'raw source'):
                check(self.root)
            path.unlink()

    def test_raw_xml_disguised_as_json_is_rejected(self):
        (self.pack / 'facts.json').write_text(json.dumps({'source_xml': '<ownedRule>private record</ownedRule>'}))
        with self.assertRaisesRegex(ValueError, 'raw source-XML marker'):
            check(self.root)

    def test_hidden_raw_xml_or_private_path_in_png_metadata_is_rejected(self):
        path = self.pack / 'diagram.png'
        for text in ('<packagedElement id="1"/>', '/home/example/private/model'):
            path.write_bytes(png(text))
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'unsafe PNG metadata'):
                check(self.root)

    def test_executable_svg_and_machine_path_are_rejected(self):
        path = self.pack / 'diagram.svg'
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>bad()</script></svg>')
        with self.assertRaisesRegex(ValueError, 'executable'):
            check(self.root)
        path.unlink()
        (self.pack / 'notes.md').write_text('Local source: /workspace/private/example')
        with self.assertRaisesRegex(ValueError, 'private path'):
            check(self.root)

    def test_local_work_path_in_historical_receipt_is_rejected(self):
        (self.pack / 'receipt.json').write_text(json.dumps({'input': 'work/pressure-test/model.sysml'}))
        with self.assertRaisesRegex(ValueError, 'local work path'):
            check(self.root)

    def test_corrupt_png_is_rejected(self):
        data = bytearray(png())
        data[-1] ^= 1
        (self.pack / 'broken.png').write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'CRC'):
            check(self.root)

    def test_compressed_metadata_with_extra_stream_is_rejected(self):
        meta = b'plantuml\0\x01\x00\0\0' + zlib.compress(b'harmless') + zlib.compress(b'<ownedRule/>')
        data = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)) +
                chunk(b'iTXt', meta) + chunk(b'IDAT', zlib.compress(b'\0\xff\xff\xff')) + chunk(b'IEND', b''))
        (self.pack / 'extra.png').write_bytes(data)
        with self.assertRaisesRegex(ValueError, 'invalid or unsafe PNG metadata'):
            check(self.root)

    def test_decoded_json_keys_and_values_cannot_hide_private_data(self):
        path = self.pack / 'facts.json'
        for text in ('{"\\u002fhome\\u002fprivate": 1}', '{"note":"\\u003cownedRule id=1/\\u003e"}',
                     '{"nested":{"work/secret": true}}'):
            path.write_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                check(self.root)

    def test_xml_entities_cannot_hide_private_paths(self):
        (self.pack / 'diagram.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><text>&#47;home&#47;private</text></svg>')
        with self.assertRaisesRegex(ValueError, 'private path'):
            check(self.root)

    def test_unknown_embedded_svg_data_is_rejected(self):
        path = self.pack / 'diagram.svg'
        for prefix in ('data:', 'data&#58;', 'DATA:'):
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="' + prefix + 'text/plain;base64,PHBhY2thZ2VkRWxlbWVudC8+"/></svg>')
            with self.subTest(prefix=prefix), self.assertRaisesRegex(ValueError, 'unreviewed embedded data type'):
                check(self.root)

    def test_font_magic_does_not_authorize_unreviewed_payload(self):
        (self.pack / 'diagram.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><style>x{src:url(data:font/woff2;base64,d09G MjxwYWNrYWdlZEVsZW1lbnQ+)}' .replace(' ', '') + '</style></svg>')
        with self.assertRaisesRegex(ValueError, 'unreviewed embedded font bytes'):
            check(self.root)

    def test_css_import_or_escape_is_rejected(self):
        path = self.pack / 'diagram.svg'
        for css in ('@import "https://example.invalid/x.css";', r'x{src:url(\68ttps://example.invalid/x)}'):
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><style>' + css + '</style></svg>')
            with self.subTest(css=css), self.assertRaisesRegex(ValueError, 'CSS import or escape'):
                check(self.root)

    def test_executable_svg_event_attribute_is_rejected(self):
        (self.pack / 'diagram.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" onload="bad()"/>')
        with self.assertRaisesRegex(ValueError, 'event attribute'):
            check(self.root)

    def test_metadata_keyword_and_translated_keyword_are_checked(self):
        for meta in (b'/home/private\0harmless', b'plantuml\0\x00\x00\0/home/private\0harmless',
                     b'plantuml\0\x00\x00/home/private\0\0harmless'):
            kind = b'tEXt' if meta.startswith(b'/home') else b'iTXt'
            data = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)) +
                    chunk(kind, meta) + chunk(b'IDAT', zlib.compress(b'\0\xff\xff\xff')) + chunk(b'IEND', b''))
            (self.pack / 'hidden.png').write_bytes(data)
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'unsafe PNG metadata'):
                check(self.root)

    def test_missing_root_or_empty_package_cannot_pass(self):
        with self.assertRaisesRegex(ValueError, 'root does not exist'):
            check(self.root / 'missing')
        with self.assertRaisesRegex(ValueError, 'no reference-package files'):
            check(self.root)


if __name__ == '__main__':
    unittest.main()
