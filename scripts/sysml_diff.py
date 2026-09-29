#!/usr/bin/env python3
"""Show structural/text changes and conservative direct impact in SysML models."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verifier.views import diff_sysml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", action="append", required=True,
                        help="one file from the prior model; repeat for a bundle")
    parser.add_argument("--after", action="append", required=True,
                        help="one file from the revised model; repeat for a bundle")
    args = parser.parse_args()
    result = diff_sysml(args.before, args.after)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
