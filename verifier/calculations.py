"""Exact, bounded arithmetic and optional polynomial identities over typed JSON.

Records never contain executable code. Finite arithmetic uses Fraction; the
optional SymPy worker constructs objects from this same allowlisted tree.
"""
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import json
import operator
from pathlib import Path
import re
import subprocess
import sys

from .core import digest, finding, ID, _pairs

VERSION = 'calculations-1.0'
LIMITS = {'variables': 32, 'checks': 64, 'domain_values': 64,
          'nodes_per_expression': 128, 'depth': 16, 'exponent': 8,
          'rational_bits': 4096, 'valuations_per_check': 4096,
          'total_valuations': 16384, 'symbolic_variables': 4,
          'symbolic_terms': 512, 'symbolic_degree': 16, 'symbolic_seconds': 5}
RELATIONS = {'eq': operator.eq, 'ne': operator.ne, 'lt': operator.lt,
             'le': operator.le, 'gt': operator.gt, 'ge': operator.ge}
NUMBER = re.compile(r'-?(?:[0-9]+(?:\.[0-9]+)?|[0-9]+/[1-9][0-9]*)\Z')


class Issue(ValueError):
    def __init__(self, status, rule, message):
        self.status, self.rule = status, rule
        super().__init__(message)


def _object(value, fields, label):
    if type(value) is not dict or set(value) != set(fields):
        raise Issue('error', 'calculation_schema', label+' needs exactly '+', '.join(fields))


def _text(value, label):
    if type(value) is not str or not value.strip() or len(value) > 2048:
        raise Issue('error', 'calculation_schema', label+' needs bounded nonempty text')


def _id(value):
    if type(value) is not str or not ID.fullmatch(value):
        raise Issue('error', 'calculation_identifier', 'Invalid engineering identifier')


def _number(value):
    if type(value) is not str or len(value) > 80 or not NUMBER.fullmatch(value):
        raise Issue('error', 'calculation_number', 'Use an exact integer, decimal or rational string (at most 80 characters)')
    return _bounded(Fraction(value))


def _bounded(value):
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > LIMITS['rational_bits']:
        raise Issue('unknown', 'calculation_limit', 'Exact rational exceeds the declared bit limit')
    return value


def _unit(value):
    if type(value) is not dict or len(value) > 16:
        raise Issue('error', 'calculation_units', 'A unit is a bounded map of unit symbols to nonzero integer exponents')
    for key, exponent in value.items():
        _id(key)
        if type(exponent) is not int or not -16 <= exponent <= 16 or exponent == 0:
            raise Issue('error', 'calculation_units', 'Unit exponents must be nonzero integers between -16 and 16')
    return tuple(sorted(value.items()))


def _combine(left, right, direction=1):
    unit = dict(left)
    for key, exponent in right:
        unit[key] = unit.get(key, 0) + direction * exponent
    return _unit({key: exponent for key, exponent in unit.items() if exponent})


@dataclass(frozen=True)
class Expression:
    op: str
    value: object
    args: tuple
    unit: tuple
    refs: frozenset
    degree: int
    terms: int
    coefficient_bits: int


