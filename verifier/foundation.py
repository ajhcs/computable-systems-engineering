"""Bounded, explicit engineering semantics bound to a parsed SysML revision.

This profile validates declarations; it does not infer source meaning, execute
native behavior, authenticate decisions, or establish requirement satisfaction.
"""
from hashlib import sha256
import json
import os
import stat
from pathlib import Path
import re

from .core import _pairs
from .sysml import check_sysml

VERSION = 'foundation-1.0'
MAX_BYTES = 1_000_000
MAX_ITEMS = 512
ID = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,63}\Z')
KINDS = {'subject', 'actor', 'function', 'resource', 'use_case', 'scenario',
         'behavior', 'capability', 'objective'}
NATIVE = {'subject': 'parts', 'actor': 'parts', 'resource': 'parts',
          'capability': 'parts', 'function': 'actions', 'behavior': 'actions',
          'scenario': 'actions', 'use_case': 'use_cases', 'objective': 'concerns'}
RELATIONS = {'supports': ({'resource'}, {'function'}),
             'motivates': ({'objective'}, {'function', 'use_case'}),
             'scenario_of': ({'scenario'}, {'use_case'}),
             'implements': ({'capability'}, {'function'}),
             'decomposes': ({'function', 'resource'}, {'function', 'resource'})}
EXECUTORS = {'foundation.check': {'input': VERSION, 'claim': 'declared_structure_and_allocation'},
             'foundation.next': {'input': VERSION, 'claim': 'next_missing_declared_fact'}}


class Invalid(ValueError):
    pass


def read_regular(path, cap):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > cap:
            raise Invalid('Input must be a regular file within its byte cap')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(cap + 1)
        if len(raw) > cap:
            raise Invalid('Input exceeds byte cap')
        return raw
    finally:
        os.close(fd)


def load_profile(path):
    raw = read_regular(path, MAX_BYTES)
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                           parse_constant=lambda x: (_ for _ in ()).throw(Invalid('Nonfinite number')))
    except (UnicodeError, RecursionError) as exc:
        raise Invalid('Invalid UTF-8 or excessive JSON nesting') from exc
    return value, sha256(raw).hexdigest()


def _object(value, keys, where, required=None):
    if type(value) is not dict:
        raise Invalid(f'{where} must be an object')
    if set(value) - set(keys):
        raise Invalid(f'{where} has unsupported fields: {sorted(set(value)-set(keys))}')
    missing = set(keys if required is None else required) - set(value)
    if missing:
        raise Invalid(f'{where} lacks fields: {sorted(missing)}')


def _text(value, where):
    if type(value) is not str or not value.strip() or len(value) > 4096:
        raise Invalid(f'{where} needs nonempty text of at most 4096 characters')


def _map(value, where):
    if type(value) is not dict or len(value) > MAX_ITEMS:
        raise Invalid(f'{where} needs a bounded ID map')
    for key in value:
        if not ID.fullmatch(key):
            raise Invalid(f'{where} has invalid ID {key!r}')


def _list(value, where):
    if type(value) is not list or len(value) > MAX_ITEMS:
        raise Invalid(f'{where} needs a bounded list')


def _bounds(value, where):
    _object(value, ('min', 'max'), where)
    if any(type(value[k]) is not int for k in ('min', 'max')) or not 0 <= value['min'] <= value['max'] <= MAX_ITEMS:
        raise Invalid(f'{where} needs integer bounds 0 <= min <= max <= {MAX_ITEMS}')


def _ids(value, where):
    _list(value, where)
    if any(type(x) is not str or not ID.fullmatch(x) for x in value) or len(value) != len(set(value)):
        raise Invalid(f'{where} needs unique valid IDs')


