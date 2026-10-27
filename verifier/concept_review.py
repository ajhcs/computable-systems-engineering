"""Project-tailored documentary coverage over the existing native CSE adapter.

The model remains authoritative; a separate scope names what this review must
retain. No project obligations or allocation minima are inferred from the draft.
"""
from copy import deepcopy
from hashlib import sha256
import json
import re

from .core import _pairs
from .foundation import Invalid, _object, read_regular, check_profile
from .workflow import KINDS, inspect_workflow
from .human_tasks import expectation as task_expectation, inspect_tasks
from .ownership import expectation as ownership_expectation, inspect_ownership

VERSION = 'concept-review-1.2'
ID = re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,63}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
RELATIONS = {'addresses', 'derives_from', 'allocated_to', 'scenario_of', 'precedes',
             'participates_in', 'decomposes', 'interfaces_with', 'information_to', 'controls'}
PURPOSES = {'verification', 'validation', 'qualification', 'analysis'}


def load(path):
    raw = read_regular(path, 1_000_000)
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(Invalid('Nonfinite JSON'))), raw


def _text(value, where):
    if type(value) is not str or len(value) > 4096:
        raise Invalid(where + ' needs text of at most 4096 characters')


def _map(value, where, cap=64):
    if type(value) is not dict or len(value) > cap or any(not ID.fullmatch(k) for k in value):
        raise Invalid(where + ' needs a bounded ID map')


def _ids(value, where):
    if (type(value) is not list or len(value) > 64 or
            any(type(k) is not str or not ID.fullmatch(k) for k in value) or len(set(value)) != len(value)):
        raise Invalid(where + ' needs distinct IDs')


def schema(scope):
    _object(scope, ('version', 'project', 'sources', 'topics', 'expectations', 'allocation_bounds'), 'scope')
    if scope['version'] not in ('concept-review-1.0','concept-review-1.1',VERSION):
        raise Invalid('Unsupported concept-review scope version')
    _object(scope['project'], ('id', 'name', 'question', 'boundary', 'basis'), 'project')
    for field in ('id', 'name', 'question', 'boundary'):
        _text(scope['project'][field], 'project.' + field)
    if not ID.fullmatch(scope['project']['id']):
        raise Invalid('Project ID must be a stable ID')
    if scope['project']['basis'] is not None and scope['project']['basis'] not in scope['sources']:
        raise Invalid('Project basis must name a declared source or be null')
    for key in ('sources', 'topics', 'expectations'):
        _map(scope[key], key, 512 if key == 'expectations' else 64)
    for key, digest in scope['sources'].items():
        if type(digest) is not str or not DIGEST.fullmatch(digest):
            raise Invalid(key + ' needs a source SHA-256')
    for key, topic in scope['topics'].items():
        _object(topic, ('applicability', 'rationale'), key)
        if topic['applicability'] not in ('included', 'excluded', 'unresolved'):
            raise Invalid(key + ' has unsupported applicability')
        _text(topic['rationale'], key + '.rationale')
    fields = {
        'element': ('element', 'element_kind', 'native_name'),
        'relation': ('relation_kind', 'from', 'to'),
        'evidence_plan': ('evidence', 'target', 'purpose'),
        'walk': ('scenario', 'functions'),
        'human_task': (),
        'ownership': (),
    }
    for key, item in scope['expectations'].items():
        if type(item) is not dict or item.get('kind') not in fields:
            raise Invalid(key + ' has unsupported expectation kind')
        if item['topic'] not in scope['topics']:
            raise Invalid(key + ' names an absent topic')
        if scope['topics'][item['topic']]['applicability'] == 'excluded':
            raise Invalid(key + ' cannot silently disable an expectation through an excluded topic')
        if item['kind']=='human_task':
            if scope['version'] not in ('concept-review-1.1','concept-review-1.2'):
                raise Invalid('Human-task expectations require explicit concept-review-1.1 or concept-review-1.2 scope version')
            task_expectation(item)
            continue
        if item['kind']=='ownership':
            if scope['version']!='concept-review-1.2':raise Invalid('Ownership expectations require the explicit concept-review-1.2 scope version')
            ownership_expectation(item)
            continue
        _object(item, ('topic', 'kind', *fields[item['kind']]), key)
        for field in fields[item['kind']]:
            if field == 'functions':
                _ids(item[field], key + '.' + field)
                if not item[field]:
                    raise Invalid('A declared walk needs at least one function')
            else:
                _text(item[field], key + '.' + field)
                if not item[field]:
                    raise Invalid(key + '.' + field + ' must not be empty')
        if item['kind'] == 'element' and item['element_kind'] not in KINDS:
            raise Invalid('Unsupported expected element kind')
        if item['kind'] == 'relation' and item['relation_kind'] not in RELATIONS:
            raise Invalid('Unsupported expected relation kind')
        if item['kind'] == 'evidence_plan' and item['purpose'] not in PURPOSES:
            raise Invalid('Unsupported evaluation purpose')
    _object(scope['allocation_bounds'], ('functions', 'resources'), 'allocation_bounds')
    for group, bounds in scope['allocation_bounds'].items():
        _map(bounds, group)
        for key, bound in bounds.items():
            _object(bound, ('min', 'max'), key)
            if any(type(bound[x]) is not int for x in ('min', 'max')) or not 0 <= bound['min'] <= bound['max'] <= 512:
                raise Invalid(key + ' needs explicit integer bounds 0 <= min <= max <= 512')
    if bool(scope['allocation_bounds']['functions']) != bool(scope['allocation_bounds']['resources']):
        raise Invalid('Selected allocation counts need both function and resource scopes')
    return scope


