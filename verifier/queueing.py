"""Exact finite FCFS replay and conditional M/M/c arithmetic.

Original bounded implementation; source/theory study is in docs/queue-analysis.md.
No stochastic sampler, user code, routed network or native behavior interpreter.
"""
from fractions import Fraction
from hashlib import sha256
import heapq
import json

from .core import ID, _pairs, digest, finding
from .foundation import read_regular
from .calculations import Issue, _number, _bounded

VERSION = 'queue-analysis-1.0'
LIMITS = {'input_bytes': 1048576, 'checks': 16, 'jobs': 512, 'servers': 64,
          'text_characters': 2048, 'rational_bits': 4096}
SEVERITY = {'pass': 0, 'unknown': 1, 'unsupported': 2, 'fail': 3, 'error': 4}
REPLAY_ASSUMPTIONS = ('empty_initial_system', 'unit_demand', 'identical_servers',
                      'nonpreemptive', 'complete_arrivals_in_window')
MMC_ASSUMPTIONS = ('poisson_arrivals', 'exponential_service',
                   'independent_arrivals_and_services', 'identical_servers',
                   'fcfs', 'infinite_queue', 'no_abandonment', 'stationary_rates')


def _object(value, fields, where):
    if type(value) is not dict or set(value) != set(fields):
        raise Issue('error', 'queue_schema', where + ' needs exactly the documented fields')


def _text(value, where):
    if type(value) is not str or not value.strip() or len(value) > LIMITS['text_characters']:
        raise Issue('error', 'queue_schema', where + ' needs bounded nonempty text')


def _id(value):
    if type(value) is not str or not ID.fullmatch(value):
        raise Issue('error', 'queue_identifier', 'Use an engineering identifier')


def _known(value, where):
    if value is None:
        raise Issue('unknown', 'queue_unknown', where + ' is unresolved')


def _servers(value):
    _known(value, 'servers')
    if type(value) is not int or not 1 <= value <= LIMITS['servers']:
        raise Issue('error', 'queue_servers', 'servers must be an integer from 1 through 64')
    return value


def _assumptions(raw, names):
    _object(raw, names, 'assumptions')
    pending = []
    for name in names:
        item = raw[name]
        _object(item, ('holds', 'basis'), 'assumption')
        if item['holds'] is not None and type(item['holds']) is not bool:
            raise Issue('error', 'queue_assumption', 'holds must be Boolean or null')
        if item['basis'] is not None:
            _text(item['basis'], 'assumption basis')
        if item['holds'] is False:
            pending.append(('unsupported', name + ' does not hold'))
        elif item['holds'] is None or item['basis'] is None:
            pending.append(('unknown', name + ' lacks an affirmative declared basis'))
    if pending:
        status = max((x[0] for x in pending), key=SEVERITY.get)
        raise Issue(status, 'queue_applicability', '; '.join(x[1] for x in pending))


def _sum(values):
    result = Fraction(0)
    for value in values:
        result = _bounded(result + value)
    return result


def _mean(values):
    return str(_bounded(_sum(values) / len(values))) if values else None


