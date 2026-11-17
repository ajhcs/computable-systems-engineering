"""Native physical views over the persisted composition document.

The view owns its selected bindings. Geometry and artwork never create a part,
change native ownership or establish selected configuration membership.
"""
from copy import deepcopy
from hashlib import sha256
from html import escape
import json
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET

from . import composition_fonts as kit_fonts
from . import kit_templates
from .composition_records import strict_json
from .visual_style import contrast


ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r'[A-Za-z_][A-Za-z0-9_.-]{0,127}\Z')
RECT = 'palette-rectangle-white-plain'
ROUTE_STROKE = 2.5
TOKENS = {
    'typography-spec.json': 'f637d78b0c1d2f83558724b57a7fceb94fc3e49370bed1e76dba727275fb7f76',
    'color-swatches.json': '0e5e5137edb8a541b7d608f70473fdd0b4f1351253a91788a9850270c18a7c49',
    'routing-policy.json': '35ffc6cf3a701fe904df3b125585cd959f42dd1a523ad1d4bbeb50a576c25ada',
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def exact(value, fields):
    need(isinstance(value, dict) and set(value) == set(fields), 'Unknown or missing physical-view fields')


def identifier(value):
    need(isinstance(value, str) and ID.fullmatch(value), 'Invalid physical-view identity')


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def token(name):
    raw = (ROOT / 'assets/engineering-library/tokens' / name).read_bytes()
    need(sha256(raw).hexdigest() == TOKENS[name], 'Saved design-kit token digest mismatch')
    return json.loads(raw)


def tokens():
    values = {name: token(name) for name in TOKENS}
    colors = {row['id']: row['hex_srgb'] for row in values['color-swatches.json']['colors']}
    colors.update(N0='#FFFFFF', N10='#E6E6E6', N25='#BFBFBF', N50='#808080', N75='#404040', N100='#000000')
    return colors, values['typography-spec.json']


def validate_companion(record, kind):
    """Structural contract; full native binding/geometry checks run on rendering."""
    if kind == 'composition_layout':
        exact(record, ('version', 'view', 'width', 'height', 'nodes', 'edges'))
        need(record['version'] == 'cse-diagram-layout-1.0', 'Unsupported composition layout version')
        need(all(finite(record[k]) and 200 <= record[k] <= 8192 for k in ('width', 'height')), 'Invalid canvas bounds')
        need(isinstance(record['nodes'], dict) and 1 <= len(record['nodes']) <= 128, 'Invalid layout node inventory')
        need(isinstance(record['edges'], dict) and len(record['edges']) <= 127, 'Invalid layout edge inventory')
        for key, box in record['nodes'].items():
            identifier(key)
            exact(box, ('x', 'y', 'width', 'height'))
            need(all(finite(v) for v in box.values()) and box['x'] >= 0 and box['y'] >= 0
                 and box['width'] > 0 and box['height'] > 0, 'Invalid node bounds')
        for key, route in record['edges'].items():
            identifier(key)
            exact(route, ('points',))
            need(isinstance(route['points'], list) and 2 <= len(route['points']) <= 128, 'Invalid physical route')
            need(all(isinstance(p, list) and len(p) == 2 and all(finite(v) for v in p) for p in route['points']),
                 'Physical route points must be finite pairs')
    elif kind == 'composition_appearance':
        exact(record, ('version', 'kit', 'view', 'nodes', 'edges', 'legend'))
        need(record['version'] == 'cse-diagram-appearance-2.0' and record['kit'] == 'engineering-palette-complete-05',
             'Unsupported saved-kit appearance')
        colors, _ = tokens()
        need(isinstance(record['nodes'], dict) and 1 <= len(record['nodes']) <= 128, 'Invalid appearance nodes')
        need(isinstance(record['edges'], dict) and len(record['edges']) <= 127, 'Invalid appearance edges')
        for key, item in record['nodes'].items():
            identifier(key)
            exact(item, ('template', 'fill', 'stroke', 'text', 'align'))
            need(isinstance(item['template'], str) and item['template'].startswith('palette-rectangle-')
                 and item['template'] in kit_templates.TEMPLATES, 'Physical nodes require a saved rectangle master')
            need(item['align'] in ('left', 'center'), 'Unsupported text alignment')
            need(all(isinstance(item[k], str) and item[k] in colors for k in ('fill', 'stroke', 'text')),
                 'Choose exact saved swatch IDs')
            fill, stroke, ink = (colors[item[k]] for k in ('fill', 'stroke', 'text'))
            need(contrast(ink, fill) >= 4.5 and contrast(stroke, '#FFFFFF') >= 3
                 and (stroke == fill or contrast(stroke, fill) >= 3), 'Insufficient kit text or boundary contrast')
            master = kit_templates.source_record(item['template'])
            if not item['template'].endswith('-plain'):
                pattern = ET.fromstring(master['svg']).find('.//{http://www.w3.org/2000/svg}pattern')
                inks = {e.get(k) for e in pattern.iter() for k in ('fill', 'stroke') if e.get(k, '').startswith('#')}
                def expanded(value):
                    return '#' + ''.join(c * 2 for c in value[1:]) if len(value) == 4 else value
                need(inks and all(contrast(expanded(v), fill) >= 1.5 for v in inks), 'Saved surface pattern loses visibility')
        for key, color in record['edges'].items():
            identifier(key)
            need(isinstance(color, str) and color in colors and contrast(colors[color], '#FFFFFF') >= 3,
                 'Invalid or low-contrast connector swatch')
        need(isinstance(record['legend'], list) and 1 <= len(record['legend']) <= 5, 'Saved appearance needs its local key')
        for line in record['legend']:
            kit_fonts.require_supported_text(line)
    else:
        raise ValueError('Unknown composition presentation role')
    identifier(record['view'])


def find_view(document, view_id):
    identifier(view_id)
    records = [row for row in document.parsed.get('documents', []) if row.get('name') == 'cseViews']
    need(len(records) == 1 and records[0].get('owner_kind') == 'Package',
         'A single package-owned cseViews record is required')
    body = records[0]['body']
    marker = re.match(r'\s*CSE-VIEWS/1\.1\s*\r?\n', body)
    need(marker is not None, 'Physical composition uses the existing CSE-VIEWS/1.1 contract')
    record = strict_json(body[marker.end():])
    exact(record, ('views',))
    need(isinstance(record['views'], list) and 1 <= len(record['views']) <= 128, 'Invalid native view inventory')
    seen = set()
    for view in record['views']:
        need(isinstance(view, dict), 'Invalid native view record')
        identifier(view.get('id'))
        need(view['id'] not in seen, 'Duplicate view identity')
        seen.add(view['id'])
    matches = [v for v in record['views'] if v['id'] == view_id]
    need(len(matches) == 1, 'Selected physical view is unavailable')
    return matches[0]


def project(document, view_id):
    view = find_view(document, view_id)
    exact(view, ('id', 'kind', 'mode', 'nodes'))
    need(view['kind'] == 'physical_composition' and view['mode'] in ('definitions', 'usages'),
         'Select a physical definition hierarchy or usage composition')
    need(isinstance(view['nodes'], list) and 1 <= len(view['nodes']) <= 128, 'Physical view needs 1 to 128 nodes')
    category = 'part_definitions' if view['mode'] == 'definitions' else 'parts'
    inventory = {r['qualified_name']: r for r in document.parsed[category]}
    ids = {name: identity for identity, name in document.registry.items()}
    nodes, edges, bindings = {}, {}, set()
    for entry in view['nodes']:
        exact(entry, ('id', 'element', 'parent', 'level', 'edge'))
        identifier(entry['id'])
        need(entry['id'] not in nodes and isinstance(entry['element'], str) and entry['element'] in inventory,
             'Physical node needs a unique binding to the selected native kind')
        need(entry['element'] not in bindings, 'Repeated native bindings need separate occurrence support')
        bindings.add(entry['element'])
        need(type(entry['level']) is int and 0 <= entry['level'] <= 16, 'Invalid physical hierarchy level')
        native = deepcopy(inventory[entry['element']])
        if 'multiplicity_offset' in native.get('source_span', {}):
            from .composition_edit import bounds
            a, b = bounds(document.source, native['source_span'], 'multiplicity_')
            native['source_multiplicity'] = document.source[a:b]
        # This projection preserves declared membership. It never expands a type
        # or treats inherited selected roles as owned declarations of the root.
        if view['mode'] == 'usages' and entry['parent'] is not None:
            need(native.get('is_composite') is True, 'Referenced resources cannot be drawn as owned usage composition')
        nodes[entry['id']] = {**deepcopy(entry), 'element_id': ids[entry['element']], 'native': native,
                              'kind': 'PartDefinition' if category == 'part_definitions' else 'PartUsage'}
    roots = [n for n in nodes.values() if n['parent'] is None]
    need(len(roots) == 1 and roots[0]['level'] == 0 and roots[0]['edge'] is None, 'Physical view needs one level-zero root')
    for key, node in nodes.items():
        if node['parent'] is None:
            continue
        need(isinstance(node['parent'], str) and node['parent'] in nodes, 'Missing physical parent')
        parent = nodes[node['parent']]
        need(node['level'] == parent['level'] + 1 and node['native'].get('owner') == parent['element'],
             'View parent must be the exact native declaring owner')
        identifier(node['edge'])
        need(node['edge'] not in edges and node['edge'] not in nodes, 'Duplicate physical relationship identity')
        edges[node['edge']] = {'source': node['parent'], 'target': key, 'kind': 'native_ownership',
                              'directed': True, 'arrowheads': False}
    need(len(edges) == len(nodes) - 1, 'Invalid native ownership tree')
    # Native ownership + strictly increasing bounded levels excludes cycles.
    return {'version': 'cse-composition-view-1', 'id': view_id, 'mode': view['mode'],
            'project_id': document.project_id, 'bundle_sha256': document.revision,
            'nodes': nodes, 'edges': edges,
            'omitted_elements': [{'element': name, 'owner': row.get('owner'), 'is_composite': row.get('is_composite')}
                                 for name, row in sorted(inventory.items()) if name not in bindings],
            'configuration_reviews': [{**deepcopy(review),
                                       'retained_scope': strict_json(document.linked_records[review['file']]['text'])}
                                      for review in document.configuration_reviews],
            'claim': 'native_declarations_only_not_selected_installation_or_behavior'}


def companion(document, kind, view_id):
    matches = []
    for name, record in document.linked_records.items():
        if record['kind'] == kind:
            value = strict_json(record['text'])
            if value.get('view') == view_id:
                matches.append((name, value))
    need(len(matches) <= 1, 'Ambiguous presentation companions for this view')
    return matches[0] if matches else (None, None)


def labels(document, projection):
    _, record = companion(document, 'display_labels', projection['id'])
    names = {n['element']: n['native'].get('name') or n['element'] for n in projection['nodes'].values()}
    if record:
        need(all(row['element'] in names for row in record['labels']), 'Display alias binds outside this view')
        names.update({row['element']: row['text'] for row in record['labels']})
    return names


def literal_multiplicity(native):
    bound = native.get('multiplicity', {})
    if bound.get('status') != 'literal':
        return None
    lower, upper = bound['lower'], bound['upper']
    return '[' + (str(lower) if lower == upper else str(lower) + '..' + str(upper)) + ']'


def annotation(native):
    lines = []
    if 'multiplicity' in native:
        bound = native.get('multiplicity', {})
        if bound.get('status') == 'literal':
            lines.append(literal_multiplicity(native))
        elif bound.get('status') != 'default':
            if native.get('source_multiplicity'):
                lines.append(' '.join(native['source_multiplicity'].split()))
            lines.append('multiplicity: ' + str(bound.get('status', 'unavailable')))
    for field, prefix in [('supertypes', ':> '), ('redefines', 'redefines: '), ('subsets', 'subsets: ')]:
        lines.extend(prefix + name for name in native.get(field, []))
    if native.get('is_variation') or native.get('is_variant'):
        lines.append('variation: unresolved')
    if native.get('has_native_value'):
        lines.append('native value: inspect source')
    return lines


def node_lines(node, name, width):
    result = [(line, 28, 700, 'DejaVu Sans') for line in kit_fonts.wrap_text(name, width - 56, 28, weight=700)]
    for note in annotation(node['native']):
        if note == literal_multiplicity(node['native']):
            need(kit_fonts.text_width(note, 24, 'DejaVu Sans Mono') <= width - 56,
                 'Multiplicity notation does not fit; enlarge its frame width')
            result.append((note, 24, 400, 'DejaVu Sans Mono'))
        else:
            result.extend((line, 24, 400, 'DejaVu Sans Mono') for line in
                          kit_fonts.wrap_text(note, width - 56, 24, 'DejaVu Sans Mono'))
    return result


def default_layout(projection, names):
    boxes, routes, cursor = {}, {}, 160
    widths = {key: max(360, math.ceil(kit_fonts.text_width(literal_multiplicity(node['native']), 24, 'DejaVu Sans Mono'))+56)
              if literal_multiplicity(node['native']) else 360 for key, node in projection['nodes'].items()}
    level_widths = {}
    for key, node in projection['nodes'].items():
        level_widths[node['level']] = max(level_widths.get(node['level'], 0), widths[key])
    levels = max(level_widths)
    # Keep the established 80-unit gap where it fits. Finite literals can make
    # every level wider; preserve room for the 30-unit routing trunk without
    # multiplying one wider frame across otherwise ordinary levels.
    gap = min(80, math.floor((8192-112-sum(level_widths.values()))/levels)) if levels else 80
    need(gap >= 40, 'Default hierarchy needs a larger canvas or a detail view')
    positions, left = {}, 56
    for level in range(levels+1):
        positions[level] = left
        left += level_widths[level] + gap
    def ordered(key):
        yield key
        for child, node in projection['nodes'].items():
            if node['parent'] == key:
                yield from ordered(child)
    root = next(key for key, node in projection['nodes'].items() if node['parent'] is None)
    for key in ordered(root):
        node = projection['nodes'][key]
        lines = node_lines(node, names[node['element']], widths[key])
        height = max(90, 40 + sum(math.ceil(size * 1.4) for _, size, _, _ in lines))
        boxes[key] = {'x': positions[node['level']], 'y': cursor, 'width': widths[key], 'height': height}
        cursor += height + 60
    for key, edge in projection['edges'].items():
        a, b = boxes[edge['source']], boxes[edge['target']]
        x = a['x'] + a['width'] + 30
        routes[key] = {'points': [[a['x'] + a['width'], a['y'] + a['height']/2], [x, a['y'] + a['height']/2],
                                  [x, b['y'] + b['height']/2], [b['x'], b['y'] + b['height']/2]]}
    return {'version': 'cse-diagram-layout-1.0', 'view': projection['id'],
            'width': max(1000, max(b['x'] + b['width'] for b in boxes.values()) + 56),
            'height': cursor + 100, 'nodes': boxes, 'edges': routes}


def overlaps(a, b):
    return min(a['x']+a['width'], b['x']+b['width']) > max(a['x'], b['x']) + 1e-7 and min(a['y']+a['height'], b['y']+b['height']) > max(a['y'], b['y']) + 1e-7


def cuts_box(a, b, box):
    # Open interior clipping, adapted from the preserved renderer. Boundary
    # contact is allowed; crossing an unrelated node is not.
    lo, hi = 0.0, 1.0
    for axis, left, right in [(0, box['x'], box['x']+box['width']), (1, box['y'], box['y']+box['height'])]:
        delta = b[axis] - a[axis]
        if abs(delta) < 1e-9:
            if not left + 1e-7 < a[axis] < right - 1e-7:
                return False
        else:
            first, last = sorted(((left+1e-7-a[axis])/delta, (right-1e-7-a[axis])/delta))
            lo, hi = max(lo, first), min(hi, last)
    return lo < hi


def geometry(projection, layout, names):
    validate_companion(layout, 'composition_layout')
    need(layout['view'] == projection['id'] and set(layout['nodes']) == set(projection['nodes'])
         and set(layout['edges']) == set(projection['edges']), 'Layout must cover exactly the selected native view')
    boxes = layout['nodes']
    for key, box in boxes.items():
        need(box['x'] >= 32 and box['y'] >= 140 and box['x'] + box['width'] <= layout['width'] - 32
             and box['y'] + box['height'] <= layout['height'] - 48, 'Node outside drawable canvas')
        lines = node_lines(projection['nodes'][key], names[projection['nodes'][key]['element']], box['width'])
        need(sum(math.ceil(size * 1.4) for _, size, _, _ in lines) + 32 <= box['height'], 'Node text does not fit; enlarge its frame')
        for other in boxes:
            if key < other:
                need(not overlaps(box, boxes[other]), 'Physical nodes overlap')
    for key, route in layout['edges'].items():
        edge = projection['edges'][key]
        points = route['points']
        def boundary(point, box):
            x, y = point
            return (box['x']-1e-7 <= x <= box['x']+box['width']+1e-7
                    and box['y']-1e-7 <= y <= box['y']+box['height']+1e-7
                    and min(abs(x-box['x']), abs(x-box['x']-box['width']), abs(y-box['y']), abs(y-box['y']-box['height'])) < 1e-7)
        need(boundary(points[0], boxes[edge['source']]) and boundary(points[-1], boxes[edge['target']]),
             'Route must attach to its exact native endpoints')
        for a, b in zip(points, points[1:]):
            need(a != b, 'Physical routes must have nonempty segments')
            need(all(0 <= p[0] <= layout['width'] and 140 <= p[1] <= layout['height']-32 for p in (a, b)),
                 'Route outside drawable canvas')
            need(not any(cuts_box(a, b, box) for box in boxes.values()), 'Physical route crosses a node interior')


def crossings(projection, layout):
    result = []
    routes = list(layout['edges'].items())
    policy = token('routing-policy.json')
    # The policy measures visible ink. Two 2.5-unit strokes add one full
    # stroke to the centreline distance required for a 6s clear gap.
    clearance = policy['connector_to_connector_clearance_ink_s'] * policy['reference_stroke_s'] + ROUTE_STROKE
    def cross(a, b):
        return a[0]*b[1]-a[1]*b[0]
    def point_distance(p, a, b):
        delta = [b[k]-a[k] for k in (0, 1)]
        length = sum(v*v for v in delta)
        need(length > 0, 'Physical routes must have nonempty segments')
        t = max(0, min(1, sum((p[k]-a[k])*delta[k] for k in (0, 1))/length))
        return math.hypot(*(p[k]-a[k]-t*delta[k] for k in (0, 1)))
    def separated(a, b, c, d):
        distance = min(point_distance(a, c, d), point_distance(b, c, d),
                       point_distance(c, a, b), point_distance(d, a, b))
        need(distance + 1e-7 >= clearance, 'Unrelated ownership routes violate saved connector ink clearance')
    for i, (under, first) in enumerate(routes):
        for over, second in routes[i+1:]:
            # Shared native-parent trunks are intentional fanout. Other route
            # crossings must not manufacture a junction or a second owner.
            if projection['edges'][under]['source'] == projection['edges'][over]['source']:
                continue
            for a, b in zip(first['points'], first['points'][1:]):
                u = [b[k]-a[k] for k in (0, 1)]
                for c, d in zip(second['points'], second['points'][1:]):
                    v = [d[k]-c[k] for k in (0, 1)]
                    offset = [c[k]-a[k] for k in (0, 1)]
                    denominator = cross(u, v)
                    if abs(denominator) < 1e-8:
                        if abs(cross(offset, u)) < 1e-8:
                            axis = 0 if abs(u[0]) > abs(u[1]) else 1
                            need(min(max(a[axis], b[axis]), max(c[axis], d[axis])) <=
                                 max(min(a[axis], b[axis]), min(c[axis], d[axis])) + 1e-7,
                                 'Unrelated ownership routes overlap; route them separately')
                        separated(a, b, c, d)
                        continue
                    t, s = cross(offset, v)/denominator, cross(offset, u)/denominator
                    if not (-1e-7 <= t <= 1+1e-7 and -1e-7 <= s <= 1+1e-7):
                        separated(a, b, c, d)
                        continue
                    need(1e-7 < t < 1-1e-7 and 1e-7 < s < 1-1e-7,
                         'Nonconnecting crossings need clearance from route bends and endpoints')
                    x, y = a[0]+t*u[0], a[1]+t*u[1]
                    angle = abs(math.degrees(math.atan2(v[1], v[0])-math.atan2(u[1], u[0]))) % 180
                    need(20-1e-7 <= angle <= 160+1e-7, 'Crossing angle is outside the saved gap treatment')
                    radius = math.ceil(10/abs(math.sin(math.radians(angle)))+5)
                    need(min(math.hypot(x-p[0], y-p[1]) for p in (a, b, c, d)) >= radius,
                         'Nonconnecting crossings need clearance from route bends and endpoints')
                    area = {'x': x-radius, 'y': y-radius, 'width': 2*radius, 'height': 2*radius}
                    need(not any(overlaps(area, box) for box in layout['nodes'].values()), 'Crossing needs clearance from native frames')
                    need(not any(abs(x-r['x']) < radius+r['radius'] and abs(y-r['y']) < radius+r['radius'] for r in result),
                         'Crossing markers need separate clear space')
                    result.append({'under': under, 'over': over, 'x': x, 'y': y, 'radius': radius,
                                   'under_angle': math.degrees(math.atan2(u[1], u[0])),
                                   'over_angle': math.degrees(math.atan2(v[1], v[0]))})
    return result


def render(document, view_id, *, layout_override=None):
    projection = project(document, view_id)
    names = labels(document, projection)
    _, layout = companion(document, 'composition_layout', view_id)
    _, appearance = companion(document, 'composition_appearance', view_id)
    default = layout_override is None and layout is None
    layout = deepcopy(layout_override if layout_override is not None else layout or default_layout(projection, names))
    if default and appearance:
        layout['height'] += len(appearance['legend'])*34+100
    geometry(projection, layout, names)
    colors, _ = tokens()
    if appearance:
        validate_companion(appearance, 'composition_appearance')
        need(set(appearance['nodes']) == set(projection['nodes']) and set(appearance['edges']) <= set(projection['edges']),
             'Appearance must cover exactly the selected view')
    mode_title = 'Physical definition hierarchy' if projection['mode'] == 'definitions' else 'Declared physical usage composition'
    _, label_record = companion(document, 'display_labels', view_id)
    title = label_record['title'] if label_record else mode_title
    ns = '{http://www.w3.org/2000/svg}'
    root = ET.Element(ns+'svg', {'width': str(layout['width']), 'height': str(layout['height']),
                                'viewBox': f"0 0 {layout['width']} {layout['height']}", 'role': 'img', 'aria-labelledby': 'view-title'})
    ET.SubElement(root, ns+'title', {'id': 'view-title'}).text = title
    ET.SubElement(root, ns+'desc').text = projection['claim']
    ET.SubElement(root, ns+'style').text = kit_fonts.font_css() + '\ntext{font-kerning:none;font-variant-ligatures:none;white-space:pre;text-rendering:geometricPrecision}'
    ET.SubElement(root, ns+'rect', {'width': str(layout['width']), 'height': str(layout['height']), 'fill': colors['N0']})
    usage = {'version': 1, 'kit': 'engineering-palette-complete-05', 'view': view_id, 'components': {},
             'token_sha256': TOKENS, 'font_manifest_sha256': kit_fonts.MANIFEST_SHA256,
             'font_profile_sha256': kit_fonts.PROFILE_SHA256, 'adaptations': []}
    heading_width = math.ceil(kit_fonts.text_width(title, 24, weight=700)) + 40
    need(heading_width <= layout['width']-64, 'Heading does not fit the canvas')
    heading = kit_templates.document_frame(kit_templates.FIGURE_HEADING, x=32, y=28,
                                          column_widths=[heading_width], row_heights=[55], prefix='composition-heading')
    root.append(ET.fromstring(heading['svg']))
    usage['components'][heading['template']] = kit_templates.source_record(heading['template'])['sha256']
    ET.SubElement(root, ns+'text', {'x': '52', 'y': '64', 'font-family': 'DejaVu Sans', 'font-size': '24', 'font-weight': '700', 'fill': colors['N100']}).text = title
    if title != mode_title:
        ET.SubElement(root, ns+'text', {'x': '32', 'y': '118', 'font-family': 'DejaVu Sans', 'font-size': '26', 'fill': colors['N100']}).text = mode_title
    for key, route in layout['edges'].items():
        edge = projection['edges'][key]
        color = colors[appearance['edges'].get(key, 'N100')] if appearance else colors['N100']
        group = ET.SubElement(root, ns+'g', {'data-edge-id': key, 'data-source-node': edge['source'], 'data-target-node': edge['target'], 'data-relation': 'native_ownership'})
        ET.SubElement(group, ns+'path', {'d': 'M' + ' L'.join(' '.join(str(v) for v in p) for p in route['points']),
                                       'fill': 'none', 'stroke': color, 'stroke-width': str(ROUTE_STROKE)})
    for index, crossing in enumerate(crossings(projection, layout)):
        color = colors[appearance['edges'].get(crossing['over'], 'N100')] if appearance else colors['N100']
        raw = kit_templates.gap_marker(prefix='composition-crossing-'+str(index),
                                       x=crossing['x'], y=crossing['y'], under_angle=crossing['under_angle'],
                                       over_angle=crossing['over_angle'], colour=color, stroke_width=ROUTE_STROKE)
        root.append(ET.fromstring(raw))
        usage['components'][kit_templates.GAP] = kit_templates.source_record(kit_templates.GAP)['sha256']
        usage['adaptations'].append({'role': 'nonconnecting crossing', **crossing})
    for key, node in projection['nodes'].items():
        box = layout['nodes'][key]
        item = appearance['nodes'][key] if appearance else {'template': RECT, 'fill': 'N0', 'stroke': 'N100', 'text': 'N100', 'align': 'center'}
        group = ET.SubElement(root, ns+'g', {'data-node-id': key, 'data-element-id': node['element_id'],
                                           'data-native-name': node['element'], 'data-native-owner': str(node['native'].get('owner') or '')})
        lines = node_lines(node, names[node['element']], box['width'])
        span = sum(math.ceil(size * 1.4) for _, size, _, _ in lines)
        baseline = box['y'] + (box['height']-span)/2 + math.ceil(lines[0][1]*1.4)/2 + lines[0][1]*.35
        positions, previous = [], None
        for _, size, _, _ in lines:
            if previous is not None:
                baseline += math.ceil(max(previous, size)*1.4)
            positions.append(baseline)
            previous = size
        word_width = max(kit_fonts.text_width(text, size, family, weight) for text, size, weight, family in lines)
        left = box['x']+28 if item['align'] == 'left' else box['x']+(box['width']-word_width)/2
        top = min(y-size-5 for y, (_, size, _, _) in zip(positions, lines))
        bottom = max(y+9 for y in positions)
        padding = max(kit_fonts.backing_padding(text) for text, _, _, _ in lines)
        # Preserve the original pattern, then use its saved opaque text backing.
        frame = kit_templates.frame(item['template'], **box, fill=colors[item['fill']], stroke=colors[item['stroke']],
                                    stroke_width=3, prefix='composition-'+key,
                                    text_bounds=[left-padding, top, word_width+2*padding, bottom-top])
        group.append(ET.fromstring(frame))
        usage['components'][item['template']] = kit_templates.source_record(item['template'])['sha256']
        usage['adaptations'].append({'node': key, 'element_id': node['element_id'], 'template': item['template'], 'geometry': box, 'stroke_width': 3,
                                     'label_backing_padding': padding,
                                     'edits': ['content-fit geometry', 'exact saved swatches', 'independent bound labels', 'unique SVG identities']})
        for baseline, (text, size, weight, family) in zip(positions, lines):
            x = box['x']+28 if item['align'] == 'left' else box['x']+box['width']/2
            ET.SubElement(group, ns+'text', {'x': str(x), 'y': str(baseline), 'font-family': family, 'font-size': str(size),
                                           'font-weight': str(weight), 'text-anchor': 'start' if item['align'] == 'left' else 'middle',
                                           'fill': colors[item['text']]}).text = text
    if appearance:
        # Reserve the key's full-width footer with the same 32-unit clearance
        # for both frames and routes. Endpoint/obstacle checks alone cannot
        # prevent a detour from crossing these authored annotations.
        count = len(appearance['legend'])
        heading_height, body_height = 44, count*34+24
        top = layout['height']-48-heading_height-body_height
        need(max(b['y']+b['height'] for b in layout['nodes'].values())+32 < top, 'Reserve space for the authored local key')
        need(all(point[1]+32 < top for route in layout['edges'].values() for point in route['points']),
             'Route enters the reserved local key area; reroute it or enlarge the canvas')
        width = math.ceil(max(kit_fonts.text_width('Local key', 24, weight=700),
                              *(kit_fonts.text_width(line, 24) for line in appearance['legend'])))+32
        need(width <= layout['width']-64, 'Local key does not fit')
        frame = kit_templates.document_frame(kit_templates.LEGEND, x=32, y=top,
                    column_widths=[width], row_heights=[heading_height, body_height], prefix='composition-key')
        group = ET.SubElement(root, ns+'g', {'data-role': 'local-key', 'data-view-id': view_id})
        group.append(ET.fromstring(frame['svg']))
        usage['components'][frame['template']] = frame['sha256']
        usage['adaptations'].append({'role': 'local key', 'view': view_id, 'template': frame['template'],
                                    'geometry': {k: frame[k] for k in ('x', 'y', 'width', 'height')},
                                    'edits': ['content-fit cells', 'preserved source rule topology', 'authored key text']})
        ET.SubElement(group, ns+'text', {'x': '48', 'y': str(top+30), 'font-family': 'DejaVu Sans',
                                       'font-size': '24', 'font-weight': '700', 'fill': colors['N100']}).text = 'Local key'
        for index, line in enumerate(appearance['legend']):
            ET.SubElement(group, ns+'text', {'x': '48', 'y': str(top+heading_height+28+index*34), 'font-family': 'DejaVu Sans', 'font-size': '24', 'fill': colors['N100']}).text = line
    return {'projection': projection, 'layout': layout, 'kit_usage': usage, 'display_title': title,
            'display_labels': {key: names[node['element']] for key, node in projection['nodes'].items()},
            'svg': ET.tostring(root, encoding='unicode')+'\n'}


def with_layout(document, layout):
    validate_companion(layout, 'composition_layout')
    render(document, layout['view'], layout_override=layout)
    name, _ = companion(document, 'composition_layout', layout['view'])
    name = name or 'presentation/' + layout['view'] + '.layout.json'
    need(name not in document.files and (name not in document.linked_records or document.linked_records[name]['kind'] == 'composition_layout'),
         'Presentation filename collides with another authoritative file')
    records = deepcopy(document.linked_records)
    records[name] = {'kind': 'composition_layout', 'text': json.dumps(layout, indent=2, allow_nan=False)+'\n'}
    return type(document)(document.files, project_id=document.project_id, registry=document.registry, linked_records=records)


def validate_saved_presentations(document):
    selected = {strict_json(record['text'])['view'] for record in document.linked_records.values()
                if record['kind'] in ('composition_layout', 'composition_appearance')}
    for view_id in sorted(selected):
        render(document, view_id)


def artifact_files(snapshot, view_id):
    document = snapshot['document']
    rendered = render(document, view_id)
    data = {'revision': snapshot['revision'], 'commit': snapshot['commit'], 'projection': rendered['projection'],
            'display_title': rendered['display_title'], 'display_labels': rendered['display_labels']}
    text = json.dumps(data, ensure_ascii=True, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = (ROOT / 'web/composition-reader.html').read_text()
    html = template.replace('<!-- CSE_SVG -->', rendered['svg']).replace('<!-- CSE_DATA -->', text)
    files = {'view.svg': rendered['svg'].encode('utf-8'), 'index.html': html.encode('utf-8'),
             'view.json': json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'),
             'layout.json': json.dumps(rendered['layout'], indent=2).encode('utf-8'),
             'kit-usage.json': json.dumps(rendered['kit_usage'], indent=2).encode('utf-8'),
             'registry.json': json.dumps(document.registry, indent=2).encode('utf-8')}
    for name, source in document.files.items():
        files['sources/'+name] = source.encode('utf-8')
    for name, record in document.linked_records.items():
        files['companions/'+name] = record['text'].encode('utf-8')
    for master in rendered['kit_usage']['components']:
        files['artwork/'+master+'.svg'] = kit_templates.source_record(master)['svg'].encode('utf-8')
    for name in kit_fonts._FILES:
        files['fonts/'+name] = (kit_fonts.ASSETS / name).read_bytes()
    files['fonts/composition-font-metrics.json'] = kit_fonts.profile_bytes()
    from .sysml_batch import runtime_identity
    from .sysml import CACHE
    engines, backend = {}, {}
    for name, digest in runtime_identity().items():
        path = Path(name)
        if path.is_relative_to(CACHE):
            backend[str(path.relative_to(CACHE))] = digest
        else:
            engines[str(path.relative_to(ROOT))] = digest
    for name in ('web/composition-reader.html', 'scripts/composition_project.py'):
        engines[name] = sha256((ROOT/name).read_bytes()).hexdigest()
    manifest = {'version': 'cse-composition-artifacts-1', 'project_id': document.project_id,
                'view': view_id, 'revision': snapshot['revision'], 'commit': snapshot['commit'],
                'bundle_sha256': document.revision, 'engines': engines, 'parser_backend': backend,
                'files': {name: sha256(raw).hexdigest() for name, raw in files.items()},
                'claim': 'saved_revision_presentation_not_application_or_required_review_acceptance'}
    files['manifest.json'] = json.dumps(manifest, indent=2, sort_keys=True).encode('utf-8')
    return files


def write_artifacts(snapshot, view_id, output):
    files = artifact_files(snapshot, view_id)
    output = Path(output)
    need(not output.exists(), 'Refusing to replace an existing artifact directory')
    output.mkdir(parents=True, exist_ok=False)
    for name, raw in files.items():
        path = output/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return {'output': str(output), 'revision': snapshot['revision'], 'commit': snapshot['commit'], 'view': view_id,
            'claim': 'saved_revision_presentation_only'}


def check_artifacts(snapshot, view_id, output):
    files = artifact_files(snapshot, view_id)
    output = Path(output)
    actual = {str(p.relative_to(output)) for p in output.rglob('*') if p.is_file()}
    need(actual == set(files), 'Artifact file inventory differs from this saved revision')
    for name, raw in files.items():
        path = output/name
        need(not path.is_symlink() and path.read_bytes() == raw, 'Stale or changed artifact: '+name)
    return {'revision': snapshot['revision'], 'commit': snapshot['commit'], 'view': view_id,
            'claim': 'source_and_artifact_correspondence_not_engineering_acceptance'}
