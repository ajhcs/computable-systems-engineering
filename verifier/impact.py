"""Declared dependency impact and retained regression selection, without execution.

An edge names its dependent and dependency explicitly. Reverse reachability over
both revisions is a conservative recheck proposal, never engineering acceptance.
The algorithm is an original stdlib implementation; source ideas and boundaries
are recorded in docs/impact-analysis.md.
"""
from collections import deque
from copy import deepcopy
import re

from .foundation import Invalid, _object, digest, load_profile

VERSION = 'impact-1.0'
SNAPSHOT_VERSION = 'impact-snapshot-1.0'
SCOPE_VERSION = 'impact-scope-1.0'
ID = re.compile(r'[A-Za-z][A-Za-z0-9_.:-]{0,255}\Z')
DIGEST = re.compile(r'[a-f0-9]{64}\Z')
MAX_NODES = 4096
MAX_EDGES = 16384
MAX_WORK = 100000
RULES = {
    'uses': 'The dependent uses the dependency.',
    'derived_from': 'The dependent was derived from the dependency.',
    'evidence_for': 'The dependent evidence concerns the dependency target.',
    'view_of': 'The dependent view presents the dependency.',
    'checks': 'The dependent check concerns the dependency.',
    'typed_by': 'The dependent declaration has the dependency as its explicit type.',
}
LIMITS = [
    'Reachability is restricted to explicitly supplied typed dependencies in both revisions.',
    'Dependency declarations and hashes establish no semantic completeness, source truth or engineer assent.',
    'A selected check is a recheck proposal; no checker is executed and no required review or acceptance is granted.',
    'Incomplete dependency coverage broadens selection to every retained check; omitted checks remain outside the supplied scope.',
]


def _text(value, where, cap=512):
    if type(value) is not str or not value.strip() or len(value) > cap:
        raise Invalid(where + ' needs bounded nonempty text')


def _id(value, where):
    if type(value) is not str or not ID.fullmatch(value):
        raise Invalid(where + ' needs a bounded stable identity')


def _map(value, where, cap):
    if type(value) is not dict or len(value) > cap:
        raise Invalid(where + ' exceeds its bounded ID map')
    for key in value: _id(key, where)


def _ids(value, where):
    if type(value) is not list or len(value) > MAX_NODES:
        raise Invalid(where + ' needs a bounded identity list')
    for key in value: _id(key, where)
    if len(set(value)) != len(value): raise Invalid(where + ' repeats an identity')


def snapshot_schema(record):
    _object(record, ('version', 'revision', 'nodes', 'dependencies', 'complete', 'unresolved'), 'snapshot')
    if record['version'] != SNAPSHOT_VERSION: raise Invalid('Unsupported impact snapshot version')
    _object(record['revision'], ('id', 'sha256'), 'revision')
    _text(record['revision']['id'], 'revision ID')
    if type(record['revision']['sha256']) is not str or not DIGEST.fullmatch(record['revision']['sha256']):
        raise Invalid('Revision needs SHA-256')
    _map(record['nodes'], 'nodes', MAX_NODES)
    for key, node in record['nodes'].items():
        _object(node, ('kind', 'native_name', 'sha256'), key)
        _text(node['kind'], 'node kind', 64)
        if node['native_name'] is not None: _text(node['native_name'], 'native qualified name')
        if type(node['sha256']) is not str or not DIGEST.fullmatch(node['sha256']):
            raise Invalid('Node needs SHA-256')
    _map(record['dependencies'], 'dependencies', MAX_EDGES)
    for key, edge in record['dependencies'].items():
        _object(edge, ('kind', 'dependent', 'dependency'), key)
        if type(edge['kind']) is not str or edge['kind'] not in RULES:
            raise Invalid('Unsupported dependency kind')
        _id(edge['dependent'], 'dependent'); _id(edge['dependency'], 'dependency')
    if type(record['complete']) is not bool: raise Invalid('Complete must be an explicit Boolean declaration')
    if type(record['unresolved']) is not list or len(record['unresolved']) > MAX_NODES:
        raise Invalid('Unresolved dependencies need a bounded list')
    for value in record['unresolved']: _text(value, 'unresolved dependency', 2048)
    return record


