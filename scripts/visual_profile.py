#!/usr/bin/env python3
"""Validate an explicitly selected visual profile or preflight its local resources."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier import visual_profile as v


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('validate', 'preflight'))
    parser.add_argument('--root', default='.', help='project root for relative resource paths')
    parser.add_argument('--runtime', help='plugin root for runtime: resource paths')
    parser.add_argument('--profile', help='explicit whole-profile selection; highest priority')
    parser.add_argument('--client-profile')
    parser.add_argument('--project-profile')
    parser.add_argument('--example-profile', help='optional example, only if no other profile was selected')
    parser.add_argument('--out', help='new JSON receipt; existing files are not overwritten')
    args = parser.parse_args()
    try:
        source, selected = v.select_profile(args.profile, args.client_profile,
                                            args.project_profile, args.example_profile)
        path = Path(selected)
        if not path.is_absolute(): path = Path(args.root) / path
        profile, digest = v.load(path)
        v.validate_profile(profile)
        if args.operation == 'preflight':
            result = v.preflight(profile, args.root, args.runtime)
        else:
            result = {'version': v.VERSION, 'status': 'pass', 'claim_scope': 'visual_profile_structure_only',
                      'profile': profile, 'findings': []}
        if v.load(path)[1] != digest:
            raise v.Invalid('Selected profile changed during checking')
        result.update({'profile_sha256': digest, 'profile_path': str(path.resolve()),
                       'selection': source})
        if args.out:
            output = Path(args.out).resolve()
            reserved = {path.resolve()}
            reserved.update(Path(entry['resolved_path']) for group in ('fonts', 'assets')
                            for entry in result.get(group, []))
            if output in reserved: raise v.Invalid('Receipt must be separate from selected inputs')
            with output.open('x', encoding='utf-8') as stream:
                # Typography role order is CSS cascade precedence. Alphabetizing
                # profile-bearing JSON would change the selected presentation.
                stream.write(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))
        return 0 if result['status'] == 'pass' else 1
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        print(json.dumps({'status': 'error', 'claim_scope': v.CLAIM, 'detail': str(exc)}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
