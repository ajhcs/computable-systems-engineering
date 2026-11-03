"""Versioned measure definitions, not observation or statistical validation.

Structured formulas reuse the existing bounded arithmetic parser. This module
does not execute formulas, infer prose meaning, or approve measurement methods.
"""
from hashlib import sha256
import json

from .core import ID, _pairs, digest, finding
from .foundation import read_regular
from . import calculations

VERSION = 'measure-definitions-1.0'
LIMITS = {'input_bytes': 262144, 'tree_nodes': 4096, 'tree_depth': 24,
          'text_characters': 2048, 'items_per_group': 64, 'inputs': 32,
          'findings': 64}
FIELDS = ('quantity', 'scale', 'inputs', 'formula', 'unit', 'population',
          'boundary', 'aggregation', 'exclusions', 'window', 'sampling',
          'conditions', 'uncertainty')
SCALES = ('nominal', 'ordinal', 'interval', 'ratio')
METHODS = ('identity', 'count', 'sum', 'mean', 'median', 'mode', 'proportion', 'rate')
SEVERITY = {'pass': 0, 'unknown': 1, 'unsupported': 2, 'fail': 3, 'error': 4}


class Invalid(ValueError):
    pass


def _object(value, fields, where):
    if type(value) is not dict or set(value) != set(fields):
        raise Invalid(where + ' needs exactly the documented fields')


def _text(value, where):
    if type(value) is not str or not value.strip() or len(value) > LIMITS['text_characters']:
        raise Invalid(where + ' needs bounded nonempty text')


def _id(value, where):
    if type(value) is not str or not ID.fullmatch(value):
        raise Invalid(where + ' needs a stable identifier')


def _tree(value, budget=None, depth=0):
    budget = [0] if budget is None else budget
    budget[0] += 1
    if budget[0] > LIMITS['tree_nodes'] or depth > LIMITS['tree_depth']:
        raise Invalid('Definition exceeds the tree node or nesting limit')
    if type(value) is str:
        if len(value) > LIMITS['text_characters']:
            raise Invalid('Definition text exceeds the character limit')
    elif type(value) in (dict, list):
        if len(value) > LIMITS['items_per_group']:
            raise Invalid('Definition exceeds the group item limit')
        if type(value) is dict:
            for key in value:
                if type(key) is not str or len(key) > LIMITS['text_characters']:
                    raise Invalid('Object keys need bounded text')
            children = value.values()
        else:
            children = value
        for child in children:
            _tree(child, budget, depth + 1)
    elif value is not None and type(value) not in (int, bool):
        raise Invalid('Definition values must be JSON objects, lists, strings, integers, booleans or null')


def load(path):
    raw = read_regular(path, LIMITS['input_bytes'])
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(Invalid('Nonfinite JSON value')))
    return value, sha256(raw).hexdigest()


def _report(scope):
    return {'checker_version': VERSION, 'status': 'error', 'claim_scope': scope,
            'limits': LIMITS.copy(), 'findings': [], 'acceptance': 'not_evaluated',
            'observation_comparability': 'not_evaluated', 'formula_evaluation': 'not_run',
            'source_validation': 'not_evaluated', 'meaning_validation': 'not_evaluated'}


