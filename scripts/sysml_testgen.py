#!/usr/bin/env python3
"""Generate and inspect bounded synthetic property-influence tests from SysML."""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.core import load_json
from verifier.sysml import check_sysml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="+", help="authoritative .sysml model file(s)")
    parser.add_argument("--manifest", help="independent expected-obligation manifest, if available")
    parser.add_argument("--max-rows", type=int, default=16)
    parser.add_argument("--evaluation-cap", type=int, default=2000)
    parser.add_argument("--json", action="store_true", help="print complete synthetic test report")
    parser.add_argument("--output", help="write complete synthetic test report as JSON")
    args = parser.parse_args()
    try:
        manifest = load_json(args.manifest) if args.manifest else None
    except (OSError, ValueError) as exc:
        print(f"Cannot read manifest: {exc}", file=sys.stderr)
        return 2
    report = check_sysml(args.model, manifest=manifest, generate_tests=True,
                         test_max_rows=args.max_rows, test_evaluation_cap=args.evaluation_cap)
    generation = report["test_generation"]
    status = report["status"] if report["status"] != "pass" else generation["status"]
    artifact = {"status": status, "claim_scope": "synthetic_tests_not_supplied_behavior_evidence",
                "synthetic": True, "model_sha256": report.get("model_sha256"),
                "model_files": report.get("model_files", []), "parser": report["parser"],
                "compilation_status": report["status"], "findings": report["findings"],
                "coverage": report["coverage"], "generation": generation}
    if "source_revision" in report:
        artifact["source_revision"] = report["source_revision"]
    serialized = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    if args.output:
        destination = Path(args.output)
        protected = {Path(model).resolve() for model in args.model}
        if args.manifest:
            protected.add(Path(args.manifest).resolve())
        if destination.resolve() in protected:
            print("Test report output cannot overwrite a model or manifest", file=sys.stderr)
            return 2
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent,
                                             prefix=".sysml-tests-", delete=False) as temporary:
                temporary.write(serialized)
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, destination)
        except OSError as exc:
            if "temporary_path" in locals():
                temporary_path.unlink(missing_ok=True)
            print(f"Cannot write test report: {exc}", file=sys.stderr)
            return 2
    if args.json:
        print(serialized, end="")
    else:
        print(f"{status}: synthetic variable-influence tests, not observed behavior; model {artifact['model_sha256']}")
        for key, result in generation["results"].items():
            if "variables" not in result:
                print(f"  {key}: {result['status']} ({result.get('reason', '')})")
                continue
            covered = result["coverage"]
            print(f"  {key}: {covered['witnessed']}/{covered['referenced']} variables have pass/fail witnesses")
            for name, item in result["variables"].items():
                print(f"    {name}: {item['status']}")
        for finding in report["findings"]:
            print(f"  {finding['code']}: {finding['detail']}")
        if args.output:
            print(f"  exported: {args.output}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
