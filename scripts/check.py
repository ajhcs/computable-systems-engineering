#!/usr/bin/env python3
"""Run standalone skill and finite-verifier suites with project-local temporary files."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    temporary = ROOT / ".tmp"
    temporary.mkdir(exist_ok=True)
    environment = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                       PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(temporary),
                       TMP=str(temporary), TEMP=str(temporary))
    for relative in ("scripts/conops.py", "references/record.md"):
        conops = ROOT / "skills/develop-conops" / relative
        scenarios = ROOT / "skills/develop-operational-scenarios" / relative
        if conops.read_bytes() != scenarios.read_bytes():
            print(f"FAIL: standalone skill copies differ: {relative}", file=sys.stderr)
            return 1
    suites = ("test_develop_conops.py", "test_scenario_split.py", "test_concept.py", "test_verifier.py")
    for suite in suites:
        result = subprocess.run([sys.executable, "-B", str(ROOT / "tests" / suite)],
                                cwd=ROOT, env=environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout
        if result.returncode:
            print(output, end="")
            return result.returncode
        summary = next((line for line in output.splitlines() if line.startswith("Ran ")), "completed")
        print(f"PASS {suite}: {summary}", flush=True)
    print("All helper and finite-verifier checks passed. Protected execution remains a separate milestone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