def scope_schema(scope):
    _object(scope, ('version', 'checks'), 'retained impact scope')
    if scope['version'] != SCOPE_VERSION: raise Invalid('Unsupported impact scope version')
    _map(scope['checks'], 'checks', 1024)
    if not scope['checks']: raise Invalid('Retain at least one check; an empty scope cannot select a regression')
    for key, check in scope['checks'].items():
        _object(check, ('targets', 'global'), key)
        _ids(check['targets'], 'check targets')
        if type(check['global']) is not bool: raise Invalid('Check global flag must be Boolean')
        if not check['global'] and not check['targets']:
            raise Invalid('A local check needs an explicit target')
    return scope


def _base():
    return {'version': VERSION, 'status': 'error', 'claim_scope': 'declared_dependency_impact_and_recheck_selection',
            'required_review': 'not_evaluated', 'acceptance': 'not_evaluated', 'execution': 'not_run',
            'limits': list(LIMITS), 'findings': [], 'changed': {}, 'impacted': {}, 'selected_checks': {},
            'unselected_checks': [], 'coverage': {}, 'work': 0}


def analyze(baseline, candidate, scope, *, max_work=MAX_WORK):
    report = _base()
    def issue(rule, status, ids, detail):
        report['findings'].append({'rule': rule, 'status': status, 'ids': sorted(ids), 'detail': detail})
    try:
        snapshot_schema(baseline); snapshot_schema(candidate); scope_schema(scope)
        if type(max_work) is not int or not 1 <= max_work <= MAX_WORK:
            raise Invalid('Work limit must be an integer within 1..' + str(MAX_WORK))
        report.update(baseline=deepcopy(baseline['revision']), candidate=deepcopy(candidate['revision']),
                      baseline_snapshot_sha256=digest(baseline), candidate_snapshot_sha256=digest(candidate),
                      scope_sha256=digest(scope), max_work=max_work)
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        issue('impact_schema', 'error', [], str(exc)); return report
    old, new = baseline['nodes'], candidate['nodes']
    added = sorted(set(new) - set(old)); removed = sorted(set(old) - set(new))
    modified = sorted(key for key in set(new) & set(old) if old[key] != new[key])
    report['changed'] = {'added': added, 'removed': removed, 'modified': modified, 'dependencies': []}
    seeds = set(added + removed + modified)
    causes = {}
    for label, keys in (('node_added', added), ('node_removed', removed), ('node_modified', modified)):
        for key in keys: causes.setdefault(key, []).append({'kind': label, 'id': key})
    old_edges, new_edges = baseline['dependencies'], candidate['dependencies']
    for key in sorted(set(old_edges) | set(new_edges)):
        if old_edges.get(key) != new_edges.get(key):
            report['changed']['dependencies'].append(key)
            for revision, graph in (('baseline', old_edges), ('candidate', new_edges)):
                if key in graph:
                    for endpoint in (graph[key]['dependent'], graph[key]['dependency']):
                        seeds.add(endpoint)
                        causes.setdefault(endpoint, []).append({'kind': 'dependency_changed', 'id': key, 'revision': revision})
    complete = True
    all_nodes = set(old) | set(new)
    adjacency = {}
    for label, snapshot in (('baseline', baseline), ('candidate', candidate)):
        if not snapshot['complete'] or snapshot['unresolved']:
            complete = False
            issue('dependency_coverage', 'unknown', [], label + ' declares incomplete coverage or unresolved dependencies')
        for key, edge in sorted(snapshot['dependencies'].items()):
            missing = {edge['dependent'], edge['dependency']} - set(snapshot['nodes'])
            if missing:
                complete = False
                issue('missing_dependency', 'unknown', missing, label + ' dependency ' + key + ' has absent endpoints')
            adjacency.setdefault(edge['dependency'], set()).add((edge['dependent'], key, edge['kind'], label))
    for key, check in sorted(scope['checks'].items()):
        missing = set(check['targets']) - all_nodes
        if missing:
            complete = False
            issue('missing_check_target', 'unknown', missing, 'Retained check ' + key + ' targets absent identities')
    # Sorted multi-source breadth-first search records a deterministic shortest
    # path. Each admitted node is processed once; cycles are permitted.
    reached = {key: {'seed': key, 'depth': 0, 'path': []} for key in sorted(seeds)}
    pending = deque(sorted(seeds)); truncated = False
    while pending and not truncated:
        current = pending.popleft()
        for dependent, edge_id, kind, revision in sorted(adjacency.get(current, ())):
            if report['work'] >= max_work:
                truncated = True; complete = False; break
            report['work'] += 1
            if dependent in reached: continue
            parent = reached[current]
            path_cost = len(parent['path']) + 1
            if report['work'] + path_cost > max_work:
                truncated = True; complete = False; break
            report['work'] += path_cost
            hop = {'id': edge_id, 'kind': kind, 'dependency': current, 'dependent': dependent, 'revision': revision}
            reached[dependent] = {'seed': parent['seed'], 'depth': parent['depth'] + 1, 'path': parent['path'] + [hop]}
            pending.append(dependent)
    if truncated: issue('impact_work_limit', 'unknown', [], 'Reachability work cap exceeded; partial paths retained')
    report['impacted'] = {key: reached[key] for key in sorted(reached)}
    report['change_reasons'] = {key: causes[key] for key in sorted(causes)}
    broad = not complete
    for key, check in sorted(scope['checks'].items()):
        targets = sorted(set(check['targets']) & set(reached))
        reasons = (['incomplete_dependency_coverage'] if broad else []) + (['global_check'] if check['global'] else [])
        if targets: reasons.append('impacted_targets')
        if reasons:
            report['selected_checks'][key] = {'reasons': reasons, 'targets': targets, 'execution': 'not_run'}
        else: report['unselected_checks'].append(key)
    report['coverage'] = {'declared_graph_complete': complete, 'selection': 'all_retained_checks' if broad else 'declared_graph',
                          'changed_seeds': sorted(seeds), 'discovered_dependencies': False}
    report['status'] = 'pass' if complete else 'unknown'
    report['findings'].sort(key=lambda row: (row['rule'], row['ids'], row['detail']))
    return report


