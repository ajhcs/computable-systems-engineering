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
from .visual_style import ASSETS, load_profile, presentation_style, require_supported_text, text_width, wrap_text, contrast, function_tree_roles
from .visual_labels import apply_labels, load_labels

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


def render_function_tree(projection, *, profile=None, body="paper", target_width=1200, show_ids=False, labels=None):
    """Content-fit documentary tree; explicit display wording never changes native facts."""
    if type(show_ids) is not bool:
        raise ValueError("show_ids must be a boolean")
    if type(target_width) not in (int, float) or not math.isfinite(target_width) or not 320 <= target_width <= 8192:
        raise ValueError("Target width must be between 320 and 8192 pixels")
    if projection.get("kind") != "function_tree" or projection.get("version") != VERSION:
        raise ValueError("Expected bounded function-tree presentation version")
    raw_nodes = [{key: n[key] for key in ("id", "element", "level", "parent")} for n in projection["nodes"]]
    inventory = {"documents": [{"name": "cseViews", "owner_kind": "Package", "body":
        "CSE-VIEWS/1.0\n" + json.dumps({"views": [{"id": projection["id"], "kind": "function_tree", "nodes": raw_nodes}]})}],
        "parts": [], "actions": [{"qualified_name": n["element"], "name": n["text"]} for n in projection["nodes"]]}
    nodes = project_function_tree(inventory, projection["id"])["nodes"]
    wording = apply_labels(projection, labels)
    style = presentation_style(profile, body=body)
    palette = load_profile(profile)['palette']
    by_id = {n['id']: n for n in nodes}
    children = {n['id']: [] for n in nodes}
    for n in nodes:
        if n['parent'] is not None:
            children[n['parent']].append(n['id'])
    root = next(n['id'] for n in nodes if n['parent'] is None)
    role_profile = function_tree_roles(profile)
    families, roles = role_profile['branch_pairs'], {root: role_profile['root_pair']}
    def assign(key, family):
        roles[key] = family
        for child in children[key]:
            assign(child, family)
    for index, key in enumerate(children[root]):
        assign(key, families[index % len(families)])
    boxes = {}
    size, padding, key_width = style['body_size'], 20, 6
    line_height = math.ceil(size * 1.4)
    for n in nodes:
        key = n['id']
        weight = 700 if children[key] else 400
        lines = wrap_text(wording['labels'][key], 300, size, weight=weight)
        footer = ([f"{len(children[key])} subfunction" + ('s' if len(children[key]) != 1 else '')] if children[key] else [])
        if show_ids:
            footer.extend(wrap_text(f"{key} · level {n['level']}", 300, 16))
        content_width = max([text_width(line, size, weight=weight) for line in lines] +
                            [text_width(line, 16 if ' · level ' in line or (show_ids and not children[key]) else 18) for line in footer] + [100])
        label_height = 2 * padding + len(lines) * line_height
        footer_height = 20 + 25 * len(footer) if footer else 0
        boxes[key] = {'width': math.ceil(content_width + 2 * padding + key_width + 8),
                      'height': label_height + footer_height, 'label_height': label_height,
                      'lines': lines, 'footer': footer, 'weight': weight}
    subtrees = {}
    def measure(key):
        box, kids = boxes[key], children[key]
        mode = 'leaf' if not kids else ('stack' if all(not children[c] for c in kids) else 'branches')
        for c in kids:
            measure(c)
        if mode == 'leaf':
            width, height = box['width'], box['height']
        elif mode == 'stack':
            width = max(box['width'], max(boxes[c]['width'] for c in kids) + 32)
            height = box['height'] + 56 + sum(boxes[c]['height'] for c in kids) + 18 * (len(kids)-1)
        else:
            width = max(box['width'], sum(subtrees[c]['width'] for c in kids) + 48 * (len(kids)-1))
            height = box['height'] + 64 + max(subtrees[c]['height'] for c in kids)
        subtrees[key] = {'width': width, 'height': height, 'mode': mode}
    measure(root)
    width = math.ceil(max(target_width, subtrees[root]['width'] + 96,
        text_width('Branch colors identify documentary groups; lines show decomposition.', 18) + 96))
    style = presentation_style(profile, body=body, target_width=target_width, canvas_width=width)
    smallest = 16 if show_ids else 18
    if smallest * target_width / width < 16:
        raise ValueError('Target too small for 16px labels and counts; use native width or scrolling')
    title_text = (projection['id'] + ' - ' if show_ids else '') + wording['title']
    title_lines = wrap_text(title_text, width - 96, style['title_size'], 'Inter', 700)
    title_leading = math.ceil(style['title_size'] * 1.2)
    graph_top = 48 + len(title_lines) * title_leading + 76
    height = math.ceil(graph_top + subtrees[root]['height'] + 96)
    if width > 20000 or height > 20000:
        raise ValueError('Presentation exceeds bounded 20000-unit canvas; select a smaller view')
    positions, edge_points = {}, {}
    def place(key, left, top):
        b, tree, kids = boxes[key], subtrees[key], children[key]
        x = left + (tree['width'] - b['width']) / 2
        positions[key] = (x, top)
        if tree['mode'] == 'stack':
            stack_width = max(boxes[c]['width'] for c in kids) + 32
            leaf_left = left + (tree['width'] - stack_width) / 2 + 32
            spine = leaf_left - 24
            y = top + b['height'] + 56
            for c in kids:
                positions[c] = (leaf_left, y)
                edge_points[c] = {'from_side': 'bottom', 'to_side': 'left', 'points':
                    [(x+b['width']/2, top+b['height']), (x+b['width']/2, top+b['height']+24),
                     (spine, top+b['height']+24), (spine, y+boxes[c]['height']/2),
                     (leaf_left, y+boxes[c]['height']/2)]}
                y += boxes[c]['height'] + 18
        elif tree['mode'] == 'branches':
            kids_width = sum(subtrees[c]['width'] for c in kids) + 48 * (len(kids)-1)
            cursor = left + (tree['width'] - kids_width)/2
            for c in kids:
                cy = top + b['height'] + 64
                place(c, cursor, cy)
                cx, _ = positions[c]
                edge_points[c] = {'from_side': 'bottom', 'to_side': 'top', 'points':
                    [(x+b['width']/2, top+b['height']), (x+b['width']/2, top+b['height']+32),
                     (cx+boxes[c]['width']/2, top+b['height']+32), (cx+boxes[c]['width']/2, cy)]}
                cursor += subtrees[c]['width'] + 48
    place(root, (width-subtrees[root]['width'])/2, graph_top)
    def text(lines, x, baseline, fontsize, color, *, family='Space Grotesk', weight=400, role='label', leading=None):
        leading = leading or math.ceil(fontsize*1.4)
        attrs = f'xml:space="preserve" data-role="{role}" x="{x:g}" y="{baseline:g}" fill="{color}" font-family="{family}" font-size="{fontsize}" font-weight="{weight}"'
        if len(lines) == 1:
            return f'<text {attrs}>{escape(lines[0])}</text>'
        return f'<text {attrs}>' + ''.join(f'<tspan x="{x:g}" y="{baseline+i*leading:g}">{escape(line)}</tspan>' for i,line in enumerate(lines)) + '</text>'
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{target_width}" height="{height*target_width/width:g}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
           f'<title id="title">{escape(title_text)}</title>', f'<desc id="description">{escape(CLAIM)}</desc>',
           '<style>'+escape(style['font_css'])+'\ntext{font-kerning:none;font-variant-ligatures:none;text-rendering:geometricPrecision}</style>',
           f'<rect width="{width}" height="{height}" fill="{style["paper"]}"/>',
           text(title_lines,48,48,style['title_size'],style['ink'],family='Inter',weight=700,role='title',leading=title_leading),
           text(['Documentary function hierarchy'],48,48+len(title_lines)*title_leading+6,18,style['ink'],role='subtitle')]
    shared_routes = []
    for parent, kids in children.items():
        if not kids:
            continue
        if subtrees[parent]['mode'] == 'branches':
            first = edge_points[kids[0]]['points']
            drops = [edge_points[c]['points'][2] for c in kids]
            segments = [[first[0],first[1]],[(min(p[0] for p in drops),first[1][1]),
                        (max(p[0] for p in drops),first[1][1])]]
            color = style['ink']
        else:
            first,last = edge_points[kids[0]]['points'],edge_points[kids[-1]]['points']
            segments = [[first[0],first[1],first[2],last[-2]]]
            color = style['ink'] if parent == root else role_profile['pairs'][roles[parent]]['connector_color']
        commands = ['M ' + ' L '.join(f'{x:g} {y:g}' for x,y in points) for points in segments]
        svg.append(f'<path data-shared-parent="{escape(parent,quote=True)}" d="{" ".join(commands)}" fill="none" stroke="{color}" stroke-width="{style["stroke_width"]}"/>')
        shared_routes.append({'parent':parent,'segments':segments,'color':color})
    for key, edge in edge_points.items():
        # Shared trunks are painted once; this path is the uniquely owned drop.
        points = edge['points'][-2:]
        path = 'M ' + ' L '.join(f'{x:g} {y:g}' for x,y in points)
        svg.append(f'<path data-parent="{escape(by_id[key]["parent"],quote=True)}" data-child="{escape(key,quote=True)}" d="{path}" fill="none" stroke="{role_profile["pairs"][roles[key]]["connector_color"]}" stroke-width="{style["stroke_width"]}"/>')
    geometry = []
    for node in nodes:
        key = node['id']; x,y = positions[key]; b = boxes[key]
        pair = role_profile['pairs'][roles[key]]
        fill = pair['fill_color'] if children[key] else style['fill']
        border = pair['frame_color']
        if contrast(style['ink'], fill) < 4.5 or min(contrast(border, fill), contrast(border, style['paper'])) < 3:
            raise ValueError('Insufficient contrast for local tree presentation roles')
        attrs = ' '.join(f'data-{k}="{escape(str(node[k]),quote=True)}"' for k in ('id','element','level','parent')) + f' data-native-name="{escape(node["text"],quote=True)}"'
        svg.extend([f'<g {attrs}>', f'<rect data-frame="true" x="{x:g}" y="{y:g}" width="{b["width"]}" height="{b["height"]}" fill="{fill}" stroke="{border}" stroke-width="{style["stroke_width"]}"/>',
                    f'<rect x="{x+2:g}" y="{y+2:g}" width="{key_width}" height="{b["height"]-4}" fill="{border}"/>',
                    text(b['lines'], x+padding+key_width, y+padding+size, size, style['ink'], weight=b['weight'])])
        if b['footer']:
            fy = y + b['label_height']
            svg.append(f'<path d="M {x+key_width:g} {fy:g} H {x+b["width"]:g}" stroke="{border}" stroke-width="{style["stroke_width"]}" fill="none"/>')
            for index,line in enumerate(b['footer']):
                is_count = bool(children[key]) and index == 0
                svg.append(text([line],x+padding+key_width,fy+25+index*25,18 if is_count else 16,style['ink'],role='count' if is_count else 'metadata'))
        svg.append('</g>')
        geometry.append({'id':key,'x':x,'y':y,'width':b['width'],'height':b['height'],
                         'label_lines':b['lines'],'label_font_weight':b['weight'],'label_baseline':y+padding+size,
                         'label_region_height':b['label_height'],'footer_lines':b['footer']})
    svg.extend([text(['Branch colors identify documentary groups; lines show decomposition.'],48,height-32,18,style['ink'],role='legend'),'</svg>'])
    ledger = {'version':VERSION,'body':body,'target_width':target_width,'canvas_width':width,'canvas_height':height,
              'claim_scope':CLAIM,'show_ids':show_ids,'display':wording,'geometry':geometry,
              'edges':[{'parent':by_id[k]['parent'],'child':k,**v} for k,v in edge_points.items()],
              'shared_routes':shared_routes,
              'layout':{'kind':'balanced-branches-with-stacked-leaves','padding':padding,'line_height':line_height,
                        'group_gap':48,'leaf_gap':18,'max_label_width':300,
                        'scope':'Measured advance-based wrapping; actual loaded glyph bounds require browser inspection.'},
              'presentation_roles':{'root':'profile-selected contrasting pair','branches':'independent fill, frame/accent and connector references',
                                    'profile':role_profile,'node_pairings':roles,
                                    'meaning':'Local navigation only; no universal engineering or status semantics','body_status':'provisional'},
              'font_metrics_sha256':_digest((ASSETS/'fonts/metrics.json').read_bytes()),'style':style}
    return '\n'.join(svg)+'\n',ledger


