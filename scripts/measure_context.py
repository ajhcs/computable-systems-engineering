#!/usr/bin/env python3
"""Reproducible context-size and repair-turn probe (not an LLM benchmark)."""

import copy
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier import focused_view, verify


def tokens(value):
    """regex-wordpunct-v1: Unicode words or one nonspace punctuation character."""
    return len(re.findall(r"\w+|[^\w\s]", json.dumps(value, sort_keys=True, separators=(",", ":"))))


def main():
    model = json.loads((ROOT / "examples/verifier/valid.json").read_text())
    model["scenarios"]["S2"] = copy.deepcopy(model["scenarios"]["S1"])
    model["scenarios"]["S2"]["steps"] = {
        "U1": {"from": "idle", "to": "done", "effects": {"speed": 1}}}
    model["scenarios"]["S2"]["external_at"] = []
    model["traces"].append({"from": "S2", "to": "R1", "kind": "addresses"})
    # Same requested S1 repair for both payloads.
    model["scenarios"]["S1"]["steps"]["T1"].pop("produces")
    whole_before = verify(model, review=True)
    focus_before = verify(model, review=True, selected=["S1"])
    if whole_before["status"] != "fail" or focus_before["status"] != "fail":
        raise RuntimeError("Defect probe did not fail")
    full_tokens = tokens(model) + tokens(whole_before)
    focus_tokens = tokens(focused_view(model, ["S1"])) + tokens(focus_before)
    model["scenarios"]["S1"]["steps"]["T1"]["produces"] = ["gap"]
    whole_after = verify(model, review=True)
    focus_after = verify(model, review=True, selected=["S1"])
    if whole_after["status"] != "pass" or focus_after["status"] != "pass":
        raise RuntimeError("Repair probe did not pass")
    print(json.dumps({"tokenizer": "regex-wordpunct-v1 (not a model tokenizer)",
                      "task": "restore S1 gap producer in a two-scenario synthetic model",
                      "whole_input_and_diagnostics": full_tokens,
                      "focused_input_and_diagnostics": focus_tokens,
                      "whole_repair_turns": 1, "focused_repair_turns": 1,
                      "before": [whole_before["status"], focus_before["status"]],
                      "after": [whole_after["status"], focus_after["status"]]}, indent=2))


if __name__ == "__main__":
    main()
