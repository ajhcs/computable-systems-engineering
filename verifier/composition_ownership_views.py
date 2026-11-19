"""Explicit per-view consequences for a single native ownership candidate."""
from copy import deepcopy
import json
import re

from .composition_edit import EditError, bounds, fingerprint
from .composition_records import STRING, embedded_json, rebind_document, strict_json, strings
from . import composition_view as view
from .composition_ownership import _canonical_facts, _move_source, _ordered_edits, _rewrite


def normalize_route_points(effects):
    """Use the same numeric representation in browser and CLI ownership requests."""
    for effect in effects:
        if not isinstance(effect, dict) or effect.get('action') != 'reparent':
            continue
        points = effect.get('points')
        if not isinstance(points, list) or not 2 <= len(points) <= 128:
            raise EditError('presentation_conflict', 'Supply 2 through 128 ownership route points')
        for point in points:
            if (not isinstance(point, list) or len(point) != 2 or
                    any(type(value) not in (int, float) or not 0 <= value <= 8192 for value in point)):
                raise EditError('presentation_conflict', 'Ownership route points need finite coordinates within the canvas limit')
            for index, value in enumerate(point):
                if type(value) is float and value.is_integer():
                    point[index] = int(value)


def _views(document, *, allow_absent=False):
    rows = [row for row in document.parsed['documents'] if row.get('name') == 'cseViews']
    if not rows and allow_absent:
        return None
    if len(rows) != 1 or rows[0].get('owner_kind') != 'Package':
        raise EditError('presentation_conflict', 'Ownership editing needs one package-owned native cseViews record')
    row = rows[0]
    start, end = bounds(document.source, row['source_span'], 'body_')
    token = document.source[start:end]
    if not token.startswith('/*') or not token.endswith('*/'):
        raise EditError('source_span', 'Native view documentation token unavailable')
    body = token[2:-2]
    marker = re.match(r'\s*CSE-VIEWS/1\.1\s*\r?\n', body)
    if marker is None:
        raise EditError('presentation_conflict', 'Physical ownership editing uses the existing CSE-VIEWS/1.1 record')
    record = strict_json(body[marker.end():])
    rebind_document(row['body'], 'cseViews', lambda value: value)
    if not isinstance(record.get('views'), list):
        raise EditError('presentation_conflict', 'Native view inventory unavailable')
    return row, start+2+marker.end(), body[marker.end():], record


def _property_changes(raw, changes):
    """Change only admitted top-level node fields, retaining all other bytes."""
    current = strict_json(raw)
    tokens, values = list(STRING.finditer(raw)), list(strings(current))
    if len(tokens) != len(values):
        raise EditError('source_span', 'View-node JSON token correspondence failed')
    edits, found = [], set()
    for token, (path, is_key, value) in zip(tokens, values):
        if json.loads(token.group()) != value:
            raise EditError('source_span', 'View-node JSON value disagrees with source')
        if is_key and len(path) == 1 and path[0] in changes:
            match = re.match(r'\s*:\s*', raw[token.end():])
            if match is None:
                raise EditError('source_span', 'View-node field value unavailable')
            at = token.end()+match.end()
            old, until = json.JSONDecoder().raw_decode(raw, at)
            if old != current[path[0]]:
                raise EditError('source_span', 'View-node property/source mismatch')
            edits.append((at, until, embedded_json(changes[path[0]])))
            found.add(path[0])
    if found != set(changes):
        raise EditError('source_span', 'Requested view-node property unavailable')
    return _rewrite(raw, edits)


