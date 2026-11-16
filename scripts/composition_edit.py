#!/usr/bin/env python3
"""Inspect physical composition or prepare a source-preserving rename candidate.

Candidate output is not committed project state. Project transactions and host
interfaces remain outstanding parity obligations.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import CompositionDocument, EditError
from verifier.core import load_json
from verifier.foundation import read_regular


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'rename'))
    parser.add_argument('model')
    parser.add_argument('--project-id', required=True)
    parser.add_argument('--registry')
    parser.add_argument('--element-id')
    parser.add_argument('--name')
    parser.add_argument('--expected-source-sha256')
    args = parser.parse_args()
    try:
        source = read_regular(args.model, 5_000_000).decode('utf-8')
        document = CompositionDocument(source, project_id=args.project_id,
                                       registry=load_json(args.registry) if args.registry else None)
        if args.command == 'rename':
            if not all((args.element_id, args.name, args.expected_source_sha256)):
                raise EditError('input', 'Rename needs element ID, name, and expected source SHA-256')
            document = document.rename(args.element_id, args.name,
                                       expected_source_sha256=args.expected_source_sha256)
        report = {'status': 'pass', 'claim': 'candidate_only_not_persisted',
                  **document.inspect(), 'registry': document.registry}
        if args.command == 'rename':
            report['source'] = document.source
    except (ValueError, OSError) as exc:
        report = {'status': 'error', 'error': {'code': getattr(exc, 'code', 'input'), 'detail': str(exc)}}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
