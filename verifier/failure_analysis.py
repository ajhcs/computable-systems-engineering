"""Bounded coherent Boolean failure analysis from authored records.

Truth tables and subset minimality are implemented directly. No upstream source,
model code, probabilistic independence, or severity ordering is imported.
"""
from fractions import Fraction
import re

from .core import ID, digest, finding

VERSION = 'failure-analysis-1.0'
LIMITS = {'events': 128, 'reachable_events': 12, 'gates': 128,
          'gate_inputs': 32, 'gate_depth': 64, 'assignments': 4096,
          'minimal_cut_sets': 256, 'cut_set_literals': 2048,
          'fmea_rows': 128, 'text_characters': 2048, 'rational_bits': 4096}
CHECKS = ('fault_tree', 'probability', 'fmea')
NUMBER = re.compile(r'(?:[0-9]+(?:\.[0-9]+)?|[0-9]+/[1-9][0-9]*)\Z')


class Issue(ValueError):
    def __init__(self, status, rule, message):
        self.status, self.rule = status, rule
        super().__init__(message)


def _object(value, fields, label):
    if type(value) is not dict or set(value) != set(fields):
        raise Issue('error', 'failure_schema', label+' needs exactly '+', '.join(fields))


def _text(value, label, nullable=False):
    if nullable and value is None:
        return
    if type(value) is not str or not value.strip() or len(value) > LIMITS['text_characters']:
        raise Issue('error', 'failure_schema', label+' needs bounded nonempty text or explicit null for unknown')


def _id(value):
    if type(value) is not str or not ID.fullmatch(value):
        raise Issue('error', 'failure_identifier', 'Invalid engineering identifier')


def _fraction(value):
    if type(value) is not str or len(value) > 80 or not NUMBER.fullmatch(value):
        raise Issue('error', 'failure_probability', 'Probability must be an exact nonnegative integer, decimal or rational string')
    try:
        number = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise Issue('error', 'failure_probability', 'Probability needs a defined exact rational value') from exc
    if not 0 <= number <= 1:
        raise Issue('fail', 'failure_probability', 'Event probabilities must be between zero and one')
    return number


def _aggregate(states):
    return next((state for state in ('error', 'fail', 'unsupported', 'unknown', 'not_run') if state in states), 'pass')


def _validate(record):
    _object(record, ('version', 'id', 'revision', 'basis', 'events', 'gates',
                     'top_event', 'probability', 'fmea'), 'Failure analysis record')
    if record['version'] != VERSION:
        raise Issue('unsupported', 'failure_version', 'Unsupported failure analysis version')
    _id(record['id']); _text(record['revision'], 'revision'); _text(record['basis'], 'basis', True)
    events, gates, rows = (record[key] for key in ('events', 'gates', 'fmea'))
    if any(type(group) is not dict for group in (events, gates, rows)):
        raise Issue('error', 'failure_schema', 'Events, gates and FMEA rows must be objects')
    if not events:
        raise Issue('fail', 'failure_empty', 'Declare at least one event')
    if len(events) > LIMITS['events'] or len(gates) > LIMITS['gates'] or len(rows) > LIMITS['fmea_rows']:
        raise Issue('unsupported', 'failure_limit', 'Declaration count exceeds the stated limit')
    if len(set(events) | set(gates) | set(rows)) != len(events)+len(gates)+len(rows):
        raise Issue('error', 'failure_identifier', 'Event, gate and FMEA row IDs must be unique across groups')
    for key in (*events, *gates, *rows):
        _id(key)
    probabilities = {}
    for key, event in sorted(events.items()):
        _object(event, ('description', 'basis', 'probability'), key)
        _text(event['description'], key+'.description'); _text(event['basis'], key+'.basis', True)
        probabilities[key] = None if event['probability'] is None else _fraction(event['probability'])
    names = events.keys() | gates.keys()
    for key, gate in sorted(gates.items()):
        _object(gate, ('operator', 'inputs'), key)
        if gate['operator'] not in ('and', 'or'):
            raise Issue('unsupported', 'failure_gate', 'Only monotone and/or gates are supported')
        inputs = gate['inputs']
        if type(inputs) is not list or not 1 <= len(inputs) <= LIMITS['gate_inputs']:
            raise Issue('error', 'failure_gate', 'Gate inputs need a nonempty bounded list')
        for ref in inputs:
            _id(ref)
            if ref not in names:
                raise Issue('fail', 'failure_reference', key+' references undeclared event or gate '+ref)
        # Repeated references are deliberately allowed: A AND A is A.
    _id(record['top_event'])
    if record['top_event'] not in names:
        raise Issue('fail', 'failure_reference', 'Top event references an undeclared event or gate')
    visiting, ordered, done, heights = set(), [], set(), {}

    def visit(key, depth=0):
        if key in visiting:
            raise Issue('fail', 'failure_cycle', 'Gate dependency cycle at '+key)
        if depth > LIMITS['gate_depth']:
            raise Issue('unsupported', 'failure_limit', 'Gate dependency depth exceeds the stated limit')
        if key in events or key in done:
            return
        visiting.add(key)
        for ref in gates[key]['inputs']:
            visit(ref, depth+1)
        heights[key] = 1 + max(heights.get(ref, 0) for ref in gates[key]['inputs'])
        if heights[key] > LIMITS['gate_depth']:
            raise Issue('unsupported', 'failure_limit', 'Gate dependency depth exceeds the stated limit')
        visiting.remove(key); done.add(key); ordered.append(key)

    # Validate even disconnected gates; a malformed unused fragment cannot pass.
    for key in sorted(gates):
        visit(key)
    probability = record['probability']
    if probability is not None:
        _object(probability, ('assumption', 'basis', 'mission'), 'Probability assumptions')
        if probability['assumption'] != 'mutually_independent':
            raise Issue('unsupported', 'failure_dependence', 'Only explicitly declared mutual independence is supported')
        _text(probability['basis'], 'probability.basis', True)
        _text(probability['mission'], 'probability.mission', True)
    for key, row in sorted(rows.items()):
        _object(row, ('component', 'failure_mode', 'event', 'local_effect',
                      'system_effect', 'detection', 'basis'), key)
        _id(row['component']); _id(row['event'])
        if row['event'] not in events:
            raise Issue('fail', 'failure_fmea_reference', key+' needs a declared basic event')
        for field in ('failure_mode', 'local_effect', 'system_effect', 'detection', 'basis'):
            _text(row[field], key+'.'+field, True)
    return events, gates, rows, ordered, probabilities