def inspect(baseline_path, candidate_path, scope_path, scope_sha256, *, max_work=MAX_WORK):
    """Bind selection to independently retained scope bytes, without executing it."""
    try:
        baseline, before_hash = load_profile(baseline_path)
        candidate, after_hash = load_profile(candidate_path)
        scope, actual_scope_hash = load_profile(scope_path)
        if actual_scope_hash != scope_sha256:
            raise Invalid('Retained scope byte digest differs from the independently supplied expected digest')
        result = analyze(baseline, candidate, scope, max_work=max_work)
        result.update(baseline_file_sha256=before_hash, candidate_file_sha256=after_hash,
                      scope_file_sha256=actual_scope_hash)
        return result
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        report = _base(); report['findings'] = [{'rule': 'impact_input', 'status': 'error', 'ids': [], 'detail': str(exc)}]
        return report


def snapshot_workflow(record, revision, *, relation_directions=None, complete=False):
    """Extract explicit documentary references; unknown directions remain visible.

    A relation direction is an engineer-supplied map from its kind to either
    from_depends_on_to or to_depends_on_from. No SysML semantics are inferred.
    Native parsing/binding must be checked separately using the existing workflow.
    """
    from .workflow import schema, GROUPS
    schema(record)
    directions = {} if relation_directions is None else relation_directions
    if type(directions) is not dict or len(directions) > 128:
        raise Invalid('Relation directions need a bounded map')
    for key, value in directions.items():
        _text(key, 'relation kind', 120)
        if value not in ('from_depends_on_to', 'to_depends_on_from'):
            raise Invalid('Unsupported declared relation direction')
    nodes = {}; edges = {}; unresolved = []
    def edge(key, dependent, dependency, kind):
        # Synthetic dependency identities are disjoint from the record IDs.
        edges[key] = {'dependent': dependent, 'dependency': dependency, 'kind': kind}
    for group in GROUPS:
        if group == 'workflows': continue
        for key, value in sorted(record[group].items()):
            nodes[key] = {'kind': value.get('kind', group), 'native_name': value.get('native_name'), 'sha256': digest(value)}
            if value.get('basis'): edge('basis:' + key, key, value['basis'], 'derived_from')
    nodes['workflow:context'] = {'kind': 'workflow_context', 'native_name': None,
        'sha256': digest({'question': record['question'], 'workflows': record['workflows']})}
    if record['question'].get('basis'):
        edge('question:basis', 'workflow:context', record['question']['basis'], 'derived_from')
    for key, value in sorted(record['relations'].items()):
        for endpoint in ('from', 'to'):
            edge('endpoint:' + key + ':' + endpoint, key, value[endpoint], 'uses')
        direction = directions.get(value['kind'])
        if direction:
            dep, base = (value['from'], value['to']) if direction == 'from_depends_on_to' else (value['to'], value['from'])
            edge('relation:' + key, dep, base, 'uses')
        else: unresolved.append('Unmapped documentary relation ' + key + ' (' + value['kind'] + ')')
    for key, value in sorted(record['evidence'].items()):
        edge('target:' + key, key, value['target'], 'evidence_for')
    for key, value in sorted(record.get('views', {}).items()):
        nodes[key] = {'kind': 'view', 'native_name': None, 'sha256': digest(value)}
        for target in value['elements']: edge('view:' + key + ':' + target, key, target, 'view_of')
    for group in ('decisions', 'questions'):
        for key, value in sorted(record[group].items()):
            if value['affects']:
                unresolved.append('Unmapped affects direction for ' + key)
    if record['trade_studies']: unresolved.append('Trade-study dependencies are outside this adapter')
    result = {'version': SNAPSHOT_VERSION, 'revision': deepcopy(revision), 'nodes': nodes, 'dependencies': edges,
              'complete': complete, 'unresolved': sorted(unresolved)}
    snapshot_schema(result)
    return result


