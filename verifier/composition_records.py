"""Exact JSON identity slots used by physical-composition rename candidates.

Only declared binding fields are rewritten. Source quotations, labels, IDs and
qualitative text retain their exact spelling. Retained scopes are inspected for
reconciliation; they are never automatically rewritten or accepted.
"""
import json
import math
import re

from .core import _pairs
from .workflow import schema as workflow_schema
from .visual_labels import load_labels
from .configuration import schema as configuration_schema


STRING = re.compile(r'"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"')


def strict_json(text):
    if not isinstance(text, str) or len(text.encode('utf-8')) > 1_000_000:
        raise ValueError('Linked JSON needs UTF-8 text within 1 MB')
    try:
        def finite_float(value):
            number = float(value)
            if not math.isfinite(number):
                raise ValueError('Nonfinite JSON number')
            return number
        return json.loads(text, object_pairs_hook=_pairs,
                          parse_float=finite_float,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    except (RecursionError, UnicodeError) as exc:
        raise ValueError('Linked JSON encoding or nesting is unsupported') from exc


def strings(value, path=()):
    """Walk keys and values in the same lexical order as the validated JSON."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield path + (key,), True, key
            yield from strings(item, path + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from strings(item, path + (index,))
    elif isinstance(value, str):
        yield path, False, value


def view_slots(record):
    if not isinstance(record, dict) or set(record) != {'views'} or not isinstance(record['views'], list):
        raise ValueError('CSE views needs its existing views list')
    slots = set()
    def fields(value, required, optional=()):
        if (not isinstance(value, dict) or not set(required) <= set(value)
                or set(value) - set(required) - set(optional)):
            raise ValueError('View contains missing or unknown fields; binding adapter cannot preserve their meaning')

    # This adapter changes identity spelling, not the admitted view semantics.
    # Full view validation remains the selected renderer/checker's obligation.
    for i, view in enumerate(record['views']):
        if not isinstance(view, dict):
            raise ValueError('Invalid CSE view')
        kind = view.get('kind')
        prefix = ('views', i)
        if kind == 'function_tree':
            fields(view, ('id', 'kind', 'nodes'))
        elif kind == 'physical_composition':
            fields(view, ('id', 'kind', 'mode', 'nodes'))
        elif kind == 'functional_flow':
            fields(view, ('id', 'kind', 'notation', 'nodes', 'edges'))
        elif kind == 'state':
            fields(view, ('id', 'kind', 'owner', 'nodes', 'edges'))
        elif kind == 'sequence':
            fields(view, ('id', 'kind', 'participants', 'exchanges'), ('rows',))
        if kind in ('function_tree', 'physical_composition', 'functional_flow', 'state'):
            if not isinstance(view.get('nodes'), list):
                raise ValueError('View nodes must be explicit')
            for j, node in enumerate(view['nodes']):
                if not isinstance(node, dict) or not isinstance(node.get('element'), str):
                    raise ValueError('View node needs a native element binding')
                fields(node, ('id', 'element'),
                       {'function_tree': ('level', 'parent'),
                        'physical_composition': ('level', 'parent', 'edge'),
                        'functional_flow': ('kind', 'code'), 'state': ()}[kind])
                slots.add(prefix + ('nodes', j, 'element'))
        elif kind != 'sequence':
            raise ValueError('Unknown view kind needs a binding adapter')
        if kind == 'sequence':
            if not isinstance(view['participants'], list) or not isinstance(view['exchanges'], list):
                raise ValueError('Sequence participants and exchanges must be lists')
            for j, participant in enumerate(view.get('participants', [])):
                if not isinstance(participant, dict) or not isinstance(participant.get('element'), str):
                    raise ValueError('Participant needs a native element binding')
                fields(participant, ('id', 'element'))
                slots.add(prefix + ('participants', j, 'element'))
            for j, exchange in enumerate(view.get('exchanges', [])):
                fields(exchange, ('id', 'from', 'to', 'message'),
                       ('element', 'timing', 'send_row', 'receive_row', 'in_transit'))
                if 'element' in exchange:
                    slots.add(prefix + ('exchanges', j, 'element'))
        if kind == 'state':
            slots.add(prefix + ('owner',))
            for j, edge in enumerate(view.get('edges', [])):
                fields(edge, ('id', 'element', 'from', 'to', 'event', 'effect', 'condition'))
                slots.add(prefix + ('edges', j, 'element'))
        if kind == 'functional_flow':
            for edge in view['edges']:
                fields(edge, ('id', 'from', 'to'), ('label', 'label_overbar'))
    return slots


def slots(record, kind):
    if kind == 'workflow':
        workflow_schema(record)
        return {('elements', key, 'native_name') for key in record['elements']}
    if kind == 'views':
        return view_slots(record)
    if kind == 'display_labels':
        load_labels(record)
        return {('labels', i, 'element') for i in range(len(record['labels']))}
    if kind == 'retained_configuration':
        configuration_schema(record)
        result = {('root', 'native_name'), ('root', 'type')}
        for section in ('selected_roles', 'external_roles'):
            for key in record.get(section, {}):
                result.update({(section, key, 'native_name'), (section, key, 'type')})
        result.update(('open_alternatives', i) for i in range(len(record['open_alternatives'])))
        # Connected configuration endpoint obligations refer to logical IDs;
        # native_connection is the explicit native identity, when present.
        for index, entry in enumerate(record['connections']):
            if record['version'] == 'configuration-1.0':
                result.update({('connections', index, 'from'), ('connections', index, 'to')})
            else:
                result.update({('connections', index, 'native_name'), ('connections', index, 'owner'),
                               ('connections', index, 'from', 'port'), ('connections', index, 'to', 'port')})
        return result
    raise ValueError('Unknown linked-record role')


def rebind_json(text, kind, mapped):
    record = strict_json(text)
    allowed = slots(record, kind)
    tokens = list(STRING.finditer(text))
    values = list(strings(record))
    if len(tokens) != len(values):
        raise ValueError('JSON token/source correspondence failed')
    changes, findings = [], []
    for token, (path, is_key, value) in zip(tokens, values):
        if json.loads(token.group()) != value:
            raise ValueError('JSON token/source correspondence failed')
        if is_key or path not in allowed:
            continue
        replacement = mapped(value)
        if replacement != value:
            findings.append({'path': list(path), 'before': value, 'after': replacement})
            if kind != 'retained_configuration':
                changes.append((token.start(), token.end(), json.dumps(replacement, ensure_ascii=True)))
    result = text
    for a, b, replacement in reversed(changes):
        result = result[:a] + replacement + result[b:]
    return result, findings


def rebind_document(body, name, mapped):
    if not isinstance(body, str):
        raise ValueError('Malformed native documentation body')
    match = re.match(r'\s*(CSE-[^\r\n]+)(?:\r?\n)', body)
    expected = {'cseWorkflow': (('CSE-WORKFLOW/1.0', 'CSE-WORKFLOW/1.1'), 'workflow'),
                'cseViews': (('CSE-VIEWS/1.0', 'CSE-VIEWS/1.1'), 'views')}
    if name not in expected:
        if isinstance(name, str) and name.startswith('cse') and mapped(body) != body:
            raise ValueError('Affected unknown CSE documentation needs a binding adapter')
        # An unknown structured CSE record can contain bindings among other text.
        if isinstance(name, str) and name.startswith('cse') and 'CSE-' in body:
            raise ValueError('CSE documentation needs its typed binding adapter')
        return body, []
    versions, kind = expected[name]
    if not match or match.group(1).strip() not in ((versions,) if isinstance(versions, str) else versions):
        raise ValueError('Unsupported CSE documentation header')
    if kind == 'workflow':
        record = strict_json(body[match.end():])
        if match.group(1).strip().replace('CSE-WORKFLOW/', 'workflow-') != record.get('version'):
            raise ValueError('Workflow marker and record version disagree')
    rewritten, findings = rebind_json(body[match.end():], kind, mapped)
    return body[:match.end()] + rewritten, findings
