"""Revision-bound presentations of existing concept and native model records.

The view is a retrieval aid. It neither infers engineering meaning nor replaces
the complete model and independent scope supplied to a required checker.
"""
from collections import deque
from copy import deepcopy
from hashlib import sha256
import json

from .core import _pairs
from .foundation import (Invalid, NATIVE, RELATIONS, check_profile, load_profile,
                         read_regular, term_digest)
from .context_inputs import parse_captured
from .context_native import add_native_references
from .sysml import check_sysml
from .workflow import (COMPOSED_MARKER, COMPOSED_VERSION, JOBS, KINDS,
                       MARKER, analyze, capture_model_inputs, schema)

VERSION = 'assembled-context-1.0'
GROUPS = ('part_definitions', 'parts', 'concerns', 'use_cases', 'actions',
          'states', 'requirements', 'constraints', 'attributes', 'events',
          'ports', 'port_definitions', 'connections')
IDENTIFIED = ('concerns', 'use_cases', 'requirements')
MAX_ELEMENTS = 512
MAX_NATIVE_RECORDS = 10000
MAX_OUTPUT_BYTES = 8_000_000
STATUS = {'pass': 0, 'not_run': 1, 'unknown': 2, 'unsupported': 3, 'fail': 4, 'error': 5}
WORKFLOW_RELATIONS = {'addresses', 'derives_from', 'allocated_to', 'scenario_of',
                      'precedes', 'participates_in', 'interfaces_with',
                      'information_to', 'controls', 'decomposes'}


def _status(states):
    return max(states, key=lambda value: STATUS.get(value, 5), default='pass')


def _base():
    return {'version': VERSION, 'claim_scope': 'assembled_existing_record_context',
            'status': 'not_run', 'retrieval_status': 'not_run',
            'semantic_review': 'not_run', 'required_review': 'not_evaluated',
            'acceptance': 'not_evaluated',
            'checker_scope': 'complete_supplied_model_unchanged',
            'profile_check': {'status': 'not_run', 'selected': False},
            'workflow_check': {'status': 'not_run', 'selected': False},
            'selection': {}, 'concepts': {},
            'elements': {'foundation': {}, 'workflow': {}},
            'relations': {'foundation': [], 'workflow': {}},
            'allocations': {}, 'use_cases': {}, 'capabilities': {},
            'english_context': {}, 'native_context': {}, 'workflow_context': {},
            'coverage': {'complete': False, 'total_elements': 0,
                         'returned_elements': 0, 'omitted_ids': [],
                         'unresolved': [], 'inclusion_reasons': {},
                         'policy': 'explicit_record_dependencies',
                         'semantic_completeness': 'not_evaluated'},
            'findings': [], 'provenance': {},
            'limits': {'elements': MAX_ELEMENTS, 'native_records': MAX_NATIVE_RECORDS,
                       'output_bytes': MAX_OUTPUT_BYTES,
                       'interpretation': 'No inference from definition prose; evidence remains at its recorded stage.'}}


def _issue(report, rule, status, ids, detail):
    report['findings'].append({'rule': rule, 'status': status,
                               'ids': list(ids), 'detail': detail})
    report['status'] = _status([report['status'], status])


def render_context_json(report):
    """The exact public CLI representation, including its final newline."""
    return json.dumps(report, sort_keys=True, indent=2, ensure_ascii=True,
                      allow_nan=False) + '\n'


def _bounded(report):
    """Refuse oversized results without retaining their large nested reports."""
    try:
        oversized = len(render_context_json(report).encode('utf-8')) > MAX_OUTPUT_BYTES
    except (ValueError, TypeError, RecursionError):
        oversized = True
    if not oversized:
        return report
    refused = _base()
    refused['status'] = refused['retrieval_status'] = 'error'
    refused['provenance']['input_stability'] = report.get('provenance', {}).get('input_stability', 'not_run')
    _issue(refused, 'context_output', 'error', [],
           'Assembled context exceeds output byte cap or cannot be serialized; no large partial view is retained.')
    return refused


