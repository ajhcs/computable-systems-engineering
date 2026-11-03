"""Check authored native/finite correspondence; never execute native behavior."""
from copy import deepcopy
import json
from pathlib import Path
import re
import tempfile

from .core import digest, _pairs, _validate
from .foundation import Invalid, _object, read_regular
from .function_flow import analyze, schema as flow_schema, OBLIGATIONS
from .sysml import check_sysml, CACHE
from .workflow import (capture_model_inputs, schema as workflow_schema,
                       MARKER, COMPOSED_MARKER, KINDS)

VERSION = 'function-native-1.0'
ID = re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,63}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')
RELATIONS = {'allocated_to': ({'function'}, {'system', 'element'}),
             'decomposes': ({'function', 'system', 'element'}, {'function', 'system', 'element'}),
             'precedes': ({'step'}, {'step'}),
             'information_to': ({'function', 'system', 'element'}, {'function', 'system', 'element'})}


def _map(value, where):
    if type(value) is not dict or len(value) > 128 or any(type(k) is not str or not ID.fullmatch(k) for k in value):
        raise Invalid(where + ' needs an ID map of at most 128 items')


def _text(value, where):
    if type(value) is not str or not value.strip() or len(value) > 4096:
        raise Invalid(where + ' needs bounded nonempty text')


def _ref(value, where):
    _object(value, ('kind', 'native_name', 'element'), where, required=('kind', 'native_name'))
    for key in value:
        _text(value[key], where + '.' + key)


def schema(binding):
    _object(binding, ('version', 'native_model_sha256', 'function_flow_sha256', 'functions', 'parties',
                      'scenarios', 'steps', 'data', 'properties', 'relations'), 'native binding')
    if binding['version'] != VERSION:
        raise Invalid('Unsupported native/finite binding version')
    for field in ('native_model_sha256', 'function_flow_sha256'):
        if type(binding[field]) is not str or not SHA.fullmatch(binding[field]):
            raise Invalid(field + ' needs a lowercase SHA-256')
    for group in ('functions', 'parties', 'scenarios', 'steps', 'data', 'properties', 'relations'):
        _map(binding[group], group)
    for group in ('functions', 'parties'):
        for key, ref in binding[group].items():
            _ref(ref, group + '.' + key)
    for key, refs in binding['scenarios'].items():
        if type(refs) is not list or not 1 <= len(refs) <= 128:
            raise Invalid('A finite scenario needs 1..128 explicit native scenario references')
        for ref in refs:
            _ref(ref, key)
        if len({digest(ref) for ref in refs}) != len(refs):
            raise Invalid('Duplicate scenario reference')
    for key, steps in binding['steps'].items():
        _map(steps, key)
        for step, ref in steps.items():
            _ref(ref, key + '.' + step)
    for group in ('data', 'properties'):
        for key, value in binding[group].items():
            _object(value, ('part', 'attribute'), group + '.' + key)
            _ref(value['part'], key + '.part'); _text(value['attribute'], key + '.attribute')
    for key, relation in binding['relations'].items():
        _object(relation, ('kind', 'from', 'to', 'label'), key)
        for field in relation:
            if field == 'label':
                if type(relation[field]) is not str or len(relation[field]) > 4096:
                    raise Invalid(key + '.label needs bounded text')
            else:
                _text(relation[field], key + '.' + field)
    return binding


def _status(findings):
    return next((s for s in ('error', 'fail', 'unsupported', 'unknown', 'not_run')
                 if any(f['status'] == s for f in findings)), 'pass')


def _workflow(inventory):
    documents = [d for d in inventory.get('documents', []) if d.get('name') == 'cseWorkflow']
    if not documents:
        return None
    if len(documents) != 1 or sum(c.get('qualified_name') == documents[0].get('owner')
                                  for c in inventory.get('concerns', [])) != 1:
        raise Invalid('Selected workflow metadata needs exactly one cseWorkflow document on a parsed concern')
    lines = documents[0]['body'].strip().splitlines()
    if not lines or lines[0].strip() not in (MARKER, COMPOSED_MARKER):
        raise Invalid('Unsupported selected workflow document header')
    payload = '\n'.join(lines[1:])
    if len(payload.encode('utf-8')) > 1_000_000:
        raise Invalid('Selected workflow document exceeds 1 MB')
    record = json.loads(payload, object_pairs_hook=_pairs,
                        parse_constant=lambda x: (_ for _ in ()).throw(Invalid('Nonfinite workflow data')))
    workflow_schema(record)
    if (lines[0].strip() == COMPOSED_MARKER) != (record['version'] == 'workflow-1.1'):
        raise Invalid('Workflow document marker/version mismatch')
    return record


