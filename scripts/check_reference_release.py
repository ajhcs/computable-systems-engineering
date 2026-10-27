#!/usr/bin/env python3
"""Check selected reference-package files for obvious raw-source and privacy leaks.

This is a packaging screen, not a source-rights, engineering-fidelity, or
acceptance determination. Human source-specific review is still required.
"""
import argparse
import base64
import binascii
from hashlib import sha256
import json
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIRS = (
    'examples/engineering-reference', 'examples/engineering-reference-extension',
    'examples/diagram-style-prototypes', 'examples/native-v2-composition',
    'examples/pharmacy-source-view-reference', 'examples/ecosystem-diagram-reference',
    'examples/industrial-project-reference',
)
RAW_MARKERS = re.compile(r'<(?:ownedRule|packagedElement|ownedBehavior)\b|\bxmi:type\s*=|["\']source_xml["\']\s*:', re.I)
PRIVATE_MARKERS = re.compile(r'/workspace/|/home/|/tmp/|file:///|-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----|ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{32,}')
PRIVATE_RECEIPT_PATH = re.compile(r'(^|[\s=:])(?:work/|\.cache/|\.tmp/)')
FORBIDDEN_SUFFIXES = {'.xml', '.mdzip', '.zip', '.pdf'}
MAX_METADATA = 1_000_000
PNG_CHUNKS = {b'IHDR', b'PLTE', b'IDAT', b'IEND', b'tRNS', b'gAMA', b'cHRM', b'sRGB', b'pHYs', b'tEXt', b'zTXt', b'iTXt'}
# Reviewed IBM Plex WOFF2 bytes; bundled OFL notices travel with their views.
REVIEWED_FONT_SHA256 = {
    'ba204497f16b6d334cee9d1e963a831b73e3a56e1d6300a8489d18df7214b350',
    '5660f8a658f8bb50dbc005232f885eadffd2bc1c235c4f6fbb63469d1f9cde6d',
    'ba711a3085ff9f27440b6b9c4550cfc47c97bf36591d5da958b975bb3add8c1a',
    'f78048030eab62e860efa39a0df79e2e5581bf122eb95b9bc42c0b8a4988d205',
}


def inspect_text(data, name):
    text = data.decode('utf-8')
    if PRIVATE_MARKERS.search(text):
        raise ValueError(f'{name}: private path or credential marker')
    if RAW_MARKERS.search(text):
        raise ValueError(f'{name}: raw source-XML marker')
    return text


def png_metadata(data, name):
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError(f'{name}: invalid PNG signature')
    pos, ended, seen_header, seen_image = 8, False, False, False
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError(f'{name}: truncated PNG chunk')
        n = struct.unpack('>I', data[pos:pos + 4])[0]
        if pos + n + 12 > len(data):
            raise ValueError(f'{name}: truncated PNG payload')
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        crc = struct.unpack('>I', data[pos + 8 + n:pos + 12 + n])[0]
        if zlib.crc32(kind + body) & 0xffffffff != crc:
            raise ValueError(f'{name}: invalid PNG chunk CRC')
        pos += n + 12
        if kind not in PNG_CHUNKS:
            raise ValueError(f'{name}: unreviewed PNG chunk {kind!r}')
        if not seen_header:
            if kind != b'IHDR' or n != 13:
                raise ValueError(f'{name}: missing PNG header')
            seen_header = True
        elif kind == b'IHDR':
            raise ValueError(f'{name}: duplicate PNG header')
        if kind == b'IDAT':
            seen_image = True
        if kind in (b'tEXt', b'zTXt', b'iTXt'):
            try:
                keyword, rest = body.split(b'\0', 1)
                if not 1 <= len(keyword) <= 79:
                    raise ValueError('invalid metadata keyword')
                inspect_text(keyword.decode('latin-1').encode('utf-8'), name + ' metadata keyword')
                if kind == b'tEXt':
                    payload = rest.decode('latin-1').encode('utf-8')
                elif kind == b'zTXt':
                    if rest[0] != 0:
                        raise ValueError('unknown compression')
                    payload = decompress_metadata(rest[1:])
                else:
                    flag, method, rest = rest[0], rest[1], rest[2:]
                    language, rest = rest.split(b'\0', 1)
                    translated, payload = rest.split(b'\0', 1)
                    inspect_text(language, name + ' metadata language')
                    inspect_text(translated, name + ' translated metadata keyword')
                    if method != 0 or flag not in (0, 1):
                        raise ValueError('unknown international-text format')
                    if flag:
                        payload = decompress_metadata(payload)
                if len(payload) > MAX_METADATA:
                    raise ValueError('metadata too large')
                inspect_text(payload, name + ' metadata')
            except (IndexError, UnicodeError, zlib.error, ValueError) as error:
                raise ValueError(f'{name}: invalid or unsafe PNG metadata: {error}') from error
        if kind == b'IEND':
            if n != 0 or not seen_image:
                raise ValueError(f'{name}: incomplete PNG image')
            ended = True
            break
    if not ended or pos != len(data):
        raise ValueError(f'{name}: missing PNG end or trailing data')


