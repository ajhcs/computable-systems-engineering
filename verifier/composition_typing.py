"""Source-preserving explicit native typing on one existing part usage."""
from copy import deepcopy

from .composition_edit import EditError, bounds, codepoint_index, elements, fingerprint
from .composition_records import rebind_document, rebind_json


def typing_sources(document, item):
    rows = item['source_span'].get('typing_sources')
    if not isinstance(rows, list) or len(rows) != len(item['types']) or len(rows) > 128:
        raise EditError('parser_contract', 'Native explicit-typing source inventory unavailable or over limit')
    declaration = bounds(document.source, item['source_span'])
    previous = declaration[0]
    for index, row in enumerate(rows):
        if row.get('status') != 'direct_reference' or row.get('target') != item['types'][index]:
            raise EditError('typing_form', 'Typing needs a direct native type reference; inspect unsupported feature-chain or implied typing in source')
        left, right = bounds(document.source, row)
        prefix, tokens = row.get('prefix_tokens'), row.get('reference_tokens')
        if (not isinstance(prefix, list) or not isinstance(tokens, list)
                or not 1 <= len(tokens) <= 1024 or not 1 <= len(prefix) <= 2):
            raise EditError('source_span', 'Native typing token coordinates unavailable')
        spelling = tuple(token.get('text') for token in prefix)
        if spelling not in ((':',), ('defined', 'by'), (',',)) or index == 0 and spelling == (',',):
            raise EditError('source_span', 'Native typing delimiter is unsupported')
        for token in prefix + tokens:
            start, end = bounds(document.source, token)
            if not (previous <= start < end <= declaration[1]
                    and document.source[start:end] == token.get('text')):
                raise EditError('source_span', 'Native typing tokens overlap, exceed their declaration or disagree with source')
            if token in prefix and end > left or token in tokens and not left <= start < end <= right:
                raise EditError('source_span', 'Native typing reference/delimiter boundary disagrees')
            previous = end
    return rows


def retained_references(document, item):
    rows = typing_sources(document, item)
    spans = {(row['offset'], row['length'], row['target']) for row in rows}
    references = document.parsed.get('reference_spans')
    if not isinstance(references, list) or len(references) > 16384:
        raise EditError('parser_contract', 'Native reference inventory unavailable or over limit')
    retained, selected = [], []
    for ref in references:
        if ref.get('resolved') is not True:
            raise EditError('unresolved_reference', 'Native reference is unresolved')
        if ref.get('feature') == 'type' and (ref.get('offset'), ref.get('length'), ref.get('target')) in spans:
            selected.append(ref['target'])
        else:
            retained.append((ref.get('feature'), ref.get('target')))
    if selected != item['types']:
        raise EditError('parser_contract', 'Native explicit typing and reference inventories disagree')
    return retained


def set_types(document, element_id, type_ids, *, expected_source_sha256):
    if expected_source_sha256 != document.revision:
        raise EditError('stale_revision', 'Source changed before candidate preparation')
    if not isinstance(element_id, str) or element_id not in document.registry:
        raise EditError('identity', 'Unknown engineering element')
    if (not isinstance(type_ids, list) or len(type_ids) > 128
            or any(not isinstance(value, str) for value in type_ids)
            or len(set(type_ids)) != len(type_ids)):
        raise EditError('typing', 'Supply zero through 128 distinct part-definition UUIDs; empty means no explicit typing')
    native = elements(document.parsed)
    name = document.registry[element_id]
    item = native[name]
    if item['kind'] != 'parts':
        raise EditError('element_kind', 'Explicit feature typing belongs to a part usage')
    types, references = [], []
    for identity in type_ids:
        if identity not in document.registry:
            raise EditError('identity', 'Unknown part-definition type')
        definition = native[document.registry[identity]]
        if definition['kind'] != 'part_definitions':
            raise EditError('element_kind', 'Usage typing requires part definitions')
        reference = definition['source_span'].get('qualified_reference')
        if not isinstance(reference, str) or not reference:
            raise EditError('parser_contract', 'Native qualified type reference unavailable')
        types.append(definition['qualified_name'])
        references.append(reference)
    anchors = typing_sources(document, item)
    retained = retained_references(document, item)
    # Preserve exact source when the engineer has requested its existing list.
    if types == item['types']:
        return document
    changes = []
    if anchors:
        for index, anchor in enumerate(anchors):
            if index > 0 or not types:
                changes.extend((*bounds(document.source, token), '') for token in anchor['prefix_tokens'])
            for token_index, token in enumerate(anchor['reference_tokens']):
                changes.append((*bounds(document.source, token),
                                ', '.join(references) if index == 0 and token_index == 0 else ''))
    elif types:
        start, end = bounds(document.source, item['source_span'])
        offset = codepoint_index(document.source, item['source_span'].get('multiplicity_insert_offset'))
        if not start < offset < end:
            raise EditError('source_span', 'Native typing insertion anchor unavailable')
        changes.append((offset, offset, ' : ' + ', '.join(references)))
    # An unchanged identity still has to pass each linked contract's adapter.
    try:
        for record in document.parsed.get('documents', []):
            rebind_document(record['body'], record.get('name'), lambda value: value)
        for record in document.linked_records.values():
            rebind_json(record['text'], record['kind'], lambda value: value)
    except (ValueError, KeyError, TypeError, RecursionError) as exc:
        raise EditError('linked_records', str(exc)) from exc
    changes.sort()
    if any(a[1] > b[0] for a, b in zip(changes, changes[1:])):
        raise EditError('overlapping_edits', 'Native typing tokens overlap')
    files = document.candidate_files(changes)
    candidate = type(document)(files if document.is_bundle else files['model.sysml'],
                              project_id=document.project_id, registry=document.registry,
                              linked_records=document.linked_records)
    expected = fingerprint(document.parsed)
    for row in expected['parts']:
        if row['qualified_name'] == name:
            row['types'] = types
            if len(types) == 1:
                row['type'] = types[0]
            else:
                row.pop('type', None)
    if fingerprint(candidate.parsed) != expected:
        raise EditError('semantic_delta', 'Native reparse changed facts outside the exact requested explicit types')
    if retained_references(candidate, elements(candidate.parsed)[name]) != retained:
        raise EditError('reference_delta', 'Native reparse changed references outside the selected explicit typing')
    candidate.reconciliation = deepcopy(document.reconciliation)
    return candidate