def _expression(raw, variables, budget=None, depth=0):
    budget = [0] if budget is None else budget
    budget[0] += 1
    if depth > LIMITS['depth'] or budget[0] > LIMITS['nodes_per_expression']:
        raise Issue('unsupported', 'calculation_limit', 'Expression exceeds the node or nesting limit')
    if type(raw) is not dict:
        raise Issue('error', 'calculation_expression', 'An expression must be an object')
    if 'number' in raw:
        _object(raw, ('number', 'unit'), 'Number')
        value = _number(raw['number'])
        return Expression('number', value, (), _unit(raw['unit']), frozenset(), 0, 1,
                          max(value.numerator.bit_length(), value.denominator.bit_length()))
    if 'ref' in raw:
        _object(raw, ('ref',), 'Reference')
        _id(raw['ref'])
        if raw['ref'] not in variables:
            raise Issue('fail', 'calculation_reference', 'Expression references an undeclared variable: '+raw['ref'])
        return Expression('ref', raw['ref'], (), _unit(variables[raw['ref']]['unit']), frozenset([raw['ref']]), 1, 1, 1)
    op = raw.get('op')
    if op not in ('add', 'sub', 'mul', 'div', 'neg', 'pow'):
        raise Issue('unsupported', 'calculation_operator', 'Unsupported structured arithmetic operation')
    _object(raw, ('op', 'args', 'exponent') if op == 'pow' else ('op', 'args'), 'Operation')
    if type(raw['args']) is not list or len(raw['args']) != (1 if op in ('neg', 'pow') else 2):
        raise Issue('error', 'calculation_expression', 'Arithmetic operation has incorrect arity')
    args = tuple(_expression(arg, variables, budget, depth+1) for arg in raw['args'])
    refs = frozenset().union(*(arg.refs for arg in args))
    unit, degree, terms, value = args[0].unit, args[0].degree, args[0].terms, None
    coefficient_bits = args[0].coefficient_bits
    if op in ('add', 'sub'):
        if unit != args[1].unit:
            raise Issue('fail', 'calculation_units', 'Addition/subtraction requires identical declared units; no conversion is inferred')
        degree, terms = max(degree, args[1].degree), terms + args[1].terms
        coefficient_bits += args[1].coefficient_bits + 1
    elif op in ('mul', 'div'):
        unit = _combine(unit, args[1].unit, 1 if op == 'mul' else -1)
        degree, terms = degree + args[1].degree, terms * args[1].terms
        coefficient_bits += args[1].coefficient_bits
    elif op == 'pow':
        value = raw['exponent']
        if type(value) is not int or abs(value) > LIMITS['exponent']:
            raise Issue('unsupported', 'calculation_exponent', 'Power requires an explicit integer exponent of absolute value at most eight')
        unit = _unit({key: exponent * value for key, exponent in unit if exponent * value})
        degree, terms = degree * abs(value), terms ** abs(value)
        coefficient_bits *= abs(value)
    return Expression(op, value, args, unit, refs, degree, min(terms, LIMITS['symbolic_terms']+1),
                      min(coefficient_bits, LIMITS['rational_bits']+1))


def _evaluate(expr, assignment):
    if expr.op == 'number':
        return expr.value
    if expr.op == 'ref':
        return assignment[expr.value]
    values = [_evaluate(arg, assignment) for arg in expr.args]
    if (expr.op == 'div' and values[1] == 0) or (expr.op == 'pow' and values[0] == 0 and expr.value <= 0):
        raise Issue('unknown', 'calculation_undefined', 'Original expression is undefined at this valuation; no cancellation or domain exclusion is inferred')
    operation = {'add': lambda: values[0]+values[1], 'sub': lambda: values[0]-values[1],
                 'mul': lambda: values[0]*values[1], 'div': lambda: values[0]/values[1],
                 'neg': lambda: -values[0], 'pow': lambda: values[0]**expr.value}
    return _bounded(operation[expr.op]())


def _polynomial(expr):
    if expr.op == 'pow' and (expr.value < 0 or (expr.value == 0 and expr.args[0].refs)):
        return False
    if expr.op == 'div' and expr.args[1].refs:
        return False
    return all(_polynomial(arg) for arg in expr.args)