def starter(project_id, name):
    """An incomplete project contract; never derive obligations from a candidate."""
    return schema({'version': VERSION,
        'project': {'id': project_id, 'name': name, 'question': '', 'boundary': '', 'basis': None},
        'sources': {}, 'topics': {}, 'expectations': {},
        'allocation_bounds': {'functions': {}, 'resources': {}}})


def _status(states):
    for state in ('error', 'fail', 'unsupported', 'unknown', 'not_run'):
        if state in states:
            return state
    return 'pass' if states and all(s == 'pass' for s in states) else 'error'


def compare(scope, record):
    """Compare explicit expectations with a natively bound documentary record."""
    findings, walks = [], {}
    def issue(rule, ids, detail, status='fail'):
        findings.append({'rule': rule, 'status': status, 'ids': ids, 'detail': detail})
    for field in ('name', 'question', 'boundary'):
        if not scope['project'][field].strip():
            issue('scope_context_missing', [], 'Project ' + field + ' is unresolved.', 'unknown')
    if not scope['sources'] or scope['project']['basis'] is None:
        issue('scope_basis_missing', [], 'Supply the project review basis.', 'unknown')
    if not scope['topics'] or not scope['expectations']:
        issue('scope_empty', [], 'Select project-specific topics and expectations before claiming coverage.', 'unknown')
    for key, topic in scope['topics'].items():
        if topic['applicability'] == 'unresolved' or not topic['rationale'].strip():
            issue('scope_applicability_unknown', [key], 'Resolve or explain this topic\'s applicability.', 'unknown')
        if topic['applicability'] == 'included' and not any(x['topic'] == key for x in scope['expectations'].values()):
            issue('topic_expectations_missing', [key], 'Included topic has no selected checks.', 'unknown')
    elements = record['elements']
    relations = {(x['kind'], x['from'], x['to']) for x in record['relations'].values()}
    relations.update((kind, right, left) for kind, left, right in list(relations) if kind == 'interfaces_with')
    def element(key, kinds, expectation):
        actual = elements.get(key)
        if actual is None or actual['kind'] not in kinds:
            issue('missing_scoped_element', [expectation, key], 'Expected element is absent or has the wrong kind.')
            return None
        return actual
    for key, item in scope['expectations'].items():
        kind = item['kind']
        if kind == 'element':
            actual = element(item['element'], {item['element_kind']}, key)
            if actual and actual['native_name'] != item['native_name']:
                issue('scoped_identity_changed', [key, item['element']], 'Expected native identity changed; review the meaning before revising scope.')
        elif kind == 'relation':
            if (item['relation_kind'], item['from'], item['to']) not in relations:
                issue('missing_scoped_relation', [key, item['from'], item['to']],
                    'Missing ' + item['relation_kind'] + ': ' + item['from'] + ' -> ' + item['to'])
        elif kind == 'evidence_plan':
            actual = record['evidence'].get(item['evidence'])
            if actual is None:
                issue('missing_evaluation_plan', [key, item['target']], 'Selected evaluation plan was removed, not completed.')
            elif (actual['target'], actual['purpose'], actual['mode'], actual['result']) != (item['target'], item['purpose'], 'plan', 'not_run'):
                issue('evaluation_meaning_changed', [key], 'Plan target, purpose, mode or result changed; reconcile the review stage explicitly.')
        elif kind == 'walk':
            element(item['scenario'], {'scenario'}, key)
            for function in item['functions']:
                element(function, {'function'}, key)
            walks[key] = {'scenario': item['scenario'], 'functions': deepcopy(item['functions']),
                'meaning': 'Expected documentary walk; order and real operational correspondence require source/human review, not native execution.'}
    return findings, walks


