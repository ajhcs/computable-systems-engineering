"""Source-bound inspection occurrences; existing configuration reports own verdicts."""
from copy import deepcopy
from hashlib import sha256
import json

from .composition_records import strict_json


def _native(document, row):
    result = {k: deepcopy(v) for k, v in row.items()
              if k not in ('source_span', 'source_location', 'element_id', 'kind')}
    if 'multiplicity_offset' in row.get('source_span', {}):
        from .composition_edit import bounds
        start, end = bounds(document.source, row['source_span'], 'multiplicity_')
        result['source_multiplicity'] = document.source[start:end]
    return result


def project(document, view_id, frames):
    """No source edits, scope replacement, ancestry inference or new verdicts."""
    native = {}
    for row in document.inspect()['elements']:
        native[row['qualified_name']] = {
            'element': row['qualified_name'], 'element_id': row['element_id'],
            'kind': 'PartDefinition' if row['kind'] == 'part_definitions' else 'PartUsage',
            'native': _native(document, row), 'source_location': deepcopy(row['source_location'])}
    occurrences, declarations, scopes = {}, [], []
    for occurrence, frame in frames.items():
        occurrences[occurrence] = {**deepcopy(frame),
            'source_location': deepcopy(native[frame['element']]['source_location']),
            'origin': 'frame', 'frame_id': occurrence, 'role': None}
    for name, row in sorted(native.items()):
        occurrence = 'decl:'+row['element_id']
        occurrences[occurrence] = {**deepcopy(row), 'id': occurrence,
            'origin': 'declaration', 'frame_id': None, 'role': None}
        declarations.append(occurrence)
    for review in document.configuration_reviews:
        filename, digest, report = review['file'], review['scope_sha256'], review['report']
        scope = strict_json(document.linked_records[filename]['text'])
        rows = [('configuration_root', '$root', scope['root'])]
        rows += [('selected_role', k, v) for k, v in sorted(scope['selected_roles'].items())]
        rows += [('external_role', k, v) for k, v in sorted(scope.get('external_roles', {}).items())]
        ids = []
        for kind, identity, binding in rows:
            key = json.dumps([filename, digest, kind, identity], ensure_ascii=True, separators=(',', ':'))
            occurrence = 'scope:'+sha256(key.encode()).hexdigest()
            requested = binding['native_name']; row = native.get(requested)
            checked = identity in report.get('checked', [])
            parent = None
            if kind == 'selected_role':
                parent = (scope['root'] if binding['parent'] == '$root'
                          else scope['selected_roles'][binding['parent']])
            role = {'file': filename, 'scope_sha256': digest, 'profile': scope['version'],
                    'kind': kind, 'id': identity, 'binding': deepcopy(binding),
                    'selected_parent': deepcopy(parent), 'checked': checked,
                    'findings': [deepcopy(f) for f in report.get('findings', []) if f['id'] == identity],
                    'review_status': report['status'], 'membership': None}
            # A checked role already passed the existing native owner/type/
            # inheritance/override rules. This label only describes that result.
            if checked and row and parent:
                owner = row['native'].get('owner')
                role['membership'] = ('usage_owned' if owner == parent['native_name'] else
                                      'type_owned' if owner == parent['type'] else 'inherited')
            occurrences[occurrence] = {
                **deepcopy(row or {'element': requested, 'element_id': None, 'kind': None,
                                  'native': None, 'source_location': None}),
                'id': occurrence, 'origin': kind, 'frame_id': None, 'role': role}
            ids.append(occurrence)
        scopes.append({'file': filename, 'scope_sha256': digest, 'profile': scope['version'],
                       'occurrences': ids, 'report': deepcopy(report)})
    return {'version': 'cse-composition-inspection-1', 'project_id': document.project_id,
            'view_id': view_id, 'bundle_sha256': document.revision,
            'occurrences': occurrences, 'declarations': declarations, 'scopes': scopes,
            'counts': {'frames': len(frames), 'declarations': len(declarations),
                       'scopes': len(scopes), 'retained_roles': sum(len(s['occurrences']) for s in scopes)},
            'claim': 'source_and_existing_review_inspection_not_new_selection_or_acceptance'}


def page(inspection, *, origin=None, offset=0, limit=25, expected_bundle_sha256=None):
    """A revision-bound page does not change the complete retained review scope."""
    if expected_bundle_sha256 is not None and expected_bundle_sha256 != inspection['bundle_sha256']:
        raise ValueError('Inspection source changed; read a current snapshot')
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Use a nonnegative offset and limit from 1 through 100')
    if origin not in (None, 'frame', 'declaration', 'configuration_root', 'selected_role', 'external_role'):
        raise ValueError('Unknown inspection origin')
    rows = [row for row in inspection['occurrences'].values() if origin is None or row['origin'] == origin]
    selected = rows[offset:offset+limit]
    return {'project_id': inspection['project_id'], 'view_id': inspection['view_id'],
            'bundle_sha256': inspection['bundle_sha256'], 'origin': origin, 'offset': offset,
            'limit': limit, 'total': len(rows), 'next_offset': offset+len(selected) if offset+len(selected) < len(rows) else None,
            'items': deepcopy(selected), 'scope': 'inspection_page_never_replaces_retained_review_scope'}