def _correspondence(record, binding, inventory):
    findings, resolved = [], []
    model = record['finite_model']
    needs_workflow = bool(binding['relations']) or any('element' in ref for group in ('functions', 'parties')
        for ref in binding[group].values()) or any('element' in ref for refs in binding['scenarios'].values() for ref in refs)
    needs_workflow = needs_workflow or any('element' in ref for steps in binding['steps'].values() for ref in steps.values())
    needs_workflow = needs_workflow or any('element' in item['part'] for group in ('data', 'properties') for item in binding[group].values())
    workflow = _workflow(inventory) if needs_workflow else None

    def issue(rule, status, ids, detail, **extra):
        findings.append({'obligation': 'native_binding', 'rule': rule, 'status': status,
                         'ids': list(ids), 'detail': detail, **extra})

    def scope(actual, expected, where):
        for key in sorted(set(expected) - set(actual)):
            issue('native_mapping_missing', 'fail', [where, key], 'Every selected finite identity needs an explicit native correspondence.')
        for key in sorted(set(actual) - set(expected)):
            issue('native_mapping_extra', 'fail', [where, key], 'Mapping names an identity absent from the bound finite record.')

    def resolve(ref, allowed, ids, *, keep_mapping=True):
        if ref['kind'] not in allowed:
            issue('native_mapping_kind', 'fail', ids, 'Declared correspondence role is incompatible with this finite identity.')
            return None
        category = KINDS[ref['kind']]
        matches = [item for item in inventory.get(category, []) if item.get('qualified_name') == ref['native_name']]
        if len(matches) != 1:
            issue('native_target', 'fail', ids, 'Expected exactly one parsed native identity of the selected category.',
                  expected={'category': category, 'native_name': ref['native_name']}, actual_matches=len(matches))
            return None
        if 'element' in ref:
            element = None if workflow is None else workflow['elements'].get(ref['element'])
            if element is None or element['kind'] != ref['kind'] or element['native_name'] != ref['native_name']:
                issue('native_workflow_identity', 'fail', ids + [ref['element']], 'Existing workflow ID, role and qualified native identity must match the authored correspondence.')
                return None
        if keep_mapping:
            resolved.append({'finite_ids': ids, 'kind': ref['kind'], 'native_name': ref['native_name'],
                             'native_category': category, **({'element': ref['element']} if 'element' in ref else {})})
        return matches[0]

    groups = {'functions': (record['functions'], {'function'}), 'parties': (model.get('actors', {}), {'actor', 'system', 'element'})}
    for group, (expected, allowed) in groups.items():
        scope(binding[group], expected, group)
        names = {}
        for key in sorted(set(binding[group]) & set(expected)):
            ref = binding[group][key]
            if ref['native_name'] in names:
                issue('native_mapping_alias', 'fail', [group, names[ref['native_name']], key], 'Distinct finite identities cannot silently collapse to one native identity within this mapping group.')
            names[ref['native_name']] = key
            resolve(ref, allowed, [group, key])
    scenarios = model.get('scenarios', {})
    scope(binding['scenarios'], scenarios, 'scenarios'); scope(binding['steps'], scenarios, 'steps')
    for key in sorted(set(binding['scenarios']) & set(scenarios)):
        for ref in binding['scenarios'][key]:
            resolve(ref, {'scenario'}, ['scenarios', key])
    for key in sorted(set(binding['steps']) & set(scenarios)):
        expected = scenarios[key].get('steps', {})
        scope(binding['steps'][key], expected, 'steps.' + key)
        for step in sorted(set(binding['steps'][key]) & set(expected)):
            ref = binding['steps'][key][step]
            resolve(ref, {'step', 'function'}, ['steps', key, step])
            if ref['kind'] == 'function':
                function_id = record['step_bindings'].get(key, {}).get(step)
                function = binding['functions'].get(function_id)
                if (function is None or ref['native_name'] != function['native_name'] or
                        'element' in ref and 'element' in function and ref['element'] != function['element']):
                    issue('native_step_function', 'fail', ['steps', key, step],
                          'Function-valued step correspondence differs from the function explicitly selected by the finite step binding.')

    for group in ('data', 'properties'):
        expected = model.get(group, {})
        scope(binding[group], expected, group)
        aliases = {}
        for key in sorted(set(binding[group]) & set(expected)):
            item, declaration = binding[group][key], expected[key]
            ids = [group, key]
            part = resolve(item['part'], {'actor', 'system', 'element'}, ids, keep_mapping=False)
            attributes = [a for a in inventory.get('attributes', []) if a.get('qualified_name') == item['attribute']]
            if part is None:
                continue
            if len(attributes) != 1 or attributes[0].get('part_definition') != part.get('type'):
                issue('native_attribute', 'fail', ids, 'Attribute must be directly declared on the explicitly bound part usage type.', expected=item['attribute'])
                continue
            attribute = attributes[0]
            alias = (item['part']['native_name'], item['attribute'])
            if alias in aliases:
                issue('native_mapping_alias', 'fail', ids + [aliases[alias]], 'Distinct finite data/property identities cannot silently collapse to one native attribute within the group.')
            aliases[alias] = key
            multiplicity = part.get('multiplicity', {})
            attribute_multiplicity = attribute.get('multiplicity', {})
            definitions = [d for d in inventory.get('part_definitions', []) if d.get('qualified_name') == part.get('type')]
            part_flags = ('has_native_value', 'has_non_typing_specialization', 'is_variation', 'is_variant')
            attribute_flags = ('has_native_value', 'has_non_typing_specialization', 'is_variation', 'is_variant')
            if (part.get('types') != [part.get('type')] or len(definitions) != 1 or
                    any(type(definitions[0].get(f)) is not bool for f in ('has_specialization', 'is_variation')) or
                    any(definitions[0].get(f) for f in ('has_specialization', 'is_variation')) or
                    any(type(part.get(f)) is not bool or part[f] for f in part_flags) or
                    multiplicity.get('status') not in ('default', 'literal') or
                    multiplicity.get('lower') != 1 or multiplicity.get('upper') != 1 or
                    attribute.get('types') != [attribute.get('type')] or attribute_multiplicity.get('status') not in ('default', 'literal') or
                    attribute_multiplicity.get('lower') != 1 or attribute_multiplicity.get('upper') != 1 or
                    any(type(attribute.get(f)) is not bool or attribute[f] for f in attribute_flags)):
                issue('native_attribute_semantics', 'unsupported', ids, 'Only direct, single-instance, unspecialized part attributes without native values are admitted.')
                continue
            if attribute.get('type') != 'ScalarValues::Boolean' or declaration.get('type') != 'bool':
                issue('native_attribute_type', 'unsupported', ids, 'This binding slice admits only direct ScalarValues::Boolean to finite bool; quantity/enum/domain conversion is not inferred.')
                continue
            if group == 'properties':
                expected_direction = {'input': 'in', 'controlled': 'out'}[declaration['owner']]
                if attribute.get('direction') != expected_direction:
                    issue('native_property_direction', 'fail', ids, 'Finite property owner must match its explicit native in/out direction.', expected=expected_direction, actual=attribute.get('direction'))
            resolved.append({'finite_ids': ids, 'native_name': part['qualified_name'] + '::' + attribute['name'],
                             'attribute_definition': attribute['qualified_name'], 'native_type': attribute['type'],
                             'finite_type': 'bool', 'native_direction': attribute.get('direction')})

    for key, expected in sorted(binding['relations'].items()):
        if expected['kind'] not in RELATIONS:
            issue('native_relation_semantics', 'unsupported', [key], 'Selected documentary relation kind is outside this correspondence slice.')
            continue
        actual = None if workflow is None else workflow['relations'].get(key)
        if actual is None or any(actual[field] != expected[field] for field in expected):
            issue('native_relation_changed', 'fail', [key], 'Selected existing documentary relation is absent or changed.', expected=expected,
                  actual=None if actual is None else {f: actual[f] for f in expected})
            continue
        left, right = (workflow['elements'].get(expected[f]) for f in ('from', 'to'))
        allowed = RELATIONS[expected['kind']]
        if left is None or right is None or left['kind'] not in allowed[0] or right['kind'] not in allowed[1] or (expected['kind'] == 'decomposes' and left['kind'] != right['kind']):
            issue('native_relation_kind', 'fail', [key], 'Selected documentary relation has incompatible endpoint roles.')
            continue
        for field, element in (('from', left), ('to', right)):
            resolve({'kind': element['kind'], 'native_name': element['native_name'], 'element': expected[field]},
                    allowed[0 if field == 'from' else 1], ['relations', key, expected[field]])
    return findings, resolved


