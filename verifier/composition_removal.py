"""Revision-bound native removal and source effects for physical composition."""
from .composition_edit import EditError, bounds, elements, fingerprint
from .composition_ownership import _ordered_edits, _position
from .composition_typing import typing_sources

_ALIAS_KINDS = {'alias_name', 'alias_short_name'}
_PART_KINDS = {'PartUsage', 'PartDefinition'}
_MEMBERSHIP_KINDS = {'FeatureMembership', 'OwningMembership'}
_SPECIALIZATION_KINDS = {'FeatureTyping', 'Subclassification', 'Redefinition', 'Subsetting', 'ReferenceSubsetting'}


def _local_span(document, span):
    start, end = bounds(document.source, span)
    file_start, _, name = document.file_range(start, end)
    return name, start - file_start, end - file_start


def _bindings(document):
    rows = document.parsed.get('reference_spans')
    if not isinstance(rows, list) or len(rows) > 16_384:
        raise EditError('parser_contract', 'Native reference inventory unavailable or over limit')
    for row in rows:
        binding = row.get('name_binding', {})
        segments = binding.get('segments')
        if (row.get('resolved') is not True or binding.get('status') != 'resolved'
                or not isinstance(segments, list) or not segments or segments[-1].get('target') != row.get('target')):
            span = _location(_local_span(document, row))
            raise EditError('reference_form', f"Native reference path is incomplete at {span['file']} offset {span['offset']}")
        aliases = []
        for segment in segments:
            if segment['kind'] in _ALIAS_KINDS:
                anchor = segment.get('alias_source_span')
                if not segment.get('alias_is_external') and not isinstance(anchor, dict):
                    raise EditError('reference_form', 'A local native alias lacks its declaration anchor')
                aliases.append((segment.get('alias_owner'), _local_span(document, anchor) if anchor else None))
        yield _local_span(document, row), row, segments, tuple(aliases)


def _collect(document, element_id, expected_source_sha256):
    if expected_source_sha256 != document.revision:
        raise EditError('stale_revision', 'Inspect the removal against the exact captured source')
    if not isinstance(element_id, str) or element_id not in document.registry:
        raise EditError('identity', 'Choose a current native part UUID')
    native = elements(document.parsed)
    selected = document.registry[element_id]
    span = _local_span(document, native[selected]['source_span'])
    path, left, right = span
    parts = {}
    for identity, name in document.registry.items():
        file, start, end = _local_span(document, native[name]['source_span'])
        if path == file and left <= start < end <= right:
            parts[identity] = name
    return span, parts, native


def _owned_blockers(document, parts, native):
    names = set(parts.values())
    blockers = []
    expected_by_owner = {name: set() for name in names}
    for name in names:
        owner = native[name].get('owner')
        if owner in expected_by_owner:
            expected_by_owner[owner].add(name)
    for name in sorted(names):
        item = native[name]
        parent_path, parent_left, parent_right = _local_span(document, item['source_span'])
        rows = item['source_span'].get('owned_relationship_sources')
        if not isinstance(rows, list):
            raise EditError('parser_contract', 'Native authored relationship inventory unavailable')
        observed_children = set()
        for row in rows:
            kind = row['relationship_kind']
            children = row['owned_elements']
            location = _local_span(document, row) if 'offset' in row else None
            if location and not (location[0] == parent_path and parent_left <= location[1] < location[2] <= parent_right):
                raise EditError('source_span', 'Native owned relationship crosses its declaration')
            child, = children if len(children) == 1 else ({},)
            if kind in _MEMBERSHIP_KINDS and child.get('kind') in _PART_KINDS:
                child_name = child.get('identity')
                if (child_name in names and native[child_name].get('owner') == name
                        and location and 'offset' in child
                        and _local_span(document, child) == _local_span(document, native[child_name]['source_span'])):
                    observed_children.add(child_name)
                    continue
            if (kind in _MEMBERSHIP_KINDS and item['kind'] == 'parts'
                    and child.get('kind') in ('Multiplicity', 'MultiplicityRange')):
                continue
            if kind in _SPECIALIZATION_KINDS and location and not children:
                continue
            blockers.append({'owner': name, 'relationship': kind, 'member_kinds': [child['kind'] for child in children],
                             'source_location': _location(location) if location else None})
        if not expected_by_owner[name].issubset(observed_children):
            raise EditError('parser_contract', 'Removed part inventory disagrees with native authored membership')
    return blockers