def render_text(report):
    lines = [report['status'] + ': declared dependency impact and recheck selection',
             'Changed seeds: ' + ', '.join(report.get('coverage', {}).get('changed_seeds', [])),
             'Selected checks (not run): ' + ', '.join(report['selected_checks'])]
    for finding in report['findings']: lines.append(finding['status'] + ': ' + finding['rule'] + ': ' + finding['detail'])
    return '\n'.join(lines) + '\n'


def snapshot_native(paths, revision_id, *, relation_directions=None, workflow='concept'):
    """Snapshot an existing native workflow using its current capture/parser path.

    This deliberately retains unresolved native breadth. It extracts represented
    native facts, but cannot certify all native dependencies or imported meaning.
    """
    from .workflow import inspect_workflow
    report = inspect_workflow(paths, workflow=workflow)
    if report.get('native_status') != 'pass' or report.get('input_stability') != 'pass' or 'record' not in report:
        raise Invalid('Native workflow capture did not complete: ' + '; '.join(
            f.get('detail', '') for f in report.get('findings', [])))
    revision = {'id': revision_id, 'sha256': report['model_sha256']}
    result = snapshot_workflow(report['record'], revision, relation_directions=relation_directions)
    def facts(value):
        if type(value) is dict:
            return {key: facts(item) for key, item in value.items() if key not in ('source', 'line')}
        if type(value) is list: return [facts(item) for item in value]
        return value
    for key, element in report['record']['elements'].items():
        binding = report.get('bindings', {}).get(key)
        if binding is None:
            result['unresolved'].append('Native binding unresolved for ' + key)
        result['nodes'][key]['sha256'] = digest({'documentary': element, 'native': facts(binding)})
    result['nodes']['native:bundle'] = {'kind': 'native_model_bundle', 'native_name': None,
        'sha256': digest({'model_sha256': report['model_sha256'], 'inventory': facts(report.get('native_inventory', {}))})}
    # Capture the workflow-wide question/focus as well as element records. A
    # changed workflow context is visible even if no element text changes.
    result['nodes']['workflow:context'] = {'kind': 'workflow_context', 'native_name': None,
        'sha256': digest({'question': report['record']['question'], 'workflows': report['record']['workflows']})}
    result['unresolved'] += [
        'Native dependencies, omitted native meaning and undeclared imports are not completely discovered',
        'Source content truth and external dependency coverage are not established by workflow snapshot extraction',
    ]
    result['unresolved'] = sorted(set(result['unresolved']))
    snapshot_schema(result)
    return result
