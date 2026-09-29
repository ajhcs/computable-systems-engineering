#!/usr/bin/env python3
"""Run standalone skill and finite-verifier suites with project-local temporary files."""
from pathlib import Path
import argparse
from hashlib import sha256
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-sysml", action="store_true", help="fail rather than skip when the pinned parser is unavailable")
    args = parser.parse_args()
    if args.require_sysml:
        cache = ROOT / ".cache/sysml"
        stamp = cache / "classes/SysmlBridge.source.sha256"
        source = ROOT / "tools/sysml/SysmlBridge.java"
        if (not (cache / "pilot-2025-09/sysml/jupyter-sysml-kernel-0.52.0-all.jar").is_file() or
                not (cache / "classes/SysmlBridge.class").is_file() or not stamp.is_file() or
                stamp.read_text().strip() != sha256(source.read_bytes()).hexdigest()):
            print("FAIL: the pinned SysML parser/bridge is missing or stale; run scripts/install_sysml_parser.py", file=sys.stderr)
            return 1
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
    for relative in ("scripts/cse.py", "references/sysml.md"):
        copies = [ROOT / "skills" / skill / relative for skill in
                  ("develop-system-concept", "develop-conops", "develop-operational-scenarios")]
        if len({path.read_bytes() for path in copies}) != 1:
            print(f"FAIL: shared skill copies differ: {relative}", file=sys.stderr)
            return 1
    suites = ("test_develop_conops.py", "test_scenario_split.py", "test_concept.py", "test_verifier.py",
              "test_language.py", "test_language_oracle.py", "test_influence.py", "test_events.py",
              "test_public_language_cases.py", "test_sysml.py", "test_sysml_views.py",
              "test_sysml_public.py", "test_skill_runtime.py")
    for suite in suites:
        result = subprocess.run([sys.executable, "-B", str(ROOT / "tests" / suite)],
                                cwd=ROOT, env=environment, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout
        if result.returncode:
            print(output, end="")
            return result.returncode
        summary = next((line for line in output.splitlines() if line.startswith("Ran ")), "completed")
        skips = next((line for line in output.splitlines() if line.startswith("OK (skipped=")), None)
        print(f"{'SKIP' if skips else 'PASS'} {suite}: {summary}" + (f"; {skips}" if skips else ""), flush=True)
    print("All helper and finite-verifier checks passed. Protected execution remains a separate milestone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
