"""Bounded, explicit presentation selections; no font substitution or model authority."""
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import struct
import xml.etree.ElementTree as ET

VERSION = 'cse.visual-profile/1'
CLAIM = 'selected_visual_resources_present_and_hashed_only'
LIMITS = {'record_bytes': 262144, 'resource_bytes': 33554432, 'total_resource_bytes': 134217728,
          'resources': 64, 'selectors': 32, 'svg_nodes': 10000}
ID = re.compile(r'^[A-Za-z][A-Za-z0-9_.-]{0,95}$')
COLOR = re.compile(r'^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$')
HASH = re.compile(r'^[0-9a-f]{64}$')


class Invalid(ValueError):
    pass


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def _read(path, limit):
    path = Path(path)
    if not path.is_file() or not 0 < path.stat().st_size <= limit:
        raise Invalid('Expected a nonempty bounded regular file: ' + str(path))
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if not 0 < len(data) <= limit:
        raise Invalid('Resource changed or exceeds byte limit: ' + str(path))
    return data


def load(path):
    raw = _read(path, LIMITS['record_bytes'])
    try:
        record = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                            parse_constant=lambda _: (_ for _ in ()).throw(Invalid('Nonfinite JSON')))
    except (UnicodeError, RecursionError) as exc:
        raise Invalid('Invalid UTF-8 or excessive JSON nesting') from exc
    return record, sha256(raw).hexdigest()


def _object(value, required, optional, where):
    if (type(value) is not dict or not set(required) <= set(value) or
            set(value) - set(required) - set(optional)):
        raise Invalid(where + ' has missing or unsupported fields')


def _text(value, where, maximum=512):
    if (type(value) is not str or not 1 <= len(value.strip()) <= maximum or
            any(ord(c) < 32 for c in value)):
        raise Invalid(where + ' needs bounded nonempty text')


def _identifier(value, where):
    if type(value) is not str or not ID.fullmatch(value):
        raise Invalid(where + ' needs a stable identifier')


def _number(value, lower, upper, where):
    if type(value) not in (int, float) or not lower <= value <= upper:
        raise Invalid(where + ' is outside its supported range')


def _selectors(value, where):
    if type(value) is not list or not 1 <= len(value) <= LIMITS['selectors']:
        raise Invalid(where + ' needs a nonempty bounded selector list')
    for selector in value:
        _text(selector, where, 256)
        if any(c in selector for c in '{};@\\'):
            raise Invalid(where + ' cannot contain CSS declarations or escapes')


def _resource_name(name):
    _text(name, 'resource path')
    value = name[len('runtime:'):] if name.startswith('runtime:') else name
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or '..' in path.parts or ':' in value or
            '\\' in value or path.as_posix() != value or value == '.'):
        raise Invalid('Use a normalized project-relative or runtime: resource path')


