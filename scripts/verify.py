#!/usr/bin/env python3
"""CLI for the opt-in version-2 finite verifier."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier import focused_view, load_json, verify


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--assignment-cap", type=int, default=100000)
    parser.add_argument("--state-cap", type=int, default=100000)
    parser.add_argument("--evidence")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--detail", action="store_true")
    parser.add_argument("--view", action="store_true", help="print a context view of selected scenarios; not a verdict")
    args = parser.parse_args(argv)
    if args.assignment_cap < 1 or args.state_cap < 1:
        parser.error("caps must be positive")
    try:
        model = load_json(args.model)
        if args.view:
            print(json.dumps(focused_view(model, args.scenario), sort_keys=True, indent=2))
            return 0
        evidence = load_json(args.evidence) if args.evidence else None
        report = verify(model, review=args.review, selected=args.scenario,
                        assignment_cap=args.assignment_cap, state_cap=args.state_cap, evidence=evidence)
    except (OSError, ValueError, TypeError) as error:
        print(f"Input error: {error}", file=sys.stderr)
        return 2
    if args.json:
        if not args.detail:
            for item in report["findings"]:
                item.pop("evidence", None)
            report.pop("rendered_requirements", None)
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        print(f"{report['status'].upper()} {report['artifact_sha256']} scope={report['scope']['scenarios']} "
              f"completed={','.join(report['completed_obligations']) or '-'}")
        for item in report["findings"]:
            print(f"{item['status']} {item['rule']} [{','.join(item['ids'])}]: {item['explanation']}")
            if args.detail and "evidence" in item:
                print("  " + json.dumps(item["evidence"], sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
