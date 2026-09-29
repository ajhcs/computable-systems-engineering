#!/usr/bin/env python3
"""Print a bounded context view for one stable SysML short ID."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.views import view_sysml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", nargs="+", help="all SysML files needed for this model")
    parser.add_argument("--id", required=True, help="short ID of concern, use case, or requirement")
    args = parser.parse_args()
    result = view_sysml(args.model, args.id)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