def _workflow_record(native):
    inventory = native['inventory']
    docs = [item for item in inventory.get('documents', [])
            if item.get('name') == 'cseWorkflow']
    if not docs:
        return None, None
    if len(docs) != 1 or sum(item.get('qualified_name') == docs[0].get('owner')
                             for item in inventory.get('concerns', [])) != 1:
        raise Invalid('Expected one cseWorkflow document owned by one native concern')
    lines = docs[0].get('body', '').strip().splitlines()
    if not lines or lines[0].strip() not in (MARKER, COMPOSED_MARKER):
        raise Invalid('Unsupported workflow document header')
    raw = '\n'.join(lines[1:])
    if len(raw.encode('utf-8')) > 1_000_000:
        raise Invalid('Workflow record exceeds 1 MB')
    record = json.loads(raw, object_pairs_hook=_pairs,
                        parse_constant=lambda value: (_ for _ in ()).throw(Invalid('Nonfinite JSON value')))
    schema(record)
    expected = COMPOSED_MARKER if record['version'] == COMPOSED_VERSION else MARKER
    if lines[0].strip() != expected:
        raise Invalid('Workflow header and record version differ')
    return record, docs[0]['owner']


def _key(category, name):
    return category + ':' + name


def _bindings(profile, record):
    result = {'foundation': {}, 'workflow': {}}
    for origin, source, categories in (('foundation', profile, NATIVE),
                                       ('workflow', record, KINDS)):
        if source is not None:
            for identity, item in source['elements'].items():
                result[origin][identity] = {**deepcopy(item),
                                           'native_category': categories[item['kind']],
                                           'origin': origin + ('_profile' if origin == 'foundation' else '_document')}
    return result


def _native_index(inventory):
    result = {}
    count = sum(len(inventory.get(group, [])) for group in (*GROUPS, 'documents', 'event_attributes'))
    if count > MAX_NATIVE_RECORDS:
        raise Invalid('Native context exceeds record work cap')
    for group in GROUPS:
        for item in inventory.get(group, []):
            name = item.get('qualified_name')
            if not name:
                continue
            key = _key(group, name)
            if key in result:
                raise Invalid('Ambiguous native category/qualified identity: ' + key)
            result[key] = {'category': group, 'record': item}
    return result


def _select(index, bindings, *, short_id, element_id, native_name):
    selectors = [value for value in (short_id, element_id, native_name) if value is not None]
    if len(selectors) != 1 or type(selectors[0]) is not str or not selectors[0]:
        raise Invalid('Select exactly one nonempty short ID, element ID or qualified native identity')
    if element_id is not None:
        origins = ('foundation', 'workflow')
        identity = element_id
        if ':' in element_id:
            origin, identity = element_id.split(':', 1)
            if origin not in origins:
                raise Invalid('Element selector prefix must be foundation: or workflow:')
            origins = (origin,)
        matches = {_key(item['native_category'], item['native_name'])
                   for origin in origins for key, item in bindings[origin].items()
                   if key == identity}
    else:
        matches = {key for key, item in index.items()
                   if ((native_name is not None and item['record'].get('qualified_name') == native_name)
                       or (short_id is not None and item['category'] in IDENTIFIED
                           and item['record'].get('id') == short_id))}
    if len(matches) != 1 or not matches.issubset(index):
        raise Invalid('Expected one exact native identity; use a source-qualified element selector for ambiguous IDs')
    return next(iter(matches))


def _graph(index, bindings, profile, record, *, workflow='concept'):
    graph = {key: {} for key in index}

    def edge(left, right, reason, reverse=False):
        if left in graph and right in graph:
            graph[left].setdefault(right, []).append(reason)
            if reverse:
                graph[right].setdefault(left, []).append(reason)

    def bind(origin, identity):
        item = bindings[origin].get(identity)
        return _key(item['native_category'], item['native_name']) if item else None

    def scope(origin, identities, reason):
        # A scope's members share documentary context, not an assignment or an
        # engineering relation. A star keeps closure linear in the scope size.
        members = sorted({bind(origin, identity) for identity in identities
                          if bind(origin, identity) in graph})
        if members:
            for member in members[1:]:
                edge(members[0], member, reason, True)

    for origin, source in (('foundation', profile), ('workflow', record)):
        if source is None:
            continue
        relations = (enumerate(source['relations']) if origin == 'foundation'
                     else source['relations'].items())
        for identity, relation in relations:
            edge(bind(origin, relation['from']), bind(origin, relation['to']),
                 f'{origin}_relation:{identity}:{relation["kind"]}', True)
    if profile is not None:
        for identity, allocation in profile['allocations'].items():
            scope('foundation', allocation['functions'] + allocation['resources'],
                  'foundation_allocation_scope:' + identity)
        for identity, case in profile['use_cases'].items():
            for dependency in [case['subject'], *case['actors'], *case['scenarios']]:
                edge(bind('foundation', identity), bind('foundation', dependency),
                     'foundation_use_case:' + identity, True)
        for identity, view in profile.get('english', {}).get('views', {}).items():
            for use in view['uses']:
                if 'element' in use:
                    edge(bind('foundation', view['element']), bind('foundation', use['element']),
                         'english_use_binding:' + identity)
    if record is not None and workflow == 'trade-study':
        for identity, trade in record['trade_studies'].items():
            scope('workflow', trade['alternatives'] + list(trade['criteria']),
                  'workflow_trade_scope:' + identity)
    by_name = {}
    for key, item in index.items():
        by_name.setdefault(item['record']['qualified_name'], []).append(key)
    for key, item in index.items():
        row, group = item['record'], item['category']
        for subject in row.get('subjects', []):
            for target in by_name.get(subject.get('target'), []):
                edge(key, target, 'native_subject_reference')
        if group == 'parts':
            edge(key, _key('part_definitions', str(row.get('type'))), 'native_direct_type')
        if group == 'constraints':
            edge(_key('requirements', str(row.get('requirement'))), key, 'native_requirement_constraint')
        if group in ('attributes', 'events'):
            edge(_key('part_definitions', str(row.get('part_definition'))), key, 'native_declared_feature')
        # Contained participants, constraints and authored features retain their
        # exact qualified owner. This is documentary containment, not execution.
        parent = row['qualified_name'].rsplit('::', 1)[0]
        for owner in by_name.get(parent, []):
            edge(owner, key, 'native_qualified_containment')
    return graph


