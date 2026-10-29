"""Opt-in reconciliation of an explicit current design context and retained selections."""
from hashlib import sha256
import json
from pathlib import Path

from .foundation import Invalid, _object, load_profile, read_regular
from .sysml import check_sysml
from .workflow import capture_model_inputs

VERSION = 'configuration-1.0'
CONNECTED_VERSION = 'configuration-1.1'
LIMITS = [
    'Checks explicit authored role declarations and exact direct types, not installed equipment or procurement quantities.',
    'Selected roles must be reachable through their explicit parent chain and linked type inheritance.',
    'Inherited role lookup is refused when a descendant redefines the requested declaration; select the overriding declaration explicitly.',
    'Usage-owned overrides are checked; specialized parent usage inheritance and native variant selection are unsupported.',
    'Connection endpoint proof is unsupported by this profile; requested connections prevent success.',
    'Open alternatives are named library definitions, not automatic selections or evidence of a complete trade space.',
    'Hashes identify supplied bytes, not engineer assent, source truth, implementation, behavior or acceptance.',
]


def _name(value):
    if type(value) is not str or not value.strip() or len(value) > 512:
        raise Invalid('Native identities need nonempty qualified text of at most 512 characters')


def schema(scope):
    connected = type(scope) is dict and scope.get('version') == CONNECTED_VERSION
    _object(scope, ('version', 'root', 'selected_roles', 'open_alternatives', 'connections', *(('external_roles',) if connected else ())), 'configuration scope')
    if scope['version'] not in (VERSION, CONNECTED_VERSION):
        raise Invalid('Unsupported configuration scope version')
    _object(scope['root'], ('native_name', 'type'), 'root')
    for value in scope['root'].values(): _name(value)
    roles = scope['selected_roles']
    if type(roles) is not dict or len(roles) > 256:
        raise Invalid('Selected roles need at most 256 distinct IDs')
    for key, role in roles.items():
        if type(key) is not str or not key.isascii() or not key.replace('_', '').isalnum() or not key[0].isalpha() or len(key) > 64:
            raise Invalid('Selected role IDs must be bounded ASCII identifiers')
        _object(role, ('parent', 'native_name', 'type'), key)
        for value in role.values(): _name(value)
        if role['parent'] != '$root' and role['parent'] not in roles:
            raise Invalid('Selected role parent must name $root or another selected role')
    for key in roles:
        seen = set(); cursor = key
        while cursor != '$root':
            if cursor in seen: raise Invalid('Selected role parent cycle')
            seen.add(cursor); cursor = roles[cursor]['parent']
    names = [scope['root']['native_name']] + [r['native_name'] for r in roles.values()]
    if len(names) != len(set(names)): raise Invalid('Selected native identities must be distinct')
    alternatives = scope['open_alternatives']
    if type(alternatives) is not list or len(alternatives) > 256:
        raise Invalid('Open alternatives need a bounded list')
    for name in alternatives: _name(name)
    if len(set(alternatives)) != len(alternatives): raise Invalid('Duplicate open alternative')
    if type(scope['connections']) is not list or len(scope['connections']) > 256:
        raise Invalid('Connections need a bounded list')
    if not connected:
        for item in scope['connections']:
            _object(item, ('from', 'to'), 'connection')
            for value in item.values(): _name(value)
    else:
        external = scope['external_roles']
        if type(external) is not dict or len(external) > 256:
            raise Invalid('External roles need a bounded map')
        for key, role in external.items():
            if type(key) is not str or not key.isascii() or not key.replace('_', '').isalnum() or not key[0].isalpha() or len(key) > 64 or key in roles:
                raise Invalid('External role IDs must be distinct bounded ASCII identifiers')
            _object(role, ('native_name', 'type'), key)
            for value in role.values(): _name(value)
        all_names = names + [r['native_name'] for r in external.values()]
        if len(all_names) != len(set(all_names)):
            raise Invalid('Current and external native usages must be distinct')
        connection_ids = set(); native_connections = set()
        for connection in scope['connections']:
            _object(connection, ('id', 'native_name', 'owner', 'from', 'to'), 'connection')
            key = connection['id']
            if type(key) is not str or not key.isascii() or not key.replace('_', '').isalnum() or not key[0].isalpha() or len(key)>64 or key in connection_ids or key in roles or key in external:
                raise Invalid('Connections need distinct bounded IDs')
            connection_ids.add(key); _name(connection['owner'])
            if connection['native_name'] is not None: _name(connection['native_name'])
            native_key = (connection['owner'], connection['native_name'])
            if connection['native_name'] is not None and native_key in native_connections:
                raise Invalid('Duplicate selected native connection')
            native_connections.add(native_key)
            for endpoint in (connection['from'], connection['to']):
                _object(endpoint, ('role', 'port'), 'connection endpoint')
                if endpoint['role'] != '$root' and endpoint['role'] not in roles and endpoint['role'] not in external:
                    raise Invalid('Connection endpoint must reference a selected root, role or external peer')
                _name(endpoint['port'])


