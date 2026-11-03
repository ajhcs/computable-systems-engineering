#!/usr/bin/env python3
"""Run selected reusable CSE analyses, returning compact deterministic JSON."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.core import _pairs
from verifier.foundation import read_regular


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('analysis', choices=('calculations', 'functional-graph'))
    parser.add_argument('model')
    parser.add_argument('--required', action='append', default=None, metavar='CHECK_ID',
                        help='Retain an independently selected expected calculation check ID (repeatable)')
    parser.add_argument('--native-model', action='append', default=[], metavar='MODEL.sysml',
                        help='Explicit native source model for functional-graph correspondence (repeatable)')
    parser.add_argument('--native-bindings', metavar='BINDINGS.json',
                        help='Retained explicit native/finite correspondence; required with --native-model')
    args = parser.parse_args()
    try:
        raw = read_regular(args.model, 1_000_000)
        # Reuse the existing duplicate-key and nonfinite-number rejection.
        record = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite number: '+value)))
        if args.analysis == 'calculations':
            if args.native_model or args.native_bindings:
                raise ValueError('Native correspondence options apply only to functional-graph')
            from verifier.calculations import analyze
            result = analyze(record, args.required)
        else:
            if args.required:
                raise ValueError('--required applies only to calculations; graph scope follows its explicit record contract')
            if bool(args.native_model) != bool(args.native_bindings):
                raise ValueError('Native correspondence needs both --native-model and --native-bindings')
            if args.native_bindings:
                from verifier.function_native import inspect
                binding_raw = read_regular(args.native_bindings, 1_000_000)
                binding = json.loads(binding_raw.decode('utf-8'), object_pairs_hook=_pairs,
                    parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite native binding')))
                result = inspect(record, binding, args.native_model)
                if read_regular(args.native_bindings, 1_000_000) != binding_raw:
                    raise ValueError('Native binding file changed during checking; results discarded')
                result['native_binding']['input_sha256'] = sha256(binding_raw).hexdigest()
            else:
                from verifier.function_flow import analyze
                result = analyze(record)
        if read_regular(args.model, 1_000_000) != raw:
            raise ValueError('Analysis input changed during checking; results discarded')
        result['input_sha256'] = sha256(raw).hexdigest()
        result['input_path'] = str(Path(args.model).resolve())
        print(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False))
        return 0 if result['status'] == 'pass' else 1
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, RecursionError) as exc:
        print(json.dumps({'status': 'error', 'claim_scope': 'analysis_input_or_operation',
                          'detail': str(exc), 'acceptance': 'not_evaluated'}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
