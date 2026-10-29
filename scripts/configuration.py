#!/usr/bin/env python3
"""Reconcile an explicitly selected native context against retained configuration scope."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.configuration import inspect_configuration, render_text, schema
from verifier.foundation import load_profile
from verifier.configuration_view import write_view, check_view


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    fingerprint = commands.add_parser('fingerprint'); fingerprint.add_argument('scope')
    for command in ('check', 'view', 'check-view'):
        check = commands.add_parser(command); check.add_argument('model', nargs='+')
        check.add_argument('--scope', required=True); check.add_argument('--scope-sha256', required=True)
        check.add_argument('--expected-model-sha256'); check.add_argument('--json', action='store_true')
        if command == 'view':check.add_argument('--output',required=True,help='new directory for editable SVG, HTML reader and source ledger')
        if command == 'check-view':check.add_argument('--view',required=True,help='existing generated view directory to compare with fresh native reconciliation')
    args = parser.parse_args()
    if args.command == 'fingerprint':
        try:
            scope, digest = load_profile(args.scope); schema(scope)
            print(json.dumps({'status': 'pass', 'scope_sha256': digest, 'claim_scope': 'scope_byte_identity_only'})); return 0
        except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
            print(json.dumps({'status': 'error', 'detail': str(exc)})); return 1
    report = inspect_configuration(args.model, args.scope, args.scope_sha256, expected_model_sha256=args.expected_model_sha256)
    if args.command in ('view','check-view'):
        try:
            result = write_view(report,args.output) if args.command == 'view' else check_view(report,args.view)
        except (OSError,ValueError,TypeError,KeyError) as exc:
            result={'status':'error','configuration_status':report['status'],'findings':[{'rule':'view_input','status':'error','detail':str(exc)}]}
        print(json.dumps(result,sort_keys=True,indent=2) if args.json else result['status']+': current-system view '+('created at '+str(args.output) if args.command == 'view' and result['status']!='error' else 'checked')+'\n'+'\n'.join(f.get('detail','') for f in result.get('findings',[])))
        return 0 if result['status']=='pass' else 1
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else render_text(report), end='\n' if args.json else '')
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__': raise SystemExit(main())
