#!/usr/bin/env python3
"""Prepare and check a project-tailored concept review using existing CSE adapters."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.concept_review import (load, schema, starter, inspect_concept, scope_diff, render_text)
from verifier.foundation import read_regular
from verifier.workflow import draft_model, write_draft
from verifier.evidence_actions import next_evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init-scope', help='Create an incomplete project scope; no obligations inferred from the model')
    init.add_argument('output'); init.add_argument('--project', required=True); init.add_argument('--name', required=True)
    fingerprint = commands.add_parser('fingerprint', help='Identify authored scope bytes; not approval or scope completeness')
    fingerprint.add_argument('scope')
    diff = commands.add_parser('scope-diff', help='Show scope changes without accepting them')
    diff.add_argument('before'); diff.add_argument('after')
    prepare = commands.add_parser('prepare', help='Create a new authoritative model from explicit workflow input, preserving an optional native base')
    prepare.add_argument('input'); prepare.add_argument('output'); prepare.add_argument('--package', required=True)
    prepare.add_argument('--base')
    check = commands.add_parser('check', help='Check explicit coverage against the retained project scope revision')
    check.add_argument('model', nargs='+'); check.add_argument('--scope', required=True); check.add_argument('--scope-sha256', required=True)
    check.add_argument('--source', action='append', default=[], metavar='ID=PATH')
    check.add_argument('--json', action='store_true')
    actions = commands.add_parser('next-evidence', help='Derive unresolved evidence questions from a fresh scoped review; no plans executed')
    actions.add_argument('model', nargs='+'); actions.add_argument('--scope', required=True)
    actions.add_argument('--scope-sha256', required=True)
    actions.add_argument('--source', action='append', default=[], metavar='ID=PATH')
    args = parser.parse_args()
    try:
        if args.command == 'init-scope':
            scope = starter(args.project, args.name)
            with Path(args.output).open('x', encoding='utf-8') as stream:
                stream.write(json.dumps(scope, indent=2)+'\n')
            result = {'status':'unknown','claim_scope':'incomplete_project_scope_created',
                'path':args.output,'detail':'Tailor sources, question, boundary, topics and expectations before coverage review.'}
        elif args.command == 'fingerprint':
            scope, raw = load(args.scope); schema(scope)
            result = {'status':'pass','claim_scope':'scope_byte_identity_only',
                'project':scope['project']['id'],'scope_sha256':sha256(raw).hexdigest(),'acceptance':'not_evaluated'}
        elif args.command == 'scope-diff':
            before, _ = load(args.before); after, _ = load(args.after)
            result = scope_diff(before, after)
        elif args.command == 'prepare':
            record, _ = load(args.input)
            base_raw = read_regular(args.base,5_000_000) if args.base else None
            text = draft_model(record,args.package,None if base_raw is None else base_raw.decode('utf-8'))
            result = write_draft(args.output,text)
            if base_raw is not None and read_regular(args.base,5_000_000) != base_raw:
                raise ValueError('Base changed during preparation; new output is unverified')
        else:
            sources = {}
            for item in args.source:
                key, separator, path = item.partition('=')
                if not separator or not key or not path or key in sources:
                    raise ValueError('Source arguments need distinct ID=PATH entries')
                sources[key] = path
            result = inspect_concept(args.model,args.scope,args.scope_sha256,sources)
            if args.command == 'next-evidence':
                print(json.dumps(next_evidence(result),indent=2,sort_keys=True))
                return 0 if result['status']=='pass' else 1
            print(json.dumps(result,indent=2,sort_keys=True) if args.json else render_text(result),end='\n' if args.json else '')
            return 0 if result['status']=='pass' else 1
        print(json.dumps(result,indent=2,sort_keys=True))
        # Creating an explicitly incomplete draft is a successful operation,
        # not a coverage pass. All actual coverage non-successes exit nonzero.
        return 0
    except (OSError, ValueError, UnicodeError, TypeError, KeyError, RecursionError) as exc:
        print(json.dumps({'status':'error','claim_scope':'concept_review_input_or_operation',
            'detail':str(exc),'acceptance':'not_evaluated'},sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
