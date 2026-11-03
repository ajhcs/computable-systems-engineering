#!/usr/bin/env python3
"""Capture and check the freshness of an explicit engineering artifact bundle."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier import artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('begin', 'finish', 'check'))
    parser.add_argument('--root', required=True, help='project directory containing declared paths')
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', help='separately retained plan digest; required after begin')
    parser.add_argument('--receipt', help='started receipt for finish; complete receipt for check')
    parser.add_argument('--out', help='new receipt path; existing files are never overwritten')
    args = parser.parse_args()
    if args.operation == 'begin' and (args.receipt or not args.out):
        parser.error('begin requires --out and no --receipt')
    if args.operation != 'begin' and (not args.receipt or not args.plan_sha256):
        parser.error('finish/check require --receipt and --plan-sha256')
    if (args.operation == 'finish' and not args.out) or (args.operation == 'check' and args.out):
        parser.error('finish requires --out; check is read-only')
    try:
        plan, digest = artifacts.load(args.plan)
        artifacts.validate_plan(plan)
        if args.plan_sha256 is not None and digest != args.plan_sha256:
            raise artifacts.Invalid('Plan differs from its retained digest')
        if args.out:
            output = Path(args.out).absolute()
            reserved = [Path(args.plan).absolute()] + ([Path(args.receipt).absolute()] if args.receipt else [])
            reserved += [artifacts._path(args.root, p).absolute() for group in ('inputs', 'outputs') for p in plan[group].values()]
            if output.resolve() in {p.resolve() for p in reserved}:
                raise artifacts.Invalid('Receipt output must be separate from plan and declared artifacts')
        if args.operation == 'begin':
            result = artifacts.begin(args.root, plan, digest)
        else:
            receipt, _ = artifacts.load(args.receipt)
            result = getattr(artifacts, args.operation)(args.root, plan, digest, receipt)
        # Check again before writing: changing the selected plan cannot narrow scope.
        if artifacts.load(args.plan)[1] != digest:
            raise artifacts.Invalid('Plan changed during the operation')
        if args.out:
            with open(args.out, 'x', encoding='utf-8') as stream:
                stream.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
            result = {'status': 'pass', 'phase': result['phase'], 'claim_scope': artifacts.CLAIM,
                      'plan_sha256': digest, 'receipt': str(Path(args.out).resolve())}
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        print(json.dumps({'status': 'error', 'claim_scope': artifacts.CLAIM, 'detail': str(exc)}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
