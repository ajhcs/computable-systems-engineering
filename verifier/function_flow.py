"""Explicit function contracts and bounded finite-model correspondence.

Flow topology is documentary. Execution uses the existing finite verifier; no
native SysML or transformation text is interpreted as executable behavior.
"""
from .core import digest, verify, ID, _predicate
from .foundation import Invalid, _object

VERSION = 'function-flow-1.0'
OBLIGATIONS = ('binding', 'functions', 'flows', 'decomposition', 'scenarios')


def _ids(value, where):
    if (type(value) is not list or len(value) > 128 or
            any(type(x) is not str or not ID.fullmatch(x) for x in value) or len(set(value)) != len(value)):
        raise Invalid(where + ' needs at most 128 distinct IDs')


def _map(value, where, cap=128):
    if type(value) is not dict or len(value) > cap or any(type(x) is not str or not ID.fullmatch(x) for x in value):
        raise Invalid(where + ' needs a bounded ID map')


def _text(value, where, nullable=False):
    if nullable and value is None:
        return
    if type(value) is not str or not value.strip() or len(value) > 4096:
        raise Invalid(where + ' needs bounded nonempty text')


def schema(record):
    _object(record, ('version', 'finite_model', 'finite_model_sha256', 'functions', 'flows',
                     'step_bindings', 'decompositions', 'policy', 'limits'), 'function-flow record')
    if record['version'] != VERSION:
        raise Invalid('Unsupported function-flow version')
    if type(record['finite_model']) is not dict:
        raise Invalid('finite_model must be an explicit finite verifier record')
    if (type(record['finite_model_sha256']) is not str or len(record['finite_model_sha256']) != 64 or
            any(c not in '0123456789abcdef' for c in record['finite_model_sha256'])):
        raise Invalid('finite_model_sha256 needs a SHA-256')
    for name in ('functions', 'flows', 'step_bindings', 'decompositions'):
        _map(record[name], name)
    _object(record['policy'], ('accountable', 'performers_required'), 'policy')
    if record['policy']['accountable'] not in ('exactly_one', 'at_least_one', 'not_selected'):
        raise Invalid('Select an explicit accountable-owner policy')
    if type(record['policy']['performers_required']) is not bool:
        raise Invalid('performers_required must be Boolean')
    _object(record['limits'], ('state_cap', 'assignment_cap'), 'limits')
    if any(type(v) is not int or not 1 <= v <= 100000 for v in record['limits'].values()):
        raise Invalid('Analysis caps must be integers in 1..100000')
    for key, function in record['functions'].items():
        _object(function, ('label', 'transformation', 'inputs', 'outputs', 'enabling', 'performers', 'accountable'), key)
        _text(function['label'], key + '.label')
        _text(function['transformation'], key + '.transformation', nullable=True)
        if function['enabling'] is not None and type(function['enabling']) is not dict:
            raise Invalid('Enabling condition must be an explicit finite predicate or null (unconditional)')
        for role in ('performers', 'accountable'):
            _ids(function[role], key + '.' + role)
        for direction in ('inputs', 'outputs'):
            _map(function[direction], key + '.' + direction)
            for port, spec in function[direction].items():
                _object(spec, ('data', 'type', 'unit'), key + '.' + port)
                _ids([spec['data']], key + '.' + port + '.data')
                if type(spec['type']) is not str or len(spec['type']) > 64:
                    raise Invalid('Port type must be bounded text')
                if spec['unit'] is not None and (type(spec['unit']) is not str or len(spec['unit']) > 128):
                    raise Invalid('Port unit must be bounded text or null')
    for key, flow in record['flows'].items():
        _object(flow, ('from', 'output', 'to', 'input'), key)
        for field in flow:
            _ids([flow[field]], key + '.' + field)
    for scenario, bindings in record['step_bindings'].items():
        _map(bindings, scenario)
        for value in bindings.values():
            _ids([value], scenario + ' function reference')
    for key, decomposition in record['decompositions'].items():
        _object(decomposition, ('parent', 'children', 'inputs', 'outputs'), key)
        _ids([decomposition['parent']], key + '.parent')
        _ids(decomposition['children'], key + '.children')
        for direction in ('inputs', 'outputs'):
            mappings = decomposition[direction]
            if type(mappings) is not list or len(mappings) > 128:
                raise Invalid('Boundary mappings must be bounded lists')
            for mapping in mappings:
                _object(mapping, ('parent_port', 'child', 'child_port'), key)
                for value in mapping.values():
                    _ids([value], key + ' boundary endpoint')
            signatures = [(m['parent_port'], m['child'], m['child_port']) for m in mappings]
            if len(set(signatures)) != len(signatures):
                raise Invalid('Duplicate boundary mapping')
    return record