def _replay(raw, details):
    _object(raw, ('kind', 'servers', 'window', 'jobs', 'assumptions'), 'fcfs_replay')
    servers = _servers(raw['servers'])
    _object(raw['window'], ('start', 'end'), 'window')
    _known(raw['window']['start'], 'window.start'); _known(raw['window']['end'], 'window.end')
    start, end = (_number(raw['window'][key]) for key in ('start', 'end'))
    if start < 0 or end <= start:
        raise Issue('error', 'queue_window', 'Use 0 <= start < end')
    duration = _bounded(end - start)
    _known(raw['jobs'], 'jobs')
    if type(raw['jobs']) is not list or len(raw['jobs']) > LIMITS['jobs']:
        raise Issue('error', 'queue_jobs', 'jobs must be a list of at most 512 records')
    jobs, ids = [], set()
    for ordinal, item in enumerate(raw['jobs']):
        _object(item, ('id', 'arrival', 'service'), 'job')
        _id(item['id'])
        if item['id'] in ids:
            raise Issue('error', 'queue_duplicate', 'Job IDs must be unique within a replay')
        ids.add(item['id'])
        _known(item['arrival'], 'arrival'); _known(item['service'], 'service')
        arrival, service = _number(item['arrival']), _number(item['service'])
        if not start <= arrival < end or service < 0:
            raise Issue('error', 'queue_job_time', 'Arrivals must be within [start,end); service must be nonnegative')
        jobs.append((arrival, ordinal, item['id'], service))
    _assumptions(raw['assumptions'], REPLAY_ASSUMPTIONS)
    if not jobs:
        raise Issue('unknown', 'queue_no_jobs', 'No supplied jobs; performance means cannot be computed')
    free = [(start, i) for i in range(servers)]
    heapq.heapify(free)
    trace, queue_events, busy_intervals, waits, system_times = [], [], [], [], []
    completed = in_service = waiting = 0
    completed_waits, completed_system = [], []
    for arrival, ordinal, identity, service in sorted(jobs):
        available, slot = heapq.heappop(free)
        begin = max(arrival, available)
        finish = _bounded(begin + service)
        wait = _bounded(begin - arrival)
        system = _bounded(finish - arrival)
        heapq.heappush(free, (finish, slot))
        waits.append(wait); system_times.append(system)
        if begin > arrival:
            queue_events += [(arrival, 1), (min(begin, end), -1)]
        busy_intervals.append(max(Fraction(0), _bounded(min(finish, end) - min(begin, end))))
        if finish <= end:
            state = 'completed'; completed += 1
            completed_waits.append(wait); completed_system.append(system)
        elif begin <= end:
            state = 'in_service'; in_service += 1
        else:
            state = 'waiting'; waiting += 1
        trace.append({'id': identity, 'input_order': ordinal, 'slot': slot,
                      'arrival': str(arrival), 'start': str(begin), 'finish': str(finish),
                      'wait': str(wait), 'state_at_end': state})
    # Group simultaneous transitions; zero-length waits create no queued occupancy.
    events = {}
    for time, delta in queue_events:
        events[time] = events.get(time, 0) + delta
    population = peak = 0
    previous, queue_area = start, Fraction(0)
    for time in sorted(events):
        queue_area = _bounded(queue_area + _bounded((time - previous) * population))
        population += events[time]
        peak = max(peak, population)
        previous = time
    queue_area = _bounded(queue_area + _bounded((end - previous) * population))
    busy_area = _sum(busy_intervals)
    result = {'completed_jobs': completed, 'in_service_at_end': in_service,
              'waiting_at_end': waiting, 'supplied_jobs': len(jobs), 'peak_queue': peak,
              'window_queue_area': str(queue_area), 'window_busy_area': str(busy_area),
              'window_mean_queue': str(_bounded(queue_area / duration)),
              'window_mean_in_system': str(_bounded((queue_area + busy_area) / duration)),
              'window_utilization': str(_bounded(busy_area / _bounded(duration * servers))),
              'completed_jobs_mean_wait': _mean(completed_waits),
              'completed_jobs_mean_system_time': _mean(completed_system),
              'supplied_cohort_mean_wait': _mean(waits),
              'supplied_cohort_mean_system_time': _mean(system_times),
              'trace_sha256': digest(trace),
              'trace_scope': 'full supplied cohort schedule; occupancy clipped to declared window',
              'boundary': 'arrivals in [start,end); state includes grants and completions at end',
              'tie_rule': 'arrival then input order; earliest available slot then slot index'}
    if details:
        result['trace'] = trace
    return result


def _mmc(raw):
    _object(raw, ('kind', 'servers', 'arrival_rate', 'service_rate', 'assumptions'), 'mmc')
    servers = _servers(raw['servers'])
    _known(raw['arrival_rate'], 'arrival_rate'); _known(raw['service_rate'], 'service_rate')
    arrival, service = _number(raw['arrival_rate']), _number(raw['service_rate'])
    if arrival < 0 or service <= 0:
        raise Issue('error', 'queue_rates', 'Arrival rate must be nonnegative and per-server service rate positive')
    _assumptions(raw['assumptions'], MMC_ASSUMPTIONS)
    spare = _bounded(servers * service - arrival)
    if spare <= 0:
        raise Issue('fail', 'queue_unstable', 'No stationary M/M/c distribution: arrival_rate >= servers * service_rate')
    load = _bounded(arrival / service)
    utilization = _bounded(load / servers)
    term = total = Fraction(1)
    for n in range(1, servers):
        term = _bounded(term * load / n)
        total = _bounded(total + term)
    tail = _bounded(_bounded(term * load / servers) / (1 - utilization))
    empty = _bounded(Fraction(1) / _bounded(total + tail))
    delayed = _bounded(tail * empty)
    wait = _bounded(delayed / spare)
    response = _bounded(wait + 1 / service)
    return {'utilization': str(utilization), 'probability_empty': str(empty),
            'probability_wait': str(delayed), 'mean_wait': str(wait),
            'mean_system_time': str(response), 'mean_queue': str(_bounded(arrival * wait)),
            'mean_in_system': str(_bounded(arrival * response)),
            'scope': 'conditional stationary M/M/c; zero-arrival waiting/service times are limiting values'}


