#!/usr/bin/env python3
"""Inspect physical composition or prepare a source-preserving edit candidate.

Candidate output is not committed project state. Use composition_project.py for
local durable transactions; hosted/application parity remains open.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import CompositionDocument, EditError
from verifier.core import _pairs
from verifier.core import load_json
from verifier.foundation import read_regular


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'rename', 'set-multiplicity', 'create-definition', 'create-usage'))
    parser.add_argument('model', nargs='?')
    parser.add_argument('--bundle', help='explicit versioned model/linked-record text bundle')
    parser.add_argument('--project-id', required=True)
    parser.add_argument('--registry')
    parser.add_argument('--element-id')
    parser.add_argument('--name')
    parser.add_argument('--owner-id')
    parser.add_argument('--short-id')
    parser.add_argument('--type-id', help='part-definition UUID; omit for no explicit typing')
    parser.add_argument('--usage-kind', choices=('composite', 'reference'))
    parser.add_argument('--view-id')
    parser.add_argument('--placement', help='optional exact box/points JSON; otherwise checked automatic placement')
    parser.add_argument('--lower', type=int)
    parser.add_argument('--upper', type=int)
    parser.add_argument('--expected-source-sha256')
    parser.add_argument('--expected-bundle-sha256')
    args = parser.parse_args()
    try:
        if bool(args.model) == bool(args.bundle):
            raise EditError('input', 'Supply one model file or --bundle')
        linked = None
        if args.bundle:
            bundle = json.loads(read_regular(args.bundle, 32_000_000).decode('utf-8'), object_pairs_hook=_pairs,
                                parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
            if (not isinstance(bundle, dict) or set(bundle) != {'version', 'models', 'linked_records'}
                    or bundle['version'] != 'cse-composition-bundle-1' or not isinstance(bundle['models'], dict)):
                raise EditError('input', 'Expected cse-composition-bundle-1 models and linked_records')
            source, linked = bundle['models'], bundle['linked_records']
        else:
            source = read_regular(args.model, 5_000_000).decode('utf-8')
        document = CompositionDocument(source, project_id=args.project_id,
                                       registry=load_json(args.registry) if args.registry else None,
                                       linked_records=linked)
        if args.command != 'inspect':
            expected = args.expected_bundle_sha256 if args.bundle else args.expected_source_sha256
            if (not all((args.element_id, expected))
                    or args.bundle and args.expected_source_sha256
                    or not args.bundle and args.expected_bundle_sha256):
                raise EditError('input', 'Edit needs element ID and expected source or bundle SHA-256')
            if args.command == 'rename':
                document = document.rename(args.element_id, args.name, expected_source_sha256=expected)
            elif args.command == 'create-definition':
                document = document.create_definition(args.owner_id, args.element_id, args.name, args.short_id,
                    args.view_id, load_json(args.placement) if args.placement else None, expected_source_sha256=expected)
            elif args.command == 'create-usage':
                if args.usage_kind is None or (args.lower is None) != (args.upper is None):
                    raise EditError('input', 'Choose --usage-kind and supply both bounds or neither')
                document = document.create_usage(args.owner_id, args.element_id, args.name, args.short_id,
                    args.type_id, args.usage_kind == 'composite',
                    None if args.lower is None else {'lower':args.lower, 'upper':args.upper},
                    args.view_id, load_json(args.placement) if args.placement else None, expected_source_sha256=expected)
            else:
                document = document.set_multiplicity(args.element_id, args.lower, args.upper,
                                                     expected_source_sha256=expected)
        report = {'status': 'pass', 'claim': 'candidate_only_not_persisted',
                  **document.inspect(), 'registry': document.registry}
        if args.command != 'inspect':
            if args.bundle:
                report['files'] = document.files
                report['linked_records'] = document.linked_records
            else:
                report['source'] = document.source
                if document.linked_records:
                    report['linked_records'] = document.linked_records
    except (ValueError, OSError, TypeError, RecursionError) as exc:
        report = {'status': 'error', 'error': {'code': getattr(exc, 'code', 'input'), 'detail': str(exc)}}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
