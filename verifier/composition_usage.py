"""One native part-usage declaration and its applicable physical presentation."""
from copy import deepcopy
import re
from uuid import UUID

from .composition_edit import EditError, bounds, elements, fingerprint, name_spelling
from . import composition_view as view


def create_usage_source(document, owner_id, element_id, new_name, short_id,
                        type_id, is_composite, multiplicity, *, expected_source_sha256):
    if expected_source_sha256 != document.revision:
        raise EditError('stale_revision', 'Source changed before candidate preparation')
    try:
        if not isinstance(element_id, str) or str(UUID(element_id)) != element_id or element_id in document.registry:
            raise ValueError('New identity must be distinct')
    except (ValueError, TypeError, AttributeError) as exc:
        raise EditError('identity', 'Supply a distinct canonical engineering UUID') from exc
    if not isinstance(owner_id, str) or owner_id not in document.registry:
        raise EditError('identity', 'Unknown native owner')
    native = elements(document.parsed)
    owner_name = document.registry[owner_id]
    owner = native[owner_name]
    if type(is_composite) is not bool:
        raise EditError('input', 'Choose composite part or reference explicitly')
    if multiplicity is not None and (not isinstance(multiplicity, dict)
            or set(multiplicity) != {'lower', 'upper'}
            or any(type(v) is not int for v in multiplicity.values())
            or not 0 <= multiplicity['lower'] <= multiplicity['upper'] <= 2_147_483_647):
        raise EditError('multiplicity', 'Use native default or integer bounds 0 <= lower <= upper <= 2147483647')
    selected_type = None
    if type_id is not None:
        if not isinstance(type_id, str) or type_id not in document.registry:
            raise EditError('identity', 'Unknown part-definition type')
        selected_type = native[document.registry[type_id]]
        if selected_type['kind'] != 'part_definitions':
            raise EditError('element_kind', 'Usage typing requires a part definition')
        if not isinstance(selected_type['source_span'].get('qualified_reference'), str):
            raise EditError('parser_contract', 'Native qualified type reference unavailable')
    spelling = name_spelling(new_name)
    short = name_spelling(short_id)['source_token'] if short_id is not None else None
    members = owner['source_span'].get('member_names')
    if not isinstance(members, list) or not all(isinstance(value, str) for value in members):
        raise EditError('parser_contract', 'Native owner membership names unavailable')
    if new_name in members or short_id is not None and short_id in members:
        raise EditError('name_collision', 'An owned member or alias already uses that name or short ID')
    qualified = owner_name+'::'+spelling['qualified_segment']
    if qualified in native:
        raise EditError('name_collision', 'Native qualified identity already exists')
    span = owner['source_span']
    start, end = bounds(document.source, span, 'namespace_end_')
    owner_start, owner_end = bounds(document.source, span)
    if not owner_start <= start < end <= owner_end:
        raise EditError('source_span', 'Native namespace boundary is outside its owner')
    terminal = document.source[start:end]
    if terminal != span.get('namespace_end_text') or terminal not in (';', '}'):
        raise EditError('source_span', 'Native owner boundary does not match its source token')
    a, _, file = document.file_range(start, end)
    newline = '\r\n' if '\r\n' in document.files[file] else '\n'
    line_start = document.source.rfind('\n', a, owner_start)+1
    indent = re.match(r'[ \t]*', document.source[line_start:owner_start]).group()
    declaration = ('' if is_composite else 'ref ')+'part '+('<'+short+'> ' if short is not None else '')+spelling['source_token']
    if multiplicity is not None:
        lo, hi = multiplicity['lower'], multiplicity['upper']
        declaration += ' ['+(str(lo) if lo == hi else f'{lo}..{hi}')+']'
    if selected_type is not None:
        declaration += ' : '+selected_type['source_span']['qualified_reference']
    declaration += ';'
    replacement = newline+indent+'    '+declaration+newline+indent
    changes = [(start, end, ' {'+replacement+'}')] if terminal == ';' else [(start, start, replacement)]
    files = document.candidate_files(changes)
    candidate = type(document)(files if document.is_bundle else files['model.sysml'],
        project_id=document.project_id, registry={**document.registry, element_id: qualified},
        linked_records=document.linked_records)
    expected = {'name': new_name, 'owner': owner_name,
                'owner_kind': 'PartDefinition' if owner['kind'] == 'part_definitions' else 'PartUsage',
                'qualified_name': qualified, 'nested': True,
                'types': [selected_type['qualified_name']] if selected_type else [],
                'redefines': [], 'subsets': [], 'is_composite': is_composite,
                'is_variation': False, 'is_variant': False,
                'multiplicity': {'status': 'literal', **multiplicity} if multiplicity is not None else
                                {'status': 'default', 'lower': 1, 'upper': 1},
                'has_native_value': False, 'has_non_typing_specialization': False}
    if short_id is not None:
        expected['id'] = short_id
    if selected_type:
        expected['type'] = selected_type['qualified_name']
    definition = owner_name if owner['kind'] == 'part_definitions' else owner.get('part_definition')
    if definition:
        expected['part_definition'] = definition
    before, after = fingerprint(document.parsed), fingerprint(candidate.parsed)
    added = [row for row in after['parts'] if row['qualified_name'] == qualified]
    if added != [expected]:
        raise EditError('semantic_delta', 'Native creation does not match the requested ordinary part usage and exact typing')
    after['parts'] = [row for row in after['parts'] if row['qualified_name'] != qualified]
    if before != after:
        raise EditError('semantic_delta', 'Native creation changed existing model facts')
    new = next(row for row in candidate.parsed['parts'] if row['qualified_name'] == qualified)
    left, right = bounds(candidate.source, new['source_span'])
    extra, retained = [], []
    for ref in candidate.parsed['reference_spans']:
        x, y = bounds(candidate.source, ref)
        (extra if left <= x < y <= right else retained).append(ref)
    refs = lambda rows: [(row.get('feature'), row.get('target')) for row in rows]
    if (refs(document.parsed['reference_spans']) != refs(retained)
            or any(row.get('resolved') is not True for row in extra)
            or refs(extra) != ([('type', selected_type['qualified_name'])] if selected_type else [])):
        raise EditError('reference_delta', 'Native creation changed references outside its exact new typing')
    candidate.reconciliation = deepcopy(document.reconciliation)
    return candidate


def create_usage(document, owner_id, element_id, new_name, short_id, type_id,
                 is_composite, multiplicity, view_id, placement, *, expected_source_sha256):
    try:
        old = view.render(document, view_id)
        candidate = create_usage_source(document, owner_id, element_id, new_name, short_id, type_id,
            is_composite, multiplicity, expected_source_sha256=expected_source_sha256)
        parents = [(key, row) for key, row in old['projection']['nodes'].items() if row['element_id'] == owner_id]
        if old['projection']['mode'] == 'usages' and is_composite and len(parents) == 1:
            from .composition_create import add_owned_frame
            parent_id, parent = parents[0]
            if len(old['projection']['nodes']) >= 128 or parent['level'] >= 16:
                raise EditError('presentation_conflict', 'The physical view node or depth limit would be exceeded')
            return add_owned_frame(document, candidate, old, view_id, owner_id, element_id, placement)
        if placement is not None:
            raise EditError('presentation_conflict', 'This usage has a declaration row, not a new ownership frame; omit placement')
        view.validate_saved_presentations(candidate)
        return candidate
    except EditError:
        raise
    except (ValueError, KeyError, TypeError, StopIteration, RecursionError) as exc:
        raise EditError('presentation_conflict', str(exc)) from exc