def _truth_table(top, events, gates, order):
    reachable = set()

    def collect(key):
        if key in reachable:
            return
        reachable.add(key)
        if key in gates:
            for ref in gates[key]['inputs']:
                collect(ref)

    collect(top)
    variables = sorted(reachable & events.keys())
    if len(variables) > LIMITS['reachable_events']:
        raise Issue('unknown', 'failure_limit', 'Reachable event count exceeds exhaustive analysis limit')
    count = 1 << len(variables)
    truth = []
    gate_order = [key for key in order if key in reachable]
    for mask in range(count):
        values = {key: bool(mask & (1 << i)) for i, key in enumerate(variables)}
        for key in gate_order:
            gate = gates[key]
            values[key] = (all if gate['operator'] == 'and' else any)(values[ref] for ref in gate['inputs'])
        truth.append(values[top])
    # Monotonicity follows from the validated AND/OR grammar. A true assignment
    # is minimal exactly when clearing each individual set bit makes it false.
    minimal = [mask for mask, value in enumerate(truth) if value and
               all(not truth[mask ^ (1 << i)] for i in range(len(variables)) if mask & (1 << i))]
    if len(minimal) > LIMITS['minimal_cut_sets'] or sum(mask.bit_count() for mask in minimal) > LIMITS['cut_set_literals']:
        raise Issue('unknown', 'failure_limit', 'Minimal cut-set output exceeds the declared antichain or literal limit; no partial list is returned')
    cuts = sorted(([key for i, key in enumerate(variables) if mask & (1 << i)] for mask in minimal),
                  key=lambda row: (len(row), row))
    return variables, truth, cuts, sorted(reachable & gates.keys())


def _probability(variables, truth, probabilities):
    total = Fraction(0)
    for mask, occurs in enumerate(truth):
        if not occurs:
            continue
        weight = Fraction(1)
        for i, key in enumerate(variables):
            p = probabilities[key]
            weight *= p if mask & (1 << i) else 1-p
        total += weight
        if max(total.numerator.bit_length(), total.denominator.bit_length()) > LIMITS['rational_bits']:
            raise Issue('unknown', 'failure_limit', 'Exact probability exceeds rational size limit')
    return str(total)


