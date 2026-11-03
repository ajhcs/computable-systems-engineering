#!/usr/bin/env python3
"""Check a versioned engineering measure definition or compare two revisions."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.measures import VERSION, check, compare, load, render_text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('check'); p.add_argument('record')
    p.add_argument('--format', choices=('json', 'text'), default='json')
    p = sub.add_parser('compare'); p.add_argument('before'); p.add_argument('after')
    p.add_argument('--format', choices=('json', 'text'), default='json')
    args = parser.parse_args(argv)
    try:
        paths = [args.record] if args.command == 'check' else [args.before, args.after]
        records, inputs = [], []
        for path in paths:
            record, sha = load(path)
            records.append(record)
            inputs.append({'path': str(Path(path).absolute()), 'sha256': sha})
        report = check(records[0]) if args.command == 'check' else compare(*records)
        report['inputs'] = inputs
    except (OSError, ValueError, TypeError, RecursionError, OverflowError):
        report = {'checker_version': VERSION, 'status': 'error', 'claim_scope': 'input_reading',
                  'findings': [{'rule': 'measure_input', 'status': 'error', 'ids': [],
                                'explanation': 'Cannot read a bounded regular UTF-8 JSON definition with unique keys'}],
                  'acceptance': 'not_evaluated', 'observation_comparability': 'not_evaluated'}
    print(render_text(report) if args.format == 'text' else json.dumps(report, sort_keys=True, indent=2))
    return 0 if report['status'] == 'pass' else 2 if report['status'] == 'error' else 1


if __name__ == '__main__':
    raise SystemExit(main())