def _node_array(raw, selected, new_nodes):
    # Use the native record's already validated JSON. Decode complete top-level
    # objects; brackets/commas in labels or quoted identities are not delimiters.
    if not raw.startswith('[') or not raw.endswith(']'):
        raise EditError('source_span', 'Native view node array unavailable')
    pos, chunks, decoder = 1, [], json.JSONDecoder()
    for node in selected:
        whitespace = re.match(r'\s*', raw[pos:]).group()
        begin = pos+len(whitespace)
        value, end = decoder.raw_decode(raw, begin)
        if value != node:
            raise EditError('source_span', 'View node/source correspondence failed')
        match = re.match(r'\s*,', raw[end:])
        comma = end+match.end()-1 if match else None
        chunks.append((pos, begin, end, comma, node))
        pos = end+match.end() if match else end
    if raw[pos:].strip() != ']':
        raise EditError('source_span', 'Native view node array contains unmatched content')
    replacements = {node['id']: node for node in new_nodes}
    edits, removed = [], []
    for index, (_, begin, end, _, node) in enumerate(chunks):
        replacement = replacements.get(node['id'])
        if replacement is None:
            removed.append(index)
            continue
        updates = {key: value for key, value in replacement.items() if value != node.get(key)}
        if set(updates)-{'parent', 'level'}:
            raise EditError('presentation_conflict', 'Ownership consequence cannot alter unrelated node properties')
        if updates:
            edits.append((begin, end, _property_changes(raw[begin:end], updates)))
    if len(chunks)-len(removed) != len(new_nodes):
        raise EditError('presentation_conflict', 'Ownership consequences cannot create new diagram occurrences')
    # Remove contiguous runs with exactly one corresponding comma. Keep the
    # original whitespace around every retained object and all unedited fields.
    while removed:
        first = last = removed.pop(0)
        while removed and removed[0] == last+1:
            last = removed.pop(0)
        if last < len(chunks)-1:
            left, right = chunks[first][0], chunks[last+1][0]
        elif first > 0:
            left, right = chunks[first-1][3], chunks[last][2]
        else:
            left, right = 1, chunks[last][2]
        if left is None:
            raise EditError('source_span', 'View-removal comma/source correspondence failed')
        edits.append((left, right, ''))
    result = _rewrite(raw, edits)
    if strict_json(result) != new_nodes:
        raise EditError('source_span', 'Rewritten native view array differs from its explicit consequence')
    return result


def _change_nodes(document, replacements):
    _, offset, payload, record = _views(document)
    tokens, values = list(STRING.finditer(payload)), list(strings(record))
    if len(tokens) != len(values):
        raise EditError('source_span', 'Native view JSON source correspondence failed')
    edits, expected = [], deepcopy(record)
    for token, (path, is_key, value) in zip(tokens, values):
        if json.loads(token.group()) != value:
            raise EditError('source_span', 'Native view JSON value disagrees with source')
        if is_key and len(path) == 3 and path[0] == 'views' and path[2] == 'nodes':
            index = path[1]
            selected = record['views'][index]
            if selected['id'] not in replacements:
                continue
            match = re.match(r'\s*:\s*', payload[token.end():])
            if match is None:
                raise EditError('source_span', 'Native view node array value unavailable')
            at = token.end()+match.end()
            nodes, end = json.JSONDecoder().raw_decode(payload, at)
            if nodes != selected['nodes']:
                raise EditError('source_span', 'Native view node array/source mismatch')
            expected['views'][index]['nodes'] = replacements[selected['id']]
            edits.append((offset+at, offset+end, _node_array(payload[at:end], nodes, replacements[selected['id']])))
    if len(edits) != len(replacements):
        raise EditError('presentation_conflict', 'An affected physical view could not be updated exactly')
    files = document.candidate_files(_ordered_edits(edits))
    result = type(document)(files if document.is_bundle else files['model.sysml'], project_id=document.project_id,
                            registry=document.registry, linked_records=document.linked_records)
    if _views(result)[3] != expected:
        raise EditError('semantic_delta', 'Ownership view consequences changed unrelated native view content')
    before, after = fingerprint(document.parsed), fingerprint(result.parsed)
    for row in before['documents']:
        if row.get('name') == 'cseViews':
            row['body'] = next(item['body'] for item in after['documents'] if item.get('name') == 'cseViews')
    if _canonical_facts(before) != _canonical_facts(after):
        raise EditError('semantic_delta', 'View consequences changed unrelated native engineering facts')
    result.reconciliation = deepcopy(document.reconciliation)
    return result


