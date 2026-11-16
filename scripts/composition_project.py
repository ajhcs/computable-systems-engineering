#!/usr/bin/env python3
"""Persist physical composition and render saved native views from a local Git project.

This local reference has no account authorization, network service or host UI.
Use an explicit private project directory on the selected workspace filesystem.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier.composition_edit import EditError
from verifier.composition_project import CompositionProject
from verifier.composition_records import strict_json
from verifier.core import _pairs
from verifier.foundation import read_regular


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('import', 'inspect', 'apply', 'history', 'render', 'check-render'))
    parser.add_argument('--project', required=True, help='trusted server-side bare Git directory')
    parser.add_argument('--bundle', help='explicit cse-composition-bundle-1 input')
    parser.add_argument('--project-id')
    parser.add_argument('--request-id')
    parser.add_argument('--request', help='exact typed operation JSON file')
    parser.add_argument('--view-id', help='native CSE-VIEWS/1.1 physical view')
    parser.add_argument('--output', help='explicit immutable artifact directory')
    args = parser.parse_args()
    try:
        if args.command in ('render', 'check-render'):
            if not args.view_id or not args.output or any((args.bundle, args.project_id, args.request_id, args.request)):
                raise EditError('input', 'Rendering requires a view ID and output directory')
        elif args.view_id or args.output:
            raise EditError('input', 'View/output fields apply only to rendering')
        project = CompositionProject(args.project)
        if args.command == 'import':
            if not all((args.bundle, args.project_id, args.request_id)) or args.request:
                raise EditError('input', 'Import requires bundle, project UUID and request UUID')
            bundle = json.loads(read_regular(args.bundle, 32_000_000).decode('utf-8'), object_pairs_hook=_pairs,
                                parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))
            if (not isinstance(bundle, dict) or set(bundle) != {'version', 'models', 'linked_records'}
                    or bundle['version'] != 'cse-composition-bundle-1'):
                raise EditError('input', 'Expected an explicit composition bundle')
            _, receipt = CompositionProject.create(args.project, bundle['models'], linked_records=bundle['linked_records'],
                                                   project_id=args.project_id, request_id=args.request_id)
            report = {'receipt': receipt}
        else:
            if args.bundle or args.project_id or args.request_id:
                raise EditError('input', 'These import fields do not apply to this command')
            if args.command == 'apply':
                if not args.request:
                    raise EditError('input', 'Apply requires an operation JSON file')
                request = strict_json(read_regular(args.request, 1_000_000).decode('utf-8'))
                report = {'receipt': project.transact(request)}
            else:
                if args.request:
                    raise EditError('input', 'Request JSON applies only to apply')
                if args.command in ('render', 'check-render'):
                    from verifier.composition_view import write_artifacts, check_artifacts
                    operation = write_artifacts if args.command == 'render' else check_artifacts
                    report = operation(project.snapshot(), args.view_id, args.output)
                elif args.command == 'history':
                    report = {'history': project.history()}
                else:
                    snapshot = project.snapshot()
                    document = snapshot['document']
                    report = {'commit': snapshot['commit'], 'revision': snapshot['revision'],
                              'receipt': snapshot['receipt'], **document.inspect(),
                              'files': document.files, 'linked_records': document.linked_records,
                              'registry': document.registry}
        report = {'status': 'pass', 'claim': 'local_composition_project_only', **report}
    except (ValueError, OSError, TypeError, RecursionError) as exc:
        report = {'status': 'error', 'error': {'code': getattr(exc, 'code', 'input'), 'detail': str(exc)}}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
