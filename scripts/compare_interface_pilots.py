#!/usr/bin/env python3
"""Compare completed pilot metadata; do not promote unreviewed semantics to success."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from benchmark_accounting import require_equivalent, summarize_events, score_completion

ROOT = Path(__file__).resolve().parents[1]


def load_trial(name, trials_root=None):
    if name not in {f"{condition}-{n}" for condition in ("baseline", "optimized") for n in range(1, 11)}:
        raise ValueError("Unknown bounded trial name")
    folder = Path(trials_root or ROOT / ".cache/interface-benchmark/trials") / name
    manifest = json.loads((folder / "run-manifest.json").read_text(encoding="utf-8"))
    result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
    result.update(summarize_events((folder / "events.jsonl").read_text(encoding="utf-8")))
    result["completion"] = score_completion(result, result.get("oracle", {}))
    result["accounting_recomputed_from_events"] = True
    # Keep raw model/tool text in the ignored private run record. Tracked evidence
    # contains its digest and costs, not duplicated source/model report material.
    for item in result.get("tool_payloads", []):
        command = item.pop("command", None)
        item["command_sha256"] = sha256(command.encode()).hexdigest() if command is not None else None
    evidence = {file: sha256((folder / file).read_bytes()).hexdigest() for file in ("events.jsonl", "run-manifest.json", "result.json", "task.txt")}
    return {"name": name, "manifest": manifest, "result": result, "evidence_sha256": evidence, "directory": str(folder)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="baseline-1")
    parser.add_argument("--optimized", default="optimized-1")
    parser.add_argument("--output", required=True)
    parser.add_argument("--trials-root", type=Path, help="Read-only location of preserved trials; output must be outside it")
    args = parser.parse_args()
    trial_root = (args.trials_root or ROOT / ".cache/interface-benchmark/trials").resolve()
    if Path(args.output).resolve().is_relative_to(trial_root):
        raise ValueError("Preserved trial evidence cannot be overwritten")
    before, after = load_trial(args.baseline, trial_root), load_trial(args.optimized, trial_root)
    require_equivalent(before["manifest"], after["manifest"])
    if any(item["result"]["transcript_status"] != "complete" for item in (before, after)):
        raise ValueError("Comparison incomplete: invalid or unfinished trial transcript")
    result = {"sample_size": "one paired pilot; no reliability or causal generalization", "conditions_equivalent": True,
              "baseline": before, "optimized": after, "deltas": {},
              "limits": ["Requested model/tier match; provider events do not expose served routing.", "Fixed baseline-first order can confound caching and latency; counterbalanced replication remains necessary.", "Exact-edit and parser oracles are separate from independent engineering fidelity review.", "NASA native numerical and migration oracles are unavailable; no equivalence or simulation success is claimed.", "Missing tool arguments are unknown. Per-tool input estimates measure logged command text only, never complete tool-argument or billed cost."]}
    for metric in ("tool_calls", "elapsed_seconds"):
        left, right = before["result"][metric], after["result"][metric]
        result["deltas"][metric] = {"baseline": left, "optimized": right, "change": right - left}
    usages = [x["result"]["provider_usage"] for x in (before, after)]
    if all(isinstance(x, dict) for x in usages):
        for metric in set(usages[0]) & set(usages[1]):
            left, right = usages[0][metric], usages[1][metric]
            result["deltas"][metric] = {"baseline": left, "optimized": right, "change": right - left}
    destination = Path(args.output)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(destination), "deltas": result["deltas"], "completion": [x["result"]["completion"] for x in (before, after)]}))


if __name__ == "__main__":
    main()
