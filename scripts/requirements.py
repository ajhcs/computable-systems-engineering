#!/usr/bin/env python3
"""Check an opt-in controlled-requirements language file."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.core import load_json
from verifier.language import check_document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--manifest", help="independent expected-obligation manifest; required with --review")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.review and not args.manifest:
        parser.error("--review requires --manifest")
    try:
        model = load_json(args.file)
        expected = load_json(args.manifest) if args.manifest else None
    except (OSError, ValueError) as exc:
        print(f"Cannot read model: {exc}", file=sys.stderr)
        return 2
    report = check_document(model, review=args.review, expected=expected)
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        print(f"{report['status']} ({report['claim_scope']}): {len(report['results'])} requirement(s)")
        if "error" in report:
            print(f"{report['error']['code']}: {report['error']['detail']}")
        for key, item in report["results"].items():
            print(f"  {key}: {item['status']}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