def check(record):
    report = _report('declared_measure_definition_structure_and_formula_units')

    def issue(rule, status, ids=(), detail=''):
        # Reserve the last diagnostic for a visible incomplete-check finding.
        if len(report['findings']) < LIMITS['findings'] - 1:
            report['findings'].append(finding(rule, status, ids, detail))
        elif len(report['findings']) == LIMITS['findings'] - 1:
            report['findings'].append(finding('measure_diagnostic_limit', 'unknown', (),
                                             'Diagnostic limit reached; definition check is incomplete'))

    def known(value, field):
        if value is None:
            issue('measure_unknown', 'unknown', [field], 'Definition field is explicitly unknown')
            return False
        return True

    def strings(value, field):
        if not known(value, field):
            return
        if type(value) is not list:
            raise Invalid(field + ' needs a list of text, or null')
        for item in value:
            _text(item, field)
        if len(value) != len(set(value)):
            raise Invalid(field + ' contains duplicate entries')

    try:
        _tree(record)
        _object(record, ('version', 'id', 'revision', 'label', 'definition', 'sources', 'unknowns', 'links'), 'Measure')
        if record['version'] != VERSION:
            issue('measure_version', 'unsupported', (), 'Unsupported measure definition version')
            report['status'] = 'unsupported'
            return report
        _id(record['id'], 'id'); _text(record['revision'], 'revision'); _text(record['label'], 'label')
        report.update(id=record['id'], revision=record['revision'])
        definition = record['definition']
        _object(definition, FIELDS, 'definition')
        # Retain exact deltas even when a later formula or source check fails.
        report.update(record_sha256=digest(record), definition_sha256=digest(definition))
        for field in ('quantity', 'population', 'boundary', 'window', 'sampling', 'uncertainty'):
            if known(definition[field], field):
                _text(definition[field], field)
        for field in ('conditions', 'exclusions'):
            strings(definition[field], field)
        if known(definition['scale'], 'scale') and definition['scale'] not in SCALES:
            raise Invalid('scale needs nominal, ordinal, interval or ratio')
        aggregation = definition['aggregation']
        if known(aggregation, 'aggregation'):
            _object(aggregation, ('method', 'basis'), 'aggregation')
            _text(aggregation['method'], 'aggregation.method')
            if aggregation['method'] not in METHODS:
                issue('measure_aggregation', 'unsupported', ['aggregation'], 'Aggregation method is outside the declared method vocabulary')
            if known(aggregation['basis'], 'aggregation.basis'):
                _text(aggregation['basis'], 'aggregation.basis')
            method, scale = aggregation['method'], definition['scale']
            if ((scale == 'nominal' and method not in ('identity', 'mode')) or
                    (scale == 'ordinal' and method not in ('identity', 'mode', 'median')) or
                    (scale == 'interval' and method not in ('identity', 'mode', 'median', 'mean'))):
                issue('measure_scale_operation', 'unsupported', ['aggregation', 'scale'],
                      'Aggregation is not supported for the declared output scale; counts/rates need their own ratio quantity')
        inputs = definition['inputs']
        inputs_ready = known(inputs, 'inputs')
        if inputs_ready:
            if type(inputs) is not dict or len(inputs) > LIMITS['inputs']:
                raise Invalid('inputs needs at most 32 explicit variable declarations')
            for key, item in sorted(inputs.items()):
                _id(key, 'input'); _object(item, ('quantity', 'unit', 'scale'), 'input')
                if known(item['quantity'], 'inputs.' + key + '.quantity'):
                    _text(item['quantity'], 'input.quantity')
                if known(item['unit'], 'inputs.' + key + '.unit'):
                    calculations._unit(item['unit'])
                else:
                    inputs_ready = False
                if known(item['scale'], 'inputs.' + key + '.scale'):
                    if item['scale'] not in SCALES:
                        raise Invalid('input.scale needs a documented measurement scale')
                else:
                    inputs_ready = False
        unit_ready = known(definition['unit'], 'unit')
        if unit_ready:
            calculations._unit(definition['unit'])
        formula_ready = known(definition['formula'], 'formula')
        if inputs_ready and unit_ready and formula_ready:
            expr = calculations._expression(definition['formula'], inputs)
            if expr.unit != calculations._unit(definition['unit']):
                issue('measure_formula_units', 'fail', ['formula', 'unit'], 'Formula output and declared measure units differ; no conversion is inferred')
            # Affine offsets and category arithmetic need a separate supported method.
            if expr.op != 'ref' and any(inputs[key]['scale'] != 'ratio' for key in expr.refs):
                issue('measure_formula_scale', 'unsupported', ['formula'], 'Arithmetic on nominal, ordinal or interval inputs is not supported in this definition checker')
            if expr.op != 'ref' and definition['scale'] is not None and definition['scale'] != 'ratio':
                issue('measure_formula_scale', 'unsupported', ['formula', 'scale'], 'Arithmetic formulas require a declared ratio output in this checker')
            if expr.op == 'ref' and definition['scale'] is not None and inputs[expr.value]['scale'] != definition['scale']:
                issue('measure_formula_scale', 'fail', ['formula', 'scale'], 'Identity formula must retain its input measurement scale')
        if type(record['sources']) is not dict:
            raise Invalid('sources needs an ID map')
        if not record['sources']:
            issue('measure_source_unknown', 'unknown', ['sources'], 'Definition has no declared source basis')
        for key, source in sorted(record['sources'].items()):
            _id(key, 'source'); _object(source, ('revision', 'locator', 'basis'), 'source')
            for field in ('revision', 'locator', 'basis'):
                if known(source[field], 'sources.' + key + '.' + field):
                    _text(source[field], 'source.' + field)
        if type(record['unknowns']) is not list or type(record['links']) is not list:
            raise Invalid('unknowns and links need lists')
        for item in record['unknowns']:
            _object(item, ('field', 'question'), 'unknown')
            _text(item['field'], 'unknown.field'); _text(item['question'], 'unknown.question')
            issue('measure_open_question', 'unknown', [item['field']], item['question'])
        for item in record['links']:
            _object(item, ('kind', 'id', 'revision'), 'link')
            if item['kind'] not in ('question', 'corrective_action', 'follow_up_measure'):
                raise Invalid('link.kind needs question, corrective_action or follow_up_measure')
            _id(item['id'], 'link.id'); _text(item['revision'], 'link.revision')
    except calculations.Issue as exc:
        issue(exc.rule, exc.status, (), str(exc))
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
        issue('measure_schema', 'error', (), 'Malformed or out-of-limit measure definition; use the documented record contract')
    report['status'] = max((f['status'] for f in report['findings']), key=SEVERITY.get, default='pass')
    return report