def _allocation_aliases(scope):
    # Workflow IDs may include hyphens; the older allocation adapter has a
    # narrower ID alphabet. Compiler-local aliases preserve native identities.
    return {key: prefix + str(index) for group, prefix in [('functions', 'CF_'), ('resources', 'CR_')]
            for index, key in enumerate(sorted(scope['allocation_bounds'][group]))}


def allocation_profile(scope, record, model_digest):
    """A derived input for the existing allocation checker, with no default bounds."""
    bounds = scope['allocation_bounds']
    if not bounds['functions']:
        return None
    selected = {**{k: 'function' for k in bounds['functions']}, **{k: 'resource' for k in bounds['resources']}}
    if len(selected) != len(bounds['functions']) + len(bounds['resources']):
        raise Invalid('Function and resource count scopes must be distinct')
    elements = record['elements']
    aliases = _allocation_aliases(scope)
    for key, kind in selected.items():
        expected = {'function'} if kind == 'function' else {'element', 'system'}
        if key not in elements or elements[key]['kind'] not in expected:
            raise Invalid('Selected allocation element absent or wrong kind: ' + key)
    return {'version': 'foundation-1.0', 'source_sha256': model_digest,
        'terms': {f'T_{kind.upper()}': {'namespace': 'CSE.ConceptReview', 'revision': '1',
            'label': kind, 'definition': 'Declared scoped ' + kind, 'kind': kind}
            for kind in ('function', 'resource')},
        'elements': {aliases[k]: {'kind': kind, 'term': f'T_{kind.upper()}', 'native_name': elements[k]['native_name']}
            for k, kind in selected.items()},
        'relations': [], 'use_cases': {}, 'capabilities': {},
        'allocations': {'PROJECT': {'functions': [aliases[k] for k in bounds['functions']], 'resources': [aliases[k] for k in bounds['resources']],
            'pairs': [{'function': aliases[x['from']], 'resource': aliases[x['to']], 'rationale': x['label']}
                for x in record['relations'].values() if x['kind'] == 'allocated_to'
                and x['from'] in bounds['functions'] and x['to'] in bounds['resources']],
            'function_bounds': {aliases[k]: deepcopy(v) for k,v in bounds['functions'].items()},
            'resource_bounds': {aliases[k]: deepcopy(v) for k,v in bounds['resources'].items()}}}}