def _schema(profile):
    _object(profile, ('version', 'source_sha256', 'terms', 'elements', 'relations',
                      'use_cases', 'allocations', 'capabilities'), 'profile')
    if profile['version'] != VERSION:
        raise Invalid('Unsupported foundation profile version')
    if type(profile['source_sha256']) is not str or not re.fullmatch('[0-9a-f]{64}', profile['source_sha256']):
        raise Invalid('source_sha256 needs a lowercase SHA-256')
    for group in ('terms', 'elements', 'use_cases', 'allocations', 'capabilities'):
        _map(profile[group], group)
    for key, term in profile['terms'].items():
        _object(term, ('namespace', 'revision', 'label', 'definition', 'kind'), key)
        for field in ('namespace', 'revision', 'label', 'definition'):
            _text(term[field], f'{key}.{field}')
        if term['kind'] not in KINDS:
            raise Invalid(f'{key} unsupported term kind')
    for key, element in profile['elements'].items():
        _object(element, ('kind', 'term', 'native_name'), key)
        if type(element['kind']) is not str or element['kind'] not in KINDS:
            raise Invalid(f'{key} unsupported element kind')
        _text(element['term'], f'{key}.term')
        _text(element['native_name'], f'{key}.native_name')
    _list(profile['relations'], 'relations')
    for relation in profile['relations']:
        _object(relation, ('kind', 'from', 'to'), 'relation')
        for field in ('kind', 'from', 'to'):
            _text(relation[field], f'relation.{field}')
    for key, case in profile['use_cases'].items():
        _object(case, ('category', 'subject', 'goal', 'actors', 'scenarios'), key)
        if case['category'] not in ('base', 'included', 'extension'):
            raise Invalid(f'{key} unsupported use-case category')
        if case['subject'] is not None:
            _text(case['subject'], f'{key}.subject')
        if case['goal'] is not None:
            _text(case['goal'], f'{key}.goal')
        _map(case['actors'], f'{key}.actors')
        _ids(case['scenarios'], f'{key}.scenarios')
        for actor, role in case['actors'].items():
            _object(role, ('role', 'invokes', 'instances', 'bounds', 'boundary'), f'{key}.{actor}')
            if role['boundary'] not in ('internal', 'external', 'unknown'):
                raise Invalid('Unsupported actor boundary role')
            if role['role'] not in ('primary', 'secondary', 'unknown'):
                raise Invalid('Unsupported actor role')
            if role['invokes'] is not None and type(role['invokes']) is not bool:
                raise Invalid('invokes needs boolean or null')
            if role['instances'] is not None and (type(role['instances']) is not int or not 0 <= role['instances'] <= MAX_ITEMS):
                raise Invalid('instances needs bounded integer or null')
            _bounds(role['bounds'], f'{key}.{actor}.bounds')
    for key, allocation in profile['allocations'].items():
        _object(allocation, ('functions', 'resources', 'pairs', 'function_bounds', 'resource_bounds'), key)
        for name in ('functions', 'resources'):
            _ids(allocation[name], f'{key}.{name}')
        for name in ('function_bounds', 'resource_bounds'):
            _map(allocation[name], f'{key}.{name}')
            for element, bounds in allocation[name].items():
                _bounds(bounds, f'{key}.{element}')
        _list(allocation['pairs'], f'{key}.pairs')
        for pair in allocation['pairs']:
            _object(pair, ('function', 'resource', 'rationale'), f'{key}.pair')
            for field in pair:
                _text(pair[field], f'{key}.pair.{field}')
    for key, capability in profile['capabilities'].items():
        _object(capability, ('element', 'state', 'executor', 'input_contract', 'reason'), key)
        _text(capability['element'], f'{key}.element')
        if capability['state'] not in ('available', 'unavailable', 'proposed'):
            raise Invalid('Unsupported capability state')
        for field in ('executor', 'input_contract'):
            if capability[field] is not None:
                _text(capability[field], f'{key}.{field}')
        _text(capability['reason'], f'{key}.reason')