def _closure(graph, root):
    queue = deque([root])
    order, reasons = [], {root: ['selected']}
    while queue:
        current = queue.popleft()
        order.append(current)
        for target in sorted(graph[current]):
            if target not in reasons:
                reasons[target] = [f'{current}:{reason}' for reason in sorted(graph[current][target])]
                queue.append(target)
    return order, reasons


def _relevant_native_gap(gap, component, index):
    if set(gap['ids']) & component:
        return True
    hint = gap.get('scope_hint', {})
    if not hint.get('conservative_same_context'):
        return False
    owner, source = hint.get('owner'), hint.get('source')
    for identity in component:
        row = index[identity]['record']
        if owner and owner in (row.get('qualified_name'), row.get('owner')):
            return True
        if source and source == row.get('source'):
            return True
    return not owner and not source


def _workflow_view(record, native, evidence, workflow, identities):
    # The existing adapter admits at most 64 explicitly selected IDs. Multiple
    # bounded calls preserve its validation/completeness logic for larger views.
    reports = [analyze(record, native, evidence, workflow=workflow,
                       ids=identities[start:start + 64])
               for start in range(0, len(identities), 64)]
    if not reports:
        reports = [analyze(record, native, evidence, workflow=workflow, ids=[])]
    if len(reports) == 1:
        return reports[0]
    merged = deepcopy(reports[0])
    merged['status'] = _status(report['status'] for report in reports)
    merged['findings'] = [finding for report in reports for finding in report['findings']]
    merged['selected_ids'] = sorted({identity for report in reports for identity in report['selected_ids']})
    merged['checks'] = [check for report in reports for check in report['checks']]
    for report in reports[1:]:
        for field in ('elements', 'relations', 'decisions', 'questions', 'evidence', 'trade_studies', 'closure_reasons'):
            merged['view'].setdefault(field, {}).update(deepcopy(report['view'].get(field, {})))
    merged['context_check_batches'] = len(reports)
    return merged