def _reconcile_base(scope, inventory):
    """Compare independently retained selections with linked native facts."""
    schema(scope)
    findings = []; checked = []; view = {'root': None, 'selected_roles': {}, 'open_alternatives': list(scope['open_alternatives'])}
    def issue(rule, status, identity, detail):
        findings.append({'rule': rule, 'status': status, 'id': identity, 'detail': detail})
    parts = inventory.get('parts', []); definitions = inventory.get('part_definitions', [])
    def exact(records, name, identity):
        found = [r for r in records if r.get('qualified_name') == name]
        if len(found) != 1:
            issue('native_identity', 'fail', identity, 'Expected one exact native identity; found ' + str(len(found)))
            return None
        return found[0]
    def ancestors(name):
        pending = [name]; found = set()
        while pending:
            current = pending.pop()
            if current in found: continue
            found.add(current)
            rows = [d for d in definitions if d.get('qualified_name') == current]
            if len(rows) != 1 or 'supertypes' not in rows[0]: return None
            pending.extend(rows[0]['supertypes'])
            if len(found) > 512: return None
        return found
    def unresolved_variation(part, type_name, identity):
        lineage = ancestors(type_name)
        if lineage is None or part.get('is_variant') or part.get('is_variation') or any(
                row.get('is_variation') for row in definitions if row.get('qualified_name') in lineage):
            issue('configuration_variability', 'unsupported', identity,
                  'Variant selection, variation contexts or unavailable type ancestry are not resolved')
            return True
        return False
    root = exact(parts, scope['root']['native_name'], '$root')
    if root:
        if root.get('type') != scope['root']['type']:
            issue('selected_type', 'fail', '$root', 'Current root has a different or ambiguous direct type')
        elif root.get('nested') or root.get('owner_kind') != 'Package':
            issue('root_context', 'fail', '$root', 'Current root must be a package-level design-context usage')
        elif root.get('has_native_value') or root.get('has_non_typing_specialization'):
            issue('root_context', 'unsupported', '$root', 'Root value binding or usage specialization is outside this profile')
        elif unresolved_variation(root, scope['root']['type'], '$root'):
            pass
        elif not _selected_bound(root, '$root', issue):
            pass
        else:
            checked.append('$root'); view['root'] = dict(scope['root'])
    resolved = {}; resolved_parts = {}; pending = dict(scope['selected_roles'])
    while pending:
        progressed = False
        for key, selection in list(pending.items()):
            parent = selection['parent']
            if parent != '$root' and parent in pending: continue
            progressed = True; del pending[key]
            if parent == '$root':
                parent_type = scope['root']['type'] if '$root' in checked else None
                parent_usage = scope['root']['native_name']
            else:
                parent_type = resolved.get(parent)
                parent_usage = scope['selected_roles'][parent]['native_name']
            if parent_type is None:
                issue('parent_unresolved', 'unknown', key, 'Selected parent was not reconciled'); continue
            if parent != '$root' and resolved_parts[parent].get('has_non_typing_specialization'):
                issue('parent_context', 'unsupported', key, 'Selected parent has usage specialization; inherited usage-owned members are not resolved'); continue
            part = exact(parts, selection['native_name'], key)
            if part is None: continue
            owner = part.get('owner'); lineage = ancestors(parent_type)
            if owner not in (parent_usage, parent_type) and (lineage is None or owner not in lineage):
                issue('role_owner', 'unsupported' if lineage is None else 'fail', key, 'Role is not a proven member of the selected parent type'); continue
            override_owners = ({parent_usage} | (lineage or {parent_type})) - {owner}
            overrides = [r for r in parts if r.get('owner') in override_owners and selection['native_name'] in r.get('redefines', [])]
            if overrides:
                issue('role_redefined', 'fail', key, 'Selected type or usage redefines this historical role; select its overriding declaration'); continue
            if part.get('type') != selection['type']:
                issue('selected_type', 'fail', key, 'Selected role has a different or ambiguous direct type'); continue
            if part.get('has_native_value'):
                issue('role_binding', 'unsupported', key, 'Role value bindings are outside this profile'); continue
            if unresolved_variation(part, selection['type'], key): continue
            if not _selected_bound(part, key, issue): continue
            checked.append(key); resolved[key] = selection['type']; resolved_parts[key] = part; view['selected_roles'][key] = dict(selection)
        if not progressed: raise Invalid('Unresolvable selection parent graph')
    selected_types = {scope['root']['type']} | {r['type'] for r in scope['selected_roles'].values()}
    for index, name in enumerate(scope['open_alternatives']):
        identity = 'open:' + str(index)
        if exact(definitions, name, identity) is None: continue
        if name in selected_types:
            issue('open_selected', 'fail', identity, 'An explicitly open alternative is also a selected exact type')
        else: checked.append(identity)
    for index, _ in enumerate(scope['connections']):
        issue('connection_proof', 'unsupported', 'connection:' + str(index), 'Linked native connection endpoints are not extracted by this profile')
    findings.sort(key=lambda f: (f['id'], f['rule'], f['detail']))
    order = {'pass': 0, 'not_run': 1, 'unknown': 2, 'unsupported': 3, 'fail': 4, 'error': 5}
    status = max((f['status'] for f in findings), key=order.get, default='pass')
    return {'status': status, 'findings': findings, 'checked': sorted(checked), 'view': view}


