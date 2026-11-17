"""Atomic native definition and physical-view additions, using the saved kit."""
from copy import deepcopy
import json
import math
import re

from .composition_edit import EditError, bounds, fingerprint
from .composition_records import strict_json, STRING, strings
from . import composition_view as view


def _view_record(body):
    marker = re.match(r'\s*CSE-VIEWS/1\.1\s*\r?\n', body)
    if marker is None:
        raise EditError('linked_records', 'Creation needs the existing version-1.1 native view record')
    return marker, strict_json(body[marker.end():])


def _append_node(document, view_id, node):
    rows = [row for row in document.parsed['documents'] if row.get('name') == 'cseViews']
    if len(rows) != 1:
        raise EditError('linked_records', 'A single native view record is required')
    row = rows[0]
    a, b = bounds(document.source, row['source_span'], 'body_')
    token = document.source[a:b]
    if not token.startswith('/*') or not token.endswith('*/'):
        raise EditError('source_span', 'Unsupported native documentation token')
    raw = token[2:-2]
    marker, record = _view_record(raw)
    payload = raw[marker.end():]
    index = next(i for i, selected in enumerate(record['views']) if selected['id'] == view_id)
    selected = record['views'][index]
    expected = deepcopy(record)
    expected['views'][index]['nodes'].append(node)
    tokens, values = list(STRING.finditer(payload)), list(strings(record))
    if len(tokens) != len(values):
        raise EditError('linked_records', 'JSON token/source correspondence failed')
    insert_at = None
    for string, (path, is_key, value) in zip(tokens, values):
        if json.loads(string.group()) != value:
            raise EditError('linked_records', 'JSON token/source correspondence failed')
        if is_key and path == ('views', index, 'nodes'):
            separator = re.match(r'\s*:\s*', payload[string.end():])
            if separator is None:
                raise EditError('linked_records', 'View node array unavailable')
            start = string.end()+separator.end()
            array, end = json.JSONDecoder().raw_decode(payload, start)
            if array != selected['nodes'] or payload[start] != '[' or payload[end-1] != ']':
                raise EditError('linked_records', 'View node array/source correspondence failed')
            insert_at = end-1
            while payload[insert_at-1] in ' \t\r\n':
                insert_at -= 1
    if insert_at is None:
        raise EditError('linked_records', 'View node array unavailable')
    newline = '\r\n' if '\r\n' in raw else '\n'
    addition = ','+newline+'      '+json.dumps(node, ensure_ascii=True, separators=(',', ':'))
    at = a+2+marker.end()+insert_at
    files = document.candidate_files([(at, at, addition)])
    result = type(document)(files if document.is_bundle else files['model.sysml'], project_id=document.project_id,
                            registry=document.registry, linked_records=document.linked_records)
    before, after = fingerprint(document.parsed), fingerprint(result.parsed)
    for old, new in zip(before['documents'], after['documents']):
        if old.get('name') == 'cseViews':
            if _view_record(new['body'])[1] != expected:
                raise EditError('semantic_delta', 'View addition differs from the requested occurrence')
            new['body'] = old['body']
    if before != after:
        raise EditError('semantic_delta', 'View addition changed existing native facts')
    result.reconciliation = deepcopy(document.reconciliation)
    return result


def create_definition(document, owner_id, element_id, new_name, short_id, view_id, placement,
                      *, expected_source_sha256):
    if expected_source_sha256 != document.revision:
        raise EditError('stale_revision', 'Source changed before candidate preparation')
    try:
        old = view.render(document, view_id)
        projection = old['projection']
        parents = [(key, node) for key, node in projection['nodes'].items() if node['element_id'] == owner_id]
        if projection['mode'] != 'definitions' or len(parents) != 1:
            raise EditError('element_kind', 'Select the native owner in a physical definition hierarchy')
        parent_id, parent = parents[0]
        if len(projection['nodes']) >= 128 or parent['level'] >= 16:
            raise EditError('presentation_conflict', 'The physical view node or depth limit would be exceeded')
        candidate = document._create_definition_source(owner_id, element_id, new_name, short_id,
            expected_source_sha256=expected_source_sha256)
        candidate.reconciliation = deepcopy(document.reconciliation)
        occurrence, edge = 'N'+element_id.replace('-', ''), 'E'+element_id.replace('-', '')
        if {occurrence, edge} & (projection['nodes'].keys() | projection['edges'].keys()):
            raise EditError('identity', 'Generated presentation identity collides with this view')
        node = {'id': occurrence, 'element': candidate.registry[element_id], 'parent': parent_id,
                'level': parent['level']+1, 'edge': edge}
        candidate = _append_node(candidate, view_id, node)
        added_projection = view.project(candidate, view_id)
        names = view.labels(candidate, added_projection)
        layout = deepcopy(old['layout'])
        if placement is None:
            width = 360
            height = max(90, 40+sum(math.ceil(size*1.4) for _, size, _, _ in
                view.node_lines(added_projection['nodes'][occurrence], names[node['element']], width)))
            owner = layout['nodes'][parent_id]
            bottom = max([box['y']+box['height'] for box in layout['nodes'].values()]+
                         [point[1] for route in layout['edges'].values() for point in route['points']])
            box = {'x': owner['x']+owner['width']+80, 'y': bottom+60, 'width': width, 'height': height}
            x, y = owner['x']+owner['width'], owner['y']+owner['height']/2
            points = [[x, y], [x+30, y], [x+30, box['y']+height/2], [box['x'], box['y']+height/2]]
        else:
            view.exact(placement, ('box', 'points'))
            box, points = deepcopy(placement['box']), deepcopy(placement['points'])
        layout['nodes'][occurrence] = box
        layout['edges'][edge] = {'points': points}
        records = deepcopy(candidate.linked_records)
        appearance_name, appearance = view.companion(candidate, 'composition_appearance', view_id)
        if appearance is not None:
            appearance['nodes'][occurrence] = {'template': view.RECT, 'fill': 'N0', 'stroke': 'N100', 'text': 'N100', 'align': 'center'}
            records[appearance_name]['text'] = json.dumps(appearance, indent=2)+'\n'
        # Existing boxes/routes remain exact. Only the canvas may grow for the
        # new frame, route and existing authored footer key.
        footer = 160+34*len(appearance['legend']) if appearance is not None else 100
        layout['width'] = max(layout['width'], box['x']+box['width']+56, max(p[0] for p in points)+56)
        layout['height'] = max(layout['height'], box['y']+box['height']+footer, max(p[1] for p in points)+footer)
        layout_name, _ = view.companion(candidate, 'composition_layout', view_id)
        layout_name = layout_name or 'presentation/'+view_id+'.layout.json'
        if layout_name in candidate.files or layout_name in records and records[layout_name]['kind'] != 'composition_layout':
            raise EditError('file_name', 'Presentation filename collides with an authoritative file')
        records[layout_name] = {'kind': 'composition_layout', 'text': json.dumps(layout, indent=2, allow_nan=False)+'\n'}
        result = type(document)(candidate.files if document.is_bundle else candidate.files['model.sysml'],
            project_id=document.project_id, registry=candidate.registry, linked_records=records)
        result.reconciliation = deepcopy(document.reconciliation)
        view.validate_saved_presentations(result)
        return result
    except EditError:
        raise
    except (ValueError, KeyError, TypeError, StopIteration, RecursionError) as exc:
        raise EditError('presentation_conflict', str(exc)) from exc
