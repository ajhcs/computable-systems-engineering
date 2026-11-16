"""Pinned DejaVu typography for opt-in engineering-palette presentations.

Advances come from the exact bundled TrueType fonts with kerning and ligatures
disabled. This module does not change the existing alpha.6 style/font API.
"""
import base64
from functools import lru_cache
from hashlib import sha256
import json
import math
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / 'assets/engineering-library/fonts'
MANIFEST_SHA256 = '43c8d4dba54124f29d4c07718bfcefbf171fa3658558130b13d8b4f95d3b92e5'
_FILES = ('manifest.json', 'metrics.json', 'DejaVu-COPYRIGHT.txt', 'DejaVuSans.ttf',
          'DejaVuSans-Bold.ttf', 'DejaVuSansMono.ttf', 'DejaVuSansMono-Bold.ttf')
_FACES = {('DejaVu Sans', 400): 'DejaVuSans.ttf',
          ('DejaVu Sans', 700): 'DejaVuSans-Bold.ttf',
          ('DejaVu Sans Mono', 400): 'DejaVuSansMono.ttf',
          ('DejaVu Sans Mono', 700): 'DejaVuSansMono-Bold.ttf'}
_CHARS = frozenset(chr(i) for i in range(32, 127)) | {'\u00b7'}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        _need(key not in result, 'Duplicate kit-font JSON key: ' + key)
        result[key] = value
    return result


def _json(raw):
    return json.loads(raw, object_pairs_hook=_unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite kit-font value: ' + value)))


def _validated():
    root = Path(ASSETS).resolve()
    try:
        signature = tuple((name, p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
                          for name in _FILES for p in (root / name,))
    except OSError as exc:
        raise ValueError('Missing or unreadable kit-font asset') from exc
    return _load(root, signature)


@lru_cache(maxsize=8)
def _load(root, signature):
    """Revalidate after asset metadata changes; no mutable public cache is exposed."""
    payloads = {name: (root / name).read_bytes() for name in _FILES}
    raw = payloads['manifest.json']
    _need(sha256(raw).hexdigest() == MANIFEST_SHA256, 'Kit font manifest digest mismatch')
    manifest = _json(raw)
    _need(manifest.get('version') == 1 and isinstance(manifest.get('faces'), list), 'Unsupported kit-font manifest')
    metrics_raw = payloads['metrics.json']
    _need(manifest.get('metrics', {}).get('file') == 'metrics.json' and
          sha256(metrics_raw).hexdigest() == manifest['metrics'].get('sha256'), 'Kit font metrics digest mismatch')
    metrics = _json(metrics_raw)
    _need(metrics.get('version') == 1 and isinstance(metrics.get('faces'), dict), 'Unsupported kit-font metrics')
    seen = set()
    for face in manifest['faces']:
        identity = (face.get('family'), face.get('weight'))
        _need(identity in _FACES and identity not in seen and face.get('file') == _FACES[identity],
              'Unexpected or duplicate kit font face')
        seen.add(identity)
        font_raw = payloads[face['file']]
        _need(len(font_raw) == face.get('bytes') and sha256(font_raw).hexdigest() == face.get('sha256'),
              'Kit font digest mismatch: ' + face['file'])
        _need(face.get('notice') == 'DejaVu-COPYRIGHT.txt' and
              sha256(payloads[face['notice']]).hexdigest() == face.get('notice_sha256'),
              'Kit font notice digest mismatch')
        key = identity[0] + ':' + str(identity[1])
        value = metrics['faces'].get(key, {})
        _need(value.get('font_sha256') == face['sha256'] and
              type(value.get('units')) is int and 0 < value['units'] <= 16384 and
              isinstance(value.get('advances'), dict) and set(value['advances']) == _CHARS and
              all(type(v) is int and v > 0 for v in value['advances'].values()),
              'Kit font metrics coverage or face mismatch: ' + key)
    _need(seen == set(_FACES) and set(metrics['faces']) == {f + ':' + str(w) for f, w in _FACES},
          'Incomplete kit-font face coverage')
    return manifest, metrics, payloads


def manifest_bytes():
    """Return exact validated provenance bytes for a native output bundle."""
    return _validated()[2]['manifest.json']


def metrics_bytes():
    """Return exact validated advance-metric bytes for a native output bundle."""
    return _validated()[2]['metrics.json']


def font_css():
    """Embed exact local TTF bytes and their preserved license notice."""
    manifest, _, payloads = _validated()
    notice = payloads['DejaVu-COPYRIGHT.txt'].decode('utf-8')
    _need('*/' not in notice and '</style' not in notice.lower(), 'Unsafe kit font notice')
    css = ['/*\n' + notice + '\n*/']
    for face in manifest['faces']:
        uri = base64.b64encode(payloads[face['file']]).decode('ascii')
        css.append("@font-face{font-family:'" + face['family'] + "';font-style:normal;font-weight:" +
                   str(face['weight']) + ';src:url(data:font/ttf;base64,' + uri + ") format('truetype');}")
    return '\n'.join(css)


def require_supported_text(text):
    _need(isinstance(text, str) and bool(text) and all(char in _CHARS for char in text),
          'Kit fonts qualify printable ASCII plus middle dot only')


def _face(text, size, family, weight):
    require_supported_text(text)
    _need(type(size) in (int, float) and math.isfinite(size) and size > 0, 'Kit font size must be finite and positive')
    _need(isinstance(family, str) and type(weight) is int and (family, weight) in _FACES,
          'Unsupported kit font family or weight')
    return _validated()[1]['faces'][family + ':' + str(weight)]


def text_width(text, size, family='DejaVu Sans', weight=400):
    """Exact advance sum at the requested size; no kerning or text distortion."""
    face = _face(text, size, family, weight)
    return sum(face['advances'][char] for char in text) * size / face['units']


def wrap_text(text, max_width, size, family='DejaVu Sans', weight=400):
    """Wrap at spaces, then glyph boundaries; joined lines retain exact text."""
    face = _face(text, size, family, weight)
    _need(type(max_width) in (int, float) and math.isfinite(max_width) and max_width > 0,
          'Kit text region must be finite and positive')
    lines, start = [], 0
    while start < len(text):
        end, last_space, width = start, None, 0
        while end < len(text):
            advance = face['advances'][text[end]] * size / face['units']
            _need(advance <= max_width, 'Kit text region cannot contain one qualified glyph')
            if width + advance > max_width and end > start:
                break
            width += advance
            end += 1
            if text[end-1] == ' ':
                last_space = end
        if end < len(text) and last_space is not None:
            end = last_space
        lines.append(text[start:end])
        start = end
    return lines
