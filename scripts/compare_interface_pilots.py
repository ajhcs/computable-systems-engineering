#!/usr/bin/env python3
"""Compare completed pilot metadata; do not promote unreviewed semantics to success."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from benchmark_accounting import require_equivalent

ROOT = Path(__file__).resolve().parents[1]


def load_trial(name):
    if name not in {f"{condition}-{n}" for condition in ("baseline", "optimized") for n in range(1, 11)}:
        raise ValueError("Unknown bounded trial name")
    folder = ROOT / ".cache/interface-benchmark/trials" / name
    manifest = json.loads((folder / "run-manifest.json").read_text())
    result = json.loads((folder / "result.json").read_text())
    # Keep raw model/tool text in the ignored private run record. Tracked evidence
    # contains its digest and costs, not duplicated source/model report material.
    for item in result.get("tool_payloads", []):
        command = item.pop("command", None)
        item["command_sha256"] = sha256((command or "").encode()).hexdigest()
    evidence = {file: sha256((folder / file).read_bytes()).hexdigest() for file in ("events.jsonl", "run-manifest.json", "result.json", "task.txt")}
    return {"name": name, "manifest": manifest, "result": result, "evidence_sha256": evidence, "directory": str(folder)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="baseline-1")
    parser.add_argument("--optimized", default="optimized-1")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    before, after = load_trial(args.baseline), load_trial(args.optimized)
    require_equivalent(before["manifest"], after["manifest"])
    result = {"sample_size": "one paired pilot; no reliability or causal generalization", "conditions_equivalent": True,
              "baseline": before, "optimized": after, "deltas": {},
              "limits": ["Requested model/tier match; provider events do not expose served routing.", "Fixed baseline-first order can confound caching and latency; counterbalanced replication remains necessary.", "Exact-edit and parser oracles are separate from independent engineering fidelity review.", "NASA native numerical and migration oracles are unavailable; no equivalence or simulation success is claimed."]}
    for metric in ("tool_calls", "elapsed_seconds"):
        left, right = before["result"][metric], after["result"][metric]
        result["deltas"][metric] = {"baseline": left, "optimized": right, "change": right - left}
    usages = [x["result"]["provider_usage"] for x in (before, after)]
    if all(isinstance(x, dict) for x in usages):
        for metric in set(usages[0]) & set(usages[1]):
            left, right = usages[0][metric], usages[1][metric]
            result["deltas"][metric] = {"baseline": left, "optimized": right, "change": right - left}
    destination = Path(args.output)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(destination), "deltas": result["deltas"], "completion": [x["result"]["completion"] for x in (before, after)]}))


if __name__ == "__main__":
    main()