def assemble_context(native, *, profile=None, short_id=None, element_id=None,
                     native_name=None, workflow='concept', limit=32,
                     source_evidence=None):
    """Pure assembly from a trusted parser result; synthetic inventories are tests.

    External callers use ``assembled_context``. No CLI accepts a saved inventory
    or saved successful checker result as an authoritative input.
    """
    report = _base()
    report['status'] = 'pass'
    evidence = {} if source_evidence is None else source_evidence
    try:
        if type(limit) is not int or not 1 <= limit <= MAX_ELEMENTS:
            raise Invalid('Context limit must be an integer from 1 through 512')
        if workflow not in JOBS:
            raise Invalid('Unknown selected workflow')
        if type(evidence) is not dict:
            raise Invalid('Source evidence needs an explicit ID map')
        report['limits']['selected_elements'] = limit
        if native.get('status') != 'pass':
            report.update(status=native.get('status', 'error'), retrieval_status=native.get('status', 'error'))
            report['findings'] = deepcopy(native.get('findings', []))
            report['parser_issues'] = deepcopy(native.get('parser_issues', []))
            return _bounded(report)
        report['retrieval_status'] = 'pass'
        report['parser_issues'] = deepcopy(native.get('parser_issues', []))
        inventory = native['inventory']
        report['provenance'].update(model_sha256=native.get('model_sha256'),
                                    model_files=deepcopy(native.get('model_files', [])),
                                    native_parser=native.get('parser'))
        record, owner = _workflow_record(native)
        if profile is not None:
            checked = check_profile(profile, native)
            report['profile_check'] = deepcopy(checked)
            report['profile_check']['selected'] = True
            report['provenance']['profile_sha256'] = checked.get('profile_sha256')
            report['status'] = _status([report['status'], checked['status']])
            report['findings'].extend(deepcopy(checked['findings']))
            if 'english' in profile and len(native.get('model_files', [])) > 1:
                _issue(report, 'english_bundle', 'unsupported', [],
                       'Selected English profiles over native file bundles are unsupported by the current contract.')
                return _bounded(report)
            if checked['status'] in ('error', 'fail', 'unsupported'):
                return _bounded(report)
        bindings = _bindings(profile, record)
        index = _native_index(inventory)
        root = _select(index, bindings, short_id=short_id, element_id=element_id, native_name=native_name)
        graph = _graph(index, bindings, profile, record, workflow=workflow)
        native_gaps = add_native_references(index, graph,
                                            connections=inventory.get('connections', []))
        ordered, reasons = _closure(graph, root)
        component = set(ordered)
        for gap in native_gaps:
            if _relevant_native_gap(gap, component, index):
                report['coverage']['unresolved'].append(deepcopy(gap))
                _issue(report, gap['rule'], gap['status'], gap['ids'], gap['detail'])
        selected = set(ordered[:limit])
        all_ids = {key: [] for key in index}
        for origin in ('foundation', 'workflow'):
            for identity, item in sorted(bindings[origin].items()):
                key = _key(item['native_category'], item['native_name'])
                all_ids.setdefault(key, []).append(origin + ':' + identity)
                if key in selected:
                    report['elements'][origin][identity] = deepcopy(item)
        report['selection'] = {'short_id': short_id, 'element_id': element_id,
                               'native_name': native_name, 'root': root,
                               'foundation_ids': sorted(identity for identity, item in bindings['foundation'].items()
                                                        if _key(item['native_category'], item['native_name']) == root),
                               'workflow_ids': sorted(identity for identity, item in bindings['workflow'].items()
                                                      if _key(item['native_category'], item['native_name']) == root)}
        if profile is not None:
            selected_ids = set(report['elements']['foundation'])
            term_ids = {item['term'] for item in report['elements']['foundation'].values()}
            report['concepts'] = {identity: {**deepcopy(profile['terms'][identity]),
                                             'term_digest': term_digest(profile['terms'][identity]),
                                             'origin': 'foundation_profile'}
                                  for identity in sorted(term_ids)}
            report['relations']['foundation'] = [{**deepcopy(relation), 'origin': 'foundation_profile',
                                                   'directed': True if relation['kind'] in RELATIONS else None}
                                                 for relation in profile['relations']
                                                 if {relation['from'], relation['to']} <= selected_ids]
            report['allocations'] = {identity: deepcopy(item) for identity, item in sorted(profile['allocations'].items())
                                      if set(item['functions'] + item['resources']) & selected_ids}
            report['use_cases'] = {identity: deepcopy(item) for identity, item in sorted(profile['use_cases'].items())
                                    if identity in selected_ids}
            report['capabilities'] = {identity: {**deepcopy(item),
                                                  'executor_admission': deepcopy(report['profile_check']['capabilities'].get(identity)),
                                                  'claim_scope': 'declared_executor_availability_not_system_ability'}
                                      for identity, item in sorted(profile['capabilities'].items())
                                      if item['element'] in selected_ids}
            english = profile.get('english', {})
            report['english_context'] = {'selected': bool(english),
                                          'revision': english.get('revision'),
                                          'status': report['profile_check'].get('english', {}).get('status', 'not_run'),
                                          'views': {identity: deepcopy(item) for identity, item in sorted(english.get('views', {}).items())
                                                    if item['element'] in selected_ids}}
        root_terms = [item for item in report['elements']['foundation'].values()
                      if _key(item['native_category'], item['native_name']) == root]
        if not root_terms:
            unresolved = {'rule': 'selected_definition', 'ids': all_ids.get(root, [root]),
                          'detail': 'No selected foundation definition binds this native identity; meaning remains unresolved.'}
            report['coverage']['unresolved'].append(unresolved)
            _issue(report, unresolved['rule'], 'unknown', unresolved['ids'], unresolved['detail'])
        if record is not None:
            workflow_ids = sorted(report['elements']['workflow'])
            checked = _workflow_view(record, native, evidence, workflow, workflow_ids)
            report['workflow_check'] = {key: deepcopy(value) for key, value in checked.items()
                                       if key not in ('record', 'bindings', 'native_inventory', 'view', 'sources')}
            report['workflow_check']['selected'] = True
            report['workflow_context'] = deepcopy(checked.get('view', {}))
            view = report['workflow_context']
            if view:
                view['elements'] = {identity: item for identity, item in view['elements'].items()
                                    if identity in workflow_ids}
                view['relations'] = {identity: item for identity, item in view['relations'].items()
                                     if {item['from'], item['to']} <= set(workflow_ids)}
                for item in view['relations'].values():
                    item['directed'] = (item['kind'] != 'interfaces_with'
                                        if item['kind'] in WORKFLOW_RELATIONS else None)
                view['evidence'] = {identity: item for identity, item in view['evidence'].items()
                                   if item['target'] in workflow_ids}
                for field in ('decisions', 'questions'):
                    view[field] = {identity: item for identity, item in view[field].items()
                                   if not item['affects'] or set(item['affects']) & set(workflow_ids)}
                view['boundary_ids'] = sorted(set(workflow_ids) - set(report['selection']['workflow_ids']))
                view['omitted_ids'] = sorted(set(record['elements']) - set(workflow_ids))
                view['closure_reasons'] = {identity: item for identity, item in view['closure_reasons'].items()
                                           if identity in workflow_ids}
                focus = record['workflows'].get(workflow, {}).get('focus', [])
                focus_native = {_key(bindings['workflow'][identity]['native_category'],
                                     bindings['workflow'][identity]['native_name'])
                                for identity in focus if identity in bindings['workflow']}
                if not focus_native.intersection(ordered):
                    # An unrelated workflow can share a label with this concept.
                    # Its conditions/question must not become governing intent.
                    view['workflow'] = None
                    view['question'] = None
                    view['workflow_applicability'] = {'status': 'unknown', 'focus_ids': focus,
                                                       'reason': 'Workflow focus is disjoint from the selected explicit dependency component.'}
                    unresolved = {'rule': 'workflow_applicability', 'ids': focus,
                                  'detail': 'Selected workflow conditions are not established for this component; unrelated conditions were excluded.'}
                    report['coverage']['unresolved'].append(unresolved)
                    _issue(report, unresolved['rule'], 'unknown', unresolved['ids'], unresolved['detail'])
                else:
                    view['workflow_applicability'] = {'status': 'pass', 'focus_ids': focus,
                                                       'claim_scope': 'explicit_dependency_component_relevance_not_semantic_proof'}
            report['provenance'].update(workflow_record_sha256=checked.get('record_sha256'), document_owner=owner)
            report['findings'].extend(deepcopy(checked.get('findings', [])))
            report['status'] = _status([report['status'], checked['status']])
            report['relations']['workflow'] = {identity: {**deepcopy(item),
                                                            'origin': 'declared_workflow_document',
                                                            'directed': (item['kind'] != 'interfaces_with'
                                                                         if item['kind'] in WORKFLOW_RELATIONS else None)}
                                                for identity, item in record['relations'].items()
                                                if {item['from'], item['to']} <= set(workflow_ids)}
        elif evidence:
            raise Invalid('Sources were supplied without a declared workflow source map')
        native_records = {group: [deepcopy(index[key]['record']) for key in ordered[:limit]
                                   if index[key]['category'] == group] for group in GROUPS}
        owners = {index[key]['record']['qualified_name'] for key in selected}
        native_records['documents'] = [deepcopy(item) for item in inventory.get('documents', [])
                                        if ((item.get('owner') in owners and item.get('name') != 'cseWorkflow')
                                            or item.get('name') == 'cseClock')]
        native_records['event_attributes'] = [deepcopy(item) for item in inventory.get('event_attributes', [])
                                               if item.get('event') in owners]
        native_records['connection_semantics'] = {'directed': False,
                                                   'claim_scope': 'parsed_native_adjacency_not_item_or_control_flow'}
        report['native_context'] = native_records
        omitted = [identity for key in ordered[limit:] for identity in (all_ids.get(key) or [key])]
        report['coverage'].update(complete=not omitted and not report['coverage']['unresolved'],
                                   total_elements=len(ordered), returned_elements=len(selected),
                                   omitted_ids=sorted(omitted),
                                   inclusion_reasons={key: reasons[key] for key in ordered[:limit]},
                                   unrelated_element_count=len(index) - len(ordered))
        if omitted:
            _issue(report, 'context_limit', 'unknown', sorted(omitted),
                   'Known explicit dependencies exceed the view limit; expand the view before assuming they are absent.')
        report['findings'].sort(key=lambda item: (item.get('rule', ''), item.get('ids', []), item.get('detail', '')))
    except (OSError, ValueError, TypeError, KeyError, RecursionError, RuntimeError) as exc:
        _issue(report, 'context_input', 'error', [], str(exc))
        report['coverage']['complete'] = False
        report['retrieval_status'] = 'error'
        for field in ('concepts', 'allocations', 'use_cases', 'capabilities', 'english_context',
                      'native_context', 'workflow_context'):
            report[field] = {}
        report['elements'] = {'foundation': {}, 'workflow': {}}
        report['relations'] = {'foundation': [], 'workflow': {}}
    return _bounded(report)


