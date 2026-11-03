#!/usr/bin/env python3
"""Compute bounded observation summaries from an explicit versioned record."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.validation import VERSION, analyze, load, render_text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record')
    parser.add_argument('--required', action='append', help='Retain an expected check ID; repeat as needed')
    parser.add_argument('--format', choices=('json', 'text'), default='json')
    args = parser.parse_args(argv)
    try:
        record, sha = load(args.record)
        report = analyze(record, args.required)
        report['inputs'] = [{'path': str(Path(args.record).absolute()), 'sha256': sha}]
    except (OSError, ValueError, TypeError, RecursionError, OverflowError):
        report = {'checker_version': VERSION, 'status': 'error', 'claim_scope': 'input_reading',
                  'findings': [{'rule': 'validation_input', 'status': 'error', 'ids': [],
                                'explanation': 'Cannot read a bounded regular UTF-8 JSON record with unique keys'}],
                  'acceptance': 'not_evaluated', 'future_coverage': 'not_established'}
    print(render_text(report) if args.format == 'text' else json.dumps(report, sort_keys=True, indent=2))
    return 0 if report['status'] == 'pass' else 2 if report['status'] == 'error' else 1


if __name__ == '__main__':
    raise SystemExit(main())