def _location(span):
    path, start, end = span
    return {'file': path, 'offset': start, 'length': end - start, 'encoding': 'codepoints'}


def _inside(span, removal):
    path, left, right = span
    chosen, start, end = removal
    return path == chosen and start <= left < right <= end


def _direct_typing_anchors(document, native, removed_names):
    for identity, name in document.registry.items():
        if name in removed_names or native[name]['kind'] != 'parts':
            continue
        for item in native[name]['source_span'].get('typing_sources', []):
            if item.get('status') == 'direct_reference':
                yield _local_span(document, item), identity


def inspect_removal(document, element_id, *, expected_source_sha256):
    """Resolve all observed incoming paths and the exact affected part membership."""
    removal, parts, native = _collect(document, element_id, expected_source_sha256)
    names = set(parts.values())
    anchors = dict(_direct_typing_anchors(document, native, names))
    incoming = []
    for span, row, segments, aliases in _bindings(document):
        if _inside(span, removal):
            continue
        reasons = []
        if row['target'] in names:
            reasons.append('terminal_target')
        if any(segment.get('target') in names for segment in segments[:-1]):
            reasons.append('path_segment')
        if any(anchor and _inside(anchor, removal) for _, anchor in aliases):
            reasons.append('local_alias')
        if not reasons:
            continue
        path, start, end = span
        typing_owner = anchors.get(span) if row['feature'] == 'type' else None
        incoming.append({'location': _location(span), 'target': row['target'], 'feature': row['feature'],
                         'spelling': document.files[path][start:end], 'reasons': reasons, 'typing_owner_id': typing_owner})
    return {'element_id': element_id, 'bundle_sha256': document.revision,
            'part_ids': parts, 'location': _location(removal), 'incoming': incoming,
            'owned_blockers': _owned_blockers(document, parts, native)}


def _key(location):
    return location['file'], location['offset'], location['offset'] + location['length']


def _effect_location(location):
    if (not isinstance(location, dict) or set(location) != {'file', 'offset', 'length', 'encoding'}
            or not isinstance(location['file'], str) or type(location['offset']) is not int
            or type(location['length']) is not int or not (location['offset'] >= 0 and location['length'] > 0)
            or location['encoding'] != 'codepoints'):
        raise EditError('explicit_effects', 'Reference locations must use the observed file and codepoint bounds')
    return _key(location)

def _typing_edits(document, incoming, effects, native, removed):
    if not isinstance(effects, list) or len(effects) != len(incoming):
        raise EditError('explicit_effects', 'Supply exactly one effect per incoming native reference')
    expected = {_key(row['location']): row for row in incoming}
    grouped = {}
    targets = {}
    for effect in effects:
        if not isinstance(effect, dict) or set(effect) != {'location', 'replacement_id'}:
            raise EditError('explicit_effects', 'Each reference effect needs an exact source locator and replacement UUID or null')
        span = _effect_location(effect['location'])
        reference = expected.pop(span, None)
        if reference is None:
            raise EditError('explicit_effects', 'Unknown, stale or duplicate incoming reference location')
        owner = reference['typing_owner_id']
        if owner is None:
            raise EditError('reference_form', 'The incoming reference needs a supported source effect before deletion')
        replacement = effect['replacement_id']
        if replacement is not None and (
            not isinstance(replacement, str) or replacement not in document.registry or replacement in removed
            or native[document.registry[replacement]]['kind'] != 'part_definitions'
        ):
            raise EditError('explicit_effects', 'Replacement must be a surviving native part definition UUID')
        grouped.setdefault(document.registry[owner], {})[span] = replacement

    changes = []
    for name, requests in grouped.items():
        anchors = typing_sources(document, native[name])
        retained = []
        expected_types = []
        for index, anchor in enumerate(anchors):
            span = _local_span(document, anchor)
            if span not in requests:
                expected_types.append(anchor['target'])
                retained.append(index)
                continue
            replacement = requests.pop(span)
            if replacement is not None:
                target = document.registry[replacement]
                spelling = native[target]['source_span'].get('qualified_reference')
                if not spelling:
                    raise EditError('parser_contract', 'Native qualified replacement spelling unavailable')
                expected_types.append(target)
                retained.append(index)
            else:
                spelling = ''
            for index_in_reference, token in enumerate(anchor['reference_tokens']):
                changes.append((*bounds(document.source, token), spelling if index_in_reference == 0 else ''))

        if requests:
            raise EditError('explicit_effects', 'Incoming reference does not match a checked direct typing')
        if len(set(expected_types)) != len(expected_types):
            raise EditError('explicit_effects', 'Reference effects would duplicate a direct type')
        targets[name] = expected_types
        retained_indices = set(retained)
        for index, anchor in enumerate(anchors):
            needed = (index == 0 and bool(retained)) or (index in retained_indices and index != retained[0])
            if not needed:
                changes.extend((*bounds(document.source, token), '') for token in anchor['prefix_tokens'])
    return changes, targets