def decompress_metadata(data):
    stream = zlib.decompressobj()
    result = stream.decompress(data, MAX_METADATA + 1)
    if len(result) > MAX_METADATA or stream.unconsumed_tail or stream.unused_data or not stream.eof:
        raise ValueError('invalid or oversized compressed metadata')
    return result


def inspect_embedded_data(text, name):
    embedded = re.findall(r'(?<![A-Za-z0-9])data:([a-zA-Z0-9.+/-]+);base64,([A-Za-z0-9+/=]+)', text, re.I)
    if len(re.findall(r'(?<![A-Za-z0-9])data:', text, re.I)) != len(embedded):
        raise ValueError(f'{name}: unreviewed embedded data URI')
    for kind, encoded in embedded:
        if kind.lower() != 'font/woff2' or len(encoded) > 300_000:
            raise ValueError(f'{name}: unreviewed embedded data type')
        try:
            font = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValueError(f'{name}: invalid embedded font') from error
        if not font.startswith(b'wOF2') or sha256(font).hexdigest() not in REVIEWED_FONT_SHA256:
            raise ValueError(f'{name}: unreviewed embedded font bytes')


def inspect_file(path, name):
    if path.is_symlink():
        raise ValueError(f'{name}: reference-package symlinks require separate review')
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        raise ValueError(f'{name}: raw source document or archive is not allowed')
    data = path.read_bytes()
    if path.suffix.lower() == '.png':
        png_metadata(data, name)
        return
    if path.suffix.lower() == '.woff2':
        if not data.startswith(b'wOF2') or sha256(data).hexdigest() not in REVIEWED_FONT_SHA256:
            raise ValueError(f'{name}: unreviewed WOFF2 bytes')
        return
    text = inspect_text(data, name)
    if path.suffix.lower() == '.json':
        inspect_json(json.loads(text), name)
    elif path.suffix.lower() in ('.svg', '.drawio'):
        inspect_embedded_data(text, name)
        root = ET.fromstring(text)
        for element in root.iter():
            for value in (element.tag, element.text, element.tail, *element.attrib.keys(), *element.attrib.values()):
                if value:
                    inspect_text(value.encode('utf-8'), name + ' decoded XML')
                    inspect_embedded_data(value, name + ' decoded XML')
                    if re.search(r'url\(\s*["\']?(?:https?:|file:|javascript:|//)', value, re.I):
                        raise ValueError(f'{name}: external or executable diagram resource')
            if element.tag.rsplit('}', 1)[-1].lower() in ('script', 'foreignobject'):
                raise ValueError(f'{name}: executable or embedded HTML in diagram')
            if element.tag.rsplit('}', 1)[-1].lower() == 'style':
                inspect_css(element.text or '', name)
            for key, value in element.attrib.items():
                local_key = key.rsplit('}', 1)[-1].lower()
                if local_key.startswith('on'):
                    raise ValueError(f'{name}: executable diagram event attribute')
                if local_key == 'style':
                    inspect_css(value, name)
                if local_key == 'href' and re.match(r'^(?:https?:|file:|javascript:|//)', value.strip(), re.I):
                    raise ValueError(f'{name}: external or executable diagram link')


def inspect_css(text, name):
    if re.search(r'@import\b', text, re.I) or '\\' in text:
        raise ValueError(f'{name}: unreviewed CSS import or escape')


def inspect_json(value, name):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() == 'source_xml':
                raise ValueError(f'{name}: raw source-XML key')
            inspect_json(key, name)
            inspect_json(item, name)
    elif isinstance(value, list):
        for item in value:
            inspect_json(item, name)
    elif isinstance(value, str):
        inspect_text(value.encode('utf-8'), name + ' decoded JSON')
        if PRIVATE_RECEIPT_PATH.search(value):
            raise ValueError(f'{name}: local work path in JSON')


def check(root=ROOT):
    if not root.is_dir():
        raise ValueError('reference checkout root does not exist')
    count = 0
    for name in REFERENCE_DIRS:
        directory = root / name
        if not directory.exists():
            continue
        if directory.is_symlink():
            raise ValueError(f'{name}: reference-package symlink is not allowed')
        for path in sorted(directory.rglob('*')):
            if path.is_file() or path.is_symlink():
                inspect_file(path, str(path.relative_to(root)))
                count += 1
    if not count:
        raise ValueError('no reference-package files found')
    return {'files_checked':count, 'claim':'bounded packaging screen; source rights and engineering fidelity require separate review'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='checkout containing the reference package')
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.root), indent=2))
    except (OSError, UnicodeError, ValueError, ET.ParseError) as error:
        print(f'Reference release screen failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
