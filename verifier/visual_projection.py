"""Bounded, offline documentary presentations of native CSE-VIEWS function trees."""

from copy import deepcopy
from hashlib import sha256
from html import escape
import json
import math
from pathlib import Path
import shutil

from .engineering_views import check_views
from .sysml import check_sysml
from .visual_style import ASSETS, load_profile, presentation_style, require_supported_text

VERSION = "cse-visual-presentation-1.0"
CLAIM = "Simplified model-derived presentation: documentary decomposition; no behavioral or engineering acceptance claim."


class PresentationError(ValueError):
    """A refused presentation, retaining the authoritative checker diagnostics."""

    def __init__(self, report):
        self.report = report
        super().__init__(json.dumps(report, sort_keys=True, ensure_ascii=False))


def _json(value):
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def _digest(raw):
    return sha256(raw).hexdigest()


def project_function_tree(inventory, view_id):
    """Check native bindings first, then copy exact selected nodes and native names."""
    checks = check_views(inventory, {"version": 1, "views": [{"id": view_id, "kind": "function_tree"}]})
    if checks["status"] != "pass":
        raise PresentationError(checks)
    doc = next(doc for doc in inventory["documents"] if doc.get("name") == "cseViews")
    data = json.loads("\n".join(doc["body"].strip().splitlines()[1:]))
    view = next(view for view in data["views"] if view["id"] == view_id)
    actions = {item["qualified_name"]: item for item in inventory["actions"]}
    nodes = []
    for original in view["nodes"]:
        node = deepcopy(original)
        # Native name is display text; never humanize or infer a verb/object label.
        node["text"] = actions[node["element"]].get("name") or node["element"]
        if not isinstance(node["text"], str) or len(node["text"]) > 2000:
            raise ValueError("Presentation supports native names up to 2000 characters")
        nodes.append(node)
    if len(nodes) > 128 or max(node["level"] for node in nodes) > 16:
        raise ValueError("Presentation supports at most 128 nodes and 16 decomposition levels")
    return {"version": VERSION, "id": view_id, "kind": "function_tree", "claim_scope": CLAIM,
            "nodes": nodes, "view_checks": checks}


def render_function_tree(projection, *, profile=None, body="paper", target_width=1200):
    """Render an arrow-free indented tree; preserve labels as literal XML text."""
    if type(target_width) not in (int, float) or not math.isfinite(target_width) or not 320 <= target_width <= 8192:
        raise ValueError("Target width must be between 320 and 8192 pixels")
    # Recheck the public structural contract even when called without project().
    if projection.get("kind") != "function_tree" or projection.get("version") != VERSION:
        raise ValueError("Expected bounded function-tree presentation version")
    raw_nodes = [{key: n[key] for key in ("id", "element", "level", "parent")} for n in projection["nodes"]]
    inventory = {"documents": [{"name": "cseViews", "owner_kind": "Package", "body":
        "CSE-VIEWS/1.0\n" + json.dumps({"views": [{"id": projection["id"], "kind": "function_tree", "nodes": raw_nodes}]})}],
        "parts": [], "actions": [{"qualified_name": n["element"], "name": n["text"]} for n in projection["nodes"]]}
    checked = project_function_tree(inventory, projection["id"])
    nodes = checked["nodes"]
    require_supported_text(projection["id"])
    for node in nodes:
        require_supported_text(node["text"])
    by_id = {node["id"]: node for node in nodes}
    children = {node["id"]: [] for node in nodes}
    for node in nodes:
        if node["parent"] is not None:
            children[node["parent"]].append(node["id"])
    root = next(node["id"] for node in nodes if node["parent"] is None)
    order, pending = [], [root]
    while pending:
        key = pending.pop()
        order.append(key)
        pending.extend(reversed(children[key]))
    # Each label has its own row. Horizontal scrolling preserves readable type.
    # Conservative per-codepoint width prevents clipping without a font renderer dependency.
    width = max(1200, 96 + (len(projection["id"]) + 25) * 28, max(104 + n["level"] * 48 + max(len(n["text"]), len(n["id"])) * 30 for n in nodes))
    height = 160 + 104 * len(nodes)
    style = presentation_style(profile, body=body, target_width=target_width, canvas_width=width)
    positions = {key: (48 + by_id[key]["level"] * 48, 112 + i * 104) for i, key in enumerate(order)}
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{target_width}" height="{height * target_width / width:g}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
           f'<title id="title">{escape(projection["id"])} - function decomposition</title>',
           f'<desc id="description">{escape(CLAIM)}</desc>',
           '<style>' + escape(style['font_css']) + '</style>',
           f'<rect width="{width}" height="{height}" fill="{style["paper"]}"/>',
           f'<text x="48" y="48" fill="{style["ink"]}" font-family="Inter" font-size="{style["title_size"]}" font-weight="700">{escape(projection["id"])} - Function decomposition</text>',
           f'<text x="48" y="78" fill="{style["ink"]}" font-family="Space Grotesk" font-size="16">Documentary parent links · no behavioral or engineering acceptance claim</text>']
    for key in order:
        node = by_id[key]
        if node['parent'] is not None:
            px, py = positions[node['parent']]
            x, y = positions[key]
            svg.append(f'<path data-parent="{escape(node["parent"], quote=True)}" data-child="{key}" d="M {px+16} {py+72} V {y+36} H {x}" fill="none" stroke="{style["ink"]}" stroke-width="{style["stroke_width"]}"/>')
    geometry = []
    for key in order:
        node = by_id[key]
        x, y = positions[key]
        box_width = width - x - 48
        attrs = ' '.join(f'data-{k}="{escape(str(node[k]), quote=True)}"' for k in ("id", "element", "level", "parent"))
        svg.extend([f'<g {attrs}>', f'<rect x="{x}" y="{y}" width="{box_width}" height="72" fill="{style["fill"]}" stroke="{style["ink"]}" stroke-width="{style["stroke_width"]}"/>',
                    f'<text x="{x+16}" y="{y+24}" fill="{style["ink"]}" font-family="Space Grotesk" font-size="{style["body_size"]}">{key} · level {node["level"]}</text>',
                    f'<text xml:space="preserve" x="{x+16}" y="{y+52}" fill="{style["ink"]}" font-family="Space Grotesk" font-size="{style["body_size"]}">{escape(node["text"])}</text>', '</g>'])
        geometry.append({"id": key, "x": x, "y": y, "width": box_width, "height": 72})
    svg.append('</svg>')
    ledger = {"version": VERSION, "body": body, "target_width": target_width, "canvas_width": width,
              "canvas_height": height, "claim_scope": CLAIM, "geometry": geometry, "style": style}
    return '\n'.join(svg) + '\n', ledger