def reconcile(scope, inventory):
    """Reconcile legacy declarations or the explicit connected-context contract."""
    schema(scope)
    if scope['version'] == VERSION:
        return _reconcile_base(scope, inventory)
    legacy = {key: value for key, value in scope.items() if key != 'external_roles'}
    legacy.update(version=VERSION, connections=[])
    result = _reconcile_base(legacy, inventory)
    return _reconcile_connected(scope, inventory, result)


def _reconcile_connected(scope, inventory, result):
    findings = result['findings']; checked = result['checked']
    def issue(rule, status, identity, detail):
        findings.append({'rule': rule, 'status': status, 'id': identity, 'detail': detail})
    def index(group):
        rows = {}
        for row in inventory.get(group, []):
            rows.setdefault(row.get('qualified_name'), []).append(row)
        return rows
    parts = index('parts'); ports = index('ports'); definitions = index('part_definitions'); port_definitions = index('port_definitions')
    def exact(rows, name, identity, rule='native_identity'):
        matches = rows.get(name, [])
        if len(matches) != 1:
            issue(rule, 'fail', identity, 'Expected one exact native identity; found ' + str(len(matches)))
            return None
        return matches[0]
    def ancestors(name, table=definitions):
        pending = [name]; visited = set()
        while pending:
            current = pending.pop()
            if current in visited: continue
            visited.add(current)
            rows = table.get(current, [])
            if len(rows) != 1 or 'supertypes' not in rows[0] or len(visited) > 512:
                return None
            pending.extend(rows[0]['supertypes'])
            if rows[0].get('is_conjugated'):
                original = rows[0].get('original_port_definition')
                if type(original) is not str: return None
                pending.append(original)
        return visited
    root = parts.get(scope['root']['native_name'], [])
    context_owner = root[0].get('owner') if len(root) == 1 else None
    nodes = {}; paths = {}; role_facts = {}
    if '$root' in checked:
        nodes['$root'] = dict(scope['root'], parent=None, kind='root')
        paths['$root'] = [scope['root']['native_name']]
        role_facts['$root'] = root[0]
    pending = dict(scope['selected_roles'])
    while pending:
        for key in list(pending):
            row = pending[key]; parent = row['parent']
            if parent in pending: continue
            del pending[key]
            if key in checked and parent in nodes:
                nodes[key] = dict(row, kind='selected_role')
                paths[key] = paths[parent] + [row['native_name']]
                role_facts[key] = parts[row['native_name']][0]
    external_view = {}
    for key, selection in sorted(scope['external_roles'].items()):
        row = exact(parts, selection['native_name'], key)
        if row is None: continue
        if context_owner is None or '$root' not in nodes:
            issue('parent_unresolved', 'unknown', key, 'Current context was not reconciled'); continue
        if row.get('owner') != context_owner or row.get('owner_kind') != 'Package' or row.get('nested'):
            issue('external_context', 'fail', key, 'External peer must be declared in the same package as the current root'); continue
        if row.get('type') != selection['type']:
            issue('selected_type', 'fail', key, 'External peer has a different or ambiguous direct type'); continue
        if row.get('has_native_value') or row.get('has_non_typing_specialization'):
            issue('external_context', 'unsupported', key, 'Bound or specialized external usage is not resolved'); continue
        lineage = ancestors(selection['type'])
        if lineage is None or row.get('is_variant') or row.get('is_variation') or any(definitions[name][0].get('is_variation') for name in lineage):
            issue('configuration_variability', 'unsupported', key, 'External peer variability or ancestry is not resolved'); continue
        if not _selected_bound(row, key, issue): continue
        checked.append(key); nodes[key] = dict(selection, parent=None, kind='external_role')
        paths[key] = [selection['native_name']]; role_facts[key] = row
        external_view[key] = dict(selection)
        if selection['type'] in scope['open_alternatives']:
            issue('open_selected', 'fail', key, 'An explicitly open alternative is also a selected external type')
    def endpoint(endpoint, identity):
        role = endpoint['role']
        if role not in nodes:
            issue('endpoint_role', 'unknown', identity, 'Endpoint role was not reconciled: ' + role); return None
        parent = role_facts[role]
        if parent.get('has_non_typing_specialization'):
            issue('endpoint_context', 'unsupported', identity, 'Usage-specialized endpoint context is not resolved'); return None
        port = exact(ports, endpoint['port'], identity, 'port_identity')
        if port is None: return None
        lineage = ancestors(nodes[role]['type'])
        if lineage is None:
            issue('port_owner', 'unsupported', identity, 'Endpoint type ancestry is not resolved'); return None
        owners = lineage | {nodes[role]['native_name']}
        if port.get('owner') not in owners:
            issue('port_owner', 'fail', identity, 'Port does not belong to the selected endpoint context'); return None
        overriding = [p for rows in ports.values() for p in rows if p.get('owner') in owners - {port.get('owner')} and endpoint['port'] in p.get('redefines', [])]
        if overriding:
            issue('port_redefined', 'fail', identity, 'Selected endpoint context redefines the retained historical port'); return None
        if port.get('has_native_value') or port.get('has_non_typing_specialization') or port.get('is_variation') or port.get('is_variant'):
            issue('port_context', 'unsupported', identity, 'Specialized, bound or variable ports are not resolved'); return None
        port_type = port.get('type')
        port_lineage = ancestors(port_type, port_definitions) if type(port_type) is str else None
        if port_lineage is None or any(port_definitions[name][0].get('is_variation') for name in port_lineage):
            issue('port_type', 'unsupported', identity, 'Port needs one direct type with available non-variable port-definition ancestry'); return None
        if not _selected_bound(port, identity, issue): return None
        return dict(endpoint, path=paths[role] + [endpoint['port']])
    connections = inventory.get('connections', [])
    eligible_owners = ({context_owner} if context_owner is not None else set()) | {node['native_name'] for node in nodes.values()}
    omission_owners = set(eligible_owners)
    for node in nodes.values():
        omission_owners.update(ancestors(node['type']) or {node['type']})
    owner_paths = {node['native_name']: paths[key] for key, node in nodes.items()}
    package_roots = {name for name, rows in parts.items() if len(rows) == 1 and rows[0].get('owner_kind') == 'Package'}
    def native_pair(row):
        if not row.get('supported') or row.get('has_native_value') or row.get('has_non_typing_specialization') or row.get('is_variation') or row.get('is_variant'):
            return None
        ends = row.get('ends', [])
        if len(ends) != 2 or any(e.get('status') != 'supported' for e in ends): return None
        pair = []
        for end in ends:
            path = end.get('path')
            if type(path) is not list or not path or any(type(x) is not str for x in path): return None
            prefix = owner_paths.get(row.get('owner'), [])
            if prefix and path[0] not in package_roots and path[:len(prefix)] != prefix:
                path = prefix + path
            pair.append(tuple(path))
        return sorted(pair)
    edges = {}; matched_rows = set(); requested_rows = set()
    for selection in scope['connections']:
        key = selection['id']
        candidates = [(i, row) for i, row in enumerate(connections) if row.get('owner') == selection['owner'] and row.get('qualified_name') == selection['native_name']]
        if selection['native_name'] is not None:
            requested_rows.update(i for i, _ in candidates)
        start = endpoint(selection['from'], key); end = endpoint(selection['to'], key)
        if start is None or end is None: continue
        if selection['owner'] not in eligible_owners:
            owner_status = 'fail' if selection['owner'] in parts else 'unsupported'
            issue('connection_context', owner_status, key, 'Connection owner is not an admitted explicit current package or selected usage'); continue
        if selection['native_name'] is not None and len(candidates) != 1:
            issue('connection_identity', 'fail', key, 'Expected exactly one selected named native connection; found ' + str(len(candidates))); continue
        expected = sorted([tuple(start['path']), tuple(end['path'])])
        matches = [(i, row) for i, row in candidates if native_pair(row) == expected]
        requested_rows.update(i for i, _ in matches)
        if len(matches) != 1:
            status = 'unsupported' if any(native_pair(row) is None for _, row in candidates) else 'fail'
            issue('connection_endpoints', status, key, 'Expected one exact native endpoint pair in the current context; found ' + str(len(matches))); continue
        i, row = matches[0]
        if i in matched_rows:
            issue('connection_duplicate', 'fail', key, 'One native connection cannot be selected twice'); continue
        if not _selected_bound(row, key, issue): continue
        matched_rows.add(i); checked.append(key)
        edges[key] = {'native_name': row.get('qualified_name'), 'owner': row.get('owner'), 'from': start, 'to': end, 'kind': 'native_connection', 'directed': False}
    expected_ids = ['$root', *scope['selected_roles'], *scope['external_roles'], *(c['id'] for c in scope['connections'])]
    omissions = []
    for key in expected_ids:
        if key not in checked:
            relevant = [f for f in findings if f['id'] == key]
            omissions.append({'id': key, 'status': relevant[0]['status'] if relevant else 'unknown', 'reason': '; '.join(f['detail'] for f in relevant) or 'Required selection was not reconciled'})
    for i, row in enumerate(connections):
        if i not in matched_rows and row.get('owner') in omission_owners:
            label = row.get('qualified_name') or f"anonymous:{row.get('owner')}:{row.get('source')}:{row.get('line')}"
            reason = ('Requested native connector failed reconciliation' if i in requested_rows else
                      'Native connector declared on a selected type is outside supported explicit context proof' if row.get('owner') not in eligible_owners else
                      'Native current-context connector outside the retained connection scope')
            omissions.append({'id': 'native:' + label, 'status': 'unreconciled' if i in requested_rows else 'not_selected', 'reason': reason})
    findings.sort(key=lambda f: (f['id'], f['rule'], f['detail']))
    order = {'pass': 0, 'not_run': 1, 'unknown': 2, 'unsupported': 3, 'fail': 4, 'error': 5}
    result['status'] = max((f['status'] for f in findings), key=order.get, default='pass')
    result['checked'] = sorted(checked); result['view'].update(external_roles=external_view, connections=edges)
    result['system_view'] = {'version': 'configuration-system-view-1.0', 'scope': 'selected_configuration_obligations', 'status': result['status'], 'nodes': dict(sorted(nodes.items())), 'edges': dict(sorted(edges.items())), 'omissions': omissions, 'open_alternatives': list(scope['open_alternatives'])}
    return result


