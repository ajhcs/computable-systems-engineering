"""Exact physical view consequences for native and view-only removal."""
from copy import deepcopy
import json
import re

from . import composition_view as view
from .composition_edit import EditError, bounds, fingerprint
from .composition_ownership_views import _change_nodes, _node_array, _views
from .composition_records import STRING, rebind_document, rebind_json
from .composition_removal import _effect_location, _key, delete_source, inspect_removal


def _views_by_id(document):
    record = _views(document, allow_absent=True)
    return {} if record is None else {row['id']: row for row in record[3]['views']}


def physical_view_ids(document):
    return [row['id'] for row in _views_by_id(document).values() if row['kind'] == 'physical_composition']


def _view_impact(document, selected, removed):
    drawing = view.render(document, selected['id'])
    nodes = [node for node in selected['nodes'] if node['id'] in removed]
    edges = {node['edge'] for node in nodes if node['edge'] is not None}
    closure = any(node['parent'] is None for node in nodes)
    _, appearance = view.companion(document, 'composition_appearance', selected['id'])
    styles = appearance['nodes'] if appearance else {}
    used = {row['template'] for node_id, row in styles.items() if node_id not in removed}
    lost = {row['template'] for node_id, row in styles.items() if node_id in removed} - used
    return {
        'view_id': selected['id'], 'action': 'close_view' if closure else 'remove_occurrences',
        'node_ids': sorted(removed), 'edge_ids': sorted(edges),
        'removed_templates': sorted(lost),
        'retained_authored_legend': list(appearance['legend']) if appearance and not closure else [],
        'layout': drawing['layout'],
    }


def model_removal_impact(document, element_id, *, expected_source_sha256):
    impact = inspect_removal(document, element_id, expected_source_sha256=expected_source_sha256)
    gone = set(impact['part_ids'].values())
    consequences = []
    for selected in _views_by_id(document).values():
        if selected['kind'] != 'physical_composition':
            continue
        removed = {node['id'] for node in selected['nodes'] if node['element'] in gone}
        if removed:
            consequences.append(_view_impact(document, selected, removed))
    return {**impact, 'views': consequences}


def _check_effects(impact, effects):
    required = {row['view_id']: {key: row[key] for key in ('view_id', 'action', 'node_ids', 'edge_ids')}
                for row in impact}
    if not isinstance(effects, list) or len(effects) != len(required):
        raise EditError('presentation_conflict', 'Supply the exact consequence for every affected view')
    for effect in effects:
        if not isinstance(effect, dict) or not isinstance(effect.get('view_id'), str):
            raise EditError('presentation_conflict', 'Supply a physical view ID for each consequence')
        if required.pop(effect['view_id'], None) != effect:
            raise EditError('presentation_conflict', 'A view consequence differs from the captured nodes, routes or closure')


def _close_views(document, closed):
    record, offset, raw, payload = _views(document)
    old = payload['views']
    keep = [row for row in old if row['id'] not in closed]
    if keep:
        opening = re.match(r'\s*\{\s*', raw)
        key = STRING.match(raw, opening.end()) if opening else None
        separator = re.match(r'\s*:\s*', raw[key.end():]) if key and json.loads(key.group()) == 'views' else None
        if separator is None:
            raise EditError('source_span', 'Physical view list has no exact source boundary')
        span_start = key.end() + separator.end()
        found, span_end = json.JSONDecoder().raw_decode(raw, span_start)
        if found != old:
            raise EditError('source_span', 'Physical view list differs from the native document')
        changed = _node_array(raw[span_start:span_end], old, keep)
        edit = (offset+span_start, offset+span_end, changed)
    else:
        start, end = bounds(document.source, record['source_span'])
        edit = (start, end, '')
    return document.candidate_files([edit]), keep