def write_presentation(model_paths, output, *, view_id, profile=None, body="paper", target_width=1200):
    """Acquire a native inventory and write a new, independently editable bundle."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Presentation output already exists: {output}")
    paths = [Path(model_paths)] if isinstance(model_paths, (str, Path)) else [Path(p) for p in model_paths]
    report = check_sysml(paths, syntax_only=True, view_profile={"version": 1, "views": [{"id": view_id, "kind": "function_tree"}]})
    if report["status"] != "pass":
        return report
    projection = project_function_tree(report["inventory"], view_id)
    validated_profile = load_profile(profile) if profile is None or isinstance(profile, (str, Path)) else deepcopy(profile)
    svg, presentation = render_function_tree(projection, profile=validated_profile, body=body, target_width=target_width)
    # Capture source bytes and verify parser pins before creating any output.
    sources = {}
    for path in paths:
        raw = path.read_bytes()
        resolved = path.resolve()
        matched = next((entry for entry in report["model_files"] if entry["path"] == str(resolved) or
                        (Path(__file__).resolve().parents[1] / entry["path"]).resolve() == resolved), None)
        if matched is None or matched["sha256"] != _digest(raw):
            raise ValueError("Model source changed during presentation acquisition")
        sources[resolved.as_posix()] = raw
    files = {"view.svg": svg.encode(), "semantic-ledger.json": _json(projection).encode(),
             "presentation.json": _json(presentation).encode()}
    # Plain offline HTML: exact SVG, embedded fonts, scroll and native browser zoom.
    html = '<!doctype html>\n<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Function decomposition</title><style>html{background:#fff}body{margin:24px;font-family:"Space Grotesk",sans-serif}main{overflow:auto}svg{display:block;max-width:none}' + presentation['style']['font_css'] + '</style><p>' + escape(CLAIM) + '</p><p>Scroll to inspect the diagram; use browser zoom to enlarge.</p><main>' + svg + '</main></html>\n'
    files["index.html"] = html.encode()
    font_manifest_raw = (ASSETS / 'fonts/manifest.json').read_bytes()
    font_manifest = json.loads(font_manifest_raw)
    files['font-notices/manifest.json'] = font_manifest_raw
    for face in font_manifest['faces']:
        files['font-notices/' + face['notice']] = (ASSETS / 'fonts' / face['notice']).read_bytes()
    source_manifest = []
    for i, (path, raw) in enumerate(sorted(sources.items())):
        companion = f"sources/model-{i+1}.sysml"
        files[companion] = raw
        source_manifest.append({"file": companion, "name": Path(path).name, "sha256": _digest(raw)})
    manifest = {"version": VERSION, "view_id": view_id, "claim_scope": CLAIM,
                "model_sha256": report["model_sha256"], "parser": report["parser"],
                "checker_version": report["checker_version"], "sources": source_manifest,
                "style_sha256": _digest(_json(validated_profile).encode()),
                "font_manifest_sha256": _digest(font_manifest_raw),
                "implementation_sha256": {str(Path('verifier') / name): _digest((Path(__file__).parent / name).read_bytes())
                    for name in ('visual_projection.py', 'visual_style.py', 'engineering_views.py', 'sysml.py')},
                "files": {name: _digest(raw) for name, raw in sorted(files.items())},
                "editable_source": "sources/*.sysml are exact source companions; edit and regenerate with sysml_present.py. No editor roundtrip claim."}
    files['manifest.json'] = _json(manifest).encode()
    output.mkdir()  # exclusive: never overwrite an existing presentation
    try:
        (output / 'sources').mkdir()
        (output / 'font-notices').mkdir()
        for name, raw in sorted(files.items()):
            (output / name).write_bytes(raw)
    except OSError:
        shutil.rmtree(output)
        raise
    return {"status": "pass", "claim_scope": CLAIM, "manifest": manifest}
