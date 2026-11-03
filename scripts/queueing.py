#!/usr/bin/env python3
"""Evaluate a bounded queue record; compact output unless --details is selected."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.queueing import analyze, load, VERSION


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record')
    parser.add_argument('--required', action='append')
    parser.add_argument('--details', action='store_true')
    args = parser.parse_args(argv)
    try:
        record, digest = load(args.record)
        report = analyze(record, args.required, details=args.details)
        report['input'] = {'path': str(Path(args.record).absolute()), 'sha256': digest}
    except (OSError, ValueError, TypeError, RecursionError, OverflowError):
        report = {'checker_version': VERSION, 'status': 'error', 'acceptance': 'not_evaluated',
                  'findings': [{'rule': 'queue_input', 'status': 'error',
                                'explanation': 'Cannot read a bounded regular UTF-8 JSON file with unique keys'}]}
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report['status'] == 'pass' else 2 if report['status'] == 'error' else 1


if __name__ == '__main__':
    raise SystemExit(main())
