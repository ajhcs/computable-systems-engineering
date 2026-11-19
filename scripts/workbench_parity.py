#!/usr/bin/env python3
"""Inspect capability progression; require --require-complete for a release gate."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.core import load_json
from verifier.workbench_parity import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger', nargs='?', default=str(ROOT / 'docs/workbench/parity.json'))
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    try:
        report = inspect(load_json(args.ledger), ROOT)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        report = {'status': 'error', 'findings': [{'reason': str(exc)}]}
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'pass' and (not args.require_complete or report['workbench_complete']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
