#!/usr/bin/env python3
"""Print a native view or assemble source-bound concept and workflow context."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.views import view_sysml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="+", help="all SysML files needed for this model")
    selected = parser.add_mutually_exclusive_group(required=True)
    selected.add_argument("--id", help="short ID of concern, use case, or requirement")
    selected.add_argument("--element", help="exact foundation/workflow element ID; optional foundation: or workflow: prefix")
    selected.add_argument("--native-name", help="exact qualified native identity")
    parser.add_argument("--context", action="store_true", help="assemble existing definitions, bindings and workflow context")
    parser.add_argument("--profile", help="existing foundation/English profile; enables assembled context")
    parser.add_argument("--workflow", choices=("concept", "scenarios", "requirements", "architecture", "trade-study"), default="concept")
    parser.add_argument("--limit", type=int, default=32, help="maximum native identities in assembled context, 1..512")
    parser.add_argument("--source", action="append", default=[], metavar="ID=PATH", help="explicit workflow source file; repeat for distinct IDs")
    args = parser.parse_args()
    sources = {}
    for value in args.source:
        identity, separator, path = value.partition("=")
        if not separator or not identity or not path or identity in sources:
            print(json.dumps({"status": "error", "detail": "Each --source needs a distinct nonempty ID=PATH"}, sort_keys=True))
            return 1
        sources[identity] = path
    result = view_sysml(args.model, args.id, context=args.context,
                        profile_path=args.profile, element_id=args.element,
                        native_name=args.native_name, workflow=args.workflow,
                        limit=args.limit, sources=sources)
    if result.get('version') == 'assembled-context-1.0':
        from verifier.context import render_context_json
        sys.stdout.write(render_context_json(result))
    else:
        print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
