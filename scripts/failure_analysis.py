#!/usr/bin/env python3
"""Check a bounded, explicitly authored Boolean failure/FMEA record."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.core import _pairs
from verifier.foundation import read_regular
from verifier.failure_analysis import analyze, CHECKS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model')
    parser.add_argument('--required', action='append', choices=CHECKS, default=None)
    args = parser.parse_args()
    try:
        raw = read_regular(args.model, 1_000_000)
        record = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite number: '+value)))
        result = analyze(record, args.required)
        if read_regular(args.model, 1_000_000) != raw:
            raise ValueError('Failure analysis input changed during checking; results discarded')
        result.update(input_sha256=sha256(raw).hexdigest(), input_path=str(Path(args.model).resolve()))
        print(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False))
        return 0 if result['status'] == 'pass' else 1
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
        print(json.dumps({'status': 'error', 'claim_scope': 'failure_analysis_input_or_operation',
                          'detail': str(exc), 'acceptance': 'not_evaluated'}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