def analyze(record, required_checks=None):
    """Return deterministic scoped evidence, preserving every required check."""
    result = {'version': VERSION, 'status': 'error', 'checks': {}, 'findings': [],
              'limits': dict(LIMITS), 'acceptance': 'not_evaluated',
              'applicability_validation': 'not_evaluated',
              'claim_scope': 'bounded_authored_coherent_boolean_failure_model',
              'scope_authority': 'caller_supplied_local_scope_not_authenticated',
              'completed_checks': [], 'expected_checks': []}
    try:
        if required_checks is not None:
            if (type(required_checks) is not list or not required_checks or len(required_checks) > len(CHECKS) or
                    any(type(key) is not str or key not in CHECKS for key in required_checks) or
                    len(set(required_checks)) != len(required_checks)):
                raise Issue('error', 'failure_scope', 'Expected checks must be a nonempty distinct list from fault_tree, probability, fmea')
            result['expected_checks'] = sorted(required_checks)
            result['scope_sha256'] = digest(result['expected_checks'])
        result['artifact_sha256'] = digest(record)
        events, gates, rows, order, probabilities = _validate(record)
        result.update(model_id=record['id'], revision=record['revision'])
        selected = ['fault_tree'] + (['probability'] if record['probability'] is not None else []) + (['fmea'] if rows else [])
        expected = selected if required_checks is None else required_checks
        if (type(expected) is not list or not expected or len(expected) > len(CHECKS) or
                any(type(key) is not str or key not in CHECKS for key in expected) or len(set(expected)) != len(expected)):
            raise Issue('error', 'failure_scope', 'Expected checks must be a nonempty distinct list from fault_tree, probability, fmea')
        result['expected_checks'] = sorted(expected)
        result['scope_sha256'] = digest(sorted(expected))
        selected = sorted(set(selected) | set(expected))
        variables = truth = None
        table_issue = None
        try:
            variables, truth, cuts, reachable_gates = _truth_table(record['top_event'], events, gates, order)
            unknown = sorted(key for key in variables if events[key]['basis'] is None)
            check = {'status': 'unknown' if unknown or record['basis'] is None else 'pass',
                     'top_event': record['top_event'], 'events': variables, 'gates': reachable_gates,
                     'unused_events': sorted(events.keys()-set(variables)),
                     'unused_gates': sorted(gates.keys()-set(reachable_gates)),
                     'expected_assignments': len(truth), 'completed_assignments': len(truth),
                     'minimal_cut_sets': cuts, 'cut_sets_complete': True,
                     'unknown_event_basis': unknown, 'record_basis_unknown': record['basis'] is None,
                     'claim_scope': 'all_unique_event_boolean_assignments_no_probability_assumptions'}
            result['checks']['fault_tree'] = check
        except Issue as exc:
            table_issue = exc
            result['checks']['fault_tree'] = {'status': exc.status, 'rule': exc.rule, 'detail': str(exc),
                                               'cut_sets_complete': False}
        if 'probability' in selected:
            assumption = record['probability']
            check = {'status': 'fail', 'probability': None, 'assumptions': assumption,
                     'claim_scope': 'conditional_on_explicit_mutual_independence_and_mission'}
            result['checks']['probability'] = check
            if assumption is None:
                check['detail'] = 'Required probability check has no authored independence and mission assumptions'
            elif table_issue:
                check.update(status=table_issue.status, detail='Exhaustive Boolean analysis did not complete')
            else:
                missing = sorted(key for key in variables if probabilities[key] is None)
                missing_basis = sorted(key for key in variables if events[key]['basis'] is None)
                if missing or missing_basis or assumption['basis'] is None or assumption['mission'] is None or record['basis'] is None:
                    check.update(status='unknown', missing_probabilities=missing, missing_event_basis=missing_basis,
                                 detail='Probability data, mission or assumption basis is incomplete')
                else:
                    try:
                        check.update(status='pass', probability=_probability(variables, truth, probabilities),
                                     completed_assignments=len(truth))
                    except Issue as exc:
                        check.update(status=exc.status, rule=exc.rule, detail=str(exc))
        if 'fmea' in selected:
            incomplete = {key: sorted(field for field, value in row.items() if value is None)
                          for key, row in sorted(rows.items()) if any(value is None for value in row.values())}
            pairs = [(row['component'], row['failure_mode']) for row in rows.values() if row['failure_mode'] is not None]
            duplicates = sorted([list(pair) for pair in set(pairs) if pairs.count(pair) > 1], key=str)
            check = {'status': ('fail' if not rows or duplicates else 'unknown' if incomplete or record['basis'] is None else 'pass'),
                     'row_ids': sorted(rows), 'incomplete_fields': incomplete,
                     'duplicate_component_failure_modes': duplicates,
                     'claim_scope': 'record_completeness_and_basic_event_reference_consistency_only',
                     'effect_correctness': 'not_evaluated', 'severity_ranking': 'not_evaluated',
                     'component_existence': 'not_evaluated'}
            if not rows:
                check['detail'] = 'Required FMEA check has no rows'
            result['checks']['fmea'] = check
        for key, check in sorted(result['checks'].items()):
            if check['status'] != 'pass':
                result['findings'].append(finding(check.get('rule', 'failure_'+key), check['status'], [key],
                                                 check.get('detail', 'Required basis or record content is incomplete or inconsistent')))
        result['completed_checks'] = sorted(key for key, check in result['checks'].items() if check['status'] in ('pass', 'fail'))
        result['status'] = _aggregate([check['status'] for check in result['checks'].values()])
    except Issue as exc:
        result['status'] = exc.status
        result['findings'].append(finding(exc.rule, exc.status, [], str(exc)))
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError) as exc:
        result['status'] = 'error'
        result['findings'].append(finding('failure_schema', 'error', [], type(exc).__name__+': '+str(exc)[:512]))
    for key in result['expected_checks']:
        result['checks'].setdefault(key, {'status': 'not_run', 'detail': 'Record validation prevented this retained check'})
    return result
