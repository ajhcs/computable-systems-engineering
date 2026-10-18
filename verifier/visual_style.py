"""Opt-in presentation values; never model meaning or engineering acceptance."""
import base64
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
import math
from pathlib import Path
import re

ASSETS = Path(__file__).resolve().parents[1] / "assets/diagram-style"
HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"Duplicate profile key: {key}")
        out[key] = value
    return out


def _color(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise ValueError("Colors must be opaque #RRGGBB values")
    return value


def contrast(foreground, background):
    """sRGB relative luminance ratio for opaque fields; not a readability verdict."""
    def luminance(color):
        channels = [int(_color(color)[i:i+2], 16) / 255 for i in (1, 3, 5)]
        channels = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
        return sum(v * weight for v, weight in zip(channels, (0.2126, 0.7152, 0.0722)))
    a, b = sorted((luminance(foreground), luminance(background)))
    return (b + 0.05) / (a + 0.05)


def load_profile(path=None):
    data = deepcopy(path) if isinstance(path, dict) else json.loads(
        Path(path or ASSETS / "profile.json").read_text(), object_pairs_hook=_unique,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Nonfinite {value}")))
    expected = {"version", "name", "direction_status", "palette", "fonts", "body_variants", "numeric_proposal", "limits"}
    if not isinstance(data, dict) or set(data) != expected or type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("Expected visual profile version 1 and exact documented fields")
    palette = data["palette"]
    if not isinstance(palette, dict) or set(palette) != {"paper", "ink", "light", "middle", "families"}:
        raise ValueError("Malformed palette")
    for key in ("paper", "ink", "light", "middle"):
        _color(palette[key])
    families = palette["families"]
    if not isinstance(families, dict) or set(families) != {"blue", "red", "amber", "green", "cyan", "violet", "tangerine", "berry"}:
        raise ValueError("Expected eight named palette families")
    for colors in families.values():
        if not isinstance(colors, dict) or set(colors) != {"shade", "base", "tint"}:
            raise ValueError("Family needs shade, base and tint")
        for value in colors.values():
            _color(value)
    if data["fonts"] != {"title": "Inter", "body": "Space Grotesk"}:
        raise ValueError("This slice qualifies only the bundled Inter / Space Grotesk faces")
    if data["direction_status"] != "selected_direction" or data["body_variants"] != {"status": "provisional", "values": ["paper", "white", "tint"]}:
        raise ValueError("Preserve selected direction and provisional body-variant distinction")
    numeric = data["numeric_proposal"]
    if not isinstance(numeric, dict) or set(numeric) != {"status", "title_size", "body_size", "stroke_display_px"} or numeric["status"] != "slice_specific_proposal":
        raise ValueError("Numeric defaults must remain a slice-specific proposal")
    for key, low, high in (("title_size", 32, 48), ("body_size", 20, 24), ("stroke_display_px", 1.5, 3)):
        v = numeric[key]
        if type(v) not in (int, float) or not math.isfinite(v) or not low <= v <= high:
            raise ValueError(f"Invalid proposed {key}")
    if data["limits"] != {"glyphs": "printable_ascii_plus_middle_dot", "color_semantics": "none"}:
        raise ValueError("Unsupported glyph or semantic color scope")
    for fill in (palette["paper"], "#ffffff", _tint(palette["families"]["violet"]["base"])):
        if contrast(palette["ink"], fill) < 4.5:
            raise ValueError("Insufficient text contrast for a body variant")
    if contrast(palette["families"]["tangerine"]["shade"], palette["families"]["violet"]["tint"]) < 4.5:
        raise ValueError("Insufficient orange-on-violet text contrast")
    return deepcopy(data)


def _tint(color):
    return "#" + "".join(f"{math.floor(0.94 * 255 + 0.06 * int(color[i:i+2], 16) + 0.5):02x}" for i in (1, 3, 5))


def require_supported_text(text):
    if not isinstance(text, str) or not text or any(not (32 <= ord(c) <= 126 or c == "\u00b7") for c in text):
        raise ValueError("This slice qualifies printable ASCII plus middle dot only; other glyphs need qualification")


def font_css():
    manifest = json.loads((ASSETS / "fonts/manifest.json").read_text())
    css = []
    included_notices = set()
    for item in manifest["faces"]:
        raw = (ASSETS / "fonts" / item["file"]).read_bytes()
        if sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("Bundled font integrity mismatch: " + item["file"])
        notice = (ASSETS / "fonts" / item["notice"]).read_bytes()
        if sha256(notice).hexdigest() != item["notice_sha256"]:
            raise ValueError("Bundled font notice integrity mismatch")
        if item["notice"] not in included_notices:
            notice_text = notice.decode("utf-8")
            if "*/" in notice_text or "</style" in notice_text.lower():
                raise ValueError("Unsafe font notice for embedded CSS")
            css.append("/*\n" + notice_text + "\n*/")
            included_notices.add(item["notice"])
        uri = base64.b64encode(raw).decode("ascii")
        css.append(f"@font-face{{font-family:'{item['family']}';font-style:normal;font-weight:{item['weight']};src:url(data:font/woff2;base64,{uri}) format('woff2');}}")
    return "\n".join(css)


def presentation_style(profile=None, *, body="paper", target_width=1200, canvas_width=1200):
    data = load_profile(profile)
    for value in (target_width, canvas_width):
        if type(value) not in (int, float) or not math.isfinite(value) or not 200 <= value <= 20000:
            raise ValueError("Canvas and target widths need finite values from 200 to 20000")
    if body not in ("paper", "white", "tint"):
        raise ValueError("Choose an explicit provisional body: paper, white or tint")
    palette, numeric = data["palette"], data["numeric_proposal"]
    if numeric["body_size"] * target_width / canvas_width < 16:
        raise ValueError("Target too small for 16px essential labels; use native width or scrolling")
    fill = {"paper": palette["paper"], "white": "#ffffff", "tint": _tint(palette["families"]["violet"]["base"])}[body]
    return {"ink": palette["ink"], "paper": palette["paper"], "fill": fill,
            "accent": palette["families"]["tangerine"]["shade"],
            "accent_fill": palette["families"]["violet"]["tint"],
            "stroke_width": numeric["stroke_display_px"] * canvas_width / target_width,
            "title_size": numeric["title_size"], "body_size": numeric["body_size"],
            "font_css": font_css(), "body_status": "provisional",
            "contrast": {"body_text": contrast(palette["ink"], fill),
                         "accent_text": contrast(palette["families"]["tangerine"]["shade"], palette["families"]["violet"]["tint"])}}


def text_width(text, size, family='Space Grotesk', weight=400):
    """Advance sum from bundled-face measurements; no fitting or text distortion."""
    require_supported_text(text)
    metrics = _font_metrics()
    face = metrics['faces'][f'{family}:{weight}']
    return sum(face['advances'][char] for char in text) * size / face['units']


def wrap_text(text, max_width, size, family='Space Grotesk', weight=400):
    """Wrap at spaces, then glyph boundaries; concatenated lines retain every character."""
    require_supported_text(text)
    lines, start = [], 0
    while start < len(text):
        end, last_space, width = start, None, 0
        while end < len(text):
            advance = text_width(text[end], size, family, weight)
            if width + advance > max_width and end > start:
                break
            if advance > max_width:
                raise ValueError('Text region cannot contain one qualified glyph')
            width += advance
            end += 1
            if text[end-1] == ' ':
                last_space = end
        if end < len(text) and last_space is not None:
            end = last_space
        lines.append(text[start:end])
        start = end
    return lines


@lru_cache(maxsize=1)
def _font_metrics():
    metrics = json.loads((ASSETS / 'fonts/metrics.json').read_text())
    manifest = json.loads((ASSETS / 'fonts/manifest.json').read_text())
    expected = {item['family'] + ':' + str(item['weight']): item['sha256'] for item in manifest['faces']}
    chars = set(chr(i) for i in range(32, 127)) | {'\u00b7'}
    if metrics.get('version') != 1 or set(metrics.get('faces', {})) != set(expected):
        raise ValueError('Unsupported qualified font metrics')
    for key, face in metrics['faces'].items():
        if face.get('font_sha256') != expected[key] or face.get('units') != 1000 or set(face.get('advances', {})) != chars:
            raise ValueError('Font metrics do not match bundled face or qualified coverage')
        if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in face['advances'].values()):
            raise ValueError('Invalid measured glyph advance')
    return metrics