def validate_profile(profile):
    """Validate declared presentation structure, without reading any resources."""
    _object(profile, ('version', 'id', 'revision', 'authority', 'fonts', 'typography',
                      'palette', 'assets'), ('figure', 'table'), 'profile')
    if profile['version'] != VERSION:
        raise Invalid('Unsupported visual profile version')
    _identifier(profile['id'], 'profile.id')
    _text(profile['revision'], 'profile.revision', 128)
    _object(profile['authority'], ('kind', 'source'), (), 'authority')
    if profile['authority']['kind'] not in ('request', 'client', 'project', 'example'):
        raise Invalid('authority.kind must name request, client, project or example')
    _text(profile['authority']['source'], 'authority.source')
    fonts = profile['fonts']
    assets = profile['assets']
    if type(fonts) is not list or not 1 <= len(fonts) <= LIMITS['resources']:
        raise Invalid('fonts needs a nonempty bounded list')
    if type(assets) is not list or len(assets) + len(fonts) > LIMITS['resources']:
        raise Invalid('Too many or malformed selected resources')
    font_ids, resource_ids = set(), set()
    for font in fonts:
        _object(font, ('id', 'family', 'path', 'weight'),
                ('style', 'postscript_name', 'sha256', 'source', 'license'), 'font')
        _identifier(font['id'], 'font.id')
        if font['id'] in resource_ids:
            raise Invalid('Resource IDs must be unique')
        font_ids.add(font['id']); resource_ids.add(font['id'])
        _text(font['family'], 'font.family', 128)
        if any(c in font['family'] for c in '\'";{}\\'):
            raise Invalid('font.family cannot contain CSS delimiters')
        _resource_name(font['path'])
        if type(font['weight']) is not int or not 1 <= font['weight'] <= 1000:
            raise Invalid('font.weight must be an integer from 1 through 1000')
        if font.get('style', 'normal') not in ('normal', 'italic', 'oblique'):
            raise Invalid('Unsupported font style')
        for key in ('postscript_name', 'source', 'license'):
            if key in font: _text(font[key], 'font.' + key)
        if 'sha256' in font and (type(font['sha256']) is not str or not HASH.fullmatch(font['sha256'])):
            raise Invalid('font.sha256 must be a lowercase digest')
    typography = profile['typography']
    if type(typography) is not dict or not 1 <= len(typography) <= 32:
        raise Invalid('typography needs bounded role mappings')
    for role, value in typography.items():
        _identifier(role, 'typography role')
        _object(value, ('font', 'size_pt', 'selectors'), (), 'typography.' + role)
        if type(value['font']) is not str or value['font'] not in font_ids:
            raise Invalid('Typography refers to an unselected font')
        _number(value['size_pt'], 1, 144, 'size_pt')
        _selectors(value['selectors'], 'typography selectors')
    palette = profile['palette']
    if type(palette) is not dict or len(palette) > 64:
        raise Invalid('palette needs bounded named colors')
    for key, color in palette.items():
        _identifier(key, 'palette role')
        if type(color) is not str or not COLOR.fullmatch(color):
            raise Invalid('Palette colors must be #RGB or #RRGGBB')
    for field in ('figure', 'table'):
        if field not in profile: continue
        treatment = profile[field]
        _object(treatment, ('selectors',), ('rule_color', 'rule_width_pt', 'padding_pt'), field)
        _selectors(treatment['selectors'], field + ' selectors')
        if 'rule_color' in treatment and (type(treatment['rule_color']) is not str or treatment['rule_color'] not in palette):
            raise Invalid('Treatment refers to an unknown palette role')
        if 'rule_width_pt' in treatment:
            _number(treatment['rule_width_pt'], 0, 12, 'rule_width_pt')
        if 'padding_pt' in treatment:
            _number(treatment['padding_pt'], 0, 144, 'padding_pt')
    for asset in assets:
        _object(asset, ('id', 'path', 'kind', 'role', 'source', 'license', 'adaptations'),
                ('sha256',), 'asset')
        _identifier(asset['id'], 'asset.id')
        if asset['id'] in resource_ids:
            raise Invalid('Resource IDs must be unique')
        resource_ids.add(asset['id'])
        _resource_name(asset['path'])
        if asset['kind'] not in ('svg', 'image'):
            raise Invalid('asset.kind must be svg or image')
        if asset['role'] not in ('formal-symbol', 'illustration', 'editorial-art',
                                 'logo', 'photograph', 'texture'):
            raise Invalid('Unsupported asset presentation role')
        for key in ('source', 'license'):
            _text(asset[key], 'asset.' + key)
        if type(asset['adaptations']) is not list or len(asset['adaptations']) > 32:
            raise Invalid('asset.adaptations needs a bounded list')
        for adaptation in asset['adaptations']:
            _text(adaptation, 'adaptation')
        if 'sha256' in asset and (type(asset['sha256']) is not str or not HASH.fullmatch(asset['sha256'])):
            raise Invalid('asset.sha256 must be a lowercase digest')
    return profile


def select_profile(explicit=None, client=None, project=None, example=None):
    """Select a whole declared profile; never silently merge or try a lower priority."""
    for label, value in (('explicit', explicit), ('client', client),
                         ('project', project), ('example', example)):
        if value is not None:
            return label, value
    raise Invalid('No visual profile was selected')


def resolve_resource(name, root, runtime=None):
    _resource_name(name)
    if name.startswith('runtime:'):
        if runtime is None:
            raise Invalid('runtime: resources require an explicit runtime root')
        base, relative = Path(runtime).resolve(strict=True), name[len('runtime:'):]
    else:
        base, relative = Path(root).resolve(strict=True), name
    if not base.is_dir(): raise Invalid('Resource root must be a directory')
    target = (base / relative).resolve(strict=True)
    if not target.is_relative_to(base):
        raise Invalid('Resource path escapes its declared root')
    return target