def inspect_concept(model_path, scope_path, expected_scope_sha256, source_paths):
    report = {'version': VERSION, 'status': 'error', 'claim_scope': 'project_scoped_documentary_coverage',
        'project': None, 'findings': [], 'workflow_status': 'not_run', 'allocation_status': 'not_run',
        'human_task_status': 'not_run',
        'ownership_status': 'not_run',
        'model_sha256': None, 'scope_sha256': None, 'sources': {}, 'walks': {},
        'coverage': {'expected': [], 'checked': [], 'not_run': []},
        'behavior': 'not_run', 'required_behavior_review': 'not_evaluated', 'acceptance': 'not_evaluated',
        'limits': ['Scope appropriateness and completeness require engineering judgment.',
            'Documentary coverage and allocation counts do not establish capability, feasibility or staffing adequacy.',
            'Plans are not observed operational evidence; narrative walks are not executable behavior.',
            'Hashes identify input bytes, not authenticated approval or protected execution.']}
    captured = []
    def issue(rule, status, ids, detail):
        report['findings'].append({'rule': rule, 'status': status, 'ids': ids, 'detail': detail})
    try:
        scope, scope_raw = load(scope_path)
        report['scope_sha256'] = sha256(scope_raw).hexdigest()
        if type(expected_scope_sha256) is not str or not DIGEST.fullmatch(expected_scope_sha256):
            raise Invalid('Supply the separately retained review scope SHA-256')
        if report['scope_sha256'] != expected_scope_sha256:
            raise Invalid('Scope revision differs from the retained review basis; no candidate checking was run')
        schema(scope)
        report['project'] = deepcopy(scope['project'])
        report['topics'] = deepcopy(scope['topics'])
        report['selected_allocation_bounds'] = deepcopy(scope['allocation_bounds'])
        report['coverage']['expected'] = sorted(scope['expectations'])
        report['coverage']['not_run'] = sorted(scope['expectations'])
        if type(source_paths) is not dict or set(source_paths) != set(scope['sources']):
            raise Invalid('Supply exactly the source IDs declared by the project scope')
        model_raw = read_regular(model_path, 5_000_000)
        report['model_sha256'] = sha256(model_raw).hexdigest()
        captured = [(model_path, model_raw, 5_000_000), (scope_path, scope_raw, 1_000_000)]
        for key, path in sorted(source_paths.items()):
            raw = read_regular(path, 1_000_000)
            captured.append((path, raw, 1_000_000))
            actual = sha256(raw).hexdigest()
            report['sources'][key] = {'expected_sha256': scope['sources'][key], 'actual_sha256': actual}
            if actual != scope['sources'][key]:
                issue('scope_source_revision', 'fail', [key], 'Source differs from the selected review basis.')
        selected_tasks={k:v for k,v in scope['expectations'].items() if v['kind']=='human_task'}
        selected_ownership={k:v for k,v in scope['expectations'].items() if v['kind']=='ownership'}
        documents=tuple((['cseHumanTasks'] if selected_tasks else [])+(['cseOwnership'] if selected_ownership else []))
        workflow = inspect_workflow(model_path, source_paths, workflow='concept',
            **({'document_names':documents} if documents else {}))
        report['workflow'] = workflow
        report['workflow_status'] = workflow['status']
        report['findings'].extend(workflow['findings'])
        if workflow.get('model_sha256') != report['model_sha256']:
            issue('input_changed', 'error', [], 'Candidate changed between capture and native checking.')
        if (workflow.get('record') is not None and workflow.get('native_status') == 'pass'
                and workflow.get('input_stability') == 'pass' and workflow['status'] in ('pass','unknown','fail')):
            for key, digest in scope['sources'].items():
                if workflow['record']['sources'].get(key, {}).get('sha256') != digest:
                    issue('model_source_revision', 'fail', [key], 'Candidate provenance differs from the project review basis.')
            findings, report['walks'] = compare(scope, workflow['record'])
            report['coverage']['checked'] = sorted(scope['expectations'])
            report['coverage']['not_run'] = []
            report['findings'].extend(findings)
            if selected_tasks:
                tasks=inspect_tasks(workflow,selected_tasks)
                report['human_tasks']=tasks
                report['human_task_status']=tasks['status']
                report['findings'].extend(tasks['findings'])
                if tasks['status'] in ('error','unsupported'):
                    report['coverage']['checked']=[k for k in report['coverage']['checked'] if k not in selected_tasks]
                    report['coverage']['not_run']=sorted(selected_tasks)
            if selected_ownership:
                ownership=inspect_ownership(workflow,selected_ownership)
                report['ownership']=ownership;report['ownership_status']=ownership['status']
                report['findings'].extend(ownership['findings'])
                if ownership['status'] in ('error','unsupported'):
                    report['coverage']['checked']=[k for k in report['coverage']['checked'] if k not in selected_ownership]
                    report['coverage']['not_run']=sorted(set(report['coverage']['not_run'])|set(selected_ownership))
            try:
                profile = allocation_profile(scope, workflow['record'], report['model_sha256'])
                if profile is not None:
                    native = {'status': workflow['native_status'], 'model_sha256': workflow['model_sha256'],
                        'inventory': workflow['native_inventory']}
                    allocation = check_profile(profile, native)
                    source_ids = {value: key for key,value in _allocation_aliases(scope).items()}
                    allocation['source_id_by_compiler_id'] = source_ids
                    for finding in allocation['findings']:
                        finding['ids'] = [source_ids.get(key,key) for key in finding['ids']]
                    report['allocation'] = allocation
                    report['allocation_status'] = allocation['status']
                    report['findings'].extend(allocation['findings'])
            except Invalid as exc:
                report['allocation_status'] = 'fail'
                issue('allocation_scope', 'fail', [], str(exc))
        states = [workflow['status']] + [f['status'] for f in report['findings']]
        if scope['allocation_bounds']['functions']:
            states.append(report['allocation_status'])
        if selected_tasks:
            states.append(report['human_task_status'])
        if selected_ownership:states.append(report['ownership_status'])
        report['status'] = _status(states)
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, RecursionError) as exc:
        issue('input_or_scope', 'error', [], str(exc))
        report['status'] = 'error'
    finally:
        try:
            if any(read_regular(path, cap) != raw for path, raw, cap in captured):
                issue('input_changed', 'error', [], 'A captured model, scope or source changed during checking.')
                report['status'] = 'error'
        except (OSError, ValueError) as exc:
            issue('input_changed', 'error', [], str(exc))
            report['status'] = 'error'
        report['findings'].sort(key=lambda x: (x['rule'], x['ids'], x['detail']))
    return report