def check_profile(profile, native):
    """Pure check against actual parser inventory; synthetic inventories are unit tests only."""
    report = {'checker_version': VERSION, 'status': 'pass', 'claim_scope': 'declared_source_bound_engineering_profile',
              'required_review': 'not_evaluated', 'acceptance': 'not_evaluated',
              'behavior': 'not_run', 'requirement_satisfaction': 'not_run', 'findings': [],
              'capabilities': {}, 'limits': {'items_per_group': MAX_ITEMS, 'profile_bytes': MAX_BYTES}}
    def issue(rule, status, ids, detail):
        report['findings'].append({'rule': rule, 'status': status, 'ids': ids, 'detail': detail})
    try:
        _schema(profile)
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        issue('schema', 'error', [], str(exc))
        report['status'] = 'error'
        return report
    report['profile_sha256'] = sha256(json.dumps(profile, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    report['source_sha256'] = profile['source_sha256']
    if native.get('status') != 'pass':
        issue('native_parse', native.get('status', 'error'), [], 'Native parse/linking did not pass')
    elif native.get('model_sha256') != profile['source_sha256']:
        issue('source_revision', 'fail', [], 'Profile source revision is stale')
    inventory = native.get('inventory', {})
    elements = profile['elements']
    terms = profile['terms']
    if not elements:
        issue('scope_empty', 'unknown', [], 'Select a nonempty engineering element scope')
    def ref(key, kind, where):
        if key not in elements or elements[key]['kind'] not in kind:
            issue('typed_reference', 'fail', [where, key], f'Expected element kind {sorted(kind)}')
            return False
        return True
    # Term labels can coincide across scopes; definitions are never silently equated.
    term_scope = set()
    for key, term in terms.items():
        scope = (term['namespace'], term['revision'], term['label'])
        if scope in term_scope:
            issue('term_scope', 'fail', [key], 'Duplicate label in the same namespace/revision')
        term_scope.add(scope)
    for key, element in elements.items():
        term = terms.get(element['term'])
        if term is None or term['kind'] != element['kind']:
            issue('term_binding', 'fail', [key, element['term']], 'Missing or wrong-kind scoped definition')
        matches = [x for x in inventory.get(NATIVE[element['kind']], [])
                   if x.get('qualified_name') == element['native_name']]
        if len(matches) != 1:
            issue('native_binding', 'fail', [key], 'Expected one parsed native element of the admitted category')
    edges = set()
    parent_graph = {}
    for relation in profile['relations']:
        edge = (relation['kind'], relation['from'], relation['to'])
        if edge in edges:
            issue('relation_duplicate', 'fail', [relation['from'], relation['to']], 'Duplicate typed relation')
        edges.add(edge)
        contract = RELATIONS.get(relation['kind'])
        if contract is None:
            issue('relation_supported', 'unsupported', [relation['from'], relation['to']], 'No admitted relation semantics')
            continue
        a, b = relation['from'], relation['to']
        okay = ref(a, contract[0], 'relation') & ref(b, contract[1], 'relation')
        if okay and relation['kind'] == 'decomposes':
            if elements[a]['kind'] != elements[b]['kind']:
                issue('decomposition_kind', 'fail', [a, b], 'Decomposition preserves function/resource kind')
            parent_graph.setdefault(a, []).append(b)
    # Bounded iterative traversal avoids recursion and rejects hierarchy cycles.
    for start in parent_graph:
        stack = list(parent_graph[start]); visited = set()
        while stack:
            node = stack.pop()
            if node == start:
                issue('hierarchy_cycle', 'fail', [start], 'Decomposition contains a cycle'); break
            if node not in visited:
                visited.add(node); stack.extend(parent_graph.get(node, []))
    for key, case in profile['use_cases'].items():
        valid_case = ref(key, {'use_case'}, key)
        if case['category'] != 'base':
            issue('use_case_semantics', 'unsupported', [key], 'Include/extend execution semantics are outside this profile')
        if case['subject'] is None:
            issue('subject_missing', 'unknown', [key], 'Identify the system subject')
        else:
            ref(case['subject'], {'subject'}, key)
        if case['goal'] is None:
            issue('goal_missing', 'unknown', [key], 'Elicit the actor goal; do not invent it')
        if not case['scenarios']:
            issue('scenario_missing', 'unknown', [key], 'Declare a scenario for the requested use case')
        for scenario in case['scenarios']:
            ref(scenario, {'scenario'}, key)
            if ('scenario_of', scenario, key) not in edges:
                issue('scenario_trace', 'fail', [scenario, key], 'Declared scenario needs its typed scenario_of relation')
        primary = 0
        actor_identities = {}
        for actor, role in case['actors'].items():
            ref(actor, {'actor'}, key)
            actor_name = elements.get(actor, {}).get('native_name')
            if actor_name in actor_identities:
                issue('actor_identity', 'fail', [key, actor_identities[actor_name], actor],
                      'Each native participant has one actor identity within a use-case contract')
            else:
                actor_identities[actor_name] = actor
            subject_name = elements.get(case['subject'], {}).get('native_name')
            if role['boundary'] == 'unknown' or subject_name is None:
                issue('boundary_unknown', 'unknown', [key, actor], 'Declare actor location against this subject boundary')
            elif actor_name:
                internal = actor_name == subject_name or actor_name.startswith(subject_name + '::')
                if (role['boundary'] == 'internal') != internal:
                    issue('actor_boundary', 'fail', [key, actor], 'Declared actor location differs from parsed subject containment')
            if role['role'] == 'unknown' or role['invokes'] is None:
                issue('role_unknown', 'unknown', [key, actor], 'Elicit invocation/role facts in this use case')
            elif (role['role'] == 'primary') != role['invokes']:
                issue('role_invocation', 'fail', [key, actor], 'Primary invokes; secondary participates without invocation under this profile')
            primary += role['role'] == 'primary'
            if role['instances'] is None:
                issue('instances_unknown', 'unknown', [key, actor], 'Supply declared participant instance count')
            elif not role['bounds']['min'] <= role['instances'] <= role['bounds']['max']:
                issue('multiplicity', 'fail', [key, actor], 'Declared participant count violates selected bounds')
        if case['category'] == 'base' and not primary:
            issue('primary_missing', 'unknown', [key], 'Identify a primary actor for this base use case')
        if valid_case:
            matches = [x for x in inventory.get('use_cases', []) if x.get('qualified_name') == elements[key]['native_name']]
            if len(matches) == 1:
                parsed = matches[0]
                target = elements.get(case['subject'], {}).get('native_name')
                subjects = [x.get('target') for x in parsed.get('subjects', [])]
                if target is not None and subjects != [target]:
                    issue('native_subject', 'fail', [key], 'Declared subject differs from parsed subject binding')
                targets = [elements.get(a, {}).get('native_name') for a in case['actors']]
                native_actors = [x.get('target') for x in parsed.get('actors', [])]
                if (len(native_actors) != len(set(native_actors)) or
                        len(targets) != len(set(targets)) or
                        len(native_actors) != len(targets) or set(native_actors) != set(targets)):
                    issue('native_actors', 'fail', [key], 'Declared actors differ from parsed actor bindings')
    # Omitting a profile use case cannot silently remove a declared profile obligation.
    declared_cases = {k for k,e in elements.items() if e['kind'] == 'use_case'}
    if set(profile['use_cases']) != declared_cases:
        issue('use_case_coverage', 'fail', sorted(declared_cases ^ set(profile['use_cases'])), 'Every declared use-case element needs exactly one contract')
    for key, allocation in profile['allocations'].items():
        functions, resources = allocation['functions'], allocation['resources']
        for e in functions: ref(e, {'function'}, key)
        for e in resources: ref(e, {'resource'}, key)
        for group in (functions, resources):
            identities = [elements.get(e, {}).get('native_name') for e in group]
            if len(identities) != len(set(identities)):
                issue('allocation_identity', 'fail', [key], 'An alternative cannot count one native function/resource more than once through aliases')
        if set(allocation['function_bounds']) != set(functions) or set(allocation['resource_bounds']) != set(resources):
            issue('allocation_scope', 'fail', [key], 'Bounds must cover exactly the declared function/resource scope')
        pairs = set()
        for pair in allocation['pairs']:
            a, b = pair['function'], pair['resource']
            if a not in functions or b not in resources or (a,b) in pairs:
                issue('allocation_pair', 'fail', [key,a,b], 'Pair outside scope or duplicated')
            pairs.add((a,b))
        for group, position, bounds in ((functions,0,allocation['function_bounds']), (resources,1,allocation['resource_bounds'])):
            for e in group:
                count = sum(pair[position] == e for pair in pairs)
                if e in bounds and not bounds[e]['min'] <= count <= bounds[e]['max']:
                    issue('allocation_cardinality', 'fail', [key,e], f'Allocation count {count} violates selected bounds')
    for key, capability in profile['capabilities'].items():
        ref(capability['element'], {'capability'}, key)
        executor = EXECUTORS.get(capability['executor'])
        available = capability['state'] == 'available'
        if available and (executor is None or capability['input_contract'] != executor['input']):
            issue('capability_admission', 'unsupported', [key], 'Available claim lacks a trusted executor/input contract')
        report['capabilities'][key] = {'available': available and executor is not None and capability['input_contract'] == executor['input'],
                                     'executor': capability['executor'], 'reason': capability['reason']}
    severity = {'pass':0,'unknown':1,'unsupported':2,'fail':3,'error':4}
    report['findings'].sort(key=lambda x:(x['rule'], str(x['ids']), x['detail']))
    report['status'] = max((x['status'] for x in report['findings']), default='pass', key=lambda x:severity.get(x,4))
    return report


def inspect(profile_path, model_path):
    profile, raw_digest = load_profile(profile_path)
    model_path = Path(model_path)
    before = sha256(read_regular(model_path, 5_000_000)).hexdigest()
    native = check_sysml(model_path, syntax_only=True)
    report = check_profile(profile, native)
    if (sha256(read_regular(model_path, 5_000_000)).hexdigest() != before or
            native.get('model_sha256') != before or
            sha256(read_regular(profile_path, MAX_BYTES)).hexdigest() != raw_digest):
        report['status'] = 'error'
        report['findings'].append({'rule':'source_changed','status':'error','ids':[], 'detail':'Source/profile changed during check or parser digest mismatched'})
    report['profile_file_sha256'] = raw_digest
    report['native_parser'] = native.get('parser')
    report['native_status'] = native.get('status')
    return profile, report


def execute(profile_path, model_path, capability_id):
    profile, report = inspect(profile_path, model_path)
    # Refusal precedes invocation; catalog data cannot provide executable commands.
    capability = report['capabilities'].get(capability_id)
    if report['status'] == 'error':
        return report
    if not capability or not capability['available']:
        report['status'] = 'unsupported'
        report['findings'].append({'rule':'capability_unavailable','status':'unsupported','ids':[capability_id],
                                  'detail':'Selected capability has no admitted executable adapter'})
        return report
    if capability['executor'] == 'foundation.next':
        # Diagnostic elicitation preserves incomplete/failed status and invents no facts.
        return next_question(report)
    return report


def next_question(report):
    unresolved = [x for x in report['findings'] if x['status'] in ('unknown','fail','unsupported','error')]
    return {'status':report['status'], 'claim_scope':'next_missing_declared_fact',
            'profile_file_sha256':report.get('profile_file_sha256'),
            'source_sha256':report.get('source_sha256'), 'acceptance':'not_evaluated',
            'next':unresolved[0] if unresolved else None,
            'message':'Resolve this declared fact; preserve meaning and ask the engineer when consequential.' if unresolved else
                      'No structural gap found in this profile. Engineering suitability and acceptance remain unevaluated.'}