def inspect(record, binding, model_paths):
    """Capture native bytes, check explicit mappings, then run existing finite checks."""
    native_findings, resolved = [], []
    record_hash = None
    metadata = {'version': VERSION, 'status': 'not_run', 'model_files': [], 'mapping': [],
                'claim_scope': 'native_identity_type_and_authored_correspondence', 'native_execution': 'unsupported'}

    def issue(rule, status, detail, **extra):
        native_findings.append({'obligation': 'native_binding', 'rule': rule, 'status': status, 'ids': [], 'detail': detail, **extra})

    def blocked():
        metadata.update(status=_status(native_findings), mapping=resolved)
        return {'checker_version': VERSION, 'status': metadata['status'], 'findings': native_findings,
                'native_binding': metadata, 'artifact_sha256': record_hash,
                'expected_obligations': ['native_binding', *OBLIGATIONS], 'completed_obligations': [],
                'obligations': {'native_binding': metadata['status'], **{o: 'not_run' for o in OBLIGATIONS}},
                'finite_execution': 'not_run'}

    try:
        record_hash = digest(record)
        record, binding = deepcopy(record), deepcopy(binding)
        if type(binding) is dict and binding.get('version') != VERSION:
            issue('native_binding_profile', 'unsupported', 'Unsupported native/finite binding version.')
            return blocked()
        schema(binding); flow_schema(record)
        metadata['binding_sha256'] = digest(binding)
        if record_hash != binding['function_flow_sha256']:
            issue('native_finite_revision', 'fail', 'The bound function-flow record changed; reconcile the authored correspondence.',
                  expected=binding['function_flow_sha256'], actual=record_hash)
            return blocked()
        _, invalid = _validate(record['finite_model'], ())
        if invalid:
            for f in invalid:
                native_findings.append({'obligation': 'native_binding', 'rule': 'finite.' + f['rule'], 'status': f['status'], 'ids': f['ids'], 'detail': f['explanation']})
            return blocked()
        captured, files, model_hash = capture_model_inputs(model_paths)
        metadata.update(model_sha256=model_hash, model_files=files)
        if model_hash != binding['native_model_sha256']:
            issue('native_source_revision', 'fail', 'Native source revision differs from the retained correspondence.',
                  expected=binding['native_model_sha256'], actual=model_hash)
            return blocked()
        directory = CACHE / 'function-native-scratch'
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if directory.is_symlink():
            raise Invalid('Native binding scratch directory must not be a symlink')
        with tempfile.TemporaryDirectory(prefix='binding-', dir=directory) as temp:
            snapshots = []
            for index, (_, raw) in enumerate(captured):
                path = Path(temp) / f'{index:03d}.sysml'; path.write_bytes(raw); path.chmod(0o600); snapshots.append(path)
            _, snapshot_files, snapshot_hash = capture_model_inputs(snapshots)
            source_map = {label: original['path'] for path, snapshot, original in zip(snapshots, snapshot_files, files)
                          for label in (str(path), snapshot['path'])}
            native = check_sysml(snapshots, syntax_only=True)
        metadata['parser_status'] = native.get('status', 'error')
        if native.get('model_sha256') != snapshot_hash:
            issue('native_parser_revision', 'error', 'Parser receipt does not match captured native source bytes.')
        elif native.get('status') != 'pass':
            status = native.get('status') if native.get('status') in ('fail', 'error', 'unknown', 'unsupported', 'not_run') else 'error'
            issue('native_parser', status, 'Native parsing/linking did not pass; finite execution remains blocked.')
            metadata['parser_findings'] = [{**item, **({'source': source_map.get(item['source'], item['source'])}
                if 'source' in item else {})} for item in (native.get('findings', []) + native.get('parser_issues', []))[:8]]
        else:
            native_findings, resolved = _correspondence(record, binding, native['inventory'])
        if any(read_regular(path, 5_000_000) != raw for path, raw in captured):
            issue('native_inputs_changed', 'error', 'Native model bytes changed during correspondence checking.')
        if native_findings:
            return blocked()
        report = analyze(record)
        if any(read_regular(path, 5_000_000) != raw for path, raw in captured):
            issue('native_inputs_changed', 'error', 'Native model bytes changed during finite checking; results discarded.')
            return blocked()
        metadata.update(status='pass', mapping=resolved,
                        summary={group: len(binding[group]) for group in ('functions', 'parties', 'scenarios', 'data', 'properties', 'relations')})
        metadata['summary']['steps'] = sum(len(steps) for steps in binding['steps'].values())
        report['native_binding'] = metadata
        report['expected_obligations'] = ['native_binding', *report['expected_obligations']]
        report['completed_obligations'] = ['native_binding', *report['completed_obligations']]
        report['obligations']['native_binding'] = 'pass'
        for finding in report['findings']:
            affected = set(finding['ids']) | set(finding.get('evidence', {}).get('path', []))
            finding['related_native_ids'] = sorted({m['native_name'] for m in resolved if m['finite_ids'][-1] in affected})
        return report
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError, RuntimeError) as exc:
        issue('native_binding_input', 'error', str(exc)[:500])
        return blocked()
    finally:
        native_findings.sort(key=lambda f: (f['rule'], f['ids'], f['detail']))
