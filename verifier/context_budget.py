"""Lossless, bounded JSON presentations of an assembled context report.

References deduplicate existing values; they do not summarize source meaning or
select fewer obligations. The expanded object is the original assembled report.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json

VERSION = 'assembled-context-compact-1.0'
REFERENCE = '$ref'
LITERAL = '$literal'
MIN_BYTES = 1024
MAX_BYTES = 8_000_000
MAX_RECORDS = 4096
MAX_NODES = 1_000_000
MAX_DEPTH = 128
ENCODING = {'reference_key': REFERENCE, 'literal_key': LITERAL,
            'meaning': 'A sole reference key names an exact value in records. '
                       'A sole literal key escapes an original object. '
                       'Expand context to recover the complete unchanged report.'}


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def render_compact_json(report):
    """Exact UTF-8 representation counted by the public CLI, with newline."""
    return _json(report) + '\n'


def _stamp(report):
    """Count the field containing the count, including its changing digit width."""
    report['budget']['emitted_bytes'] = 0
    for _ in range(8):
        size = len(render_compact_json(report).encode('utf-8'))
        if size == report['budget']['emitted_bytes']:
            return report
        report['budget']['emitted_bytes'] = size
    raise ValueError('Unable to stabilize compact byte count')


def _refused(limit, *, invalid=False, source=None):
    prior = source.get('status') if type(source) is dict else None
    status = 'error' if invalid else prior if prior in ('error', 'fail', 'unsupported') else 'unknown'
    report = {'version': VERSION, 'status': status,
              'retrieval_status': 'error' if invalid else 'unknown',
              'semantic_review': 'not_run', 'required_review': 'not_evaluated',
              'acceptance': 'not_evaluated',
              'checker_scope': 'complete_supplied_model_unchanged',
              'coverage': {'complete': False, 'semantic_completeness': 'not_evaluated'},
              'budget': {'status': 'error' if invalid else 'refused',
                         'max_bytes': limit if type(limit) is int and MIN_BYTES <= limit <= MAX_BYTES else None},
              'findings': [{'rule': 'context_budget', 'status': 'error' if invalid else 'unknown',
                            'ids': [], 'detail':
                            'Compact max_bytes must be an integer from 1024 through 8000000.' if invalid else
                            'The complete compact context does not fit. No partial context is returned; '
                            'increase the byte budget or explicitly select a narrower view. '
                            'The independent required-check scope is unchanged.'}]}
    return _stamp(report)


def _encode(source):
    """Intern repeated substantial values, with deterministic record identities."""
    counts, originals = Counter(), {}
    nodes = 0

    def count(value, depth=0):
        nonlocal nodes
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError('Compact context work limit exceeded')
        if isinstance(value, (str, dict, list)):
            key = _json(value)
            if len(key.encode('utf-8')) >= 32:
                counts[key] += 1
                originals.setdefault(key, value)
        if type(value) is dict:
            for key in sorted(value):
                count(value[key], depth + 1)
        elif type(value) is list:
            for item in value:
                count(item, depth + 1)

    count(source)
    # The savings estimate includes reference objects and a pool entry. Small
    # literals stay directly readable in their original locations.
    candidates = [key for key, n in counts.items()
                  if n > 1 and (n - 1) * len(key.encode('utf-8')) - n * 16 - 9 > 8]
    candidates.sort(key=lambda key: (-(counts[key] - 1) * len(key.encode('utf-8')), key))
    selected = sorted(candidates[:MAX_RECORDS])
    identities = {key: f'r{number:04d}' for number, key in enumerate(selected)}

    def encode(value, *, definition=False):
        key = _json(value) if isinstance(value, (str, dict, list)) else None
        if not definition and key in identities:
            return {REFERENCE: identities[key]}
        if type(value) is dict:
            if set(value) in ({REFERENCE}, {LITERAL}):
                return {LITERAL: deepcopy(value)}
            return {key: encode(value[key]) for key in sorted(value)}
        if type(value) is list:
            return [encode(item) for item in value]
        return value

    return encode(source), {identities[key]: encode(originals[key], definition=True)
                            for key in selected}


def expand_context(package):
    """Decode a successful compact transport; this does not authenticate it.

    Refused, cyclic, excessively nested or expanding packages are rejected. This
    helper is not an alternate input route into any engineering checker.
    """
    if (type(package) is not dict or package.get('version') != VERSION or
            package.get('encoding') != ENCODING or 'context' not in package or
            type(package.get('records')) is not dict or len(package['records']) > MAX_RECORDS):
        raise ValueError('Expected a complete compact context package')
    records = package['records']
    nodes = size = 0

    def decode(value, trail=(), depth=0, *, references=True):
        nonlocal nodes, size
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError('Compact expansion work limit exceeded')
        if type(value) is dict:
            if references and set(value) == {REFERENCE}:
                identity = value[REFERENCE]
                if type(identity) is not str or identity not in records or identity in trail:
                    raise ValueError('Unknown or cyclic compact reference')
                return decode(records[identity], trail + (identity,), depth + 1)
            if references and set(value) == {LITERAL}:
                return decode(value[LITERAL], trail, depth + 1, references=False)
            size += 2 + max(len(value) - 1, 0)
            result = {}
            for key, item in value.items():
                if type(key) is not str:
                    raise ValueError('Compact JSON object keys must be strings')
                size += len(_json(key).encode('utf-8')) + 1
                result[key] = decode(item, trail, depth + 1, references=references)
        elif type(value) is list:
            size += 2 + max(len(value) - 1, 0)
            result = [decode(item, trail, depth + 1, references=references) for item in value]
        else:
            size += len(_json(value).encode('utf-8'))
            result = value
        if size > MAX_BYTES:
            raise ValueError('Expanded context exceeds byte cap')
        return result

    result = decode(package['context'])
    if sha256(_json(result).encode('utf-8')).hexdigest() != package.get('source_report_sha256'):
        raise ValueError('Expanded context differs from source report digest')
    return result


def compact_context(report, max_bytes=None):
    """Return the entire report losslessly, or an explicit bounded refusal.

    Whole authored values remain in context/records, without abbreviation. The
    requested limit includes all transport metadata and the final newline.
    """
    limit = MAX_BYTES if max_bytes is None else max_bytes
    if type(limit) is not int or not MIN_BYTES <= limit <= MAX_BYTES:
        return _refused(limit, invalid=True)
    try:
        raw = _json(report).encode('utf-8')
        if len(raw) > MAX_BYTES:
            return _refused(limit, source=report)
        context, records = _encode(report)
        package = {'version': VERSION,
                   **{key: report.get(key) for key in
                      ('status', 'retrieval_status', 'semantic_review', 'required_review',
                       'acceptance', 'checker_scope')},
                   'source_report_sha256': sha256(raw).hexdigest(),
                   'encoding': ENCODING, 'context': context, 'records': records,
                   'budget': {'status': 'pass', 'max_bytes': limit,
                              'source_json_bytes': len(raw), 'policy': 'complete_report_or_refusal'}}
        # Deduplication is optional when its reference table would increase size.
        if len(_json({'context': context, 'records': records}).encode('utf-8')) > len(raw):
            # Literal marker objects still need escaping in the no-pool format.
            package['context'], package['records'] = _encode_literals(report), {}
        package = _stamp(package)
        if package['budget']['emitted_bytes'] > limit:
            return _refused(limit, source=report)
        if expand_context(package) != report:
            raise ValueError('Compact round-trip did not preserve the source report')
        return package
    except (ValueError, TypeError, RecursionError, KeyError):
        refused = _refused(limit, invalid=True)
        refused['findings'][0]['detail'] = 'Compact serialization or round-trip failed; no partial context is returned.'
        return _stamp(refused)


def _encode_literals(value):
    """Escape original marker objects even when no deduplication is useful."""
    if type(value) is dict:
        if set(value) in ({REFERENCE}, {LITERAL}):
            return {LITERAL: deepcopy(value)}
        return {key: _encode_literals(item) for key, item in value.items()}
    if type(value) is list:
        return [_encode_literals(item) for item in value]
    return value