def svg_geometry(raw):
    """Fingerprint native geometry and transforms, excluding text, IDs and paint."""
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise Invalid('SVG entity declarations are unsupported')
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise Invalid('Malformed selected SVG') from exc
    if root.tag.rsplit('}', 1)[-1] != 'svg':
        raise Invalid('Selected SVG resource needs an SVG root')
    nodes = list(root.iter())
    if len(nodes) > LIMITS['svg_nodes']:
        raise Invalid('Selected SVG exceeds node limit')
    attrs = {'d', 'points', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'width', 'height',
             'rx', 'ry', 'cx', 'cy', 'r', 'transform', 'viewBox', 'preserveAspectRatio'}
    geometry = [(node.tag.rsplit('}', 1)[-1],
                 sorted((k, v) for k, v in node.attrib.items() if k in attrs))
                for node in nodes if node.tag.rsplit('}', 1)[-1] not in ('style', 'title', 'desc', 'metadata', 'text', 'tspan')]
    return sha256(json.dumps(geometry, separators=(',', ':')).encode()).hexdigest()


def font_metadata(raw):
    """Read uncompressed SFNT names/weight; WOFF identity remains a render check."""
    magic = raw[:4]
    formats = {b'wOF2': 'woff2', b'wOFF': 'woff', b'OTTO': 'otf', b'\x00\x01\x00\x00': 'ttf'}
    minimum = {b'wOF2': 48, b'wOFF': 44, b'OTTO': 12, b'\x00\x01\x00\x00': 12}
    if magic not in formats or len(raw) < minimum[magic]:
        raise Invalid('Selected font is not a supported TTF, OTF, WOFF or WOFF2 file')
    info = {'format': formats[magic], 'identity_scope': 'requires_rendered_glyph_and_pdf_check'}
    if magic in (b'wOFF', b'wOF2'):
        return info
    try:
        count = struct.unpack_from('>H', raw, 4)[0]
        if count > 512: raise Invalid('Too many font tables')
        tables = {}
        for i in range(count):
            tag, _, offset, length = struct.unpack_from('>4sIII', raw, 12 + i * 16)
            if offset + length > len(raw): raise Invalid('Font table extends beyond file')
            tables[tag] = raw[offset:offset + length]
        names = tables.get(b'name', b'')
        if names:
            _, total, start = struct.unpack_from('>HHH', names)
            values = {}
            for i in range(total):
                platform, encoding, language, kind, length, offset = struct.unpack_from('>HHHHHH', names, 6 + i * 12)
                encoded = names[start + offset:start + offset + length]
                value = encoded.decode('utf-16-be' if platform in (0, 3) else 'mac_roman', errors='replace')
                if kind in (1, 4, 6, 16) and (kind not in values or platform == 3): values[kind] = value
            info.update({'family': values.get(16, values.get(1)),
                         'postscript_name': values.get(6), 'full_name': values.get(4)})
        os2 = tables.get(b'OS/2', b'')
        if len(os2) >= 6: info['weight'] = struct.unpack_from('>H', os2, 4)[0]
        return info
    except (struct.error, UnicodeError) as exc:
        raise Invalid('Malformed selected font tables') from exc


def preflight(profile, root, runtime=None):
    """Check selected files and capture identities; do not claim rendered fidelity."""
    validate_profile(profile)
    result = {'version': VERSION, 'status': 'pass', 'claim_scope': CLAIM,
              'profile': profile, 'fonts': [], 'assets': [], 'findings': []}
    total_bytes = 0
    for group in ('fonts', 'assets'):
        for declared in profile[group]:
            entry = dict(declared)
            try:
                path = resolve_resource(declared['path'], root, runtime)
                available = min(LIMITS['resource_bytes'], LIMITS['total_resource_bytes'] - total_bytes)
                raw = _read(path, available)
                total_bytes += len(raw)
                digest = sha256(raw).hexdigest()
                if 'sha256' in declared and declared['sha256'] != digest:
                    raise Invalid('Selected source differs from its retained digest')
                entry.update({'resolved_path': str(path), 'sha256': digest, 'bytes': len(raw)})
                if group == 'fonts':
                    metadata = font_metadata(raw)
                    entry.update({'format': metadata['format'], 'font_metadata': metadata})
                    for key in ('postscript_name', 'weight'):
                        if key in declared and key in metadata and declared[key] != metadata[key]:
                            raise Invalid('Selected font ' + key + ' differs from font table')
                elif declared['kind'] == 'svg':
                    entry['svg_geometry_sha256'] = svg_geometry(raw)
                elif not (raw.startswith(b'\x89PNG\r\n\x1a\n') or raw.startswith(b'\xff\xd8\xff') or
                          raw.startswith((b'GIF87a', b'GIF89a')) or
                          (raw.startswith(b'RIFF') and raw[8:12] == b'WEBP')):
                    raise Invalid('Selected image must be PNG, JPEG, GIF or WebP')
                result[group].append(entry)
            except (OSError, ValueError) as exc:
                result['status'] = 'fail'
                result['findings'].append({'id': declared['id'], 'status': 'fail', 'detail': str(exc)})
    return result