def _linked_presentations(document, consequences, views):
    linked = deepcopy(document.linked_records)
    expected_layouts = {}
    closed = set()
    replacements = {}
    for row in consequences:
        view_id = row['view_id']
        gone = set(row['node_ids'])
        edges = set(row['edge_ids'])
        keys = ('composition_layout', 'composition_appearance', 'display_labels')
        companions = {kind: view.companion(document, kind, view_id) for kind in keys}
        if row['action'] == 'close_view':
            closed.add(view_id)
            for name, _ in companions.values():
                if name is not None:
                    del linked[name]
            continue
        keep = [node for node in views[view_id]['nodes'] if node['id'] not in gone]
        replacements[view_id] = keep
        layout = deepcopy(row['layout'])
        layout['nodes'] = {node_id: box for node_id, box in layout['nodes'].items() if node_id not in gone}
        layout['edges'] = {edge_id: path for edge_id, path in layout['edges'].items() if edge_id not in edges}
        for kind, (saved, record) in companions.items():
            if kind == 'composition_layout':
                name = saved or 'presentation/'+view_id+'.layout.json'
                if name in document.files or saved is None and name in linked:
                    raise EditError('file_name', 'Removal layout companion collides with an authoritative file')
                record = layout
            elif record is None:
                continue
            elif kind == 'composition_appearance':
                name = saved
                record['nodes'] = {node_id: style for node_id, style in record['nodes'].items() if node_id not in gone}
                record['edges'] = {edge_id: style for edge_id, style in record['edges'].items() if edge_id not in edges}
            else:
                name = saved
                visible = {node['element'] for node in keep}
                record['labels'] = [label for label in record['labels'] if label['element'] in visible]
            if linked.get(name) is None or json.loads(linked[name]['text']) != record:
                linked[name] = {'kind': kind, 'text': json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False)+'\n'}
        expected_layouts[view_id] = layout
    return linked, expected_layouts, closed, replacements


def _prepare_views(document, consequences, effects):
    _check_effects(consequences, effects)
    if not consequences:
        return document, {}
    views = _views_by_id(document)
    linked, layouts, closed, replacements = _linked_presentations(document, consequences, views)
    amended = _change_nodes(document, replacements) if replacements else document
    files, keep = _close_views(amended, closed) if closed else (amended.files, None)
    prepared = type(document)(files if document.is_bundle else files['model.sysml'], project_id=document.project_id,
                              registry=document.registry, linked_records=linked)
    if keep is not None and list(_views_by_id(prepared).values()) != keep:
        raise EditError('semantic_delta', 'Close only the exact declared physical views')
    original = fingerprint(document.parsed)
    changed = fingerprint(prepared.parsed)
    old_views = [row for row in original['documents'] if row.get('name') == 'cseViews']
    next_views = [row for row in changed['documents'] if row.get('name') == 'cseViews']
    if len(old_views) != 1 or len(next_views) > 1 or any(
        {key: value for key, value in row.items() if key != 'body'}
        != {key: value for key, value in old_views[0].items() if key != 'body'}
        for row in next_views
    ):
        raise EditError('semantic_delta', 'Native view documentation identity changed unexpectedly')
    original['documents'] = [row for row in original['documents'] if row.get('name') != 'cseViews']
    changed['documents'] = [row for row in changed['documents'] if row.get('name') != 'cseViews']
    if original != changed:
        raise EditError('semantic_delta', 'Presentation effects changed the native engineering facts')
    # A package-owned view record can precede other model text. Compare
    # normalized native bindings with offsets removed only for this doc edit.
    def ref_facts(value):
        return [(row['feature'], row['target'], tuple(
            (part['kind'], part['name'], part.get('target'), part.get('alias_owner'))
            for part in row['name_binding']['segments']))
                for row in value.parsed['reference_spans']]

    if ref_facts(document) != ref_facts(prepared):
        raise EditError('reference_delta', 'Presentation effects changed a native reference')
    return prepared, layouts


