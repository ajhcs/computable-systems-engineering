"""Physical-view extension of the preserved DejaVu kit, without font fallback.

Original ASCII measurements/wrapping delegate unchanged to kit_fonts. The fixed
additional character profile uses advances generated from those same exact TTFs.
This is not general Unicode shaping or permission to normalize engineering text.
"""
from functools import lru_cache
from hashlib import sha256
import math
from pathlib import Path
from . import kit_fonts as original

ASSETS = original.ASSETS
_FILES = original._FILES
MANIFEST_SHA256 = original.MANIFEST_SHA256
font_css = original.font_css
manifest_bytes = original.manifest_bytes
metrics_bytes = original.metrics_bytes
PROFILE_PATH = Path(__file__).resolve().parents[1]/'assets/workbench/composition-font-metrics.json'
PROFILE_SHA256 = 'd786a2ff7f806b2a61f9eb0643733fbba56f0643e917932837f5be4beaec1577'


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _validated_profile():
    # Validate original bytes/notices too, rather than trusting the extension's
    # embedded source digests or using a system font with a matching name.
    original._validated()
    path = Path(PROFILE_PATH).resolve()
    stat = path.stat()
    return _cached(path, (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns), original.MANIFEST_SHA256)


@lru_cache(maxsize=8)
def _cached(path, signature, manifest_hash):
    raw = path.read_bytes()
    _need(sha256(raw).hexdigest() == PROFILE_SHA256, 'Composition font-profile digest mismatch')
    profile = original._json(raw)
    _need(profile.get('version') == 'cse-composition-fonts-1'
          and profile.get('source_manifest_sha256') == manifest_hash, 'Unsupported composition font profile')
    _, metrics, _ = original._validated()
    faces = profile.get('faces')
    _need(isinstance(faces, dict) and set(faces) == set(metrics['faces']), 'Incomplete composition font faces')
    for key, face in faces.items():
        source = metrics['faces'][key]
        _need(face.get('font_sha256') == source['font_sha256'] and face.get('units') == source['units'],
              'Composition metrics use a different source font')
        advances = face.get('advances')
        _need(isinstance(advances, dict) and all(isinstance(c, str) and len(c) == 1
              and type(v) is int and v > 0 for c, v in advances.items()), 'Invalid composition glyph advances')
        _need(all(advances.get(c) == v for c, v in source['advances'].items()), 'Original kit advances changed')
    return profile, raw


def _profile():
    return _validated_profile()[0]


def profile_bytes():
    return _validated_profile()[1]


def require_supported_text(text):
    _need(isinstance(text, str) and bool(text), 'Engineering labels need nonempty text')
    if all(c in original._CHARS for c in text):
        return original.require_supported_text(text)
    faces = _profile()['faces']
    _need(all(any(c in face['advances'] for face in faces.values()) for c in text),
          'Text is outside the qualified DejaVu composition profile; no fallback or normalization')


def _face(text, size, family, weight):
    require_supported_text(text)
    _need(type(size) in (int, float) and math.isfinite(size) and size > 0, 'Kit font size must be finite and positive')
    _need(isinstance(family, str) and type(weight) is int and (family, weight) in original._FACES,
          'Unsupported kit font family or weight')
    face = _profile()['faces'][family+':'+str(weight)]
    _need(all(c in face['advances'] for c in text), 'Requested DejaVu face has no qualified glyph; no fallback')
    return face


def text_width(text, size, family='DejaVu Sans', weight=400):
    if isinstance(text, str) and all(c in original._CHARS for c in text):
        return original.text_width(text, size, family, weight)
    face = _face(text, size, family, weight)
    return sum(face['advances'][c] for c in text)*size/face['units']


def backing_padding(text):
    """Keep original padding; cover added glyph overhang at the fixed 28/24 roles.

    The source glyf audit bounds additional left/right ink below 11 units,
    independently checked against actual browser ink. Advances alone do not
    bound detached accents on wrapped monospace reference lines.
    """
    require_supported_text(text)
    return 8 if all(c in original._CHARS for c in text) else 12


def wrap_text(text, max_width, size, family='DejaVu Sans', weight=400):
    if isinstance(text, str) and all(c in original._CHARS for c in text):
        return original.wrap_text(text, max_width, size, family, weight)
    face = _face(text, size, family, weight)
    _need(type(max_width) in (int, float) and math.isfinite(max_width) and max_width > 0,
          'Kit text region must be finite and positive')
    lines, start = [], 0
    while start < len(text):
        end, last_space, width = start, None, 0
        while end < len(text):
            advance = face['advances'][text[end]]*size/face['units']
            _need(advance <= max_width, 'Kit text region cannot contain one qualified glyph')
            if width+advance > max_width and end > start:
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
