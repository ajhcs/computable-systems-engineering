#!/usr/bin/env python3
"""One bounded access probe using the existing login; no task-success claim."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / ".cache/interface-benchmark/access-probe"
folder.mkdir(parents=True, exist_ok=True)
command = ["/home/builderbob/.local/bin/codex", "exec", "--ephemeral", "--ignore-user-config", "--strict-config",
           "--json", "--skip-git-repo-check", "-C", str(folder), "--sandbox", "read-only",
           "-m", "gpt-6.1-sol", "-c", 'service_tier="default"', "-c", 'model_reasoning_effort="medium"',
           "-c", 'web_search="disabled"', "-c", 'approval_policy="never"',
           "Return exactly READY. This is an access probe. Do not use tools or read files."]
try:
    run = subprocess.run(command, input="", text=True, capture_output=True, timeout=90)
    result = {"command": command[:-1], "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
except subprocess.TimeoutExpired as exc:
    result = {"status": "timeout", "stdout": (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else exc.stdout,
              "stderr": (exc.stderr or b"").decode() if isinstance(exc.stderr, bytes) else exc.stderr}
destination = folder / "result.json"
if destination.exists():
    destination = folder / "result-2.json"
destination.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
