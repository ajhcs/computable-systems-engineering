#!/usr/bin/env python3
"""Run the shared CSE engine from the complete repository or plugin package."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
COMMANDS = {
    "check": "sysml.py",
    "testgen": "sysml_testgen.py",
    "view": "sysml_view.py",
    "diff": "sysml_diff.py",
    "finite": "verify.py",
    "install-parser": "install_sysml_parser.py",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=(*COMMANDS, "runtime"))
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not (ROOT / "verifier/sysml.py").is_file() or not (ROOT / "tools/sysml/SysmlBridge.java").is_file():
        print("The shared CSE runtime is missing. Use the complete repository or plugin package; "
              "copying a skill folder alone does not install "
              "the SysML checker.", file=sys.stderr)
        return 2
    if args.command == "runtime":
        print(json.dumps({"runtime_root": str(ROOT),
                          "profile": str(ROOT / "docs/sysml-v2-profile.md")}, sort_keys=True))
        return 0
    # Keep the caller's working directory: user model paths are not runtime paths.
    try:
        return subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / COMMANDS[args.command]),
                               *args.arguments], check=False).returncode
    except OSError as exc:
        print(f"Cannot run the CSE engine: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