def _selected_bound(part, identity, issue):
    bound = part.get('multiplicity', {})
    if bound.get('status') not in ('default', 'literal'):
        issue('selected_multiplicity', 'unsupported', identity, 'Selected role needs a supported positive lower multiplicity; inherited or complex bounds are not resolved')
        return False
    if bound.get('upper') == 0:
        issue('selected_multiplicity', 'fail', identity, 'Selected role is suppressed by zero upper multiplicity')
        return False
    if type(bound.get('lower')) is not int or bound['lower'] < 1:
        issue('selected_multiplicity', 'unknown', identity, 'Optional role declaration does not establish selected presence')
        return False
    return True


def inspect_configuration(models, scope_path, scope_sha256, *, expected_model_sha256=None):
    report = {'version': VERSION, 'status': 'error', 'claim_scope': 'selected_native_configuration_reconciliation',
              'acceptance': 'not_evaluated', 'behavior': 'not_run', 'findings': [], 'checked': [], 'limits': LIMITS,
              'checker_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    try:
        scope, digest = load_profile(scope_path); report['scope_sha256'] = digest; schema(scope)
        if digest != scope_sha256: raise Invalid('Scope fingerprint is missing or stale')
        if scope['version'] == CONNECTED_VERSION:
            report['version'] = CONNECTED_VERSION
            report['claim_scope'] = 'selected_native_connected_context_reconciliation'
            report['connectivity_claim'] = 'selected_binary_adjacencies' if scope['connections'] else 'empty_scope_no_connectivity_claim'
            report['limits'] = [x for x in LIMITS if not x.startswith('Connection endpoint proof')] + [
                'Connection checks prove only retained ordinary binary native adjacency in the selected explicit context; no flow, direction, protocol or behavior is established.',
                'The system view covers retained obligations; omitted native connectors are disclosed. Empty connections make no connectivity claim.']
        captured, files, model_digest = capture_model_inputs(models)
        report.update(model_files=files, model_sha256=model_digest)
        if expected_model_sha256 is not None and expected_model_sha256 != model_digest:
            raise Invalid('Expected model fingerprint is stale')
        native = check_sysml([p for p, _ in captured], syntax_only=True)
        report['native'] = {k: native.get(k) for k in ('status', 'checker_version', 'parser', 'parser_issues', 'findings')}
        if native.get('status') != 'pass':
            report.update(status=native.get('status', 'error'), findings=[{'rule': 'native_input', 'status': native.get('status', 'error'), 'id': '$root', 'detail': 'Native parsing did not succeed; reconciliation not run'}])
            return report
        if native.get('model_sha256') != model_digest: raise Invalid('Native parse did not bind the captured model bundle')
        compared = reconcile(scope, native['inventory'])
        if any(read_regular(path, 5_000_000) != raw for path, raw in captured): raise Invalid('Model changed during reconciliation')
        if load_profile(scope_path)[1] != digest: raise Invalid('Scope changed during reconciliation')
        report.update(compared)
    except (OSError, ValueError, UnicodeError, TypeError, KeyError, RecursionError) as exc:
        report.update(status='error', checked=[], findings=[{'rule': 'input_or_record', 'status': 'error', 'id': '$root', 'detail': str(exc)}])
        report.pop('view', None)
        report.pop('system_view', None)
    return report


def render_text(report):
    lines = [report['status'] + ': selected native configuration reconciliation; behavior not evaluated']
    if report.get('view', {}).get('root'):
        root = report['view']['root']; lines.append('Current context: ' + root['native_name'] + ' : ' + root['type'])
        for key, role in sorted(report['view']['selected_roles'].items()):
            lines.append(f"  {key}: {role['native_name']} : {role['type']} (parent {role['parent']})")
        for name in report['view']['open_alternatives']: lines.append('  Open library alternative: ' + name)
        for key, peer in sorted(report['view'].get('external_roles', {}).items()):
            lines.append(f"  External {key}: {peer['native_name']} : {peer['type']}")
        for key, edge in sorted(report['view'].get('connections', {}).items()):
            lines.append(f"  Native adjacency {key}: {edge['from']['role']}.{edge['from']['port']} -- {edge['to']['role']}.{edge['to']['port']}")
    if report.get('system_view'):
        lines.append('System view covers retained configuration obligations only; no behavior or whole-model completeness is claimed.')
        for omission in report['system_view']['omissions']:
            lines.append(f"  Omitted {omission['id']} ({omission['status']}): {omission['reason']}")
    for finding in report['findings']:
        lines.append(f"  {finding['id']} {finding['rule']}: {finding['detail']}")
    return '\n'.join(lines) + '\n'