def _status(findings):
    states = {f['status'] for f in findings}
    return next((s for s in ('error', 'fail', 'unsupported', 'unknown', 'not_run') if s in states), 'pass')


def analyze(record):
    """Check all explicitly declared contracts; return deterministic diagnostics."""
    result = {'checker_version': VERSION, 'status': 'error', 'artifact_sha256': None,
              'dependencies': {}, 'scope': 'all_declared_functions_flows_and_finite_scenarios',
              'expected_obligations': list(OBLIGATIONS), 'completed_obligations': [],
              'findings': [], 'limits': {},
              'claim_scope': 'explicit_function_contract_and_finite_model_correspondence',
              'native_sysml_execution': 'unsupported', 'transformation_correctness': 'not_evaluated',
              'decision_authentication': 'not_evaluated'}

    def issue(obligation, rule, status, ids, detail, evidence=None):
        f = {'obligation': obligation, 'rule': rule, 'status': status, 'ids': list(ids), 'detail': detail}
        if evidence is not None:
            f['evidence'] = evidence
        result['findings'].append(f)

    try:
        result['artifact_sha256'] = digest(record)
        if type(record) is dict and record.get('version') != VERSION:
            issue('binding', 'function_profile', 'unsupported', [], 'Unsupported function-flow profile version.')
            return result
        schema(record)
        model = record['finite_model']
        model_hash = digest(model)
        result['dependencies']['finite_model_sha256'] = model_hash
        result['limits'] = dict(record['limits']) | {'map_items': 128, 'record_bytes': 1000000}
        import json
        if len(json.dumps(record, ensure_ascii=False).encode()) > 1000000:
            raise Invalid('Function-flow record exceeds 1 MB')
        if record['finite_model_sha256'] != model_hash:
            issue('binding', 'finite_revision', 'fail', [], 'The explicitly bound finite-model revision has changed.')
            issue('scenarios', 'finite_not_run', 'not_run', [], 'Reconcile the finite-model binding before execution.')
            return result
        finite = verify(model, review=False, **record['limits'])
        result['finite_analysis'] = {k: finite[k] for k in ('checker_version', 'artifact_sha256', 'status', 'obligations', 'limits')}
        for f in finite['findings']:
            issue('scenarios', 'finite.' + f['rule'], f['status'], f['ids'], f['explanation'], f.get('evidence'))
        # Malformed or unsupported finite declarations cannot supply endpoint types.
        if finite['obligations']['declarations'] != 'pass' or finite['obligations']['types'] != 'pass':
            issue('functions', 'finite_contract_unavailable', 'not_run', [], 'Function contracts need admitted finite declarations and types.')
            return result
        functions, flows = record['functions'], record['flows']
        actors, data = model.get('actors', {}), model.get('data', {})
        if not functions:
            issue('functions', 'function_scope_empty', 'unknown', [], 'No explicit function contract is selected.')
        if not model.get('scenarios'):
            issue('scenarios', 'scenario_scope_empty', 'unknown', [], 'No explicit finite scenario is supplied.')
        for key, function in sorted(functions.items()):
            if function['transformation'] is None:
                issue('functions', 'transformation_unknown', 'unknown', [key], 'Describe the proposed transformation; description presence does not prove correctness.')
            for role in ('performers', 'accountable'):
                for actor in function[role]:
                    if actor not in actors:
                        issue('functions', 'function_party', 'fail', [key, actor], 'Function party must identify a declared finite-model actor.')
            if record['policy']['performers_required'] and not function['performers']:
                issue('functions', 'performer_unknown', 'unknown', [key], 'The selected policy requires an identified performer.')
            count, policy = len(function['accountable']), record['policy']['accountable']
            if policy != 'not_selected' and count == 0:
                issue('functions', 'accountable_unknown', 'unknown', [key], 'The selected policy requires an identified accountable owner.')
            elif policy == 'exactly_one' and count != 1:
                issue('functions', 'accountable_cardinality', 'fail', [key], 'The project selected exactly one accountable owner; performers have no such restriction.')
            if function['enabling'] is not None:
                issues = []
                _predicate(function['enabling'], model.get('properties', {}), key, issues)
                for f in issues:
                    issue('functions', 'enabling.' + f['rule'], f['status'], f['ids'], f['explanation'])
            for direction in ('inputs', 'outputs'):
                for port, spec in sorted(function[direction].items()):
                    declaration = data.get(spec['data'])
                    if declaration is None:
                        issue('functions', 'port_data', 'fail', [key, port, spec['data']], 'Port data identity is absent from the bound finite model.')
                        continue
                    if spec['type'] not in ('bool', 'enum', 'int'):
                        issue('functions', 'port_type', 'unsupported', [key, port], 'Only existing finite bool/enum/int port types are supported.')
                    elif spec['type'] != declaration['type']:
                        issue('functions', 'port_type', 'fail', [key, port, spec['data']], 'Port type differs from the bound data declaration.')
                    if spec['unit'] != declaration.get('unit'):
                        issue('functions', 'port_unit', 'fail', [key, port, spec['data']], 'Port unit differs from the bound data declaration; no conversion is inferred.')

        def endpoint(function, direction, port, ids, obligation):
            if function not in functions or port not in functions[function][direction]:
                issue(obligation, 'port_endpoint', 'fail', ids, 'Endpoint must name a declared function port in the stated direction.')
                return None
            return functions[function][direction][port]

        for key, flow in sorted(flows.items()):
            left = endpoint(flow['from'], 'outputs', flow['output'], [key, flow['from'], flow['output']], 'flows')
            right = endpoint(flow['to'], 'inputs', flow['input'], [key, flow['to'], flow['input']], 'flows')
            if left is not None and right is not None and left != right:
                issue('flows', 'flow_contract', 'fail', [key, flow['from'], flow['to']], 'Connected ports must preserve data identity, type and unit; adapters need explicit authored functions.')
        result['topology'] = {'kind': 'directed_function_port_multigraph', 'nodes': sorted(functions),
                              'edges': len(flows), 'reachability_claim': 'not_execution_feasibility',
                              'feedback_cycles': 'permitted'}

        adjacency = {key: set() for key in functions}
        parents = set()
        for key, decomp in sorted(record['decompositions'].items()):
            parent, children = decomp['parent'], set(decomp['children'])
            if parent in parents:
                issue('decomposition', 'decomposition_duplicate_parent', 'fail', [key, parent], 'A parent needs one explicit decomposition contract; combine its selected children and mappings.')
            parents.add(parent)
            if parent not in functions or not children or children - functions.keys():
                issue('decomposition', 'decomposition_member', 'fail', [key, parent, *sorted(children)], 'Decomposition needs a declared parent and nonempty declared children.')
                continue
            adjacency[parent].update(children)
            for direction in ('inputs', 'outputs'):
                mapped_parent, mapped_child = set(), set()
                for mapping in decomp[direction]:
                    child, cp, pp = mapping['child'], mapping['child_port'], mapping['parent_port']
                    if child not in children:
                        issue('decomposition', 'boundary_child', 'fail', [key, child], 'Boundary mapping must name a direct child.')
                        continue
                    outer = endpoint(parent, direction, pp, [key, parent, pp], 'decomposition')
                    inner = endpoint(child, direction, cp, [key, child, cp], 'decomposition')
                    mapped_parent.add(pp); mapped_child.add((child, cp))
                    if outer is not None and inner is not None and outer != inner:
                        issue('decomposition', 'boundary_contract', 'fail', [key, parent, child, pp, cp], 'Parent and child boundary ports must preserve direction, data, type and unit.')
                for pp in sorted(set(functions[parent][direction]) - mapped_parent):
                    issue('decomposition', 'parent_boundary_missing', 'fail', [key, parent, pp], 'Parent port has no explicit child boundary mapping.')
                internally_connected = {(f['to'], f['input']) if direction == 'inputs' else (f['from'], f['output'])
                                        for f in flows.values() if f['from'] in children and f['to'] in children}
                for child in sorted(children):
                    for port in sorted(functions[child][direction]):
                        if (child, port) not in mapped_child | internally_connected:
                            issue('decomposition', 'child_boundary_missing', 'fail', [key, child, port], 'Child port needs an internal connection or an explicit parent boundary mapping.')
        # Kahn traversal bounds hierarchy checks and retains isolated function IDs.
        indegree = {key: 0 for key in functions}
        for children in adjacency.values():
            for child in children:
                indegree[child] += 1
        queue = sorted(key for key in functions if indegree[key] == 0)
        visited = 0
        while queue:
            node = queue.pop(); visited += 1
            for child in sorted(adjacency[node]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if visited != len(functions):
            done, active, path = set(), set(), []
            def cycle(node):
                if node in active:
                    return path[path.index(node):] + [node]
                if node in done:
                    return None
                active.add(node); path.append(node)
                for child in sorted(adjacency[node]):
                    witness = cycle(child)
                    if witness:
                        return witness
                path.pop(); active.remove(node); done.add(node)
                return None
            witness = next((w for node in sorted(functions) if (w := cycle(node))), [])
            issue('decomposition', 'decomposition_cycle', 'fail', sorted(set(witness)), 'Decomposition hierarchy is cyclic; feedback flow cycles remain permitted.', {'cycle': witness})

        used = set()
        scenarios = model.get('scenarios', {})
        for scenario in sorted(set(scenarios) | set(record['step_bindings'])):
            if scenario not in scenarios:
                issue('scenarios', 'binding_scenario', 'fail', [scenario], 'Step binding names an absent finite scenario.')
                continue
            steps = scenarios[scenario].get('steps', {})
            bindings = record['step_bindings'].get(scenario, {})
            for step in sorted(set(steps) | set(bindings)):
                function_id = bindings.get(step)
                if step not in steps or function_id not in functions:
                    issue('scenarios', 'binding_step', 'fail', [scenario, step], 'Each finite step needs a binding to an existing function; extra bindings are refused.')
                    continue
                used.add(function_id)
                function, actual = functions[function_id], steps[step]
                for direction, field in (('inputs', 'consumes'), ('outputs', 'produces')):
                    if {p['data'] for p in function[direction].values()} != set(actual.get(field, [])):
                        issue('scenarios', 'step_data_contract', 'fail', [scenario, step, function_id], 'Step ' + field + ' differs from its bound function ports.')
                if function['enabling'] != actual.get('guard'):
                    issue('scenarios', 'step_enabling_contract', 'fail', [scenario, step, function_id], 'Step guard differs from its explicit function enabling condition.')
        for function_id in sorted(functions.keys() - used - parents):
            issue('scenarios', 'function_unexercised', 'unknown', [function_id], 'Leaf function has no explicitly bound scenario step.')
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError, OverflowError) as exc:
        issue('binding', 'function_input', 'error', [], str(exc)[:500])
    finally:
        result['findings'].sort(key=lambda f: (f['obligation'], f['rule'], f['ids'], f['status'], f['detail']))
        result['status'] = _status(result['findings'])
        blocked = {f['obligation'] for f in result['findings']}
        result['completed_obligations'] = [o for o in OBLIGATIONS if o not in blocked] if result.get('topology') else []
        result['obligations'] = {o: _status([f for f in result['findings'] if f['obligation'] == o])
                                 if o in blocked else 'pass' if o in result['completed_obligations'] else 'not_run' for o in OBLIGATIONS}
    return result
