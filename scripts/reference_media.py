"""Bounded static media checks for the selected reference derivatives; no renderer."""
import base64
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path


def inspect_svg(path, font_source, notice, font_directory=None):
    path = Path(path)
    text = path.read_text()
    root = ET.fromstring(text)
    records = json.loads(Path(font_source).read_text())['files']
    fonts = {r['sha256']: r for r in records if r['file'].endswith('.woff2')}
    license_record = next(r for r in records if r['file'] == 'LICENSE.txt')
    if hashlib.sha256(Path(notice).read_bytes()).hexdigest() != license_record['sha256']:
        raise ValueError(f'{path.name}: missing or changed font license')
    payloads = []
    for uri in re.findall(r'data:[^\s\"\)\'<>]+', text):
        if not uri.startswith('data:font/woff2;base64,'):
            raise ValueError(f'{path.name}: unsupported embedded data URI')
        data = base64.b64decode(uri.partition(',')[2], validate=True)
        digest = hashlib.sha256(data).hexdigest()
        if data[:4] != b'wOF2' or digest not in fonts or len(data) != fonts[digest]['bytes']:
            raise ValueError(f'{path.name}: unrecognized embedded font')
        record = fonts[digest]
        if font_directory is not None and data != (Path(font_directory) / record['file']).read_bytes():
            raise ValueError(f'{path.name}: embedded font differs from standalone binary')
        payloads.append({'file': record['file'], 'bytes': len(data), 'sha256': digest})
    if not payloads:
        raise ValueError(f'{path.name}: expected embedded fonts are absent')
    for element in root.iter():
        if element.tag.rsplit('}', 1)[-1] in ('script', 'foreignObject'):
            raise ValueError(f'{path.name}: active SVG content is outside the reviewed scope')
        for key, value in element.attrib.items():
            if key.rsplit('}', 1)[-1].startswith('on'):
                raise ValueError(f'{path.name}: active SVG event handler')
            if key.rsplit('}', 1)[-1] == 'href' and not value.startswith('#'):
                raise ValueError(f'{path.name}: external or embedded image/link reference')
    return {'svg': path.name, 'embedded_fonts': payloads, 'other_data_uris': 0}


def inspect_png(path):
    """Validate chunk boundaries/CRCs and expose metadata for explicit review."""
    data = Path(path).read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Invalid PNG signature: ' + str(path))
    pos = 8
    chunks = []
    metadata = []
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError('Truncated PNG chunk')
        length = struct.unpack('>I', data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        end = pos + 12 + length
        if end > len(data) or zlib.crc32(kind + payload) & 0xffffffff != struct.unpack('>I', data[end - 4:end])[0]:
            raise ValueError('Invalid PNG chunk CRC/boundary')
        chunks.append(kind.decode('ascii'))
        if kind in (b'tEXt', b'zTXt', b'iTXt', b'eXIf'):
            metadata.append({'kind': kind.decode(), 'bytes': length, 'sha256': hashlib.sha256(payload).hexdigest()})
        pos = end
        if kind == b'IEND':
            break
    if pos != len(data) or not chunks or chunks[-1] != 'IEND':
        raise ValueError('Unexpected PNG trailer or missing IEND')
    return {'png': Path(path).name, 'chunks': chunks, 'metadata': metadata}
