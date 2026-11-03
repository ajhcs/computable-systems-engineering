"""Bounded observation summaries; computed scores do not establish acceptance.

Source-informed formulas and boundaries are credited in observation-validation.md.
The runtime uses exact rational arithmetic and contains no upstream source code.
"""
from fractions import Fraction
from hashlib import sha256
import json
from math import comb

from .core import ID, _pairs, digest, finding
from .foundation import read_regular
from . import calculations

VERSION = 'observation-validation-1.0'
LIMITS = {'input_bytes': 262144, 'tree_nodes': 12000, 'tree_depth': 16,
          'text_characters': 2048, 'checks': 32, 'rows_per_check': 512,
          'assumptions': 32, 'binomial_trials': 256, 'rational_bits': 4096,
          'findings': 64}
SEVERITY = {'pass': 0, 'unknown': 1, 'unsupported': 2, 'fail': 3, 'error': 4}
KINDS = {'sample_alignment', 'central_interval', 'held_out_separation',
         'weight_meaning', 'independent_trials', 'common_probability', 'binary_outcome'}


class Invalid(ValueError):
    pass


def _object(value, fields, where):
    if type(value) is not dict or set(value) != set(fields):
        raise Invalid(where + ' needs exactly the documented fields')


def _text(value, where):
    if type(value) is not str or not value.strip() or len(value) > LIMITS['text_characters']:
        raise Invalid(where + ' needs bounded nonempty text')


def _id(value):
    if type(value) is not str or not ID.fullmatch(value):
        raise Invalid('Use a stable ASCII engineering identifier')


def _tree(value, budget=None, depth=0):
    budget = [0] if budget is None else budget
    budget[0] += 1
    if budget[0] > LIMITS['tree_nodes'] or depth > LIMITS['tree_depth']:
        raise Invalid('Observation record exceeds tree limits')
    if type(value) is str:
        if len(value) > LIMITS['text_characters']:
            raise Invalid('Observation text exceeds its limit')
    elif type(value) in (dict, list):
        if len(value) > LIMITS['rows_per_check']:
            raise Invalid('Observation collection exceeds its limit')
        if type(value) is dict:
            for key in value:
                _text(key, 'key')
            children = value.values()
        else:
            children = value
        for child in children:
            _tree(child, budget, depth + 1)
    elif value is not None and type(value) not in (bool, int):
        raise Invalid('Numbers must be exact strings; binary floats are refused')


def load(path):
    raw = read_regular(path, LIMITS['input_bytes'])
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(Invalid('Nonfinite JSON value')))
    return value, sha256(raw).hexdigest()


def _sum(values):
    result = Fraction(0)
    for value in values:
        result = calculations._bounded(result + value)
    return result


def _product(left, right):
    return calculations._bounded(left * right)


def _ratio(left, right):
    return calculations._bounded(left / right)


def _rows(raw, fields):
    if type(raw) is not list or not 1 <= len(raw) <= LIMITS['rows_per_check']:
        raise Invalid('rows needs 1 to 512 explicitly aligned observations')
    ids, rows = set(), []
    for row in raw:
        _object(row, ('id',) + fields, 'row')
        _id(row['id'])
        if row['id'] in ids:
            raise Invalid('Observation row identifiers must be unique within a check')
        ids.add(row['id'])
        rows.append((row['id'], *(calculations._number(row[field]) for field in fields)))
    return rows