def assembled_context(paths, *, short_id=None, element_id=None, native_name=None,
                      profile_path=None, workflow='concept', limit=32, sources=None):
    """Read actual bounded files, parse once, join records and check freshness."""
    report = _base()
    try:
        captured, files, model_digest = capture_model_inputs(paths)
        profile, profile_bytes = None, None
        if profile_path is not None:
            profile_bytes = read_regular(profile_path, 1_000_000)
            profile, profile_digest = load_profile(profile_path)
            if sha256(profile_bytes).hexdigest() != profile_digest:
                raise Invalid('Profile changed while reading')
        native = parse_captured(captured, files, model_digest, parser=check_sysml)
        if native.get('model_sha256') != model_digest:
            raise Invalid('Parsed native model revision differs from captured inputs')
        record, owner = _workflow_record(native) if native.get('status') == 'pass' else (None, None)
        sources = {} if sources is None else sources
        if native.get('status') == 'pass' and (type(sources) is not dict or
                (sources and (record is None or set(sources) - set(record['sources'])))):
            raise Invalid('Only explicitly declared workflow source IDs may be supplied')
        source_bytes, evidence = {}, {}
        for identity, path in sorted(sources.items()) if native.get('status') == 'pass' else []:
            raw = read_regular(path, 1_000_000)
            text = raw.decode('utf-8')
            source_bytes[identity] = raw
            expected = record['sources'][identity]
            actual = sha256(raw).hexdigest()
            status, detail = 'pass', 'Supplied bytes and unique excerpt match; interpretation is not established'
            if actual != expected['sha256']:
                status, detail = 'fail', 'Supplied source revision is stale'
            elif text.count(expected['excerpt']) != 1:
                status, detail = 'fail', 'Source excerpt must occur exactly once'
            evidence[identity] = {'path': str(path), 'status': status, 'detail': detail,
                                   'kind': expected['kind'], 'actual_sha256': actual,
                                   'expected_sha256': expected['sha256']}
        report = assemble_context(native, profile=profile, short_id=short_id,
                                  element_id=element_id, native_name=native_name,
                                  workflow=workflow, limit=limit, source_evidence=evidence)
        report['provenance'].update(model_files=files, model_sha256=model_digest,
                                    profile_file_sha256=sha256(profile_bytes).hexdigest() if profile_bytes is not None else None,
                                    sources=deepcopy(evidence))
        changed = any(read_regular(path, 5_000_000) != raw for path, raw in captured)
        changed = changed or (profile_path is not None and read_regular(profile_path, 1_000_000) != profile_bytes)
        changed = changed or any(read_regular(sources[identity], 1_000_000) != raw
                                 for identity, raw in source_bytes.items())
        if changed:
            raise Invalid('Model, profile or source bytes changed during context assembly')
        report['provenance']['input_stability'] = 'pass'
    except (OSError, ValueError, TypeError, KeyError, RecursionError, RuntimeError) as exc:
        # Never expose a previously successful assembled view after input drift.
        previous = report.get('provenance', {})
        report = _base()
        report['provenance'] = previous
        report['provenance']['input_stability'] = 'error'
        report['status'] = report['retrieval_status'] = 'error'
        _issue(report, 'context_input', 'error', [], str(exc))
    return _bounded(report)