def _comparison(document, map_span, ignored):
    output = {}
    for span, row, segments, aliases in _bindings(document):
        if ignored(span):
            continue
        mapped = map_span(span)
        if mapped in output:
            raise EditError('reference_delta', 'Two retained native references occupy the same source span')
        output[mapped] = (
            row['feature'], row['target'],
            tuple((segment['kind'], segment['name'], segment.get('target')) for segment in segments),
            tuple((name, map_span(anchor) if anchor else None) for name, anchor in aliases),
        )
    return output


def delete_source(document, element_id, effects, *, expected_source_sha256):
    """Return the checked native candidate and impact for the view transaction."""
    impact = inspect_removal(document, element_id, expected_source_sha256=expected_source_sha256)
    if impact['owned_blockers']:
        raise EditError('owned_members', 'Resolve the listed native authored members before deletion')
    native = elements(document.parsed)
    removed = impact['part_ids']
    names = set(removed.values())
    file, start, end = removal = _key(impact['location'])
    file_offset, _, _ = next(row for row in document.ranges if row[2] == file)
    incoming = impact['incoming']
    changes, targets = _typing_edits(document, incoming, effects, native, removed)
    changes = _ordered_edits([*changes, (file_offset + start, file_offset + end, '')])
    local = {name: [] for name in document.files}
    for left, right, value in changes:
        origin, _, path = document.file_range(left, right)
        local[path].append((left-origin, right-origin, value))

    def map_span(span):
        path, left, right = span
        return path, _position(left, local[path]), _position(right, local[path])

    files = document.candidate_files(changes)
    registry = {identity: name for identity, name in document.registry.items() if identity not in removed}
    result = type(document)(files if document.is_bundle else files['model.sysml'], project_id=document.project_id,
                            registry=registry, linked_records=document.linked_records)
    expected = fingerprint(document.parsed)
    for key in ('parts', 'part_definitions'):
        expected[key] = [row for row in expected[key] if row['qualified_name'] not in names]
    for row in expected['parts']:
        if row['qualified_name'] in targets:
            types = targets[row['qualified_name']]
            row['types'] = types
            if len(types) == 1:
                row['type'] = types[0]
            else:
                row.pop('type', None)
    if fingerprint(result.parsed) != expected:
        raise EditError('native_delta', 'Native reparse changed facts outside the exact deletion and explicit typings')

    incoming_spans = {_key(row['location']) for row in incoming}
    before = _comparison(document, map_span, lambda span: _inside(span, removal) or span in incoming_spans)
    after = _comparison(result, lambda span: span, lambda span: False)
    for span, binding in before.items():
        if after.pop(span, None) != binding:
            raise EditError('reference_delta', 'A retained native reference changed its target or resolved path')
    # A qualified replacement can contain fewer tokens than the old term.
    # Its start must remain at the checked insertion point.
    expected_targets = {
        map_span(_key(row['location']))[:2]: document.registry[row['replacement_id']]
        for row in effects if row['replacement_id'] is not None
    }
    actual_changed = {(path, left): binding for (path, left, _), binding in after.items()}
    if ({site: (binding[0], binding[1]) for site, binding in actual_changed.items()}
            != {site: ('type', target) for site, target in expected_targets.items()}
            or len(actual_changed) != len(after)):
        raise EditError('reference_delta', 'A replacement did not resolve to its exact chosen native type')
    return result, impact