def scope_diff(before, after):
    schema(before); schema(after)
    changes = {}
    for group in ('sources', 'topics', 'expectations'):
        old, new = before[group], after[group]
        changes[group] = {'removed': sorted(set(old)-set(new)), 'added': sorted(set(new)-set(old)),
            'changed': sorted(k for k in set(old)&set(new) if old[k] != new[k])}
    return {'status': 'pass', 'claim_scope': 'scope_comparison_only', 'changes': changes,
        'project_changed': before['project'] != after['project'],
        'allocation_bounds_changed': before['allocation_bounds'] != after['allocation_bounds'],
        'acceptance': 'not_evaluated'}


def render_text(report):
    project = report.get('project') or {}
    lines = ['Concept coverage: ' + report['status'] + '.',
        'Project: ' + project.get('name', 'unresolved'), 'Question: ' + project.get('question', 'unresolved'),
        'Boundary: ' + project.get('boundary', 'unresolved'),
        'Workflow checks: ' + report['workflow_status'] + '; allocation counts: ' + report['allocation_status'] + '.']
    record = report.get('workflow', {}).get('record') or {}
    elements = record.get('elements', {})
    for walk in report['walks'].values():
        scenario = elements.get(walk['scenario'], {}).get('label', walk['scenario'])
        functions = [elements.get(k, {}).get('label', k) for k in walk['functions']]
        lines.append('Expected walk: ' + scenario + ' — ' + ' -> '.join(functions) + ' (documentary).')
    for key, plan in record.get('evidence', {}).items():
        lines.append('Evaluation ' + key + ': ' + plan['purpose'] + ', ' + plan['mode'] + ', result ' + plan['result'] + '.')
    if report.get('human_tasks'):
        lines.append('Human-task review: ' + report['human_task_status'] + '; documentary facts, no workload execution.')
        for task in report['human_tasks']['tasks'].values():
            people=', '.join(elements.get(p['element'],{}).get('label',p['element'])+' ('+p['role']+', '+p['allocation']+')' for p in task['performers'])
            states=sorted({f['status'] for f in task['selected_facts'].values()})
            lines.append('  '+task['label']+': '+people+'; fact status '+', '.join(states)+'.')
    if report.get('ownership'):
        lines.append('Ownership/agreement review: '+report['ownership_status']+'; declared roles, actual commitments not authenticated.')
        for target,item in report['ownership']['items'].items():
            label=elements.get(target,{}).get('label',target)
            roles='; '.join(role+': '+', '.join(elements.get(p,{}).get('label',p) for p in claim['parties'])+' ('+claim['status']+')' for role,claim in item['roles'].items())
            lines.append('  '+label+' — '+roles+'.')
    native_seen=set();native_printed=0
    native_total=sum(f['rule']=='native_parser' for f in report['findings'])
    for finding in report['findings']:
        if finding['rule']=='native_parser':
            identity=(finding.get('source'),finding.get('line'),finding['detail'])
            if identity in native_seen or native_printed>=8:continue
            native_seen.add(identity);native_printed+=1
        location=(' '+str(finding['source'])+(':'+str(finding['line']) if 'line' in finding else '')) if finding.get('source') else ''
        lines.append(f"  {finding['status']} {finding['rule']}{location} [{', '.join(finding['ids'])}]: {finding['detail']}")
    if native_total>native_printed:
        lines.append(f'  {native_total-native_printed} further native parser diagnostics; use --json for complete details.')
    lines += ['Model SHA-256: ' + str(report['model_sha256']), 'Scope SHA-256: ' + str(report['scope_sha256']),
        'Behavior not run; engineering acceptance not evaluated.'] + report['limits']
    return '\n'.join(lines) + '\n'
