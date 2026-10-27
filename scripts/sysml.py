#!/usr/bin/env python3
"""Parse and check a SysML v2 model with the bounded CSE profile."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.core import load_json
from verifier.sysml import check_sysml
from verifier.sysml_batch import inspect_batch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="+", help="authoritative .sysml file(s), parsed as one model")
    parser.add_argument("--manifest", help="independent expected-obligation manifest")
    parser.add_argument("--evidence", help="sampled observations bound to the SysML digest")
    parser.add_argument("--review", action="store_true", help="require evidence and independent scope")
    parser.add_argument("--syntax-only", action="store_true", help="check SysML syntax and references without compiling CSE clauses")
    parser.add_argument("--kind", choices=("concept", "conops", "scenario"),
                        help="also check the minimal model shape for this skill")
    parser.add_argument("--view-profile", help="explicit task requirements for documentary function trees/sequences")
    parser.add_argument("--json", action="store_true")
    parser.add_argument('--evidence-case', action='append', default=[], metavar='ID=PATH')
    parser.add_argument('--manifest-sha256', help='retained manifest byte digest for batch')
    args = parser.parse_args()
    if args.evidence_case:
        if not args.manifest or not args.manifest_sha256 or args.evidence or args.syntax_only or args.kind or args.view_profile:
            parser.error('Trace batch needs manifest/digest and separate cases; no single evidence, shape or syntax-only mode')
        cases={}
        for item in args.evidence_case:
            key,sep,path=item.partition('=')
            if not sep or not key or not path or key in cases:
                parser.error('Trace cases need distinct ID=PATH entries')
            cases[key]=path
        report=inspect_batch(args.model,args.manifest,args.manifest_sha256,cases)
        print(json.dumps(report,sort_keys=True,indent=2))
        return 0 if report['status']=='pass' and report['results_usable'] else 1
    if args.manifest_sha256:
        parser.error('--manifest-sha256 is used only with --evidence-case')
    try:
        view_profile = load_json(args.view_profile) if args.view_profile is not None else None
        if args.view_profile is not None and not isinstance(view_profile, dict):
            raise ValueError("View profile must be a JSON object, not null or another JSON value")
        manifest = load_json(args.manifest) if args.manifest else None
        evidence = load_json(args.evidence) if args.evidence else None
    except (OSError, ValueError) as exc:
        print(f"Cannot read input: {exc}", file=sys.stderr)
        return 2
    report = check_sysml(args.model, manifest=manifest, evidence=evidence, review=args.review,
                         syntax_only=args.syntax_only, kind=args.kind, view_profile=view_profile)
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        scope = report["claim_scope"]
        if scope.startswith("sysml_syntax"):
            description = "SysML parsing and structural checks" + (f"; {args.kind} draft structure" if args.kind else "")
            description += "; no behavior evaluated"
        elif scope == "sysml_and_controlled_text_compilation":
            description = "controlled requirement grammar and bindings; no behavior evaluated"
        else:
            description = "supplied behavior evidence"
        print(f"{report['status']}: {description}, {len(report['results'])} compiled obligation(s)")
        if "view_checks" in report:
            print(f"  documentary view structure: {report['view_checks']['status']}; action names, exchange meaning, and engineering adequacy need human review")
            for exception in report['view_checks']['exceptions']:
                print(f"    exception {exception['view']}/{exception['rule']}/{exception['target']}: {exception['rationale']}")
        issues = report.get("parser_issues", [])
        for issue in issues[:8]:
            print(f"  {issue.get('severity', 'ISSUE')} {issue.get('source')}:{issue.get('line')}: {issue.get('message')}")
        if len(issues) > 8:
            print(f"  {len(issues) - 8} further parser diagnostics; use --json for details")
        for finding in report["findings"]:
            location = f" {finding['source']}" if "source" in finding else ""
            location += f":{finding['line']}" if "line" in finding else ""
            print(f"  {finding['code']}{location}: {finding['detail']}")
        for key, result in report["results"].items():
            print(f"  {key}: {result['check']['status']}")
            detail = result["check"].get("results", {}).get(key, result["check"])
            if detail.get("reason"):
                print(f"    {detail['reason']}")
            if "coverage" in detail:
                print(f"    exercised condition(s): {detail['coverage'].get('triggers', 0)}")
            if "counterexample" in detail:
                print(f"    counterexample: {json.dumps(detail['counterexample'], sort_keys=True)}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