def write_presentation(model_paths, output, *, view_id, profile=None, body="paper", target_width=1200, show_ids=False, labels=None):
    """Acquire a native inventory and write a new, independently editable bundle."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Presentation output already exists: {output}")
    paths = [Path(model_paths)] if isinstance(model_paths, (str, Path)) else [Path(p) for p in model_paths]
    report = check_sysml(paths, syntax_only=True, view_profile={"version": 1, "views": [{"id": view_id, "kind": "function_tree"}]})
    if report["status"] != "pass":
        return report
    projection = project_function_tree(report["inventory"], view_id)
    validated_profile = load_profile(profile)
    validated_labels = load_labels(labels)
    svg, presentation = render_function_tree(projection, profile=validated_profile, body=body, target_width=target_width, show_ids=show_ids, labels=validated_labels)
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
    if validated_labels is not None:
        files["display-labels.json"] = _json(validated_labels).encode()
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
    manifest = {"version": VERSION, "view_id": view_id, "claim_scope": CLAIM, "show_ids": show_ids,
                "model_sha256": report["model_sha256"], "parser": report["parser"],
                "checker_version": report["checker_version"], "sources": source_manifest,
                "style_sha256": _digest(_json(validated_profile).encode()),
                "font_manifest_sha256": _digest(font_manifest_raw),
                "font_metrics_sha256": _digest((ASSETS / "fonts/metrics.json").read_bytes()),
                "implementation_sha256": {str(Path('verifier') / name): _digest((Path(__file__).parent / name).read_bytes())
                    for name in ('visual_projection.py', 'visual_style.py', 'visual_labels.py', 'engineering_views.py', 'sysml.py')},
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