def _assert_linked_scope(document, removed):
    def mark(name):
        return 'CSE-REMOVED' if name in removed else name

    try:
        for row in document.parsed['documents']:
            _, bindings = rebind_document(row['body'], row.get('name'), mark)
            if bindings:
                raise EditError('linked_records', 'A native documentary record still binds a removed declaration: '+row['name'])
        for file, row in document.linked_records.items():
            if row['kind'] != 'retained_configuration':
                _, bindings = rebind_json(row['text'], row['kind'], mark)
                if bindings:
                    raise EditError('linked_records', 'A linked record still binds a removed declaration: '+file)
    except EditError:
        raise
    except (ValueError, KeyError, TypeError, RecursionError) as exc:
        raise EditError('linked_records', str(exc)) from exc


def _check_drawings(document, expected_layouts):
    view.validate_saved_presentations(document)
    for view_id, layout in expected_layouts.items():
        if view.render(document, view_id)['layout'] != layout:
            raise EditError('presentation_conflict', 'The original remaining geometry changed unexpectedly')


def delete_element(document, element_id, reference_effects, view_effects, *, expected_source_sha256):
    impact = model_removal_impact(document, element_id, expected_source_sha256=expected_source_sha256)
    prepared, layouts = _prepare_views(document, impact['views'], view_effects)
    _assert_linked_scope(prepared, set(impact['part_ids'].values()))
    # View JSON can precede native declarations in the same file. Resolve the
    # source positions after that edit, preserving the ordered binding effect.
    new_impact = inspect_removal(prepared, element_id, expected_source_sha256=prepared.revision)
    if not isinstance(reference_effects, list) or not all(
        isinstance(effect, dict) and set(effect) == {'location', 'replacement_id'} and isinstance(effect['location'], dict)
        for effect in reference_effects
    ):
        raise EditError('explicit_effects', 'Supply exact captured reference effects')
    if [dict(row, location=None) for row in new_impact['incoming']] != [
        dict(row, location=None) for row in impact['incoming']
    ]:
        raise EditError('reference_delta', 'Presentation effects changed the captured reference inventory')
    remapped = []
    by_location = {_key(row['location']): index for index, row in enumerate(impact['incoming'])}
    for effect in reference_effects:
        index = by_location.get(_effect_location(effect['location']))
        if index is None:
            raise EditError('explicit_effects', 'Use an exact captured incoming reference locator')
        remapped.append({**effect, 'location': new_impact['incoming'][index]['location']})
    candidate, _ = delete_source(prepared, element_id, remapped, expected_source_sha256=prepared.revision)
    _check_drawings(candidate, layouts)
    return candidate, {**impact, 'retained_configuration': deepcopy(candidate.configuration_reviews)}


def occurrence_removal_impact(document, view_id, node_id, *, expected_source_sha256):
    if expected_source_sha256 != document.revision:
        raise EditError('stale_revision', 'Inspect the removal against the exact captured source')
    selected = view.find_view(document, view_id)
    nodes = {node['id']: node for node in selected['nodes']}
    if not isinstance(node_id, str) or node_id not in nodes:
        raise EditError('identity', 'Choose a captured diagram occurrence')
    gone = {node_id}
    for node in sorted(nodes.values(), key=lambda item: item['level']):
        if node['parent'] in gone:
            gone.add(node['id'])
    consequence = _view_impact(document, selected, gone)
    root = nodes[node_id]['element']
    element_id = next(identity for identity, native in document.registry.items() if native == root)
    return {'view_id': view_id, 'node_id': node_id, 'element_id': element_id,
            'bundle_sha256': document.revision, 'views': [consequence]}


def remove_occurrence(document, view_id, node_id, effects, *, expected_source_sha256):
    impact = occurrence_removal_impact(document, view_id, node_id, expected_source_sha256=expected_source_sha256)
    result, layouts = _prepare_views(document, impact['views'], effects)
    _check_drawings(result, layouts)
    return result, impact
