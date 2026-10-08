#!/usr/bin/env python3
"""Build fresh offline matched evidence. This program has no model dispatch path."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from harness import (ARMS, answer_template, check_answer, check_patch, cost_ledger, equal_information,
                     load_json, patch_reference, response, review_reference, scripted_calls, size, snapshot, wire)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--license", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture = load_json(Path(__file__).with_name("fixtures.json"))
    source = args.source.read_bytes()
    reference = snapshot(source, fixture)
    if sha256(args.license.read_bytes()).hexdigest() != fixture["source"]["license_sha256"]:
        raise ValueError("License does not match pinned source")
    args.output.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        (args.output / name).write_bytes(wire(value))
    bootstrap = wire({"contract": "offline-matched-reference/1", "read": "task_packet", "scope": reference["authority"],
                      "limits": reference["evidence_limits"], "note": "Reference replay only; not the native API"})
    save("reference-snapshot.json", reference)
    (args.output / "bootstrap.json").write_bytes(bootstrap)
    comparisons = []
    roles = {"status": "review_bundle_only_not_an_agent_workspace", "agent_inputs_released": False,
             "enforcement": "Manifest only; a separate isolated runner must enforce these allowlists before any future trial",
             "per_task_arm_allowlists": []}
    for task in fixture["tasks"]:
        packets = [response(reference, task, arm) for arm in ARMS]
        equality = equal_information(reference, task, packets)
        oracle = answer_template(reference, task)
        save(task["id"] + "-answer-oracle.json", oracle)
        assert check_answer(reference, task, oracle)["reference_checks"] == "pass"
        task_bytes = wire({"id": task["id"], "goal": task["goal"]})
        (args.output / (task["id"] + "-task.json")).write_bytes(task_bytes)
        for packet in packets:
            packet_name = task["id"] + "-" + packet["arm"] + ".json"
            save(packet_name, packet)
            roles["per_task_arm_allowlists"].append({"task": task["id"], "arm": packet["arm"],
                "files": ["bootstrap.json", task["id"] + "-task.json", packet_name]})
            for retry in (False, True):
                calls = scripted_calls(packet, retry)
                receipt = {"task": task["id"], "arm": packet["arm"], "scenario": "one_forced_retry" if retry else "clean",
                           "equality": next(row for row in equality if row["arm"] == packet["arm"]),
                           "task_size": size(task_bytes), "bootstrap_size": size(bootstrap),
                           "cost": cost_ledger(bootstrap, task_bytes, calls), "model_run": False}
                comparisons.append(receipt)
                save(task["id"] + "-" + packet["arm"] + "-" + receipt["scenario"] + "-calls.json",
                     [{**call, "request": call["request"].decode(), "result": call["result"].decode()} for call in calls])
    patches = []
    for intent in fixture["patches"]:
        candidate = patch_reference(source, reference, intent)
        review = review_reference(source, reference, intent)
        report = check_patch(source, source, candidate, reference, intent, review, review)
        assert report["reference_checks"] == "pass"
        (args.output / (intent["id"] + "-reference-candidate.sysml")).write_bytes(candidate)
        save(intent["id"] + "-review-oracle.json", review)
        patches.append({"id": intent["id"], "candidate_sha256": sha256(candidate).hexdigest(), "checks": report})
    if args.source.read_bytes() != source:
        raise ValueError("Input changed while preparing evidence")
    report = {"status": "offline_preparation_only", "source": fixture["source"], "native_binding": None,
              "method": "regex-wordpunct-v2 on exact UTF-8 protocol bytes; not model tokens or billed cost",
              "schedule": "Scripted oracle-selected task packets; clean and exactly one forced failed lookup/retry per arm",
              "scope": "Equal information, identical batch-call count; duplicated arm has one repeated fact across two containers; deduplicated artifact is the control",
              "bootstrap_size": size(bootstrap), "comparisons": comparisons, "patch_oracles": patches,
              "query_tasks": len(fixture["tasks"]), "matched_scenarios": len(comparisons), "model_runs": 0,
              "human_runs": 0, "native_acceptances": 0, "independent_oracle_review": "pending",
              "elicitation_observations": {"domain_questions": None, "needless_questions": None, "provider_safety_confirmations": None},
              "limitations": ["This is reference replay, not an authoritative native query implementation.",
                              "Artifact duplication does not incur model context unless those bytes are actually retrieved.",
                              "A real agent may select, batch or deduplicate differently; actual total/retry context must be recorded.",
                              "Initial native discovery/schema cost, provider context and usage remain unavailable.",
                              "These previously exposed EV facts are calibration data, not held-out engineering qualification."]}
    save("REPORT.json", report)
    save("ROLE_SEPARATION.json", roles)
    save("READINESS.json", {"offline_preparation": "complete", "native_human_ai_acceptance": "blocked",
        "model_dispatch_implemented": False, "ten_capabilities_accepted": 0,
        "required_external_evidence": [
            "Frozen native artifact/core pin and discovery/query/preview/review/apply contract from native owner via parent",
            "Independent source-identity, semantic-annotation, exact-patch and held-out licensed-task oracle approval",
            "Isolated evaluator/actor input separation enforced by the future runner, not just this manifest",
            "Assigned human reviewers and parent-authorized bounded Standard runs; no new credentials or paid provisioning"]})
    pins = {path.name: sha256(path.read_bytes()).hexdigest() for path in sorted(args.output.iterdir()) if path.is_file()}
    save("MANIFEST.json", {"sha256": pins, "source_preserved": True})
    print(json.dumps({key: report[key] for key in ("status", "query_tasks", "matched_scenarios", "model_runs", "human_runs", "native_acceptances")}))


if __name__ == "__main__":
    main()