def compare(before, after):
    report = _report('exact_declared_definition_equivalence')
    left, right = check(before), check(after)
    report.update(before=left, after=right, definition_equivalence='unknown',
                  changed_meaning_fields=[], changed_metadata_fields=[])
    if 'record_sha256' in left and 'record_sha256' in right:
        report['changed_meaning_fields'] = [field for field in FIELDS
                                           if before['definition'][field] != after['definition'][field]]
        report['changed_metadata_fields'] = [field for field in ('label', 'sources', 'links')
                                            if before[field] != after[field]]
        if report['changed_meaning_fields']:
            report['definition_equivalence'] = 'different'
    if left['status'] != 'pass' or right['status'] != 'pass':
        report['status'] = max((left['status'], right['status']), key=SEVERITY.get)
        report['findings'] = [finding('measure_comparison_incomplete', report['status'], (),
            'Both complete definition checks must pass before equivalence can succeed')]
        return report
    if before['id'] != after['id']:
        report['findings'].append(finding('measure_identity', 'fail', (), 'Definition comparison needs the same stable measure identity'))
    if before != after and before['revision'] == after['revision']:
        report['findings'].append(finding('measure_revision_reused', 'fail', [before['id']], 'Changed record reuses its previous revision'))
    if report['changed_meaning_fields']:
        report['definition_equivalence'] = 'different'
        report['findings'].append(finding('measure_definition_changed', 'fail', report['changed_meaning_fields'],
            'Declared meaning changed; preserve both versions and review the baseline comparison'))
    elif before['id'] == after['id']:
        report['definition_equivalence'] = 'equal'
    report['status'] = 'fail' if report['findings'] else 'pass'
    return report


def render_text(report):
    """A concise human view, not a replacement for the retained typed record."""
    lines = [report['status'] + ': ' + report['claim_scope']]
    if 'id' in report:
        lines.append(report['id'] + ' @ ' + report['revision'])
    if 'definition_equivalence' in report:
        lines.append('Definition equivalence: ' + report['definition_equivalence'])
        lines.append('Changed meaning: ' + (', '.join(report['changed_meaning_fields']) or 'none reported'))
        lines.append('Changed metadata: ' + (', '.join(report['changed_metadata_fields']) or 'none reported'))
    for item in report['findings'][:12]:
        lines.append(item['rule'] + ': ' + item['explanation'])
    lines.append('Observation comparability and acceptance: not evaluated.')
    return '\n'.join(lines)
