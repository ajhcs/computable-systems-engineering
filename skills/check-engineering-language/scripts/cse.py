#!/usr/bin/env python3
"""Invoke the shared English checker independently of the drafting skills."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def main():
    script = ROOT/'scripts/terminology.py'
    if not script.is_file():
        print('The shared CSE runtime is missing. Use the complete repository or plugin package.', file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, '-B', str(script), *sys.argv[1:]], check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