def consequences(document, element_id):
    """Every affected physical view, with current occurrence/route identities."""
    if element_id not in document.registry:
        raise EditError('identity', 'Unknown captured engineering declaration')
    old, result = document.registry[element_id], []
    declared = _views(document, allow_absent=True)
    for selected in declared[3]['views'] if declared is not None else []:
        if selected.get('kind') != 'physical_composition':
            continue
        touched = [row for row in selected['nodes'] if row['element'] == old or row['element'].startswith(old+'::')]
        if not touched:
            continue
        painted = view.render(document, selected['id'])
        root = next((row for row in selected['nodes'] if row['element'] == old), None)
        result.append({'view_id': selected['id'], 'subject_node': root['id'] if root else None,
                       'current_parent': root['parent'] if root else None,
                       'incoming_edge': root['edge'] if root else None,
                       'required_action': 'reparent_or_remove_occurrences' if root and root['parent'] is not None else 'preserve_boundary_or_structure',
                       'affected_nodes': [row['id'] for row in touched],
                       'current_layout': deepcopy(painted['layout'])})
    return result


def reparent(document, element_id, destination, composition_transition, view_effects, *, expected_source_sha256):
    from .composition_ownership import _owner
    try:
        if not isinstance(view_effects, list) or len(view_effects) > 128:
            raise EditError('presentation_conflict', 'Supply an explicit consequence for every affected physical view')
        view_effects = deepcopy(view_effects)
        normalize_route_points(view_effects)
        expected = consequences(document, element_id)
        if (any(not isinstance(effect, dict) or not isinstance(effect.get('view_id'), str) for effect in view_effects)
                or len({effect['view_id'] for effect in view_effects}) != len(view_effects)
                or {effect['view_id'] for effect in view_effects} != {row['view_id'] for row in expected}):
            raise EditError('presentation_conflict', 'Affected-view consequences are missing, duplicate or extraneous')
        candidate = _move_source(document, element_id, destination, composition_transition,
                                 expected_source_sha256=expected_source_sha256)
        ownership_change = deepcopy(candidate.ownership_change)
        native_owner = _owner(document, destination)
        replacements, layouts, expected_layouts, removed = {}, {}, {}, {}
        after_views = {row['id']: row for row in _views(candidate)[3]['views']} if expected else {}
        effects = {row['view_id']: row for row in view_effects}
        for impact in expected:
            view_id = impact['view_id']
            effect, selected = effects[view_id], after_views[view_id]
            nodes, layout = deepcopy(selected['nodes']), deepcopy(impact['current_layout'])
            if impact['required_action'] == 'preserve_boundary_or_structure':
                if set(effect) != {'view_id', 'action'} or effect['action'] != 'preserve_structure':
                    raise EditError('presentation_conflict', 'The affected view boundary/structure must be retained explicitly')
            elif effect.get('action') == 'reparent':
                if set(effect) != {'view_id', 'action', 'parent_node', 'points'}:
                    raise EditError('presentation_conflict', 'A reparented occurrence needs its exact parent node and route points')
                parent = next((row for row in nodes if row['id'] == effect['parent_node']), None)
                if (parent is None or parent['element'] != native_owner.get('qualified_name')
                        or parent['id'] in impact['affected_nodes']):
                    raise EditError('presentation_conflict', 'New parent frame must be the exact native destination outside the moved subtree')
                subject = next(row for row in nodes if row['id'] == impact['subject_node'])
                delta = parent['level']+1-subject['level']
                subject['parent'] = parent['id']
                for node in nodes:
                    if node['id'] in impact['affected_nodes']:
                        node['level'] += delta
                layout['edges'][subject['edge']] = {'points': deepcopy(effect['points'])}
            elif effect.get('action') == 'remove_occurrences':
                if set(effect) != {'view_id', 'action'}:
                    raise EditError('presentation_conflict', 'View-only removal does not take hidden node or model edits')
                removed[view_id] = {'nodes': set(impact['affected_nodes']),
                                    'edges': {row['edge'] for row in nodes if row['id'] in impact['affected_nodes'] and row['edge'] is not None},
                                    'elements': {row['element'] for row in nodes if row['id'] in impact['affected_nodes']}}
                nodes = [row for row in nodes if row['id'] not in removed[view_id]['nodes']]
                if not nodes:
                    raise EditError('presentation_conflict', 'Ownership editing cannot leave an empty physical view')
                layout['nodes'] = {key: value for key, value in layout['nodes'].items() if key not in removed[view_id]['nodes']}
                layout['edges'] = {key: value for key, value in layout['edges'].items() if key not in removed[view_id]['edges']}
            else:
                raise EditError('presentation_conflict', 'Choose an explicit native parent/route or remove the affected view occurrences')
            expected_layouts[view_id] = layout
            if nodes != selected['nodes']:
                replacements[view_id] = nodes
            if effect.get('action') != 'preserve_structure' or view.render(candidate, view_id)['layout'] != layout:
                layouts[view_id] = layout
        if replacements:
            candidate = _change_nodes(candidate, replacements)
        linked = deepcopy(candidate.linked_records)
        for view_id, layout in layouts.items():
            name, saved_layout = view.companion(candidate, 'composition_layout', view_id)
            name = name or 'presentation/'+view_id+'.layout.json'
            if name in candidate.files or name in linked and linked[name]['kind'] != 'composition_layout':
                raise EditError('file_name', 'Ownership layout companion collides with an authoritative file')
            if saved_layout != layout:
                linked[name] = {'kind': 'composition_layout', 'text': json.dumps(layout, indent=2, allow_nan=False)+'\n'}
            if view_id not in removed:
                continue
            lost = removed[view_id]
            name, appearance = view.companion(candidate, 'composition_appearance', view_id)
            if appearance is not None:
                appearance['nodes'] = {key: value for key, value in appearance['nodes'].items() if key not in lost['nodes']}
                appearance['edges'] = {key: value for key, value in appearance['edges'].items() if key not in lost['edges']}
                linked[name] = {'kind': 'composition_appearance', 'text': json.dumps(appearance, indent=2)+'\n'}
            name, labels = view.companion(candidate, 'display_labels', view_id)
            if labels is not None:
                labels['labels'] = [row for row in labels['labels'] if row['element'] not in lost['elements']]
                linked[name] = {'kind': 'display_labels', 'text': json.dumps(labels, indent=2)+'\n'}
        result = type(document)(candidate.files if document.is_bundle else candidate.files['model.sysml'],
                                project_id=document.project_id, registry=candidate.registry, linked_records=linked)
        result.reconciliation = deepcopy(candidate.reconciliation)
        view.validate_saved_presentations(result)
        for impact in expected:
            view_id = impact['view_id']
            actual = view.render(result, view_id)
            if actual['layout'] != expected_layouts[view_id]:
                raise EditError('presentation_conflict', 'Ownership rendering changed the explicitly checked geometry')
        result.ownership_change = {**ownership_change,
                                   'element_id': element_id, 'destination': deepcopy(destination),
                                   'composition_transition': deepcopy(composition_transition),
                                   'view_effects': deepcopy(view_effects), 'affected_views': [row['view_id'] for row in expected]}
        return result
    except EditError:
        raise
    except (ValueError, KeyError, TypeError, StopIteration, RecursionError) as exc:
        raise EditError('presentation_conflict', str(exc)) from exc