def analyze(record, required_checks=None, *, details=False):
    report = {'checker_version': VERSION, 'status': 'error', 'checks': {}, 'findings': [],
              'limits': LIMITS.copy(), 'claim_scope': 'declared_queue_model_computation',
              'applicability': 'declared_only', 'native_correspondence': 'not_evaluated',
              'observed_data_validation': 'not_evaluated', 'acceptance': 'not_evaluated',
              'required_scope': 'caller_selected' if required_checks is not None else 'authored_checks_only'}
    try:
        if required_checks is not None:
            if type(required_checks) is not list or not 1 <= len(required_checks) <= LIMITS['checks']:
                raise Issue('error', 'queue_scope', 'Required scope needs 1 through 16 check IDs')
            for identity in required_checks: _id(identity)
            if len(set(required_checks)) != len(required_checks):
                raise Issue('error', 'queue_scope', 'Required check IDs must be unique')
            report['expected_checks'] = sorted(required_checks)
        _object(record, ('version', 'id', 'revision', 'subject', 'time_unit', 'job_unit', 'checks'), 'record')
        if record['version'] != VERSION:
            raise Issue('unsupported', 'queue_version', 'Unsupported queue record version')
        _id(record['id']); _text(record['revision'], 'revision')
        _id(record['time_unit']); _id(record['job_unit'])
        _object(record['subject'], ('id', 'model_revision', 'basis'), 'subject')
        _id(record['subject']['id']); _text(record['subject']['model_revision'], 'model revision')
        _known(record['subject']['basis'], 'subject basis'); _text(record['subject']['basis'], 'subject basis')
        checks = record['checks']
        if type(checks) is not dict or not 1 <= len(checks) <= LIMITS['checks']:
            raise Issue('error', 'queue_checks', 'Use 1 through 16 named checks')
        for identity in checks: _id(identity)
        report.update(id=record['id'], revision=record['revision'], record_sha256=digest(record),
                      subject=record['subject'].copy(), time_unit=record['time_unit'], job_unit=record['job_unit'])
        for identity, raw in sorted(checks.items()):
            row = {'status': 'error', 'findings': []}
            try:
                if type(raw) is not dict:
                    raise Issue('error', 'queue_schema', 'A check needs an object')
                if raw.get('kind') == 'fcfs_replay': row['result'] = _replay(raw, details)
                elif raw.get('kind') == 'mmc': row['result'] = _mmc(raw)
                else: raise Issue('unsupported', 'queue_kind', 'Supported kinds are fcfs_replay and mmc')
                row['status'] = 'pass'
            except Issue as exc:
                row['status'] = exc.status
                row['findings'] = [finding(exc.rule, exc.status, [identity], str(exc))]
            report['checks'][identity] = row
        for identity in sorted(set(required_checks or ()) - set(checks)):
            report['checks'][identity] = {'status': 'fail', 'findings': [finding(
                'queue_required_missing', 'fail', [identity], 'Required queue check is absent')]}
        report['status'] = max((row['status'] for row in report['checks'].values()), key=SEVERITY.get)
    except Issue as exc:
        report['status'] = exc.status
        report['findings'] = [finding(exc.rule, exc.status, (), str(exc))]
    except (ValueError, TypeError, KeyError, RecursionError, OverflowError):
        report['status'] = 'error'
        report['findings'] = [finding('queue_schema', 'error', (), 'Malformed or out-of-limit queue record')]
    return report


def load(path):
    raw = read_regular(path, LIMITS['input_bytes'])
    record = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
    return record, sha256(raw).hexdigest()