def _symbolic(record, check):
    """Run optional symbolic work with a wall-time boundary and compact output."""
    job = {'variables': record['variables'], 'check': check}
    try:
        child = subprocess.run([sys.executable, '-B', '-m', 'verifier.calculations', '--symbolic-worker'],
            input=json.dumps(job), capture_output=True, text=True,
            cwd=Path(__file__).resolve().parents[1], timeout=LIMITS['symbolic_seconds'])
    except subprocess.TimeoutExpired:
        raise Issue('unknown', 'calculation_timeout', 'Optional symbolic worker exceeded its declared wall-time limit')
    except OSError as exc:
        raise Issue('error', 'calculation_worker', str(exc)) from exc
    if child.returncode:
        raise Issue('error', 'calculation_worker', 'Optional symbolic worker failed')
    try:
        result = json.loads(child.stdout, object_pairs_hook=_pairs,
                            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite worker output')))
    except (ValueError, TypeError, RecursionError) as exc:
        raise Issue('error', 'calculation_worker', 'Optional symbolic worker returned malformed JSON') from exc
    if type(result) is not dict or type(result.get('status')) is not str:
        raise Issue('error', 'calculation_worker', 'Optional symbolic worker returned no supported result object')
    status = result['status']
    if status == 'not_run':
        raise Issue('unknown', 'calculation_worker', 'Optional symbolic worker reported not_run; no identity check completed')
    if status in ('unsupported', 'error', 'unknown'):
        if (set(result) != {'status', 'rule', 'detail'} or
                any(type(result[field]) is not str or not result[field].strip() or len(result[field]) > 2048
                    for field in ('rule', 'detail'))):
            raise Issue('error', 'calculation_worker', 'Optional symbolic worker returned a malformed non-success result')
        raise Issue(status, result['rule'], result['detail'])
    fields = {'status', 'backend', 'backend_version', 'claim_scope', 'coefficient_count', 'difference'}
    if (status not in ('pass', 'fail') or set(result) != fields or result['backend'] != 'sympy' or
            type(result['backend_version']) is not str or not result['backend_version'].strip() or len(result['backend_version']) > 128 or
            result['claim_scope'] != 'polynomial_identity_over_declared_rational_or_real_domains' or
            type(result['coefficient_count']) is not int or not 0 <= result['coefficient_count'] <= LIMITS['symbolic_terms'] or
            type(result['difference']) is not str or not result['difference'].strip() or len(result['difference']) > 2048 or
            (status == 'pass') != (result['difference'] == '0')):
        raise Issue('error', 'calculation_worker', 'Optional symbolic worker returned an incomplete or inconsistent identity result')
    return result


def _symbolic_worker(job):
    try:
        import sympy as sp
    except ImportError:
        return {'status': 'unsupported', 'rule': 'calculation_dependency',
                'detail': 'Polynomial identity checking requires optional SymPy; no dependency is installed by this command'}
    variables, check = job['variables'], job['check']
    symbols = {key: sp.Symbol(key, **{variables[key]['domain']: True}) for key in variables}

    def build(expr):
        if not expr.refs:
            value = _evaluate(expr, {})
            return sp.Rational(value.numerator, value.denominator)
        if expr.op == 'number':
            return sp.Rational(expr.value.numerator, expr.value.denominator)
        if expr.op == 'ref':
            return symbols[expr.value]
        args = [build(arg) for arg in expr.args]
        if expr.op == 'div' and args[1] == 0:
            raise Issue('unknown', 'calculation_undefined', 'Original polynomial expression has a zero denominator')
        if expr.op == 'pow' and expr.value == 0 and args[0] == 0:
            raise Issue('unknown', 'calculation_undefined', 'Zero to power zero is outside the selected arithmetic profile')
        return {'add': lambda: args[0]+args[1], 'sub': lambda: args[0]-args[1],
                'mul': lambda: args[0]*args[1], 'div': lambda: args[0]/args[1],
                'neg': lambda: -args[0], 'pow': lambda: args[0]**expr.value}[expr.op]()

    try:
        left, right = (_expression(check[key], variables) for key in ('lhs', 'rhs'))
        polynomial = sp.Poly(build(left)-build(right), *[symbols[key] for key in sorted(left.refs | right.refs)], domain=sp.QQ) if left.refs | right.refs else None
        if polynomial is not None:
            for coefficient in polynomial.all_coeffs() if polynomial.is_univariate else polynomial.coeffs():
                _bounded(Fraction(int(coefficient.p), int(coefficient.q)))
        equal = polynomial.is_zero if polynomial is not None else build(left) == build(right)
        return {'status': 'pass' if equal else 'fail', 'backend': 'sympy', 'backend_version': sp.__version__,
                'claim_scope': 'polynomial_identity_over_declared_rational_or_real_domains',
                'coefficient_count': 0 if polynomial is None else len(polynomial.terms()),
                'difference': str(polynomial.as_expr())[:2048] if polynomial is not None else str(build(left)-build(right))}
    except Issue as exc:
        return {'status': exc.status, 'rule': exc.rule, 'detail': str(exc)}
    except Exception as exc:
        return {'status': 'error', 'rule': 'calculation_worker', 'detail': type(exc).__name__+': '+str(exc)[:512]}


def analyze(record: dict, required_checks: list[str] | None = None) -> dict:
    """Evaluate all authored checks, retaining a separately supplied expected set.

    A local record or caller-supplied scope is not an authenticated acceptance
    channel. Semantic hashes identify inputs only.
    """
    result = {'version': VERSION, 'status': 'error', 'findings': [], 'checks': {},
              'limits': dict(LIMITS), 'acceptance': 'not_evaluated',
              'applicability_validation': 'not_evaluated', 'assumptions': {},
              'claim_scope': 'conditional_exact_calculations_for_explicit_authored_expressions',
              'scope_authority': 'caller_supplied_local_scope_not_authenticated'}
    try:
        result['artifact_sha256'] = digest(record)
        _object(record, ('version', 'id', 'revision', 'variables', 'assumptions', 'checks'), 'Calculation record')
        if record['version'] != VERSION:
            raise Issue('unsupported', 'calculation_version', 'Unsupported calculation record version')
        _id(record['id']); _text(record['revision'], 'Revision')
        result.update(model_id=record['id'], revision=record['revision'], assumptions=record['assumptions'])
        variables, assumptions, checks = (record[key] for key in ('variables', 'assumptions', 'checks'))
        if any(type(group) is not dict for group in (variables, assumptions, checks)):
            raise Issue('error', 'calculation_schema', 'Variables, assumptions and checks must be objects')
        if len(variables) > LIMITS['variables'] or not checks or len(checks) > LIMITS['checks'] or len(assumptions) > 64:
            raise Issue('unsupported', 'calculation_limit', 'Provide 1..64 checks, at most 32 variables and at most 64 assumptions')
        if len(set(variables) | set(assumptions) | set(checks)) != len(variables)+len(assumptions)+len(checks):
            raise Issue('error', 'calculation_identifier', 'Engineering identifiers must be unique across groups')
        for key in (*variables, *assumptions, *checks):
            _id(key)
        domains = {}
        for key, variable in variables.items():
            _object(variable, ('domain', 'values', 'unit', 'basis'), key)
            if variable['domain'] not in ('rational', 'real'):
                raise Issue('unsupported', 'calculation_domain', 'Only explicit rational or real domains are supported')
            _unit(variable['unit'])
            if variable['basis'] is not None:
                _text(variable['basis'], key+'.basis')
            values = variable['values']
            if values is not None and (type(values) is not list or len(values) > LIMITS['domain_values']):
                raise Issue('unsupported', 'calculation_domain', 'Finite values must be null or a list of at most 64 exact rational strings')
            domains[key] = None if values is None else tuple(_number(value) for value in values)
            if domains[key] is not None and len(set(domains[key])) != len(domains[key]):
                raise Issue('error', 'calculation_domain', 'Finite values must be numerically distinct')
        for key, assumption in assumptions.items():
            _object(assumption, ('text', 'basis'), key)
            _text(assumption['text'], key+'.text')
            if assumption['basis'] is not None:
                _text(assumption['basis'], key+'.basis')
        expected = sorted(checks) if required_checks is None else required_checks
        if type(expected) is not list or not expected or len(expected) > 64 or len(set(expected)) != len(expected):
            raise Issue('error', 'calculation_scope', 'Expected check IDs must be a nonempty distinct bounded list')
        for key in expected:
            _id(key)
        result['expected_checks'] = sorted(expected)
        result['scope_sha256'] = digest(sorted(expected))
        for key in sorted(set(expected)-set(checks)):
            result['findings'].append(finding('calculation_missing_required', 'fail', [key], 'Required check is absent from this candidate'))
        total_valuations = 0
        for key, check in sorted(checks.items()):
            checked = {'status': 'error', 'completed_valuations': 0, 'expected_valuations': None}
            result['checks'][key] = checked
            try:
                _object(check, ('kind', 'relation', 'lhs', 'rhs', 'assumptions'), key)
                if check['kind'] not in ('forall', 'exists', 'polynomial_identity') or check['relation'] not in RELATIONS:
                    raise Issue('unsupported', 'calculation_check', 'Unsupported check kind or relation')
                if type(check['assumptions']) is not list or len(check['assumptions']) > 64 or len(set(check['assumptions'])) != len(check['assumptions']):
                    raise Issue('error', 'calculation_assumption', 'Selected assumption IDs must be a distinct bounded list')
                for assumption in check['assumptions']:
                    _id(assumption)
                    if assumption not in assumptions:
                        raise Issue('fail', 'calculation_assumption', 'Selected assumption is undeclared')
                    if assumptions[assumption]['basis'] is None:
                        raise Issue('unknown', 'calculation_assumption', 'Selected assumption has no declared basis')
                left, right = (_expression(check[field], variables) for field in ('lhs', 'rhs'))
                refs = sorted(left.refs | right.refs)
                checked.update(variables=refs, assumptions=check['assumptions'])
                if left.unit != right.unit:
                    raise Issue('fail', 'calculation_units', 'Comparison requires identical declared units; no conversion is inferred')
                if any(variables[ref]['basis'] is None for ref in refs):
                    raise Issue('unknown', 'calculation_basis', 'Referenced variable has no declared source or assumption basis')
                if check['kind'] == 'polynomial_identity':
                    if check['relation'] != 'eq' or not _polynomial(left) or not _polynomial(right):
                        raise Issue('unsupported', 'calculation_polynomial', 'Polynomial identities require equality, nonnegative powers and division only by constant expressions')
                    if any(variables[ref]['values'] is not None for ref in refs):
                        raise Issue('unsupported', 'calculation_domain', 'Polynomial identities use the whole declared domain: set values to null; use forall for finite domains')
                    if len(refs) > LIMITS['symbolic_variables'] or max(left.degree, right.degree) > LIMITS['symbolic_degree'] or left.terms+right.terms > LIMITS['symbolic_terms'] or max(left.coefficient_bits, right.coefficient_bits) > LIMITS['rational_bits']:
                        raise Issue('unsupported', 'calculation_limit', 'Polynomial exceeds symbolic variable, degree, coefficient-growth or expansion bounds')
                    checked.update(_symbolic(record, check))
                    if checked['status'] != 'pass':
                        result['findings'].append(finding('calculation_polynomial_identity', checked['status'], [key],
                            'Exact polynomial coefficients differ over the declared domain', {'difference': checked['difference']}))
                    continue
                if any(not domains[ref] for ref in refs):
                    raise Issue('unknown', 'calculation_domain', 'Finite checks require a nonempty explicit value list for every referenced variable')
                count = 1
                for ref in refs:
                    count *= len(domains[ref])
                checked['expected_valuations'] = count
                if count > LIMITS['valuations_per_check'] or total_valuations+count > LIMITS['total_valuations']:
                    raise Issue('unknown', 'calculation_limit', 'Finite domain exceeds the per-check or total valuation limit')
                total_valuations += count
                true_count, first_true, first_false = 0, None, None
                for values in product(*(domains[ref] for ref in refs)):
                    assignment = dict(zip(refs, values))
                    lhs, rhs = _evaluate(left, assignment), _evaluate(right, assignment)
                    holds = RELATIONS[check['relation']](lhs, rhs)
                    evidence = {'assignment': {ref: str(value) for ref, value in assignment.items()},
                                'lhs': str(lhs), 'rhs': str(rhs), 'unit': dict(left.unit)}
                    checked['completed_valuations'] += 1
                    if holds:
                        true_count += 1
                        first_true = first_true or evidence
                    else:
                        first_false = first_false or evidence
                checked.update(status='pass' if (true_count == count if check['kind'] == 'forall' else true_count > 0) else 'fail',
                               satisfying_valuations=true_count, claim_scope='exhaustive_finite_domain_'+check['kind'])
                if check['kind'] == 'forall':
                    checked['counterexample' if first_false else 'example'] = first_false or first_true
                else:
                    checked['witness'] = first_true
                    checked['solution_set_scope'] = 'only_the_explicit_finite_domain'
                    if not first_true:
                        checked['counterexample'] = first_false
            except Issue as exc:
                checked.update(status=exc.status, rule=exc.rule, detail=str(exc))
            result['findings'].extend([finding(checked.get('rule', 'calculation_check'), checked['status'], [key],
                checked.get('detail', checked.get('claim_scope', 'Exact calculation completed')))] if checked['status'] != 'pass' else [])
        states = [item['status'] for item in result['checks'].values()] + [item['status'] for item in result['findings']]
        result['completed_checks'] = sorted(key for key, value in result['checks'].items() if value['status'] in ('pass', 'fail'))
        all_pass = (len(result['checks']) == len(checks) and set(expected) <= result['checks'].keys() and
                    all(state == 'pass' for state in states))
        result['status'] = 'pass' if all_pass else next(
            (state for state in ('error', 'fail', 'unsupported', 'unknown', 'not_run') if state in states), 'error')
    except Issue as exc:
        result['status'] = exc.status
        result['findings'].append(finding(exc.rule, exc.status, [], str(exc)))
    except (TypeError, ValueError, KeyError, RecursionError, OverflowError) as exc:
        result['status'] = 'error'
        result['findings'].append(finding('calculation_schema', 'error', [], type(exc).__name__+': '+str(exc)[:512]))
    return result


if __name__ == '__main__':
    if sys.argv[1:] != ['--symbolic-worker']:
        raise SystemExit('Use scripts/analyze.py for the public CLI')
    print(json.dumps(_symbolic_worker(json.load(sys.stdin)), sort_keys=True))