def _interval(item, unit):
    _object(item, ('kind', 'purpose', 'alpha', 'rows', 'assumptions'), 'interval check')
    if item['purpose'] not in ('descriptive', 'held_out_validation'):
        raise Invalid('interval purpose needs descriptive or held_out_validation')
    alpha = calculations._number(item['alpha'])
    if not 0 < alpha < 1:
        raise Invalid('alpha must be strictly between zero and one')
    rows = _rows(item['rows'], ('actual', 'lower', 'upper'))
    if any(lower > upper for _, _, lower, upper in rows):
        raise Invalid('Interval endpoints must be ordered; reversed intervals are not repaired')
    n = len(rows)
    below = [key for key, actual, lower, _ in rows if actual < lower]
    above = [key for key, actual, _, upper in rows if actual > upper]
    widths = [calculations._bounded(upper - lower) for _, _, lower, upper in rows]
    scores = []
    for (_, actual, lower, upper), width in zip(rows, widths):
        distance = lower - actual if actual < lower else actual - upper if actual > upper else Fraction(0)
        scores.append(calculations._bounded(width + _ratio(_product(Fraction(2), distance), alpha)))
    coverage = Fraction(n - len(below) - len(above), n)
    return {'n': n, 'covered': n - len(below) - len(above),
            'coverage': str(coverage), 'nominal_coverage': str(1 - alpha),
            'coverage_minus_nominal': str(coverage - (1 - alpha)),
            'mean_width': str(_ratio(_sum(widths), n)),
            'mean_interval_score': str(_ratio(_sum(scores), n)), 'unit': dict(unit),
            'below_ids': below, 'above_ids': above, 'endpoints': 'closed',
            'interpretation': item['purpose']}


def _weighted(item, unit):
    _object(item, ('kind', 'rows', 'assumptions'), 'weighted_summary check')
    rows = _rows(item['rows'], ('value', 'weight'))
    if any(weight < 0 for _, _, weight in rows):
        raise Invalid('Weights must be nonnegative')
    total = _sum(weight for _, _, weight in rows)
    if total == 0:
        raise Invalid('Total weight must be positive')
    mean = _ratio(_sum(_product(value, weight) for _, value, weight in rows), total)
    variance = _ratio(_sum(_product(_product(calculations._bounded(value - mean),
                                             calculations._bounded(value - mean)), weight)
                           for _, value, weight in rows), total)
    squared = _sum(_product(weight, weight) for _, _, weight in rows)
    return {'n': len(rows), 'positive_weight_rows': sum(weight > 0 for _, _, weight in rows),
            'total_weight': str(total), 'mean': str(mean),
            'population_variance': str(variance),
            'weight_effective_size': str(_ratio(_product(total, total), squared)),
            'mean_unit': dict(unit), 'variance_unit': dict(calculations._combine(unit, unit)),
            'interpretation': 'weighted_descriptive_population_moments',
            'independent_sample_size': 'not_established'}


def _binomial(item):
    _object(item, ('kind', 'n', 'k', 'probability', 'tail', 'assumptions'), 'binomial_tail check')
    n, k = item['n'], item['k']
    if type(n) is not int or type(k) is not int or not 1 <= n <= LIMITS['binomial_trials'] or not 0 <= k <= n:
        raise Invalid('Binomial bounds require integer 1 <= n <= 256 and 0 <= k <= n')
    p = calculations._number(item['probability'])
    if not 0 <= p <= 1 or item['tail'] not in ('le', 'ge'):
        raise Invalid('Binomial probability needs [0,1] and tail needs le or ge')
    # Bound work and rational growth before exponentiation, including 1-p.
    q = 1 - p
    bits = max(p.numerator.bit_length(), p.denominator.bit_length(), q.numerator.bit_length())
    if n * (bits + 1) + n > LIMITS['rational_bits']:
        raise calculations.Issue('unknown', 'validation_numeric_limit', 'Binomial rational growth exceeds its conservative limit')
    indices = range(k + 1) if item['tail'] == 'le' else range(k, n + 1)
    terms = [_product(Fraction(comb(n, i)), _product(p ** i, q ** (n - i))) for i in indices]
    return {'n': n, 'k': k, 'probability': str(p), 'tail': item['tail'],
            'tail_probability': str(_sum(terms)), 'terms_completed': len(terms), 'unit': {},
            'interpretation': 'conditional_iid_bernoulli_probability',
            'confidence_interval': 'not_computed', 'coverage_guarantee': 'not_established'}


