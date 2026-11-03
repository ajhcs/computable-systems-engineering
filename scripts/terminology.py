#!/usr/bin/env python3
"""Check controlled English during drafting or compare a supported repair proposal."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.foundation import digest, load_profile, read_regular
from verifier.language import check_repair
from verifier.terminology import inspect, render_text, english_schema
from verifier.terminology_prepare import prepare_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('check')
    check.add_argument('model'); check.add_argument('--profile', required=True)
    check.add_argument('--review', action='store_true'); check.add_argument('--scope-sha256'); check.add_argument('--json', action='store_true')
    fingerprint = commands.add_parser('fingerprint', help='Identify selected rule/term scope; not approval')
    fingerprint.add_argument('profile')
    repair = commands.add_parser('repair', help='Compare bounded language-1.0 clause meanings; no edit applied')
    repair.add_argument('language_file'); repair.add_argument('--id', required=True); repair.add_argument('--replacement-file', required=True)
    prepare = commands.add_parser('prepare', help='Create a separate proposed English profile; no prose or retained review scope changed')
    prepare.add_argument('model'); prepare.add_argument('--profile', required=True)
    prepare.add_argument('--output', required=True); prepare.add_argument('--before-model')
    prepare.add_argument('--selection', help='Explicit offset-free initial selection over an existing vocabulary')
    prepare.add_argument('--revision', help='Explicit proposed draft revision; required for an existing English selection')
    args = parser.parse_args()
    try:
        if args.command == 'fingerprint':
            profile, _ = load_profile(args.profile); english_schema(profile['english'])
            print(json.dumps({'status': 'pass', 'claim_scope': 'scope_content_identity_only',
                              'scope_sha256': digest(profile['english']), 'acceptance': 'not_evaluated'}, sort_keys=True))
            return 0
        if args.command == 'prepare':
            result = prepare_profile(args.model, args.profile, args.output,
                selection_path=args.selection, before_model_path=args.before_model, revision=args.revision)
            print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')))
        elif args.command == 'repair':
            model, _ = load_profile(args.language_file)
            replacement = read_regular(args.replacement_file, 16384).decode('utf-8').strip()
            result = check_repair(model['requirements'][args.id], replacement, model['actors'], model['properties'], model['clock'], requirement_id=args.id)
            print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            result = inspect(args.model, args.profile, review=args.review, retained_scope_sha256=args.scope_sha256)
            print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) if args.json else render_text(result), end='\n' if args.json else '')
        return 0 if result['status'] == 'pass' else 1
    except (OSError, ValueError, UnicodeError, TypeError, KeyError, RecursionError) as exc:
        print(json.dumps({'status': 'error', 'detail': str(exc)}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
