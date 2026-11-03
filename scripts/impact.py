#!/usr/bin/env python3
"""Propose rechecks from explicit dependencies across retained model revisions."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.impact import inspect, render_text, scope_schema, snapshot_workflow, snapshot_native, MAX_WORK
from verifier.foundation import load_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    fingerprint = commands.add_parser('fingerprint'); fingerprint.add_argument('scope')
    check = commands.add_parser('check')
    check.add_argument('--before', required=True); check.add_argument('--after', required=True)
    check.add_argument('--scope', required=True); check.add_argument('--scope-sha256', required=True)
    check.add_argument('--max-work', type=int, default=MAX_WORK); check.add_argument('--json', action='store_true')
    snapshot = commands.add_parser('workflow-snapshot')
    snapshot.add_argument('record'); snapshot.add_argument('--revision', required=True)
    snapshot.add_argument('--model-sha256', required=True); snapshot.add_argument('--directions')
    snapshot.add_argument('--declared-complete', action='store_true')
    native = commands.add_parser('native-snapshot')
    native.add_argument('model', nargs='+'); native.add_argument('--revision', required=True)
    native.add_argument('--directions'); native.add_argument('--workflow', default='concept')
    args = parser.parse_args()
    if args.command in ('fingerprint', 'workflow-snapshot', 'native-snapshot'):
        try:
            if args.command == 'native-snapshot':
                directions = load_profile(args.directions)[0] if args.directions else None
                result = snapshot_native(args.model, args.revision, relation_directions=directions, workflow=args.workflow)
                print(json.dumps(result, indent=2, sort_keys=True)); return 0
            value, file_hash = load_profile(args.scope if args.command == 'fingerprint' else args.record)
            if args.command == 'fingerprint':
                scope_schema(value); result = {'status': 'pass', 'scope_sha256': file_hash, 'claim_scope': 'scope_byte_identity_only'}
            else:
                directions = load_profile(args.directions)[0] if args.directions else None
                result = snapshot_workflow(value, {'id': args.revision, 'sha256': args.model_sha256},
                    relation_directions=directions, complete=args.declared_complete)
            print(json.dumps(result, indent=2, sort_keys=True)); return 0
        except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
            print(json.dumps({'status': 'error', 'detail': str(exc)})); return 1
    result = inspect(args.before, args.after, args.scope, args.scope_sha256, max_work=args.max_work)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else render_text(result), end='\n' if args.json else '')
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__': raise SystemExit(main())