def analyze(record, required_checks=None):
    report = {'checker_version': VERSION, 'status': 'error',
              'claim_scope': 'bounded_observation_computation', 'limits': LIMITS.copy(),
              'findings': [], 'checks': {}, 'expected_checks': [],
              'computed_checks': [], 'completed_checks': [],
              'acceptance': 'not_evaluated', 'source_truth': 'not_evaluated',
              'simulation_fidelity': 'not_evaluated', 'future_coverage': 'not_established',
              'assumption_truth': 'not_evaluated', 'external_scope': 'not_evaluated'}
    # Verdict state is independent of the bounded diagnostic presentation. A
    # later check must retain its failures even after the report reaches its cap.
    states = []

    def issue(rule, status, ids=(), detail=''):
        states.append(status)
        if len(report['findings']) < LIMITS['findings'] - 1:
            report['findings'].append(finding(rule, status, ids, detail))
        elif len(report['findings']) == LIMITS['findings'] - 1:
            report['findings'].append(finding('validation_diagnostic_limit', 'unknown', (), 'Diagnostic limit reached; review is incomplete'))
            states.append('unknown')

    def known(value, where):
        if value is None:
            issue('validation_unknown', 'unknown', [where], 'Required documentary context is explicitly unknown')
        else:
            _text(value, where)

    try:
        _tree(record)
        _object(record, ('version', 'id', 'revision', 'measure', 'dataset', 'assumptions', 'checks', 'unknowns'), 'record')
        if record['version'] != VERSION:
            issue('validation_version', 'unsupported', (), 'Unsupported observation validation version')
            report['status'] = 'unsupported'
            return report
        _id(record['id']); _text(record['revision'], 'revision')
        report.update(id=record['id'], revision=record['revision'], record_sha256=digest(record))
        measure = record['measure']
        _object(measure, ('id', 'revision', 'unit'), 'measure')
        _id(measure['id']); known(measure['revision'], 'measure.revision')
        unit = calculations._unit(measure['unit'])
        report['measure'] = measure.copy()
        dataset = record['dataset']
        _object(dataset, ('id', 'revision', 'population', 'boundary', 'window', 'sampling', 'role', 'basis'), 'dataset')
        _id(dataset['id'])
        for field in ('revision', 'population', 'boundary', 'window', 'sampling', 'basis'):
            known(dataset[field], 'dataset.' + field)
        if dataset['role'] not in ('held_out', 'training', 'calibration', 'simulation', None):
            raise Invalid('Dataset role needs held_out, training, calibration, simulation or null')
        known(dataset['role'], 'dataset.role')
        report['dataset'] = dataset.copy()
        assumptions = record['assumptions']
        if type(assumptions) is not dict or len(assumptions) > LIMITS['assumptions']:
            raise Invalid('assumptions needs a bounded ID map')
        for key, assumption in assumptions.items():
            _id(key); _object(assumption, ('kind', 'text', 'basis'), 'assumption')
            if assumption['kind'] not in KINDS:
                issue('validation_assumption_kind', 'unsupported', [key], 'Unsupported assumption kind')
            _text(assumption['text'], 'assumption.text')
            if assumption['basis'] is not None:
                _text(assumption['basis'], 'assumption.basis')
        checks = record['checks']
        if type(checks) is not dict or not 1 <= len(checks) <= LIMITS['checks']:
            raise Invalid('checks needs 1 to 32 named checks')
        if required_checks is not None and type(required_checks) is not list:
            raise Invalid('Required scope needs an explicit list of check identifiers')
        expected = list(checks) if required_checks is None else required_checks.copy()
        if not expected or len(expected) > LIMITS['checks'] or len(expected) != len(set(expected)):
            raise Invalid('Required scope needs bounded unique check identifiers')
        for key in expected:
            _id(key)
        report['expected_checks'] = sorted(expected)
        report['external_scope'] = 'caller_selected' if required_checks is not None else 'not_evaluated'
        for key in sorted(set(expected) - set(checks)):
            issue('validation_required_missing', 'fail', [key], 'An expected observation check is absent')
        for key, item in sorted(checks.items()):
            _id(key)
            start = len(states)
            result = {'status': 'error', 'assumptions': []}
            report['checks'][key] = result
            try:
                if type(item) is not dict:
                    raise Invalid('check needs an object')
                kind = item.get('kind')
                if kind not in ('interval', 'weighted_summary', 'binomial_tail'):
                    issue('validation_check_kind', 'unsupported', [key], 'Unsupported observation check kind')
                    result['status'] = 'unsupported'
                    continue
                refs = item.get('assumptions')
                if type(refs) is not list or len(refs) > LIMITS['assumptions'] or any(type(ref) is not str for ref in refs) or len(set(refs)) != len(refs):
                    raise Invalid('check.assumptions needs unique bounded assumption identifiers')
                declared_kinds = set()
                for ref in refs:
                    _id(ref)
                    if ref not in assumptions:
                        issue('validation_assumption_missing', 'fail', [key, ref], 'Referenced assumption is undeclared')
                    else:
                        declared_kinds.add(assumptions[ref]['kind'])
                        if assumptions[ref]['basis'] is None:
                            issue('validation_assumption_unknown', 'unknown', [key, ref], 'Selected assumption basis is unknown')
                needed = {'sample_alignment', 'central_interval'} if kind == 'interval' else {'weight_meaning'} if kind == 'weighted_summary' else {'independent_trials', 'common_probability', 'binary_outcome'}
                if kind == 'interval' and item.get('purpose') == 'held_out_validation':
                    needed.add('held_out_separation')
                    if dataset['role'] != 'held_out':
                        issue('validation_holdout_role', 'unknown', [key], 'Held-out validation requires an explicitly held_out dataset')
                for missing in sorted(needed - declared_kinds):
                    issue('validation_applicability_missing', 'unknown', [key, missing], 'Needed applicability assumption is not selected')
                result['assumptions'] = refs.copy()
                result['metrics'] = (_interval(item, unit) if kind == 'interval' else
                                     _weighted(item, unit) if kind == 'weighted_summary' else _binomial(item))
                report['computed_checks'].append(key)
            except calculations.Issue as exc:
                issue(exc.rule, exc.status, [key], str(exc))
            except (ValueError, TypeError, KeyError, OverflowError):
                issue('validation_check_schema', 'error', [key], 'Malformed, undefined or out-of-limit observation check')
            result['status'] = max(states[start:], key=SEVERITY.get, default='pass')
            if result['status'] in ('pass', 'fail'):
                report['completed_checks'].append(key)
        if type(record['unknowns']) is not list or len(record['unknowns']) > LIMITS['assumptions']:
            raise Invalid('unknowns needs a bounded list')
        for unknown in record['unknowns']:
            _object(unknown, ('field', 'question'), 'unknown')
            _text(unknown['field'], 'unknown.field'); _text(unknown['question'], 'unknown.question')
            issue('validation_open_question', 'unknown', [unknown['field']], unknown['question'])
    except calculations.Issue as exc:
        issue(exc.rule, exc.status, (), str(exc))
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
        issue('validation_schema', 'error', (), 'Malformed or out-of-limit observation record; use the documented contract')
    report['status'] = max(states, key=SEVERITY.get, default='pass')
    return report


def render_text(report):
    lines = [report['checker_version'] + ': ' + report['status'],
             'Scope: ' + report['claim_scope']]
    for key, result in sorted(report.get('checks', {}).items()):
        lines.append(key + ': ' + result['status'])
        if 'metrics' in result:
            lines.append('  ' + json.dumps(result['metrics'], sort_keys=True))
    for item in report.get('findings', [])[:12]:
        lines.append(item['status'] + ' ' + item['rule'] + ': ' + item['explanation'])
    lines.append('Engineering acceptance and future coverage are not established.')
    return '\n'.join(lines)
