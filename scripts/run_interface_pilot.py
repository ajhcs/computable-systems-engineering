#!/usr/bin/env python3
"""Run one isolated Standard pilot condition; never read private session stores."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tarfile
import time

from benchmark_accounting import summarize_events, score_completion

ROOT = Path(__file__).resolve().parents[1]
REVISIONS = {"baseline": "b01ef01698450e5a47cc20f957fe93a09e9744b4", "optimized": "2e3525cd5042e793d44d2f4bdf9be76dfc4b0895"}
CODEX = "/home/builderbob/.local/bin/codex"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def prepare(condition, replicate):
    root = ROOT / ".cache/interface-benchmark/trials" / f"{condition}-{replicate}"
    if root.exists():
        raise ValueError("Trial already exists; retain its evidence and choose a new replicate")
    root.mkdir(parents=True)
    archive = subprocess.check_output(["git", "archive", REVISIONS[condition]], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        # Archive consists only of this user's pinned Git tree. Reject absolute/traversal members.
        for member in bundle.getmembers():
            if Path(member.name).is_absolute() or ".." in Path(member.name).parts:
                raise ValueError("Unsafe archive member")
        bundle.extractall(root, filter="data")
    shutil.copytree(ROOT / ".cache/sysml", root / ".cache/sysml")
    inputs = root / "inputs"
    inputs.mkdir()
    records = json.loads((ROOT / "benchmarks/interface/corpus-lock.json").read_text())["sources"]
    hashes = {}
    for record in records:
        if record["id"] not in ("sysml-ev", "nasa-jt9d"):
            continue
        if record["license_identifier"] not in ("Apache-2.0", "EPL-2.0"):
            raise ValueError("License review required before model use")
        for key in ("model", "license", "readme"):
            entry = record[key]
            source = ROOT / entry["cache_path"]
            if digest(source) != entry["sha256"]:
                raise ValueError("Pinned public bytes changed: " + str(source))
            name = source.name if key == "model" else record["id"] + "-" + source.name
            shutil.copyfile(source, inputs / name)
            hashes[name] = entry["sha256"]
    for source in (ROOT / ".cache/interface-benchmark/corpus/sysml-ev").glob("*.dependency.sysml"):
        raise ValueError("Additional dependency must first be pinned in the corpus contract")
    (root / "work").mkdir()
    return root, hashes


def artifact_oracle(root, hashes):
    source = (root / "inputs/EVSample.sysml").read_bytes()
    old, new = "capacity = 50['A⋅h']".encode(), "capacity = 60['A⋅h']".encode()
    candidate = root / "work/EVSample.candidate.sysml"
    expected = source.replace(old, new, 1)
    preserved = all(digest(root / "inputs" / name) == value for name, value in hashes.items())
    exact = source.count(old) == 1 and candidate.is_file() and candidate.read_bytes() == expected
    validation = None
    if candidate.is_file():
        checked = subprocess.run(["python3", str(ROOT / "scripts/sysml.py"), str(candidate), "--syntax-only", "--json"], text=True, capture_output=True, timeout=120)
        try:
            report = json.loads(checked.stdout)
            validation = {k: report.get(k) for k in ("status", "claim_scope", "findings", "parser_issues", "model_sha256")}
        except ValueError:
            validation = {"status": "error", "stderr": checked.stderr[:1500]}
    return {"inputs_preserved": preserved, "exact_authorized_capacity_edit": exact,
            "independent_parser_rerun": validation, "report_exists": (root / "work/report.md").is_file(),
            "artifact_check": preserved and exact and (root / "work/report.md").is_file(),
            "semantic_fidelity": None, "independent_review": False,
            "scope": "Exact byte edit establishes only preservation outside the authorized literal. Engineering explanation/decomposition/migration judgments need independent review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("condition", choices=REVISIONS)
    parser.add_argument("--replicate", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    if not 1 <= args.replicate <= 10 or not 30 <= args.timeout <= 900:
        raise ValueError("Bounded replicate/time budget required")
    root, hashes = prepare(args.condition, args.replicate)
    prompt = (ROOT / "benchmarks/interface/pilot-task.txt").read_text()
    schema = {"type": "object", "properties": {
        "summary": {"type": "string"}, "artifacts": {"type": "array", "items": {"type": "string"}},
        "domain_questions": {"type": "array", "items": {"type": "string"}},
        "limitations": {"type": "array", "items": {"type": "string"}}},
        "required": ["summary", "artifacts", "domain_questions", "limitations"], "additionalProperties": False}
    schema_path = root / "response-schema.json"
    schema_path.write_text(json.dumps(schema))
    final_path = root / "final.json"
    command = [CODEX, "exec", "--ephemeral", "--ignore-user-config", "--strict-config", "--json", "--skip-git-repo-check", "-C", str(root),
               "--sandbox", "workspace-write", "-m", "gpt-6.1-sol", "-c", 'service_tier="default"', "-c", 'model_reasoning_effort="medium"',
               "-c", 'web_search="disabled"', "-c", 'approval_policy="never"', "--output-schema", str(schema_path), "-o", str(final_path), "-"]
    manifest = {"condition": args.condition, "replicate": args.replicate, "revision": REVISIONS[args.condition], "model": "gpt-6.1-sol", "effort": "medium", "service_tier": "default",
                "served_model_and_tier": "CLI events do not expose response routing; requested configuration is recorded", "sandbox": "workspace-write", "timeout_seconds": args.timeout,
                "task_sha256": sha256(prompt.encode()).hexdigest(), "source_sha256": hashes, "parser_sha256": digest(ROOT / ".cache/sysml/pilot-2025-09/sysml/jupyter-sysml-kernel-0.52.0-all.jar"),
                "cli_version": subprocess.check_output([CODEX, "--version"], text=True).strip(), "command": command,
                "started_utc": datetime.now(timezone.utc).isoformat(), "task_payload_bytes": len(prompt.encode())}
    (root / "run-manifest.json").write_text(json.dumps(manifest, indent=2))
    (root / "task.txt").write_text(prompt)
    print(json.dumps({"started": str(root), "configuration": {k: manifest[k] for k in ("model", "effort", "service_tier", "timeout_seconds")}}), flush=True)
    started = time.monotonic()
    timed_out = False
    with (root / "events.jsonl").open("w") as out, (root / "stderr.txt").open("w") as err:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True, start_new_session=True)
        try:
            proc.communicate(prompt, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
    result = summarize_events((root / "events.jsonl").read_text())
    result.update(returncode=proc.returncode, timed_out=timed_out, elapsed_seconds=round(time.monotonic() - started, 3),
                  ended_utc=datetime.now(timezone.utc).isoformat())
    oracle = artifact_oracle(root, hashes)
    result["oracle"] = oracle
    result["completion"] = score_completion(result, oracle)
    (root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"trial": str(root), **{k: result[k] for k in ("returncode", "timed_out", "elapsed_seconds", "provider_usage", "tool_calls", "completion", "oracle")}}), flush=True)


if __name__ == "__main__":
    main()
